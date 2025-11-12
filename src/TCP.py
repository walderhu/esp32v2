import network
import socket
import time
from machine import Pin

PORT = 5421
MASTER = '192.168.0.123'
SLAVE = '192.168.0.232'
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

def button_pressed(): return button.value() == 0

def run_master():
    s = socket.socket(); s.connect((SLAVE, PORT))
    print(f"Connected to slave at {SLAVE}:{PORT}")
    try:
        while True:
            time.sleep_ms(50)
            if button_pressed():
                cmd = "ON"; print("Sending:", cmd); s.send(cmd.encode())
                response = s.recv(1024); print("Response:", response.decode())
                
                while button_pressed(): time.sleep_ms(50)
                cmd = "OFF"; print("Sending:", cmd); s.send(cmd.encode())
                response = s.recv(1024); print("Response:", response.decode())
    except Exception as e: print("Error:", e)
    finally: s.close()


sta = network.WLAN(network.STA_IF)
if not sta.isconnected():
    connect_wifi("TP-Link_0D14", "24827089")
net = sta.ifconfig()[0]
ROLE = "MASTER" if net == MASTER else "SLAVE"
if ROLE == "MASTER": run_master()
else: run_slave()
