from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from functools import wraps
import os

app = Flask(__name__)
#DB connection details and functions
DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DATABASE)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def db_connection_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        try:
            result = f(conn, *args, **kwargs)
            return result
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    
    return decorated_function

#API Endpoints
@app.route('/api/stops', methods=['GET'])
@db_connection_required
def get_stops(conn):
    route_id = request.args.get('route_id')
    
    cursor = conn.cursor(dictionary=True)
    
    if route_id:
        cursor.execute("""
            SELECT s.stop_id, s.stop_name 
            FROM Stop s
            JOIN Bus b ON s.stop_id = b.current_stop_id
            WHERE b.route_id = %s
            ORDER BY s.stop_name
        """, (route_id,))
    else:
        cursor.execute("SELECT stop_id, stop_name FROM Stop ORDER BY stop_name")
    
    stops = cursor.fetchall()
    cursor.close()
    
    return jsonify(stops)

@app.route('/api/routes', methods=['GET'])
@db_connection_required
def get_routes(conn):
    """Get all routes or filter by stop_id if provided"""
    stop_id = request.args.get('stop_id')
    
    cursor = conn.cursor(dictionary=True)
    
    if stop_id:
        cursor.execute("""
            SELECT r.route_id, r.route_name 
            FROM Route r
            JOIN Bus b ON r.route_id = b.route_id
            WHERE b.current_stop_id = %s
            ORDER BY r.route_name
        """, (stop_id,))
    else:
        cursor.execute("SELECT route_id, route_name FROM Route ORDER BY route_name")
    
    routes = cursor.fetchall()
    cursor.close()
    
    return jsonify(routes)


@app.route('/api/buses', methods=['GET'])
@db_connection_required
def get_buses(conn):
    """Get all buses or filter by route_id or stop_id if provided"""
    route_id = request.args.get('route_id')
    stop_id = request.args.get('stop_id')

    cursor = conn.cursor(dictionary=True)

    if route_id and stop_id:
        cursor.execute("""
            SELECT vehicle_id, pattern_id, route_id
            FROM Bus 
            WHERE route_id = %s
        """, (route_id,))
    elif route_id:
        cursor.execute("""
            SELECT vehicle_id, pattern_id, route_id
            FROM Bus 
            WHERE route_id = %s
        """, (route_id,))
    elif stop_id:
        cursor.execute("SELECT vehicle_id, pattern_id, route_id FROM Bus")
    else:
        cursor.execute("SELECT vehicle_id, pattern_id, route_id FROM Bus")

    buses = cursor.fetchall()
    cursor.close()

    return jsonify(buses)

@app.route('/prediction/<input>', methods=['GET'])
@db_connection_required
def get_prediction(conn, input):
    """
    Get bus arrival predictions for the given input parameter
    Input could be a stop_id, route_id, and/or bus ID
    """
    return jsonify({"error": "No API Endpoint"}), 500

@app.route('/')
def index():
    """API root"""
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

if __name__ == '__main__':
    #Server configuration
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)