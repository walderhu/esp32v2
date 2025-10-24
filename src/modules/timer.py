from machine import Pin, Timer
import time

step_pin = Pin(14, Pin.OUT)
dir_pin = Pin(15, Pin.OUT)
en_pin = Pin(13, Pin.OUT)

steps_left = 0
step_state = 0
step_delay_us = 500
timer = Timer(0)

def enable(state=True, invert=True):
    if invert: state = not state
    en_pin.value(state)

def tick(t):
    global steps_left, step_state
    if steps_left <= 0:
        timer.deinit()
        enable(False)
        return
    step_state ^= 1
    step_pin.value(step_state)
    if step_state == 0: steps_left -= 1  

def move(steps, step_delay_us=500):
    global steps_left, step_state  
    direction = steps > 0; steps = abs(steps)  
    dir_pin.value(direction)
    steps_left = steps
    step_state = 0 
    enable(True)
    freq = 1_000_000 // step_delay_us  
    timer.init(freq=freq, mode=Timer.PERIODIC, callback=tick)  

move(200, step_delay_us=500)
time.sleep(3)