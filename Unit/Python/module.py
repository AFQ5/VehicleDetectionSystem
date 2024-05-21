import os
import cv2
import time
import numpy as np
import pandas as pd
from ultralytics import YOLO
from urllib.parse import urlparse
from tkinter import Tk, simpledialog, messagebox as msgbox
from util import read_parking_areas, insert_parking_area, delete_parking_area, save_parking_occupancy, add_section, delete_section
from utils import read_class_list

drawing = False  # Global variable to keep track of drawing state
points = []  # Global list to keep track of points drawn on the frame
mode = "spot"  # Default mode

def initialize_yolo_model():
    """
    Initializes the YOLO model for object detection.

    Returns:
    YOLO: The initialized YOLO model.
    """
    return YOLO('yolov8s.pt')

def initialize_video_capture(source):
    """
    Initializes the video capture from a given source.

    Parameters:
    source (int, str): The video source, which can be a camera index, a URL, or a file path.

    Returns:
    cv2.VideoCapture: The video capture object.

    Raises:
    ValueError: If the video file does not exist.
    OSError: If the video source cannot be opened.
    """
    if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
        cap = cv2.VideoCapture(int(source))  # Convert source to integer if it's digit string or int
    elif urlparse(source).scheme in ('http', 'https', 'rtsp'):
        cap = cv2.VideoCapture(source)  # Directly use the URL for network streams
    else:  # Assuming the source is a filepath
        if not os.path.exists(source):
            raise ValueError("Video file does not exist: " + source)
        cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        raise OSError("Failed to open video source: " + source)
    
    return cap

def make_draw_function(camera_id, root):
    """
    Creates a drawing function for interactive annotation on the video frame.

    Parameters:
    camera_id (int): The ID of the camera.
    root (Tk): The Tkinter root window for displaying dialogs.

    Returns:
    function: The drawing function to be used with OpenCV's setMouseCallback.
    """
    def draw(events, x, y, flags, param):
        global points, drawing, mode
        if events == cv2.EVENT_LBUTTONDOWN:
            if not drawing:
                drawing = True
                points = [(x, y)]
                print(f"Started new {mode} at {points}")
            else:
                points.append((x, y))
                print(f"Point added: {points}")
                if len(points) == 4:
                    polygon = np.array(points, dtype=np.int32)
                    if mode == "section":
                        polygon = np.array(points, dtype=np.int32)
                        if not check_overlap_with_existing_sections(polygon, camera_id):
                            section_id = simpledialog.askstring("Input", "Enter ID for the new section", parent=root)
                            if section_id:
                                try:
                                    add_section(points.copy(), section_id, camera_id)
                                except ValueError as e:
                                    msgbox.showerror("Error", str(e))
                        else:
                            msgbox.showerror("Error", "Section overlaps with an existing one.")
                    else:
                        section_id = detect_section(polygon, camera_id)
                        if section_id and is_mostly_inside_section(polygon, section_id, camera_id):
                            insert_parking_area(points.copy(), section_id, camera_id)
                        else:
                            msgbox.showerror("Error", "Parking area must be within a section and at least 80% inside its section.")
                    points = []
                    drawing = False

        elif events == cv2.EVENT_RBUTTONDOWN:
            if mode == "section":
                delete_section_by_point(x, y, camera_id, root)
            else:
                delete_parking_area_by_point(x, y, camera_id)

        elif events == cv2.EVENT_MBUTTONDOWN:
            mode = "section" if mode == "spot" else "spot"
            points = []
            drawing = False
            print(f"Mode switched to {mode}")

    return draw

def delete_parking_area_by_point(x, y, camera_id):
    """
    Deletes a parking area based on the point clicked by the user.

    Parameters:
    x (int): X-coordinate of the mouse click.
    y (int): Y-coordinate of the mouse click.
    camera_id (int): The ID of the camera.
    """
    drawing = False
    sections = read_parking_areas(camera_id)
    for section in sections:
        for i, area in enumerate(section['parking_areas']):
            if cv2.pointPolygonTest(np.array(area['coordinates'], dtype=np.int32), (x, y), False) >= 0:
                section_id = section['id']
                delete_parking_area(section_id, i, camera_id)
                return
    print("No spot found at the clicked location.")

def delete_section_by_point(x, y, camera_id, root):
    """
    Deletes a section based on a point clicked by the user within that section's area.

    Parameters:
    x (int): X-coordinate of the mouse click.
    y (int): Y-coordinate of the mouse click.
    camera_id (int): The ID of the camera.
    root (Tk): The Tkinter root window for displaying dialogs.
    """
    sections = read_parking_areas(camera_id)
    for section in sections:
        section_polygon = np.array(section['coordinates'], dtype=np.int32)
        if cv2.pointPolygonTest(section_polygon, (x, y), False) >= 0:
            if msgbox.askyesno("Confirm Delete", "Delete all spots in this section?", parent=root):
                delete_section(section['id'], camera_id)
                return
            else:
                print("Deletion cancelled.")
                return
    print("No section found at the clicked location.")

def check_overlap_with_existing_sections(polygon, camera_id):
    """
    Checks if a given polygon overlaps with any existing sections.

    Parameters:
    polygon (list of tuples): The coordinates of the polygon to check.
    camera_id (int): The ID of the camera.

    Returns:
    bool: True if the polygon overlaps with any existing sections, False otherwise.
    """
    sections = read_parking_areas(camera_id)
    new_poly = np.array(polygon, dtype=np.int32)
    for section in sections:
        section_polygon = np.array(section['coordinates'], dtype=np.int32)
        _, intersection = cv2.intersectConvexConvex(new_poly, section_polygon)
        if intersection is not None and intersection.size > 0:
            return True
    return False

def detect_section(polygon, camera_id):
    """
    Detects which section a given polygon belongs to based on its coordinates.

    Parameters:
    polygon (list of tuples): The coordinates of the polygon to check.
    camera_id (int): The ID of the camera.

    Returns:
    str: The ID of the section if found, None otherwise.
    """
    sections = read_parking_areas(camera_id)
    test_point = (int(polygon[0][0]), int(polygon[0][1]))
    for section in sections:
        section_polygon = np.array(section['coordinates'], dtype=np.int32).reshape((-1, 1, 2))
        if cv2.pointPolygonTest(section_polygon, test_point, False) >= 0:
            return section['id']
    return None

def is_mostly_inside_section(polygon, section_id, camera_id):
    """
    Checks if a given polygon is mostly inside a specified section.

    Parameters:
    polygon (list of tuples): The coordinates of the polygon to check.
    section_id (str): The ID of the section.
    camera_id (int): The ID of the camera.

    Returns:
    bool: True if the polygon is at least 80% inside the section, False otherwise.
    """
    sections = read_parking_areas(camera_id)
    new_poly = np.array(polygon, dtype=np.int32)
    for section in sections:
        if section['id'] == section_id:
            section_polygon = np.array(section['coordinates'], dtype=np.int32)
            _, intersection = cv2.intersectConvexConvex(new_poly, section_polygon, handleNested=True)
            if intersection is not None and intersection.size > 0:
                intersection_area = cv2.contourArea(intersection)
                polygon_area = cv2.contourArea(new_poly)
                if (intersection_area / polygon_area) >= 0.8:
                    return True
    return False

def iou(box1, box2):
    """
    Calculates the Intersection over Union (IoU) of two bounding boxes.

    Parameters:
    box1 (tuple): The coordinates of the first bounding box (x1, y1, x2, y2).
    box2 (tuple): The coordinates of the second bounding box (x1, y1, x2, y2).

    Returns:
    float: The IoU value.
    """
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0  # No intersection

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    iou = intersection_area / float(box1_area + box2_area - intersection_area)
    return iou

def convert_polygon_to_bbox(polygon):
    """
    Converts a polygon to a bounding box.

    Parameters:
    polygon (list of tuples): The coordinates of the polygon.

    Returns:
    tuple: The bounding box coordinates (x1, y1, x2, y2).
    """
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    return min(xs), min(ys), max(xs), max(ys)

def process_frame(frame, sections, class_list, model):
    """
    Processes each frame of the video to detect objects and determine their presence in predefined areas
    within sections. Utilizes both center point and IoU methods sequentially.

    Parameters:
    frame (numpy.ndarray): The current video frame.
    sections (list of dicts): Each dict represents a section containing multiple parking areas.
    class_list (list of str): The list of class names the model can detect.
    model (YOLO): The YOLO model instance used for detection.

    Returns:
    tuple: Processed frame, updated sections with occupancy details.
    """
    results = model.predict(frame, verbose=False)
    detections = pd.DataFrame(results[0].boxes.data).astype("float")

    for section in sections:
        section['total'] = len(section['parking_areas'])
        section['occupied'] = 0
        section['free'] = section['total']
        section['details'] = [0] * section['total']

        for i, area in enumerate(section['parking_areas']):
            area['occupied'] = False
            polygon = np.array(area['coordinates'], dtype=np.int32)

            for _, row in detections.iterrows():
                x1, y1, x2, y2, _, class_id = row.astype(int)
                class_name = class_list[class_id]
                if 'car' in class_name or 'truck' in class_name:
                    car_bbox = (x1, y1, x2, y2)
                    car_center = ((x1 + x2) // 2, (y1 + y2) // 2)

                    # Check if the car center is inside the parking area polygon
                    if cv2.pointPolygonTest(polygon, car_center, False) >= 0:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.circle(frame, car_center, 3, (0, 0, 255), -1)
                        area['occupied'] = True
                        section['details'][i] = 1
                        section['occupied'] += 1
                        section['free'] -= 1
                        break

                    # If not found by center point, check by IoU
                    if not area['occupied']:
                        area_bbox = convert_polygon_to_bbox(area['coordinates'])
                        if iou(car_bbox, area_bbox) > 0.25:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            area['occupied'] = True
                            section['details'][i] = 1
                            section['occupied'] += 1
                            section['free'] -= 1
                            break

    return frame, sections

def display_parking_occupancy(frame, sections, camera_id, root):
    """
    Displays parking space occupancy on the video frame with labels at the bottom (or top) of each section and parking area.

    Parameters:
    frame (numpy.ndarray): The current video frame.
    sections (list): List of sections including static and dynamic details.
    camera_id (int): The identifier for the camera.
    root (Tk): The Tkinter root window for displaying dialogs.
    """
    free_spaces = 0
   
    for section in sections:
        section_polygon = np.array(section['coordinates'], np.int32)
        cv2.polylines(frame, [section_polygon], True, (0, 165, 255), 3)  # Orange color for section boundary
        
        # Calculate position for section label
        bottom_line = np.array(section['coordinates'][-2:])
        bottom_center_x = int((bottom_line[0][0] + bottom_line[1][0]) / 2)
        bottom_center_y = int(max(bottom_line[0][1], bottom_line[1][1]))
        
        section_text = f"{section['id']}"
        (text_width, text_height), _ = cv2.getTextSize(section_text, cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
        background_top_left = (bottom_center_x - text_width // 2 - 2, bottom_center_y - text_height - 2)
        background_bottom_right = (bottom_center_x + text_width // 2 + 2, bottom_center_y + 2)
        cv2.rectangle(frame, background_top_left, background_bottom_right, (0, 165, 255), -1)
        
        text_position = (bottom_center_x - text_width // 2, bottom_center_y - 2)
        cv2.putText(frame, section_text, text_position, cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

        for area_index, area in enumerate(section['parking_areas']):
            count = section['details'][area_index]
            color = (0, 255, 0) if count == 0 else (0, 0, 255)  # Green if free, red if occupied

            # Draw the polygon for each parking area
            cv2.polylines(frame, [np.array(area['coordinates'], np.int32)], True, color, 2)

            # Calculate label position for parking area
            bottom_line = np.array(area['coordinates'][-2:])
            bottom_center_x = int((bottom_line[0][0] + bottom_line[1][0]) / 2)
            bottom_center_y = int(max(bottom_line[0][1], bottom_line[1][1]))
            
            text = f"{area_index+1}"
            (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
            background_top_left = (bottom_center_x - text_width // 2 - 2, bottom_center_y - text_height - 2)
            background_bottom_right = (bottom_center_x + text_width // 2 + 2, bottom_center_y + 2)
            cv2.rectangle(frame, background_top_left, background_bottom_right, color, -1)
            
            text_position = (bottom_center_x - text_width // 2, bottom_center_y - 2)
            cv2.putText(frame, text, text_position, cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

            free_spaces += 1 if count == 0 else 0

    # Display the total number of free spaces
    cv2.putText(frame, f"Free spaces: {free_spaces}", (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
    
    # Show the frame with the occupancy information
    cv2.imshow(f"Camera {camera_id} - Parking Occupancy", frame)
    cv2.waitKey(1)  # Adjust the wait key as necessary

    # Set up mouse callback for interactive drawing and editing
    draw_function = make_draw_function(camera_id, root)
    cv2.setMouseCallback(f"Camera {camera_id} - Parking Occupancy", draw_function)

def camera_thread(camera_source, display, camera_id):
    """
    Handles video capture from a specified source, processes each frame to detect and display parking occupancy,
    and manages the drawing functionality based on user interaction.

    Parameters:
    camera_source (str or int): The source of the video. Can be a filepath, a URL, or an integer representing a webcam ID.
    display (bool): Flag to control whether to display the processed video frames.
    camera_id (int): An identifier for the camera source, used for window naming and storage purposes.
    """
    model = initialize_yolo_model()
    class_list = read_class_list()
    cap = initialize_video_capture(camera_source)
    window_name = f"Camera {camera_id} - Parking Occupancy"
    root = Tk()  # Create a Tkinter root instance once for the application
    root.withdraw()  # Hide the main window

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        time.sleep(0.5)  # Control frame rate for processing by adding a slight delay
        frame = cv2.resize(frame, (1020, 500))  # Resize frame for processing

        sections = read_parking_areas(camera_id)  # Read the current state of sections
        processed_frame, updated_sections = process_frame(frame, sections, class_list, model)  # Process each frame

        # Save occupancy updates immediately after processing
        save_parking_occupancy(camera_id, updated_sections)

        if display:
            display_parking_occupancy(processed_frame, updated_sections, camera_id, root)

        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyWindow(window_name)  # Close only the window associated with this thread
    root.destroy()  # Properly destroy the root window when done
