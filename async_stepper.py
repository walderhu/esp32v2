from machine import Pin
import uasyncio as asyncio
from tools import AsyncStepper



async def main():
    sr1 = AsyncStepper(en_pin=Pin(2, Pin.OUT, drive=Pin.DRIVE_3),
                       step_pin=Pin(16, Pin.OUT, drive=Pin.DRIVE_3),
                       dir_pin=Pin(4, Pin.OUT, drive=Pin.DRIVE_3),
                       steps_per_sec=5000, invert_enable=True)

    sr2 = AsyncStepper(en_pin=Pin(13, Pin.OUT, drive=Pin.DRIVE_3),
                       step_pin=Pin(14, Pin.OUT, drive=Pin.DRIVE_3),
                       dir_pin=Pin(15, Pin.OUT, drive=Pin.DRIVE_3),
                       steps_per_sec=5000, invert_enable=True)

    sr1.free_run(1)
    sr2.free_run(1)
    await asyncio.sleep(5)  
    sr1.stop_task()
    sr2.stop_task()

if __name__ == '__main__': asyncio.run(main())

# sr1.move_to(1000)
# while not sr1.target_reached: await asyncio.sleep(1 / sr1.steps_per_sec)
