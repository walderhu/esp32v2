import time
import machine
import network
import os 
from machine import Pin, I2C

def connect_wifi(ssid="TP-Link_0D14", password="24827089"):
    sta = network.WLAN(network.STA_IF); sta.active(True)
    if not sta.isconnected():
        print("Connecting to WiFi...")
        sta.connect(ssid, password)
        t_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t_start) < 1e5: 
            if sta.isconnected(): break
            time.sleep_ms(500)
        else: raise Exception("WiFi connect failed")
    return sta.ifconfig()[0]


class I2CBundle:
    def __init__(self, board, *, button=Pin(0, Pin.IN, Pin.PULL_UP), led=Pin(2, Pin.OUT), freq=400000):
        self.board = board
        self.button = button
        self.led = led
        self.addr = 0x42  # произвольный адрес устройства
        self.i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=freq)
        print(f"I2C bundle initialized on board {board}")
        print("Scanning I2C bus...")
        print("Found devices:", self.i2c.scan())

    def blink(self, d=0.05, f=0.05, n=3):
        for _ in range(n):
            self.led.on(); time.sleep(f)
            self.led.off(); time.sleep(d)

    def button_pressed(self):
        return self.button.value() == 0

    def master_mode(self):
        """Поведение платы как мастера"""
        try:
            while True:
                if self.button_pressed():
                    msg = b"Hello from master!"
                    try:
                        self.i2c.writeto(self.addr, msg)
                        print("Sent:", msg)
                        self.led.on()
                    except Exception as e: print("I2C write error:", e)
                    
                    while self.button_pressed(): time.sleep_ms(50)
                    self.led.off()
                time.sleep_ms(100)
        finally: self.i2c.deinit()

    def slave_mode(self):
        """Поведение платы как слейва (псевдо — MicroPython не поддерживает полноценный slave I2C)"""
        print("I2C slave emulation started")
        while True:
            try:
                data = self.i2c.readfrom(self.addr, 16)  # чтение с адреса
                if data:
                    print("Got:", data)
                    self.blink()
            except Exception as e: pass
            time.sleep_ms(200)

    def run(self):
        print("Master/Slave I2C mode started")
        if self.board == 1:
            print("Running as MASTER")
            self.master_mode()
        else:
            print("Running as SLAVE (emulated)")
            self.slave_mode()


sta = network.WLAN(network.STA_IF)
if not sta.isconnected():
    connect_wifi("TP-Link_0D14", "24827089")
net = sta.ifconfig()[0]
_board = 1 if net == '192.168.0.123' else 2

i2c_bundle = I2CBundle(_board)
i2c_bundle.run()
