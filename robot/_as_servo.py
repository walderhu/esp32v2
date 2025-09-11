import machine
from machine import Pin
import math
import uasyncio as asyncio

SERV_PIN = 13

class ServoEngine:
    def __init__(self, pin_id=SERV_PIN, min_us=544.0 ,max_us=2400.0,
                 min_deg=0.0, max_deg=180.0, freq=50):
        """
        :param pin_id: идентификатор pin-кода, подключенного к сервоприводу
        :param min_us: минимальная ширина импульса (минимальное время срабатывания в микросекундах)
        :param max_us: максимальная ширина импульса (максимальное время срабатывания в микросекундах)
        :param min_deg: минимальное положение в градусах 
        :param max_deg: максимальное положение в градусах
        :param freq: частота
        """
        self.pwm = machine.PWM(Pin(pin_id))
        self.pwm.freq(freq)
        self.current_us = 0.0
        self.min_deg = min_deg
        self.max_deg = max_deg
        self._slope = (min_us - max_us) / (math.radians(min_deg) - math.radians(max_deg))
        self._offset = min_us
        
    def set(self, deg):
        """
        Перемещение сервопривода на заданный угол
        :param deg: Положение в градусах
        """
        if not self.min_deg <= deg <= self.max_deg:
            raise ValueError("Угол вне допустимого диапазона")
        self._set_rad(math.radians(deg))

    def _set_rad(self, rad):
        """
        Перемемещение сервопривода в заданное положение по радианам
        :param rad: Положение в радианах
        """
        self._set_us(rad * self._slope + self._offset)
        
    def _set_us(self, us):
        """
        Установление ширины импульса для сервопривода 
        :param us: Длительность импульса в микросекундах
        """
        self.current_us = us
        val = int(self.current_us * 1000.0)
        self.pwm.duty_ns(val)
        
    def get(self):
        "Возвращает последнее установленное положение в градусах"
        return math.degrees(self._get_rad())
        
    def _get_rad(self):
        "Возвращает последнее установленное положение в радианах"
        return (self.current_us - self._offset) / self._slope
        
    def _get_us(self):
        "Возвращает последнюю заданную ширину импульса"
        return self.current_us

    def off(self):
        "Отключает серву"
        self.pwm.duty_ns(0)
        
    @property
    def angle(self):
        return self.get()
    
    def __iadd__(self, angle):
        new_angle = self.angle + angle
        self.set(new_angle)
        return self

    def __isub__(self, angle):
        new_angle = self.angle - angle
        self.set(new_angle)
        return self


async def main():
    delay = 1.5
    servo = ServoEngine()
    for deg in range(0, 181, 10):
        servo.set(deg)
        print(servo.angle)
        asyncio.sleep(delay)
        
    servo.set(0)
    for _ in range(30):
        servo += 5
        print(servo.angle)
        