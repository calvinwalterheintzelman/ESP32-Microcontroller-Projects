import machine
from machine import ADC
from machine import Pin
from machine import PWM
from machine import Timer
from machine import TouchPad
from machine import I2C
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
from sys import exit
from math import sqrt
from math import atan
from math import pi
from struct import unpack
import upip
import crypt
import random
import json
import urequests

# how to use CryptAes
'''
cpt = crypt.CryptAes(b"1111"*8)
print(cpt.iv)
print(cpt)

cpt.encrypt(b'1234'*8)
an_hmac = cpt.sign_hmac(b"brya" * 8)
mes = cpt.send_mqtt(an_hmac)

print()
print('done')
print()
'''

# LED setup
red_led = Pin(15, mode=Pin.OUT, value=0)
gre_led = PWM(Pin(32), freq=10, duty=500)
onb_led = Pin(13, mode=Pin.OUT, value=0)
chk_led = Pin(14, mode=Pin.OUT, value=1)

# pushbutton setup
but1 = Pin(34, mode=Pin.IN, pull=Pin.PULL_DOWN)
but2 = Pin(21, mode=Pin.IN, pull=Pin.PULL_DOWN)

# Connecting to Wifi
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect("Y2K killed millions", "foogledoogle") # this is my phone's SSID and password
while(not station.isconnected()):
    pass

print("Oh Yes! Get Connected")
print("Connected to " + str(station.config('essid'))) # prints SSID Y2K killed millions
print("MAC Address: " + str(ubinascii.hexlify(station.config('mac'),':').decode())) # prints MAC address C4:85:08:49:57:37
print("IP Address: " + str(station.ifconfig()[0])) # prints IP address
print()

# install stuff with upip
'''
print("Starting Installations...")
upip.install('micropython-umqtt.simple')
upip.install('micropython-umqtt.robust')
upip.install('micropython-hmac')
print()
print("Installations Finished!")
'''

'''
Useful Websites:
https://github.com/micropython/micropython-lib/issues/304
https://github.com/micropython/micropython-lib/tree/master/umqtt.simple
'''

from umqtt.robust import MQTTClient
client = MQTTClient(client_id='1ebe9d4c-9e49-4bf4-8abb-f322009c377b', server='m16.cloudmqtt.com', port=17330, user='djizngjh', password='qkFOOBGLwyOA')

check = False

# This works!
def sub_cb(topic, msg):
    global check
    check = True
    if topic == b"SessionID":
        print("Session ID received!")
        session_id = b'%s'%(msg)
        x_d, y_d, z_d, t_d = get_data()
        cpt = crypt.CryptAes(b"1111"*4, session_id)
        t_send = round(t_d, 1)
        if x_d > 30 or y_d > 30 or z_d > 30:
            red_led.value(1)
        else:
            red_led.value(0)
        x_d = x_d.to_bytes(4, 'big')
        y_d = y_d.to_bytes(4, 'big')
        z_d = z_d.to_bytes(4, 'big')
        t_d = bytes(str(round(t_d, 1)), 'utf-8')
        
        sensor_data = x_d + y_d + z_d + t_d
    
        cpt.encrypt(sensor_data)
        an_hmac = cpt.sign_hmac(session_id)
        message = cpt.send_mqtt(an_hmac)
        
        print('Sending acceleration data...')
        dictionary = {}
        dictionary["value1"] = str(int.from_bytes(x_d, 'big'))
        dictionary["value2"] = str(int.from_bytes(y_d, 'big'))
        dictionary["value3"] = str(int.from_bytes(z_d, 'big'))

        urequests.request("POST", "http://maker.ifttt.com/trigger/sense/with/key/C6chg8ToX1kwz8YJSIY7kMEinDfvsCz-wIoOfZIEJZ", json=dictionary, headers={"Content-Type": "application/json"})
                
        print('Sending temperature, node ID, and session ID data...')
        dictionary = {}
        dictionary["value1"] = str(t_send)
        dictionary["value2"] = str(cpt.nodeid)
        dictionary["value3"] = str(cpt.sessionID)
        urequests.request("POST", "http://maker.ifttt.com/trigger/sense/with/key/C6chg8ToX1kwz8YJSIY7kMEinDfvsCz-wIoOfZIEJZ", json=dictionary, headers={"Content-Type": "application/json"})
        
        print('Sending buffer...')
        
        dictionary2 = {}
        dictionary2["value1"] = "__________________"
        dictionary2["value2"] = "__________________"
        dictionary2["value3"] = "__________________"
        urequests.request("POST", "http://maker.ifttt.com/trigger/sense/with/key/C6chg8ToX1kwz8YJSIY7kMEinDfvsCz-wIoOfZIEJZ", json=dictionary2, headers={"Content-Type": "application/json"})
        print('Done!')
        print()
        
        client.publish("Sensor_Data", message, True, 0)
        #client.wait_msg()
        print("Waiting for Session ID...")
      
        
    if topic == b"Acknowledgement": # topic is Acknowledgement
        #client.wait_msg()
        pass



# Initialize I2C Sensors
i2c = I2C(scl=Pin(22), sda=Pin(23), freq=400000)
temp_sens, accel = i2c.scan() # returns 0x48/72/1001000 and 0x53/83/1010011

# Button press interrupt functions
def but1_press(pin):
    global check
    check = False
    chk_led.value(0)
    onb_led.value(1)
    # Do stuff for 2.2.3
    # Initialize Accelerometer
    try:
        device_id = i2c.readfrom_mem(accel, 0, 1)
    except:
        print("ERROR: accelerometer device ID is inaccessible")
        exit()
            
    if device_id != b'\xe5':
        print('ERROR: accelerometer device ID is wrong')
        exit()
            
    i2c.writeto_mem(accel, 49, b'\x00') # sets 10-bit-resolution mode and +-2g
    i2c.writeto_mem(accel, 44, b'\x0d') # sets output data rate to 800 HZ
    i2c.writeto_mem(accel, 45, b'\x0b') # turn on measurements
    print("Accelerometer Initialization Complete")
    
    # Calibrate Accelerometer
    i2c.writeto_mem(accel, 30, b'\x01')
    i2c.writeto_mem(accel, 31, b'\x04')
    i2c.writeto_mem(accel, 32, b'\xc4') # was c4
    print("Accelerometer Calibration Completed")
    
    # Initialize Temperature Sensor
    try:
        device_id = i2c.readfrom_mem(temp_sens, 11, 1)
    except:
        print("ERROR: temperature sensor device ID is inaccessible")
        exit()
    if device_id != b'\xcb':
        print("ERROR: temperature sensor device ID is wrong, make sure the revision ID is 011 (in bits)!")            
        exit()
    i2c.writeto_mem(temp_sens, 3, b'\x80') # sets sensor to 16-but high resolution
    print("Temperature Sensor Calibration Complete")
    print()


    
def get_data():
        # do stuff for 2.2.4
        # SPINNER 1 ONLY CODE
        
        # read accelerometer sensor data
        data = i2c.readfrom_mem(accel, 50, 6)
        x_data = data[0] + data[1] * 256
        y_data = data[2] + data[3] * 256
        z_data = data[4] + data[5] * 256 # 65535 is max
        
        # read temperature sensor 
        temp_data = i2c.readfrom_mem(temp_sens, 0, 2)
        celc_temp = unpack('>h', temp_data)[0] * 0.0078
        return x_data, y_data, z_data, celc_temp

def but2_press(pin):
    if chk_led.value() == 0:

        onb_led.value(0)
        
        print("Connecting to MQTT Client...")
        client.set_callback(sub_cb)
        client.connect()

        print("Connected!")

        # the first argument is the topic, the second is the message
        client.subscribe("SessionID")
        client.subscribe("Acknowledgement")
        print('Waiting for message...')
        global check
        check = True
        sleep(0.5)
        
        #client.publish("SessidonID", 'connected', True, 0) # connected should be a random number
        
    else:
        print("Press the other button!")
        print()


d_v = 100 # debounce wait value
# button debouncing
def but1_debounce(pin):
    pin_held_time = 0
    while pin_held_time <= d_v:
        if pin.value() == 1:
            pin_held_time += 1
        else:
            break
        sleep(0.001)
    if pin_held_time == d_v + 1:
        but1_press(pin)

def but2_debounce(pin):

    pin_held_time = 0
    while pin_held_time <= d_v:
        if pin.value() == 1:
            pin_held_time += 1
        else:
            break
        sleep(0.001)
    if pin_held_time == d_v + 1:
        but2_press(pin)
    
        
# Button press interrupts
but1.irq(trigger=Pin.IRQ_RISING, handler=but1_debounce)
but2.irq(trigger=Pin.IRQ_RISING, handler=but2_debounce)


def check_for_stuff(temp):

    if check == True:
        client.check_msg()
        
tim1 = Timer(3)
tim1.init(period = 500, mode=Timer.PERIODIC, callback=check_for_stuff)
