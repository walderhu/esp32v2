# boot.py
import time
import machine
import urequests 
import ujson as json
import network
# import lib.wss_repl as wss
import deploy_server


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
    print("Connected:", sta.ifconfig())
    return sta.ifconfig()[0]

def send_telegram(message, token, chat_id):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
        urequests.get(url).close()
        print("Telegram message sent!")
    except Exception as e:
        print("Failed to send Telegram message:", e)
        

def deploy():
    import deploy_server; deploy_server.start_deploy_server()
# import deploy_server; deploy_server.temp_start_deploy_server()
d = deploy

with open("config.json") as f: config = json.load(f)
ip = connect_wifi(*config['wifi_home'].values())
blink()
# import webrepl; webrepl.start()


# link = wss.start()  
# send_telegram(link, *config['telegram'].values())
# deploy_server.start_deploy_server() 

# import uasyncio as asyncio
# import deploy_server; asyncio.run(deploy_server.start_deploy_server())


# import test

# import utelnetserver; utelnetserver.start()


def dd(): import repl_server; repl_server.run()