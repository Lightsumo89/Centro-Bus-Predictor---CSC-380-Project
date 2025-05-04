from flask import Flask, request, jsonify, render_template
import os
import pandas as pd
import folium
from database import db_connection_required, get_all_stops, get_all_routes, get_all_buses
import pandas as pd
import folium
import numpy as np
from hmmlearn import hmm
from scipy.stats import multivariate_normal
import mysql.connector
import jinja2
from datetime import datetime
from error_handlers import register_error_handlers

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

# ------------------ EXISTING API ROUTES ------------------ #

# Register error handlers
register_error_handlers(app)


def get_stop_A(stop, route, direction):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    select_query = "SELECT * FROM Delays WHERE StopID = %s AND Route = %s AND Direction = %s"

    cursor.execute(select_query, (stop, route, direction))

    row = cursor.fetchall()

    stop_A = row[0]  # get stop_id next

    return stop_A

def probabilistic_predict_delay_B(given_delay_A, data):
    # Reshape for HMM training
    X = data.reshape(-1, 2)  # each row is [delay_A, delay_B]

    # Define and train the HMM
    num_states = 2
    model = hmm.GaussianHMM(n_components=num_states, covariance_type="full", n_iter=100)
    model.fit(X)

    # predict delay_B using a probabilistic approach based on state likelihoods.
    means = model.means_  # state-wise [delay_A, delay_B] means
    covars = model.covars_  # state-wise covariance matrices
    priors = model.startprob_  # initial state probabilities

    # compute P(delay_A | state) using the Gaussian likelihood
    state_probs = np.array([
        multivariate_normal.pdf(given_delay_A, mean=means[s, 0], cov=covars[s, 0, 0]) * priors[s]
        for s in range(num_states)
    ])

    # normalize to get P(state | delay_A)
    state_probs /= np.sum(state_probs)

    # Compute weighted prediction for delay_B
    predicted_delay_B = np.sum(state_probs * means[:, 1])

    return predicted_delay_B



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

'''
# Original prediction endpoint from paste.txt - Commented out due to incompleteness
@app.route('/prediction/<stop>/<direction>/<route>', methods=['GET'])
def get_prediction(stop, route, direction):


    data = np.array([
    [1.0, 2.0], [1.3, 2.1], [1.2, 2.0], [1.7, 2.4], [1.4, 2.2], [2.0, 3.1], [1.3, 2.0], [2.1, 3.2], [2.4, 3.2], [2.2, 3.0], [1.9, 2.5], [1.5, 2.4], [2.3, 3.2], [2.5, 3.5], [1.6, 2.7], [1.3, 2.4],
    [1.4, 2.2], [2.3, 3.4], [2.7, 3.4], [2.1, 3.0], [2.3, 3.0], [2.2, 2.9], [1.4, 2.0], [1.3, 2.1] 
    ])

    data = get_data(stop, route, direction)

    given_delay_A = 

    predicted_delay_B = predict_delay_B(given_delay_A, data)
'''


@app.route('/prediction/<stop>/<direction>/<route>', methods=['GET'])
def get_prediction(stop, direction, route):
    return jsonify({
        "message": "Prediction functionality is under development",
        "stop": stop,
        "direction": direction,
        "route": route
    })


@app.route('/generate_map', methods=['POST'])
def generate_map():
    # Retrieve user input from the form
    stop = request.form.get('stop')
    route = request.form.get('route')
    direction = request.form.get('direction')

    try:
        df = pd.read_csv('/Controller/matched_stops.csv')
        df.columns = df.columns.str.strip()

        map_center = [43.455, -76.532]  # Oswego, NY
        bus_map = folium.Map(location=map_center, zoom_start=13)

        for index, row in df.iterrows():
            if route == row['Route']:
                lat = row['stop_lat']
                lon = row['stop_lon']
                stop_name = row['stop_id']

                folium.Marker(
                    location=[lat, lon],
                    popup=f"{stop_name}<br>Lat: {lat}, Lon: {lon}",  # Pop up thingy
                ).add_to(bus_map)

        static_folder = 'static'
        if not os.path.exists(static_folder):
            os.makedirs(static_folder)

        bus_map.save(os.path.join(static_folder, "bus_stops_map.html"))
        print("Map saved as bus_stops_map.html")

        # Make new map
        return render_template('routes.html', map_file="static/bus_stops_map.html")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def dev_index():
    return jsonify({
        "name": "Bus System API",
        "version": "1.1",
        "endpoints": {
            "stops": "/api/stops?route_id={route_id}",
            "routes": "/api/routes?stop_id={stop_id}",
            "buses": "/api/buses?route_id={route_id}&stop_id={stop_id}",
            "prediction": "/prediction/{input}"
        }
    })

# A helper function to handle template rendering with error catching
def safe_render_template(template_name):
    try:
        return render_template(template_name)
    except jinja2.exceptions.TemplateNotFound:
        if not app.debug:
            app.logger.error(f"Template not found: {template_name}")
            return render_template('errors/404.html'), 404
        else:
            raise
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
    return safe_render_template('index.html')


@app.route('/frontend/contact.html')
def contact():
    return safe_render_template('contact.html')


@app.route('/frontend/faq.html')
def faq():
    return safe_render_template('faq.html')


@app.route('/frontend/time_operation.html')
def time_operation():
    return safe_render_template('time_operation.html')


@app.route('/frontend/oswego_team.html')
def oswego_team():
    return safe_render_template('oswego_team.html')


@app.route('/frontend/how_to_ride.html')
def how_to_ride():
    return safe_render_template('how_to_ride.html')


@app.route('/frontend/passes.html')
def passes():
    return safe_render_template('passes.html')


@app.route('/frontend/updates.html')
def updates():
    return safe_render_template('updates.html')


@app.route('/frontend/routes.html')
def routes():
    return safe_render_template('routes.html')

@app.route('/frontend/plan-your-trip.html')
def plan_your_trip():
    return safe_render_template('plan-your-trip.html')


@app.route('/frontend/fares.html')
def fares():
    return safe_render_template('fares.html')


@app.route('/frontend/news.html')
def news():
    return safe_render_template('news.html')


@app.route('/frontend/alerts.html')
def alerts():
    return safe_render_template('alerts.html')

# ------------------ INITIALIZATION ------------------ #

def generate_empty_map():
    empty_map = folium.Map(location=[43.455, -76.532], zoom_start=13)
    empty_map.save('static/bus_stops_map.html')  # Overwrites with default

generate_empty_map()

if __name__ == '__main__':
    #Server configuration
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)