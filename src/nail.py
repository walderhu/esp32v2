from machine import Pin, PWM
import uasyncio as asyncio
import time 
import math


class StepperPWMAsync:
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
        self.step_pwm.freq(1000)
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
        self.step_pwm.freq(freq)
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
        """
        Асинхронное вращение с поддержкой концевика:
        - Если концевик уже сработал в выбранном направлении — меняем направление
        - Во время движения: при срабатывании концевика — меняем направление
        """
        if not self.enabled:
            self.enable(True)

        # Проверка концевика перед стартом
        if direction == 0 and self.sw_pin.value() == 1:
            direction = 1
        elif direction == 1 and self.sw_pin.value() == 1:
            direction = 0

        self.dir_pin.value(direction ^ self.invert_dir)
        self.step_pwm.freq(freq)
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


    async def move_mm(self, distance_mm, freq=1000):
        """Асинхронное перемещение на мм"""
        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        await self.run(direction=direction, freq=freq, duration=duration)

    # ---------------------- Утилиты ----------------------

    def set_speed_rps(self, rps):
        """Настроить частоту вращения по оборотам в секунду"""
        self.freq = rps * self.steps_per_rev
        if self.running:
            self.step_pwm.freq(int(self.freq))

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
            self.enable(False)

    class StepperEngineError(Exception):
        def __init__(self, message): super().__init__(message)



    def cleanup(self):
        """Отключить PWM и очистить ресурсы"""
        
        for p in [14, 15, 13]:
            try: PWM(Pin(p)).deinit()
            except: pass

        self.stop()
        if self.en_pin: self.en_pin.value((not self.invert_enable))
        import gc; gc.collect()


    # async def move_mm_accel(self, distance_mm, max_freq=1000):
    #     """
    #     Перемещение с косинусным ускорением и торможением через PWM
    #     - 10% пути на разгон
    #     - 80% на постоянной max_freq
    #     - 10% на торможение
    #     """
    #     steps = int(abs(distance_mm) * self.steps_per_rev / self.lead_mm)
    #     self.dir_pin.value(1 if distance_mm > 0 else 0)
    #     self.enable(True)

    #     self.step_pwm.duty_u16(32768)  # PWM включён постоянно

    #     accel_steps = max(1, steps // 10)
    #     decel_start = steps - accel_steps

    #     for i in range(steps):
    #         if i < accel_steps:
    #             ratio = i / accel_steps
    #             freq = max_freq * (1 - math.cos(math.pi / 2 * ratio))  # разгон
    #         elif i >= decel_start:
    #             ratio = (i - decel_start) / accel_steps
    #             freq = max_freq * math.cos(math.pi / 2 * ratio)        # торможение
    #         else:
    #             freq = max_freq

    #         freq = max(1, freq)
    #         self.step_pwm.freq(int(freq))  # меняем частоту PWM прямо на лету

    #         # маленькая пауза, чтобы цикл asyncio не заблокировал
    #         await asyncio.sleep_ms(1)



async def move_mm_accel(self, distance_mm, max_freq=1000):
    """
    Точный путь с косинусным ускорением и торможением.
    Каждый шаг считается вручную, чтобы пройденная дистанция = distance_mm
    """
    steps = int(abs(distance_mm) * self.steps_per_rev / self.lead_mm)
    self.dir_pin.value(1 if distance_mm > 0 else 0)
    self.enable(True)

    accel_steps = max(1, steps // 10)
    decel_start = steps - accel_steps

    for i in range(steps):
        # Косинусное ускорение/торможение
        if i < accel_steps:
            ratio = i / accel_steps
            freq = max_freq * (1 - math.cos(math.pi / 2 * ratio))
        elif i >= decel_start:
            ratio = (i - decel_start) / accel_steps
            freq = max_freq * math.cos(math.pi / 2 * ratio)
        else:
            freq = max_freq

        freq = max(1, freq)
        delay = 1 / freq / 2  # делим на 2, потому что на HIGH и LOW

        # делаем один шаг вручную
        self.step_pwm.duty_u16(32768)  # поднять step
        await asyncio.sleep(delay)
        self.step_pwm.duty_u16(0)      # опустить step
        await asyncio.sleep(delay)
    

# ---------------------- Точка входа ----------------------
import uasyncio as asyncio

async def main():
    async with StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13, lead_mm=2.5) as motor:
        await motor.home(freq=12_000)
        
    
async def test():
    
    motor = StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13, lead_mm=2.5)
    motor.enable(True)

    try:    
        await motor.home(freq=12_000)
        await motor.move_mm(distance_mm=60 * 10, freq=12_000) # 60l
    finally:
        motor.cleanup()

asyncio.run(test())
