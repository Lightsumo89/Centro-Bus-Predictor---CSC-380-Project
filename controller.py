import mysql.connector
from collections import defaultdict
from datetime import datetime, timedelta, time, date

DATABASE = {
    "host": "pi.cs.oswego.edu",
    "user": "CSC380_25S_TeamD",
    "password": "csc380_25s",
    "database": "CSC380_25S_TeamD"
}


def select_table1(route):  # need to account for both directions
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary=True)

    select_query = "SELECT * FROM LastArrival2 WHERE Route = %s"

    cursor.execute(select_query, (route,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def select_table2(stop_id, route, direction):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary=True)

    select_query = "SELECT * FROM Delays_n WHERE StopID = %s AND Route = %s AND Direction = %s ORDER BY ID"  # add order by id

    cursor.execute(select_query, (stop_id, route, direction))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def select_table3(route, direction, stop_id, hour):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary=True)

    select_query = f"SELECT * FROM Delays_n WHERE Route = %s AND Direction = %s AND StopID = %s AND TIME(ArriveTime) >= '{int(hour):02}:00:00' AND TIME(ArriveTime) < '{(int(hour) + 1):02}:00:00'"

    cursor.execute(select_query, (route, direction, stop_id))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def select_table4(route):
    db = mysql.connector.connect(**DATABASE)
    cursor = db.cursor(dictionary=True)

    select_query = f"SELECT * FROM Delays_n WHERE Route = %s ORDER BY ID, ArriveTime"  # add order by id and arrive time

    cursor.execute(select_query, (route,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


def contains_stop(id_array, stop_id):  # return arrive time if stop_id is in id_array, else return None
    for arrival in id_array:
        if stop_id == arrival.get("StopID"):
            return arrival

    return None


if __name__ == "__main__":
    day = input("Enter day: ")
    month = input("Enter month: ")
    year = input("Enter year: ")

    input_date = date(int(year), int(month), int(day))

    if datetime.now().date() != input_date:
        hour = input("Enter hour: ")  # only if the day is not the current day

    route = input("Enter route: ")
    direction = input("Enter direction: ")
    stop_id = input("Enter stop id: ")

    if datetime.now().date() != input_date:
        rows_hour = select_table3(route, direction, stop_id, hour)

        if len(rows_hour) == 0:
            print("no bus for given time")

        else:
            timestamps = [
                row_hour.get("ArriveTime").hour * 3600 + row_hour.get("ArriveTime").minute * 60 + row_hour.get(
                    "ArriveTime").second for row_hour in rows_hour]

            average_time = int(sum(timestamps) / len(timestamps))

            predicted_time = time(hour=average_time // 3600,
                                  minute=(average_time % 3600) // 60,
                                  second=average_time % 60
                                  )

            predicted_time = datetime.combine(input_date, predicted_time)

            print(predicted_time)

    else:
        last_arrivals = select_table1(route)  # get the stops of the last arrived buses on the route

        predicted_times = []

        if len(last_arrivals) == 0:
            print("no bus on route")

        else:
            rows_user_input = select_table2(stop_id, route, direction)

            ctr = 0
            total_sum = 0

            for last_arrival in last_arrivals:
                last_arrival_time = last_arrival.get("ArriveTime")

                rows_last_arrival = select_table2(last_arrival.get("StopID"), last_arrival.get("Route"),
                                                  last_arrival.get("Direction"))

                for row_last_arrival in rows_last_arrival:
                    for row_user_input in rows_user_input:  # could do a check for an id one less or more for different directions for multiple round trips
                        if row_user_input.get("ID") == row_last_arrival.get("ID") and row_user_input.get(
                                "ArriveTime") > row_last_arrival.get("ArriveTime"):
                            ctr += 1

                            total_sum += (row_user_input.get("ArriveTime") - row_last_arrival.get(
                                "ArriveTime")).total_seconds()

                            break

                        elif row_user_input.get("ID") > row_last_arrival.get("ID"):
                            break

                if ctr == 0:
                    consecutive_round_trips = defaultdict(list)

                    consecutive_round_trips_day = []  # array of arrivals in consecutive round trips per day (keep track of the max arrival time of all of them)

                    rows_route = select_table4(route)

                    arrive_day = rows_route[0].get("ArriveTime").date()
                    traversal_id = rows_route[0].get("ID")

                    b = False

                    for row_route in rows_route:
                        if row_route.get("ArriveTime").date() != arrive_day:
                            if any(row_route.get("ID") == c[-1][-1].get("ID") for c in
                                   consecutive_round_trips_day):  # include the next day's 0:00:00 hour in the previous flag, set a flag so that the change in id clears the consecutive_round_trips_day array, loop through individually

                                for c in consecutive_round_trips_day:
                                    if row_route.get("ID") == c[-1][-1].get("ID"):  # maximum id array in c array
                                        c[-1].append(row_route)  # last array in c adds an arrival with the same id

                                        break

                                b = True

                            else:  # the id is different from the previous day to the first in the next day so clear the array
                                # print("different day")

                                for c in consecutive_round_trips_day:  # c is an array containing the arrivals of  consecutive round trips (could include those with just 1 round trip)
                                    if len(c) >= 2:  # c contains each arrival, need to check if number of different ids is greater than or equal to 2
                                        consecutive_round_trips[arrive_day].append(c)  # an array of arrays

                                consecutive_round_trips_day.clear()

                                consecutive_round_trips_day.append([[row_route]])

                                arrive_day = row_route.get("ArriveTime").date()  # update arrive_day
                                traversal_id = row_route.get("ID")  # update traversal_id

                        elif row_route.get("ID") != traversal_id:  # check where to append it
                            if b:  # clear the consecutive_round_trips array like in the else above and reset b to False
                                # print("different day")

                                for c in consecutive_round_trips_day:  # c is an array containing the arrivals of  consecutive round trips (could include those with just 1 round trip)
                                    if len(c) >= 2:  # c contains each arrival, need to check if number of different ids is greater than or equal to 2
                                        consecutive_round_trips[arrive_day].append(c)  # an array of arrays

                                consecutive_round_trips_day.clear()

                                consecutive_round_trips_day.append([[row_route]])

                                arrive_day = row_route.get("ArriveTime").date()  # update arrive_day
                                traversal_id = row_route.get("ID")  # update traversal_id

                                b = False

                            else:
                                # print("different id") # add debug statements like this

                                non_intersecting_round_trips = []

                                for c in consecutive_round_trips_day:  # look for non intersecting round trips and take the minimum of the differences from the max and min
                                    max_round_trip = c[-1][-1]  # maximum of each last array in c array

                                    if row_route.get("ArriveTime") > max_round_trip.get("ArriveTime"):
                                        non_intersecting_round_trips.append(max_round_trip)

                                # find the minimum and put it in the correct c array in consecutive_round_trips_day, check if within 20 minutes

                                if len(non_intersecting_round_trips) == 0:
                                    consecutive_round_trips_day.append(
                                        [[row_route]])  # append to new consecutive round trip array of id arrays

                                else:
                                    max_max_round_trip = max(non_intersecting_round_trips,
                                                             key=lambda x: x.get("ArriveTime"))  # this needs max

                                    if (row_route.get("ArriveTime") - max_max_round_trip.get(
                                            "ArriveTime")).total_seconds() <= 1200:  # remove 1200 conditional
                                        # append to correct c array, get id of the min and look for that id in the c arrays
                                        max_max_round_trip_id = max_max_round_trip.get("ID")

                                        for c in consecutive_round_trips_day:
                                            if max_max_round_trip_id == c[-1][-1].get("ID"):
                                                c.append(
                                                    [row_route])  # create a new id array in c for the next id for a consecutive round trip

                                                break

                                    else:
                                        # append to a new array, a separate consecutive round trip
                                        consecutive_round_trips_day.append([[row_route]])

                                    # update traversal_id
                                    traversal_id = row_route.get("ID")

                        else:  # same ID, just append it to the most recent appended from the else if
                            if len(consecutive_round_trips_day) == 0:  # first route of the day
                                consecutive_round_trips_day.append([[row_route]])

                            else:
                                for c in consecutive_round_trips_day:
                                    if row_route.get("ID") == c[-1][-1].get("ID"):  # maximum id array in c array
                                        c[-1].append(row_route)  # last array in c adds an arrival with the same id

                                        break

                    for day, cr_list in consecutive_round_trips.items():
                        for cr in cr_list:  # cr is each consecutive round trip, containing arrays of the arrivals, where all with the same id go in an array
                            for i in range(len(cr_list) - 1):
                                arrive_time_i1 = contains_stop(cr[i], last_arrival.get(
                                    "StopID"))  # cr[i] is each id array in cr

                                if arrive_time_i1 is not None:  # stop_id inputted from user
                                    arrive_time_i2 = contains_stop(cr[i + 1], stop_id)

                                    if arrive_time_i2 is not None:
                                        ctr += 1

                                        total_sum += (arrive_time_i2.get("ArriveTime") - arrive_time_i1.get(
                                            "ArriveTime")).total_seconds()

                                    else:
                                        continue

                                else:
                                    continue

                if (ctr == 0):
                    print("no data")

                else:
                    predicted_time = last_arrival_time + timedelta(seconds=(total_sum / ctr))

                    predicted_times.append(predicted_time)

            if len(predicted_times) == 0:
                print("no prediction")

            else:
                print(f"{min(predicted_times)}")




