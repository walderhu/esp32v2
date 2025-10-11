from machine import Pin, PWM
import uasyncio as asyncio
import math


class StepperPWMAsync:
    def __init__(self, step_pin=14, dir_pin=15, en_pin=13,
                 steps_per_rev=200, lead_mm=8,
                 invert_dir=False, invert_enable=False):
        """
        Асинхронный шаговый драйвер с управлением через PWM.
        Поддерживает несколько моторов одновременно (уникальные каналы PWM).
        """

        # создаем уникальный PWM-канал, чтобы избежать конфликтов
        self.step_pwm = PWM(Pin(step_pin))
        self.step_pwm.freq(999 + step_pin)  # уникальная частота
        self.step_pwm.duty_u16(0)

        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.en_pin = Pin(en_pin, Pin.OUT) if en_pin is not None else None

        self.steps_per_rev = steps_per_rev
        self.lead_mm = lead_mm
        self.invert_dir = invert_dir
        self.invert_enable = invert_enable

        self.enabled = False
        self.running = False
        self.current_dir = 1

        # начальное состояние
        self.enable(False)

    def enable(self, state=True):
        """Включить/выключить драйвер"""
        if self.en_pin:
            val = 0 if (state ^ self.invert_enable) else 1
            self.en_pin.value(val)
        self.enabled = state

    async def move_mm_accel_pwm(self, distance_mm=None, max_freq=20000,
                                min_freq=5000, accel_ratio=0.2, distance_cm=None):
        """
        Перемещение с плавным ускорением/торможением по косинусной кривой.
        Можно задать либо distance_mm, либо distance_cm.
        """

        # выбор единиц измерения
        if distance_mm is None and distance_cm is None:
            return
        if distance_mm is None:
            distance_mm = distance_cm * 10

        steps_total = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        steps_total = int(steps_total)

        direction = 1 if distance_mm > 0 else 0
        self.dir_pin.value(direction ^ self.invert_dir)

        self.enable(True)
        self.running = True

        accel_steps = int(steps_total * accel_ratio)
        decel_start = steps_total - accel_steps

        steps_done = 0
        duty = 32768  # 50% скважность

        while steps_done < steps_total and self.running:
            # косинусная зависимость ускорения/торможения
            if steps_done < accel_steps:  # ускорение
                ratio = steps_done / accel_steps
                freq = min_freq + (max_freq - min_freq) * (1 - math.cos(math.pi * ratio / 2))
            elif steps_done > decel_start:  # торможение
                ratio = (steps_total - steps_done) / accel_steps
                freq = min_freq + (max_freq - min_freq) * (1 - math.cos(math.pi * ratio / 2))
            else:
                freq = max_freq

            # установка частоты
            self.step_pwm.freq(int(freq))
            self.step_pwm.duty_u16(duty)

            # задержка по частоте (1 цикл = 1 шаг)
            delay = 1 / freq
            await asyncio.sleep(delay)

            steps_done += 1

        self.step_pwm.duty_u16(0)
        self.enable(False)
        self.running = False

    async def stop(self):
        """Аварийная остановка"""
        self.running = False
        self.step_pwm.duty_u16(0)
        self.enable(False)



import uasyncio as asyncio

motor1 = StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13)
motor2 = StepperPWMAsync(step_pin=16, dir_pin=4, en_pin=2)

async def main():
    await asyncio.gather(
        motor1.move_mm_accel_pwm(distance_cm=10),
        motor2.move_mm_accel_pwm(distance_cm=10)
    )

asyncio.run(main())
