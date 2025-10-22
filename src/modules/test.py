from machine import Pin, PWM
import time 

class StepperPWM:
    def __init__(self, step_pin, dir_pin, en_pin, sw_pin,
                 steps_per_rev=200, invert_dir=False, invert_enable=False, 
                 lead_mm=8, limit_coord=None):
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
        self._freq = 0

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
        if 0 <= new_freq <= 50_000: self._freq = new_freq
        else: raise ValueError('Неккоректное значение, дб 0 ≤ freq ≤ 50_000')
        
        
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
        self.freq = freq
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
            
        if self.current_coord is None: self.home(freq=12_000)
        distance_mm = target_mm - self.current_coord * 10
        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        self.run(direction=direction, freq=freq, duration=duration)


    def move_accel(self, distance_mm=None, max_freq=20000, 
                         min_freq=5000, accel_ratio=0.2, distance_cm=None):
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
    

    def __add__(self, coord): return self.move_accel(coord)
    def __sub__(self, coord): return self.move_accel(-coord)
    def __imatmul__(self, coord): return self.move_to(coord)





class Portal:
    def __init__(self, motor_x: StepperPWM, motor_y: StepperPWM, start_freq=None):
        self.x = motor_x
        self.y = motor_y
        
        if start_freq is not None:
            self.x.freq = start_freq
            self.y.freq = start_freq
        self.home()

    def enable(self, state=True):
        """Включить или выключить оба мотора."""
        self.x.enable(state)
        self.y.enable(state)

    def stop(self):
        """Остановить оба мотора."""
        self.x.stop()
        self.y.stop()

    def home(self, freq=12000):
        self.x.home(freq=freq)
        freq_y = int(freq * self.y.limit_coord / self.x.limit_coord)
        self.y.home(freq=freq_y)


    def move_accel(self, x_cm=None, y_cm=None, max_freq=20000, accel_ratio=0.2):
        if x_cm is not None: self.x.move_accel(distance_cm=x_cm, max_freq=max_freq)
        if y_cm is not None: self.y.move_accel(distance_cm=y_cm, max_freq=max_freq)

    def move_to(self, x_mm=None, y_mm=None, freq=10000):
        if self.x.is_running() or self.y.is_running():
            raise RuntimeError("Движение уже выполняется")
        if x_mm is not None: self.x.move_to(target_mm=x_mm, freq=freq)
        if y_mm is not None: self.y.move_to(target_mm=y_mm, freq=freq)


    def __enter__(self):
        self.enable(True)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type: raise exc_type(exc) from tb
        finally: self.enable(False)
            
    def __add__(self, coord: tuple[float, float]): 
        x_cm, y_cm = coord
        if x_cm: self.x.move_to(target_cm=x_cm+self.x.current_coord)
        if y_cm: self.y.move_to(target_cm=y_cm+self.y.current_coord)
        
    def __sub__(self, coord: tuple[float, float]): 
        return self.__add__(-coord)

    def __imatmul__(self, coord):
        x_cm, y_cm = coord
        if x_cm: self.x.move_to(target_cm=x_cm)
        if y_cm: self.y.move_to(target_cm=y_cm)

    def move_to(self, coord, freq=None):
        x_cm, y_cm = coord
        if x_cm: self.x.move_to(target_cm=x_cm, freq=freq)
        if y_cm: self.y.move_to(target_cm=y_cm, freq=freq)



    def __iadd__(self, coord): return self.__add__(coord)
    def __isub__(self, coord): return self.__sub__(coord)



    def __repr__(self):
        return (f"<Portal x={self.x.current_coord:.2f}cm "
                f"y={self.y.current_coord:.2f}cm "
                f"running={self.x.is_running() or self.y.is_running()}>")


    @property
    def pos(self): return (self.x.current_coord, self.y.current_coord)
    @pos.setter
    def pos(self, coord): self.move_to(coord)

    def is_busy(self):
        """Проверка, движется ли хотя бы один из моторов"""
        return self.x.is_running() or self.y.is_running()



    def move_accel(self, x_mm=0, y_mm=0, max_freq=20000, min_freq=5000, accel_ratio=0.2):
        """Параллельное движение двух осей с ускорением/торможением"""
        if self.x.current_coord is None: self.x.home(freq=12000)
        if self.y.current_coord is None: self.y.home(freq=12000)
        dx = x_mm
        dy = y_mm

        # Самое длинное движение определяет общее время
        dist_max = max(abs(dx), abs(dy))
        if dist_max == 0: return

        # Отношение шагов для каждой оси (чтобы сохранить пропорции движения)
        ratio_x = abs(dx) / dist_max if dx else 0
        ratio_y = abs(dy) / dist_max if dy else 0

        # Настраиваем направление
        self.x.dir_pin.value(1 if dx > 0 else 0)
        self.y.dir_pin.value(1 if dy > 0 else 0)
        self.x.enable(True)
        self.y.enable(True)

        self.x.running = True
        self.y.running = True

        dt = 0.005
        steps_total = dist_max * self.x.steps_per_rev / self.x.lead_mm
        accel_steps = max(1, int(steps_total * accel_ratio))
        decel_start = steps_total - accel_steps
        steps_done = 0
        last_time = time.ticks_ms()

        try:
            while steps_done < steps_total and (self.x.running or self.y.running):
                # Фаза ускорения/равномерного/торможения
                if steps_done < accel_steps:
                    ratio = steps_done / accel_steps
                    freq = min_freq + (max_freq - min_freq) * ratio
                elif steps_done > decel_start:
                    ratio = (steps_total - steps_done) / accel_steps
                    freq = min_freq + (max_freq - min_freq) * max(0, ratio)
                else:
                    freq = max_freq

                freq = max(min_freq, min(freq, max_freq))

                now = time.ticks_ms()
                dt_real = time.ticks_diff(now, last_time) / 1000
                last_time = now

                # Считаем смещения по каждой оси (пропорционально ratio_x / ratio_y)
                delta_mm = dt_real * freq * self.x.lead_mm / self.x.steps_per_rev
                dx_step = delta_mm * ratio_x * (1 if dx > 0 else -1)
                dy_step = delta_mm * ratio_y * (1 if dy > 0 else -1)

                self.x.current_coord += dx_step / 10
                self.y.current_coord += dy_step / 10

                # Обновляем ШИМ частоты для каждой оси
                if ratio_x: self.x.step_pwm.freq(int(freq * ratio_x))
                if ratio_y: self.y.step_pwm.freq(int(freq * ratio_y))

                self.x.step_pwm.duty_u16(32768)
                self.y.step_pwm.duty_u16(32768)

                steps_done += freq * dt_real
                time.sleep(dt)

        finally:
            self.x.stop()
            self.y.stop()
            self.x.running = False
            self.y.running = False
            time.sleep(0.05)




def test():
    portal = Portal(
        motor_x=StepperPWM(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, lead_mm=2.475, limit_coord=60),
        motor_y=StepperPWM(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, lead_mm=2.475, limit_coord=90),
        start_freq=12_000
    )

    with portal:
        print(f'home done: x={portal.x.current_coord}, y={portal.x.current_coord}')
        portal @= (10, 10)
        time.sleep(0.5)
        portal.x += 5
        portal.y += 5
        time.sleep(1)
        print(f'home done: x={portal.x.current_coord}, y={portal.x.current_coord}')

        portal += (5, 0)    # сдвиг
        portal -= (3, 2)
        portal @= (0, 0)    # домой


    portal += (10, 5)
    while portal.is_busy():
        print(f"X={portal.x.current_coord:.2f} Y={portal.y.current_coord:.2f}")
        time.sleep(0.1)
    else: print("Движение завершено ✅")