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
import dht
import usocket as socket
import gc

gc.collect()
esp.osdebug(None)

# A0 (or GPIO #26) is the gre led
# A1 (or GPIO #25) is the red led
# A2 and A3 (GPIO #34 and #39 respectively) are buttons
gre_led = Pin(26, mode=Pin.OUT, value=1)
red_led = Pin(25, mode=Pin.OUT, value=1)
but1 = Pin(34, mode=Pin.IN, pull=Pin.PULL_DOWN)
but2 = Pin(21, mode=Pin.IN, pull=Pin.PULL_DOWN)

# Global variables
#temp = esp32.raw_temperature() # measure temperature sensor data
#hall = esp32.hall_sensor() # measure hall sensor data
#red_led_state = "hi" # string, check state of red led, ON or OFF
#green_led_state = "bye" # string, check state of red led, ON or OFF


def web_page(temp, hall, red_led_state, green_led_state, but1_state, but2_state):
    """Function to build the HTML webpage which should be displayed
    in client (web browser on PC or phone) when the client sends a request
    the ESP32 server.
    
    The server should send necessary header information to the client
    (YOU HAVE TO FIND OUT WHAT HEADER YOUR SERVER NEEDS TO SEND)
    and then only send the HTML webpage to the client.
    
    Global variables:
    TEMP, HALL, RED_LED_STATE, GREEN_LED_STAT
    """
    
    html_webpage = """<!DOCTYPE HTML><html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
    <style>
    html {
     font-family: Arial;
     display: inline-block;
     margin: 0px auto;
     text-align: center;
    }
    h2 { font-size: 3.0rem; }
    p { font-size: 3.0rem; }
    .units { font-size: 1.5rem; }
    .sensor-labels{
      font-size: 1.5rem;
      vertical-align:middle;
      padding-bottom: 15px;
    }
    .button {
        display: inline-block; background-color: #e7bd3b; border: none; 
        border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none;
        font-size: 30px; margin: 2px; cursor: pointer;
    }
    .button2 {
        background-color: #4286f4;
    }
    </style>
    </head>
    <body>
    <h2>ESP32 WEB Server</h2>
    <p>
    <i class="fas fa-thermometer-half" style="color:#059e8a;"></i> 
    <span class="sensor-labels">Temperature</span> 
    <span>"""+str(temp)+"""</span>
    <sup class="units">&deg;F</sup>
    </p>
    <p>
    <i class="fas fa-bolt" style="color:#00add6;"></i>
    <span class="sensor-labels">Hall</span>
    <span>"""+str(hall)+"""</span>
    <sup class="units">V</sup>
    </p>
    <p>
    RED LED Current State: <strong>""" + red_led_state + """</strong>
    </p>
    <p>
    <a href="/?red_led=on"><button class="button">RED ON</button></a>
    </p>
    <p><a href="/?red_led=off"><button class="button button2">RED OFF</button></a>
    </p>
    <p>
    GREEN LED Current State: <strong>""" + green_led_state + """</strong>
    </p>
    <p>
    <a href="/?green_led=on"><button class="button">GREEN ON</button></a>
    </p>
    <p><a href="/?green_led=off"><button class="button button2">GREEN OFF</button></a>
    </p>
    <p>
    SWITCH1 Current State: <strong>""" + but1_state + """</strong>
    </p>
    <p>
    SWITCH2 Current State: <strong>""" + but2_state + """</strong>
    </p>
    </body>
    </html>"""
    return html_webpage

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect("Y2K killed millions", "foogledoogle") # this is my phone's SSID and password
while(not station.isconnected()):
    pass


print("Oh Yes! Get Connected")
print("Connected to " + str(station.config('essid'))) # prints SSID Y2K killed millions
print("MAC Address: " + str(ubinascii.hexlify(station.config('mac'),':').decode())) # prints MAC address C4:85:08:49:57:37
print("IP Address: " + str(station.ifconfig()[0])) # prints IP address

sock = socket.socket()
address = socket.getaddrinfo(station.ifconfig()[0], 80)[0][-1]
sock.bind(address)
sock.listen(4)

red_led_state = "ON"
gre_led_state = "ON"
but1_state = 'OFF'
but2_state = 'OFF'


while True:
    connection, address = sock.accept()
    get_str = connection.recv(1024)
    get_str = get_str[0:50]

    if "green_led=off" in get_str:
        gre_led.value(0)
        gre_led_state = "OFF"
    if "green_led=on" in get_str:
        gre_led.value(1)
        gre_led_state = "ON"
    if "red_led=off" in get_str:
        red_led.value(0)
        red_led_state = "OFF"
    if "red_led=on" in get_str:
        red_led.value(1)
        red_led_state = "ON"
        
    if but1.value() == 1:
        but1_state = 'ON'
    else:
        but1_state = 'OFF'
    print(but2.value())
    if but2.value() == 1:
        but2_state = 'ON'
    else:
        but2_state = 'OFF'
    
    webpage = web_page(esp32.raw_temperature(), esp32.hall_sensor(), red_led_state, gre_led_state, but1_state, but2_state)

    connection.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n' + webpage)
    connection.close()

