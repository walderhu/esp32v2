# can_bus_wifi_role.py
from machine import Pin
import CAN
import time
import network

# ====================== КОНФИГУРАЦИЯ ======================
CAN_TX = 5
CAN_RX = 4
LED_PIN = 2
BUTTON_PIN = 0

CMD_CAN_ID = 0x100
MASTER_IP = "192.168.0.123"  # ← ТВОЯ МАСТЕР-ПЛАТА

LOOPBACK = False

# =========================================================

# --- Подключение к Wi-Fi ---
def connect_wifi(ssid="TP-Link_0D14", password="24827089", timeout=15):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if sta.isconnected():
        return sta.ifconfig()[0]
    
    print("Connecting to WiFi...")
    sta.connect(ssid, password)
    t_start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t_start) < timeout * 1000:
        if sta.isconnected():
            ip = sta.ifconfig()[0]
            print(f"WiFi connected: {ip}")
            return ip
        time.sleep_ms(500)
    
    print("WiFi FAILED — using DEFAULT role (SLAVE)")
    return "0.0.0.0"  # fallback

# --- Определяем роль по IP ---
try:
    MY_IP = connect_wifi()
    IS_MASTER = (MY_IP == MASTER_IP)
except:
    MY_IP = "0.0.0.0"
    IS_MASTER = False

MY_ID = 1 if IS_MASTER else 2
print(f"Device: {'MASTER' if IS_MASTER else 'SLAVE'} | IP: {MY_IP} | ID: {MY_ID}")

# --- Инициализация ---
led = Pin(LED_PIN, Pin.OUT)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP) if IS_MASTER else None

can = CAN(
    0,
    tx=CAN_TX,
    rx=CAN_RX,
    mode=CAN.LOOPBACK if LOOPBACK else CAN.NORMAL,
    bitrate=500000,
    extframe=False
)

print("CAN bus ready")

# --- Протокол ---
def send_cmd(cmd: str):
    data = cmd.encode('utf-8')
    if len(data) > 8:
        print(f"CMD too long: {cmd}")
        return
    can.send(list(data), CMD_CAN_ID)
    print(f"→ {cmd}")

def parse_cmd(data: bytes) -> str:
    try:
        return data.decode('utf-8').strip()
    except:
        return ""

# --- Основной цикл ---
last_button = None
print("Running...")

while True:
    # === MASTER: кнопка ===
    if IS_MASTER and button:
        current = button.value() == 0
        if current != last_button:
            cmd = "ON" if current else "OFF"
            send_cmd(cmd)
            time.sleep_ms(300)
        last_button = current

    # === ВСЕ: приём команд по CAN ===
    if can.any():
        msg = can.recv()
        msg_id, _, _, data_bytes = msg
        if msg_id == CMD_CAN_ID:
            cmd = parse_cmd(bytes(data_bytes))
            if cmd:
                print(f"CMD: {cmd}")
                if cmd == "ON":
                    led.value(1)
                elif cmd == "OFF":
                    led.value(0)

    time.sleep_ms(10)