import time
import machine


class Servo:
    def __init__(
        self,
        pin_id,
        min_us=544.0,
        max_us=2500.0,
        min_deg=0.0,
        max_deg=180.0,
        freq=50,
        speed=180.0,
    ):
        self.pwm = machine.PWM(machine.Pin(pin_id))
        self.pwm.freq(freq)
        self.min_us = min_us
        self.max_us = max_us
        self.min_deg = min_deg
        self.max_deg = max_deg
        self.current_us = 0.0
        self._speed = speed  # °/сек
        self._slope = (self.max_us - self.min_us) / (self.max_deg - self.min_deg)
        self._min_step_delay = 1e-2  # минимальный sleep в секундах (10 мс)

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = min(360, max(1, value))

    @property
    def angle(self):
        return (self.current_us - self.min_us) / self._slope + self.min_deg

    @angle.setter
    def angle(self, deg):
        self.move_to(deg)

    def write(self, deg):
        deg = max(self.min_deg, min(self.max_deg, deg))
        us = self.min_us + (deg - self.min_deg) * self._slope
        self.current_us = us
        self.pwm.duty_ns(int(us * 1000))

    def off(self):
        self.pwm.duty_ns(0)

    def move_to(self, deg):
        start_deg = self.angle
        deg = max(self.min_deg, min(self.max_deg, deg))
        delta = deg - start_deg
        if delta == 0:
            return

        duration = abs(delta) / self.speed
        steps = max(int(abs(delta)), 1)
        step_delta = delta / steps
        step_delay = max(duration / steps, self._min_step_delay)

        steps = int(abs(delta) / (self.speed * step_delay)) + 1
        step_delta = delta / steps

        angle = start_deg
        for _ in range(steps):
            angle += step_delta
            self.write(angle)
            time.sleep(step_delay)

        self.write(deg)  # убирает погрешность округлений
        # time.sleep(0.1)

    def move(self, start_deg, end_deg):
        self.move_to(start_deg)
        self.move_to(end_deg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.off()
        time.sleep(0.1)

    def __repr__(self):
        return f"Servo(us={self.current_us:.1f}, deg={self.angle:.1f}°, speed={self.speed}°/sec)"

    def __add__(self, angle):
        self.move_to(self.angle + angle)
        return self

    def __sub__(self, angle):
        self.move_to(self.angle - angle)
        return self

    def __imatmul__(self, deg):
        self.move_to(deg)
        return self

    def __ior__(self, deg):
        self.write(deg)
        return self

    def __ior__(self, deg, accel_ratio=0.15):
        return self.move_accel(deg=deg, accel_ratio=accel_ratio)
        
    def move_accel(self, deg, accel_ratio=0.05):
        start_deg = self.angle
        deg = max(self.min_deg, min(self.max_deg, deg))
        delta = deg - start_deg
        if delta == 0:
            return self
        total_steps = max(int(abs(delta)), 1)
        accel_steps = max(1, int(total_steps * accel_ratio))
        decel_start = total_steps - accel_steps

        angle = start_deg
        step_sign = 1 if delta > 0 else -1

        for step in range(total_steps):
            if step < accel_steps:
                ratio = step / accel_steps
                step_delay = max(
                    self._min_step_delay,
                    self._min_step_delay
                    + (1 / self.speed - self._min_step_delay) * (1 - ratio),
                )
            elif step >= decel_start:
                ratio = (total_steps - step) / accel_steps
                step_delay = max(
                    self._min_step_delay,
                    self._min_step_delay
                    + (1 / self.speed - self._min_step_delay) * (1 - ratio),
                )
            else:
                step_delay = 1 / self.speed

            angle += step_sign
            self.write(angle)
            time.sleep(step_delay)

        self.write(deg)
        return self


def main():
    with Servo(pin_id=13, speed=360) as servo:
        servo.angle = 0
        # servo.move(0, 180)
        # servo.move(180, 0)
        # servo += 180
        # servo -= 180
        # servo.move_to(90)

        while True:
            servo @= 0
            servo @= 180

        # servo.angle = 0
        # servo.angle = 180
        # servo.angle = 0
        # servo.angle = 180
        # servo.angle = 0
        # servo.angle = 180

        # servo.move_to(0)
        # while True:
        #     servo += 0.1
        #     time.sleep(0.0001)


if __name__ == "__main__":
    main()


"""
Возможные пины для сигнала сервы
GPIO 13
GPIO 15
GPIO 23
GPIO 16
GPIO 17
GPIO 18
GPIO 19
GPIO 14
GPIO 12
GPIO 2
GPIO 4
GPIO 5
"""
