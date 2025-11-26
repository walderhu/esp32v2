from machine import Pin, PWM, Timer
import time, math
from array import array
from modules.test2 import Stepper
from modules.serva import Servo

class Button:
    def __init__(self, pin_num): self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
    def is_pressed(self): return self.pin.value() == 0  




def plan_steps(self, target):
    """Возвращает количество шагов и направление ДЛЯ синхронного движения."""
    distance = target - self.current_coord
    if distance == 0:
        return 0, 0
    direction = 1 if distance > 0 else 0
    self.dir_pin.value(direction)
    steps = int(abs(distance) * (self.steps_per_deg if self.angle_mode else self.steps_per_mm))
    return steps, direction
Stepper.plan_steps = plan_steps

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


    def move_sync_to_xyz(self, x, y, z):
        t1, t2, phi = self.inverse_kinematics(x, y)
        self.move_sync(t1, t2, phi, z)
        self.current['x'], self.current['y'], self.current['z'] = x, y, z


    def move_sync(self, t1, t2, phi, z, freq=8000):
        # Планируем шаги для каждой оси
        s1, _ = self.m1.plan_steps(t1)
        s2, _ = self.m2.plan_steps(t2)
        s3, _ = self.m3.plan_steps(phi)
        sZ, _ = self.mZ.plan_steps(z)

        steps = [s1, s2, s3, sZ]
        steppers = [self.m1, self.m2, self.m3, self.mZ]

        max_steps = max(steps)
        if max_steps == 0:
            return

        # период шага
        delay_us = int(1_000_000 / freq)

        # Дробные накопители
        acc = [0, 0, 0, 0]

        for i in range(max_steps):
            for idx, total in enumerate(steps):
                if total == 0:    # мотор не движется
                    continue

                # ждем, пока накопится ≥ 1
                acc[idx] += total / max_steps

                if acc[idx] >= 1:
                    steppers[idx].step_pin.on()
                    steppers[idx].step_pin.off()
                    acc[idx] -= 1

            time.sleep_us(delay_us)

        # Обновить координаты
        self.m1.current_coord = t1
        self.m2.current_coord = t2
        self.m3.current_coord = phi
        self.mZ.current_coord = z


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
        
        
# https://chatgpt.com/s/t_6927751e9dac8191bca72d315af86983