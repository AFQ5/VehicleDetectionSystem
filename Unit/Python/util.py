import json
from utils import read_parking_areas, find_file
from data_sender import send_parking_info

info = find_file("parking_info.json")

def write_parking_areas(camera_id, sections, filename=info):
    """
    Writes the parking sections data to the JSON file. If there are changes, it triggers an update.

    Parameters:
    camera_id (int): The ID of the camera.
    sections (list): The list of sections to write to the file.
    filename (str): The path to the JSON file (default is the global 'info' variable).

    Raises:
    Exception: If there is an error writing to the file.
    """
    global previously_written
    try:
        with open(filename, 'r+') as file:
            data = json.load(file)
            camera_key = f"camera_{camera_id}"
            if camera_key not in data['cameras']:
                data['cameras'][camera_key] = {"sections": []}
            if data['cameras'][camera_key]['sections'] != sections:
                data['cameras'][camera_key]['sections'] = sections
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
                print("Write successful")
                previously_written = True
                send_parking_info(camera_id)  # Trigger the update when changes are detected
            else:
                if previously_written:
                    print("No changes to write")
                    previously_written = False
    except Exception as e:
        print(f"Failed to write to file {filename}: {e}")

def add_section(new_area, section_id, camera_id, filename=info):
    """
    Adds a new section to the parking areas for a specified camera.

    Parameters:
    new_area (list): The coordinates of the new area.
    section_id (int): The ID of the new section.
    camera_id (int): The ID of the camera.
    filename (str): The path to the JSON file (default is the global 'info' variable).

    Raises:
    ValueError: If a section with the specified ID already exists.
    """
    sections = read_parking_areas(camera_id, filename)
    if any(sec['id'] == f"section_{section_id}" for sec in sections):
        raise ValueError(f"Section with ID '{section_id}' already exists.")
    
    new_section = {
        "id": f"section_{section_id}",
        "coordinates": new_area,
        "total": 0,
        "occupied": 0,
        "free": 0,
        "details": [],
        "parking_areas": []
    }
    sections.append(new_section)
    write_parking_areas(camera_id, sections, filename)
    print(f"New section '{section_id}' added successfully: {new_area}")

def delete_section(section_id, camera_id, filename=info):
    """
    Deletes a section from the parking areas for a specified camera.

    Parameters:
    section_id (str): The ID of the section to delete.
    camera_id (int): The ID of the camera.
    filename (str): The path to the JSON file (default is the global 'info' variable).

    Returns:
    None
    """
    sections = read_parking_areas(camera_id, filename)
    filtered_sections = [sec for sec in sections if sec['id'] != section_id]
    if len(filtered_sections) != len(sections):
        write_parking_areas(camera_id, filtered_sections, filename)
        print(f"Section '{section_id}' has been successfully deleted along with its associated spots.")
    else:
        print(f"No section with ID '{section_id}' found. Unable to delete.")

def insert_parking_area(new_area, section_id, camera_id, filename=info):
    """
    Inserts a new parking area into a specified section for a specified camera.

    Parameters:
    new_area (list): The coordinates of the new parking area.
    section_id (str): The ID of the section to insert the parking area into.
    camera_id (int): The ID of the camera.
    filename (str): The path to the JSON file (default is the global 'info' variable).

    Returns:
    None
    """
    sections = read_parking_areas(camera_id, filename)
    found = False
    for section in sections:
        if section['id'] == section_id:
            found = True
            new_parking_area = {
                "coordinates": new_area,
                "occupied": False
            }
            section['parking_areas'].append(new_parking_area)
            section['parking_areas'].sort(key=lambda x: (min(point[0] for point in x['coordinates']), min(point[1] for point in x['coordinates'])))
            write_parking_areas(camera_id, sections, filename)
            print(f"New parking area added in section '{section_id}': {new_area}")
            break
    if not found:
        print(f"No section with ID '{section_id}' found. Unable to add parking area.")

def delete_parking_area(section_id, index, camera_id, filename=info):
    """
    Deletes a parking area from a specified section for a specified camera.

    Parameters:
    section_id (str): The ID of the section to delete the parking area from.
    index (int): The index of the parking area to delete.
    camera_id (int): The ID of the camera.
    filename (str): The path to the JSON file (default is the global 'info' variable).

    Returns:
    None
    """
    sections = read_parking_areas(camera_id, filename)
    for section in sections:
        if section['id'] == section_id:
            if 0 <= index < len(section['parking_areas']):
                del section['parking_areas'][index]
                write_parking_areas(camera_id, sections, filename)
                print(f"Parking area {index+1} in section '{section_id}' has been deleted.")
                return
            else:
                print("Invalid index for parking area deletion.")
                return
    print("Section ID not found for deletion.")

def save_parking_occupancy(camera_id, updated_sections, filename=info):
    """
    Saves the updated parking occupancy information for a specified camera.

    Parameters:
    camera_id (int): The ID of the camera.
    updated_sections (list): The updated list of sections.
    filename (str): The path to the JSON file (default is the global 'info' variable).

    Returns:
    None
    """
    current_sections = read_parking_areas(camera_id, filename)
    for section in updated_sections:
        index = next((i for i, s in enumerate(current_sections) if s['id'] == section['id']), None)
        if index is not None:
            current_sections[index] = section
        else:
            current_sections.append(section)
    write_parking_areas(camera_id, current_sections, filename)
