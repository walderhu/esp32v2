from machine import Pin
import time
import sys, math

    
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


    def _move_accel(self, distance_cm, max_freq=None, min_freq=5000, accel_ratio=0.15, accel_grain=10):
        if max_freq is None: max_freq = self.freq
        direction = distance_cm > 0; self.dir_pin.value(direction)
        if not (0 <= (self.current_coord + distance_cm ) <= self.limit_coord_cm):
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
        self._move_accel(distance_cm=coord)
        return self
    
    def move_to(self, target_coord): 
        move_coord = target_coord - self.current_coord
        self += move_coord

    def __imatmul__(self, target_coord): 
        if not (0 <= target_coord <= self.limit_coord_cm):
            raise ValueError('Выход за границы портала')
        if target_coord == 0: self.home()
        self.move_to(target_coord)
        return self

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
    def __init__(self, motor_x: Stepper, motor_y: Stepper, freq=30_000):
        self._x = motor_x; self._y = motor_y
        self.home(freq_base=12_000)
        self.freq = freq
        
    def enable(self, state=True):
        self._x.enable(state); self._y.enable(state)
    
    def __enter__(self):
        self.enable(True); return self

    @property
    def freq(self):
        return (self._x.freq, self._y.freq)

    @freq.setter
    def freq(self, new_freq):
        self._x.freq = new_freq
        self._y.freq = new_freq
   
    @property
    def x(self): return self._x.current_coord
    @x.setter
    def x(self, coord): self._x @= coord

    @property
    def y(self): return self._y.current_coord
    @y.setter
    def y(self, coord): self._y @= coord

    @property
    def coord(self): return (self.x, self.y)
    
    @coord.setter
    def coord(self, new_coord): 
        self |= new_coord

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                print("Exception caught in __exit__:")
                sys.print_exception(exc, sys.stdout)
        finally:
            self.enable(False); return False
            
    def __ior__(self, coords):
            """
            Параллельное движение по двум осям: p |= (x_target, y_target)
            """
            target_dx_cm, target_dy_cm = coords
            dx_cm = target_dx_cm -  self._x.current_coord
            dy_cm = target_dy_cm -  self._y.current_coord
            self.parallel_accel_move(dx_cm=dx_cm, dy_cm=dy_cm, accel_grain=20)
            return self
        

    def home(self, *, freq_base=None, speed_ratio=1.5, direction=0, debounce_ms=100):
        if freq_base is None: freq_base = min(self._x.freq, self._y.freq)
        freq_x = int(freq_base * speed_ratio)
        freq_y = int(freq_base)
        delay_x_us = int(1_000_000 / (2 * freq_x))
        delay_y_us = int(1_000_000 / (2 * freq_y))
        delay_min = delay_x_us if delay_x_us < delay_y_us else delay_y_us
        if not (self._x.enabled and self._y.enabled): self.enable(True)
        self._x.dir_pin.value(direction); self._y.dir_pin.value(direction)

        sx_on, sx_off = self._x.step_pin.on, self._x.step_pin.off
        sy_on, sy_off = self._y.step_pin.on, self._y.step_pin.off
        swx_val, swy_val = self._x.sw_pin.value, self._y.sw_pin.value
        x_done = False; y_done = False
        SCALE = 10_000
        step_ratio_x = int(speed_ratio * SCALE / (1 + speed_ratio))
        step_ratio_y = int(SCALE / (1 + speed_ratio))
        acc_x = 0; acc_y = 0
        t_next = time.ticks_us()

        while not (x_done and y_done):
            now = time.ticks_us()
            if time.ticks_diff(now, t_next) >= 0:
                acc_x += step_ratio_x
                acc_y += step_ratio_y

                if not x_done and acc_x >= SCALE:
                    acc_x -= SCALE
                    if swx_val() == 0:
                        sx_on(); sx_off()
                    else:
                        x_done = True

                if not y_done and acc_y >= SCALE:
                    acc_y -= SCALE
                    if swy_val() == 0:
                        sy_on(); sy_off()
                    else:
                        y_done = True

                t_next = time.ticks_add(now, delay_min)

        time.sleep_ms(debounce_ms)
        self._x.current_coord = 0
        self._y.current_coord = 0



    def _build_runlist(self, steps_total, max_freq, min_freq, accel_ratio, accel_grain):
        """Формирует компактный список (delay_us, count) для accel/cruise/decel."""
        accel_steps = max(1, int(steps_total * accel_ratio))
        decel_steps = accel_steps
        cruise_steps = steps_total - accel_steps - decel_steps
        if cruise_steps < 0:
            cruise_steps = 0

        min_delay_us = int(1_000_000 / max_freq / 2)
        runs = []
        s = 0
        while s < accel_steps:
            repeats = min(accel_grain, accel_steps - s)
            ratio = s / accel_steps
            freq = min_freq + int((max_freq - min_freq) * ratio)
            delay_us = int(1_000_000 / freq / 2)
            runs.append((delay_us, repeats))
            s += repeats

        if cruise_steps > 0:
            runs.append((min_delay_us, cruise_steps))

        # зеркалим разгон для торможения
        accel_part = []
        remaining = accel_steps
        idx = 0
        while remaining > 0 and idx < len(runs):
            d, c = runs[idx]
            take = min(c, remaining)
            accel_part.append((d, take))
            remaining -= take
            idx += 1
        for d, c in reversed(accel_part):
            runs.append((d, c))

        # корректировка общего числа шагов
        total_runs_steps = sum(c for _, c in runs)
        if total_runs_steps < steps_total:
            runs.append((min_delay_us, steps_total - total_runs_steps))
        elif total_runs_steps > steps_total:
            extra = total_runs_steps - steps_total
            d, c = runs[-1]
            runs[-1] = (d, c - extra)
            if runs[-1][1] == 0:
                runs.pop()

        return runs


    def _execute_parallel_runs(self, runs, steps_x, steps_y, steps_total):
        """Исполняет синхронное движение по X/Y по runlist."""
        acc_x = 0; acc_y = 0
        sx_pin = self._x.step_pin
        sy_pin = self._y.step_pin
        for delay_us, count in runs:
            for _ in range(count):
                acc_x += steps_x; acc_y += steps_y
                step_x = acc_x >= steps_total
                step_y = acc_y >= steps_total
                if step_x: acc_x -= steps_total
                if step_y: acc_y -= steps_total

                if step_x: sx_pin.on()
                if step_y: sy_pin.on()
                time.sleep_us(delay_us)
                if step_x: sx_pin.off()
                if step_y: sy_pin.off()
                time.sleep_us(delay_us)


    def parallel_accel_move(self, dx_cm, dy_cm, max_freq=50_000, min_freq=5000,
                             accel_ratio=0.15, accel_grain=10):
        """Параллельное синхронное движение X/Y с accel/cruise/decel."""
        if max_freq is None: max_freq = min(self._x.freq, self._y.freq)
        target_x = self._x.current_coord + dx_cm
        target_y = self._y.current_coord + dy_cm
        if not (0 <= target_x <= self._x.limit_coord_cm): raise ValueError("Выход за границы X")
        if not (0 <= target_y <= self._y.limit_coord_cm): raise ValueError("Выход за границы Y")

        if target_x == 0:
            self._x.home(freq=16_000)
            return self
        if target_y == 0:
            self._y.home(freq=16_000)
            return self

        dir_x = dx_cm > 0; self._x.dir_pin.value(dir_x)
        dir_y = dy_cm > 0; self._y.dir_pin.value(dir_y)

        steps_x = int(abs(dx_cm) * self._x.steps_per_mm * 10)
        steps_y = int(abs(dy_cm) * self._y.steps_per_mm * 10)
        steps_total = max(steps_x, steps_y)
        if steps_total == 0: return self

        runs = self._build_runlist(steps_total, max_freq, min_freq, accel_ratio, accel_grain)
        self._execute_parallel_runs(runs, steps_x, steps_y, steps_total)
        self._x.current_coord += dx_cm
        self._y.current_coord += dy_cm
        return self




def test():
    m2=Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90)
    m1=Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60)
    
    with Portal(m2, m1, freq=20_000) as p:
        print("X coord:", p.x, "Y coord:", p.y)
        p.coord = (45, 30)
        p.x = 20
        p.y = 10
        p.y += 20

        p.x = 0
        p.y = 0
