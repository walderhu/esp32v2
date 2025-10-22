from machine import Pin, PWM
import time 

class StepperPWM:
    def __init__(self, step_pin, dir_pin, en_pin, sw_pin,
                 steps_per_rev=200, invert_dir=False, invert_enable=False, 
                 lead_mm=8, limit_coord=None, freq=0):
        self.step_pwm = PWM(Pin(step_pin))
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.en_pin = Pin(en_pin, Pin.OUT) if en_pin is not None else None
        self.sw_pin = Pin(sw_pin, Pin.IN, Pin.PULL_UP)

        self.steps_per_rev = steps_per_rev
        self.invert_dir = invert_dir
        self.invert_enable = invert_enable
        self.lead_mm = lead_mm
        self.limit_coord = limit_coord

        self.enabled = False
        self.running = False
        self.current_dir = 1
        self._freq = freq

        self.step_pwm.duty_u16(0)
        self.enable(False)
        self.current_coord = None
        

    def enable(self, state=True):
        """Включить или выключить драйвер"""
        self.enabled = state
        if self.en_pin:
            pin_state = (not state) if not self.invert_enable else state
            self.en_pin.value(pin_state)
        if not state: self.stop()

    def stop(self):
        """Остановить вращение (убрать импульсы)"""
        try: self.step_pwm.duty_u16(0)
        except RuntimeError: pass
        self.running = False
        
    def is_running(self): return self.running
    def is_enabled(self): return self.enabled

    @property
    def freq(self): return self._freq

    @freq.setter
    def freq(self, new_freq):
        if 1 <= new_freq <= 40_000: self._freq = new_freq
        else: raise ValueError('frequency must be from 1Hz to 40MHz')
        
    def __enter__(self):
        self.enable(True)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type: raise exc_type(exc) from tb
        finally: self.enable(False)

    def __del__(self):
        try: self.enable(False)
        except Exception: pass

    def home(self, freq=None, debounce_ms=150):
        """Возврат к концевику (нулевая позиция)"""
        if not self.enabled: self.enable(True)
        if self.sw_pin.value() == 1:
            self.current_coord = 0; return
        if freq is None: freq = self.freq
        
        self.dir_pin.value(0 ^ self.invert_dir)
        self.step_pwm.freq(int(freq))
        self.step_pwm.duty_u16(32768)
        self.running = True
        self.current_dir = 0
        try:
            while True:
                if self.sw_pin.value() == 1: 
                    self.step_pwm.duty_u16(0)
                    time.sleep_ms(debounce_ms)
                    break
                time.sleep_ms(2)
        finally:
            self.step_pwm.duty_u16(0)
            self.running = False
            time.sleep(0.5)
            self.current_coord = 0


    def run(self, direction=1, freq=1000, duration=None):
        if not self.enabled: self.enable(True)
        self.current_dir = direction
        self.dir_pin.value(self.current_dir ^ self.invert_dir)
        self.step_pwm.freq(int(freq))
        self.step_pwm.duty_u16(32768)  
        self.running = True
        self.freq = freq

        start_time = time.ticks_ms()
        stop_time = None
        if duration is not None:
            stop_time = time.ticks_add(start_time, int(duration * 1000))
        last_step_time = time.ticks_ms()

        try:
            while self.running:
                now = time.ticks_ms()
                delta_ms = time.ticks_diff(now, last_step_time)
                delta_s = delta_ms / 1000
                delta_mm = delta_s * freq * self.lead_mm / self.steps_per_rev
                delta_cm = delta_mm / 10
                self.current_coord += delta_cm if direction == 1 else -delta_cm
                last_step_time = now

                if self.sw_pin.value() == 1 and direction == 0:
                    self.current_coord = 0
                    self.stop(); break # начало из концевика и движение на концевик
                if stop_time and time.ticks_diff(now, stop_time) >= 0:
                    self.stop(); break # ограничение по времени
                if self.current_coord >= self.limit_coord:
                    self.stop(); break # ограничение по координате
                time.sleep_ms(5)
        finally:
            self.stop()
            

    def move_to(self, target_mm=None, target_cm=None, freq=None):
        """Асинхронное перемещение на мм"""
        if target_mm == None:
            if target_cm == None: raise RuntimeError('Не передано сколько передвигаться')
            else: target_mm = target_cm * 10
            
        if freq is None: freq = self.freq
        if self.current_coord is None: self.home(freq=12_000)
        distance_mm = target_mm - self.current_coord * 10
        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        self.run(direction=direction, freq=freq, duration=duration)
        

    def move_accel(self, distance_mm=None, max_freq=20_000, 
                         min_freq=5_000, accel_ratio=0.2, distance_cm=None):
        """Перемещение с плавным ускорением/торможением (через PWM), с учётом координатных ограничений"""
        if distance_mm is None and distance_cm is None:
            raise ValueError("Укажите distance_mm или distance_cm")
        if distance_mm is None:
            distance_mm = distance_cm * 10

        if self.current_coord is None:
            self.home(freq=12_000)

        direction = 1 if distance_mm > 0 else 0
        self.dir_pin.value(direction ^ self.invert_dir)
        self.enable(True)
        self.current_dir = direction

        steps_total = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        accel_steps = max(1, int(steps_total * accel_ratio))
        decel_start = steps_total - accel_steps
        dt = 0.005  
        self.running = True
        self.step_pwm.duty_u16(32768)
        steps_done = 0
        last_time = time.ticks_ms()
        try:
            while steps_done < steps_total and self.running:
                if steps_done < accel_steps:
                    ratio = steps_done / accel_steps
                    freq = min_freq + (max_freq - min_freq) * ratio
                elif steps_done > decel_start:
                    ratio = (steps_total - steps_done) / accel_steps
                    freq = min_freq + (max_freq - min_freq) * max(0, ratio)
                else:
                    freq = max_freq

                freq = max(min_freq, min(freq, max_freq))
                self.step_pwm.freq(int(freq))
                self.freq = freq

                now = time.ticks_ms()
                dt_real = time.ticks_diff(now, last_time) / 1000
                last_time = now
                delta_mm = dt_real * freq * self.lead_mm / self.steps_per_rev
                delta_cm = delta_mm / 10

                if direction == 1:
                    self.current_coord += delta_cm
                    if self.limit_coord is not None and self.current_coord >= self.limit_coord:
                        self.stop(); break
                else:
                    self.current_coord -= delta_cm
                    if self.sw_pin.value() == 1:
                        self.current_coord = 0
                        self.stop(); break

                steps_done += freq * dt_real
                time.sleep(dt)
        finally:
            self.stop()
            self.running = False
            time.sleep(0.1)
    
    def __add__(self, coord): return self.move_accel(distance_cm=coord)
    def __sub__(self, coord): return self.move_accel(distance_cm=-coord)
    def __imatmul__(self, coord): return self.move_to(coord)


def test():
    lead = 2.475 * (20.4 / 20)
    m1=StepperPWM(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, lead_mm=lead, limit_coord=60)
    m2=StepperPWM(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, lead_mm=lead, limit_coord=90)
    with m1, m2:
        m1.home(freq=12_000)        
        m2.home(freq=12_000)        

        time.sleep(5)
        m1.move_to(target_cm=20, freq=10_000)
        time.sleep(0.5)
        m2.move_to(target_cm=20, freq=10_000)
        
        # m1 -= 30
        # m2 -= 20
        
        # portal @= (10, 10)
        # time.sleep(0.5)
        # portal.x += 5
        # portal.y += 5
