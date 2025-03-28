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

# FROM HUB: pid is 8966, first stop is B13 (stpid 17652), last stop is Widewaters Pkwy & Bridge St (stpid 8149)

# TO HUB: pid is 8957/8970, first stop is Widewaters Pkwy & Bridge St (stpid 8149), last stop is B13/A1 (stpid 17652/17640)


API_URL_1 = "https://bus-time.centro.org/bustime/api/v3/getvehicles?key=PUZXP7CxWkPaWnvDWdacgiS4M&rt=SY76&format=json"

API_URL_2_before = "https://bus-time.centro.org/bustime/api/v3/getpatterns?key=PUZXP7CxWkPaWnvDWdacgiS4M&pid="

# in between is pid

API_URL_2_after = "&format=json"

API_URL_3_before = "https://bus-time.centro.org/bustime/api/v3/getpredictions?key=PUZXP7CxWkPaWnvDWdacgiS4M&vid="

# in between is vid 

API_URL_3_after = "&tmres=s&rptidatafeed&top=1&format=json"





def get_final_stop_id(pid):
    response_2 = requests.get(API_URL_2_before + pid + API_URL_2_after) 
    data_2 = response_2.json()

    pattern = data_2.get("bustime-response", {}).get("ptr", [])[0].get("pt", []) 

    final_stop = pattern[len(pattern) - 1]
    final_stop_id = final_stop.get("stpid")

    return final_stop_id


def insert_into_database(stop_name, stop_id, route, direction, type_arrival, arrive_time, delay):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    insert_query = "INSERT INTO Delays_New (StopName, StopID, Route, Direction, TypeArrival, ArriveTime, Delay) VALUES (%s, %s, %s, %s, %s, %s, %s)"

    cursor.execute(insert_query, (stop_name, stop_id, route, direction, type_arrival, arrive_time, delay))

    db.commit()	
 
    cursor.close()
    db.close()


def poll_api(pid, vid, arrivals):
    while True: # first getprediction poll
        response = requests.get(API_URL_3_before + vid + API_URL_3_after)
        data = response.json()

        if "prd" in data.get("bustime-response", {}): # not an error
            prediction = data.get("bustime-response", {}).get("prd", [])[0] # set the initial fields

            last_stop_name = prediction.get("stpnm")
            last_stop_id = prediction.get("stpid") 
            last_route = prediction.get("rt")
            last_direction = prediction.get("rtdir") 
            last_type = prediction.get("typ")

            last_date_time = prediction.get("prdtm").split()

            last_date = last_date_time[0]
            last_time = last_date_time[1]

            last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

            time.sleep(1) # to wait a second before updating response

            c = True

            if last_type == "D": # wait until it departs to update pid to get final stop
                while c:
                    response = requests.get(API_URL_3_before + vid + API_URL_3_after)
                    data = response.json()

                    if "prd" in data.get("bustime-response", {}): # not an error, update predicted time since other fields are the same since it is still the same stop
                        prediction = data.get("bustime-response", {}).get("prd", [])[0]

                        if last_stop_id != prediction.get("stpid"): # departed
                            arrive_time = datetime.now()
			
                            delay = arrive_time - last_predicted_time # positive if late, negative if early

                            arrivals.append({
                                "last_stop_name": last_stop_name,
                                "last_stop_id": last_stop_id,
                                "last_route": last_route,
                                "last_direction": last_direction,
                                "last_type": last_type,
                                "last_predicted_time": last_predicted_time,
                                "delay": delay.total_seconds()
                            })

                            last_stop_name = prediction.get("stpnm")
                            last_stop_id = prediction.get("stpid") 
                            last_route = prediction.get("rt")
                            last_direction = prediction.get("rtdir") 
                            last_type = prediction.get("typ")

                            last_date_time = prediction.get("prdtm").split()

                            last_date = last_date_time[0]
                            last_time = last_date_time[1]

                            last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                            time.sleep(1) # to wait a second from response

                            print("inserted")
                            print(arrivals)

                            while True: # get the pid
                                response_v = requests.get(API_URL_1)
                                data_v = response_v.json()

                                if "vehicle" in data_1.get("bustime-response"): # not an error
                                    v = data_v.get("bustime-response", {}).get("vehicle", [])[0]

                                    pid = str(v.get("pid")) # have to wait for the bus to depart for the pid to update

                                    final_stop_id = get_final_stop_id(pid)

                                    c = False

                                    time.sleep(1) # to wait a second before while True for the rest of the stops
                
                                    break
    
                                time.sleep(1) # for the get the pid while True

                        else: # has not departed yet, just update prediction
                            last_date_time = prediction.get("prdtm").split()

                            last_date = last_date_time[0]
                            last_time = last_date_time[1]

                            last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                            print("did not depart yet")	

                    time.sleep(1) # for while c             

            else: # not a departure, so old pid is valid 
                final_stop_id = get_final_stop_id(pid)  

            print(f"last stop name: {last_stop_name}, last stop id: {last_stop_id}, last predicted date: {last_date}, last_predicted_time: {last_time}, last route: {last_route}, last direction: {last_direction}")

            break

        #it is an error, so keep poling until a valid prediction response
        time.sleep(1) # for outermost while True

    # rest of the stops

    a = False
	
    while True:	
        response = requests.get(API_URL_3_before + vid + API_URL_3_after)
        data = response.json()

        if "prd" in data.get("bustime-response", {}): # not an error
            prediction = data.get("bustime-response", {}).get("prd", [])[0]

            if last_stop_id != prediction.get("stpid") and a: # arrived to the final stop
                arrive_time = datetime.now()
			
                delay = arrive_time - last_predicted_time # positive if late, negative if early 

                arrivals.append({
                    "last_stop_name": last_stop_name,
                    "last_stop_id": last_stop_id,
                    "last_route": last_route,
                    "last_direction": last_direction,
                    "last_type": last_type,
                    "last_predicted_time": last_predicted_time,
                    "delay": delay.total_seconds()
                })

                # there is already a time.sleep(1) in the main, this would be the final one if here

                break  

            elif last_stop_id != prediction.get("stpid"): # arrived to a stop
                arrive_time = datetime.now()
			
                delay = arrive_time - last_predicted_time # positive if late, negative if early

                arrivals.append({
                    "last_stop_name": last_stop_name,
                    "last_stop_id": last_stop_id,
                    "last_route": last_route,
                    "last_direction": last_direction,
                    "last_type": last_type,
                    "last_predicted_time": last_predicted_time,
                    "delay": delay.total_seconds()
                })

                print("inserted")
                print(arrivals)

                last_stop_name = prediction.get("stpnm") # update all the fields for the next stop since the bus just arrived to the previously predicted stop
                last_stop_id = prediction.get("stpid")
                last_route = prediction.get("rt")
                last_direction = prediction.get("rtdir")
                last_type = prediction.get("typ")

                last_date_time = prediction.get("prdtm").split()

                last_date = last_date_time[0]
                last_time = last_date_time[1]

                last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                if last_stop_id == final_stop_id: # arrived to stop before final stop, predicted stop is final stop
                    a = True 

            else: # did not arrive yet 
                last_date_time = prediction.get("prdtm").split()

                last_date = last_date_time[0]
                last_time = last_date_time[1]

                last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))

                print("did not arrive yet")	

        # it is an error, keep polling until valid prediction response

        else:
            break

        time.sleep(1) # for while True for rest of the stops

            		                		
# Start polling
if __name__ == "__main__":
    while True: 
    # 1.  
        while True:
            response_1 = requests.get(API_URL_1)
            data_1 = response_1.json()

            if "vehicle" in data_1.get("bustime-response"):
                vehicle = data_1.get("bustime-response", {}).get("vehicle", [])[0]

                pid = str(vehicle.get("pid")) # have to wait for the bus to depart for the pid to update
                vid = vehicle.get("vid")

                print(f"pid: {pid}, vid: {vid}")

                break

            time.sleep(1) # for the inner while True

        # 2.
        arrivals = []

        poll_api(pid, vid, arrivals)

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
            insert_into_database(arrival.get("last_stop_name"), arrival.get("last_stop_id"), arrival.get("last_route"), arrival.get("last_direction"), arrival.get("last_type"), arrival.get("last_predicted_time"), arrival.get("delay"))

        print("inserted into database")

        time.sleep(1) # for the outer while True
