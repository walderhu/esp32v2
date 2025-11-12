import time
from machine import Pin, CAN
import network

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


sta = network.WLAN(network.STA_IF)
if not sta.isconnected():
    connect_wifi("TP-Link_0D14", "24827089")
net = sta.ifconfig()[0]
_board = 1 if net == '192.168.0.123' else 2
led = Pin(2, Pin.OUT)
button = Pin(0, Pin.IN, Pin.PULL_UP)

def blink(d=0.05, f=0.05, n=3):
    for _ in range(n):
        led.on(); time.sleep(f)
        led.off(); time.sleep(d)

def button_pressed():
    return button.value() == 0

can = CAN(0, mode=CAN.NORMAL, extframe=False, prescaler=80, sjw=1, bs1=15, bs2=2)
can.setfilter(0, CAN.FILTER_MASK, 0, (0, 0))
print(f"Board mode: {'MASTER' if _board==1 else 'SLAVE'}")

if _board == 1:  
    while True:
        if button_pressed():
            msg = b"RUN_TASK"
            can.send(msg, 0x100)  # ID 0x100 для команды
            print("Sent command:", msg.decode())
            led.on()
            while button_pressed(): time.sleep_ms(50)
            led.off()

        # Приём ответа от слейва
        if can.any():
            msg = can.recv(0)
            if msg:
                data, can_id, timestamp = msg
                try:
                    print(f"Got response from ID {hex(can_id)}:", data.decode())
                except UnicodeError:
                    print(f"Got response from ID {hex(can_id)}: <decode error>")
        time.sleep_ms(50)

else:  # SLAVE
    while True:
        if can.any():
            msg = can.recv(0)
            if msg:
                data, can_id, timestamp = msg
                try:
                    cmd = data.decode().strip()
                except UnicodeError:
                    cmd = ""
                if cmd:
                    print("Got command:", cmd)
                    if cmd == "RUN_TASK":
                        status = "OK"
                        blink()
                    else:
                        status = "UNKNOWN"
                    # Ответ мастеру с другим ID
                    can.send(status.encode(), 0x101)  # 0x101 — ID для ответов
        time.sleep_ms(50)
