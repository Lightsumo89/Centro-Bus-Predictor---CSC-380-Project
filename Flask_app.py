from flask import Flask, jsonify, request, render_template
import pandas as pd
import folium
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('routes.html', map_file="static/bus_stops_map.html")

# Prediction endpoint
@app.route('/prediction/<stop>/<direction>/<route>', methods=['GET'])
def get_prediction(stop: str, direction: str, route: str):
    prediction = f"Prediction for stop '{stop}' on route '{route}' heading {direction} is 'Next bus arrives in 5 minutes'"
    return jsonify({
        "stop": stop,
        "direction": direction,
        "route": route,
        "prediction": prediction
    })


# Route to generate the map based on user input
@app.route('/generate_map', methods=['POST'])
def generate_map():
    # Retrieve user input from the form
    route = request.form.get('route')
    direction = request.form.get('direction')
    stop = request.form.get('stop')


    df = pd.read_csv('matched_stops.csv')

    df.columns = df.columns.str.strip()

    map_center = [43.455, -76.532]  #Oswego NY
    bus_map = folium.Map(location=map_center, zoom_start=13)

    for index, row in df.iterrows():
        if route == row['Route']:
            lat = row['stop_lat']
            lon = row['stop_lon']
            stop_name = row['stop_id']

            folium.Marker(
                location=[lat, lon],
                popup=f"{stop_name}<br>Lat: {lat}, Lon: {lon}", #Pop up thingy
            ).add_to(bus_map)

    static_folder = 'static'
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    bus_map.save(os.path.join(static_folder, "bus_stops_map.html"))
    print("Map saved as bus_stops_map.html")

    # Make new map
    return render_template('routes.html', map_file="static/bus_stops_map.html")

if __name__ == '__main__':
    app.run(debug=True)
