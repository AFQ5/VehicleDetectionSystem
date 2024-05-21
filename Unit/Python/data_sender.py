import requests
import os
import time
from utils import fetch_parking_occupancy

GLOBAL_URL = None  # Replace with your actual backend URL
BACKEND_URL = GLOBAL_URL if GLOBAL_URL is not None else 'http://127.0.0.1:5000/spots'  

def send_updates(updates):
    """
    Sends parking occupancy updates to the backend server.

    Parameters:
    updates (list): A list of dictionaries containing parking spot updates.

    Raises:
    requests.exceptions.RequestException: If the request to the backend server fails.
    """
    try:
        response = requests.post(BACKEND_URL, json=updates)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def send_parking_info(camera_id):
    """
    Fetches parking occupancy information for a specific camera and sends updates to the backend server.

    Parameters:
    camera_id (int): The ID of the camera to fetch parking occupancy information for.
    """
    sections = fetch_parking_occupancy(camera_id)
    updates = []
    for section in sections:
        section_id = section.get('id')
        for i, area in enumerate(section.get('parking_areas', [])):
            status = 'occupied' if area.get('occupied') else 'available'
            updates.append({
                'section': section_id,
                'spot_number': i + 1,
                'status': status
            })
    send_updates(updates)

def monitor_file(file_path, callback, camera_id):
    """
    Monitors a file for changes and calls a callback function when a change is detected.

    Parameters:
    file_path (str): The path of the file to monitor.
    callback (function): The callback function to call when the file changes.
    camera_id (int): The ID of the camera to pass to the callback function.
    """
    last_mtime = os.path.getmtime(file_path)
    while True:
        try:
            current_mtime = os.path.getmtime(file_path)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                callback(camera_id)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"An error occurred while monitoring the file: {e}")
        time.sleep(1)
