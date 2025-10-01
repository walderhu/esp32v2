import usocket as socket
import network
import ujson

with open("config.json") as f: config = ujson.load(f)
wlan = network.WLAN(network.STA_IF); wlan.active(True)

ssid, password = config['wifi'].values()
while True:
    try: wlan.connect(ssid, password)
    except: continue
    if wlan.isconnected(): break

s = socket.socket()
s.bind(('0.0.0.0', 23))   
s.listen(1)
print("Waiting for rshell connection...")

conn, addr = s.accept()
print("Connected from", addr)

import os, sys
sys.stdin = conn
sys.stdout = conn
sys.stderr = conn
