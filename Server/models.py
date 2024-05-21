from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ParkingSpot(db.Model):
    """
    ParkingSpot model represents a parking spot within a section.

    Attributes:
    id (int): The unique identifier for the parking spot.
    section (str): The section to which the parking spot belongs.
    spot_number (int): The number assigned to the parking spot within its section.
    status (str): The current status of the parking spot (e.g., 'occupied', 'available').
    updated_at (datetime): The timestamp of the last update to the parking spot's status.
    """
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(50), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
