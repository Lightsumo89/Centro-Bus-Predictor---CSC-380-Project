from flask import Flask, render_template, jsonify, send_from_directory
import os
import csv
import json

app = Flask(__name__)

CSV_FILE_PATH = 'matched_stops.csv'
PREDICTIONS_FILE_PATH = 'predictions.json'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'js'), filename)

@app.route('/api/stops/<route>', methods=['GET'])
def get_stops(route):
    stops = read_csv()  # Assuming you're reading data from the CSV
    if route != "all":
        stops = [stop for stop in stops if stop["Route"] == route]
    return jsonify(stops)

@app.route('/api/prediction/<stop_id>', methods=['GET'])
def get_prediction(stop_id):
    predictions = read_predictions()
    prediction = next((p for p in predictions if p['stop_id'] == stop_id), None)
    return jsonify(prediction)

def read_csv():
    stops = []
    with open(CSV_FILE_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            stops.append({
                "stop_id": row["stop_id"],
                "stop_lat": float(row["stop_lat"]),
                "stop_lon": float(row["stop_lon"]),
                "Route": row["Route"]
            })
    return stops

def read_predictions():
    with open(PREDICTIONS_FILE_PATH, 'r', encoding='utf-8') as jsonfile:
        return json.load(jsonfile)

if __name__ == '__main__':
    app.run(debug=True)
