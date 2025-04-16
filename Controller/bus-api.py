from flask import Flask, request, jsonify, render_template
import os
from database import db_connection_required, get_all_stops, get_all_routes, get_all_buses
import pandas as pd
import folium
import numpy as np
from hmmlearn import hmm
from scipy.stats import multivariate_normal
import mysql.connector
from datetime import datetime

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')



def get_stop_A(stop, route, direction):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    select_query = "SELECT * FROM Delays WHERE StopID = %s AND Route = %s AND Direction = %s"

    cursor.execute(select_query, (stop, route, direction))

    row = cursor.fetchall()

    stop_A = row[0]  # get stop_id next

    return stop_A


'''
# Incomplete method
def get_delay_A(stop, route, direction):
    # get delay from LastArrival 
    pass
'''

'''
# Incomplete method
def get_data(stop_A, stop_B, route, direction): # stop_B is the inputted stop, stop_A is the last stop the bus arrived to
    # select rows from database 

    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    select_query = "SELECT * FROM Delays WHERE StopID = %s AND Route = %s AND Direction = %s ORDER BY ArriveTime DESC"

    cursor.execute(select_query, (stop_A, route, direction))

    rows_A = cursor.fetchall()

    cursor.execute(select_query, (stop_B, route, direction))

    rows_B = cursor.fetchall()

    cursor.close()
    db.close()

    # convert to numpy array of [delay_A, delay_B] pairs, need to appropriately match entries in rows_A and rows_B, especially if they contain a different number of entries

    return data
'''

'''
# Incomplete method - has undefined variable 'known_delay_A'
def predict_delay_B(given_delay_A, data):
    # reshape for HMM training
    X = data.reshape(-1, 2)  # each row is [delay_A, delay_B]

    # define and train the HMM
    num_states = 2  
    model = hmm.GaussianHMM(n_components=num_states, covariance_type="full", n_iter=100)
    model.fit(X)

    # predict delay_B given delay_A using the trained HMM.

    # construct a partial observation (only delay_A is known)
    means = model.means_  # Get mean [delay_A, delay_B] for each state
    covariances = model.covars_  # Get covariance matrices

    # Find the most likely state given delay_A
    best_state = np.argmin(np.abs(means[:, 0] - known_delay_A))  # Closest state in delay_A

    # Predict delay_B based on that state's mean
    predicted_delay_B = means[best_state, 1]

    return predicted_delay_B
'''


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
        df = pd.read_csv('matched_stops.csv')
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
        "version": "1.0",
        "endpoints": {
            "stops": "/api/stops?route_id={route_id}",
            "routes": "/api/routes?stop_id={stop_id}",
            "buses": "/api/buses?route_id={route_id}&stop_id={stop_id}",
            "prediction": "/prediction/{input}"
        }
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


@app.route('/frontend/routes.html')
def routes():
    return render_template('routes.html')


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


if __name__ == '__main__':
    # Server configuration
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)