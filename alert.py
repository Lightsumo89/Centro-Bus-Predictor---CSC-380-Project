import os
import json
import pymysql
from flask import Flask, render_template, jsonify

# Database connection details
DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}

# Set up static directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

def get_db_connection():
    """Create and return a database connection, with connection test printout"""
    try:
        connection = pymysql.connect(
            host=DATABASE['host'],
            user=DATABASE['user'],
            password=DATABASE['password'],
            database=DATABASE['database'],
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Successfully connected to the database.")
        return connection
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")
        raise

def write_alerts_to_json():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Query to fetch the service bulletin data
        cursor.execute("""
            SELECT sb.route_id, sb.alert_details, sb.alert_cause 
            FROM ServiceBulletin sb
            JOIN Route r ON sb.route_id = r.route_id
            WHERE sb.route_id IN ('OSW10', 'OSW11', 'OSW1A', 'OSW46', 'SY74', 'SY76', 'SY80')
        """)

        data = cursor.fetchall()

        # Write to JSON file
        with open(os.path.join(STATIC_DIR, "alerts.json"), "w") as f:
            json.dump(data, f, indent=4)

        cursor.close()
        db.close()
        print("✅ Alerts JSON file updated successfully.")
        return True
    except Exception as e:
        print(f"❌ Error updating alerts JSON: {e}")
        return False

# Flask app setup
app = Flask(__name__, static_folder=STATIC_DIR)

@app.route('/')
def index():
    try:
        if not os.path.exists(os.path.join(STATIC_DIR, "alerts.json")):
            write_alerts_to_json()

        with open(os.path.join(STATIC_DIR, "alerts.json"), "r") as f:
            alerts_data = json.load(f)
        return render_template("alerts.html", alerts=alerts_data)
    except Exception as e:
        print(f"❌ Error loading alerts: {e}")
        return render_template("alerts.html", alerts=[])

@app.route('/api/alerts')
def api_alerts():
    try:
        if not os.path.exists(os.path.join(STATIC_DIR, "alerts.json")):
            write_alerts_to_json()

        with open(os.path.join(STATIC_DIR, "alerts.json"), "r") as f:
            alerts_data = json.load(f)
        return jsonify(alerts_data)
    except Exception as e:
        print(f"❌ Error loading alerts API: {e}")
        return jsonify([])

@app.route('/refresh')
def refresh():
    print("🔄 Refreshing alerts data...")
    alerts_success = write_alerts_to_json()

    if alerts_success:
        return jsonify({"status": "success", "message": "Alerts refreshed successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to refresh alerts"}), 500

if __name__ == '__main__':
    print("🚀 Starting Flask server...")

    # Test DB connection on startup
    try:
        test_conn = get_db_connection()
        test_conn.close()
    except:
        print("⚠️ Continuing to run, but database connection failed at startup.")

    # Initial JSON export
    write_alerts_to_json()

    app.run(debug=True, host='0.0.0.0', port=5000)
