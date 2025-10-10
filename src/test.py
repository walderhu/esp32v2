from machine import Pin, PWM
import uasyncio as asyncio
import time


class StepperPWMAsync:
    def __init__(self, step_pin=14, dir_pin=15, en_pin=13,
                 steps_per_rev=200, invert_dir=False, invert_enable=False, lead_mm=8,
                 sw_pin=27, max_travel_mm=None):
        """
        max_travel_mm — максимальный ход по оси, например 100 мм
        (если None — без ограничения)
        """
        self.step_pwm = PWM(Pin(step_pin))
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.en_pin = Pin(en_pin, Pin.OUT) if en_pin is not None else None
        self.sw_pin = Pin(sw_pin, Pin.IN, Pin.PULL_UP)

        self.steps_per_rev = steps_per_rev
        self.invert_dir = invert_dir
        self.invert_enable = invert_enable
        self.lead_mm = lead_mm

        # --- Состояние ---
        self.enabled = False
        self.running = False
        self.current_dir = 1
        self.freq = 0

        # --- Счётчик ---
        self.position_steps = 0  # 0 = концевик
        self.max_steps = int(max_travel_mm * steps_per_rev / lead_mm) if max_travel_mm else None

        # Настройка PWM
        self.step_pwm.duty_u16(0)
        self.step_pwm.freq(1000)
        self.enable(False)

    # ------------------- Управление питанием -------------------

    def enable(self, state=True):
        self.enabled = state
        if self.en_pin:
            pin_state = (not state) if not self.invert_enable else state
            self.en_pin.value(pin_state)
        if not state:
            self.stop()

    def stop(self):
        self.step_pwm.duty_u16(0)
        self.running = False

    # ------------------- Основное вращение -------------------

    async def run(self, direction=1, freq=1000, duration=None):
        """Асинхронное вращение с авторазворотом и концевиком"""
        if not self.enabled:
            self.enable(True)

        self.dir_pin.value(direction ^ self.invert_dir)
        self.step_pwm.freq(freq)
        self.step_pwm.duty_u16(32768)
        self.running = True
        self.current_dir = direction
        self.freq = freq

        start_time = time.ticks_ms()
        stop_time = None
        if duration:
            stop_time = time.ticks_add(start_time, int(duration * 1000))

        prev_sw_state = self.sw_pin.value()
        debounce_ms = 200
        step_interval_us = int(1_000_000 / freq)
        last_step_time = time.ticks_us()

        try:
            while self.running:
                # Концевик
                sw_state = self.sw_pin.value()
                if sw_state == 1 and prev_sw_state == 0:
                    print("⚠️ Концевик сработал — позиция = 0")
                    self.position_steps = 0
                    self.step_pwm.duty_u16(0)
                    await asyncio.sleep_ms(debounce_ms)
                    # Разворот
                    self.current_dir ^= 1
                    self.dir_pin.value(self.current_dir ^ self.invert_dir)
                    await asyncio.sleep_ms(100)
                    self.step_pwm.duty_u16(32768)

                prev_sw_state = sw_state

                # Обновляем позицию
                now = time.ticks_us()
                if time.ticks_diff(now, last_step_time) >= step_interval_us:
                    last_step_time = now
                    if self.current_dir:
                        self.position_steps += 1
                    else:
                        self.position_steps -= 1

                    # Проверка границ
                    if self.max_steps is not None:
                        if self.position_steps < 0:
                            self.position_steps = 0
                            print("🛑 Левая граница")
                            self.stop()
                        elif self.position_steps > self.max_steps:
                            self.position_steps = self.max_steps
                            print("🛑 Правая граница")
                            self.stop()

                # Проверка на время
                if stop_time and time.ticks_diff(time.ticks_ms(), stop_time) >= 0:
                    self.stop()
                    break

                await asyncio.sleep_ms(2)

        finally:
            self.step_pwm.duty_u16(0)
            self.running = False

    # ------------------- Движение по координате -------------------

    async def go_to(self, target_mm, freq=1000):
        """Перейти к целевой позиции в мм"""
        if self.max_steps is None:
            raise ValueError("⚠️ max_travel_mm не задан — ограничение невозможно.")

        target_steps = int(target_mm * self.steps_per_rev / self.lead_mm)
        target_steps = max(0, min(self.max_steps, target_steps))
        delta_steps = target_steps - self.position_steps

        if delta_steps == 0:
            print("ℹ️ Уже на позиции", target_mm, "мм")
            return

        direction = 1 if delta_steps > 0 else 0
        duration = abs(delta_steps) / freq
        print(f"➡️ Перемещение к {target_mm} мм ({delta_steps} шагов, {duration:.2f} сек)")
        await self.run(direction=direction, freq=freq, duration=duration)

    async def home(self, freq=1000):
        await self.run(direction=0, freq=freq, duration=None)

    # ------------------- Утилиты -------------------

    def pos_mm(self):
        return self.position_steps * self.lead_mm / self.steps_per_rev

    def is_running(self): return self.running
    def is_enabled(self): return self.enabled

    # ------------------- Контекстный менеджер -------------------

    async def __aenter__(self):
        self.enable(True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.stop()
        self.enable(False)
        if exc:
            raise exc


# ---------------------- Пример ----------------------

на_меня = 0
от_меня = 1

async def main():
    async with StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13, max_travel_mm=50) as motor:
        await motor.home(freq=1000)          # домой к концевику
        await asyncio.sleep(1)
        await motor.go_to(30, freq=3000)     # на 30 мм вперёд
        await asyncio.sleep(1)
        await motor.go_to(10, freq=2000)     # назад на 10 мм

asyncio.run(main())
