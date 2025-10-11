from machine import Pin, PWM
import uasyncio as asyncio
import time 
import math


class StepperPWMAsync:
    count = 0  

    def __new__(cls, *args, **kwargs):
        cls.count += 1
        instance = super().__new__(cls)
        instance.id = cls.count
        return instance
    
    def __init__(self, step_pin=14, dir_pin=15, en_pin=13,
                 steps_per_rev=200, invert_dir=False, invert_enable=False, lead_mm=8):
        self.step_pwm = PWM(Pin(step_pin))
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.en_pin = Pin(en_pin, Pin.OUT) if en_pin is not None else None

        self.steps_per_rev = steps_per_rev
        self.invert_dir = invert_dir
        self.invert_enable = invert_enable
        self.lead_mm = lead_mm

        self.enabled = False
        self.running = False
        self.current_dir = 1
        self.freq = 0

        self.step_pwm.duty_u16(0)
        self.step_pwm.freq(1000 + self.id)
        self.enable(False)
        self.sw_pin = Pin(27, Pin.IN, Pin.PULL_UP)


    def enable(self, state=True):
        """Включить или выключить драйвер"""
        self.enabled = state
        if self.en_pin:
            pin_state = (not state) if not self.invert_enable else state
            self.en_pin.value(pin_state)
        if not state:
            self.stop()

    def stop(self):
        """Остановить вращение (убрать импульсы)"""
        self.step_pwm.duty_u16(0)
        self.running = False

                

    async def home(self, freq=1000, debounce_ms=150):
        """Возврат к концевику (нулевая позиция)"""
        if not self.enabled: self.enable(True)
        self.dir_pin.value(0 ^ self.invert_dir)
        self.step_pwm.freq(freq + self.id)
        self.step_pwm.duty_u16(32768)
        self.running = True
        self.current_dir = 0
        self.freq = freq
        try:
            while True:
                if self.sw_pin.value() == 1: 
                    self.step_pwm.duty_u16(0)
                    await asyncio.sleep_ms(debounce_ms)
                    self.position_steps = 0
                    break
                await asyncio.sleep_ms(2)
        finally:
            self.step_pwm.duty_u16(0)
            self.running = False
            await asyncio.sleep(0.5)

        
        
    async def run(self, direction=1, freq=1000, duration=None):
        if not self.enabled: self.enable(True)

        if direction == 0 and self.sw_pin.value() == 1:
            direction = 1
        elif direction == 1 and self.sw_pin.value() == 1:
            direction = 0

        self.dir_pin.value(direction ^ self.invert_dir)
        self.step_pwm.freq(freq + self.id)
        self.step_pwm.duty_u16(32768)
        self.running = True
        self.current_dir = direction
        self.freq = freq

        start_time = time.ticks_ms()
        stop_time = None
        if duration is not None:
            stop_time = time.ticks_add(start_time, int(duration * 1000))

        try:
            while self.running:
                sw_state = self.sw_pin.value()

                # Если движемся к концевику и он сработал — меняем направление
                if sw_state == 1:
                    self.current_dir ^= 1
                    self.dir_pin.value(self.current_dir ^ self.invert_dir)
                    await asyncio.sleep_ms(200)  # защита от дребезга
                    self.step_pwm.duty_u16(32768)  # снова включаем шаги

                # Проверка по времени
                if stop_time and time.ticks_diff(time.ticks_ms(), stop_time) >= 0:
                    self.stop()
                    break

                await asyncio.sleep_ms(5)
        finally:
            self.step_pwm.duty_u16(0)



        

    async def run_deg(self, deg, speed_hz):
        """Асинхронное вращение на угол (градусы)"""
        steps = int(self.steps_per_rev * deg / 360.0)
        duration = abs(steps / speed_hz)
        direction = 1 if steps > 0 else 0
        await self.run(direction=direction, freq=abs(speed_hz), duration=duration)

    async def run_rev(self, revs, speed_hz):
        """Асинхронное вращение на обороты"""
        deg = revs * 360.0
        await self.run_deg(deg, speed_hz)


    async def move(self, distance_mm=None, distance_cm=None, freq=1000):
        """Асинхронное перемещение на мм"""
        if distance_mm == None:
            if distance_cm == None: raise RuntimeError('Не передано сколько передвигаться')
            else: distance_mm = distance_cm * 10
        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        await self.run(direction=direction, freq=freq, duration=duration)

    # ---------------------- Утилиты ----------------------

    def set_speed_rps(self, rps):
        """Настроить частоту вращения по оборотам в секунду"""
        self.freq = rps * self.steps_per_rev
        if self.running:
            self.step_pwm.freq(int(self.freq) + self.id)

    def is_running(self): return self.running
    def is_enabled(self): return self.enabled

    # ---------------------- Контекстный менеджер ----------------------

    async def __aenter__(self):
        self.enable(True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type: raise self.StepperEngineError(str(exc))
        finally:
            self.stop()
            self.deinit()
            self.enable(False)

    class StepperEngineError(Exception):
        def __init__(self, message): super().__init__(message)

    def deinit(self):
        try: self.step_pwm.deinit()
        except: pass 
        
        
    async def move_accel(self, distance_mm=None, max_freq=20000, 
                            min_freq=5000, accel_ratio=0.2, distance_cm=None):
        """Перемещение с плавным ускорением/торможением (через PWM)"""
        if distance_mm is None and distance_cm is None: 
            raise ValueError("Укажите distance_mm или distance_cm")
        if distance_mm is None: distance_mm = distance_cm * 10
        
        direction = 1 if distance_mm > 0 else 0
        self.dir_pin.value(direction ^ self.invert_dir)
        self.enable(True)

        steps_total = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        accel_steps = max(1, int(steps_total * accel_ratio)) # 20% ускорение, 20% торможение
        decel_start = steps_total - accel_steps

        self.step_pwm.duty_u16(32768)
        self.running = True

        steps_done = 0; dt = 0.005  # шаг по времени ~5 мс

        while steps_done < steps_total and self.running:
            if steps_done < accel_steps:  # ускорение
                ratio = steps_done / accel_steps
                freq = min_freq + (max_freq - min_freq) * ratio
            elif steps_done > decel_start:  # торможение
                ratio = (steps_total - steps_done) / accel_steps
                freq = min_freq + (max_freq - min_freq) * max(0, ratio)
            else:
                freq = max_freq

            freq = max(min_freq, min(freq, max_freq))
            self.step_pwm.freq(int(freq) + self.id)
            steps_done += freq * dt * 2
            await asyncio.sleep(dt)

        self.stop()
        await asyncio.sleep(0.1)
        self.running = False


# ---------------------- Точка входа ----------------------
import uasyncio as asyncio

motor1 = StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13, lead_mm=2.5)
motor2 = StepperPWMAsync(step_pin=16, dir_pin=4, en_pin=2, lead_mm=2.5)

async def main():
    await motor1.home(freq=10_000)
    await motor1.move(distance_cm=5, freq=12_000),
    await asyncio.gather(
        motor1.move(distance_cm=30, freq=12_000),
        motor2.move_accel(distance_cm=-75, max_freq=20_000),
        # motor2.move(distance_cm=50, freq=12_000)
    )
    
    await asyncio.sleep(0.2)
    await motor2.move(distance_cm=50, freq=12_000)

asyncio.run(main())
