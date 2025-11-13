from machine import Pin, PWM, Timer
import time, math
from array import array

class Button:
    def __init__(self, pin_num): self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
    def is_pressed(self): return self.pin.value() == 0  


class Stepper:
    def __init__(self, step_pin, dir_pin, en_pin, sw_pin,
                 steps_per_rev=200, microstep=16, pulley_teeth=20, tooth_pitch=2,
                 invert_enable=False, limit_coord_cm=None, freq=12_000,
                 angle_mode=False, angle_per_rev=None):
        """
        angle_mode=True → управление в градусах
        angle_per_rev → сколько градусов на оборот (например, 18° для 20:1)
        """
        self.step_pin = Pin(step_pin, Pin.OUT)
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.en_pin = Pin(en_pin, Pin.OUT) if en_pin is not None else None
        self.button = Button(sw_pin)

        self.steps_per_rev = steps_per_rev
        self.microstep = microstep
        self.steps_per_rev_total = steps_per_rev * microstep

        self.pulley_teeth = pulley_teeth
        self.tooth_pitch = tooth_pitch
        self.mm_per_rev = pulley_teeth * tooth_pitch
        self.steps_per_mm = self.steps_per_rev_total / self.mm_per_rev
        self.invert_enable = invert_enable
        self.limit_coord_cm = limit_coord_cm

        self.angle_mode = angle_mode
        self.angle_per_rev = angle_per_rev or 360  # по умолчанию 360°
        self.steps_per_deg = self.steps_per_rev_total / self.angle_per_rev if angle_mode else None

        self.enabled = False
        self.current_coord = 0  # в мм или градусах
        self.enable(False)
        self.freq = freq

    def enable(self, state=True):
        self.enabled = state
        if self.en_pin:
            pin_state = (not state) if not self.invert_enable else state
            self.en_pin.value(pin_state)

    def home(self, freq=None, direction=0, debounce_ms=100):
        if freq is None: freq = self.freq
        delay_us = int(1e6 / (2 * freq))
        if not self.enabled: self.enable(True)
        self.dir_pin.value(direction)
        while not self.button.is_pressed():
            self.step_pin.on(); time.sleep_us(delay_us)
            self.step_pin.off(); time.sleep_us(delay_us)
        time.sleep_ms(debounce_ms)
        self.current_coord = 0

    def _move_accel(self, distance, max_freq=None, min_freq=5000, accel_ratio=0.15, accel_grain=10):
        if max_freq is None: max_freq = self.freq
        direction = distance > 0; self.dir_pin.value(direction)
        if self.limit_coord_cm is not None:
            if not (0 <= (self.current_coord + distance) <= self.limit_coord_cm):
                raise ValueError('Выход за границы')
        steps_total = int(abs(distance) * (self.steps_per_deg if self.angle_mode else self.steps_per_mm) * 10)
        if steps_total == 0: return
        accel_steps = max(1, int(steps_total * accel_ratio))
        decel_steps = accel_steps
        cruise_steps = steps_total - accel_steps - decel_steps
        delay_us_list = array('H')
        for step in range(0, accel_steps, accel_grain):
            ratio = step / accel_steps
            freq = min_freq + (max_freq - min_freq) * ratio
            delay_us = int(1_000_000 / freq / 2)
            repeats = min(accel_grain, accel_steps - step)
            delay_us_list.extend([delay_us] * repeats)
        min_delay_us = int(1_000_000 / max_freq / 2)
        for delay_us in delay_us_list:
            self.step_pin.on(); time.sleep_us(delay_us)
            self.step_pin.off(); time.sleep_us(delay_us)
        for _ in range(cruise_steps):
            self.step_pin.on(); time.sleep_us(min_delay_us)
            self.step_pin.off(); time.sleep_us(min_delay_us)
        for delay_us in reversed(delay_us_list):
            self.step_pin.on(); time.sleep_us(delay_us)
            self.step_pin.off(); time.sleep_us(delay_us)
        self.current_coord += distance

    def move_to(self, target):
        move = target - self.current_coord
        self._move_accel(move)

    def __imatmul__(self, target):
        if target == 0: self.home()
        else: self.move_to(target)
        return self

    def __add__(self, delta): 
        self._move_accel(delta); return self

    def __sub__(self, delta): 
        self._move_accel(-delta); return self

    def __enter__(self): self.enable(True); return self
    def __exit__(self, *args): self.enable(False); return False

    @property
    def freq(self): return self._freq
    @freq.setter
    def freq(self, f): 
        if 0 <= f <= 50_000: self._freq = f
        else: raise ValueError('freq 0-50kHz')

    def __repr__(self): return f"{self.current_coord:.2f}"


class Servo:
    def __init__(self, pin_id, min_us=544.0, max_us=2500.0, min_deg=0.0, max_deg=180.0, freq=50, speed=180.0):
        self.pwm = PWM(Pin(pin_id))
        self.pwm.freq(freq)
        self.min_us = min_us
        self.max_us = max_us
        self.min_deg = min_deg
        self.max_deg = max_deg
        self.current_us = 0.0
        self._speed = speed
        self._slope = (self.max_us - self.min_us) / (self.max_deg - self.min_deg)
        self._min_step_delay = 1e-2

    @property
    def speed(self): return self._speed
    @speed.setter
    def speed(self, value): self._speed = min(360, max(1, value))

    @property
    def angle(self): return (self.current_us - self.min_us) / self._slope + self.min_deg
    @angle.setter
    def angle(self, deg): self.move_to(deg)

    def write(self, deg):
        deg = max(self.min_deg, min(self.max_deg, deg))
        us = self.min_us + (deg - self.min_deg) * self._slope
        self.current_us = us
        self.pwm.duty_ns(int(us * 1000))

    def off(self): self.pwm.duty_ns(0)

    def move_to(self, deg):
        start_deg = self.angle
        deg = max(self.min_deg, min(self.max_deg, deg))
        delta = deg - start_deg
        if delta == 0: return
        duration = abs(delta) / self.speed
        steps = max(int(abs(delta)), 1)
        step_delay = max(duration / steps, self._min_step_delay)
        steps = int(abs(delta) / (self.speed * step_delay)) + 1
        step_delta = delta / steps
        angle = start_deg
        for _ in range(steps):
            angle += step_delta
            self.write(angle)
            time.sleep(step_delay)
        self.write(deg)

    def __imatmul__(self, deg): self.move_to(deg); return self
    def __enter__(self): return self
    def __exit__(self, *args): self.off(); time.sleep(0.1)



class Robohand:
    def __init__(self, m1: Stepper, m2: Stepper, m3: Stepper, mZ: Stepper, gripper_servo: Servo,
                 L1=225, L2=180, z_steps_per_mm=800,
                 max_speed=1000, accel=500):
        self.m1 = m1      # θ1 (Joint 1)
        self.m2 = m2      # θ2 (Joint 2)
        self.m3 = m3      # φ (Joint 3)
        self.mZ = mZ      # Z axis
        self.gripper = gripper_servo

        self.L1 = L1
        self.L2 = L2
        self.z_steps_per_mm = z_steps_per_mm

        self.max_speed = max_speed
        self.accel = accel

        self.positions = []
        self.current = {'x': 365, 'y': 0, 'z': 170, 'g': 90}

    def enable(self, state=True):
        m: Stepper
        for m in [self.m1, self.m2, self.m3, self.mZ]: m.enable(state)

    def home(self):
        print("Homing SCARA...")
        self.m1.home(direction=1); self.m1.current_coord = 90
        self.m2.home(direction=0); self.m2.current_coord = 0
        self.m3.home(direction=1); self.m3.current_coord = 90
        self.mZ.home(direction=0); self.mZ.current_coord = 0
        self.mZ += 170  # поднять на 170 мм
        self.current = {'x': 365, 'y': 0, 'z': 170, 'g': 90}
        print("Homed.")

    def forward_kinematics(self, t1, t2):
        rad1 = math.radians(t1)
        rad2 = math.radians(t2)
        x = self.L1 * math.cos(rad1) + self.L2 * math.cos(rad1 + rad2)
        y = self.L1 * math.sin(rad1) + self.L2 * math.sin(rad1 + rad2)
        return round(x), round(y)

    def inverse_kinematics(self, x, y):
        c2 = (x*x + y*y - self.L1**2 - self.L2**2) / (2 * self.L1 * self.L2)
        if abs(c2) > 1: raise ValueError("Недостижимо")
        t2 = math.degrees(math.acos(c2))
        if x < 0 and y < 0: t2 = -t2
        t1 = math.degrees(math.atan2(y, x) - math.atan2(self.L2*math.sin(math.radians(t2)),
                                                       self.L1 + self.L2*math.cos(math.radians(t2))))
        if x >= 0 and y >= 0: t1 = 90 - t1
        elif x < 0 and y > 0: t1 = 90 - t1
        elif x < 0 and y < 0: t1 = 270 - t1
        elif x > 0 and y < 0: t1 = -90 - t1
        phi = 90 + t1 + t2
        if abs(phi) > 165: phi = 180 + phi
        return round(t1), round(-t2), round(phi)

    def move_to_xyz(self, x, y, z):
        t1, t2, phi = self.inverse_kinematics(x, y)
        self.m1 @= t1
        self.m2 @= t2
        self.m3 @= phi
        self.mZ @= z
        self.current['x'], self.current['y'], self.current['z'] = x, y, z

    @property
    def coord(self):
        return (self.current['x'], self.current['y'], self.current['z'])

    @coord.setter
    def coord(self, xyz):
        x, y, z = xyz
        self.move_to_xyz(x, y, z)

    @property
    def gripper_angle(self): return self.gripper.angle
    @gripper_angle.setter
    def gripper_angle(self, deg): self.gripper @= deg; self.current['g'] = deg

    def save(self):
        self.positions.append(self.current.copy())
        print(f"Saved position {len(self.positions)}")

    def run(self, delay=0.5):
        for pos in self.positions:
            self.coord = (pos['x'], pos['y'], pos['z'])
            self.gripper_angle = pos['g']
            time.sleep(delay)

    def __enter__(self): self.enable(True); return self
    def __exit__(self, *args): self.enable(False); return False



def test():
    # Пины: step, dir, en, sw
    m1 = Stepper(16, 4, 2, 33, angle_mode=True, angle_per_rev=18)     
    m2 = Stepper(14, 15, 13, 27, angle_mode=True, angle_per_rev=22.5) 
    m3 = Stepper(12, 26, 25, 35, angle_mode=True, angle_per_rev=90)   
    mZ = Stepper(5, 18, 19, 32, limit_coord_cm=40)                    
    grip = Servo(13)

    r = Robohand(m1, m2, m3, mZ, grip)

    with r:
        r.home()
        r.coord = (300, 100, 100)
        r.gripper_angle = 0
        time.sleep(1)
        r.save()
        r.coord = (365, 0, 170)
        r.gripper_angle = 90
        r.save()
        r.run()
        
        
        
