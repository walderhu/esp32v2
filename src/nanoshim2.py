from machine import Pin, PWM
import uasyncio as asyncio
import time
import math

class StepperPWMAsync:
    def __init__(self, step_pin, dir_pin, en_pin, sw_pin,
                 steps_per_rev=3200, invert_dir=False, invert_enable=False, 
                 lead_mm=8, limit_coord=None, pwm_channel=None):
        """
        Адаптировано для ESP32: pwm_channel (0-15) для назначения конкретного канала PWM.
        На ESP32 каналы 0-1 (timer0), 2-3 (timer1), ... 14-15 (timer7) — разные таймеры для независимых частот.
        Для 2 шаговиков: stepper1 с channel=0, stepper2 с channel=2 (разные таймеры).
        """
        self.pwm_channel = pwm_channel  # Опционально: канал для контроля таймера
        self.step_pwm = PWM(Pin(step_pin), freq=1000, duty=0, channel=self.pwm_channel)
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
        self.steps_count = 0  # Для точного трекинга

        self.step_pwm.duty(0)
        self.enable(False)
        self.current_coord = None  # В см

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
        self.step_pwm.duty(0)
        self.running = False

    def is_running(self):
        return self.running

    def is_enabled(self):
        return self.enabled

    async def __aenter__(self):
        self.enable(True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                raise exc_type(exc) from tb
        finally:
            self.enable(False)
            await asyncio.sleep(0.2)

    def deinit(self):
        self.step_pwm.deinit()

    async def home(self, freq=12_000, debounce_ms=150, start_event=None):
        """Возврат к концевику (нулевая позиция)"""
        if start_event:
            await start_event.wait()
        if not self.enabled:
            self.enable(True)
        if self.sw_pin.value() == 1:
            self.current_coord = 0
            return

        self.dir_pin.value(0 ^ self.invert_dir)
        self.step_pwm.freq(int(freq))
        self.step_pwm.duty(512)  # 50% duty (0-1023 на ESP32)
        self.running = True
        self.current_dir = 0
        self.freq = freq
        self.steps_count = 0
        try:
            while True:
                if self.sw_pin.value() == 1:
                    self.step_pwm.duty(0)
                    await asyncio.sleep_ms(debounce_ms)
                    break
                await asyncio.sleep_ms(2)
        finally:
            self.step_pwm.duty(0)
            self.running = False
            await asyncio.sleep(0.5)
            self.current_coord = 0
            self.steps_count = 0

    async def run(self, direction=1, freq=1000, duration=None, start_event=None):
        if not self.enabled:
            self.enable(True)
        self.current_dir = direction
        self.dir_pin.value(self.current_dir ^ self.invert_dir)
        self.step_pwm.freq(int(freq))
        if start_event:
            await start_event.wait()
        self.step_pwm.duty(512)  # 50% для импульсов
        self.running = True
        self.freq = freq
        self.steps_count = 0

        start_time = time.ticks_ms()
        stop_time = None
        if duration is not None:
            stop_time = time.ticks_add(start_time, int(duration * 1000))

        last_check = time.ticks_ms()
        expected_steps = 0.0

        try:
            while self.running:
                now = time.ticks_ms()
                delta_ms = time.ticks_diff(now, last_check)
                delta_s = delta_ms / 1000.0
                expected_steps += delta_s * freq
                new_steps = int(expected_steps)
                expected_steps -= new_steps

                # Обновляем позицию
                step_delta_cm = (new_steps * self.lead_mm / self.steps_per_rev) / 10
                self.current_coord += step_delta_cm if direction == 1 else -step_delta_cm

                last_check = now

                if self.sw_pin.value() == 1 and direction == 0:
                    self.current_coord = 0
                    self.stop()
                    break
                if stop_time and time.ticks_diff(now, stop_time) >= 0:
                    self.stop()
                    break
                if self.limit_coord is not None and self.current_coord >= self.limit_coord:
                    self.stop()
                    break

                await asyncio.sleep_ms(5)
        finally:
            self.stop()

    async def move_to(self, target_mm=None, target_cm=None, freq=1000, start_event=None):
        """Асинхронное перемещение до цели"""
        if target_mm is None:
            if target_cm is None:
                raise RuntimeError('Не передано сколько передвигаться')
            else:
                target_mm = target_cm * 10

        if self.current_coord is None:
            await self.home(freq=12_000)

        distance_mm = target_mm - self.current_coord * 10
        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        await self.run(direction=direction, freq=freq, duration=duration, start_event=start_event)
        
        
async def main():
    stepper1 = StepperPWMAsync(step_pin=2, dir_pin=4, en_pin=5, sw_pin=18,
                               steps_per_rev=3200, lead_mm=8, limit_coord=100.0, pwm_channel=0)
    stepper2 = StepperPWMAsync(step_pin=19, dir_pin=21, en_pin=22, sw_pin=23,
                               steps_per_rev=3200, lead_mm=8, limit_coord=50.0, pwm_channel=2)

    async with stepper1, stepper2:
        await asyncio.gather(
            stepper1.move_to(target_cm=10, freq=5000),  # Быстро, 5кГц
            stepper2.move_to(target_cm=-5, freq=2000)   # Медленнее, 2кГц
        )
    print("Готово: разные freq одновременно!")

asyncio.run(main())