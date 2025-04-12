from flask import Flask, jsonify, request, render_template
import pandas as pd
import folium
import os
import numpy as np
from hmmlearn import hmm
from scipy.stats import multivariate_normal

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD", 	
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD" 
}

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('routes.html', map_file="static/bus_stops_map.html")

def get_delay_A(stop, route, direction):
    # get delay from LastArrival 

def get_data(stop, route, direction):
    # select rows from database and convert to numpy array
    select_query = "SELECT * FROM Delays WHERE StopID = %s AND Route = %s AND Direction = %s"

    

    return data

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


# Prediction endpoint
@app.route('/prediction/<stop>/<direction>/<route>', methods=['GET'])
def get_prediction(stop, route, direction):
    # select the right rows in the database and convert to numpy array
    

    data = np.array([
    [1.0, 2.0], [1.3, 2.1], [1.2, 2.0], [1.7, 2.4], [1.4, 2.2], [2.0, 3.1], [1.3, 2.0], [2.1, 3.2], [2.4, 3.2], [2.2, 3.0], [1.9, 2.5], [1.5, 2.4], [2.3, 3.2], [2.5, 3.5], [1.6, 2.7], [1.3, 2.4],
    [1.4, 2.2], [2.3, 3.4], [2.7, 3.4], [2.1, 3.0], [2.3, 3.0], [2.2, 2.9], [1.4, 2.0], [1.3, 2.1] 
    ])

    data = get_data(stop, route, direction)

    given_delay_A = 

    predicted_delay_B = predict_delay_B(given_delay_A, data)




    


# Route to generate the map based on user input
@app.route('/generate_map', methods=['POST'])
def generate_map():
    # Retrieve user input from the form
    stop = request.form.get('stop')
    route = request.form.get('route')
    direction = request.form.get('direction')
    

    
    


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
                popup=f"{stop_name}<br>Lat: {lat}, Lon: {lon}", #Pop up thingy
            ).add_to(bus_map)

    static_folder = 'static'
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    bus_map.save(os.path.join(static_folder, "bus_stops_map.html"))
    print("Map saved as bus_stops_map.html")

    # Make new map
    return render_template('routes.html', map_file="static/bus_stops_map.html")






# Example prediction
delay_A_given = 2.0  # Replace with an actual delay_A value
predicted_delay_B1 = predict_delay_B(delay_A_given)

print(f"Predicted delay_B for delay_A={delay_A_given}: {predicted_delay_B1}")
print(f"Predicted delay_B2 for delayA={delay_A_given}: {predicted_delay_B1}")





#


    



if __name__ == '__main__':
    app.run(debug=True)
