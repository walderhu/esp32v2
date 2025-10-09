import uasyncio as asyncio
from machine import Pin

class AsyncStepper:
    def __init__(self, step_pin, dir_pin, en_pin=None, steps_per_sec=200,
                 invert_dir=False, invert_enable=False, accel=1000, max_speed=None):
        if not isinstance(step_pin, Pin): 
            step_pin = Pin(step_pin, Pin.OUT)
        if not isinstance(dir_pin, Pin): 
            dir_pin = Pin(dir_pin, Pin.OUT) 
        if en_pin and not isinstance(en_pin, Pin): 
            en_pin = Pin(en_pin, Pin.OUT)   
        self.step_pin, self.dir_pin, self.en_pin = step_pin, dir_pin, en_pin

        self.invert_dir = invert_dir
        self.invert_enable = invert_enable
        self.steps_per_sec = steps_per_sec   # стартовая скорость
        self.target_speed = steps_per_sec    # к какой скорости идем
        self.max_speed = max_speed or steps_per_sec
        self.accel = accel                   # шагов/сек²

        self.current_speed = 0               # текущая скорость (шаг/сек)
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

    def free_run(self, direction, speed=None):
        self.free_run_mode = direction
        if speed:
            self.target_speed = min(abs(speed), self.max_speed)
        else:
            self.target_speed = self.steps_per_sec
        self.start_task()

    async def _run(self):
        try:
            while self.enabled and (self.free_run_mode != 0 or not self.target_reached):
                # разгон / торможение
                if self.current_speed < self.target_speed:
                    self.current_speed = min(self.current_speed + self.accel/ self.target_speed, self.target_speed)
                elif self.current_speed > self.target_speed:
                    self.current_speed = max(self.current_speed - self.accel/ self.target_speed, self.target_speed)

                if self.current_speed <= 0:
                    await asyncio.sleep(0)  # холостая итерация
                    continue

                # шаг
                if self.free_run_mode > 0:          self.step(1)
                elif self.free_run_mode < 0:        self.step(-1)
                elif self.target_pos > self.pos:    self.step(1)
                elif self.target_pos < self.pos:    self.step(-1)
                else: self.target_reached = True

                # задержка = 1 / скорость
                await asyncio.sleep(1 / self.current_speed)
        except asyncio.CancelledError: 
            pass
        finally:
            self._task = None

    def start_task(self):
        if self._task is None: 
            self._task = asyncio.create_task(self._run())

    def stop_task(self):
        if self._task:
            self._task.cancel()
            self._task = None
        self.free_run_mode = 0
        self.enable(False)


sr1 = AsyncStepper(en_pin=Pin(2, Pin.OUT, drive=Pin.DRIVE_3), step_pin=Pin(16, Pin.OUT, drive=Pin.DRIVE_3),
                    dir_pin=Pin(4, Pin.OUT, drive=Pin.DRIVE_3), steps_per_sec=5000, invert_enable=True)

async def main():
    sr1.free_run(1, speed=5000)
    await asyncio.sleep(5)
    sr1.target_speed = 500
    await asyncio.sleep(5)
    sr1.stop_task()


try: asyncio.run(main())
except KeyboardInterrupt: 
    print('Program interrupted')
    sr1.stop_task()
