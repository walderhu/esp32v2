from machine import Pin, PWM
from time import sleep

servo = PWM(Pin(13), freq=50)  

def set_angle(angle, min_duty=40, max_duty=115):
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty(duty)
    print(f"angle={angle}, duty={duty}")

while True:
    for angle in range(180, -1, -10):
        set_angle(angle); sleep(0.2)
    for angle in range(0, 181, 10):
        set_angle(angle); sleep(0.2)
