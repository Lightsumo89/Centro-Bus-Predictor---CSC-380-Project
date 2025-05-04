

import ctypes
import requests
import json
import mysql.connector
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
# from lxml import etree

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}

stopurl1 = 'https://bus-time.centro.org/bustime/api/v3/getstops?key=PUZXP7CxWkPaWnvDWdacgiS4M&rt='
stopurl2 = '&dir='
stopurl3 = '%20'

response = requests.get(stopurl1 + 'SY76' + stopurl2 + 'FROM' + stopurl3 + 'HUB')
print(response.status_code)
print(response.text)

def insertStopsData(stop_id, stop_name, route_id, route_dir):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()
    insert_into_stop = ("INSERT INTO Stop(stop_id, stop_name) VALUES (%s, %s)" 
                        " ON DUPLICATE KEY UPDATE stop_id = %s, stop_name = %s"
                        )
    insert_into_routestop = (
            "INSERT INTO RouteStops(route_id, stop_id, route_dir) VALUES (%s, %s, %s)" 
    "ON DUPLICATE KEY UPDATE route_id = %s, stop_id = %s, route_dir = %s"
    )

    cursor.execute(insert_into_stop, (stop_id, stop_name))
    cursor.execute(insert_into_routestop, (route_id, stop_id, route_dir))

    db.commit()
    cursor.close()
    db.close()


def pollStops(route_id, route_dir, input_dir, input_destination):
    route_dir_parse = route_dir.split(' ')
    response = requests.get(stopurl1 + route_id + stopurl2 + input_dir + stopurl3 + input_destination)
    while True:
        parse = BeautifulSoup(response.text, 'xml')
        stops = parse.findAll('stop')
        # for tag in parse.find_all(True):
        #     print(tag.name)
        for stop in stops:
            stop_id = parse.find("stpid").text
            stop_name = parse.find("stpnm").text
            # print(stop_id)
            # print(stop_name)
            insertStopsData(stop_id, stop_name, route_id, route_dir)
            print("INSERTING A STOP!!!")



pollStops('SY76', 'FROM HUB', 'FROM', 'HUB')