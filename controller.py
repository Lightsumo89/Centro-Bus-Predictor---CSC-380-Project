import mysql.connector
from datetime import datetime, timedelta, time, date

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

    select_query = "SELECT * FROM Delays_n  WHERE StopID = %s AND Route = %s AND Direction = %s" # add order by id

    cursor.execute(select_query, (stop_id, route, direction))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def select_table3(route, direction, stop_id, hour):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary = True)

    select_query = f"SELECT * FROM Delays_n WHERE Route = %s AND Direction = %s AND StopID = %s AND TIME(ArriveTime) >= '{int(hour):02}:00:00' AND TIME(ArriveTime) < '{(int(hour) + 1):02}:00:00'"

    cursor.execute(select_query, (route, direction, stop_id))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


if __name__ == "__main__":
    day = input("Enter day: ")
    month = input("Enter month: ")
    year = input("Enter year: ")

    input_date = date(int(year), int(month), int(day))

    if datetime.now().date() != input_date:
        hour = input("Enter hour: ") # only if the day is not the current day

    route = input("Enter route: ")
    direction = input("Enter direction: ")
    stop_id = input("Enter stop id: ")

    if datetime.now().date() != input_date:
        rows = select_table3(route, direction, stop_id, hour)

        if len(rows) == 0:
            print("no bus for given time")

        else:
            timestamps = [row.get("ArriveTime").hour * 3600 + row.get("ArriveTime").minute * 60 + row.get("ArriveTime").second for row in rows]

            average_time = int(sum(timestamps) / len(timestamps))

            predicted_time = time(hour=average_time // 3600,
                                  minute=(average_time % 3600) // 60,
                                  second=average_time % 60
                             )

            predicted_time = datetime.combine(input_date, predicted_time)

            print(predicted_time)

    else:
        last_arrivals = select_table1(route) # get the stops of the last arrived buses on the route

        predicted_times = []

        if len(last_arrivals) == 0:
            print("no bus on route")
    
        else:
            rows_user_input = select_table2(stop_id, route, direction)

            ctr = 0
            total_sum = 0

            for last_arrival in last_arrivals:
                # print(f"Last Arrival: {last_arrival.get('ArriveTime')}")

                last_arrival_time = last_arrival.get("ArriveTime") 

                if last_arrival.get("StopID") == stop_id: # last arrival is the same as user inputted stop
                    # get all of the arrivals for that stop and check for same day and ID greater than 1
                    # print(f"Rows User Input 1: {rows_user_input}")
                    # print(f"Rows User Input 2: {rows_user_input}")

                    for row_user_input1 in rows_user_input:
                        for row_user_input2 in rows_user_input:
                            if row_user_input2.get("ID") == row_user_input1.get("ID") + 1 and row_user_input1.get("ArriveTime").date() == row_user_input2.get("ArriveTime").date():
                                ctr += 1

                                total_sum += (row_user_input2.get("ArriveTime") - row_user_input1.get("ArriveTime")).total_seconds()

                             #   print(f"User Input 1 ArriveTime: {row_user_input1.get('ArriveTime')}")
                             #   print(f"User Input 2 ArriveTime: {row_user_input2.get('ArriveTime')}")

                              #  print(f"Difference: {(row_user_input2.get('ArriveTime') - row_user_input1.get('ArriveTime')).total_seconds()}, User Input 1 ID: {row_user_input1.get('ID')}, User Input 2 ID: {row_user_input2.get('ID')}")

                                break
                                
   

                else:
                    last_arrival_time = last_arrival.get("ArriveTime")

                    rows_last_arrival = select_table2(last_arrival.get("StopID"), last_arrival.get("Route"), last_arrival.get("Direction"))

                    # print(f"Rows Last Arrival: {rows_last_arrival}")
                    # print(f"Rows User Input: {rows_user_input}")

                    for row_last_arrival in rows_last_arrival:
                        for row_user_input in rows_user_input: # could do a check for an id one less or more for different directions for multiple round trips
                            if row_user_input.get("ID") == row_last_arrival.get("ID") and row_user_input.get("ArriveTime") > row_last_arrival.get("ArriveTime"):
                                ctr += 1

                                total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get("ArriveTime")).total_seconds()

                               # print(f"Last Arrival Row ArriveTime: {row_last_arrival.get('ArriveTime')}")
                                # print(f"User Input Row ArriveTime: {row_user_input.get('ArriveTime')}")

                                # print(f"Difference: {(row_user_input.get('ArriveTime') - row_last_arrival.get('ArriveTime')).total_seconds()}, User Input ID: {row_user_input.get('ID')}, Last Arrival ID: {row_last_arrival.get('ID')}")
        

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

                                    # print(f"Last Arrival Row ArriveTime: {row_last_arrival.get('ArriveTime')}")
                                    # print(f"User Input Row ArriveTime: {row_last_arrival.get('ArriveTime')}")

                                   #  print(f"Difference: {(row_user_input.get('ArriveTime') - row_last_arrival.get('ArriveTime')).total_seconds()}, User Input ID: {row_user_input.get('ID')}, Last Arrival ID: {row_last_arrival.get('ID')}")

                                    break

  
                if ctr == 0:
                    print("no data")

                else:
                    predicted_time = last_arrival_time + timedelta(seconds = (total_sum / ctr))

                    # print(f"Predicted Time: {predicted_time}")

                    predicted_times.append(predicted_time)

        if len(predicted_times) == 0:
            print("no prediction")

        else:
            print(f"Final Predicted Time: {min(predicted_times)}")                    
        

                 
        


