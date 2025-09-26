import uasyncio as asyncio
import machine
from machine import Pin
# import logging
# import config

STEP_PIN = 14
DIR_PIN = 15
ENABLE_PIN = 13

# logging.basicConfig(level=logging.WARNING)
# log = logging.getLogger(__name__)

class StepperEngineError(Exception):
    """Базовые исключения для ошибок, связанных с шаговым двигателем."""
    def __init__(self, message):
        super().__init__(message)


class StepperEngine:
    def __init__(self, step_pin=STEP_PIN, dir_pin=DIR_PIN, enable_pin=ENABLE_PIN):
        """
        :param step_pin: Номер пина для шага.
        :param dir_pin: Номер пина для направления.
        :param enable_pin: Номер пина для включения/выключения.
        """
        self.__step_pin = Pin(step_pin, Pin.OUT)
        self.__dir_pin = Pin(dir_pin, Pin.OUT)
        self.__enable_pin = Pin(enable_pin, Pin.OUT)
    
    async def __aenter__(self):
        """Включение шагового двигателя"""
        self.__enable_pin.value(1)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Выключение шагового двигателя"""
        try:
            if exc_type: raise StepperEngineError(exc_type)
        finally: self.__enable_pin.value(0)


    async def step(self, direction=1, delay_ms=1):
        """
        Сделать один шаг в указанном направлении.
        :param direction: Направление (1 для вперед, 0 для назад).
        :param delay_ms: Задержка между шагами в миллисекундах.
        """
        assert int(direction) in (0, 1), "Направление должно быть 0 или 1"
        self.__dir_pin.value(direction)
        self.__step_pin.value(1)
        await asyncio.sleep_ms(delay_ms)
        self.__step_pin.value(0)
        await asyncio.sleep_ms(delay_ms)
        
    # async def move(self, steps, delay_ms=1):
    #     _dir = steps > 0
    #     steps = abs(steps)
    #     for _ in range(steps):
    #         await eng.step(direction=_dir)


async def main():
    # log.info("Start stepper engine")
    steps = 100
    try:
        async with StepperEngine() as eng:
            for _ in range(steps):
                await eng.step()
    except Exception as e: pass
        # log.warning(f"Error occurred: {e}")

async def main():
    steps = 100
    async with StepperEngine() as eng:
        eng.move(steps)

    