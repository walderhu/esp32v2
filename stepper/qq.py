import math
import machine

class Stepper:
    def __init__(self, step_pin=14, dir_pin=15, en_pin=13, steps_per_rev=200,
                 speed_sps=10, invert_dir=False, invert_enable=False, timer_id=-1):

        if not isinstance(step_pin, machine.Pin):
            step_pin = machine.Pin(step_pin, machine.Pin.OUT, drive=machine.Pin.DRIVE_3)
        if not isinstance(dir_pin, machine.Pin):
            dir_pin = machine.Pin(dir_pin, machine.Pin.OUT, drive=machine.Pin.DRIVE_3)
        if (en_pin is not None) and (not isinstance(en_pin, machine.Pin)):
            en_pin = machine.Pin(en_pin, machine.Pin.OUT, drive=machine.Pin.DRIVE_3)

        self.step_value_func = step_pin.value
        self.dir_value_func = dir_pin.value
        self.en_pin = en_pin
        self.invert_dir = invert_dir
        self.invert_enable = invert_enable

        self.timer = machine.Timer(timer_id)
        self.timer_is_running = False
        self.free_run_mode = 0
        self.enabled = True

        self.target_pos = 0
        self.pos = 0
        self.target_reached = True
        self.steps_per_sec = speed_sps
        self.steps_per_rev = steps_per_rev

        self.track_target()

    def speed(self, sps):
        self.steps_per_sec = sps
        if self.timer_is_running:
            self.track_target()

    def speed_rps(self, rps):
        self.speed(rps * self.steps_per_rev)

    def target(self, t):
        self.target_reached = False
        self.target_pos = t

    def target_deg(self, deg):
        self.target(round(self.steps_per_rev * deg / 360.0))

    def target_rad(self, rad):
        self.target(round(self.steps_per_rev * rad / (2.0 * math.pi)))

    def get_pos(self): return self.pos
    def get_pos_deg(self): return self.get_pos() * 360.0 / self.steps_per_rev
    def get_pos_rad(self): return self.get_pos() * (2.0 * math.pi) / self.steps_per_rev

    def overwrite_pos(self, p): self.pos = p

    def overwrite_pos_deg(self, deg):
        self.overwrite_pos(deg * self.steps_per_rev / 360.0)

    def overwrite_pos_rad(self, rad):
        self.overwrite_pos(rad * self.steps_per_rev / (2.0 * math.pi))

    def step(self, d):
        if d == 0: return
        if self.enabled:
            self.dir_value_func(int(d > 0) ^ self.invert_dir)
            self.step_value_func(1)
            self.step_value_func(0)
        self.pos += 1 if (d > 0) else -1

    def _timer_callback(self, t):
        if self.free_run_mode > 0: self.step(1)
        elif self.free_run_mode < 0: self.step(-1)
        elif self.target_pos > self.pos: self.step(1)
        elif self.target_pos < self.pos: self.step(-1)
        else: self.target_reached = True

    def free_run(self, d):
        self.free_run_mode = d
        if self.timer_is_running: self.timer.deinit()
        if d != 0:
            self.timer.init(freq=self.steps_per_sec, callback=self._timer_callback)
            self.timer_is_running = True
        else:
            self.dir_value_func(0)

    def track_target(self):
        self.free_run_mode = 0
        if self.timer_is_running: self.timer.deinit()
        self.timer.init(freq=self.steps_per_sec, callback=self._timer_callback)
        self.timer_is_running = True

    def stop(self):
        self.free_run_mode = 0
        if self.timer_is_running: self.timer.deinit()
        self.timer_is_running = False
        self.dir_value_func(0)

    def enable(self, e):
        self.enabled = e
        if self.en_pin:
            pin_state = bool(e) ^ self.invert_enable
            self.en_pin.value(pin_state)
        if not e: self.dir_value_func(0)

    def is_enabled(self): return self.enabled
    def is_target_reached(self): return self.target_reached

    def __enter__(self):
        self.enable(not self.invert_enable)
        return self

    def __exit__(self, exc_type, exc, tb):
        try: 
            if exc_type: raise self.StepperEngineError(exc_type)
        finally:
            self.enable(self.invert_enable); self.stop()

    class StepperEngineError(Exception):
        def __init__(self, message): super().__init__(message)
        
        
        



        
import time
motor = Stepper(step_pin=14, dir_pin=15, en_pin=13,
                steps_per_rev=200, speed_sps=200)


motor.enable(False)
print("Тест 1: свободный прогон вперёд")
motor.free_run(1)   
time.sleep(2)
motor.stop()

print("Тест 2: свободный прогон назад")
motor.free_run(-1)  
time.sleep(2)
motor.stop()

print("Тест 3: поворот на 1 оборот (200 шагов)")
motor.target(motor.get_pos() + motor.steps_per_rev)  
while not motor.is_target_reached(): time.sleep(0.01)
print("Готово, позиция:", motor.get_pos())

print("Тест 4: поворот на 90°")
motor.target_deg(motor.get_pos_deg() + 90)
while not motor.is_target_reached(): time.sleep(0.01)
print("Готово, позиция:", motor.get_pos_deg(), "градусов")

print("Тест 5: поворот на 1 радиан")
motor.target_rad(motor.get_pos_rad() + 1.0)
while not motor.is_target_reached(): time.sleep(0.01)
print("Готово, позиция:", motor.get_pos_rad(), "рад")

motor.stop()
motor.enable(True)
print("Отключено")
