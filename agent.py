import time
import json
import requests
import mysql.connector
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD", 	
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD" 
}

API_URL_1 = "https://bus-time.centro.org/bustime/api/v3/getvehicles?key=PUZXP7CxWkPaWnvDWdacgiS4M&rt=SY76&rptidatafeed&format=json"

API_URL_2_before = "https://bus-time.centro.org/bustime/api/v3/getpredictions?key=PUZXP7CxWkPaWnvDWdacgiS4M&vid="

# in between is vid 

API_URL_2_after = "&tmres=s&top=1&rptidatafeed&format=json"

# change time.sleep to 5 

def create_session():
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
        raise_on_redirect=True
    )

    adapter = HTTPAdapter(max_retries=retries)

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({"Connection": "keep-alive"})

    return session


def truncate_table():
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    truncate_query = "TRUNCATE TABLE LastArrival"

    cursor.execute(truncate_query)

    db.commit()

    cursor.close()
    db.close()


def insert_into_table(stop_name, stop_id, route, direction, arrive_time, delay, table_name):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    insert_query = "INSERT INTO " + table_name + " (StopName, StopID, Route, Direction, ArriveTime, Delay) VALUES (%s, %s, %s, %s, %s, %s)"

    cursor.execute(insert_query, (stop_name, stop_id, route, direction, arrive_time, delay))

    db.commit()	
 
    cursor.close()
    db.close()


def poll_api(vid, arrivals, session):
    try:
        response_2 = session.get(API_URL_2_before + vid + API_URL_2_after, timeout=30)
        data_2 = response_2.json()

        if "prd" in data_2.get("bustime-response", {}): # not an error
            prediction = data_2.get("bustime-response", {}).get("prd", [])[0] # set the initial fields

            if prediction.get("rt") == "SY76":
                last_stop_name = prediction.get("stpnm")
                last_stop_id = prediction.get("stpid") 
                last_route = prediction.get("rt")
                last_direction = prediction.get("rtdir") 

                last_date_time = prediction.get("prdtm").split()

                last_date = last_date_time[0]
                last_time = last_date_time[1]

                last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                print(f"last stop name: {last_stop_name}, last stop id: {last_stop_id}, last predicted date: {last_date}, last predicted time: {last_time}, last route: {last_route}, last direction: {last_direction}")

            else:
                return

        else:
            return # error like running out of API calls

        time.sleep(5)

    except requests.exceptions.RequestException:
        return

    # rest of the stops
	
    while True:	
        try:
            response_2 = session.get(API_URL_2_before + vid + API_URL_2_after, timeout=30)
            data_2 = response_2.json()

            if "prd" in data_2.get("bustime-response", {}): # not an error
                prediction = data_2.get("bustime-response", {}).get("prd", [])[0]

                if last_stop_id != prediction.get("stpid"): # arrived to a stop
                    if prediction.get("rt") == "SY76":
                        arrive_time = datetime.now()
			
                        delay = arrive_time - last_predicted_time # positive if late, negative if early 

                        arrivals.append({ # the same duplicate issue here
                            "stop_name": last_stop_name,
                            "stop_id": last_stop_id,
                            "route": last_route,
                            "direction": last_direction,
                            "predicted_time": last_predicted_time,
                            "delay": delay.total_seconds()
                        })

                        truncate_table()

                        insert_into_table(last_stop_name, last_stop_id, last_route, last_direction, last_predicted_time, delay.total_seconds(), "LastArrival")

                        print(f"last stop name: {last_stop_name}, last stop id: {last_stop_id}, last predicted date: {last_date}, last predicted time: {last_time}, last route: {last_route}, last direction: {last_direction}, delay: {delay.total_seconds()}")

                        last_stop_name = prediction.get("stpnm")
                        last_stop_id = prediction.get("stpid") 
                        last_route = prediction.get("rt")
                        last_direction = prediction.get("rtdir") 

                        last_date_time = prediction.get("prdtm").split()

                        last_date = last_date_time[0]
                        last_time = last_date_time[1]

                        last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                        print("inserted")
                        print(len(arrivals))

                    else:
                        arrive_time = datetime.now() # arrived to the final stop (check duplicates below)
			
                        delay = arrive_time - last_predicted_time

                        arrivals.append({ # the same duplicate issue here
                            "stop_name": last_stop_name,
                            "stop_id": last_stop_id,
                            "route": last_route,
                            "direction": last_direction,
                            "predicted_time": last_predicted_time,
                            "delay": delay.total_seconds()
                        })

                        truncate_table()

                        insert_into_table(last_stop_name, last_stop_id, last_route, last_direction, last_predicted_time, delay.total_seconds(), "LastArrival")

                        print(f"last stop name: {last_stop_name}, last stop id: {last_stop_id}, last predicted date: {last_date}, last predicted time: {last_time}, last route: {last_route}, last direction: {last_direction}, delay: {delay.total_seconds()}")

                        last_stop_name = prediction.get("stpnm")
                        last_stop_id = prediction.get("stpid") 
                        last_route = prediction.get("rt")
                        last_direction = prediction.get("rtdir") 

                        last_date_time = prediction.get("prdtm").split()

                        last_date = last_date_time[0]
                        last_time = last_date_time[1]

                        last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                        print("inserted")
                        print(len(arrivals))

                        final_stop = last_stop_id

                        first_stop_different_route = prediction.get("stpid")

                        while True:    
                            try:
                                response_2 = session.get(API_URL_2_before + vid + API_URL_2_after, timeout=30)
                                data_2 = response_2.json()

                                if "prd" in data_2.get("bustime-response", {}): # not an error
                                    prediction = data_2.get("bustime-response", {}).get("prd", [])[0]
 
                                    # last_stop_id is the final stop on SY76 for the current bus
                                    if last_stop_id != prediction.get("stpid"): # arrived to a stop
                                        if final_stop != prediction.get("stpid") and first_stop_different_route != prediction.get("stpid"): # arrived to the final stop
                                            arrive_time = datetime.now()
			
                                            delay = arrive_time - last_predicted_time 

                                            arrivals.append({ 
                                                "stop_name": last_stop_name,
                                                "stop_id": last_stop_id,
                                                "route": last_route,
                                                "direction": last_direction,
                                                "predicted_time": last_predicted_time,
                                                "delay": delay.total_seconds()
                                            })

                                            print("inserted")
                                            print(len(arrivals))
            
                                            return

                                        else: # either predicting final_stop or first_stop_different_route
                                            arrive_time = datetime.now() 
			
                                            delay = arrive_time - last_predicted_time

                                            arrivals.append({ 
                                                "stop_name": last_stop_name,
                                                "stop_id": last_stop_id,
                                                "route": last_route,
                                                "direction": last_direction,
                                                "predicted_time": last_predicted_time,
                                                "delay": delay.total_seconds()
                                            })

                                            truncate_table()

                                            insert_into_table(last_stop_name, last_stop_id, last_route, last_direction, last_predicted_time, delay.total_seconds(), "LastArrival")

                                            print(f"last stop name: {last_stop_name}, last stop id: {last_stop_id}, last predicted date: {last_date}, last predicted time: {last_time}, last route: {last_route}, last direction: {last_direction}, delay: {delay.total_seconds()}")

                                            last_stop_name = prediction.get("stpnm")
                                            last_stop_id = prediction.get("stpid") 
                                            last_route = prediction.get("rt")
                                            last_direction = prediction.get("rtdir") 

                                            last_date_time = prediction.get("prdtm").split()

                                            last_date = last_date_time[0]
                                            last_time = last_date_time[1]

                                            last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                                            print("inserted")
                                            print(len(arrivals))

                                    else: # did not arrive yet
                                        last_date_time = prediction.get("prdtm").split()

                                        last_date = last_date_time[0]
                                        last_time = last_date_time[1]

                                        last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                                        print("did not arrive yet")	

                                else: # it is an error or empty
                                    return   

                                time.sleep(5)

                            except requests.exceptions.RequestException:
                                return                       

                else: # did not arrive yet 
                    last_date_time = prediction.get("prdtm").split()

                    last_date = last_date_time[0]
                    last_time = last_date_time[1]

                    last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                    print("did not arrive yet")	

            # it is an error
            else: 
                return

            time.sleep(5)

        except requests.exceptions.RequestException:
            return  


def remove_duplicates(arrivals):
    added_arrival_stop_ids = set()

    arrivals_without_duplicates = []

    reversed_arrivals = list(reversed(arrivals))  

    ctr = 0

    for i in range(len(reversed_arrivals)):
        if i != len(reversed_arrivals) - 1:
            if reversed_arrivals[i].get("direction") != reversed_arrivals[i + 1].get("direction"): # duplicates at changing direction
                ++ctr

                if ctr == 1:
                    if reversed_arrivals[i].get("stop_id") not in added_arrival_stop_ids:
                        added_arrival_stop_ids.add(reversed_arrivals[i].get("stop_id"))

                        arrivals_without_duplicates.append(reversed_arrivals[i])

                elif ctr == 2:
                    added_arrival_stop_ids.add(reversed_arrivals[i].get("stop_id"))

                    arrivals_without_duplicates.append(reversed_arrivals[i])

            elif reversed_arrivals[i].get("direction") == reversed_arrivals[i + 1].get("direction") and ctr > 0: # no more duplicates at changing direction
                added_arrival_stop_ids.clear()

                if ctr == 1: # no duplicates at changing direction
                    added_arrival_stop_ids.add(reversed_arrivals[i].get("stop_id"))

                    arrivals_without_duplicates.append(reversed_arrivals[i])
                
                ctr = 0

            else: # direction is not changing
                if reversed_arrivals[i].get("stop_id") not in added_arrival_stop_ids:
                    added_arrival_stop_ids.add(reversed_arrivals[i].get("stop_id"))

                    arrivals_without_duplicates.append(reversed_arrivals[i])

        else: # if same direction, check if it is a duplicate, if different direction, just add it
            if ctr > 0: # changing direction
                if ctr == 1: 
                    added_arrival_stop_ids.add(reversed_arrivals[i].get("stop_id"))

                    arrivals_without_duplicates.append(reversed_arrivals[i])

            else: # same direction
                if reversed_arrivals[i].get("stop_id") not in added_arrival_stop_ids:
                    added_arrival_stop_ids.add(reversed_arrivals[i].get("stop_id"))

                    arrivals_without_duplicates.append(reversed_arrivals[i]) 

    arrivals_without_duplicates.reverse()

    return arrivals_without_duplicates

            		                		
# start polling
if __name__ == "__main__":
    while True:
        if datetime.now().hour >= 10:
            pass

        else:
            print("not 10 or after")
 
            time.sleep(5)

            continue
            
        try:
            session = create_session()

        except Exception:
            time.sleep(5)

            continue

        # 1.  
        while True:
            vid = ""

            try:
                response_1 = session.get(API_URL_1, timeout=30)
                data_1 = response_1.json()

                if "vehicle" in data_1.get("bustime-response"):
                    vehicle = data_1.get("bustime-response", {}).get("vehicle", [])[0]

                    vid = vehicle.get("vid")

                    print(f"vid: {vid}")

                    time.sleep(5)

                    break

                else:
                    time.sleep(5)

                    print("no bus")

            except requests.exceptions.RequestException:
                time.sleep(5)
 
                # continue

        # 2.
        arrivals = []

        poll_api(vid, arrivals, session)

        # 3.
        # remove the duplicates
        arrivals_without_duplicates = remove_duplicates(arrivals)

        print(arrivals_without_duplicates)
            
        # 4. insert into the database

        for arrival in arrivals_without_duplicates:
            if arrival.get("route") == "SY76":
                insert_into_table(arrival.get("stop_name"), arrival.get("stop_id"), arrival.get("route"), arrival.get("direction"), arrival.get("predicted_time"), arrival.get("delay"), "Delays")

        print(len(arrivals_without_duplicates))
        print("inserted into database")

        session.close()

        time.sleep(5) # for the outer while True
