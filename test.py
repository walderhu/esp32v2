# http://192.168.0.248:8266/
import ujson
import network
import uasyncio as asyncio
from machine import Pin

async def blink(*, led=Pin(2, Pin.OUT), delay=0.05, flash=0.05, repeat=3):
    for _ in range(repeat):
        led.on(); await asyncio.sleep(flash)
        led.off(); await asyncio.sleep(delay)

async def connect_wifi():
    with open("config.json") as f: config = ujson.load(f)
    wlan = network.WLAN(network.STA_IF); wlan.active(True)
    ssid, password = config['wifi'].values()

    while True:
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            print("  Wi-Fi...", end='\r')
            await asyncio.sleep(0.5)  
        else:
            await blink(repeat=2)
            return wlan.ifconfig()[0]
        
async def status_log(delay=0.5):
    while True:
        for dots in range(4):
            print(f'Server works{"." * dots}\033[K', end='\r')
            await asyncio.sleep(delay)


async def main():
    await connect_wifi()
    print('Подключение установлено')
    await status_log()


# Запуск программы
try: asyncio.run(main())
except KeyboardInterrupt: print('Program interrupted')
