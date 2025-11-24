from machine import Pin, PWM
import time

class Vortex:
    def __init__(self, step_pin, dir_pin, enable_pin=None, freq=5000):
        self.step = PWM(Pin(step_pin))
        self.step.freq(freq)
        self.step.duty_u16(0)
        self.dir = Pin(dir_pin, Pin.OUT)

        if enable_pin is not None:
            self.enable = Pin(enable_pin, Pin.OUT)
            self.enable.value(0)    # 0 = ENABLE for A4988
        else: self.enable = None

        self.running = False
        self.speed = 0

    def set_direction(self, clockwise=True):
        """Устанавливает направление вращения"""
        self.dir.value(0 if clockwise else 1)

    def start(self, speed):
        """
        Запускает вращение
        speed: 0..65535 (duty)
        """
        if speed < 0: speed = 0
        if speed > 65535: speed = 65535

        self.speed = speed
        self.step.duty_u16(speed)
        self.running = True

    def stop(self):
        """Останавливает вращение"""
        self.step.duty_u16(0)
        self.running = False

    def ramp(self, target_speed, duration_ms=500):
        """
        Плавное изменение скорости
        (например для мягкого старта)
        """
        start = self.speed
        steps = 20
        delay = duration_ms / steps / 1000

        for i in range(steps):
            s = start + (target_speed - start) * (i / steps)
            self.step.duty_u16(int(s))
            time.sleep(delay)

        self.step.duty_u16(target_speed)
        self.speed = target_speed


def main():
    mix = Vortex(step_pin=16, dir_pin=17, enable_pin=18)
    mix.set_direction(clockwise=True)
    mix.ramp(target_speed=30000, duration_ms=1500)  # Плавный запуск
    time.sleep(3)
    mix.stop()
