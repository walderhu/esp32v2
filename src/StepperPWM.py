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

        self.enabled = False
        self.running = False
        self.current_dir = 1
        self.freq = 0

        # PWM начально выключен
        self.step_pwm.duty_u16(0)
        self.step_pwm.freq(1000)  # дефолт
        self.enable(False)

        self.lead_mm = 8  # например винт T8 8 мм/об

    # ---------------------- Управление ----------------------

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
        self.step_pwm.duty_u16(0)
        self.running = False

    def run(self, direction=1, freq=1000, duration=None):
        """
        Запустить вращение двигателя.
        direction — 1 или 0
        freq — частота шагов (Гц)
        duration — время вращения (сек) или None для непрерывного вращения
        """
        if not self.enabled:
            self.enable(True)

        self.dir_pin.value(direction ^ self.invert_dir)
        self.step_pwm.freq(freq)
        self.step_pwm.duty_u16(32768)  # 50% duty cycle
        self.running = True
        self.current_dir = direction
        self.freq = freq

        if duration is not None:
            time.sleep(duration)
            self.stop()

    def run_deg(self, deg, speed_hz):
        """
        Прокрутить на заданный угол (в градусах)
        speed_hz — частота шагов
        """
        steps = int(self.steps_per_rev * deg / 360.0)
        duration = abs(steps / speed_hz)
        direction = 1 if steps > 0 else 0
        self.run(direction=direction, freq=abs(speed_hz), duration=duration)

    def run_rev(self, revs, speed_hz):
        """Повернуться на заданное количество оборотов"""
        deg = revs * 360.0
        self.run_deg(deg, speed_hz)

    # ---------------------- Утилиты ----------------------

    def set_speed_rps(self, rps):
        """Настроить частоту вращения по оборотам в секунду"""
        self.freq = rps * self.steps_per_rev
        if self.running:
            self.step_pwm.freq(int(self.freq))

    def is_running(self): return self.running
    def is_enabled(self): return self.enabled

    # ---------------------- Контекстный менеджер ----------------------

    def __enter__(self):
        self.enable(True)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type: raise self.StepperEngineError(str(exc))
        finally:
            self.stop()
            self.enable(False)

    class StepperEngineError(Exception):
        def __init__(self, message): super().__init__(message)
        
        
        





    def move_mm(self, distance_mm, freq=1000):
        """
        Переместить мотор на заданное расстояние в миллиметрах
        distance_mm — положительное или отрицательное расстояние
        freq — частота шагов (Гц)
        """
        if not hasattr(self, 'lead_mm'):
            raise ValueError("Не задан параметр lead_mm (ход винта/ремня за оборот)")

        direction = 1 if distance_mm > 0 else 0
        steps_needed = abs(distance_mm) * self.steps_per_rev / self.lead_mm
        duration = steps_needed / freq
        self.run(direction=direction, freq=freq, duration=duration)






import time

with StepperPWM(step_pin=14, dir_pin=15, en_pin=13) as motor:
    print("Едем вперёд 2 секунды...")
    motor.run(direction=1, freq=5000, duration=2)

    print("Пауза..."); time.sleep(1)
    
    print("Едем назад...")
    motor.run(direction=0, freq=5000, duration=2)

