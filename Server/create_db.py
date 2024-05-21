# create_db.py
from app import app
from models import db

# Create all database tables within the application context
with app.app_context():
    db.create_all()
