# main.py 
import network, time, wss_repl, urequests 
import ujson as json


def send_telegram(message, token, chat_id):
    token, chat_id = config['telegram'].values()
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    urequests.get(url).close()


def connect_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    if not sta.isconnected():
        print('Connecting to WiFi...')
        sta.active(True); sta.connect(ssid, password)
        t = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t) < 10000:
            if sta.isconnected(): break
        else: print('Error: Could not connect to WiFi!')

def main():
    with open("config.json") as f: config = json.load(f)
    connect_wifi(*config['wifi_home'].values())
    lnk = wss_repl.start()
    send_telegram(lnk, *config['telegram'].values())
