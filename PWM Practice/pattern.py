import machine
from machine import ADC
from machine import Pin
from machine import PWM

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
tim = machine.Timer(0)
rtc.datetime((year, month, day, weekday, hour, minute, second, microsecond))
tim.init(period=30000, mode=machine.Timer.PERIODIC, callback=lambda t: print_time_and_date(rtc.datetime()))

state = 0


adc = ADC(Pin(32, Pin.IN, Pin.PULL_UP))
adc.atten(ADC.ATTN_6DB)
adc.width(ADC.WIDTH_9BIT)

# max duty cycle is 1023
# freq goes from 0 to 40000000
pwm0 = PWM(Pin(27), freq=10, duty=256)
pwm1 = PWM(Pin(33), freq=10, duty=256)




switch1 = Pin(21, Pin.IN, Pin.PULL_DOWN)
sav_but_val = 0
while switch1.value() == 0:
    pass
#timer0 = machine.Timer(1)
#timer0.init(period=500, mode=machine.Timer.PERIODIC, callback=lambda t: switch_leds(pwm0, pwm1))

def do_switching(timer1, adc, pwm0, state):
    if state == 1: #change red frequency
        timer1.deinit()
        timer1.init(period=100 * round(adc.read()/511) + 1, mode=machine.Timer.PERIODIC, callback=lambda t: flip_red(red))
    elif state == 2: #change green duty
        pwm0.duty(round(1023 * adc.read() / 511))

def flip_red(red):
    red.value(not red.value())

pwm1.deinit()
red = Pin(33, Pin.OUT)
timer0 = machine.Timer(-1)
timer1 = machine.Timer(1)
print(round(adc.read()/511))
timer1.init(period=100* round(adc.read()/511) + 1, mode=machine.Timer.PERIODIC, callback=lambda t: flip_red(red))
timer0.init(period = 100, mode=machine.Timer.PERIODIC, callback=lambda t: do_switching(timer1, adc, pwm0, state))


# 0 is green, 1 is red
while 1:
    while(switch1.value() == 1):
        state = 1
    while(switch1.value() == 0):
        pass
    while(switch1.value() == 1):
        state = 2
    while(switch1.value() == 0):
        pass
