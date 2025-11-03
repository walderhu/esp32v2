import time
import machine
import urequests 
import network

def blink(led=machine.Pin(2, machine.Pin.OUT), d=0.05, f=0.05, n=3):
    for _ in range(n): led.on(); time.sleep(f); led.off(); time.sleep(d)

def connect_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("Connecting to WiFi...")
        sta.connect(ssid, password)
        t_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t_start) < 30_000:  # 30 секунд таймаут
            if sta.isconnected():
                ip = sta.ifconfig()[0]
                print("Connected, IP:", ip)
                return ip
            time.sleep_ms(500)
        raise Exception("WiFi connect failed")
    else:
        ip = sta.ifconfig()[0]
        print("Already connected, IP:", ip)
        return ip

def send_telegram(message):
    token = "8169199071:AAFqyr5RA3V1yEdYVNsdIk4C9b6OF8bPUuE"; chat_id = "683190449"
    try: urequests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}").close()
    except Exception as e: print("Failed to send Telegram message:", e)

def master():
    uart = machine.UART(2, baudrate=115200, tx=machine.Pin(17), rx=machine.Pin(16))
    button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
    print(f"Master mode started. Press button for send UART messages")
    while True:
        if button.value() == 0:
            uart.write('Hello!\n'); print("Sent Hello!")
            blink(n=1)
            while button.value() == 0: time.sleep_ms(50)
        time.sleep_ms(50)
    
def slave():
    uart = machine.UART(2, baudrate=115200, tx=machine.Pin(16), rx=machine.Pin(17))
    print("Slave mode started. Waiting for UART messages...")
    while True:
        if uart.any():
            data = uart.readline()
            print("\nGot:", data)
            # send_telegram(f"Got: {data}")
            blink()
    
    
def main():
    connect_wifi("Home 11", "HDMJ1890"); blink()
    master()
    # slave()

try: main()
except Exception as e: print("Fatal error:", e)
