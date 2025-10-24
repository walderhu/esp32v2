from machine import Pin
import esp32, time, gc


class Stepper:
    count = 0

    def __new__(cls, *args, **kwargs):
        if cls.count > 7: raise RuntimeError('Нельзя создать больше 8 объектов')
        obj = object.__new__(cls)   
        obj.id = cls.count
        cls.count += 1
        return obj
        
    def __init__(self, dir_pin, en_pin, step_pin, invert_en=False, clock_div=80):
        self.invert_en = invert_en
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.rmt = esp32.RMT(self.id, pin=Pin(step_pin, Pin.OUT), clock_div=clock_div)  
        self.en_pin = Pin(en_pin, Pin.OUT)

    def enable(self, state=True):
        if self.invert_en: state = not state
        self.en_pin.value(state)

    def __enter__(self):
        self.enable(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.enable(False)
        return False

    def move(self, steps, step_delay_us=500):
        direction = steps > 0; steps = abs(steps)
        self.dir_pin.value(direction)
        tick_us = self.rmt.clock_div() / 80
        step_ticks = min(32767, (max(0, int(step_delay_us / (tick_us)))))
        pulse = (step_ticks, step_ticks) # HIGH and LOW for 1 step
        for _ in range(steps):
            self.rmt.write_pulses(pulse)
            while not self.rmt.wait_done(): pass


def main():
    stepper = Stepper(dir_pin=15, en_pin=13, step_pin=14, invert_en=True, clock_div=80)
    with stepper:
        stepper.move(200, step_delay_us=500) # 635
        time.sleep(1)
        stepper.move(-200, step_delay_us=500)
        time.sleep(1)
        
main()