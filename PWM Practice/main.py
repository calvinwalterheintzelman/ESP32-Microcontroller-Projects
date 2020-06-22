import machine

year = int(input("Year? "))
month = int(input("Month? "))

month_dict = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}

day = int(input("Day? "))
weekday = int(input("Weekday? "))

weekday_dict = {
    0: "Monday",
    1: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday"
}
hour = int(input("Hour? "))
minute = int(input("Minute? "))
second = int(input("Second? "))
microsecond = int(input("Microsecond? "))

def print_time_and_date(dt):
    print("Today is " + weekday_dict[dt[3]] + " " + month_dict[dt[1]] + ' ' + str(dt[2]) + ", " + str(dt[0]) + ".")
    print("The time is " + str(dt[4]) + ":" + str(dt[5]) + ":" + str(dt[6]) + ":" + str(dt[7]) + ".")
    

rtc = machine.RTC()
tim = machine.Timer(-1)
rtc.datetime((year, month, day, weekday, hour, minute, second, microsecond))
tim.init(period=5000, mode=machine.Timer.PERIODIC, callback=lambda t: print_time_and_date(rtc.datetime()))

