from machine import Pin, PWM
import time

class StepperPWM:
    def __init__(self, step_pin=14, dir_pin=15, en_pin=13,
                 steps_per_rev=200, invert_dir=False, invert_enable=False):

        self.step_pwm = PWM(Pin(step_pin))
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.en_pin = Pin(en_pin, Pin.OUT) if en_pin is not None else None

        self.steps_per_rev = steps_per_rev
        self.invert_dir = invert_dir
        self.invert_enable = invert_enable
        self.lead_mm = 8  # мм/оборот

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
        self.enabled = state
        if self.en_pin:
            pin_state = (not state) if not self.invert_enable else state
            self.en_pin.value(pin_state)
        if not state:
            self.stop()

    def stop(self):
        self.step_pwm.duty_u16(0)
        self.running = False

    # ---------------------- Новая функция с ускорением ----------------------

    def run_ramp(self, direction=1, freq=1000, duration=3, ramp_time=0.5):
        """
        Запуск с плавным ускорением и замедлением.
        direction — 1 или 0
        freq — целевая частота шагов (Гц)
        duration — общее время движения (сек)
        ramp_time — время разгона и торможения (сек)
        """
        if not self.enabled:
            self.enable(True)

        if duration < 2 * ramp_time:
            ramp_time = duration / 2  # корректируем, чтобы не превышать duration

        self.dir_pin.value(direction ^ self.invert_dir)
        self.running = True

        # разгон
        start_time = time.ticks_ms()
        end_ramp = start_time + int(ramp_time * 1000)
        while time.ticks_ms() < end_ramp:
            t = (time.ticks_ms() - start_time) / 1000  # сек
            f = int(freq * (t / ramp_time))
            self.step_pwm.freq(max(f, 1))
            self.step_pwm.duty_u16(32768)
            time.sleep(0.01)

        # постоянная скорость
        steady_time = duration - 2 * ramp_time
        if steady_time > 0:
            self.step_pwm.freq(freq)
            self.step_pwm.duty_u16(32768)
            time.sleep(steady_time)

        # торможение
        start_brake = time.ticks_ms()
        end_brake = start_brake + int(ramp_time * 1000)
        while time.ticks_ms() < end_brake:
            t = (time.ticks_ms() - start_brake) / 1000
            f = int(freq * (1 - t / ramp_time))
            self.step_pwm.freq(max(f, 1))
            time.sleep(0.01)

        self.stop()

    # ---------------------- Остальные функции ----------------------

    def run(self, direction=1, freq=1000, duration=None):
        """Простой запуск без разгона"""
        if not self.enabled:
            self.enable(True)

        self.dir_pin.value(direction ^ self.invert_dir)
        self.step_pwm.freq(freq)
        self.step_pwm.duty_u16(32768)
        self.running = True

        if duration is not None:
            time.sleep(duration)
            self.stop()

    def move_mm(self, distance_mm, freq=1000, ramp_time=0.5):
        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        self.run_ramp(direction=direction, freq=freq, duration=duration, ramp_time=ramp_time)




motor = StepperPWM(step_pin=14, dir_pin=15, en_pin=13)
motor.enable(True)
motor.move_mm(8, freq=5000, ramp_time=0.5)
time.sleep(1)
motor.move_mm(-8, freq=5000, ramp_time=0.5)
