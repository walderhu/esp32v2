# from machine import Pin
# import esp32

# dir_pin = Pin(4, Pin.OUT)
# en_pin = Pin(2, Pin.OUT)
# step_pin_rmt = 16  

# steps_per_rev = 200      # шагов на оборот (full step)
# microstep = 16           # дробление
# steps_per_rev_micro = steps_per_rev * microstep  # 3200 шагов на оборот

# steps_per_mm = 80        # 80 шагов на 1 мм
# mm_to_move = 100          # сколько мм хотим пройти
# total_steps = steps_per_mm * mm_to_move  # например, 100 мм → 8000 шагов

# en_pin.off()     
# dir_pin.value(1) 

# # Настройка длительности импульсов
# # 50 µs HIGH + 50 µs LOW = 1 шаг = 100 µs
# # clock_div = 4 → тик = 50 нс
# ticks_per_50us = 1000  # 1000 тиков * 50 нс = 50 µs
# pulses = [ticks_per_50us, ticks_per_50us] * total_steps  # формируем массив импульсов
# rmt = esp32.RMT(0, pin=Pin(step_pin_rmt, Pin.OUT, drive=Pin.DRIVE_3), clock_div=4)
# rmt.write_pulses(pulses)
# rmt.wait_done()  

# # РАБОТАЕТ
# # import time
# # step_pin = Pin(step_pin_rmt, Pin.OUT, drive=Pin.DRIVE_3)
# # for _ in range(total_steps):
# #     step_pin.on(); time.sleep_us(50)
# #     step_pin.off(); time.sleep_us(50)

# en_pin.on()      







##########

from machine import Pin
import esp32
import time

# Пины
STEP_PIN = 16
DIR_PIN = 4

step = Pin(STEP_PIN, Pin.OUT)
dir_pin = Pin(DIR_PIN, Pin.OUT)

dir_pin.value(0)

# Настройка RMT для генерации импульсов на STEP
rmt = esp32.RMT(0, pin=step, clock_div=80)  # 1 тик = 1 мкс

def move_steps(num_steps, step_delay_us=300):
    """
    Сделать num_steps шагов.
    step_delay_us — задержка между шагами (минимум ~2–5 мкс для большинства драйверов).
    """
    if num_steps <= 0:
        return
    
    pulses = []
    for _ in range(num_steps):
        pulses.append(5) 
        pulses.append(step_delay_us - 5) 

    rmt.write_pulses(pulses, 1)
    # total_time_ms = (num_steps * step_delay_us) // 1000
    # time.sleep_ms(max(1, total_time_ms + 1))




en_pin = Pin(2, Pin.OUT)
en_pin.off()     

move_steps(5000)
time.sleep(5)
en_pin.on()     