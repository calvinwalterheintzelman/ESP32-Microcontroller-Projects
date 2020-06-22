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

# SCL and SDA need pullup resistors

# LED initialization
gre_led = Pin(32, mode=Pin.OUT, value=0)
red_led = Pin(15, mode=Pin.OUT, value=0)
yel_led = Pin(14, mode=Pin.OUT, value=0)

onb_led = PWM(Pin(13), freq = 10, duty =0)
interfacing = Pin(12, mode=Pin.OUT, value=0)

# switch buttons
but1 = Pin(34, mode=Pin.IN, pull=Pin.PULL_DOWN)
but2 = Pin(21, mode=Pin.IN, pull=Pin.PULL_DOWN)

# I2C pins and initialization
i2c = I2C(scl=Pin(22), sda=Pin(23), freq=400000)

def but1_press(pin): # TODO
    interfacing.value(1)
    
def but2_press(pin): # TODO
    interfacing.value(0)

but1.irq(trigger=Pin.IRQ_RISING, handler=but1_press)
but2.irq(trigger=Pin.IRQ_RISING, handler=but2_press)



time_c = 0.005 # was 0.005

# set bit that enables measurements
x_v = 0
y_v = 0
z_v = 0

while not interfacing.value():
    pass

onb_led.freq(10)

orig_temp = 0
old_celc_diff = 0
while(1):
    if interfacing.value():
        red_led.value(0)
        gre_led.value(0)
        yel_led.value(0)
        # Initialize Accelerometer
        temp_sens, accel = i2c.scan() # returns 0x48/72/1001000 and 0x53/83/1010011
        try:
            device_id = i2c.readfrom_mem(accel, 0, 1)
        except:
            print("ERROR: accelerometer device ID is inaccessible")
            exit()
            
        if device_id != b'\xe5':
            print('ERROR: accelerometer device ID is wrong')
            exit()
            
        i2c.writeto_mem(accel, 49, b'\x08') # sets full-resolution mode and +-2g
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
            
        i2c.writeto_mem(temp_sens, 3, b'\x80')

        print("Temperature Sensor Calibration Complete")
        print()
        onb_led.duty(1023)
    
        while interfacing.value():
            pass
        onb_led.duty(512)
        orig_temp = i2c.readfrom_mem(temp_sens, 0, 2)
        orig_temp = unpack('>h', orig_temp)[0] * 0.0078
    else:
        
        x_change = 0
        y_change = 0
        z_change = 0
        
        for i in range(10):
            data = i2c.readfrom_mem(accel, 50, 6)
            x_data = data[0] + data[1] * 256
            y_data = data[2] + data[3] * 256
            z_data = data[4] + data[5] * 256 # 65535 is max
           
            # below is velocity code
            if i == 0:
                x_v = x_data
                y_v = y_data
                z_v = z_data
                if x_v > 32767:
                    x_v -= 65545
                if y_v > 32767:
                    y_v -= 65545
                if z_v > 32767:
                    z_v -= 65545
                if x_data > 32767:
                    x_ang = x_data - 65536
                else:
                    x_ang = x_data
                if y_data > 32767:
                    y_ang = y_data - 65536
                else:
                    y_ang = y_data
                if z_data > 32767:
                    z_ang = z_data - 65536
                else:
                    z_ang = z_data
                x_ang = round((x_ang-6) * 360/515/2)
                y_ang = round((y_ang - 20) * 360/515/2)
                z_ang = round((z_ang-10) * -360/520/2)
                if x_ang > 30 or x_ang < -30 or y_ang > 30 or y_ang < -30 or z_ang > 30:
                    yel_led.value(1)
                else:
                    yel_led.value(0)
                print('Angles')
                print("Pitch: " + str(x_ang) + " Deg")
                print("Roll: " + str(y_ang) + " Deg")
                print("Theta: " + str(z_ang) + " Deg")
            else:
                if x_data >= 0 and x_data < 32767:
                    x_change += x_v - x_data
                else:
                    x_change += x_v - (x_data - 65535)
                if y_data >= 0 and y_data < 32767:
                    y_change += y_v - y_data
                else:
                    y_change += y_v - (y_data - 65535)
                if z_data >= 0 and z_data < 32767:
                    z_change += z_v - z_data
                else:
                    z_change += z_v - (z_data - 65535)
                
            sleep(time_c)
        
        print()
        print('Velocities:')
        g_c = 9.8 * 4 / 65535
        x_vel = x_change * time_c * g_c
        y_vel = y_change * time_c * g_c
        z_vel = z_change * time_c * g_c
        print("X velocity: " + str(round(x_vel, 3)) + " m/s")
        print("Y velocity: " + str(round(y_vel, 3)) + " m/s")
        print("Z velocity: " + str(round(z_vel, 3)) + " m/s")
        print()
        

        c = 0.002
        if x_vel > c or x_vel < -c or y_vel > c or y_vel < -c or z_vel > c:
            red_led.value(1)
        else:
            red_led.value(0)
        move_check = 0.00028
        if x_vel > move_check or x_vel < -move_check or y_vel > move_check \
           or y_vel < -move_check or z_vel > move_check or z_vel < -move_check:
            gre_led.value(0)
        else:
            gre_led.value(1)
            
        # Temperature detection
        temp_data = i2c.readfrom_mem(temp_sens, 0, 2)
        celc_temp = unpack('>h', temp_data)[0] * 0.0078
        print('Temperature: ' + str(round(celc_temp, 1)) + " Deg C")
        celc_diff = round(celc_temp - orig_temp)
        if celc_diff != old_celc_diff:
            onb_led.freq(10 + celc_diff * 5)
            old_celc_diff = celc_diff
        print()
