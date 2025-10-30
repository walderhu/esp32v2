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
        self.home(freq=30_000)
        
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
            target_dx_cm, target_dy_cm = coords
            dx_cm = target_dx_cm -  self.x.current_coord
            dy_cm = target_dy_cm -  self.y.current_coord
            self.parallel_accel_move(dx_cm=dx_cm, dy_cm=dy_cm, accel_grain=20)
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

    def home(self, freq=None, *, direction=0, debounce_ms=100):
        """Общий home для портала (X движется в 1.5 раза быстрее, чем Y)"""
        if freq is None: freq = min(self.x.freq, self.y.freq)
        delay_x_us = int(1e6 / (2 * (freq)))  # X быстрее
        if not self.x.enabled or not self.y.enabled: self.enable(True)
        self.x.dir_pin.value(direction)
        self.y.dir_pin.value(direction)
        x_done = False; y_done = False
        counter = 0 
        while not (x_done and y_done):
            counter += 1
            if not x_done:
                if self.x.sw_pin.value() == 0:
                    self.x.step_pin.on()
                else: x_done = True

            if not y_done and counter % 2 == 0:
                if self.y.sw_pin.value() == 0:
                    self.y.step_pin.on()
                else: y_done = True

            if not (x_done and y_done):
                time.sleep_us(delay_x_us)
                self.x.step_pin.off()
                self.y.step_pin.off()
                time.sleep_us(delay_x_us)

        time.sleep_ms(debounce_ms)
        self.x.current_coord = 0
        self.y.current_coord = 0


    def parallel_accel_move(self, dx_cm, dy_cm, max_freq=50_000, min_freq=5000,
                             accel_ratio=0.15, accel_grain=10):
        """
        Параллельное синхронное движение X/Y с accel/cruise/decel.
        Акцент на минимальную память: delay-runlist вместо per-step массивов.
        """
        if max_freq is None: max_freq = min(self.x.freq, self.y.freq)
        target_x = self.x.current_coord + dx_cm
        target_y = self.y.current_coord + dy_cm
        if not (0 <= target_x <= self.x.limit_coord_cm): raise ValueError("Выход за границы X")
        if not (0 <= target_y <= self.y.limit_coord_cm): raise ValueError("Выход за границы Y")
        
        if target_x == 0: 
            self.x.home(freq=16_000)
            return self
        if target_y == 0: 
            self.y.home(freq=16_000)
            return self
        
        dir_x = dx_cm > 0; self.x.dir_pin.value(dir_x)
        dir_y = dy_cm > 0; self.y.dir_pin.value(dir_y)
        # шаги (целые)
        steps_x = int(abs(dx_cm) * self.x.steps_per_mm * 10)
        steps_y = int(abs(dy_cm) * self.y.steps_per_mm * 10)
        steps_total = max(steps_x, steps_y)
        if steps_total == 0: return self

        # phases
        accel_steps = max(1, int(steps_total * accel_ratio))
        decel_steps = accel_steps
        cruise_steps = steps_total - accel_steps - decel_steps
        if cruise_steps < 0:
            cruise_steps = 0

        # минимальные/максимальные задержки (в микросекундах)
        min_delay_us = int(1_000_000 / max_freq / 2)
        # max_delay_us = int(1_000_000 / min_freq / 2)
        # delta = max_delay_us - min_delay_us

        # --- Построим компактный runlist: список (delay_us, count) ---
        # Разгон: лесенка с шагом accel_grain
        runs = []
        s = 0
        while s < accel_steps:
            repeats = min(accel_grain, accel_steps - s)
            # ratio в диапазоне [0,1)
            ratio = s / accel_steps
            freq = min_freq + int((max_freq - min_freq) * ratio)
            delay_us = int(1_000_000 / freq / 2)
            runs.append((delay_us, repeats))
            s += repeats

        # Круиз (один run)
        if cruise_steps > 0: runs.append((min_delay_us, cruise_steps))
        # Торможение — зеркально разгону
        # возьмём delays из runs, соответствующие разгонной части
        # (только первые N разгонных записей суммарно = accel_steps)
        # и добавим их в обратном порядке
        # собираем разгонные элементы (delay,count) в список, затем mirror
        accel_part = []
        remaining = accel_steps
        idx = 0
        while remaining > 0 and idx < len(runs):
            d, c = runs[idx]
            take = min(c, remaining)
            accel_part.append((d, take))
            remaining -= take
            idx += 1
        # mirror
        for d, c in reversed(accel_part): runs.append((d, c))

        # Убедимся, что суммарно steps == steps_total (инвариант)
        total_runs_steps = sum(c for _, c in runs)
        if total_runs_steps < steps_total:
            # дополним круизом
            runs.append((min_delay_us, steps_total - total_runs_steps))
        elif total_runs_steps > steps_total:
            # если вдруг получилось лишнее (маловероятно), обрежем последний run
            extra = total_runs_steps - steps_total
            d, c = runs[-1]
            runs[-1] = (d, c - extra)
            if runs[-1][1] == 0: runs.pop()

        # --- Подготовка для шага: целочисленный "Bresenham-like" счетчик ---
        # В цикле будем делать:
        # acc_x += steps_x; if acc_x >= steps_total: acc_x -= steps_total; step_x = True
        acc_x = 0; acc_y = 0
        # Локальные пины для скорости
        sx_pin = self.x.step_pin; sy_pin = self.y.step_pin
        # --- Основной цикл: проходим runs, внутри — count шагов с одним delay ---
        for delay_us, count in runs:
            # count — обычно accel_grain или cruise chunk; небольшое число
            for _ in range(count):
                # вычисления — целые операции (быстро)
                acc_x += steps_x; acc_y += steps_y
                step_x = False; step_y = False
                if acc_x >= steps_total:
                    acc_x -= steps_total
                    step_x = True
                if acc_y >= steps_total:
                    acc_y -= steps_total
                    step_y = True

                # физический шаг
                if step_x: sx_pin.on()
                if step_y: sy_pin.on()
                time.sleep_us(delay_us)
                if step_x: sx_pin.off()
                if step_y: sy_pin.off()
                time.sleep_us(delay_us)

        self.x.current_coord += dx_cm
        self.y.current_coord += dy_cm
        return self



def test():
    m2=Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90)
    m1=Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60)
    
    with Portal(m2, m1) as p:
        p.x.freq = 50_000; p.y.freq = 50_000
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)
        p |= (90, 60)
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)
        p |= (45, 30)
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)
        p |= (0, 0)
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)
        p |= (30, 0)
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)
        p |= (0, 30)
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)
        p |= (0, 30)
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)
        p |= (30, 30)
        print("X coord:", p.x.current_coord, "Y coord:", p.y.current_coord)
        p |= (45, 30)
        p |= (40, 45)





# python tools/webrepl_client.py -p 1234 192.168.0.92 -e  "\         
# import test2; \
# m2=test2.Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90); \
# m1=test2.Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60); \
# p = test2.Portal(m2, m1); \
# p.enable(True); \
# "

# python tools/webrepl_client.py -p 1234 192.168.0.92 -e  "p.x += 10"