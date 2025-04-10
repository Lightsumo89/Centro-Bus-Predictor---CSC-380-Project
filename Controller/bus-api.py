from flask import Flask, request, jsonify, render_template
import os
from database import db_connection_required, get_all_stops, get_all_routes, get_all_buses

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

# API Endpoints
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
def get_prediction(conn, input):
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
    #Server configuration
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)