#!/usr/bin/env mp
import ujson
import network
from machine import Pin
from utime import sleep
import sys; sys.path.append('/remote')

def include(name: str): 
    if not name.endswith('.py'): name = f'{name}.py'
    with open(f'/remote/{name}') as f: exec(f.read())  


class ClearScreen:
    def __repr__(self):
        print("\033[2J\033[H", end='')
        return ''  

c = ClearScreen()
clear = ClearScreen()


def blink(*, led=Pin(2, Pin.OUT), delay=0.05, flash=0.05, repeat=3):
    for _ in range(repeat):
        led.on(); sleep(flash)
        led.off(); sleep(delay)

def connect_wifi():
    with open("config.json") as f: config = ujson.load(f)
    wlan = network.WLAN(network.STA_IF); wlan.active(True)
    ssid, password = config['wifi_phone'].values()

    while True:
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            print("  Wi-Fi...", end='\r'); sleep(0.5)  
        else:
            blink(repeat=5, delay=0.5)
            return wlan.ifconfig()[0]
        
        
print(f'Сеть: {connect_wifi()}')

# import utelnetserver; utelnetserver.start()   
import webrepl; webrepl.start()   