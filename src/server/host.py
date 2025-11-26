import socket

HOST = '192.168.0.123'  # IP ESP32
PORT = 5421              # порт TCP сервера

def send_command(cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(cmd.encode())
        data = s.recv(1024)
        print('Received:', data.decode())

send_command("ON")   # Включить светодиод
send_command("OFF")  # Выключить светодиод
send_command("BLINK") # Отправка неизвестной команды
