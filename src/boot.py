import time
import machine
import urequests 
import uos as os
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
        
def rm(path):
    if not os.path.exists(path): return
    if os.path.isfile(path): os.remove(path)
    elif os.path.isdir(path):
        for name in os.listdir(path): rm(f'{path}/{name}')  
        os.rmdir(path)
def ls(): print(os.listdir())
def reset(): machine.reset()

with open("config.json") as f: config = json.load(f)
ip = connect_wifi(*config['wifi_work'].values())
webrepl.start()

blink()


# try: import main
# except: pass




# import lib.wss_repl
# lib.wss_repl.start()
