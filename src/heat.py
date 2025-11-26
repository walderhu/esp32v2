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





TARGET_TEMP = 40
sensor_pin = Pin(13)
heater = Pin(15, Pin.OUT)
# pid = PID(kp=4.0, ki=0.5, kd=1.5, setpoint=TARGET_TEMP)
pid = PID(kp=1.5, ki=0.3, kd=2, setpoint=TARGET_TEMP)
# kp = 2.5; ki = 0.5; kd = 1.2 # более бодрый 
# kp = 1; ki = 0.2; kd = 1.5 # супер мягкий долгий  

PWM_PERIOD = 2.0 
ow = onewire.OneWire(sensor_pin)
ds = ds18x20.DS18X20(ow)
roms = ds.scan()
if not roms: raise Exception("DS18B20 not found!")
rom = roms[0]; print("Sensor:", rom)
last_time = time.ticks_ms()

while True:
    try:
        ds.convert_temp()
        time.sleep_ms(500)
        temp = ds.read_temp(rom)
        now = time.ticks_ms()
        dt = (time.ticks_diff(now, last_time)) / 1000
        last_time = now
        power = pid.compute(temp, dt)
        print(f"\rTemp={temp:.2f}°C  Power={power:.1f}%", end="")
        on_time = PWM_PERIOD * (power / 100)
        off_time = PWM_PERIOD - on_time

        if on_time > 0:
            heater.on()
            time.sleep(on_time)
        if off_time > 0:
            heater.off()
            time.sleep(off_time)

    except (onewire.OneWireError, Exception):
        heater.off()



# https://chatgpt.com/s/t_69276c758e3c8191a4bfcd89ccc11ba3