from machine import Pin
import time

button = Pin(13, Pin.IN, Pin.PULL_UP)

while True:
    if not button.value(): print('Да', end='\r')
    else: print('Нет', end='\r')
    time.sleep_ms(50)
    print("\r\033[K", end="")
