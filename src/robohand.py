# main.py — MicroPython для ESP32
from math import radians, sin, cos
from machine import Pin, PWM, Timer, UART
from time import sleep, ticks_ms, sleep_us
import network, time
import usocket as socket
import ujson

# === Пины ===
STEP_PINS = [15, 2, 4, 16]   # X, Y, Z, A
DIR_PINS  = [0, 4, 16, 2]     # Подключи по схеме CNC Shield
ENDSTOPS  = [34, 35, 32, 33]  # X, Y, Z, A (вход с подтяжкой)
SERVO_PIN = 13

# === Настройки ===
L1 = 225.0
L2 = 180.0
STEPS_PER_MM_Z = 800  # 8мм винт, 1/4 шаг
ANGLE_TO_STEPS = [44.44, 35.55, 8.88]  # θ1, θ2, φ
MAX_POS = 100
HOME_Z_UP = 170  # мм

# === Переменные ===
positions = []
current_pos = {'x': 365, 'y': 0, 'z': 170, 'g': 90}
target = {'t1': 90, 't2': 0, 'phi': 90, 'z': 170, 'g': 90}
homing_done = False

# === Инициализация ===
steppers = [Pin(p, Pin.OUT) for p in STEP_PINS]
dirs = [Pin(p, Pin.OUT) for p in DIR_PINS]
endstops = [Pin(p, Pin.IN, Pin.PULL_UP) for p in ENDSTOPS]
servo = PWM(Pin(SERVO_PIN), freq=50)

uart = UART(1, baudrate=115200, tx=17, rx=19)  # Для отладки (опционально)

# === Wi-Fi ===
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

# === Шаг ===
def step_motor(idx, steps, speed=500):
    dir_pin = dirs[idx]
    step_pin = steppers[idx]
    dir_pin.value(1 if steps > 0 else 0)
    steps = abs(steps)
    delay = 1000000 // speed
    for _ in range(steps):
        step_pin.value(1)
        sleep_us(10)
        step_pin.value(0)
        sleep_us(delay)

# === Хоминг ===
def homing():
    global homing_done
    print("Homing...")
    # Z вверх
    while endstops[2].value() == 1:
        step_motor(2, 100, 600)
    step_motor(2, -50, 300)  # отъезд
    # Остальные оси
    for i in range(4):
        if i == 2: continue
        while endstops[i].value() == 1:
            step_motor(i, -100 if i < 3 else 50, 400)
        step_motor(i, 20, 200)
    # Z на 170 мм
    step_motor(2, int(HOME_Z_UP * STEPS_PER_MM_Z), 600)
    homing_done = True
    print("Homing done!")

# === Кинематика ===
def forward_kinematics(t1, t2):
    t1r = radians(t1)
    t2r = radians(t2)
    x = L1 * cos(t1r) + L2 * cos(t1r + t2r)
    y = L1 * sin(t1r) + L2 * sin(t1r + t2r)
    return round(x), round(y)

def inverse_kinematics(x, y):
    from math import acos, atan2, degrees, sqrt
    c2 = (x*x + y*y - L1*L1 - L2*L2) / (2*L1*L2)
    if abs(c2) > 1: return None
    t2 = degrees(acos(c2))
    if x < 0 and y < 0: t2 = -t2
    t1 = degrees(atan2(y, x) - atan2(L2*sin(radians(t2)), L1 + L2*cos(radians(t2))))
    if x >= 0 and y >= 0: t1 = 90 - t1
    elif x < 0 and y > 0: t1 = 90 - t1
    elif x < 0 and y < 0: t1 = 270 - t1
    elif x > 0 and y < 0: t1 = -90 - t1
    phi = 90 + t1 + t2
    if abs(phi) > 165: phi = 180 + phi
    return round(t1), round(-t2), round(phi)

# === Движение ===
def move_to(t1, t2, phi, z, g):
    steps = [
        int(t1 * ANGLE_TO_STEPS[0]),
        int(t2 * ANGLE_TO_STEPS[1]),
        int(phi * ANGLE_TO_STEPS[2]),
        int(z * STEPS_PER_MM_Z)
    ]
    max_steps = max([abs(s) for s in steps])
    speed = 800
    for i in range(max_steps):
        for j in range(4):
            if abs(steps[j]) > i:
                dirs[j].value(1 if steps[j] > i else 0)
                steppers[j].value(1)
                sleep_us(5)
                steppers[j].value(0)
        sleep_us(1000000 // speed)
    servo.duty_ns(int(600 + g * 2000 / 180 * 1000))  # 600–2500 мкс

