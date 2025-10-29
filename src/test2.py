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

    def __imatmul__(self, target_coord): 
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
    def __init__(self, motor_x: Stepper, motor_y: Stepper):
        self.x = motor_x; self.y = motor_y
        self.home()
        
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
            
    def __ior__(self, coords):
            """
            Параллельное движение по двум осям: p |= (x_target, y_target)
            """
            target_x, target_y = coords
            dx = target_x - self.x.current_coord
            dy = target_y - self.y.current_coord

            # Проверка границ
            if not (0 <= target_x <= self.x.limit_coord_cm):
                raise ValueError('Выход за границы X')
            if not (0 <= target_y <= self.y.limit_coord_cm):
                raise ValueError('Выход за границы Y')

            # Подготовка направлений
            dir_x = dx > 0
            dir_y = dy > 0
            self.x.dir_pin.value(dir_x)
            self.y.dir_pin.value(dir_y)

            steps_x = int(abs(dx) * self.x.steps_per_mm * 10)
            steps_y = int(abs(dy) * self.y.steps_per_mm * 10)
            max_steps = max(steps_x, steps_y)

            # вычисляем задержку (по максимальной частоте)
            freq = min(self.x.freq, self.y.freq)
            delay_us = int(1_000_000 / freq / 2)

            # Алгоритм Брезенхэма для синхронного шага
            err_x = err_y = 0
            acc_x = acc_y = 0

            for i in range(max_steps):
                step_x = False
                step_y = False

                if steps_x:
                    acc_x += steps_x
                    if acc_x >= max_steps:
                        acc_x -= max_steps
                        step_x = True

                if steps_y:
                    acc_y += steps_y
                    if acc_y >= max_steps:
                        acc_y -= max_steps
                        step_y = True

                if step_x:
                    self.x.step_pin.on()
                if step_y:
                    self.y.step_pin.on()

                # короткая пауза — только если хоть один шаг сделан
                if step_x or step_y:
                    time.sleep_us(delay_us)
                    self.x.step_pin.off()
                    self.y.step_pin.off()
                    time.sleep_us(delay_us)

            # Обновляем текущие координаты
            self.x.current_coord = target_x
            self.y.current_coord = target_y
            return self
        
    
    
    def home(self, freq=None, *, direction=0, debounce_ms=100):
        """Общий home для портала (оба мотора синхронно по концевикам)"""
        if freq is None:
            freq = min(self.x.freq, self.y.freq)

        delay_us = int(1e6 / (2 * freq))
        if not self.x.enabled or not self.y.enabled:
            self.enable(True)

        self.x.dir_pin.value(direction)
        self.y.dir_pin.value(direction)

        x_done = False
        y_done = False

        while not (x_done and y_done):
            if not x_done:
                if self.x.sw_pin.value() == 0:
                    self.x.step_pin.on()
                else:
                    x_done = True
            if not y_done:
                if self.y.sw_pin.value() == 0:
                    self.y.step_pin.on()
                else:
                    y_done = True

            if not (x_done and y_done):
                time.sleep_us(delay_us)
                self.x.step_pin.off()
                self.y.step_pin.off()
                time.sleep_us(delay_us)

        time.sleep_ms(debounce_ms)
        self.x.current_coord = 0
        self.y.current_coord = 0




def test():
    m2=Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90)
    m1=Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60)
    
    with Portal(m2, m1) as p:
        p.x.freq = 30_000; p.y.freq = 30_000
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)

        p |= (45, 45) 
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)

        p |= (45, 45) 
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)
        # p.x += 30
        # p.y += 30
        # print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)

        # p.x -= 10
        # p.y -= 10
        # print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)

        # p.x @= 45
        # p.y @= 45
        # print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)




# python tools/webrepl_client.py -p 1234 192.168.0.92 -e  "\         
# import test2; \
# m2=test2.Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90); \
# m1=test2.Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60); \
# p = test2.Portal(m2, m1); \
# p.enable(True); \
# "

# python tools/webrepl_client.py -p 1234 192.168.0.92 -e  "p.x += 10"