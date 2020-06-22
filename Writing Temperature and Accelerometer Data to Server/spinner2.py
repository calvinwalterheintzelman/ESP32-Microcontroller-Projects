from machine import Pin, Timer, RTC, TouchPad, deepsleep, PWM, I2C
from time import sleep
import esp32
import ntptime
import machine
from umqtt.robust import MQTTClient
import crypt
import random
import json
import ubinascii
#  Connects to wifi prints Mac + IP address
def do_connect():
    import network
    import ubinascii
    print("Oh yes! Get connected")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        #wlan.connect('Y2K killed millions', 'foogledoogle')
        wlan.connect('esp32', '12345678')
        while not wlan.isconnected():
            pass
    print('Connected to', wlan.config('essid'))
    print('Mac Address:', ubinascii.hexlify(wlan.config('mac'),':').decode())
    print('IP Address', wlan.ifconfig()[0])
    
    
def callback(temp):
    pass



def button_interrupt_1(temp1):
    global demo
    global client
    button1.irq(trigger=Pin.IRQ_RISING, handler=callback)
    
    while True:
        sleep(0.001)
        if button1.value() == 0:
            break
    
    button1.irq(trigger=Pin.IRQ_RISING, handler=button_interrupt_1)
    
    init_acc()
    calibrate()
    init_temp()
    
    onboard.value(1)
    AES.G_LED = PWM(Pin(21),freq=100,duty=0)
    AES.R_LED = Pin(27,Pin.OUT, value=0)
    if demo:
        demo = False
        client.disconnect()
        client = None
    
def button_interrupt_2(temp):
    global demo
    global button2
    button2.irq(trigger=Pin.IRQ_RISING, handler=callback)
    while True:
        sleep(0.001)
        if button2.value() == 0:
            break
    button2.irq(trigger=Pin.IRQ_RISING, handler=button_interrupt_2)
    mqtt_server()
    demo = True
    AES.G_LED = PWM(Pin(21),freq=10,duty=512)
    AES.R_LED = Pin(27,Pin.OUT, value=0)
    onboard.value(0)
    
def init_acc():
    if int.from_bytes(i2c.readfrom_mem(83,0,1),"big") == 0b11100101:
        print("valid id")
    else:
        ValueError("Invalid id")
    i2c.writeto_mem(83, 0x2c, b'\x0d')
    i2c.writeto_mem(83, 0x2d, b'\x08')
    i2c.writeto_mem(83, 0x31, b'\x08')


def complement_2s(bits):
    if bits & 0x0200 == 0x0200:#  negative
        bits &= 0x03ff
        bits = bits - (1 << 10)
        return bits
    else:
        return bits & 0x1ff
        
def calibrate():
    global prev_ax
    global prev_ay
    global prev_az
    temp = bytearray(1)
    accel = bytearray(6)
    x_accel, y_accel, z_accel = 0,0,0
    for i in range(900):
        i2c.readfrom_mem_into(83, 0x32, accel)
        
        x_accel_t = accel[1] << 8 | accel[0]
        y_accel_t = accel[3] << 8 | accel[2]
        z_accel_t = accel[5] << 8 | accel[4]

        x_accel_t = complement_2s(x_accel_t)
        y_accel_t = complement_2s(y_accel_t)
        z_accel_t = complement_2s(z_accel_t-256)
    
        
        x_accel += x_accel_t // 4
        y_accel += y_accel_t // 4
        z_accel += z_accel_t // 4
            
    if x_accel < 0:    
        i2c.writeto_mem(83, 0x1E, bytearray([256 - (x_accel//900)]))
    else:
        i2c.writeto_mem(83, 0x1E, bytearray([x_accel//900]))
    if y_accel < 0:
        i2c.writeto_mem(83, 0x1F, bytearray([256 - (y_accel//900)]))
    else:
        i2c.writeto_mem(83, 0x1F, bytearray([y_accel//900]))
    if z_accel < 0:
        i2c.writeto_mem(83, 0x20, bytearray([256 - (z_accel//900)]))
    else:
        i2c.writeto_mem(83, 0x20, bytearray([z_accel//900]))
    
    temp = bytearray(1)
    accel = bytearray(6)
    while True:
        i2c.readfrom_mem_into(83, 0x32, accel)
        x_accel_t = accel[1] * 256 + accel[0]
        y_accel_t = accel[3] * 256 + accel[2]
        z_accel_t = accel[5] * 256 + accel[4]
        #print("83 x: {}".format(complement_2s(x_accel_t) / 256))
        prev_ax = complement_2s(x_accel_t) / 256
        #print("83 y: {}".format(complement_2s(y_accel_t) / 256))
        prev_ay = complement_2s(y_accel_t) / 256
        #print("83 z: {}".format(complement_2s(z_accel_t) / 256))
        break
        

#set to 16 bit resolution
def init_temp():
    global prev_temp
    i2c.writeto_mem(72, 0x03,b'\x80')
    temp = bytearray(2)
    i2c.readfrom_mem_into(72, 0x00, temp)
    if (bytes([temp[0]]) >= b'\x80'):
        prev_temp = ((temp[0] * 256 + temp[1]) - 65536)/128
    else:
        prev_temp = (temp[0] * 256 + temp[1])/128 

def sub_cb(topic, msg):
    global client
    global AES
    global client_int
    global wait
    #client_int.deinit()
    #print(type(msg), msg)
    #print("message received:", json.loads(msg))
    try:
        #print(msg)
        msg = json.loads(msg)
        
        msg['eiv'] = ubinascii.unhexlify(msg['eiv'])
        msg['enid'] = ubinascii.unhexlify(msg['enid'])
        msg['ed'] = ubinascii.unhexlify(msg['ed'])
        msg['hmac'] = ubinascii.unhexlify(msg['hmac'])
    
        #print(msg)
        
    except:
        print("not good")
        client.publish("Acknowledge", "Failed", True, 0) 
        client_interrupt(None)
        client.wait_msg()
        return
    ans = AES.verify_hmac(msg)
    #print(b'%s'%(msg['eiv']))
    #print(b'%s'%(msg['ed']))
    #print(b'%s'%(msg['enid']))
    #print(b'%s'%(msg['ed']))
    #print(b'%s %s %s'%(AES.datakey, AES.ivkey, AES.staticiv))
    #print(ans)
    if ans == "Failed Authentication":
        client.publish("Acknowledge", ans, True, 0)   
        #client_int = Timer(1)
        #client_int.init(period=1000, mode=Timer.PERIODIC, callback=client_interrupt)
    else:
        #client.publish("Acknowledge", ans, True, 0)
        print("good")
        client.publish("Acknowledge", AES.decrypt(msg), True, 0)
        #  AES.decrypt(msg)
        #client_int = Timer(1)
        #client_int.init(period=1000, mode=Timer.PERIODIC, callback=client_interrupt)
    AES.sessionID = ''
    for i in range(16):
        AES.sessionID += chr(random.randint(48,122))
    client.publish("SessionID", AES.sessionID, True, 0)
    #wait = True
    #client_interrupt(None)
    #client.wait_msg()
    



def client_interrupt(temp):
    global AES
    global wait
    global client
    #AES.sessionID = bytes(random.getrandbits(8) for _ in range(16))
    #client.publish("SessionID", AES.sessionID, True, 0)
    #print(AES.sessionID)
    #client.publish("SessionID", b"four" * 4, True, 0)
    if demo:
        print('ok')
        client.check_msg()
    #client.wait_msg()
   # print(wait)
   # if wait:
   
     #   wait = False
    

def mqtt_server():
    global client
    global client_int
    if client == None:
        client = MQTTClient(client_id='1ebe9d4c-9e49-4bf4-8abb-f322009c377c', server='m16.cloudmqtt.com', port=17330, user='djizngjh', password='qkFOOBGLwyOA')
    #client = MQTTClient(client_id='1ebe9d4c-9e49-4bf4-8abb-f322009c377c', server='m16.cloudmqtt.com', port=17661, user='pnxixoiw', password='bNugts8UAhj9')
        client.set_callback(sub_cb)
        client.connect()

        print("Connected to MQTT Client")

    # the first argument is the topic, the second is the message
        client.subscribe("Sensor_Data")
    
    
        client_int = Timer(3)
        client_int.init(period=1000, mode=Timer.PERIODIC, callback=client_interrupt)
    #client.publish("SessionID", b"four"*8, True, 0)
        client.publish("SessionID", AES.sessionID, True, 0)
        client_interrupt(None)
    
    #while 1:
    #    client.check_msg()
        
    

if __name__ == "__main__":
    '''do_connect()
    a = crypt.CryptAes()
    print(a.iv)
    print(a.verify_hmac("fdsiufhisuf"))
        on.loads(a)))
    '''
    client_int = None
    client = None
    do_connect()
    AES = crypt.CryptAes(b'2222'*4, b'four' * 4)
    demo = False
    AES.G_LED = PWM(Pin(21),freq=100,duty=0)
    AES.R_LED = Pin(27,Pin.OUT, value=0)
    
    onboard = Pin(13, Pin.OUT, value=0)
    
    button1 = Pin(12, Pin.IN, Pin.PULL_DOWN)
    button2 = Pin(14, Pin.IN, Pin.PULL_DOWN)
    
    button1.irq(trigger=Pin.IRQ_RISING, handler=button_interrupt_1)
    button2.irq(trigger=Pin.IRQ_RISING, handler=button_interrupt_2)
    
    i2c = I2C(scl=Pin(22), sda=Pin(23), freq=400000)
    
    wait = True