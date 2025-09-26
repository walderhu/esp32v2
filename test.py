import time
from machine import Pin

en_pin   = Pin(13, Pin.OUT, drive=Pin.DRIVE_3) 
step_pin = Pin(14, Pin.OUT, drive=Pin.DRIVE_3)  
dir_pin  = Pin(15, Pin.OUT,  drive=Pin.DRIVE_3)  

steps_per_rev = 200
total_steps = 100 * steps_per_rev  
invert_enable = True

en_pin.value(not invert_enable)
dir_pin.value(1)

print("Начало")
for i in range(total_steps):
    step_pin.value(1); time.sleep_us(5)
    step_pin.value(0); time.sleep_ms(1)  

en_pin.value(invert_enable)
print("Готово")

# purelogic ist-1706 
