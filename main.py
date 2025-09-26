"""
Пример для работы с шаговиком в синхронном режиме
"""
from machine import Pin
from tools import Stepper
import time


if __name__ == '__main__':
    with Stepper(en_pin = Pin(13, Pin.OUT, drive=Pin.DRIVE_3),
                 step_pin = Pin(14, Pin.OUT, drive=Pin.DRIVE_3),
                 dir_pin = Pin(15, Pin.OUT,  drive=Pin.DRIVE_3),
                 steps_per_rev=200, speed_sps=1000, 
                 invert_enable=True) as stepper:
        print('Start')
        stepper.free_run(1)
        time.sleep(5)

# stepper.target(3 * stepper.steps_per_rev)
# while not stepper.is_target_reached(): time.sleep(0.1)
# print("Готово, 3 оборота сделаны")

# purelogic ist-1706 
# import time
# from machine import Pin
# en_pin   = Pin(13, Pin.OUT, drive=Pin.DRIVE_3) 
# step_pin = Pin(14, Pin.OUT, drive=Pin.DRIVE_3)  
# dir_pin  = Pin(15, Pin.OUT,  drive=Pin.DRIVE_3)  

# steps_per_rev = 200
# n_steps = 10
# invert_enable = True

# print("Начало")
# en_pin.value(not invert_enable)
# dir_pin.value(1)
# for i in range(n_steps * steps_per_rev):
#     step_pin.value(1); time.sleep_us(5)
#     step_pin.value(0); time.sleep_ms(1)  
# en_pin.value(invert_enable)
# print("Готово")


