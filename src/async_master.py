import uasyncio as asyncio
import machine
import time

from machine import Pin, UART

def blink(led, d=0.05, f=0.05, n=3):
    for _ in range(n):
        led.on()
        time.sleep(f)
        led.off()
        time.sleep(d)

async def handle_button(uart, led, button):
    last_pressed = False
    while True:
        pressed = button.value() == 0
        if pressed and not last_pressed:
            uart.write(b'Hello!\n')
            print(f"Sent Hello!")
            led.on()
        elif not pressed and last_pressed:
            led.off()
        last_pressed = pressed
        await asyncio.sleep_ms(20)

async def handle_uart(uart):
    while True:
        if uart.any():
            data = uart.readline()
            if data:
                try:
                    msg = data.decode().strip()
                    print("Got:", msg)
                except UnicodeError:
                    print("Received non-UTF8 data")
        await asyncio.sleep_ms(20)

async def bundle(board, *, button_pin=0, led_pin=2):
    tx, rx = (16, 17) if board == 1 else (17, 16)
    uart = UART(2, baudrate=115200, tx=Pin(tx), rx=Pin(rx))
    button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
    led = Pin(led_pin, Pin.OUT)
    
    print(f"Master/Slave mode started on board {board}")
    
    await asyncio.gather(
        handle_button(uart, led, button),
        handle_uart(uart)
    )

# Пример использования:
import network

sta = network.WLAN(network.STA_IF)
if not sta.isconnected():
    sta.active(True)
    sta.connect("TP-Link_0D14", "24827089")
    t_start = time.ticks_ms()
    while not sta.isconnected() and time.ticks_diff(time.ticks_ms(), t_start) < 100000:
        time.sleep_ms(500)

net = sta.ifconfig()[0]
_board = 1 if net == '192.168.0.123' else 2

asyncio.run(bundle(board=_board))
