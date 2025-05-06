import mysql.connector
from flask import Flask, request, jsonify, render_template
import pandas as pd
import folium
from datetime import datetime, timedelta
import os
import traceback
from collections import defaultdict
from datetime import date, time


DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD",
    "port": 3306
}


app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')


def select_table1(route): # need to account for both directions
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary = True)

    select_query = "SELECT * FROM LastArrival2 WHERE Route = %s"

    cursor.execute(select_query, (route,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def select_table2(stop_id, route, direction):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary = True)

    select_query = "SELECT * FROM Delays_n WHERE StopID = %s AND Route = %s AND Direction = %s ORDER BY ID" # add order by id

    cursor.execute(select_query, (stop_id, route, direction))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def select_table3(route, direction, stop_id, hour):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary = True)

    select_query = f"SELECT * FROM Delays_n WHERE Route = %s AND Direction = %s AND StopID = %s AND TIME(ArriveTime) >= '{int(hour):02}:00:00' AND TIME(ArriveTime) < '{(int(hour) + 1):02}:00:00'"

    cursor.execute(select_query, (route, direction, stop_id))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def select_table4(route):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary = True)

    select_query = f"SELECT * FROM Delays_n WHERE Route = %s ORDER BY ID, ArriveTime" # add order by id and arrive time

    cursor.execute(select_query, (route,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def contains_stop(id_array, stop_id): # return arrive time if stop_id is in id_array, else return None
    for arrival in id_array:
        if stop_id == arrival.get("StopID"):
            return arrival

    return None 


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
            timestamps = [row_hour.get("ArriveTime").hour * 3600 + row_hour.get("ArriveTime").minute * 60 + row_hour.get("ArriveTime").second for row_hour in rows_hour]

            average_time = int(sum(timestamps) / len(timestamps))

            predicted_time = time(hour=average_time // 3600,
                                  minute=(average_time % 3600) // 60,
                                  second=average_time % 60
                             )

            predicted_time = datetime.combine(input_date, predicted_time)

            return predicted_time

    else:
        last_arrivals = select_table1(route) # get the stops of the last arrived buses on the route

        predicted_times = []

        if len(last_arrivals) == 0:
            return "no bus on route"
    
        else:
            rows_user_input = select_table2(stop_id, route, direction)

            ctr = 0
            total_sum = 0

            for last_arrival in last_arrivals:
                last_arrival_time = last_arrival.get("ArriveTime")

                rows_last_arrival = select_table2(last_arrival.get("StopID"), last_arrival.get("Route"), last_arrival.get("Direction"))

                for row_last_arrival in rows_last_arrival:
                    for row_user_input in rows_user_input: # could do a check for an id one less or more for different directions for multiple round trips
                        if row_user_input.get("ID") == row_last_arrival.get("ID") and row_user_input.get("ArriveTime") > row_last_arrival.get("ArriveTime"):
                            ctr += 1

                            total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get("ArriveTime")).total_seconds()

                            break

                        elif row_user_input.get("ID") > row_last_arrival.get("ID"):
                            break


                if ctr == 0:
                    consecutive_round_trips = defaultdict(list)

                    consecutive_round_trips_day = [] # array of arrivals in consecutive round trips per day (keep track of the max arrival time of all of them)

                    rows_route = select_table4(route)

                    arrive_day = rows_route[0].get("ArriveTime").date()
                    traversal_id = rows_route[0].get("ID")

                    b = False

                    for row_route in rows_route:
                        if row_route.get("ArriveTime").date() != arrive_day:
                            if any(row_route.get("ID") == c[-1][-1].get("ID") for c in consecutive_round_trips_day): #include the next day's 0:00:00 hour in the previous flag, set a flag so that the change in id clears the consecutive_round_trips_day array, loop through individually

                                for c in consecutive_round_trips_day:
                                    if row_route.get("ID") == c[-1][-1].get("ID"): # maximum id array in c array
                                        c[-1].append(row_route) # last array in c adds an arrival with the same id

                                        break

                                b = True

                            else: # the id is different from the previous day to the first in the next day so clear the array
                                # print("different day")

                                for c in consecutive_round_trips_day: # c is an array containing the arrivals of  consecutive round trips (could include those with just 1 round trip)
                                    if len(c) >= 2: # c contains each arrival, need to check if number of different ids is greater than or equal to 2
                                        consecutive_round_trips[arrive_day].append(c) # an array of arrays
                         
                                consecutive_round_trips_day.clear()

                                consecutive_round_trips_day.append([[row_route]])

                                arrive_day = row_route.get("ArriveTime").date() # update arrive_day
                                traversal_id = row_route.get("ID") # update traversal_id

                        elif row_route.get("ID") != traversal_id: # check where to append it
                            if b: # clear the consecutive_round_trips array like in the else above and reset b to False
                                # print("different day")

                                for c in consecutive_round_trips_day: # c is an array containing the arrivals of  consecutive round trips (could include those with just 1 round trip)
                                    if len(c) >= 2: # c contains each arrival, need to check if number of different ids is greater than or equal to 2
                                        consecutive_round_trips[arrive_day].append(c) # an array of arrays
                     
                                consecutive_round_trips_day.clear()

                                consecutive_round_trips_day.append([[row_route]])

                                arrive_day = row_route.get("ArriveTime").date() # update arrive_day
                                traversal_id = row_route.get("ID") # update traversal_id

                                b = False

                            else:
                                # print("different id") # add debug statements like this

                                non_intersecting_round_trips = []

                                for c in consecutive_round_trips_day: # look for non intersecting round trips and take the minimum of the differences from the max and min
                                    max_round_trip = c[-1][-1] # maximum of each last array in c array

                                    if row_route.get("ArriveTime") > max_round_trip.get("ArriveTime"):
                                        non_intersecting_round_trips.append(max_round_trip)
                    
                                # find the minimum and put it in the correct c array in consecutive_round_trips_day, check if within 20 minutes

                                if len(non_intersecting_round_trips) == 0:
                                    consecutive_round_trips_day.append([[row_route]]) # append to new consecutive round trip array of id arrays

                                else:
                                    max_max_round_trip = max(non_intersecting_round_trips, key=lambda x: x.get("ArriveTime")) # this needs max

                                    if (row_route.get("ArriveTime") - max_max_round_trip.get("ArriveTime")).total_seconds() <= 1200: # remove 1200 conditional
                                        # append to correct c array, get id of the min and look for that id in the c arrays
                                        max_max_round_trip_id = max_max_round_trip.get("ID")

                                        for c in consecutive_round_trips_day:
                                            if max_max_round_trip_id == c[-1][-1].get("ID"):
                                                c.append([row_route]) # create a new id array in c for the next id for a consecutive round trip

                                                break

                                    else:
                                        # append to a new array, a separate consecutive round trip
                                        consecutive_round_trips_day.append([[row_route]])

                                    # update traversal_id
                                    traversal_id = row_route.get("ID")

                        else: # same ID, just append it to the most recent appended from the else if
                            if len(consecutive_round_trips_day) == 0: # first route of the day
                                consecutive_round_trips_day.append([[row_route]])

                            else:
                                for c in consecutive_round_trips_day:
                                    if row_route.get("ID") == c[-1][-1].get("ID"): # maximum id array in c array
                                        c[-1].append(row_route) # last array in c adds an arrival with the same id

                                        break
 

                    for day, cr_list in consecutive_round_trips.items():
                        for cr in cr_list: # cr is each consecutive round trip, containing arrays of the arrivals, where all with the same id go in an array
                            for i in range(len(cr_list) - 1): 
                                arrive_time_i1 = contains_stop(cr[i], last_arrival.get("StopID")) # cr[i] is each id array in cr

                                if arrive_time_i1 is not None:  # stop_id inputted from user
                                    arrive_time_i2 = contains_stop(cr[i + 1], stop_id)

                                    if arrive_time_i2 is not None:
                                        ctr += 1

                                        total_sum += (arrive_time_i2.get("ArriveTime") - arrive_time_i1.get("ArriveTime")).total_seconds()

                                    else:
                                        continue

                                else:
                                    continue

                if (ctr == 0):
                    return "no bus for given time"

                else:
                    predicted_time = last_arrival_time + timedelta(seconds = (total_sum / ctr))

                    predicted_times.append(predicted_time)

            if len(predicted_times) == 0:
                return "no bus on route"
            else:
                # Convert the datetime object to a consistent string format before returning
                predicted_datetime = min(predicted_times)
                return predicted_datetime.strftime("%Y-%m-%d %H:%M:%S")  
                
        
            

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
        "version": "1.0",
        "endpoints": {
            "stops": "/api/stops?route_id={route_id}",
            "routes": "/api/routes?stop_id={stop_id}",
            "buses": "/api/buses?route_id={route_id}&stop_id={stop_id}",
            "prediction": "/prediction/{route}/{stop_id}/{direction}"
        }
    })

# ------------------ NEW MAP + ROUTE ROUTES ------------------ #

@app.route('/frontend/routes.html')
def routes():
    return render_template('routes.html', map_file="static/bus_stops_map.html")

@app.route('/get_stops/<route>', methods=['GET'])
def get_stops_for_route(route):
    direction = request.args.get('direction')  # Accept direction as a query param
    df = pd.read_csv('static/matched_stops.csv')
    print(f"[DEBUG] Direction: {direction}")
    df.columns = df.columns.str.strip()

    # First filter by route
    filtered_df = df[df['Route'] == route].copy()
    
    # Convert Selector to numeric, handling NaN values
    filtered_df['Selector'] = pd.to_numeric(filtered_df['Selector'], errors='coerce').fillna(-1).astype(int)

    # Filter by direction parameter
    if direction == 'FROM HUB' or direction == 'FROM DOWNTOWN':
        filtered_df = filtered_df[filtered_df['Selector'] == 0]
    elif direction == 'TO HUB' or direction == 'TO DOWNTOWN':
        filtered_df = filtered_df[filtered_df['Selector'] == 1]
    
    # Set DirectionName based on Selector value
    filtered_df['DirectionName'] = filtered_df.apply(
        lambda row: row['Direction1'] if row['Selector'] == 0 else row['Direction2'],
        axis=1
    )

    # Select only the needed columns and remove duplicates
    stops = filtered_df[['stop_name', 'stop_id', 'DirectionName']].drop_duplicates()
    return jsonify(stops.to_dict(orient='records'))



@app.route('/get_directions/<route_name>', methods=['GET'])
def get_directions(route_name):
    df = pd.read_csv('static/matched_stops.csv')
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


@app.route('/frontend/generate_map', methods=['POST'])
def generate_map():

    data = request.get_json()

    selected_datetime_str= str(data.get('selected_datetime') or data.get('selected_hour'))
    year = selected_datetime_str.split('-')[0] if '-' in selected_datetime_str else None
    month = selected_datetime_str.split('-')[1] if '-' in selected_datetime_str else None
    whole = selected_datetime_str.split('-')[2] if '-' in selected_datetime_str else None
    day = whole.split(' ')[0] if ' ' in whole else whole
    time_hour = selected_datetime_str.split(' ')[1]
    hour = time_hour.split(':')[0] if ':' in time_hour else time_hour
    selected_datetime_obj = None
    print(f"[DEBUG] Received selected_datetime: {selected_datetime_str}")

    if selected_datetime_str:
        try:
            # Handle both full datetime and just hour (e.g., "2025-05-06 14:00" or "14:00")
            if len(selected_datetime_str) <= 5:  # Likely just hour, add today's date
                today_str = datetime.today().strftime('%Y-%m-%d')
                selected_datetime_obj = datetime.strptime(f"{today_str} {selected_datetime_str}", "%Y-%m-%d %H:%M")
            else:
                selected_datetime_obj = datetime.strptime(selected_datetime_str, "%Y-%m-%d %H:%M")
            print(f"[DEBUG] Parsed datetime: {selected_datetime_obj}")
        except Exception as e:
            print(f"[ERROR] Failed to parse selected_datetime: {selected_datetime_str}, Error: {str(e)}")


    route = data.get('route')
    direction = data.get('direction')
    direction_text = data.get('directionText')
    stop = data.get('stop')
    stop_id = data.get('stopId')
    
    print(f"[DEBUG] Parsed request: route = '{route}', direction = '{direction}', direction_text = '{direction_text}', stop = '{stop}', stop_id = '{stop_id}'")
    
    # If stop_id is None, try to find it using route, direction, and stop name
    if stop_id is None and stop is not None:
        try:
            print(f"[DEBUG] Looking up stop_id for stop name '{stop}'")
            df = pd.read_csv('static/matched_stops.csv')
            df.columns = df.columns.str.strip()
            
            # Convert direction to integer for filtering
            # Convert direction to integer for filtering
            dir_filter = [0, 1]  # Default to all selectors if direction is invalid
            if direction == '0':
                dir_filter = [0]  # Direction 1 selectors
            elif direction == '1':
                dir_filter = [1]  # Direction 2 selectors
            
            # Filter dataframe by route, direction, and stop name
            print(f"[DEBUG] Filtering dataframe for route = '{route}', direction = {dir_filter}, stop = '{stop}'")
            filtered = df[(df['Route'] == route) & 
                          (df['Selector'].isin(dir_filter)) & 
                          (df['stop_name'] == stop)]
            
            print(f"[DEBUG] Found {len(filtered)} matching rows")
            if not filtered.empty:
                stop_id = filtered.iloc[0]['stop_id']
                print(f"[DEBUG] Found stop_id: {stop_id} for stop {stop}")
            else:
                print(f"[DEBUG] No matching stop found")
        except Exception as e:
            print(f"[ERROR] Error finding stop_id: {str(e)}")
            print(traceback.format_exc())
    
    # Decide which direction value to use for prediction
    prediction_direction = direction_text if direction_text else direction
    print(f"[DEBUG] Using direction value for prediction: '{prediction_direction}'")
    
    # Get prediction for the selected stop
    print(f"[DEBUG] Calling get_bus_arrival_prediction with stop_id = '{stop_id}', route = '{route}', direction = '{prediction_direction}'")
    prediction = get_bus_arrival_prediction(stop_id, route, prediction_direction, day, month, year, hour)
    print(f"[DEBUG] Prediction result: {prediction}")
    string_prediction = str(prediction).split(' ')[1] if ' ' in str(prediction) else str(prediction)

    # Read and clean CSV
    df = pd.read_csv('static/matched_stops.csv')
    df.columns = df.columns.str.strip()
    df = df[df['Selector'].notnull()].copy()  # Create explicit copy
    df['Selector'] = pd.to_numeric(df['Selector'], errors='coerce').fillna(-1).astype(int)

    # Apply direction-based filtering
    if direction == '0':
        df = df[df['Selector'].isin([0])]
    elif direction == '1':
        df = df[df['Selector'].isin([1])]

    df = df[df['Route'] == route]

    # Create folium map
    map_center = [43.455, -76.532]
    bus_map = folium.Map(location=map_center, zoom_start=13)

    for _, row in df.iterrows():
        lat = row['stop_lat']
        lon = row['stop_lon']
        stop_name = row['stop_id']
        popup_text = f"{row['stop_name']}<br>ID: {stop_name}<br>Lat: {lat}, Lon: {lon}"
        
        if stop == row['stop_name']:
            folium.Marker(
                location=[lat, lon],
                popup=popup_text,
                tooltip=row['stop_name'],
                icon=folium.Icon(color='red')
            ).add_to(bus_map)
        else:
            folium.Marker(
                location=[lat, lon],
                popup=popup_text,
                tooltip=row['stop_name'],
            ).add_to(bus_map)

    # Save map
    static_folder = 'static'
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
    map_path = os.path.join(static_folder, "bus_stops_map.html")
    bus_map.save(map_path)
    

    return jsonify({
    "map_file": "static/bus_stops_map.html",
    "prediction": string_prediction
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
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
