#!/usr/bin/env python3
import mysql.connector
import json

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}


def listStops(route=None):
    try:
        db = mysql.connector.connect(**DATABASE)
        cursor = db.cursor()

        query = """
            SELECT DISTINCT StopName, StopID, Direction 
            FROM Delays 
        """

        params = []
        if route:
            query += " WHERE Route = %s"
            params.append(route)

        query += " ORDER BY StopName"

        cursor.execute(query, params)
        stops = cursor.fetchall()
        cursor.close()
        db.close()

        unique_stops = {}
        for name, stop_id, direction in stops:
            if stop_id not in unique_stops:
                unique_stops[stop_id] = {"name": name, "direction": direction}

        return [{"id": stop_id, "name": info["name"], "direction": info["direction"]}
                for stop_id, info in unique_stops.items()]

    except Exception as e:
        print(f"Error listing stops: {e}")
        return []


def generate_stops_json(route=None, output_file="stops.json"):

    stops_data = listStops(route)

    try:
        with open(output_file, "w") as file:
            json.dump(stops_data, file, indent=2)
        print(f"Successfully wrote information to {output_file}")
    except Exception as e:
        print(f"Error generating json file: {e}")


if __name__ == "__main__":
    route = None
    output_file = "stops.json"

    # use_route = input("Filter by route? (y/n): ").lower().strip()
    # if use_route == 'y':
    #     route = input("Enter route code (e.g., SY76): ").strip()

    # custom_output = input("Use custom output filename? (y/n): ").lower().strip()
    # if custom_output == 'y':
    #     output_file = input("Enter output filename: ").strip()

    generate_stops_json(route, output_file)