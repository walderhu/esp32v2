# main.py 
import network, time, wss_repl, urequests 

WIFI_SSID='letai_B359'; WIFI_PASS='Uui84KLq'
TOKEN = "8169199071:AAFqyr5RA3V1yEdYVNsdIk4C9b6OF8bPUuE"; CHAT_ID = "683190449"
REPL_PASS='1234'

sta = network.WLAN(network.STA_IF)
if not sta.isconnected():
    print('Connecting to WiFi...')
    sta.active(True); sta.connect(WIFI_SSID, WIFI_PASS)
    t = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t) < 10000:
        if sta.isconnected(): break
    else: print('Error: Could not connect to WiFi!')

lnk = wss_repl.start()
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={lnk}"
urequests.get(url).close()
