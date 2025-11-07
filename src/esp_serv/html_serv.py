# ESP32 / WROOM micropython v1.26.1 (2025-09-11)
import network, time
import socket

def connect_wifi(ssid="TP-Link_0D14", password="24827089"):
    sta = network.WLAN(network.STA_IF); sta.active(True)
    if not sta.isconnected():
        print("Connecting to WiFi...")
        sta.connect(ssid, password)
        t_start = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), t_start) > 1e4: raise Exception("WiFi connect failed")
            time.sleep_ms(100)
    print("Wi-Fi connected:", sta.ifconfig())
    return sta.ifconfig()[0]

HTML = """<!DOCTYPE html>
<html>
    <head><title>ESP32</title></head>
    <body><h1>Hello ESP32!</h1></body>
</html>
""" # HTML = open("index.html").read()

def main():
    print(f"🌐 Web server running at: http://{connect_wifi()}/")
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket(); s.bind(addr); s.listen(1)
    print('Listening on', addr)
    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)
        try:
            request = cl.recv(1024)
            cl.send('HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nCache-Control: no-cache\r\n\r\n')
            cl.send(HTML)
        except Exception as e: print(f'Fatal error: {e}')
        finally: cl.close()

try: main()
except Exception as e: print("Fatal error:", e)
