import cv2
import threading
from module import camera_thread

def main():
    """
    Main function to initialize the model, read class lists, set up video sources,
    and create threads for processing each video source concurrently.
    """
    try:
        # Define your video sources here. Replace with actual sources as needed.
        camera_sources = ["parking.mp4"]  
        # Example: ["0", "http://example.com/stream", "localvideo.mp4"]
        
        # Flag to control whether to display the processed video frames.
        display = True
        
        # Container for threads.
        threads = []
        
        # Create and start a thread for each video source.
        for index, source in enumerate(camera_sources):
            camera_id = index + 1
            t = threading.Thread(target=camera_thread, args=(source, display, camera_id))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Ensure all OpenCV windows are closed.
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
