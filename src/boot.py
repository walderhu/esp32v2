import time
import machine
import urequests 
import uos as os
import ujson as json
import network
import webrepl
import uasyncio as asyncio

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


def send_telegram(message, token, chat_id):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
        urequests.get(url).close()
        print("Telegram message sent!")
    except Exception as e:
        print("Failed to send Telegram message:", e)
        
        
def dd(message, token, chat_id, delay=5):
    try:
        url_send = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
        response = urequests.get(url_send)
        result = response.json()
        response.close()
        message_id = result["result"]["message_id"]
        print("Telegram message sent!")
        time.sleep(delay)
        url_delete = f"https://api.telegram.org/bot{token}/deleteMessage?chat_id={chat_id}&message_id={message_id}"
        urequests.get(url_delete).close()
        print("Telegram message deleted!")
    except Exception as e:
        print("Failed:", e)
        
def rm(path):
    if not os.path.exists(path): return
    if os.path.isfile(path): os.remove(path)
    elif os.path.isdir(path):
        for name in os.listdir(path): rm(f'{path}/{name}')  
        os.rmdir(path)
def ls(): print(os.listdir())
def reset(): machine.reset()


def tree(path='.', prefix=''):
    entries = sorted(os.listdir(path))
    entries_count = len(entries)
    for index, name in enumerate(entries):
        full_path = path + '/' + name
        connector = '└── ' if index == entries_count - 1 else '├── '
        print(prefix + connector + name)
        try:
            if os.stat(full_path)[0] & 0x4000:  # директория
                extension = '    ' if index == entries_count - 1 else '│   '
                tree(full_path, prefix + extension)
        except Exception: pass

with open("config.json") as f: config = json.load(f)
ip = connect_wifi(*config['wifi_work'].values())
# dd('Плата запущена!', *config['telegram'].values(), delay=0.5)
dd(f'Плата запущена!, {ip=}', *config['telegram'].values(), delay=0.5)
webrepl.start()
blink()



import os; os.mkdir('dir')


os.makedirs('dir', exist_ok=True)
