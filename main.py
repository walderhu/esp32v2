"""
Пример для работы с шаговиком в синхронном режиме
"""
from machine import Pin
from tools import AsyncStepper
import uasyncio as asyncio


async def main():
    sw_pin = Pin(27, Pin.IN, Pin.PULL_UP)
    sr1 = AsyncStepper(en_pin=Pin(2, Pin.OUT, drive=Pin.DRIVE_3),
                       step_pin=Pin(16, Pin.OUT, drive=Pin.DRIVE_3),
                       dir_pin=Pin(4, Pin.OUT, drive=Pin.DRIVE_3),
                       steps_per_sec=5000, invert_enable=True)
    try:
        while True:
            await asyncio.sleep(1e-3)
            if sw_pin.value() == 0: sr1.step(1)
    finally: sr1.stop_task()


if __name__ == '__main__': asyncio.run(main())