# main.py 
import network, time, urequests 
import ujson as json
from lib.wss_repl import start as wss_start


def send_telegram(message, token, chat_id):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
        urequests.get(url).close()
        print("Telegram message sent!")
    except Exception as e:
        print("Failed to send Telegram message:", e)


def connect_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    if not sta.isconnected():
        print('Connecting to WiFi...')
        sta.active(True); sta.connect(ssid, password)
        t = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t) < 10000:
            if sta.isconnected(): break
        else: print('Error: Could not connect to WiFi!')

    ip = sta.ifconfig()[0]; port = 8266  
    print(f'Connected! WebREPL available at: ws://{ip}:{port}/')
    return f'{ip}:{port}/'





def main():
    with open("config.json") as f: config = json.load(f)
    local_link = connect_wifi(*config['wifi_home'].values())
    remote_link = wss_start()
    # msg = f'{local_link}\n{remote_link}'
    # send_telegram(msg, *config['telegram'].values())
