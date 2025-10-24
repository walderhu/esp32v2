from machine import Pin
import time
import time

class Stepper:
    def __init__(self, step_pin, dir_pin, en_pin, sw_pin,
                 steps_per_rev=200, microstep=16, pulley_teeth=20, tooth_pitch=2,
                 invert_dir=False, invert_enable=False, limit_coord_cm=None, freq=12_000):
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
        self.enable(False)
        self.freq = freq

    def enable(self, state=True):
        """Включить или выключить драйвер"""
        self.enabled = state
        if self.en_pin:
            pin_state = (not state) if not self.invert_enable else state
            self.en_pin.value(pin_state)
        
    def home(self, direction=0, freq=None, debounce_ms=100):
        """Домой по концевику"""
        if freq is None: freq = self.freq
        delay_us = int(1e6 / (2 * freq))
        if not self.enabled: self.enable(True)
        self.dir_pin.value(direction ^ self.invert_dir)
        while self.sw_pin.value() == 0:
            self.step_pin.on(); time.sleep_us(delay_us)
            self.step_pin.off(); time.sleep_us(delay_us)
        time.sleep_ms(debounce_ms)
        self.current_coord = 0

    def move_accel(self, distance_mm=None, distance_cm=None, max_freq=None, min_freq=5000, accel_ratio=0.2, blocks=500):
        if distance_mm is None: distance_mm = distance_cm * 10
        if distance_mm == 0: return
        if max_freq is None: max_freq = self.freq
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

    @property
    def freq(self): return self._freq
    @freq.setter
    def freq(self, new_freq):
        if 0 <= new_freq <= 50_000: self._freq = new_freq
        else: raise ValueError('Неккоректное значение, дб 0 ≤ freq ≤ 50_000')
        
    def __sub__(self, coord): return self.__add__(-coord)
    
    def __add__(self, coord): 
        final_coord = self.current_coord + coord
        if 0 <= final_coord <= self.limit_coord_cm: self.move_accel(coord)
        else: raise ValueError('Выход за границы портала')
    
    def move_to(self, target_coord): 
        move_coord = target_coord - self.current_coord
        self += move_coord

    def __imatmul__(self, target_coord): return self.move_to(target_coord)

    def __enter__(self):
        self.enable(True)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type: raise exc_type(exc) from tb
        finally: self.enable(False)



class Portal:
    def __init__(self, motor_x: Stepper, motor_y: Stepper):
        self.x = motor_x
        self.y = motor_y
        self.home()

    def enable(self, state=True):
        self.x.enable(state)
        self.y.enable(state)
    

    def __enter__(self):
        self.x.enable(True)
        self.y.enable(True)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type: raise exc_type(exc) from tb
        finally:
            self.x.enable(False)
            self.y.enable(False)
            
    def home(self):
        self.x.home(freq=12_000)
        self.y.home(freq=18_000)
        return self


    def __sub__(self, coord: tuple[float, float]): return self.__add__(-coord)
    
    def __add__(self, coord: tuple[float, float]): 
        x_coord, y_coord = coord
        
        final_x = self.x.current_coord + x_coord
        final_y = self.y.current_coord + y_coord
        
        if (0 <= final_x <= self.x.limit_coord_cm) and \
           (0 <= final_y <= self.y.limit_coord_cm):
            self.x.move_accel(x_coord)
            self.y.move_accel(y_coord)
        else: raise ValueError('Выход за границы портала')
    
    def move_to(self, target_coord): 
        x_target_coord, y_target_coord = target_coord
        x_move_coord = x_target_coord - self.x.current_coord
        y_move_coord = y_target_coord - self.y.current_coord
        self += (x_move_coord, y_move_coord)

    def __imatmul__(self, target_coord): return self.move_to(target_coord)

    def move_both(self, x_dist, y_dist):
        import _thread, time
        _x_done = False
        def move_x():
            nonlocal _x_done
            self.x.move_accel(x_dist)
            _x_done = True

        _thread.start_new_thread(move_x, ())
        self.y.move_accel(y_dist)
        while not _x_done: time.sleep_ms(1)

    def __repr__(self):
        return f'Portal({self.x.current_coord:2f}, {self.y.current_coord:2f})'


def test():
    m1=Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60)
    m2 = Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90)
    with Portal(m1, m2) as p:
        p.x += 10
        p.y += 20
        p += (4, 2)
        p @= (30, 30)
        p @= (0, 0)
        

