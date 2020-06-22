import machine
from machine import ADC
from machine import Pin
from machine import PWM
from machine import Timer
from machine import TouchPad
import esp
import network
from time import sleep
import ubinascii
import ntptime
import utime
import time
import esp32

print()
wake_reason = machine.wake_reason()
if wake_reason == 3: # button
    print("Woke up from button press (EXT1 wake-up)")
if wake_reason == 4: # timer
    print("Woke up from a timer")
if wake_reason == 5:
    print("Woke up from touchpad touch")
print()

# A0 (or GPIO #26) is the gre led
# A1 (or GPIO #25) is the red led
# A2 and A3 (GPIO #34 and #39 respectively) are buttons
but1 = Pin(34, mode=Pin.IN, pull=Pin.PULL_DOWN)
but2 = Pin(39, mode=Pin.IN, pull=Pin.PULL_DOWN)
esp32.wake_on_ext1((but1, but2), esp32.WAKEUP_ANY_HIGH)

red_led = Pin(25, Pin.OUT)
red_led.value(1)

touch1 = TouchPad(Pin(14)) # yellow wire
touch2 = TouchPad(Pin(32)) # blue wire
# touchx.read() (x is 1 or 2) returns a number smaller than 200 when touched.

touch1.config(450)
esp32.wake_on_touch(True)


station = network.WLAN(network.STA_IF)
station.active(True)
station.connect("Y2K killed millions", "foogledoogle") # this is my phone's SSID and password
while(not station.isconnected()):
    pass

print("Oh Yes! Get Connected")
print("Connected to " + str(station.config('essid'))) # prints SSID Y2K killed millions
print("MAC Address: " + str(ubinascii.hexlify(station.config('mac'),':').decode())) # prints MAC address C4:85:08:49:57:37
print("IP Address: " + str(station.ifconfig()[0])) # prints IP address

ntptime.settime()
print()
rtc = machine.RTC()
rtc.datetime((rtc.datetime()[0],
              rtc.datetime()[1],
              rtc.datetime()[2],
              rtc.datetime()[3],
              rtc.datetime()[4] - 4,
              rtc.datetime()[5],
              rtc.datetime()[6],
              rtc.datetime()[7]))

def print_datetime(rtc):
    print("Date: " + '{:02}'.format(rtc.datetime()[1]) + '/' +
      '{:02}'.format(rtc.datetime()[2]) + '/' + '{:02}'.format(rtc.datetime()[0]))
    print("Time: " + '{:02}'.format(rtc.datetime()[4]) + ':' + '{:02}'.format(rtc.datetime()[5])
      + ':' + '{:02}'.format(rtc.datetime()[6]) + ' HRS')
    print()

time_clock = Timer(0)
time_clock.init(period=15000, mode=Timer.PERIODIC, callback=lambda t: print_datetime(rtc))
# online clock works great!



gre_led = Pin(26, Pin.OUT)
red_led = Pin(25, Pin.OUT)
def read_touch2(touch2):
    if touch2.read() < 500:
        gre_led.value(1)
    else:
        gre_led.value(0)

t_touch2 = Timer(1)
t_touch2.init(period=10, mode=Timer.PERIODIC, callback=lambda t: read_touch2(touch2))


sleep(30) # FIXME
print("I am awake. Going to sleep for 1 minute")
red_led.value(0)
machine.deepsleep(60000) # FIXME

