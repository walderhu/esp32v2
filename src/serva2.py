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
                delta_s = delta_ms * 1000
                delta_mm = delta_s * self.lead_mm * self.steps_per_rev / freq
                delta_cm = delta_mm / 10
                if direction == 0:
                    delta_cm = -delta_cm
                self.current_coord += delta_cm
                last_step_time = now

                if self.sw_pin.value() == 1 and direction == 0:
                    self.stop() # начало из концевика и движение на концевик
                    break

                if stop_time and time.ticks_diff(now, stop_time) >= 0:
                    self.stop() # ограничение по времени
                    break

                # if not (0 < self.current_coord <= self.limit_coord):
                #     self.stop(); break

                await asyncio.sleep_ms(5)
        finally:
            self.stop()
            

m1 = StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, lead_mm=2.5, limit_coord=60)
m2 = StepperPWMAsync(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, lead_mm=2.5, limit_coord=90)

async def test():
    async with m1:
        await m1.home(freq=12_000)
        print(m1.current_coord)
        
        await m1.run(direction=1, freq=6_000, duration=3)
        print(m1.current_coord)
        await asyncio.sleep(1)
        
        await m1.run(direction=0, freq=6_000, duration=5)
        print(m1.current_coord)
        # await asyncio.sleep(1)
        
        await m1.run(direction=1, freq=6_000, duration=3)
        print(m1.current_coord)
        
        