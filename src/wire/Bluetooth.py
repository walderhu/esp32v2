import network
import bluetooth
import socket
import time
from machine import Pin

PORT = 5421
MASTER = '192.168.0.123'
SLAVE = '192.168.0.232'

led = Pin(2, Pin.OUT)
button = Pin(0, Pin.IN, Pin.PULL_UP)

bt = bluetooth.Bluetooth()
bt.active(True)

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

def button_pressed():
    return button.value() == 0

# -------------------- SLAVE --------------------
def run_slave():
    print("Starting Bluetooth SLAVE...")
    bt.config(name="ESP32_SLAVE")
    bt.advertise(name="ESP32_SLAVE")

    conn = None

    @bt.on_connect
    def on_connect(c):
        nonlocal conn
        conn = c
        print("Master connected via Bluetooth:", c)

        @c.on_recv
        def on_recv(data):
            cmd = data.decode().strip()
            print("Received command:", cmd)
            if cmd == "ON":
                led.value(1)
                c.send(b"OK: LED ON\n")
            elif cmd == "OFF":
                led.value(0)
                c.send(b"OK: LED OFF\n")
            else:
                c.send(b"ERROR: Unknown command\n")

    while True:
        time.sleep(1)

# -------------------- MASTER --------------------
def run_master():
    print("Starting Bluetooth MASTER...")
    bt.config(name="ESP32_MASTER")
    print("Scanning for ESP32_SLAVE...")

    devices = bt.discover()
    target = None

    for d in devices:
        name, addr = d[0], d[1]
        print("Found:", name, addr)
        if name == "ESP32_SLAVE":
            target = addr
            break

    if not target:
        raise Exception("Slave not found")

    print("Connecting to ESP32_SLAVE", target)
    conn = bt.connect(target)
    print("Connected!")

    try:
        while True:
            time.sleep_ms(50)
            if button_pressed():
                cmd = "ON"
                print("Sending:", cmd)
                conn.send(cmd.encode() + b"\n")

                time.sleep_ms(100)
                while button_pressed():
                    time.sleep_ms(50)

                cmd = "OFF"
                print("Sending:", cmd)
                conn.send(cmd.encode() + b"\n")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()

# -------------------- MAIN --------------------
sta = network.WLAN(network.STA_IF)
if not sta.isconnected(): connect_wifi("TP-Link_0D14", "24827089")
net = sta.ifconfig()[0]
ROLE = "MASTER" if net == MASTER else "SLAVE"
print("Device role:", ROLE)
if ROLE == "MASTER": run_master()
else: run_slave()
