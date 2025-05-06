import time

import requests
import json
import mysql.connector
import urllib.request
import schedule

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}

stopurl1 = "https://bus-time.centro.org/bustime/api/v3/getstops?key=PUZXP7CxWkPaWnvDWdacgiS4M&rt="
stopurl2 = "&dir="
stopurl3 = "%20"
stopurl4 = "&format=json"

serviceurl = "https://bus-time.centro.org/bustime/api/v3/getservicebulletins?key=PUZXP7CxWkPaWnvDWdacgiS4M&rt="
serviceurl2 = "&format=json"



def insertStopsData(stop_id, stop_name, route_id, route_dir):
    db = mysql.connector.connect(**DATABASE, connection_timeout = 200)
    cursor = db.cursor()
    insert_into_stop = ("INSERT INTO Stop(stop_id, stop_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE stop_id = %s, stop_name = %s"
                        )
    insert_into_routestop = (
            "INSERT INTO RouteStops(route_id, stop_id, route_dir) VALUES (%s, %s, %s)" 
    "ON DUPLICATE KEY UPDATE route_id = %s, stop_id = %s, route_dir = %s"
    )

    cursor.execute(insert_into_stop, (stop_id, stop_name, stop_id, stop_name))
    cursor.execute(insert_into_routestop, (route_id, stop_id, route_dir, route_id, stop_id, route_dir))

    db.commit()
    cursor.close()
    db.close()

def insertServiceData(route_id, alert_details, alert_cause):
    db = mysql.connector.connect(**DATABASE, connection_timeout = 200)
    cursor = db.cursor()
    insert_into_service = ("""
        INSERT INTO ServiceBulletin(route_id, alert_details, alert_cause) VALUES (%s, %s, %s)
                           ON DUPLICATE KEY UPDATE alert_details = %s, alert_cause = %s""")

    cursor.execute(insert_into_service, (route_id, alert_details, alert_cause, alert_details, alert_cause))

    db.commit()
    cursor.close()
    db.close()


def pollStops():
    db = mysql.connector.connect(**DATABASE, connection_timeout=500)
    cursor = db.cursor()
    getRoutes = ("""SELECT DISTINCT Route, Direction
                    FROM Delays_n""")
    cursor.execute(getRoutes)
    Routes = cursor.fetchall()
    for row in Routes:
        route_id = row[0]
        route_dir = row[1]
        split = route_dir.split(" ")
        input_dir = split[0]
        input_destination = split[1]
        print(input_dir)
        print(input_destination)
        print(route_id + " " + route_dir)


        url = stopurl1 + route_id + stopurl2 + input_dir + stopurl3 + input_destination + stopurl4

        try:
            with urllib.request.urlopen(url) as response:
                parse = json.loads(response.read().decode('utf-8'))
                stops = parse.get('bustime-response', {}).get('stops', [])
                # parse = response.json()
                #     while True:
                        # parse = BeautifulSoup(response.text, 'json')
                        # stops = parse.findAll('stop')
                        # for tag in parse.find_all(True):
                        #      print(tag.name)
                for stop in stops:
                    stop_id = stop.get("stpid")
                    stop_name = stop.get("stpnm")
                    print(stop_id)
                    print(stop_name)
                    insertStopsData(stop_id, stop_name, route_id, route_dir)
                    print("INSERTING A STOP!!!")
                    # time.sleep(5)
        except urllib.error.URLError as e:
            print("error")
        cursor.close()
        db.close()

def pollServiceBulletin():
    db = mysql.connector.connect(**DATABASE, connection_timeout = 200)
    cursor = db.cursor()
    getRoutes = ("""SELECT route_id FROM Route""")
    cursor.execute(getRoutes)
    routes = cursor.fetchall()
    for row in routes:
        route = row[0]
        print("running " + route)
        url = serviceurl + route + serviceurl2
        try:
            with urllib.request.urlopen(url) as response:
                parse = json.loads(response.read().decode('utf-8'))
                # services = parse.get('bustime-response', {}).get('services', [])
                alerts = parse.get('bustime-response', {}).get('sb', [])
                if not alerts:
                    print("No service bulletins found.")
                    alertDetails = "No service bulletins found."
                    alertCause = ""
                    insertServiceData(route, alertDetails, alertCause)
                for alert in alerts:
                    # alertName = alert.get('nm')
                    alertDetails = alert.get('dtl')
                    alertCause = alert.get('cse')
                    alertCauseAnnotated = "Cause: " + alertCause
                    # print(alertName)
                    print(alertDetails)
                    print(alertCauseAnnotated)
                    insertServiceData(route, alertDetails, alertCauseAnnotated)
        except urllib.error.URLError as e:
            print("error")
        except ValueError as e:
            print("ValueError")

        cursor.close()
        db.close()


# test schedule
schedule.every().day.at("05:00").do(pollServiceBulletin)
schedule.every().day.at("05:00").do(pollStops)

while True:
    schedule.run_pending()
    time.sleep(30)


# pollServiceBulletin()
# pollStops()
