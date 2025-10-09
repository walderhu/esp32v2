import machine
from machine import Pin
import uasyncio as asyncio

class AsyncStepper:
    def __init__(self, step_pin, dir_pin, en_pin=None, steps_per_sec=200,
                 invert_dir=False, invert_enable=True, drive=Pin.DRIVE_3):
        
        if not isinstance(step_pin, machine.Pin):
            step_pin = machine.Pin(step_pin, machine.Pin.OUT, drive=drive)
        if not isinstance(dir_pin, machine.Pin):
            dir_pin = machine.Pin(dir_pin, machine.Pin.OUT, drive=drive)
        if (en_pin is not None) and (not isinstance(en_pin, machine.Pin)):
            en_pin = machine.Pin(en_pin, machine.Pin.OUT, drive=drive)  
        
        self.step_pin, self.dir_pin, self.en_pin = step_pin, dir_pin, en_pin
        self.invert_dir = invert_dir
        self.invert_enable = invert_enable
        self.steps_per_sec = steps_per_sec
        self.steps_per_sec = min(steps_per_sec, 1000)  

        self.enabled = True
        self.pos = 0
        self.target_pos = 0
        self.target_reached = True
        self.free_run_mode = 0
        self._task = None
        self.enable(True)

    def enable(self, e):
        self.enabled = e
        if self.en_pin: self.en_pin.value(bool(e) ^ self.invert_enable)
        if not e: self.dir_pin.value(0)

    def step(self, d):
        if d == 0 or not self.enabled: return
        self.dir_pin.value(int(d > 0) ^ self.invert_dir)
        self.step_pin.value(1)
        self.step_pin.value(0)
        self.pos += 1 if d > 0 else -1

    def move_to(self, target):
        self.target_pos = target
        self.target_reached = False
        self.start_task()

    def free_run(self, direction):
        self.free_run_mode = direction
        self.start_task()

    async def _run(self):
        try:
            while self.enabled and (self.free_run_mode != 0 or not self.target_reached):
                if self.free_run_mode > 0:          self.step(1)
                elif self.free_run_mode < 0:        self.step(-1)
                elif self.target_pos > self.pos:    self.step(1)
                elif self.target_pos < self.pos:    self.step(-1)
                else: self.target_reached = True
                await asyncio.sleep(1 / self.steps_per_sec)
        except asyncio.CancelledError: pass
        finally: self._task = None

    def start_task(self):
        if self._task is None: self._task = asyncio.create_task(self._run())

    def stop_task(self):
        if self._task:
            self._task.cancel()
            self._task = None
        self.free_run_mode = 0
        self.enable(False) 


    async def __aenter__(self):
        self.enable(not self.invert_enable)
        await asyncio.sleep(0)
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        try:
            if exc_type: raise self.AsyncStepperEngineError(str(exc_val))
        finally:
            self.stop()
            self.enable(self.invert_enable)
            await asyncio.sleep(0)


    class AsyncStepperEngineError(Exception):
        def __init__(self, message): super().__init__(message)
        

async def main():
    async with AsyncStepper(en_pin=13, step_pin=14, dir_pin=15, \
                        steps_per_sec=10000, invert_dir=True) as s:
        # s.free_run(1); await asyncio.sleep(10)  
        s.move_to(500)  
        while not s.target_reached: await asyncio.sleep(0.01)


if __name__ == '__main__': 
    asyncio.run(main())
    
# 1600 пульсов 1 оборот (18 шкифов на 1 оборот, примерно 18 мм)
    

