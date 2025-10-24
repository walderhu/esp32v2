from machine import Pin
import esp32, time, gc



dir_pin_y = Pin(15, Pin.OUT)

def move_steps(rmt, num_steps, step_delay_us=700, delay = 50, dir = 1):
    dir_pin_y.value(dir)
    # rmt.write_pulses((20, 20), 1)
    
    pulses = []
    for _ in range(num_steps):
        pulses.append(500) 
        pulses.append(500) 
        if len(pulses) > 60:
            rmt.write_pulses(pulses, 0)
            del pulses
            pulses = []
    else: rmt.write_pulses(pulses, 0)
    del pulses
    # gc.collect()

rmt_y = esp32.RMT(1, pin=Pin(14, Pin.OUT), clock_div=80, tx_carrier=(1100, 50, 0))  

en_pin_y = Pin(13, Pin.OUT)
en_pin_y.on()     

move_steps(rmt_y, 1_000, step_delay_us=800, dir=1)
# time.sleep(2)
# while rmt_y.wait_done(): pass

en_pin_y.on()     