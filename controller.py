from datetime import datetime, timedelta
import mysql.connector

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD", 	
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD" 
}

def select_table1(route): # need to account for both directions
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary = True)

    select_query = "SELECT * FROM LastArrival2 WHERE Route = %s"

    cursor.execute(select_query, (route,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def select_table2(stop_id, route, direction):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary = True)

    select_query = "SELECT * FROM Delays_n  WHERE StopID = %s AND Route = %s AND Direction = %s"

    cursor.execute(select_query, (stop_id, route, direction))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


if __name__ == "__main__":
    stop_id = input("Enter stop id: ")
    route = input("Enter route: ")
    direction = input("Enter direction: ")

    last_arrivals = select_table1(route) # get the stops of the last arrived buses on the route

    predicted_times = []

    if len(last_arrivals) == 0:
        print("no bus on route")
    
    else:
        rows_user_input = select_table2(stop_id, route, direction)

        for last_arrival in last_arrivals:
            print(f"Last Arrival: {last_arrival.get('ArriveTime')}")
   
            rows_last_arrival = select_table2(last_arrival.get("StopID"), route, last_arrival.get("Direction"))


            print(f"Rows Last Arrival: {rows_last_arrival}")
            print(f"Rows User Input: {rows_user_input}")

            last_arrival_time = last_arrival.get("ArriveTime")

            ctr = 0
            total_sum = 0

            for row_last_arrival in rows_last_arrival:
                for row_user_input in rows_user_input: # could do a check for an id one less or more for different directions for multiple round trips
                    if row_user_input.get("ID") == row_last_arrival.get("ID") and row_user_input.get("ArriveTime") > row_last_arrival.get("ArriveTime"):
                        ctr += 1

                        total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get("ArriveTime")).total_seconds()

                        print(f"Last Arrival Row ArriveTime: {row_last_arrival.get('ArriveTime')}")
                        print(f"User Input Row ArriveTime: {row_user_input.get('ArriveTime')}")

                        print(f"Difference: {(row_user_input.get('ArriveTime') - row_last_arrival.get('ArriveTime')).total_seconds()}, User Input ID: {row_user_input.get('ID')}, Last Arrival ID: {row_last_arrival.get('ID')}")
        

                        break

                    elif row_user_input.get("ID") > row_last_arrival.get("ID"):
                        break


            if ctr == 0:
                # get consecutive round trips, have to check for a row_last_arrival that has an ID 1 greater than a row_user_input]
                for row_user_input in rows_user_input:
                    for row_last_arrival in rows_last_arrival:
                        if (row_user_input.get("ID") == row_last_arrival.get("ID") + 1 and 
                            row_user_input.get("ArriveTime") > row_last_arrival.get("ArriveTime") and 
                            row_user_input.get("ArriveTime").date() == row_last_arrival.get("ArriveTime").date()
                        ):
                            ctr += 1

                            total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get("ArriveTime")).total_seconds()

                            print(f"Last Arrival Row ArriveTime: {row_last_arrival.get('ArriveTime')}")
                            print(f"User Input Row ArriveTime: {row_last_arrival.get('ArriveTime')}")

                            print(f"Difference: {(row_user_input.get('ArriveTime') - row_last_arrival.get('ArriveTime')).total_seconds()}, User Input ID: {row_user_input.get('ID')}, Last Arrival ID: {row_last_arrival.get('ID')}")

                            break

  
            if ctr == 0:
                print("no data")

            else:
                predicted_time = last_arrival_time + timedelta(seconds = (total_sum / ctr))

                print(f"Predicted Time: {predicted_time}")

                predicted_times.append(predicted_time)

    if len(predicted_times) == 0:
        print("no prediction")

    else:
        print(f"Final Predicted Time: {min(predicted_times)}")                    
        

