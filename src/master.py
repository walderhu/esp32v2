import time
import machine
import urequests 
import network
import os 
from machine import Pin

def delete_all(path="/"):
    except_ = ['boot.py', 'config.json', 'webrepl_cfg.py']
    # except_ = []
    for filename in os.listdir(path):
        filepath = path + filename
        try:
            if filename in except_: continue
            if 'stat' in dir(os):
                mode = os.stat(filepath)[0]
                if mode & 0x4000:
                    delete_all(filepath + "/")
                    os.rmdir(filepath)
                    print("Deleted directory:", filepath)
                else:
                    os.remove(filepath)
                    print("Deleted file:", filepath)
            else:
                os.remove(filepath)
                print("Deleted file:", filepath)
        except Exception as e:
            print("Error deleting", filepath, ":", e)
def blink(led=machine.Pin(2, machine.Pin.OUT), d=0.05, f=0.05, n=3):
    for _ in range(n): led.on(); time.sleep(f); led.off(); time.sleep(d)
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
def send_telegram(message):
    token = "8169199071:AAFqyr5RA3V1yEdYVNsdIk4C9b6OF8bPUuE"; chat_id = "683190449"
    try: urequests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}").close()
    except Exception as e: print("Failed to send Telegram message:", e)
def UART(board, *, button = Pin(0, Pin.IN, Pin.PULL_UP), led=Pin(2, Pin.OUT)): 
    tx, rx = (16, 17) if board == 1 else (17, 16) #
    uart = machine.UART(2, baudrate=115200, tx=Pin(tx), rx=Pin(rx))
    button_pressed = lambda: button.value() == 0
    print(f"Master/Slave mode started")
    while True:
        time.sleep_ms(50)
        
        if button_pressed(): # Master
            uart.write(b'Hello!\n')
            print(f"Sent Hello from {board} board")
            led.on()
            while button_pressed(): 
                time.sleep_ms(50)
            led.off() 
            
        if uart.any(): # Slave
            data = uart.readline()
            if data: 
                print("\nGot:", data.decode().strip())
                blink()


def I2C(*, button = Pin(0, Pin.IN, Pin.PULL_UP), led=Pin(2, Pin.OUT)): 
    i2c = machine.I2C(freq=400000)
    print(f"Master/Slave I2C mode started")
    try:
        while True:
            i2c.scan()
    
            if button.value() == 0: # button pressed
                pass
            
            i2c.writeto(42, b'123')
            i2c.readfrom(42, 4)
            i2c.readfrom_mem(42, 8, 3)
            i2c.writeto_mem(42, 2, b'\x10')
    
    
            time.sleep_ms(50)
    finally: i2c.deinit()        
    
    
sta = network.WLAN(network.STA_IF)
if not sta.isconnected(): connect_wifi("TP-Link_0D14", "24827089")
net = sta.ifconfig()[0]   
_board = 1 if net == '192.168.0.123' else 2
I2C()
