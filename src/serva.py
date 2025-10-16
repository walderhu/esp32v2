from machine import Pin, PWM
from time import sleep

class ServoController:
    def __init__(self, pin_num=13):
        self.pin_num = pin_num
        self.servo = None
        
    def init_servo(self):
        if self.servo is None:
            self.servo = PWM(Pin(self.pin_num), freq=50)
        return self.servo
    
    def set_angle(self, angle, min_duty=30, max_duty=130):
        self.init_servo()
        duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
        self.servo.duty(duty)
        print(f"angle={angle}, duty={duty}")
    
    def cleanup(self):
        if self.servo:
            self.servo.deinit()
            self.servo = None
        Pin(self.pin_num, Pin.OUT).value(0)


    def move_slowly(self, target_angle, duration=2.0, steps=50):
        """Плавное перемещение за указанное время"""
        current_angle = self.current_angle  
        step_delay = duration / steps
        angle_step = (target_angle - current_angle) / steps
        
        for i in range(steps):
            new_angle = current_angle + angle_step * (i + 1)
            self.set_angle(new_angle)
            sleep(step_delay)



servo_ctrl = ServoController()

# def _main():
#     while True:
#         servo_ctrl.set_angle(0); sleep(1)
#         servo_ctrl.set_angle(180); sleep(1)


def _main():
    while True:
        servo_ctrl.move_slowly(180, duration=3.0); sleep(1)
        servo_ctrl.move_slowly(0, duration=3.0); sleep(1)
        


def main():
    try: _main()
    except KeyboardInterrupt:
        print("Interrupted, disabling servo...")
        servo_ctrl.cleanup()

