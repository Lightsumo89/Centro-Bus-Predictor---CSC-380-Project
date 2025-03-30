import time
import json
import requests
import mysql.connector
from datetime import datetime

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD", 	
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD" 
}

API_URL_1 = "https://bus-time.centro.org/bustime/api/v3/getvehicles?key=PUZXP7CxWkPaWnvDWdacgiS4M&rt=SY76&format=json"

API_URL_3_before = "https://bus-time.centro.org/bustime/api/v3/getpredictions?key=PUZXP7CxWkPaWnvDWdacgiS4M&vid="

# in between is vid 

API_URL_3_after = "&tmres=s&rptidatafeed&top=1&format=json"

# change time.sleep to 5 

def insert_into_database(stop_name, stop_id, route, direction, arrive_time, delay):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    insert_query = "INSERT INTO Delays (StopName, StopID, Route, Direction, ArriveTime, Delay) VALUES (%s, %s, %s, %s, %s, %s)"

    cursor.execute(insert_query, (stop_name, stop_id, route, direction, arrive_time, delay))

    db.commit()	
 
    cursor.close()
    db.close()


def poll_api(vid, arrivals):
    while True: # first getprediction poll
        response = requests.get(API_URL_3_before + vid + API_URL_3_after)
        data = response.json()

        if "prd" in data.get("bustime-response", {}): # not an error
            prediction = data.get("bustime-response", {}).get("prd", [])[0] # set the initial fields

            last_stop_name = prediction.get("stpnm")
            last_stop_id = prediction.get("stpid") 
            last_route = prediction.get("rt")
            last_direction = prediction.get("rtdir") 

            last_date_time = prediction.get("prdtm").split()

            last_date = last_date_time[0]
            last_time = last_date_time[1]

            last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

            time.sleep(5) # to wait a second before updating response

            print(f"last stop name: {last_stop_name}, last stop id: {last_stop_id}, last predicted date: {last_date}, last_predicted_time: {last_time}, last route: {last_route}, last direction: {last_direction}")

            break

        #it is an error, so keep poling until a valid prediction response
        time.sleep(5) # for outermost while True

    # rest of the stops

    a = True
	
    while a:	
        response = requests.get(API_URL_3_before + vid + API_URL_3_after)
        data = response.json()

        if "prd" in data.get("bustime-response", {}): # not an error
            prediction = data.get("bustime-response", {}).get("prd", [])[0]

            if last_stop_id != prediction.get("stpid"): # arrived to a stop
                if prediction.get("rt") == "SY76":
                    arrive_time = datetime.now()
			
                    delay = arrive_time - last_predicted_time # positive if late, negative if early 

                    arrivals.append({ # the same duplicate issue here
                        "last_stop_name": last_stop_name,
                        "last_stop_id": last_stop_id,
                        "last_route": last_route,
                        "last_direction": last_direction,
                        "last_predicted_time": last_predicted_time,
                        "delay": delay.total_seconds()
                    })

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
                        "last_stop_name": last_stop_name,
                        "last_stop_id": last_stop_id,
                        "last_route": last_route,
                        "last_direction": last_direction,
                        "last_predicted_time": last_predicted_time,
                        "delay": delay.total_seconds()
                    })

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
                        response = requests.get(API_URL_3_before + vid + API_URL_3_after)
                        data = response.json()

                        if "prd" in data.get("bustime-response", {}): # not an error
                            prediction = data.get("bustime-response", {}).get("prd", [])[0]
 
                            # last_stop_id is the final stop on SY76 for the current bus
                            if last_stop_id != prediction.get("stpid"): # arrived to a stop
                                if final_stop != prediction.get("stpid") and first_stop_different_route != prediction.get("stpid"):
                                    arrive_time = datetime.now()
			
                                    delay = arrive_time - last_predicted_time 

                                    arrivals.append({ # change so also appending the first_stop_different_route, not currently adding duplicates
                                        "last_stop_name": last_stop_name,
                                        "last_stop_id": last_stop_id,
                                        "last_route": last_route,
                                        "last_direction": last_direction,
                                        "last_predicted_time": last_predicted_time,
                                        "delay": delay.total_seconds()
                                    })

                                    print("inserted")
                                    print(len(arrivals))
            
                                    a = False

                                    break

                                else: # either predicting final_stop or first_stop_different_route
                                    arrive_time = datetime.now() # arrived to the final stop (check duplicates below)
			
                                    delay = arrive_time - last_predicted_time

                                    arrivals.append({ 
                                        "last_stop_name": last_stop_name,
                                        "last_stop_id": last_stop_id,
                                        "last_route": last_route,
                                        "last_direction": last_direction,
                                        "last_predicted_time": last_predicted_time,
                                        "delay": delay.total_seconds()
                                     })

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

                            time.sleep(5)

                        else: # it is an error or empty
                            a = False

                            break                           

            else: # did not arrive yet 
                last_date_time = prediction.get("prdtm").split()

                last_date = last_date_time[0]
                last_time = last_date_time[1]

                last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                print("did not arrive yet")	

        # it is an error, keep polling until valid prediction response

        else: 
            a = False

            break

        time.sleep(5) # for while True for rest of the stops

            		                		
# Start polling
if __name__ == "__main__":
    while True: 
    # 1.  
        while True:
            response_1 = requests.get(API_URL_1)
            data_1 = response_1.json()

            if "vehicle" in data_1.get("bustime-response"):
                vehicle = data_1.get("bustime-response", {}).get("vehicle", [])[0]

                vid = vehicle.get("vid")

                print(f"vid: {vid}")

                break

            time.sleep(5) # for the inner while True

        # 2.
        arrivals = []

        poll_api(vid, arrivals)

        # 3.
        # remove the duplicates
        added_arrival_stop_ids = set()

        arrivals_without_duplicates = []

        for arrival in reversed(arrivals):
            if arrival.get("last_stop_id") not in added_arrival_stop_ids:
                added_arrival_stop_ids.add(arrival.get("last_stop_id"))
 
                arrivals_without_duplicates.append(arrival)

        arrivals_without_duplicates.reverse()

        print(arrivals_without_duplicates)
            
        # 4. insert into the database

        for arrival in arrivals_without_duplicates:
            if arrival.get("last_route") == "SY76":
                insert_into_database(arrival.get("last_stop_name"), arrival.get("last_stop_id"), arrival.get("last_route"), arrival.get("last_direction"), arrival.get("last_predicted_time"), arrival.get("delay"))

        print("inserted into database")

        time.sleep(5) # for the outer while True

