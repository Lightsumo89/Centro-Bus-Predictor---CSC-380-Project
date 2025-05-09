import mysql.connector
from mysql.connector import Error
from functools import wraps
from flask import jsonify

# Database configuration
DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}


def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DATABASE)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def db_connection_required(f):
    """Decorator to handle database connection for API endpoints"""

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


# Database operations
def get_all_stops(conn, route_id=None):
    """Get all stops or filter by route_id if provided"""
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

    return stops


def get_all_routes(conn, stop_id=None):
    """Get all routes or filter by stop_id if provided"""
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

    return routes


def get_all_buses(conn, route_id=None, stop_id=None):
    """Get all buses or filter by route_id or stop_id if provided"""
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

    return buses