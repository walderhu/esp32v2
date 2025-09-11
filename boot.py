#!/usr/bin/env micropython
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

# from libs import utelegram 
# token, chat_id = config['telegram'].values()
# bot = utelegram.ubot(token)
# bot.send(chat_id, "ESP32 подключен ✅")

import webrepl
if wlan.isconnected(): webrepl.start()
else: print("WebREPL не стартует")

# WebREPL server started on http://192.168.0.232:8266/
# Started webrepl in normal mode
# print('IP', wlan.ifconfig())
