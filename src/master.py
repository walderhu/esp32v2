import time
import machine
import urequests 
import network

def blink(led=machine.Pin(2, machine.Pin.OUT), d=0.05, f=0.05, n=3):
    for _ in range(n): led.on(); time.sleep(f); led.off(); time.sleep(d)

def connect_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("Connecting to WiFi...")
        sta.connect(ssid, password)
        t_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t_start) < 30_000:  # 30 секунд таймаут
            if sta.isconnected():
                ip = sta.ifconfig()[0]
                print("Connected, IP:", ip)
                return ip
            time.sleep_ms(500)
        raise Exception("WiFi connect failed")
    else:
        ip = sta.ifconfig()[0]
        print("Already connected, IP:", ip)
        return ip

def send_telegram(message, token, chat_id):
    try: urequests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}").close()
    except Exception as e: print("Failed to send Telegram message:", e)

        
token = "8169199071:AAFqyr5RA3V1yEdYVNsdIk4C9b6OF8bPUuE"; chat_id = "683190449"
SSID = "Home 11"; PASSWORD = "HDMJ1890"


try:
    ip = connect_wifi(SSID, PASSWORD)
    send_telegram(f'Плата запущена!, {ip=}', token, chat_id)
    blink()
except Exception as e:
    print("Fatal error:", e)

import machine
uart = machine.UART(1, baudrate=115200, tx=machine.Pin(17), rx=machine.Pin(16))
# while True:
#     if uart.any():
#         data = uart.readline()
#         print("Got:", data)


