import network
import socket
import time
from machine import Pin

HOST = '192.168.0.123'
PORT = 5421
led = Pin(2, Pin.OUT)
button = Pin(0, Pin.IN, Pin.PULL_UP)

def connect_wifi(ssid="TP-Link_0D14", password="24827089"):
    sta = network.WLAN(network.STA_IF); sta.active(True)
    if not sta.isconnected():
        print("Connecting to WiFi...")
        sta.connect(ssid, password)
        t_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t_start) < 1e5: 
            if sta.isconnected(): break
            time.sleep_ms(500)
        else: raise Exception("WiFi connect failed")
    return sta.ifconfig()[0]

def run_slave():
    addr = socket.getaddrinfo('0.0.0.0', PORT)[0][-1]
    s = socket.socket(); s.bind(addr); s.listen(1)
    print('Slave listening on', addr)
    while True:
        cl, addr = s.accept()
        print('Master connected from', addr)
        try:
            while True:
                data = cl.recv(1024)
                if not data: break
                cmd = data.decode().strip()
                print('Received command:', cmd)
                if cmd == "ON":
                    led.value(1); cl.send(b"OK: LED ON")
                elif cmd == "OFF":
                    led.value(0); cl.send(b"OK: LED OFF")
                else: cl.send(b"ERROR: Unknown command")
        except Exception as e: print("Error:", e)
        finally: cl.close()

sta = network.WLAN(network.STA_IF)
if not sta.isconnected(): connect_wifi("TP-Link_0D14", "24827089")
net = sta.ifconfig()[0]
run_slave()

