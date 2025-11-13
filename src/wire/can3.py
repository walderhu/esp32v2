# can3.py — ИСПРАВЛЕНО: 8-байтные сообщения + рабочие фильтры
from machine import Pin
import CAN
import time

# ====================== КОНФИГУРАЦИЯ ======================
CAN_TX = 5
CAN_RX = 4
LED_PIN = 2
BUTTON_PIN = 0

BROADCAST_ID = 0x000
BASE_CMD_ID  = 0x100
BASE_ACK_ID  = 0x200

ADDR_PINS = [12, 13, 14]
LOOPBACK = False

def get_my_id() -> int:
    addr = 0
    for i, pin in enumerate(ADDR_PINS):
        p = Pin(pin, Pin.IN, Pin.PULL_UP)
        if p.value() == 0:
            addr |= (1 << i)
    return addr + 1

MY_ID = get_my_id()
IS_MASTER = (MY_ID == 1)

led = Pin(LED_PIN, Pin.OUT)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP) if IS_MASTER else None

can = CAN(0, tx=CAN_TX, rx=CAN_RX,
          mode=CAN.LOOPBACK if LOOPBACK else CAN.NORMAL,
          bitrate=500000, extframe=False)

# === ФИЛЬТРЫ: только мой ID (broadcast вручную) ===
def setup_filters():
    cmd_id = BASE_CMD_ID + MY_ID
    can.set_filters(
        bank=0,
        mode=CAN.FILTER_RAW_SINGLE,
        params=[cmd_id, 0x7FF]
    )
    print(f"Filter: 0x{cmd_id:03X}")

if not LOOPBACK:
    setup_filters()

print(f"Device ID: {MY_ID} | {'MASTER' if IS_MASTER else 'SLAVE'}")

# === ПРОТОКОЛ: короткие строки (≤8 байт) ===
def parse_command(data: bytes) -> tuple:
    try:
        s = data.decode('utf-8').strip()
        if ',' not in s: return None, None
        to_str, cmd = s.split(',', 1)
        if not to_str.startswith("TO:"): return None, None
        to_id = int(to_str[3:])
        return to_id, cmd
    except:
        return None, None

def send(to_id: int, cmd: str):
    msg = f"TO:{to_id},{cmd}"
    data = msg.encode('utf-8')
    if len(data) > 8:
        raise ValueError(f"Message too long: {msg}")
    can.send(list(data), BASE_CMD_ID + to_id)
    print(f"→ {msg}")

def send_ack(status: str):
    msg = f"FM:{MY_ID},{status}"
    data = msg.encode('utf-8')
    if len(data) > 8:
        raise ValueError(f"ACK too long: {msg}")
    can.send(list(data), BASE_ACK_ID + MY_ID)

# === ОСНОВНОЙ ЦИКЛ ===
last_button = None
print("CAN Bus running...")

while True:
    # --- Master: кнопка ---
    if IS_MASTER and button:
        current = button.value() == 0
        if current != last_button:
            target = 2
            cmd = "ON" if current else "OFF"
            send(target, cmd)
            time.sleep_ms(300)
        last_button = current

    # --- Приём ---
    if can.any():
        msg = can.recv()
        msg_id, _, _, data_bytes = msg
        data = bytes(data_bytes)

        # Команды (с фильтром + broadcast)
        if msg_id == BROADCAST_ID or (BASE_CMD_ID <= msg_id < BASE_CMD_ID + 256):
            if msg_id != BROADCAST_ID:
                expected_id = msg_id - BASE_CMD_ID
                if expected_id != MY_ID:
                    continue  # не мой ID
            to_id, cmd = parse_command(data)
            if to_id in (0, MY_ID):
                print(f"CMD: {data.decode('utf-8')}")
                if cmd == "ON":
                    led.value(1)
                    send_ack("OK")
                elif cmd == "OFF":
                    led.value(0)
                    send_ack("OK")
                else:
                    send_ack("ERR")

        # ACK (только Master)
        elif IS_MASTER and BASE_ACK_ID <= msg_id < BASE_ACK_ID + 256:
            print(f"ACK: {data.decode('utf-8')}")

    time.sleep_ms(10)