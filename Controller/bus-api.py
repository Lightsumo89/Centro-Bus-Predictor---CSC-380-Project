import mysql.connector
from flask import Flask, request, jsonify, render_template
import pandas as pd
import folium
from datetime import datetime, timedelta
import os
import traceback


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


# Helper prediction functions
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

    select_query = "SELECT * FROM Delays_n  WHERE StopID = %s AND Route = %s AND Direction = %s"

    cursor.execute(select_query, (stop_id, route, direction))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows

def get_bus_arrival_prediction(stop_id, route, direction):

    direction = str(direction)
    stop_id = str(stop_id)
    route = str(route)

    last_arrivals = select_table1(route) # get the stops of the last arrived buses on the route

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

            if last_arrival.get("StopID") == stop_id: # last arrival is the same as user inputted stop
                # get all of the arrivals for that stop and check for same day and ID greater than 1
                print(f"Rows User Input 1: {rows_user_input}")
                print(f"Rows User Input 2: {rows_user_input}")

                for row_user_input1 in rows_user_input:
                    for row_user_input2 in rows_user_input:
                        if row_user_input2.get("ID") == row_user_input1.get("ID") + 1 and row_user_input1.get("ArriveTime").date() == row_user_input2.get("ArriveTime").date():
                            ctr += 1

                            total_sum += (row_user_input2.get("ArriveTime") - row_user_input1.get("ArriveTime")).total_seconds()

                            print(f"User Input 1 ArriveTime: {row_user_input1.get('ArriveTime')}")
                            print(f"User Input 2 ArriveTime: {row_user_input2.get('ArriveTime')}")

                            print(f"Difference: {(row_user_input2.get('ArriveTime') - row_user_input1.get('ArriveTime')).total_seconds()}, User Input 1 ID: {row_user_input1.get('ID')}, User Input 2 ID: {row_user_input2.get('ID')}")

                            break
                                
   

            else:
                last_arrival_time = last_arrival.get("ArriveTime")

                rows_last_arrival = select_table2(last_arrival.get("StopID"), last_arrival.get("Route"), last_arrival.get("Direction"))

                print(f"Rows Last Arrival: {rows_last_arrival}")
                print(f"Rows User Input: {rows_user_input}")

                for row_last_arrival in rows_last_arrival:
                    for row_user_input in rows_user_input: # could do a check for an id one less or more for different directions for multiple round trips
                        if row_user_input.get("ID") == row_last_arrival.get("ID") and row_user_input.get("ArriveTime") > row_last_arrival.get("ArriveTime"):
                            ctr += 1

                            total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get("ArriveTime")).total_seconds()

                            print(f"Last Arrival Row ArriveTime: {row_last_arrival.get('ArriveTime')}")
                            print(f"User Input Row ArriveTime: {row_user_input.get('ArriveTime')}")

                            print(f"Difference: {(row_user_input.get('ArriveTime') - row_last_arrival.get('ArriveTime')).total_seconds()}, User Input ID: {row_user_input.get('ID')}, Last Arrival ID: {row_last_arrival.get('ID')}")
        

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

                                total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get("ArriveTime")).total_seconds()

                                print(f"Last Arrival Row ArriveTime: {row_last_arrival.get('ArriveTime')}")
                                print(f"User Input Row ArriveTime: {row_last_arrival.get('ArriveTime')}")

                                print(f"Difference: {(row_user_input.get('ArriveTime') - row_last_arrival.get('ArriveTime')).total_seconds()}, User Input ID: {row_user_input.get('ID')}, Last Arrival ID: {row_last_arrival.get('ID')}")

                                break

  
            if ctr == 0:
                print("no data")

            else:
                predicted_time = last_arrival_time + timedelta(seconds = (total_sum / ctr))

                print(f"Predicted Time: {predicted_time}")

                predicted_times.append(predicted_time)

    return predicted_times

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
    prediction = get_bus_arrival_prediction(stop_id, route, prediction_direction)
    print(f"[DEBUG] Prediction result: {prediction}")

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
        "prediction": prediction
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
