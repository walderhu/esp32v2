import time
import machine
import urequests 
import ujson as json
import network
import webrepl

def blink(led=machine.Pin(2, machine.Pin.OUT), d=0.05, f=0.05, n=3):
    for _ in range(n): led.on(); time.sleep(f); led.off(); time.sleep(d)
    
def connect_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    if not sta.isconnected():
        print("Connecting to WiFi...")
        sta.active(True)
        sta.connect(ssid, password)
        t_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t_start) < 10000:
            if sta.isconnected():
                break
            time.sleep_ms(100)
        else:
            raise Exception("WiFi connect failed")
    return sta.ifconfig()[0]


def send_telegram(message):
    token, chat_id = config['telegram'].values()
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
        urequests.get(url).close()
        print("Telegram message sent!")
    except Exception as e:
        print("Failed to send Telegram message:", e)
        

import os
import shutil

def rm(path):
    """Удаляет файл или каталог рекурсивно с устройства."""
    if not os.path.exists(path):
        print(f"{path} не найден")
        return
    if os.path.isfile(path):
        os.remove(path)
        print(f"Файл {path} удалён")
    elif os.path.isdir(path):
        shutil.rmtree(path)
        print(f"Каталог {path} удалён")
        
def ls(): print(os.listdir())










with open("config.json") as f: config = json.load(f)
ip = connect_wifi(*config['wifi_work'].values())
blink()
webrepl.start()

try: import main
except: pass