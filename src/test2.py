from machine import Pin
import time
import time

class StepperManual:
    def __init__(self, step_pin, dir_pin, en_pin, sw_pin,
                 steps_per_rev=200, microstep=16, pulley_teeth=20, tooth_pitch=2,
                 invert_dir=False, invert_enable=False, limit_coord_cm=None):
        self.step_pin = Pin(step_pin, Pin.OUT)
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.en_pin = Pin(en_pin, Pin.OUT) if en_pin is not None else None
        self.sw_pin = Pin(sw_pin, Pin.IN, Pin.PULL_UP)
        self.steps_per_rev = steps_per_rev
        self.microstep = microstep
        self.steps_per_rev_total = steps_per_rev * microstep

        self.pulley_teeth = pulley_teeth
        self.tooth_pitch = tooth_pitch
        self.mm_per_rev = pulley_teeth * tooth_pitch  
        self.steps_per_mm = self.steps_per_rev_total / self.mm_per_rev
        self.invert_dir = invert_dir
        self.invert_enable = invert_enable
        self.limit_coord_cm = limit_coord_cm

        self.enabled = False
        self.current_coord = None
        self.enable(True)

    def enable(self, state=True):
        """Включить или выключить драйвер"""
        self.enabled = state
        if self.en_pin:
            pin_state = (not state) if not self.invert_enable else state
            self.en_pin.value(pin_state)
        
    def home(self, direction=0, freq=500, debounce_ms=100):
        """Домой по концевику"""
        delay_us = int(1e6 / (2 * freq))
        if not self.enabled: self.enable(True)
        self.dir_pin.value(direction ^ self.invert_dir)
        while self.sw_pin.value() == 0:
            self.step_pin.on(); time.sleep_us(delay_us)
            self.step_pin.off(); time.sleep_us(delay_us)
        time.sleep_ms(debounce_ms)
        self.current_coord = 0

    def move_accel(self, distance_mm=None, distance_cm=None, max_freq=20000, min_freq=5000, accel_ratio=0.2, blocks=500):
        if distance_mm is None: distance_mm = distance_cm * 10
        if distance_mm == 0: return
        direction = 1 if distance_mm > 0 else 0
        self.dir_pin.value(direction ^ self.invert_dir)
        self.enable(True)
        steps_total = int(abs(distance_mm) * self.steps_per_mm)
        accel_steps = max(1, int(steps_total * accel_ratio))
        decel_start = steps_total - accel_steps

        steps_per_block = max(1, steps_total // blocks)
        step_done = 0
        while step_done < steps_total:
            mid_step = step_done + steps_per_block // 2
            if mid_step < accel_steps:
                ratio = mid_step / accel_steps
                freq = min_freq + (max_freq - min_freq) * ratio
            elif mid_step >= decel_start:
                ratio = (steps_total - mid_step) / accel_steps
                freq = min_freq + (max_freq - min_freq) * max(0, ratio)
            else:
                freq = max_freq
            delay_us = int(1_000_000 / freq / 2)
            block_steps = min(steps_per_block, steps_total - step_done)
            for _ in range(block_steps):
                self.step_pin.on(); time.sleep_us(delay_us)
                self.step_pin.off(); time.sleep_us(delay_us)
            step_done += block_steps
        self.current_coord = (self.current_coord or 0) + (1 / self.steps_per_mm) * (1 if direction else -1) * steps_total





def test():
    m1=StepperManual(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60)
    m2 = StepperManual(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90)
    m1.home(freq=12_000)
    m2.home(freq=18_000)

    m1.move_accel(distance_cm=60, accel_ratio=0.15, max_freq=40_000)  
    m2.move_accel(distance_cm=60, accel_ratio=0.15, max_freq=40_000)  
    print(m1.current_coord)
    print(m2.current_coord)

