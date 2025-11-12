import time
from machine import Pin, UART
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

TX_PIN = 17; RX_PIN = 16; DE_PIN = 4  
uart = UART(2, baudrate=115200, tx=Pin(TX_PIN), rx=Pin(RX_PIN))
de = Pin(DE_PIN, Pin.OUT)
de.value(0)  
led = Pin(2, Pin.OUT)
button = Pin(0, Pin.IN, Pin.PULL_UP)

def blink(d=0.05, f=0.05, n=3):
    for _ in range(n):
        led.on(); time.sleep(f)
        led.off(); time.sleep(d)

def button_pressed():
    return button.value() == 0

sta = network.WLAN(network.STA_IF)
if not sta.isconnected():
    connect_wifi("TP-Link_0D14", "24827089")
net = sta.ifconfig()[0]
_board = 1 if net == '192.168.0.123' else 2


print(f"Board mode: {'MASTER' if _board==1 else 'SLAVE'}")

if _board == 1:  # MASTER
    while True:
        if button_pressed():
            msg = b"RUN_TASK\n"
            de.value(1)  # включаем передачу
            uart.write(msg)
            de.value(0)
            try:
                print("Sent command:", msg.decode().strip())
            except UnicodeError:
                print("Sent command (decode error)")

            led.on()
            while button_pressed(): time.sleep_ms(50)
            led.off()

        if uart.any():
            resp = uart.readline()
            if resp:
                try:
                    print("Got response:", resp.decode(errors="ignore").strip())
                except UnicodeError:
                    print("Got response (decode error)")

        time.sleep_ms(100)

else:  # SLAVE
    while True:
        if uart.any():
            line = uart.readline()
            if line:
                try:
                    cmd = line.decode(errors="ignore").strip()
                except UnicodeError:
                    cmd = ""  # если не получилось декодировать
                if cmd:
                    print("Got command:", cmd)
                    if cmd == "RUN_TASK":
                        status = "OK"
                        blink()
                    else:
                        status = "UNKNOWN"
                    de.value(1)
                    uart.write((status + "\n").encode())
                    de.value(0)
        time.sleep_ms(50)
