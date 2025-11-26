from machine import Pin
import onewire, ds18x20
import time

class PID:
    def __init__(self, kp, ki, kd, setpoint=0, output_limits=(0, 100)):
        self.kp = kp; self.ki = ki; self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.integral = 0
        self.last_error = None

    def compute(self, value, dt):
        error = self.setpoint - value
        # P
        p = self.kp * error
        # I
        self.integral += error * dt
        i = self.ki * self.integral
        # D
        if self.last_error is None: d = 0
        else: d = self.kd * (error - self.last_error) / dt
        self.last_error = error
        output = p + i + d
        # ограничим выход 0..100%
        low, high = self.output_limits
        if output < low: output = low
        if output > high: output = high
        return output


class HeatingSystem:
    def __init__(self, sensor_pin, heater_pin, target_temp=40, 
                 kp=1.5, ki=0.3, kd=2.0, pwm_period=2.0):
        self.pid = PID(kp, ki, kd, setpoint=target_temp)
        # --- железо ---
        self.sensor_pin = Pin(sensor_pin)
        self.heater = Pin(heater_pin, Pin.OUT)
        self.pwm_period = pwm_period
        # --- датчик ---
        ow = onewire.OneWire(self.sensor_pin)
        self.ds = ds18x20.DS18X20(ow)
        roms = self.ds.scan()
        if not roms:
            raise Exception("DS18B20 not found!")
        self.rom = roms[0]

        self.last_time = time.ticks_ms() # время
        self.running = False # статус

    def set_target(self, temp):
        self.pid.setpoint = temp

    def set_pid(self, kp, ki, kd):
        self.pid.kp = kp
        self.pid.ki = ki
        self.pid.kd = kd

    def get_temp(self):
        """Просто чтение температуры"""
        self.ds.convert_temp()
        time.sleep_ms(500)
        return self.ds.read_temp(self.rom)

    def start(self):
        """Запускает основной цикл регулирования"""
        self.running = True
        self._loop()

    def stop(self):
        self.running = False
        self.heater.off()

    def _loop(self):
        """Внутренний цикл PID + PWM"""
        while self.running:
            try:
                self.ds.convert_temp()
                time.sleep_ms(500)
                temp = self.ds.read_temp(self.rom)

                now = time.ticks_ms()
                dt = time.ticks_diff(now, self.last_time) / 1000
                self.last_time = now

                power = self.pid.compute(temp, dt)
                print(f"Temp={temp:.2f}°C  Power={power:.1f}%")

                on_time = self.pwm_period * (power / 100)
                off_time = self.pwm_period - on_time

                if on_time > 0:
                    self.heater.on()
                    time.sleep(on_time)
                if off_time > 0:
                    self.heater.off()
                    time.sleep(off_time)

            except Exception:
                self.heater.off()

    @property
    def temp(self): return self.get_temp()
    
    @temp.setter
    def temp(self, new_temp):
        if 0 <= new_temp <= 120: self.set_target(new_temp)
        else: raise ValueError('Неккоректное значение, дб 0 ≤ temp ≤ 120')
        

def main():
    system = HeatingSystem(sensor_pin=13, heater_pin=15)
    system.set_pid(kp=2.0, ki=0.4, kd=1.3)
    system.temp = 42
    system.start()

main()