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

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect("Y2K killed millions", "foogledoogle") # this is my phone's SSID and password
while(not station.isconnected()):
    pass

print("Oh Yes! Get Connected")
print("Connected to " + str(station.config('essid'))) # prints SSID Y2K killed millions
print("MAC Address: " + str(ubinascii.hexlify(station.config('mac'),':').decode())) # prints MAC address C4:85:08:49:57:37
print("IP Address: " + str(station.ifconfig()[0])) # prints IP address

def thingspeak():
    int_temp = esp32.raw_temperature()
    hall_val = esp32.hall_sensor()
    print()
    print("Internal Temperature: " + str(int_temp) + " Degrees Fahrenheit")
    print("Hall: " + str(hall_val))
    
    #send temperature info
    s = socket.socket()
    address = socket.getaddrinfo("thingspeak.com", 80)[0][-1]
    s.connect(address)
    s.send(b"GET https://api.thingspeak.com/update?api_key=0P5Y117MOWZABDHV&field1=" + str(int_temp) + " HTTP/1.0\r\n\r\n")
    s.close()
    time.sleep(18)

    #send hall info
    s = socket.socket()
    address = socket.getaddrinfo("thingspeak.com", 80)[0][-1]
    s.connect(address)
    s.send("GET https://api.thingspeak.com/update?api_key=0P5Y117MOWZABDHV&field2=" + str(hall_val) + " HTTP/1.0\r\n\r\n")
    s.close()

tim1 = Timer(0)

tim1.init(period=40000, mode=Timer.PERIODIC, callback=lambda t: thingspeak())

