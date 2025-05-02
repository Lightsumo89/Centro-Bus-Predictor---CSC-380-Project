import csv

import mysql.connector

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}

def exportToCSV(route_id):
    db = mysql.connector.connect(**DATABASE, connection_timeout = 220)
    cursor = db.cursor()
    # cursor.execute("""
    #                SELECT * FROM Stop, Route, RouteStops WHERE RouteStops.route_id = RouteID
    #                    INTO OUTFILE 'stops.csv'
    #                    """)

    # cursor.execute("""
    #                SELECT * FROM RouteStops
    #                 JOIN Route ON RouteStops.route_id = Route.route_id
    #                 JOIN Stop ON RouteStops.stop_id = Stop.stop_id
    #                WHERE RouteStops.route_id = %s""", (route_id,))

    cursor.execute("""
        SELECT DISTINCT StopID, Route, Direction FROM Delays_n
            WHERE Route = %s
    """, (route_id,))
    rows = cursor.fetchall()

    with open(f"{route_id}_stops.csv", "w", newline="") as file:
        write = csv.writer(file)
        write.writerows(rows)


    cursor.close()
    db.close()

exportToCSV("OSW46")