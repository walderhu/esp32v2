from machine import Pin
import network, CAN
import time

CAN_TX = 5; CAN_RX = 4; LED_PIN = 2; BUTTON_PIN = 0
CMD_CAN_ID = 0x100; MASTER_IP = "192.168.0.123"; LOOPBACK = False  

def connect_wifi(timeout = 15):
    WIFI_SSID = "TP-Link_0D14"; WIFI_PASS = "24827089"
    sta = network.WLAN(network.STA_IF); sta.active(True)
    if sta.isconnected(): return sta.ifconfig()[0]
    print("Connecting to WiFi...")
    sta.connect(WIFI_SSID, WIFI_PASS)
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < timeout * 1000:
        if sta.isconnected(): return sta.ifconfig()[0]
        time.sleep_ms(500)
    print("WiFi FAILED → using SLAVE role")
    return "0.0.0.0"

MY_IP = connect_wifi()
print(f"ROLE: {'MASTER' if (MY_IP == MASTER_IP) else 'SLAVE'} | IP: {MY_IP}")
led = Pin(LED_PIN, Pin.OUT)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
can = CAN(0, tx=CAN_TX, rx=CAN_RX,
    mode=CAN.LOOPBACK if LOOPBACK else CAN.NORMAL,
    bitrate=500000, extframe=False)

print("CAN bus ready (TX→TX, RX→RX)")

def send_cmd(cmd: str):
    data = cmd.encode('utf-8')
    if len(data) > 8:
        print(f"CMD too long: {cmd}")
        return
    can.send(list(data), CMD_CAN_ID)
    print(f"→ {cmd}")

def parse_cmd(data: bytes) -> str:
    try: return data.decode('utf-8').strip()
    except: return ""

def button_pressed(): return button.value() == 0
print("Running...")
while True:
    time.sleep_ms(50)
    if button_pressed():
        cmd = "ON"; print("Sending:", cmd); send_cmd(cmd)
        while button_pressed(): time.sleep_ms(50)
        cmd = "OFF"; print("Sending:", cmd); send_cmd(cmd)
    if can.any():
        try:
            msg_id, _, _, data_bytes = can.recv()
            if msg_id == CMD_CAN_ID:
                cmd = parse_cmd(bytes(data_bytes))
                if cmd:
                    print(f"CMD: {cmd}")
                    if cmd == "ON": led.value(1)
                    elif cmd == "OFF": led.value(0)
        except Exception as e: print("CAN recv error:", e)
    time.sleep_ms(10)