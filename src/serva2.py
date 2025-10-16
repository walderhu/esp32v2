import time
import machine
import math

class Servo:
    def __init__(self, pin_id, min_us=544.0, max_us=2400.0,
                 min_deg=0.0, max_deg=180.0, freq=50, speed=180.0):
        self.pwm = machine.PWM(machine.Pin(pin_id))
        self.pwm.freq(freq)
        self.current_us = 0.0
        self.min_us = min_us
        self.max_us = max_us
        self.min_deg = min_deg
        self.max_deg = max_deg
        self._slope = (max_us - min_us) / (max_deg - min_deg)
        self._offset = min_us
        self._speed = speed  # °/sec

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = min(360, max(1, value))

    @property
    def angle(self):
        return self.read()

    @angle.setter
    def angle(self, angle):
        self.write(angle)

    def write(self, deg):
        deg = min(max(self.min_deg, deg), self.max_deg)
        us = self.min_us + (deg - self.min_deg) * self._slope
        self.write_us(us)

    def read(self):
        return (self.current_us - self.min_us) / self._slope + self.min_deg

    def write_us(self, us):
        self.current_us = us
        self.pwm.duty_ns(int(us * 1000))

    def off(self):
        self.pwm.duty_ns(0)

    def move_to(self, deg, duration=None, steps=50):
        start = self.angle
        deg = min(max(self.min_deg, deg), self.max_deg)
        delta = deg - start

        if duration is None:
            duration = abs(delta) / self.speed
        if steps < 1:
            steps = 1

        step_delay = duration / steps
        step_delta = delta / steps
        angle = start

        for _ in range(steps):
            angle += step_delta
            self.write(angle)
            time.sleep(step_delay)
        self.write(deg)
        time.sleep(0.1)

    def move(self, start_deg, end_deg, duration=None, steps=50):
        print(self.angle)
        self.move_to(start_deg)
        self.move_to(end_deg, duration=duration, steps=steps)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.off()
        time.sleep(0.1)

    def __repr__(self):
        return f"Servo(us={self.current_us:.1f}, deg={self.angle:.1f}°, speed={self.speed}°/sec)"

    # def __sub__(self, angle):
    #     self += -angle

    # def __add__(self, angle):
    #     res_angle = min(180, max(0, self.angle + angle))
    #     self.move_to(res_angle)
    #     return self



def main():
    with Servo(pin_id=13, speed=360) as servo:
        servo.move(0, 180)
        # servo.move(180, 0, duration=4, steps=100)
