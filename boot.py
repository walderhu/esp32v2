#!/usr/bin/env mp
import ujson
from utime import sleep
from machine import Pin
import network

def blink(*, led=Pin(2, Pin.OUT), delay=0.05, repeat=3):
    for i in range(1, repeat * 2 + 1):
        led.value(i % 2); sleep(delay)

with open("config.json") as f: config = ujson.load(f)
wlan = network.WLAN(network.STA_IF); wlan.active(True)

ssid, password = config['wifi'].values()
while True:
    try: wlan.connect(ssid, password)
    except: continue
    if wlan.isconnected(): break

import webrepl
if wlan.isconnected(): webrepl.start()
else: print("WebREPL не стартует")

blink()