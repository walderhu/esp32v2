from machine import Pin, PWM
import uasyncio as asyncio
import time 
import math

class StepperPWMAsync:
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
        self.freq = 0

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

    async def __aenter__(self):
        self.enable(True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type: 
                raise exc_type(exc) from tb
        finally:
            self.enable(0)
            # self.deinit()
            await asyncio.sleep(0.2)

    def deinit(self):
        try: self.step_pwm.deinit()
        except: pass 
    
    
# def deinit(self):
#     try:
#         if hasattr(self, "step_pwm") and self.step_pwm:
#             self.step_pwm.deinit()
#     except Exception as e:
#         print("PWM deinit skipped:", e)

    async def home(self, freq=1000, debounce_ms=150):
        """Возврат к концевику (нулевая позиция)"""
        if not self.enabled: self.enable(True)
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
                    self.current_coord = 0
                    await asyncio.sleep_ms(debounce_ms)
                    break
                await asyncio.sleep_ms(2)
        finally:
            self.step_pwm.duty_u16(0)
            self.running = False
            await asyncio.sleep(0.5)



    async def run(self, direction=1, freq=1000, duration=None):
        if not self.enabled: self.enable(True)
        if self.sw_pin.value() == 1: 
            self.stop(); return

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

        step_interval_ms = 1000 / freq
        last_step_time = time.ticks_ms()

        try:
            while self.running:
                now = time.ticks_ms()
                if time.ticks_diff(now, last_step_time) >= step_interval_ms:
                    if self.current_dir == 1:
                        self.current_coord += 1
                    else:
                        self.current_coord -= 1
                    last_step_time = now

                if self.sw_pin.value() == 1:
                    self.current_dir ^= 1
                    self.dir_pin.value(self.current_dir ^ self.invert_dir)
                    await asyncio.sleep_ms(200)  # антидребезг
                    self.step_pwm.duty_u16(32768)

                if stop_time and time.ticks_diff(now, stop_time) >= 0:
                    self.stop(); break

                if not (0 < self.current_coord <= self.limit_coord):
                    self.stop(); break

                await asyncio.sleep_ms(5)
        finally:
            self.step_pwm.duty_u16(0)
            
            
    async def run(self, direction=1, freq=1000, duration=None):
        if not self.enabled: self.enable(True)
        self.current_dir = direction
        self.dir_pin.value(self.current_dir ^ self.invert_dir)
        self.step_pwm.freq(int(freq))
        self.step_pwm.duty_u16(32768)
        self.running = True

        if duration:
            await asyncio.sleep(duration)

        self.stop()

'''
    async def move(self, distance_mm=None, distance_cm=None, freq=1000):
        """Асинхронное перемещение на мм"""
        if distance_mm == None:
            if distance_cm == None: raise RuntimeError('Не передано сколько передвигаться')
            else: distance_mm = distance_cm * 10
        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        await self.run(direction=direction, freq=freq, duration=duration)

    async def move_accel(self, distance_mm=None, max_freq=20000, 
                        min_freq=5000, accel_ratio=0.2, distance_cm=None):
        """Перемещение с плавным ускорением/торможением (через PWM) с учётом координат"""
        if distance_mm is None and distance_cm is None: 
            raise ValueError("Укажите distance_mm или distance_cm")
        if distance_mm is None: 
            distance_mm = distance_cm * 10

        direction = 1 if distance_mm > 0 else 0
        self.dir_pin.value(direction ^ self.invert_dir)
        self.enable(True)

        steps_total = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        accel_steps = max(1, int(steps_total * accel_ratio))
        decel_start = steps_total - accel_steps

        self.step_pwm.duty_u16(32768)
        self.running = True

        steps_done = 0
        dt = 0.005  # ~5 мс
        step_interval_ms = 1000 / max_freq
        last_step_time = time.ticks_ms()

        while steps_done < steps_total and self.running:
            now = time.ticks_ms()

            # проверка концевика и ограничения по координате
            if (direction == 1 and self.current_coord >= getattr(self, "max_coord", float('inf'))) or \
            (direction == 0 and self.current_coord <= 0):
                self.stop()
                break

            # рассчёт частоты с ускорением/торможением
            if steps_done < accel_steps:  # ускорение
                ratio = steps_done / accel_steps
                freq = min_freq + (max_freq - min_freq) * ratio
            elif steps_done > decel_start:  # торможение
                ratio = (steps_total - steps_done) / accel_steps
                freq = min_freq + (max_freq - min_freq) * max(0, ratio)
            else:
                freq = max_freq

            freq = max(min_freq, min(freq, max_freq))
            self.step_pwm.freq(int(freq))

            # обновление координаты в зависимости от направления
            step_interval_ms = 1000 / freq
            if time.ticks_diff(now, last_step_time) >= step_interval_ms:
                if direction == 1:
                    self.current_coord += 1
                else:
                    self.current_coord -= 1
                steps_done += 1
                last_step_time = now

            await asyncio.sleep(dt)

        self.stop()
        await asyncio.sleep(0.1)
        self.running = False

'''
m1 = StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, lead_mm=2.5, limit_coord=60)
m2 = StepperPWMAsync(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, lead_mm=2.5, limit_coord=90)

async def test():
    async with m1, m2: 
        # await m1.home(freq=12_000)
        # await m2.home(freq=12_000)
        m1.current_coord = 0
        print(m1.current_coord)
        await m1.run(direction=1, freq=8_000, duration=1)
        
        
        # m1.enable(True)
        # m1.dir_pin.value(1)
        # m1.step_pwm.freq(8000)
        # m1.step_pwm.duty_u16(32768)
        # await asyncio.sleep(1)
        # m1.stop()

        # await m2.run(direction=1, freq=8_000, duration=2)

