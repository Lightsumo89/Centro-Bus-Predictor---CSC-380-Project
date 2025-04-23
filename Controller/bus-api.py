from flask import Flask, request, jsonify, render_template
import os
import pandas as pd
import folium
from database import db_connection_required, get_all_stops, get_all_routes, get_all_buses

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

# ------------------ EXISTING API ROUTES ------------------ #

@app.route('/api/stops', methods=['GET'])
@db_connection_required
def get_stops(conn):
    route_id = request.args.get('route_id')
    stops = get_all_stops(conn, route_id)
    return jsonify(stops)

@app.route('/api/routes', methods=['GET'])
@db_connection_required
def get_routes(conn):
    stop_id = request.args.get('stop_id')
    routes = get_all_routes(conn, stop_id)
    return jsonify(routes)

@app.route('/api/buses', methods=['GET'])
@db_connection_required
def get_buses(conn):
    route_id = request.args.get('route_id')
    stop_id = request.args.get('stop_id')
    buses = get_all_buses(conn, route_id, stop_id)
    return jsonify(buses)

@app.route('/prediction/<input>', methods=['GET'])
@db_connection_required
def get_prediction_placeholder(conn, input):
    return jsonify({"error": "No API Endpoint"}), 500

@app.route('/')
def dev_index():
    return jsonify({
        "name": "Bus System API",
        "version": "1.0",
        "endpoints": {
            "stops": "/api/stops?route_id={route_id}",
            "routes": "/api/routes?stop_id={stop_id}",
            "buses": "/api/buses?route_id={route_id}&stop_id={stop_id}",
            "prediction": "/prediction/{input}"
        }
    })

# ------------------ NEW MAP + ROUTE ROUTES ------------------ #

@app.route('/frontend/routes.html')
def routes():
    return render_template('routes.html', map_file="static/bus_stops_map.html")

@app.route('/get_stops/<route>', methods=['GET'])
def get_stops_for_route(route):
    df = pd.read_csv('matched_stops.csv')
    df.columns = df.columns.str.strip()
    stops = df[df['Route'] == route]['stop_name'].tolist()
    return jsonify(stops)

@app.route('/get_directions/<route_name>', methods=['GET'])
def get_directions(route_name):
    df = pd.read_csv('matched_stops.csv')  # adjust the path
    route_df = df[df['Route'] == route_name]
    
    if route_df.empty:
        return jsonify([])

    directions = set()
    directions.update(route_df['Direction1'].dropna().unique())
    directions.update(route_df['Direction2'].dropna().unique())

    return jsonify(sorted(directions))

@app.route('/frontend/generate_map', methods=['POST'])
def generate_map():
    data = request.get_json()

    route = data.get('route')
    direction = data.get('direction')
    stop = data.get('stop')

    df = pd.read_csv('matched_stops.csv')
    df.columns = df.columns.str.strip()

    map_center = [43.455, -76.532]
    bus_map = folium.Map(location=map_center, zoom_start=13)

    for index, row in df.iterrows():
        if route == row['Route']:
            lat = row['stop_lat']
            lon = row['stop_lon']
            stop_name = row['stop_id']

            folium.Marker(
                location=[lat, lon],
                popup=f"{stop_name}<br>Lat: {lat}, Lon: {lon}",
            ).add_to(bus_map)

    static_folder = 'static'
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    map_path = os.path.join(static_folder, "bus_stops_map.html")
    bus_map.save(map_path)

    return jsonify({
        "map_file": "static/bus_stops_map.html",
        "prediction": f"Next bus arrives in 5 minutes for {stop or 'selected stop'}"
    })

@app.route('/prediction/<stop>/<direction>/<route>', methods=['GET'])
def get_prediction(stop: str, direction: str, route: str):
    prediction = f"Prediction for stop '{stop}' on route '{route}' heading {direction} is 'Next bus arrives in 5 minutes'"
    return jsonify({
        "stop": stop,
        "direction": direction,
        "route": route,
        "prediction": prediction
    })

@app.route('/frontend/index.html')
def index():
    return render_template('index.html')

@app.route('/frontend/contact.html')
def contact():
    return render_template('contact.html')

@app.route('/frontend/faq.html')
def faq():
    return render_template('faq.html')

@app.route('/frontend/time_operation.html')
def time_operation():
    return render_template('time_operation.html')

@app.route('/frontend/oswego_team.html')
def oswego_team():
    return render_template('oswego_team.html')

@app.route('/frontend/how_to_ride.html')
def how_to_ride():
    return render_template('how_to_ride.html')

@app.route('/frontend/passes.html')
def passes():
    return render_template('passes.html')

@app.route('/frontend/updates.html')
def updates():
    return render_template('updates.html')

@app.route('/frontend/plan-your-trip.html')
def plan_your_trip():
    return render_template('plan-your-trip.html')

@app.route('/frontend/fares.html')
def fares():
    return render_template('fares.html')

@app.route('/frontend/news.html')
def news():
    return render_template('news.html')

@app.route('/frontend/alerts.html')
def alerts():
    return render_template('alerts.html')

# ------------------ INITIALIZATION ------------------ #

def generate_empty_map():
    empty_map = folium.Map(location=[43.455, -76.532], zoom_start=13)
    empty_map.save('static/bus_stops_map.html')  # Overwrites with default

generate_empty_map()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
