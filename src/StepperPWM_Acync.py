from machine import Pin, PWM
import uasyncio as asyncio

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

        # PWM изначально выключен
        self.step_pwm.duty_u16(0)
        self.step_pwm.freq(1000)
        self.enable(False)

    # ---------------------- Управление ----------------------

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

    async def run_async(self, direction=1, freq=1000, duration=None):
        """
        Асинхронное вращение двигателя
        direction — 1 или 0
        freq — частота шагов (Гц)
        duration — время вращения (сек) или None для непрерывного вращения
        """
        if not self.enabled:
            self.enable(True)

        self.dir_pin.value(direction ^ self.invert_dir)
        self.step_pwm.freq(freq)
        self.step_pwm.duty_u16(32768)  # 50% duty
        self.running = True
        self.current_dir = direction
        self.freq = freq

        if duration is not None:
            await asyncio.sleep(duration)
            self.stop()

    async def run_deg_async(self, deg, speed_hz):
        """Асинхронное вращение на угол (градусы)"""
        steps = int(self.steps_per_rev * deg / 360.0)
        duration = abs(steps / speed_hz)
        direction = 1 if steps > 0 else 0
        await self.run_async(direction=direction, freq=abs(speed_hz), duration=duration)

    async def run_rev_async(self, revs, speed_hz):
        """Асинхронное вращение на обороты"""
        deg = revs * 360.0
        await self.run_deg_async(deg, speed_hz)

    async def move_mm_async(self, distance_mm, freq=1000):
        """Асинхронное перемещение на мм"""
        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        await self.run_async(direction=direction, freq=freq, duration=duration)

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


# ---------------------- Пример использования ----------------------
import uasyncio as asyncio

async def main():
    async with StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13) as motor:
        print("Едем вперёд 2 секунды...")
        await motor.run_async(direction=1, freq=5000, duration=2)

        print("Пауза...")
        await asyncio.sleep(1)

        print("Едем назад...")
        await motor.run_async(direction=0, freq=5000, duration=2)

asyncio.run(main())
