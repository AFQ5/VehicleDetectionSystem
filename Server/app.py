import io
import time
import base64
import matplotlib
import pandas as pd
matplotlib.use('Agg')  # Use the Agg backend for non-interactive environments
from flask_cors import CORS
from datetime import datetime
import matplotlib.pyplot as plt
from models import db, ParkingSpot
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
db.init_app(app)

@app.route('/')
def home():
    """
    Renders the home page.

    Returns:
    str: The rendered HTML template for the home page.
    """
    return render_template('index.html')

@app.route('/analysis-page')
def analysis_page():
    """
    Renders the analysis page.

    Returns:
    str: The rendered HTML template for the analysis page.
    """
    return render_template('analysis.html')

@app.route('/spots', methods=['GET'])
def get_spots():
    """
    Retrieves all parking spots from the database and returns them as JSON.

    Returns:
    Response: A JSON response containing a list of parking spots.
    """
    spots = ParkingSpot.query.all()
    spot_list = [{
        'section': spot.section,
        'spot_number': spot.spot_number,
        'status': spot.status
    } for spot in spots]
    return jsonify(spot_list)

@app.route('/spots', methods=['POST'])
def update_spots():
    """
    Updates the status of parking spots based on the received JSON data.

    Returns:
    Response: A JSON response indicating the success or failure of the update operation.
    """
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({'error': 'Invalid data format, expected a list of spot updates'}), 400

    retries = 5
    for spot_data in data:
        section = spot_data.get('section')
        spot_number = spot_data.get('spot_number')
        status = spot_data.get('status')

        if not section or not spot_number or not status:
            return jsonify({'error': 'Missing data fields'}), 400

        while retries > 0:
            try:
                spot = ParkingSpot.query.filter_by(section=section, spot_number=spot_number).first()
                if spot:
                    spot.status = status
                    spot.updated_at = datetime.utcnow()
                else:
                    new_spot = ParkingSpot(section=section, spot_number=spot_number, status=status)
                    db.session.add(new_spot)
                db.session.commit()
                break
            except Exception as e:
                db.session.rollback()
                retries -= 1
                if "database is locked" in str(e):
                    time.sleep(0.5)
                else:
                    return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Spots updated successfully'})

@app.route('/analysis', methods=['GET'])
def analyze_data():
    """
    Analyzes the parking spot data and returns various charts and statistics as JSON.

    Returns:
    Response: A JSON response containing the analysis results, including base64-encoded charts.
    """
    spots = ParkingSpot.query.all()
    df = pd.DataFrame([{
        'section': spot.section,
        'spot_number': spot.spot_number,
        'status': spot.status,
        'updated_at': spot.updated_at
    } for spot in spots])

    if df.empty:
        return jsonify({'message': 'No data available for analysis'})

    df['updated_at'] = pd.to_datetime(df['updated_at'])
    df['date'] = df['updated_at'].dt.date
    df['hour'] = df['updated_at'].dt.hour
    df['day_of_week'] = df['updated_at'].dt.day_name()

    occupancy_rate = df['status'].value_counts(normalize=True).to_dict()
    total_spots = len(df)
    occupied_spots = len(df[df['status'] == 'occupied'])
    free_spots = total_spots - occupied_spots

    analysis_results = {
        'total_spots': total_spots,
        'occupied_spots': occupied_spots,
        'free_spots': free_spots,
        'occupancy_rate': {
            'available': occupancy_rate.get('available', 0) * 100,
            'occupied': occupancy_rate.get('occupied', 0) * 100
        }
    }

    # Line chart for occupancy over time
    plt.figure(figsize=(10, 5))
    df_occupied = df[df['status'] == 'occupied'].groupby('hour').size()
    df_occupied.plot(kind='line', title='Occupancy Over Time', ylabel='Number of Cars', xlabel='Hour of Day')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    analysis_results['occupancy_over_time_chart'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()  # Close the figure

    # Bar chart for section-wise occupancy
    plt.figure(figsize=(10, 5))
    section_occupancy = df.groupby('section')['status'].value_counts(normalize=True).unstack().fillna(0)
    section_occupancy.plot(kind='bar', stacked=True, title='Section-wise Occupancy', ylabel='Proportion')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    analysis_results['section_occupancy_chart'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()  # Close the figure

    # Histogram for duration of occupancy
    plt.figure(figsize=(10, 5))
    df['duration'] = (df['updated_at'] - df.groupby('spot_number')['updated_at'].transform('min')).dt.total_seconds() / 60
    df['duration'].plot(kind='hist', bins=20, title='Duration of Occupancy', xlabel='Minutes')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    analysis_results['duration_histogram_chart'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()  # Close the figure

    # Bar chart for occupancy by day of the week
    plt.figure(figsize=(10, 5))
    df.groupby('day_of_week')['status'].value_counts(normalize=True).unstack().plot(kind='bar', stacked=True, title='Occupancy by Day of the Week', ylabel='Proportion')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    analysis_results['day_of_week_chart'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()  # Close the figure

    # Pie chart for occupancy rate
    plt.figure(figsize=(6, 5))  # Update figure size to be the same as other charts
    labels = 'Available', 'Occupied'
    sizes = [occupancy_rate.get('available', 0) * 100, occupancy_rate.get('occupied', 0) * 100]
    colors = ['#7EBF7F', '#FF6347']
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('Occupancy Rate')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    analysis_results['occupancy_rate_chart'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()  # Close the figure

    return jsonify(analysis_results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
