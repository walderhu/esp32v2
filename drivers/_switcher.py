from machine import Pin
import uasyncio as asyncio

SWITCH_PIN = 27
sw_pin = Pin(SWITCH_PIN, Pin.IN, Pin.PULL_UP)


async def switcher():
    while True:
        state = (sw_pin.value() == 0)
        status_msg = "ДА" if state else "НЕТ"
        print(status_msg, end='\r')
        await asyncio.sleep(0.1)


async def main():
    try:
        task = asyncio.create_task(switcher())  
        await task
    except Exception as e:
        log.exception(e, "")
        
        
if __name__ == '__main__':
    asyncio.run(main())