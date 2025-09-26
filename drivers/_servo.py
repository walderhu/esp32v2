import machine
from machine import Pin
import time

servo_pin = Pin(4) # пин D4, к которому подключена сервомашин
pwm = machine.PWM(servo_pin, freq=50)  # Частота 50 Гц для сервомашин

# Установите ширину импульса для управления сервомашиной
# Обычно диапазон от 0.5 мс до 2.5 мс
def set_servo_angle(angle):
    if not 0 <= angle <= 180:
        raise ValueError("Угол должен быть от 0 до 180 градусов")
    
    # Преобразование угла в ширину импульса. Обычно 0.5 мс соответствует 0 градусам, а 2.5 мс — 180 градусам
    pulse_width = int((angle / 180) * (2.5 - 0.5) + 0.5) * 1000  # в микросекундах
    pwm.duty(pulse_width)

# Пример использования
while True:
    set_servo_angle(0)  # Установите сервомашину в положение 0 градусов
    time.sleep(1)
    set_servo_angle(180)  # Установите сервомашину в положение 180 градусов
    time.sleep(1)
