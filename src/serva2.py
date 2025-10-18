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
            # del self

    def deinit(self):
        try: self.step_pwm.deinit()
        except: pass 
    

    async def home(self, freq=12_000, debounce_ms=150, start_event=None):
        """Возврат к концевику (нулевая позиция)"""
        if start_event: await start_event.wait()
        if not self.enabled: self.enable(True)
        if self.sw_pin.value() == 1:
            self.current_coord = 0; return
        
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
                    await asyncio.sleep_ms(debounce_ms)
                    break
                await asyncio.sleep_ms(2)
        finally:
            self.step_pwm.duty_u16(0)
            self.running = False
            await asyncio.sleep(0.5)
            self.current_coord = 0



    async def run(self, direction=1, freq=1000, duration=None, start_event=None):
        if not self.enabled: self.enable(True)
        self.current_dir = direction
        self.dir_pin.value(self.current_dir ^ self.invert_dir)
        self.step_pwm.freq(int(freq))
        if start_event: await start_event.wait()
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

                await asyncio.sleep_ms(5)
        finally:
            self.stop()
            

    async def move_to(self, target_mm=None, target_cm=None, freq=1000, start_event=None):
        """Асинхронное перемещение на мм"""
        if target_mm == None:
            if target_cm == None: raise RuntimeError('Не передано сколько передвигаться')
            else: target_mm = target_cm * 10
            
        if self.current_coord is None: await self.home(freq=12_000)
        distance_mm = target_mm - self.current_coord * 10
        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        await self.run(direction=direction, freq=freq, duration=duration, start_event=start_event)










    async def move_accel(self, distance_mm=None, max_freq=20000, 
                         min_freq=5000, accel_ratio=0.2, distance_cm=None, start_event=None):
        """Перемещение с плавным ускорением/торможением (через PWM), с учётом координатных ограничений"""
        if distance_mm is None and distance_cm is None:
            raise ValueError("Укажите distance_mm или distance_cm")
        if distance_mm is None:
            distance_mm = distance_cm * 10

        if self.current_coord is None:
            await self.home(freq=12_000)

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

        if start_event:
            await start_event.wait()

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
                        self.stop()
                        break
                else:
                    self.current_coord -= delta_cm
                    if self.sw_pin.value() == 1:
                        self.current_coord = 0
                        self.stop()
                        break

                steps_done += freq * dt_real
                await asyncio.sleep(dt)
        finally:
            self.stop()
            self.running = False
            await asyncio.sleep(0.1)
    

    
    
# async def test():
#     k = 95 / 60
#     m1 = StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, lead_mm=2.475, limit_coord=65)
#     m2 = StepperPWMAsync(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, lead_mm=2.475, limit_coord=90)
    
#     async with m1, m2:
#         start_event = asyncio.Event()
#         t1 = asyncio.create_task(m1.home(freq=12_000, start_event=start_event))
#         t2 = asyncio.create_task(m2.home(freq=k*12_000, start_event=start_event))
#         await asyncio.sleep(1)  
#         start_event.set()    
#         await asyncio.gather(t1, t2)
#         print(f'home done: m1={m1.current_coord}, m2={m2.current_coord}')


#         # start_event = asyncio.Event()
#         start_event = None
#         t1 = asyncio.create_task(m1.move_accel(distance_cm=60, max_freq=20_000, accel_ratio=0.2, start_event=start_event))
#         t2 = asyncio.create_task(m2.move_accel(distance_cm=60, max_freq=20_000, accel_ratio=0.2, start_event=start_event))
#         await asyncio.sleep(1)
#         # start_event.set()
#         await asyncio.gather(t1, t2)
#         print(f'run done: m1={m1.current_coord}, m2={m2.current_coord}')



class Portal:
    """
    Синхронный интерфейс для портала на двух шаговиках (X и Y).
    """
    def __init__(self, motor_x: StepperPWMAsync, motor_y: StepperPWMAsync, ratio_yx=1.0):
        """
        ratio_yx — коэффициент скорости для второго мотора относительно первого
        (например, если моторы двигают одну ось с разными передачами).
        """
        self.x = motor_x
        self.y = motor_y
        self.ratio_yx = ratio_yx

    # ======= ВСПОМОГАТЕЛЬНОЕ =======
    def _run(self, coro):
        """Запуск асинхронной задачи синхронно."""
        try:
            asyncio.run(coro)
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro)

    # ======= ПУБЛИЧНЫЕ МЕТОДЫ =======
    def enable(self, state=True):
        """Включить или выключить оба мотора."""
        self.x.enable(state)
        self.y.enable(state)

    def stop(self):
        """Остановить оба мотора."""
        self.x.stop()
        self.y.stop()

    def home(self, freq=12000):
        """Возврат к концевикам синхронно для обоих моторов."""
        async def _home():
            tasks = [asyncio.create_task(self.x.home(freq=freq)),
                     asyncio.create_task(self.y.home(freq=int(freq*self.ratio_yx)))]
            await asyncio.gather(*tasks)
        self._run(_home())

    def move_accel(self, x_cm=None, y_cm=None, max_freq=20000, accel_ratio=0.2):
        """Синхронное перемещение с плавным ускорением."""
        async def _move():
            tasks = []
            if x_cm is not None:
                tasks.append(asyncio.create_task(self.x.move_accel(distance_cm=x_cm,
                                max_freq=max_freq, accel_ratio=accel_ratio)))
            if y_cm is not None:
                tasks.append(asyncio.create_task(self.y.move_accel(distance_cm=y_cm,
                                max_freq=int(max_freq*self.ratio_yx), accel_ratio=accel_ratio)))
            await asyncio.gather(*tasks)
        self._run(_move())

    def move_to(self, x_mm=None, y_mm=None, freq=10000):
        """Простое перемещение без ускорения."""
        async def _move():
            tasks = []
            if x_mm is not None:
                tasks.append(asyncio.create_task(self.x.move_to(distance_mm=x_mm, freq=freq)))
            if y_mm is not None:
                tasks.append(asyncio.create_task(self.y.move_to(distance_mm=y_mm, freq=int(freq*self.ratio_yx))))
            await asyncio.gather(*tasks)
        self._run(_move())

    def deinit(self):
        """Деинициализация PWM."""
        self.x.deinit()
        self.y.deinit()

    def __enter__(self):
        self.enable(True)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type: 
                raise exc_type(exc) from tb
        finally:
            self.enable(False)
            self.deinit()
            
            
            
            
            
async def test():
    m1 = StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, lead_mm=2.475, limit_coord=65)
    m2 = StepperPWMAsync(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, lead_mm=2.475, limit_coord=90)

    with Portal(m1, m2, ratio_yx=90/64) as portal:
        portal.home(freq=12_000)
        portal.move_to(x_mm=30, y_mm=40, freq=12_000)
        portal.move_to(x_mm=10, y_mm=10, freq=15_000)


