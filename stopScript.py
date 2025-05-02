import time

import requests
import json
import mysql.connector
import urllib.request
from requests.adapters import HTTPAdapter
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

# global route_id
# global stop_id
# global stop_name
# global route_dir

# def getStops():
    # will iterate through a db query to get stop, alter global variable (hopefully)

# response = requests.get(stopurl1 + 'SY76' + stopurl2 + 'FROM' + stopurl3 + 'HUB')
# print(response.status_code)
# print(response.text)

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


def pollStops(route_id, route_dir, input_dir, input_destination):
    # route_dir_parse = route_dir.split(' ')
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

def pollServiceBulletin(route_id):
    url = serviceurl + route_id + serviceurl2
    try:
        with urllib.request.urlopen(url) as response:
            parse = json.loads(response.read().decode('utf-8'))
            # services = parse.get('bustime-response', {}).get('services', [])
            alerts = parse.get('bustime-response', {}).get('sb', [])
            if not alerts:
                print("No service bulletins found.")
                alertDetails = "No service bulletins found."
                alertCause = ""
                insertServiceData(route_id, alertDetails, alertCause)
            for alert in alerts:
                # alertName = alert.get('nm')
                alertDetails = alert.get('dtl')
                alertCause = alert.get('cse')
                alertCauseAnnotated = "Cause: " + alertCause
                # print(alertName)
                print(alertDetails)
                print(alertCauseAnnotated)
                insertServiceData(route_id, alertDetails, alertCauseAnnotated)
    except urllib.error.URLError as e:
        print("error")
    except ValueError as e:
        print("ValueError")


# test schedule
# schedule.every().monday.at("05:00").do(pollStops(route_id, route_dir, input_dir, input_destination))
# while True:
#     schedule.run_pending()
#     time.sleep(1)

# pollStops("SY76", "TO HUB", "TO", "HUB")

pollServiceBulletin("SY76")
