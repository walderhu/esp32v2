import network
import socket
from machine import UART, Pin

wlan = network.WLAN(network.STA_IF); wlan.active(True)
wlan.connect("TP-Link_0D14", "24827089")
while not wlan.isconnected(): pass
print("Connected, IP:", wlan.ifconfig()[0])
Pin(2, Pin.OUT).on()

uart = UART(1, tx=17, rx=16, baudrate=115200)
s = socket.socket()
s.bind(('0.0.0.0', 2217))
s.listen(1)

while True:
    conn, addr = s.accept()
    print("Client connected:", addr)
    while True:
        data = conn.recv(1024)
        if not data: break
        uart.write(data)
        out = uart.read()
        if out: conn.send(out)
    conn.close()



# mpremote connect rfc2217://192.168.0.232:2217
