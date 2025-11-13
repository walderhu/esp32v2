# can_master_slave.py
from machine import Pin
import CAN
import time

# === КОНФИГУРАЦИЯ ===
CAN_TX_PIN = 5
CAN_RX_PIN = 4
LED_PIN = 2
BUTTON_PIN = 0

# CAN IDs
CMD_ID = 0x100      # Master → Slave
ACK_ID = 0x101      # Slave → Master (опционально)

# Режим: LOOPBACK для теста на одной плате, иначе NORMAL
LOOPBACK_MODE = False  # Поменяй на True, если тестируешь на одной плате

# === Инициализация ===
led = Pin(LED_PIN, Pin.OUT)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# Инициализация CAN
can = CAN(
    0,
    tx=CAN_TX_PIN,
    rx=CAN_RX_PIN,
    mode=CAN.LOOPBACK if LOOPBACK_MODE else CAN.NORMAL,
    bitrate=500000,
    extframe=False
)

print("CAN initialized. Mode:", "LOOPBACK" if LOOPBACK_MODE else "NORMAL")

# === Вспомогательные функции ===
def button_pressed():
    return button.value() == 0

def send_command(cmd: str):
    data = cmd.encode('utf-8')
    can.send(list(data), CMD_ID)
    print(f"Sent: {cmd} (ID: 0x{CMD_ID:03X})")

def send_ack(status: str):
    data = status.encode('utf-8')
    can.send(list(data), ACK_ID)
    print(f"Ack: {status} (ID: 0x{ACK_ID:03X})")

# === Основной цикл ===
last_state = None
print("Starting CAN Master/Slave...")

while True:
    current_state = button_pressed()

    # === Master: отправка по нажатию кнопки ===
    if current_state != last_state:
        if current_state:
            send_command("ON")
        else:
            send_command("OFF")
        time.sleep_ms(300)  # Дебаунс
    last_state = current_state

    # === Slave: приём команд ===
    if can.any():
        msg = can.recv()
        msg_id, ext, rtr, data = msg
        if msg_id == CMD_ID and not rtr:
            try:
                cmd = bytes(data).decode('utf-8').strip()
                print(f"Received command: {cmd}")
                if cmd == "ON":
                    led.value(1)
                    send_ack("OK: LED ON")
                elif cmd == "OFF":
                    led.value(0)
                    send_ack("OK: LED OFF")
                else:
                    send_ack("ERROR")
            except:
                send_ack("ERROR")

    # === Опционально: приём подтверждений (Master) ===
    # (можно раскомментировать, если нужно)
    if can.any():
        msg = can.recv()
        if msg[0] == ACK_ID:
            print("Ack:", bytes(msg[3]).decode('utf-8'))

    time.sleep_ms(10)