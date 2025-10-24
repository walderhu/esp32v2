from machine import Pin
import time
import sys

    
class Stepper:
    def __init__(self, step_pin, dir_pin, en_pin, sw_pin,
                 steps_per_rev=200, microstep=16, pulley_teeth=20, tooth_pitch=2,
                 invert_enable=False, limit_coord_cm=None, freq=12_000):
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
        self.invert_enable = invert_enable
        self.limit_coord_cm = limit_coord_cm

        self.enabled = False
        self.current_coord = None
        self.enable(False)
        self.freq = freq

    def enable(self, state=True):
        """Включить или выключить драйвер"""
        self.enabled = state
        if self.en_pin:
            pin_state = (not state) if not self.invert_enable else state
            self.en_pin.value(pin_state)
        
    def home(self, freq=None, *, direction=0, debounce_ms=100):
        """Домой по концевику"""
        if freq is None: freq = self.freq
        delay_us = int(1e6 / (2 * freq))
        if not self.enabled: self.enable(True)
        self.dir_pin.value(direction)
        while self.sw_pin.value() == 0:
            self.step_pin.on(); time.sleep_us(delay_us)
            self.step_pin.off(); time.sleep_us(delay_us)
        time.sleep_ms(debounce_ms)
        self.current_coord = 0


    def move_accel(self, distance_cm, max_freq=None, min_freq=5000, accel_ratio=0.15, accel_grain=10):
        if max_freq is None: max_freq = self.freq
        direction = distance_cm > 0; self.dir_pin.value(direction)
        if not (0 <= (self.current_coord + distance_cm) <= self.limit_coord_cm):
            raise ValueError('Выход за границы портала')
        steps_total = int(abs(distance_cm) * self.steps_per_mm * 10)
        accel_steps = max(1, int(steps_total * accel_ratio))
        decel_steps = accel_steps
        cruise_steps = steps_total - accel_steps - decel_steps
        from array import array
        delay_us_list = array('H')
        for step in range(0, accel_steps, accel_grain):
            ratio = step / accel_steps
            freq = min_freq + (max_freq - min_freq) * ratio
            delay_us = int(1_000_000 / freq / 2)
            repeats = min(accel_grain, accel_steps - step)
            delay_us_list.extend([delay_us] * repeats)
        min_delay_us = int(1_000_000 / max_freq / 2)
        for delay_us in delay_us_list:
            self.step_pin.on(); time.sleep_us(delay_us)
            self.step_pin.off(); time.sleep_us(delay_us)
        for _ in range(cruise_steps):
            self.step_pin.on(); time.sleep_us(min_delay_us)
            self.step_pin.off(); time.sleep_us(min_delay_us)
        for delay_us in reversed(delay_us_list):
            self.step_pin.on(); time.sleep_us(delay_us)
            self.step_pin.off(); time.sleep_us(delay_us)
        self.current_coord = (self.current_coord or 0) + distance_cm



    @property
    def freq(self): return self._freq
    @freq.setter
    def freq(self, new_freq):
        if 0 <= new_freq <= 50_000: self._freq = new_freq
        else: raise ValueError('Неккоректное значение, дб 0 ≤ freq ≤ 50_000')
        
    def __sub__(self, coord): return self.__add__(-coord)
    
    def __add__(self, coord): 
        self.move_accel(distance_cm=coord)
        return self
    
    def move_to(self, target_coord): 
        move_coord = target_coord - self.current_coord
        self += move_coord

    def __imatmul__(self, target_coord): return self.move_to(target_coord)

    def __enter__(self):
        self.enable(True)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                print("Exception caught in __exit__:")
                sys.print_exception(exc, sys.stdout)
        finally:
            self.enable(False); return False

    def __repr__(self):
        return self.current_coord







class Portal:
    def __init__(self, motor_x: Stepper, motor_y: Stepper):
        self.x = motor_x; self.y = motor_y
        self.home()
        
    def home(self, freq=10_000):
        self.x.home(freq=20_000) 
        self.y.home(freq=freq)

    def enable(self, state=True):
        self.x.enable(state); self.y.enable(state)
    
    def __enter__(self):
        self.enable(True); return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                print("Exception caught in __exit__:")
                sys.print_exception(exc, sys.stdout)
        finally:
            self.enable(False); return False
            

def test():
    m2=Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90)
    m1=Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60)
    
    with Portal(m2, m1) as p:
        p.x.freq = 30_000; p.y.freq = 30_000
        
        p.x.move_accel(30)
        p.y.move_accel(30)
        
        p.x.move_accel(-30)
        p.y.move_accel(-30)
        
        