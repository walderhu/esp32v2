from machine import Pin
import uasyncio as asyncio

class AsyncStepper:
    def __init__(self, step_pin, dir_pin, en_pin=None, steps_per_sec=200,
                 invert_dir=False, invert_enable=False):
        if not isinstance(step_pin, Pin): 
            step_pin = Pin(step_pin, Pin.OUT)
        if not isinstance(dir_pin, Pin): 
            dir_pin = Pin(dir_pin, Pin.OUT) 
        if en_pin and not isinstance(en_pin, Pin): 
            en_pin = Pin(en_pin, Pin.OUT)   
        self.step_pin, self.dir_pin, self.en_pin = step_pin, dir_pin, en_pin

        self.invert_dir = invert_dir
        self.invert_enable = invert_enable
        self.steps_per_sec = steps_per_sec

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



async def main():
    """async def main():
        sr1 = Stepper(en_pin=Pin(13, Pin.OUT, drive=Pin.DRIVE_3),
                        step_pin=Pin(14, Pin.OUT, drive=Pin.DRIVE_3),
                        dir_pin=Pin(15, Pin.OUT, drive=Pin.DRIVE_3),
                        steps_per_sec=200)
        sr2 = Stepper(en_pin=Pin(12, Pin.OUT, drive=Pin.DRIVE_3),
                        step_pin=Pin(16, Pin.OUT, drive=Pin.DRIVE_3),
                        dir_pin=Pin(17, Pin.OUT, drive=Pin.DRIVE_3),
                        steps_per_sec=200)
        
        sr1.move_to(100); sr2.move_to(50)
        while not sr1.target_reached or not sr2.target_reached: await asyncio.sleep_ms(10)
        sr1.free_run(1); sr2.free_run(-1)
        await asyncio.sleep(5)  
        sr1.stop_task(); sr2.stop_task()"""
    sr1 = AsyncStepper(en_pin=Pin(13, Pin.OUT, drive=Pin.DRIVE_3),
                       step_pin=Pin(14, Pin.OUT, drive=Pin.DRIVE_3),
                       dir_pin=Pin(15, Pin.OUT, drive=Pin.DRIVE_3),
                       steps_per_sec=5000, invert_enable=True)
    # sr1.move_to(1000)
    # while not sr1.target_reached: await asyncio.sleep(1 / sr1.steps_per_sec)
    sr1.free_run(1)
    await asyncio.sleep(1)  
    sr1.stop_task()

if __name__ == '__main__': asyncio.run(main())

