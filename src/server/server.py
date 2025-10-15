import socket
import json
import subprocess


def run(command):
    cmd = [
        "python", "/home/des/WORK/src/tools/webrepl_cli.py",
        "-p", "1234",
        "192.168.0.92",
        "-e", command
    ]
    try: subprocess.Popen(cmd)
    except: print('Ошибка выполнения команды')

    
    
def on_press(direction):
    dir_up = direction.upper()
    print(f"▶ Нажата кнопка: {dir_up}")
    match dir_up:
        case 'UP': command = "asyncio.run(motor1.move(distance_cm=5, freq=10_000))"
        case 'DOWN': command = "asyncio.run(motor1.move(distance_cm=-5, freq=10_000))"
        case 'RIGHT': command = "asyncio.run(motor2.move(distance_cm=5, freq=10_000))"
        case 'LEFT': command = "asyncio.run(motor2.move(distance_cm=-5, freq=10_000))"
        case 'HOME': command = "go_home()"
        case 'STOP': command = "go_stop()"
        case _: return  # если неизвестная кнопка — просто выходим
    run(command)


def on_release(direction):
    dir_up = direction.upper()
    print(f"◀ Отпущена кнопка: {dir_up}")
    match dir_up:
        case 'UP': command = "motor1.stop()"
        case 'DOWN': command = "motor1.stop()"
        case 'RIGHT': command = "motor2.stop()"
        case 'LEFT': command = "motor2.stop()"
        case 'HOME': return  # 🟢 ничего не делаем при отпускании HOME
        case 'STOP': return  # 🟢 ничего не делаем при отпускании HOME
        case _: return        # 🟢 неизвестная кнопка — выходим
    run(command)


def serve():
    with open("index.html", "r", encoding="utf-8") as f:
        HTML = f.read()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    s.bind(("0.0.0.0", 8081))
    s.listen(1)
    # print("Открой http://localhost:8081")
    print("Открой https://jazlynn-englacial-undoubtfully.ngrok-free.dev/")

    while True:
        cl, addr = s.accept()
        try:
            req = cl.recv(4096).decode(errors='ignore')
            if req.startswith('POST /press'):
                body = req.split('\r\n\r\n', 1)[-1]
                try:
                    data = json.loads(body)
                    dir = data.get('dir')
                    action = data.get('action')

                    if action == 'press': on_press(dir)
                    elif action == 'release': on_release(dir)
                except Exception as e: print("Ошибка JSON:", e)
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")
                
            elif req.startswith('GET /misc/home.svg'):
                try:
                    with open('misc/home.svg', 'rb') as f:
                        svg = f.read()
                    cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: image/svg+xml\r\n\r\n")
                    cl.sendall(svg)
                except Exception as e:
                    print("Ошибка SVG:", e)
                    cl.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
                
                
            elif req.startswith('GET /misc/stop.svg'):
                try:
                    with open('misc/stop.svg', 'rb') as f:
                        svg = f.read()
                    cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: image/svg+xml\r\n\r\n")
                    cl.sendall(svg)
                except Exception as e:
                    print("Ошибка SVG:", e)
                    cl.send(b"HTTP/1.1 404 Not Found\r\n\r\n")

            else:
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n")
                cl.sendall(HTML.encode())

        except Exception as e: print("⚠️  Ошибка:", e)
        finally: cl.close()

if __name__ == "__main__":
    try: serve()
    except KeyboardInterrupt: pass
