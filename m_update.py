from machine import Pin
from utime import sleep_ms

class StepperEngineError(Exception):
    def __init__(self, message): super().__init__(message)

class StepperEngine:
    def __init__(self, step_pin=14, dir_pin=15, enable_pin=13):
        self.__step_pin = Pin(step_pin, Pin.OUT)
        self.__dir_pin = Pin(dir_pin, Pin.OUT)
        self.__enable_pin = Pin(enable_pin, Pin.OUT)
    
    def __aenter__(self):
        self.__enable_pin.value(0)
        return self

    def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type: raise StepperEngineError(exc_type)
        finally: self.__enable_pin.value(1)

    def step(self, direction=1, delay_ms=1):
        assert int(direction) in (0, 1), "Направление должно быть 0 или 1"
        self.__dir_pin.value(direction)
        self.__step_pin.value(1); sleep_ms(delay_ms)
        self.__step_pin.value(0); sleep_ms(delay_ms)
        
if __name__ == '__main__':
    with StepperEngine() as eng:
        while True: eng.step()

