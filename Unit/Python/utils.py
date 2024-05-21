import json
import os

def find_file(filename):
    """
    Searches for a file with the specified filename in the current directory and all subdirectories.

    Parameters:
    filename (str): The name of the file to search for.

    Returns:
    str: The full path to the file if found.

    Raises:
    FileNotFoundError: If the file is not found in the directory tree.
    """
    for root, dirs, files in os.walk('.'):
        if filename in files:
            return os.path.join(root, filename)
    raise FileNotFoundError(f"File '{filename}' not found")

coco = find_file("coco.json")
info = find_file("parking_info.json")
previously_written = False

def read_class_list(class_list_path=coco):
    """
    Reads a JSON file containing class information and returns a list of class names.

    Parameters:
    class_list_path (str): The path to the JSON file containing class information.

    Returns:
    list: A list of class names.
    """
    with open(class_list_path, 'r') as file:
        data = json.load(file)
    return [item["name"] for item in data["classes"]]

def initialize_file(camera_id, filename=info):
    """
    Initializes a JSON file for storing camera information. If the file does not exist, it creates it.

    Parameters:
    camera_id (int): The ID of the camera to initialize in the file.
    filename (str): The path to the JSON file to initialize (default is the global 'info' variable).
    """
    if not os.path.exists(filename):
        data = {"cameras": {}}
    else:
        with open(filename, 'r') as file:
            data = json.load(file)

    camera_key = f"camera_{camera_id}"
    if camera_key not in data['cameras']:
        data['cameras'][camera_key] = {"sections": []}

    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def read_parking_areas(camera_id, filename=info):
    """
    Reads the parking areas for a specified camera from a JSON file.

    Parameters:
    camera_id (int): The ID of the camera to read parking areas for.
    filename (str): The path to the JSON file to read from (default is the global 'info' variable).

    Returns:
    list: A list of sections for the specified camera. Returns an empty list if the camera is not found.

    Raises:
    FileNotFoundError: If the file is not found.
    json.JSONDecodeError: If there is an error decoding the JSON file.
    """
    camera_key = f"camera_{camera_id}"
    try:
        if not os.path.exists(filename):
            initialize_file(camera_id, filename)
        with open(filename, 'r') as file:
            data = json.load(file)

        if camera_key not in data['cameras']:
            initialize_file(camera_id, filename)
            with open(filename, 'r') as file:
                data = json.load(file)
        sections = data['cameras'].get(camera_key, {}).get('sections', [])
        return sections

    except FileNotFoundError:
        print(f"File not found: {filename}")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {filename}")
        return []

def fetch_parking_occupancy(camera_id=None, filename=info):
    """
    Fetches the parking occupancy information for a specified camera or all cameras from a JSON file.

    Parameters:
    camera_id (int, optional): The ID of the camera to fetch parking occupancy for. If None, fetches for all cameras.
    filename (str): The path to the JSON file to read from (default is the global 'info' variable).

    Returns:
    dict or list: If camera_id is specified, returns a list of sections for the specified camera. 
                  If camera_id is None, returns a dictionary with occupancy information for all cameras.
    """
    with open(filename, 'r') as file:
        data = json.load(file)
    return data['cameras'].get(f"camera_{camera_id}", {}).get('sections', []) if camera_id else data
