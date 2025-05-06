from flask import Flask, request, jsonify, render_template
import os
from database import db_connection_required, get_all_stops, get_all_routes, get_all_buses, get_db_connection
import pandas as pd
import folium
import numpy as np
from hmmlearn import hmm
from scipy.stats import multivariate_normal
import mysql.connector
import jinja2
from datetime import datetime, timedelta, date, time
from error_handlers import register_error_handlers
import traceback
from collections import defaultdict


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

# Helper prediction functions
def select_table1(route):  # need to account for both directions
    db = get_db_connection()
    if not db:
        print("Database connection failed")
        return []

    try:
        cursor = db.cursor(dictionary=True)
        select_query = "SELECT * FROM LastArrival2 WHERE Route = %s"
        cursor.execute(select_query, (route,))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error in select_table1: {e}")
        return []
    finally:
        if db.is_connected():
            cursor.close()
            db.close()


# Replace the existing select_table2 function with this one
def select_table2(stop_id, route, direction):
    db = get_db_connection()
    if not db:
        print("Database connection failed")
        return []

    try:
        cursor = db.cursor(dictionary=True)
        select_query = "SELECT * FROM Delays_n WHERE StopID = %s AND Route = %s AND Direction = %s"
        cursor.execute(select_query, (stop_id, route, direction))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error in select_table2: {e}")
        return []
    finally:
        if db.is_connected():
            cursor.close()
            db.close()

def select_table3(route, direction, stop_id, hour):
    db = get_db_connection()
    if not db:
        print("Database connection failed")
        return []

    try:
        cursor = db.cursor(dictionary=True)
        select_query = f"SELECT * FROM Delays_n WHERE Route = %s AND Direction = %s AND StopID = %s AND TIME(ArriveTime) >= '{int(hour):02}:00:00' AND TIME(ArriveTime) < '{(int(hour) + 1):02}:00:00'"
        cursor.execute(select_query, (route, direction, stop_id))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error in select_table3: {e}")
        return []
    finally:
        if db.is_connected():
            cursor.close()
            db.close()

def select_table4(route):
    db = get_db_connection()
    if not db:
        print("Database connection failed")
        return []

    try:
        cursor = db.cursor(dictionary=True)
        select_query = f"SELECT * FROM Delays_n WHERE Route = %s ORDER BY ID, ArriveTime" # add order by id and arrive time
        cursor.execute(select_query, (route,))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error in select_table4: {e}")
        return []
    finally:
        if db.is_connected():
            cursor.close()
            db.close()


def contains_stop(id_array, stop_id): # return arrive time if stop_id is in id_array, else return None
    for arrival in id_array:
        if stop_id == arrival.get("StopID"):
            return arrival

    return None

"""
def get_bus_arrival_prediction(stop_id, route, direction):
    direction = str(direction)
    stop_id = str(stop_id)
    route = str(route)

    last_arrivals = select_table1(route)  # get the stops of the last arrived buses on the route

    predicted_times = []

    if len(last_arrivals) == 0:
        print("no bus on route")

    else:
        rows_user_input = select_table2(stop_id, route, direction)

        ctr = 0
        total_sum = 0

        for last_arrival in last_arrivals:
            print(f"Last Arrival: {last_arrival.get('ArriveTime')}")

            last_arrival_time = last_arrival.get("ArriveTime")

            if last_arrival.get("StopID") == stop_id:  # last arrival is the same as user inputted stop
                # get all of the arrivals for that stop and check for same day and ID greater than 1
                print(f"Rows User Input 1: {rows_user_input}")
                print(f"Rows User Input 2: {rows_user_input}")

                for row_user_input1 in rows_user_input:
                    for row_user_input2 in rows_user_input:
                        if row_user_input2.get("ID") == row_user_input1.get("ID") + 1 and row_user_input1.get(
                                "ArriveTime").date() == row_user_input2.get("ArriveTime").date():
                            ctr += 1

                            total_sum += (row_user_input2.get("ArriveTime") - row_user_input1.get(
                                "ArriveTime")).total_seconds()

                            print(f"User Input 1 ArriveTime: {row_user_input1.get('ArriveTime')}")
                            print(f"User Input 2 ArriveTime: {row_user_input2.get('ArriveTime')}")

                            print(
                                f"Difference: {(row_user_input2.get('ArriveTime') - row_user_input1.get('ArriveTime')).total_seconds()}, User Input 1 ID: {row_user_input1.get('ID')}, User Input 2 ID: {row_user_input2.get('ID')}")

                            break



            else:
                last_arrival_time = last_arrival.get("ArriveTime")

                rows_last_arrival = select_table2(last_arrival.get("StopID"), last_arrival.get("Route"),
                                                  last_arrival.get("Direction"))

                print(f"Rows Last Arrival: {rows_last_arrival}")
                print(f"Rows User Input: {rows_user_input}")

                for row_last_arrival in rows_last_arrival:
                    for row_user_input in rows_user_input:  # could do a check for an id one less or more for different directions for multiple round trips
                        if row_user_input.get("ID") == row_last_arrival.get("ID") and row_user_input.get(
                                "ArriveTime") > row_last_arrival.get("ArriveTime"):
                            ctr += 1

                            total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get(
                                "ArriveTime")).total_seconds()

                            print(f"Last Arrival Row ArriveTime: {row_last_arrival.get('ArriveTime')}")
                            print(f"User Input Row ArriveTime: {row_user_input.get('ArriveTime')}")

                            print(
                                f"Difference: {(row_user_input.get('ArriveTime') - row_last_arrival.get('ArriveTime')).total_seconds()}, User Input ID: {row_user_input.get('ID')}, Last Arrival ID: {row_last_arrival.get('ID')}")

                            break

                        elif row_user_input.get("ID") > row_last_arrival.get("ID"):
                            break

                if ctr == 0:
                    # get consecutive round trips, have to check for a row_last_arrival that has an ID 1 greater than a row_user_input]
                    for row_user_input in rows_user_input:
                        for row_last_arrival in rows_last_arrival:
                            if (row_user_input.get("ID") == row_last_arrival.get("ID") + 1 and
                                    row_user_input.get("ArriveTime") > row_last_arrival.get("ArriveTime") and
                                    row_user_input.get("ArriveTime").date() == row_last_arrival.get("ArriveTime").date()
                            ):
                                ctr += 1

                                total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get(
                                    "ArriveTime")).total_seconds()

                                print(f"Last Arrival Row ArriveTime: {row_last_arrival.get('ArriveTime')}")
                                print(f"User Input Row ArriveTime: {row_last_arrival.get('ArriveTime')}")

                                print(
                                    f"Difference: {(row_user_input.get('ArriveTime') - row_last_arrival.get('ArriveTime')).total_seconds()}, User Input ID: {row_user_input.get('ID')}, Last Arrival ID: {row_last_arrival.get('ID')}")

                                break

            if ctr == 0:
                print("no data")

            else:
                predicted_time = last_arrival_time + timedelta(seconds=(total_sum / ctr))

                print(f"Predicted Time: {predicted_time}")

                predicted_times.append(predicted_time)

    return predicted_times
"""


def get_bus_arrival_prediction(stop_id, route, direction, day, month, year, input_hour):
    input_date = date(int(year), int(month), int(day))
    print(input_date)

    if datetime.now().date() != input_date:
        hour = input_hour

    if datetime.now().date() != input_date:
        rows_hour = select_table3(route, direction, stop_id, hour)
        print(rows_hour)

        if len(rows_hour) == 0:
            return "no bus for given time"

        else:
            timestamps = [
                row_hour.get("ArriveTime").hour * 3600 + row_hour.get("ArriveTime").minute * 60 + row_hour.get(
                    "ArriveTime").second for row_hour in rows_hour]

            average_time = int(sum(timestamps) / len(timestamps))

            predicted_time = time(hour=average_time // 3600,
                                  minute=(average_time % 3600) // 60,
                                  second=average_time % 60
                                  )

            predicted_time = datetime.combine(input_date, predicted_time)

            return predicted_time

    else:
        last_arrivals = select_table1(route)  # get the stops of the last arrived buses on the route

        predicted_times = []

        if len(last_arrivals) == 0:
            return "no bus on route"

        else:
            rows_user_input = select_table2(stop_id, route, direction)

            ctr = 0
            total_sum = 0

            for last_arrival in last_arrivals:
                last_arrival_time = last_arrival.get("ArriveTime")

                rows_last_arrival = select_table2(last_arrival.get("StopID"), last_arrival.get("Route"),
                                                  last_arrival.get("Direction"))

                for row_last_arrival in rows_last_arrival:
                    for row_user_input in rows_user_input:  # could do a check for an id one less or more for different directions for multiple round trips
                        if row_user_input.get("ID") == row_last_arrival.get("ID") and row_user_input.get(
                                "ArriveTime") > row_last_arrival.get("ArriveTime"):
                            ctr += 1

                            total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get(
                                "ArriveTime")).total_seconds()

                            break

                        elif row_user_input.get("ID") > row_last_arrival.get("ID"):
                            break

                if ctr == 0:
                    consecutive_round_trips = defaultdict(list)

                    consecutive_round_trips_day = []  # array of arrivals in consecutive round trips per day (keep track of the max arrival time of all of them)

                    rows_route = select_table4(route)

                    arrive_day = rows_route[0].get("ArriveTime").date()
                    traversal_id = rows_route[0].get("ID")

                    b = False

                    for row_route in rows_route:
                        if row_route.get("ArriveTime").date() != arrive_day:
                            if any(row_route.get("ID") == c[-1][-1].get("ID") for c in
                                   consecutive_round_trips_day):  # include the next day's 0:00:00 hour in the previous flag, set a flag so that the change in id clears the consecutive_round_trips_day array, loop through individually

                                for c in consecutive_round_trips_day:
                                    if row_route.get("ID") == c[-1][-1].get("ID"):  # maximum id array in c array
                                        c[-1].append(row_route)  # last array in c adds an arrival with the same id

                                        break

                                b = True

                            else:  # the id is different from the previous day to the first in the next day so clear the array
                                # print("different day")

                                for c in consecutive_round_trips_day:  # c is an array containing the arrivals of  consecutive round trips (could include those with just 1 round trip)
                                    if len(c) >= 2:  # c contains each arrival, need to check if number of different ids is greater than or equal to 2
                                        consecutive_round_trips[arrive_day].append(c)  # an array of arrays

                                consecutive_round_trips_day.clear()

                                consecutive_round_trips_day.append([[row_route]])

                                arrive_day = row_route.get("ArriveTime").date()  # update arrive_day
                                traversal_id = row_route.get("ID")  # update traversal_id

                        elif row_route.get("ID") != traversal_id:  # check where to append it
                            if b:  # clear the consecutive_round_trips array like in the else above and reset b to False
                                # print("different day")

                                for c in consecutive_round_trips_day:  # c is an array containing the arrivals of  consecutive round trips (could include those with just 1 round trip)
                                    if len(c) >= 2:  # c contains each arrival, need to check if number of different ids is greater than or equal to 2
                                        consecutive_round_trips[arrive_day].append(c)  # an array of arrays

                                consecutive_round_trips_day.clear()

                                consecutive_round_trips_day.append([[row_route]])

                                arrive_day = row_route.get("ArriveTime").date()  # update arrive_day
                                traversal_id = row_route.get("ID")  # update traversal_id

                                b = False

                            else:
                                # print("different id") # add debug statements like this

                                non_intersecting_round_trips = []

                                for c in consecutive_round_trips_day:  # look for non intersecting round trips and take the minimum of the differences from the max and min
                                    max_round_trip = c[-1][-1]  # maximum of each last array in c array

                                    if row_route.get("ArriveTime") > max_round_trip.get("ArriveTime"):
                                        non_intersecting_round_trips.append(max_round_trip)

                                # find the minimum and put it in the correct c array in consecutive_round_trips_day, check if within 20 minutes

                                if len(non_intersecting_round_trips) == 0:
                                    consecutive_round_trips_day.append(
                                        [[row_route]])  # append to new consecutive round trip array of id arrays

                                else:
                                    max_max_round_trip = max(non_intersecting_round_trips,
                                                             key=lambda x: x.get("ArriveTime"))  # this needs max

                                    if (row_route.get("ArriveTime") - max_max_round_trip.get(
                                            "ArriveTime")).total_seconds() <= 1200:  # remove 1200 conditional
                                        # append to correct c array, get id of the min and look for that id in the c arrays
                                        max_max_round_trip_id = max_max_round_trip.get("ID")

                                        for c in consecutive_round_trips_day:
                                            if max_max_round_trip_id == c[-1][-1].get("ID"):
                                                c.append(
                                                    [row_route])  # create a new id array in c for the next id for a consecutive round trip

                                                break

                                    else:
                                        # append to a new array, a separate consecutive round trip
                                        consecutive_round_trips_day.append([[row_route]])

                                    # update traversal_id
                                    traversal_id = row_route.get("ID")

                        else:  # same ID, just append it to the most recent appended from the else if
                            if len(consecutive_round_trips_day) == 0:  # first route of the day
                                consecutive_round_trips_day.append([[row_route]])

                            else:
                                for c in consecutive_round_trips_day:
                                    if row_route.get("ID") == c[-1][-1].get("ID"):  # maximum id array in c array
                                        c[-1].append(row_route)  # last array in c adds an arrival with the same id

                                        break

                    for day, cr_list in consecutive_round_trips.items():
                        for cr in cr_list:  # cr is each consecutive round trip, containing arrays of the arrivals, where all with the same id go in an array
                            for i in range(len(cr_list) - 1):
                                arrive_time_i1 = contains_stop(cr[i], last_arrival.get(
                                    "StopID"))  # cr[i] is each id array in cr

                                if arrive_time_i1 is not None:  # stop_id inputted from user
                                    arrive_time_i2 = contains_stop(cr[i + 1], stop_id)

                                    if arrive_time_i2 is not None:
                                        ctr += 1

                                        total_sum += (arrive_time_i2.get("ArriveTime") - arrive_time_i1.get(
                                            "ArriveTime")).total_seconds()

                                    else:
                                        continue

                                else:
                                    continue

                if (ctr == 0):
                    return "no bus for given time"

                else:
                    predicted_time = last_arrival_time + timedelta(seconds=(total_sum / ctr))

                    predicted_times.append(predicted_time)

            if len(predicted_times) == 0:
                return "no bus on route"
            else:
                # Convert the datetime object to a consistent string format before returning
                predicted_datetime = min(predicted_times)
                return predicted_datetime.strftime("%Y-%m-%d %H:%M:%S")


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
def get_prediction_endpoint(input):
    # Parse the input parameters - assuming input format is "route/stop_id/direction"
    print(f"[DEBUG] Prediction endpoint called with input: '{input}'")
    try:
        route, stop_id, direction = input.split('/')
        print(f"[DEBUG] Parsed input: route = '{route}', stop_id = '{stop_id}', direction = '{direction}'")
        prediction = get_bus_arrival_prediction(stop_id, route, direction)
        print(f"[DEBUG] Prediction result: {prediction}")
        return jsonify({"prediction": prediction})
    except Exception as e:
        error_msg = f"Error in prediction endpoint: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(traceback.format_exc())
        return jsonify({"error": error_msg}), 500


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


@app.route('/get_stops/<route>', methods=['GET'])
def get_stops_for_route(route):
    direction = request.args.get('direction')  # Accept direction as a query param
    df = pd.read_csv('../static/matched_stops.csv')
    print(f"[DEBUG] Direction from query: {direction}")
    df.columns = df.columns.str.strip()

    # First filter by route
    filtered_df = df[df['Route'] == route].copy()

    # Convert Selector to numeric, handling NaN values
    filtered_df['Selector'] = pd.to_numeric(filtered_df['Selector'], errors='coerce').fillna(-1).astype(int)

    # Filter by direction parameter
    if direction:
        print(f"[DEBUG] Filtering by direction: {direction}")
        if direction == 'FROM HUB' or direction == 'FROM DOWNTOWN':
            filtered_df = filtered_df[filtered_df['Selector'] == 0]
        elif direction == 'TO HUB' or direction == 'TO DOWNTOWN':
            filtered_df = filtered_df[filtered_df['Selector'] == 1]
        else:
            # Try to parse the direction as a number
            try:
                dir_num = int(direction)
                filtered_df = filtered_df[filtered_df['Selector'] == dir_num]
            except ValueError:
                # If not a number, try to match with Direction1 or Direction2
                filtered_df = filtered_df[
                    (filtered_df['Direction1'] == direction) |
                    (filtered_df['Direction2'] == direction)
                    ]

    # Set DirectionName based on Selector value
    filtered_df['DirectionName'] = filtered_df.apply(
        lambda row: row['Direction1'] if row['Selector'] == 0 else row['Direction2'],
        axis=1
    )

    # Select only the needed columns and remove duplicates
    stops = filtered_df[['stop_name', 'stop_id', 'DirectionName', 'Selector']].drop_duplicates()
    stops_list = stops.to_dict(orient='records')

    print(f"[DEBUG] Returning {len(stops_list)} stops for route {route} with direction {direction}")
    return jsonify(stops_list)


@app.route('/get_directions/<route_name>', methods=['GET'])
def get_directions(route_name):
    df = pd.read_csv('../static/matched_stops.csv')
    df.columns = df.columns.str.strip()
    route_df = df[df['Route'] == route_name]

    if route_df.empty:
        return jsonify([])

    directions = []
    direction1 = route_df['Direction1'].dropna().iloc[0] if 'Direction1' in route_df.columns and not route_df['Direction1'].dropna().empty else "Direction 1"
    direction2 = route_df['Direction2'].dropna().iloc[0] if 'Direction2' in route_df.columns and not route_df['Direction2'].dropna().empty else "Direction 2"

    directions.append({"value": "0", "name": direction1})
    directions.append({"value": "1", "name": direction2})

    return jsonify(directions)


def get_project_root():
    """Returns the absolute path to the project root directory"""
    # Get the directory of the current file (bus-api.py)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))

    # In production, we're in the Controller directory, so project root is one level up
    project_root = os.path.dirname(current_file_dir)

    print(f"[DEBUG] Current file directory: {current_file_dir}")
    print(f"[DEBUG] Project root resolved to: {project_root}")

    # Fall back to using an absolute path if the above doesn't work
    if not os.path.exists(os.path.join(project_root, 'static')):
        print(f"[DEBUG] Static directory not found at {os.path.join(project_root, 'static')}")
        # Try alternative - go up one more level (in case we're in Controller/something)
        project_root = os.path.dirname(project_root)
        print(f"[DEBUG] Trying alternative project root: {project_root}")

        # If still no static dir, use the home directory + bus-tracking-app
        if not os.path.exists(os.path.join(project_root, 'static')):
            home_dir = os.path.expanduser('~')
            project_root = os.path.join(home_dir, 'bus-tracking-app')
            print(f"[DEBUG] Using home directory fallback: {project_root}")

    return project_root



@app.route('/frontend/generate_map', methods=['POST'])
def generate_map():
    try:
        print(f"[DEBUG] Starting map generation")
        print(f"[DEBUG] Current working directory: {os.getcwd()}")

        # Get request data
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            print(f"[DEBUG] Received data: {data}")
        except Exception as req_err:
            print(f"[ERROR] Failed to parse request data: {str(req_err)}")
            data = {}

        # Get route parameters
        route = data.get('route', '')
        direction = data.get('direction', '')
        direction_text = data.get('directionText', '')
        stop = data.get('stop', '')
        stop_id = data.get('stopId', '')

        # Get datetime parameters
        selected_datetime_str = str(
            data.get('selected_datetime') or data.get('selected_hour') or datetime.today().strftime('%Y-%m-%d %H:%M'))
        year = selected_datetime_str.split('-')[0] if '-' in selected_datetime_str else None
        month = selected_datetime_str.split('-')[1] if '-' in selected_datetime_str else None
        whole = selected_datetime_str.split('-')[2] if '-' in selected_datetime_str else None
        day = whole.split(' ')[0] if ' ' in whole and whole else None
        time_hour = selected_datetime_str.split(' ')[1] if ' ' in selected_datetime_str else None
        hour = time_hour.split(':')[0] if time_hour and ':' in time_hour else None

        print(f"[DEBUG] Route: {route}, Direction: {direction}, Stop: {stop}, Stop ID: {stop_id}")
        print(f"[DEBUG] Date params: year={year}, month={month}, day={day}, hour={hour}")

        # Get project root and verify paths
        project_root = get_project_root()
        static_dir = os.path.join(project_root, 'static')
        csv_path = os.path.join(static_dir, 'matched_stops.csv')
        map_path = os.path.join(static_dir, 'bus_stops_map.html')

        print(f"[DEBUG] Static directory: {static_dir}")
        print(f"[DEBUG] CSV path: {csv_path}")
        print(f"[DEBUG] Map path: {map_path}")

        # Create static directory if it doesn't exist
        if not os.path.exists(static_dir):
            print(f"[DEBUG] Creating static directory")
            try:
                os.makedirs(static_dir)
            except Exception as mkdir_err:
                print(f"[ERROR] Failed to create static directory: {str(mkdir_err)}")

        # Check if CSV exists
        if not os.path.exists(csv_path):
            print(f"[ERROR] CSV file not found at {csv_path}")
            # List files in the directory to help debug
            try:
                print(f"[DEBUG] Files in {static_dir}: {os.listdir(static_dir)}")
            except Exception as list_err:
                print(f"[ERROR] Failed to list directory: {str(list_err)}")

            # Create an empty map as fallback
            bus_map = folium.Map(location=[43.455, -76.532], zoom_start=13)
            try:
                bus_map.save(map_path)
                print(f"[DEBUG] Saved fallback map to {map_path}")
            except Exception as save_err:
                print(f"[ERROR] Failed to save fallback map: {str(save_err)}")

            return jsonify({
                "map_file": "static/bus_stops_map.html",
                "error": "CSV file not found"
            })

        # Try to find stop_id if needed
        if stop_id is None and stop is not None and route:
            try:
                df = pd.read_csv(csv_path)
                df.columns = df.columns.str.strip()

                dir_filter = [0, 1]  # Default to all selectors
                if direction == '0':
                    dir_filter = [0]
                elif direction == '1':
                    dir_filter = [1]

                # Convert Selector column to numeric
                df['Selector'] = pd.to_numeric(df['Selector'], errors='coerce').fillna(-1).astype(int)

                # Filter by route and direction
                filtered = df[(df['Route'] == route) &
                              (df['Selector'].isin(dir_filter)) &
                              (df['stop_name'] == stop)]

                if not filtered.empty:
                    stop_id = filtered.iloc[0]['stop_id']
                    print(f"[DEBUG] Found stop_id: {stop_id} for stop {stop}")
            except Exception as e:
                print(f"[ERROR] Error finding stop_id: {str(e)}")

        # Read the CSV file
        try:
            df = pd.read_csv(csv_path)
            print(f"[DEBUG] CSV loaded with {len(df)} rows")
            print(f"[DEBUG] CSV columns: {df.columns.tolist()}")

            # Clean column names
            df.columns = df.columns.str.strip()

            # Create a copy to avoid SettingWithCopyWarning
            df = df.copy()

            # Handle Selector column
            if 'Selector' in df.columns:
                df['Selector'] = pd.to_numeric(df['Selector'], errors='coerce').fillna(-1).astype(int)
                print(f"[DEBUG] Processed Selector column")
            else:
                print(f"[WARNING] 'Selector' column not found in CSV")
        except Exception as csv_err:
            print(f"[ERROR] Failed to process CSV: {str(csv_err)}")
            # Create an empty map as fallback
            bus_map = folium.Map(location=[43.455, -76.532], zoom_start=13)
            try:
                bus_map.save(map_path)
            except Exception as save_err:
                print(f"[ERROR] Failed to save fallback map: {str(save_err)}")

            return jsonify({
                "map_file": "static/bus_stops_map.html",
                "error": f"Failed to process CSV: {str(csv_err)}"
            })

        # Filter data
        try:
            # Filter by route
            if route:
                filtered_df = df[df['Route'] == route].copy()
                print(f"[DEBUG] After route filter: {len(filtered_df)} rows")
            else:
                filtered_df = df.copy()

            # Filter by direction
            if direction == '0':
                filtered_df = filtered_df[filtered_df['Selector'] == 0]
            elif direction == '1':
                filtered_df = filtered_df[filtered_df['Selector'] == 1]

            print(f"[DEBUG] After direction filter: {len(filtered_df)} rows")

            # Calculate map center
            map_center = [43.455, -76.532]  # Default center
            if len(filtered_df) > 0 and 'stop_lat' in filtered_df.columns and 'stop_lon' in filtered_df.columns:
                lat_values = filtered_df['stop_lat'].dropna()
                lon_values = filtered_df['stop_lon'].dropna()

                if len(lat_values) > 0 and len(lon_values) > 0:
                    avg_lat = lat_values.mean()
                    avg_lon = lon_values.mean()
                    map_center = [avg_lat, avg_lon]
        except Exception as filter_err:
            print(f"[ERROR] Failed during data filtering: {str(filter_err)}")
            filtered_df = pd.DataFrame()
            map_center = [43.455, -76.532]  # Default center

        # Create map
        try:
            bus_map = folium.Map(location=map_center, zoom_start=13)
            print(f"[DEBUG] Created base map centered at {map_center}")

            # Add markers
            marker_count = 0
            for _, row in filtered_df.iterrows():
                try:
                    # Validate coordinates
                    if 'stop_lat' not in row or 'stop_lon' not in row:
                        continue

                    lat = float(row['stop_lat'])
                    lon = float(row['stop_lon'])

                    # Skip invalid coordinates
                    if pd.isna(lat) or pd.isna(lon):
                        continue

                    stop_name = str(row.get('stop_name', 'Unknown Stop'))
                    stop_id_val = str(row.get('stop_id', 'Unknown ID'))

                    popup_text = f"{stop_name}<br>ID: {stop_id_val}<br>Lat: {lat}, Lon: {lon}"

                    # Use red icon for selected stop
                    if stop and stop == stop_name:
                        folium.Marker(
                            location=[lat, lon],
                            popup=popup_text,
                            tooltip=stop_name,
                            icon=folium.Icon(color='red')
                        ).add_to(bus_map)
                    else:
                        folium.Marker(
                            location=[lat, lon],
                            popup=popup_text,
                            tooltip=stop_name
                        ).add_to(bus_map)

                    marker_count += 1
                except Exception as marker_err:
                    print(f"[ERROR] Failed to add marker for {row.get('stop_name', 'unknown')}: {str(marker_err)}")
                    continue

            print(f"[DEBUG] Added {marker_count} markers to map")
        except Exception as map_err:
            print(f"[ERROR] Failed to create map: {str(map_err)}")
            bus_map = folium.Map(location=[43.455, -76.532], zoom_start=13)

        # Save map
        try:
            bus_map.save(map_path)
            print(f"[DEBUG] Successfully saved map to {map_path}")
        except Exception as save_err:
            print(f"[ERROR] Failed to save map: {str(save_err)}")
            return jsonify({
                "map_file": "static/bus_stops_map.html",
                "error": f"Failed to save map: {str(save_err)}"
            })

        # Get prediction
        prediction = "No prediction available"
        if route and stop_id:
            try:
                # Decide which direction value to use for prediction
                prediction_direction = direction_text if direction_text else direction
                print(
                    f"[DEBUG] Getting prediction for stop_id={stop_id}, route={route}, direction={prediction_direction}")

                # Call get_bus_arrival_prediction with datetime parameters
                prediction = get_bus_arrival_prediction(stop_id, route, prediction_direction, day, month, year, hour)
                string_prediction = str(prediction).split(' ')[1] if ' ' in str(prediction) else str(prediction)

                print(f"[DEBUG] Prediction result: {string_prediction}")
            except Exception as pred_err:
                print(f"[ERROR] Prediction error: {str(pred_err)}")

        return jsonify({
            "map_file": "static/bus_stops_map.html",
            "prediction": string_prediction if 'string_prediction' in locals() else prediction,
            "markers_count": marker_count
        })

    except Exception as e:
        print(f"[ERROR] Unhandled exception in generate_map: {str(e)}")
        print(traceback.format_exc())

        # Always return something, even in case of errors
        project_root = get_project_root()
        map_path = os.path.join(project_root, 'static', 'bus_stops_map.html')

        try:
            bus_map = folium.Map(location=[43.455, -76.532], zoom_start=13)
            bus_map.save(map_path)
        except Exception as final_err:
            print(f"[ERROR] Failed final fallback: {str(final_err)}")

        return jsonify({
            "map_file": "static/bus_stops_map.html",
            "error": f"Unhandled exception: {str(e)}"
        })


# Test endpoint for direct prediction testing
@app.route('/test-prediction/<stop_id>/<route>/<direction>')
def test_prediction(stop_id, route, direction):
    print(f"[DEBUG] Test prediction called with stop_id={stop_id}, route={route}, direction={direction}")
    result = get_bus_arrival_prediction(stop_id, route, direction)
    return jsonify({
        "stop_id": stop_id,
        "route": route,
        "direction": direction,
        "result": result
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

@app.route('/frontend/routes.html?filename=routes/Osw10-Osw11.pdf')
def Osw10_Osw11():
    return safe_render_template('routes.html?filename=routes/Osw10-Osw11.pdf')

@app.route('/frontend/how_to_ride.html')
def how_to_ride():
    return safe_render_template('how_to_ride.html')


@app.route('/frontend/passes.html')
def passes():
    return safe_render_template('passes.html')


@app.route('/frontend/updates.html')
def updates():
    return safe_render_template('updates.html')

@app.route('/frontend/help.html')
def help():
    return render_template('help.html')

# @app.route('/frontend/routes.html')
# def routes():
#     return render_template('routes.html', map_file="static/bus_stops_map.html")

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
    """Create an empty map file in the static directory"""
    # Create the static directory if it doesn't exist
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    print(f"Static directory path: {static_dir}")

    # Ensure the directory exists
    if not os.path.exists(static_dir):
        try:
            os.makedirs(static_dir)
            print(f"Created static directory at {static_dir}")
        except Exception as e:
            print(f"Error creating static directory: {e}")
            # Fall back to current directory if we can't create the proper path
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            if not os.path.exists(static_dir):
                os.makedirs(static_dir)

    # Create and save the empty map
    empty_map = folium.Map(location=[43.455, -76.532], zoom_start=13)
    map_path = os.path.join(static_dir, 'bus_stops_map.html')

    try:
        empty_map.save(map_path)
        print(f"Empty map created at {map_path}")
    except Exception as e:
        print(f"Error saving empty map: {e}")
generate_empty_map()

if __name__ == '__main__':
    #Server configuration
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
