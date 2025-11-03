import network, json, time
import socket

def connect_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    while not sta.isconnected():
        if not sta.isconnected():
            print("Connecting to WiFi...")
            sta.active(True)
            sta.connect(ssid, password)
            t_start = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), t_start) < 1e5:
                if sta.isconnected(): break
                time.sleep_ms(100)
            else: raise Exception("WiFi connect failed")
        else: return sta.ifconfig()[0]



with open("config.json") as f: config = json.load(f)
ip = connect_wifi(*config['wifi_work'].values())

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('Listening on', addr)

html = """<!DOCTYPE html>
<html>
    <head><title>ESP32</title></head>
    <body><h1>Hello ESP32!</h1></body>
</html>
"""

while True:
    cl, addr = s.accept()
    print('Client connected from', addr)
    request = cl.recv(1024)
    cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    cl.send(html)
    cl.close()
