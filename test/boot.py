# http://192.168.1.4:8266/
import webrepl
import network
from machine import Pin
from time import sleep

def blink(led=Pin(2, Pin.OUT), d=0.05, f=0.05, n=3):
    for _ in range(n): led.on(); sleep(f); led.off(); sleep(d)

wlan = network.WLAN(network.STA_IF); wlan.active(True)
wlan.connect('letai_B359', 'Uui84KLq')
while not wlan.isconnected(): pass
else: blink(n=2)
webrepl.passwd = b''
webrepl.start()