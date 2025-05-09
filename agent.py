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

routes = {"OSW10", "OSW11", "OSW1A", "OSW46", "SY74", "SY76", "SY80"} 

API_URL_1_before = "https://bus-time.centro.org/bustime/api/v3/getvehicles?key=PUZXP7CxWkPaWnvDWdacgiS4M&rt="

# in between are all of the routes

API_URL_1_after = "&rptidatafeed&format=json"

API_URL_2_before = "https://bus-time.centro.org/bustime/api/v3/getpredictions?key=PUZXP7CxWkPaWnvDWdacgiS4M&vid="

# in between are all of the vids

API_URL_2_after = "&tmres=s&rptidatafeed&format=json"

traversal_id = 0 # increment this upon direction change and/or vid change after removing duplicates in insert_arrivals and insert it into database as well, global keyword to increment

# change time.sleep to 60 

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


def update_table(stop_name, stop_id, route, direction, arrive_time, delay, vid):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    update_query = (
        "INSERT INTO LastArrival2 (StopName, StopID, Route, Direction, ArriveTime, Delay, VehicleID) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE "
        "StopName = VALUES(StopName), StopID = VALUES(StopID), Route = VALUES(Route), "
        "Direction = VALUES(Direction), ArriveTime = VALUES(ArriveTime), Delay = VALUES(Delay), VehicleID = VALUES(VehicleID)"
    )

    cursor.execute(update_query, (stop_name, stop_id, route, direction, arrive_time, delay, vid))

    db.commit()

    cursor.close()
    db.close()


def insert_table(stop_name, stop_id, route, direction, arrive_time, delay, traversal_id):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    insert_query = "INSERT INTO Delays_n (StopName, StopID, Route, Direction, ArriveTime, Delay, ID) VALUES (%s, %s, %s, %s, %s, %s, %s)"

    cursor.execute(insert_query, (stop_name, stop_id, route, direction, arrive_time, delay, traversal_id))

    db.commit()	
 
    cursor.close()
    db.close()


def remove_rows(vid):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    delete_query = "DELETE FROM LastArrival2 WHERE VehicleID = %s"

    cursor.execute(delete_query, (vid,))

    db.commit()

    cursor.close()
    db.close()


def truncate_table():
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor()

    truncate_query = "TRUNCATE TABLE LastArrival2"

    cursor.execute(truncate_query)

    db.commit()

    cursor.close()
    db.close()


def remove_duplicates(arrivals): # call this on the arrivals in a dictionary in the dictionary_array if a bus is no longer showing predictions or changes routes
    added_arrival_stop_ids = set()

    arrivals_without_duplicates = []

    reversed_arrivals = list(reversed(arrivals))  

    ctr = 0

    for i in range(len(reversed_arrivals)):
        if i != len(reversed_arrivals) - 1:
            if reversed_arrivals[i].get("direction") != reversed_arrivals[i + 1].get("direction"): # duplicates at changing direction
                ctr += 1

                if reversed_arrivals[i].get("stop_id") not in added_arrival_stop_ids:
                    added_arrival_stop_ids.add(reversed_arrivals[i].get("stop_id"))

                    arrivals_without_duplicates.append(reversed_arrivals[i])

            elif reversed_arrivals[i].get("direction") == reversed_arrivals[i + 1].get("direction") and ctr > 0: # no more duplicates at changing direction
                added_arrival_stop_ids.clear()

                if ctr == 1: # no duplicates at changing direction
                    added_arrival_stop_ids.add(reversed_arrivals[i].get("stop_id"))

                    arrivals_without_duplicates.append(reversed_arrivals[i])
                
                ctr = 0

            else: # direction is not changing
                ctr = 0

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


def add_id(arrivals_without_duplicates, dictionary):
    # for each arrival in arrivals_without_duplicates, add another field to the dictionary as id, upon direction change, increment it 
    global traversal_id

    arrivals_same_route = [] # also make sure only the same route as dictionary

    for arrival in arrivals_without_duplicates:
        if arrival.get("route") == dictionary.get("route"):
            arrivals_same_route.append(arrival)

    arrivals_added_ids = []

    ctr = 0

    if arrivals_same_route:
        traversal_id += 1

        last_direction = arrivals_same_route[0].get("direction")

        for arrival in arrivals_same_route:
            if arrival.get("direction") != last_direction:
                ctr += 1
 
                if ctr == 2:
                    traversal_id += 1

                    ctr = 0

                last_direction = arrival.get("direction")

            arrivals_added_ids.append({
                "stop_name": arrival.get("stop_name"), 
                "stop_id": arrival.get("stop_id"), 
                "route": arrival.get("route"), 
                "direction": arrival.get("direction"), 
                "arrive_time": arrival.get("arrive_time"), 
                "delay": arrival.get("delay"), 
                "traversal_id": traversal_id
            })
        
    return arrivals_added_ids


def insert_arrivals(dictionary_array): # inserting for all arrivals in dictionary_array upon restart
    for dictionary in dictionary_array:
        for arrival in add_id(remove_duplicates(dictionary.get("arrivals")), dictionary):
            insert_table(arrival.get("stop_name"), arrival.get("stop_id"), arrival.get("route"), arrival.get("direction"), arrival.get("arrive_time"), arrival.get("delay"), arrival.get("traversal_id"))


def poll_api(dictionary_array, session): # only restarting if no predictions are being shown for any buses/error, get vehicles, get predictions, remove/adjust dictionaries, check for arrivals
    vids = ",".join(dictionary.get("vid") for dictionary in dictionary_array)

    try:
        response_2 = session.get(API_URL_2_before + vids + API_URL_2_after, timeout=30)
        data_2 = response_2.json()

        if "prd" in data_2.get("bustime-response", {}): # not an error
            last_predictions = data_2.get("bustime-response", {}).get("prd", []) # get the last_predictions array

            # check the dictionaries without None vids if they are predicting different routes. if they are, need to check if predicting the third stop in the sequence before retrying for a new vid

            for dictionary in dictionary_array[:]: # checking for if any vehicles are predicting only stops for a different route than in its dictionary
                if not any(last_prediction.get("vid") == dictionary.get("vid") and last_prediction.get("rt") == dictionary.get("route")
                    for last_prediction in last_predictions
                ):
                    # dont have to insert/clear since it is the first iteration

                    if any(last_prediction.get("vid") == dictionary.get("vid") and last_prediction.get("rt") in routes
                        for last_prediction in last_predictions
                    ):

                        remove_rows(dictionary.get("vid"))
                        
                        for last_prediction in last_predictions: 
                            if last_prediction.get("vid") == dictionary.get("vid") and last_prediction.get("rt") in routes:
                                dictionary["route"] = last_prediction.get("rt")

                                print(f"vid {dictionary.get('vid')} changed route to {dictionary.get('route')}")

                                break

                    else:
                    # dont have to insert since it is the first iteration
                    # either not showing predictions or predicting for a different route not in routes only

                        print(f"removed vid: {dictionary.get('vid')}, route: {dictionary.get('route')}")

                        remove_rows(dictionary.get("vid"))
  
                        dictionary_array.remove(dictionary)  

        else: # error like none of the buses showing predictions or running out of API calls, go back to main and try again
            truncate_table()

            return # do not need to insert_arrivals since they are all empty in the first iteration

        time.sleep(60)

    except requests.exceptions.RequestException:
        truncate_table()

        return # do not need to insert_arrivals since they are all empty in the first iteration

    # rest of the stops
	
    while True:	# add check for buses changing route (get new vids to replace the ones that changed and remove duplicates, insert into database, and clear the arrivals array) and retrying for buses that are not showing predictions (either not running on route anymore or was not showing them from the start, get new vids for them)

        # update the api url

        # retry for vids that are None
        all_routes = ",".join(routes)

        # dont need to account for the vids that are showing predictions on their respective routes, as long as the routes are in routes and they are showing predictions
                
        try:
            response_1 = session.get(API_URL_1_before + all_routes + API_URL_1_after, timeout=30)
            data_1 = response_1.json()

            if "vehicle" in data_1.get("bustime-response"): # else dont do anything, vids stay None
                vehicles = data_1.get("bustime-response", {}).get("vehicle", [])

                for vehicle in vehicles: 
                    if not any(dictionary.get("vid") == vehicle.get("vid") for dictionary in dictionary_array) and len(dictionary_array) < 10: # check if vehicle already in dictionary_array
                        dictionary_array.append({"route": vehicle.get("rt"), "vid": vehicle.get("vid"), "arrivals": []})

                for dictionary in dictionary_array:
                    print(f"route: {dictionary.get('route')}, vid: {dictionary.get('vid')}")  


            else:
                insert_arrivals(dictionary_array) # no routes showing any vehicles on them

                truncate_table()

                return

        except requests.exceptions.RequestException: # insert database procedure here and other returns
            insert_arrivals(dictionary_array)   

            truncate_table()
               
            return


        vids = ",".join(dictionary.get("vid") for dictionary in dictionary_array)
        
        #  accounts for previously removed dictionaries, will count all of their predictions (if any) as arrivals, but wont insert them anywhere

        try:
            response_2 = session.get(API_URL_2_before + vids + API_URL_2_after, timeout=30)
            data_2 = response_2.json()

            if "prd" in data_2.get("bustime-response", {}): # not an error, also check the routes for the vehicles
                current_predictions = data_2.get("bustime-response", {}).get("prd", []) 

                for dictionary in dictionary_array[:]: # checking for if any vehicles are predicting only stops for a different route than in its dictionary
                    if not any(current_prediction.get("vid") == dictionary.get("vid") and current_prediction.get("rt") == dictionary.get("route")
                        for current_prediction in current_predictions
                    ):

                        if any(current_prediction.get("vid") == dictionary.get("vid") and current_prediction.get("rt") in routes
                            for current_prediction in current_predictions
                        ):

                            for arrival in add_id(remove_duplicates(dictionary.get("arrivals")), dictionary): # adding all of the stops the vid arrived at, then setting vid to None and clearing the array
                            # add id

                                insert_table(arrival.get("stop_name"), arrival.get("stop_id"), arrival.get("route"), arrival.get("direction"), arrival.get("arrive_time"), arrival.get("delay"), arrival.get("traversal_id"))

                        # clear arrivals array and set route to the next predicted one in routes
  
                            dictionary["arrivals"].clear()

                            remove_rows(dictionary.get("vid"))
                        
                            for current_prediction in current_predictions: 
                                if current_prediction.get("vid") == dictionary.get("vid") and current_prediction.get("rt") in routes:
                                    dictionary["route"] = current_prediction.get("rt")

                                    print(f"vid {dictionary.get('vid')} changed route to {dictionary.get('route')}")

                                    break
        

                        else: 
                            for arrival in add_id(remove_duplicates(dictionary.get("arrivals")), dictionary): # adding all of the stops the vid arrived at, then setting vid to None and clearing the array
                            # add id

                                insert_table(arrival.get("stop_name"), arrival.get("stop_id"), arrival.get("route"), arrival.get("direction"), arrival.get("arrive_time"), arrival.get("delay"), arrival.get("traversal_id"))

                        # either not showing predictions or predicting for a different route not in routes only

                            print(f"removed vid: {dictionary.get('vid')}, route: {dictionary.get('route')}")

                            remove_rows(dictionary.get("vid"))
  
                            dictionary_array.remove(dictionary)  
                                                                         
                
                # check for arrival if predictions in last_predictions are not in current_predictions. if not, get the time now and convert the prdtm into a datetime object and append to its arrivals array

                for last_prediction in last_predictions: # poll for vehicles if they are None in the dictionary every minute
                    if not any(
                        current_prediction.get("stpid") == last_prediction.get("stpid") and 
                        current_prediction.get("rtdir") == last_prediction.get("rtdir") and # if buses change routes/are not displaying predictions, poll for vehicles again
                        current_prediction.get("rt") == last_prediction.get("rt") and 
                        current_prediction.get("origtatripno") == last_prediction.get("origtatripno") 
                        for current_prediction in current_predictions
                    ):
                        # get the times
                        last_date_time = last_prediction.get("prdtm").split()

                        last_date = last_date_time[0]
                        last_time = last_date_time[1]

                        last_predicted_time = datetime(int(last_date[0:4]), int(last_date[4:6]), int(last_date[6:8]), int(last_time[0:2]), int(last_time[3:5]), int(last_time[6:8]))  

                        arrive_time = datetime.now()

                        delay = arrive_time - last_predicted_time # positive if late, negative if early

                        # append to respective arrivals array, last_prediction is the one that got arrived at
                        for dictionary in dictionary_array:
                            if dictionary.get("vid") == last_prediction.get("vid") and dictionary.get("route") == last_prediction.get("rt"):
                                dictionary.get("arrivals").append({
                                    "stop_name": last_prediction.get("stpnm"),
                                    "stop_id": last_prediction.get("stpid"),
                                    "route": last_prediction.get("rt"),
                                    "direction": last_prediction.get("rtdir"),
                                    "arrive_time": arrive_time,
                                    "delay": delay.total_seconds()
                                })

                                # inserted stops
                                update_table(last_prediction.get("stpnm"), last_prediction.get("stpid"), last_prediction.get("rt"), last_prediction.get("rtdir"), arrive_time, delay.total_seconds(), last_prediction.get("vid"))

                                print(f"inserted {last_prediction.get('stpnm')} {last_prediction.get('stpid')} {last_prediction.get('rt')} {last_prediction.get('rtdir')} {arrive_time} {delay.total_seconds()}")
                                print(f"vid: {last_prediction.get('vid')}")
                                print(f"{dictionary.get('route')}: {len(dictionary.get('arrivals'))}") # length of route's arrivals

                                break # an arrival only goes in one dictionary


                        # if vids are None, then no predictions are being shown. if they are not None, then they could still be showing predictions for different routes

                last_predictions = current_predictions # update

                # if a vid is only showing predictions for a different route, insert to database, reset arrivals array and set vid to None, retry         

            # error like none of the buses showing predictions or running out of API calls, call remove_duplicates and insert all of the arrivals without None vid into the database
            else: # have to do this inside while True as well
                insert_arrivals(dictionary_array)

                truncate_table()

                # does not matter about setting vids to None and clearing the array since returning from the function
                return

            time.sleep(60)

        except requests.exceptions.RequestException: # have to add the insert into database procedure into all of the returns, including the exceptions (maybe put in in a function)
            insert_arrivals(dictionary_array)

            truncate_table()

            return  

            		                		
# start polling
if __name__ == "__main__":
    while True:
        if datetime.now().hour >= 5:
            pass

        else:
            print("not after 5 am")
 
            time.sleep(60)

            continue
            
        try:
            session = create_session()

        except Exception:
            time.sleep(60)

            continue

        # 1. 
        dictionary_array = []
 
        while True:
            API_URL_1 = API_URL_1_before
       
            
            for route in routes:
                API_URL_1 += route + ','

            API_URL_1 += API_URL_1_after

            try:
                response_1 = session.get(API_URL_1, timeout=30)
                data_1 = response_1.json()

                if "vehicle" in data_1.get("bustime-response"):
                    vehicles = data_1.get("bustime-response", {}).get("vehicle", [])

                    for vehicle in vehicles: # inserting vehicles, as well as their respective routes
                        if len(dictionary_array) < 10:
                            dictionary_array.append({"route": vehicle.get("rt"), "vid": vehicle.get("vid"), "arrivals": []}) # check if vid exists

                    for dictionary in dictionary_array:
                        print(f"route: {dictionary.get('route')}, vid: {dictionary.get('vid')}")  
                       
                    print(len(dictionary_array))

                    break

                else:
                    time.sleep(60)

                    print("no buses for all routes")

            except requests.exceptions.RequestException:
                time.sleep(60)
 
                # continue

        # 2.
        #  have an array of dictionaries, one per route. the dictionaries contain the route, vid (None if none), and array of arrivals. once a vehicle has changed routes or the API ran out of calls or an error, do remove_duplicates on it and insert into the database

        poll_api(dictionary_array, session)

        session.close()

        time.sleep(60) # for the outer while True

