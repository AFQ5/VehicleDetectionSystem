# VehicleDetectionSystem

A real-time vehicle detection and parking occupancy system using YOLOv8 and OpenCV. Developed as a final-year project at King Saud University.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Introduction

This project aims to create an efficient and effective vehicle detection and parking occupancy system. It utilizes YOLOv8 for real-time object detection and OpenCV for image processing, running on a Raspberry Pi.

## Features

- Real-time vehicle detection
- Accurate parking occupancy status
- User-friendly web interface
- Data storage with SQLite

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/AFQ5/VehicleDetectionSystem.git
   cd VehicleDetectionSystem
   ```

2. **Set up the virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required packages for both `Server` and `Unit` folders:**

   ```bash
   pip install -r Server/requirements.txt
   pip install -r Unit/requirements.txt
   ```

4. **Set up the SQLite database:**

   ```bash
   python Server/create_db.py
   ```

5. **Configure environment variables:**

   Create a `.env` file in the `Server` directory and add the following configuration:

   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   ```

6. **Update `data_sender.py` in the `Unit` folder:**

   In the `data_sender.py` file, set the backend URL configuration:

   ```python
   GLOBAL_URL = None  # Replace with your actual backend URL
   BACKEND_URL = GLOBAL_URL if GLOBAL_URL is not None else 'http://127.0.0.1:5000/spots'
   ```

## Usage

1. **Start the Flask server:**

   ```bash
   cd Server
   flask run --host=0.0.0.0
   ```

2. **Start the unit script:**

   Navigate to the `Unit` directory and run the main script to start processing video data and sending updates:

   ```bash
   cd Unit
   python main.py
   ```

3. **Access the web interface:**

   Open your browser and navigate to `http://localhost:5000` or use your public IP if you have configured port forwarding.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

**Abdullah Alqahtani**  
Email: [abdullahfaq5@gmail.com](mailto:abdullahfaq5@gmail.com)
