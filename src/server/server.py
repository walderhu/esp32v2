import socket
import json
import subprocess

# Словари для колбеков
PRESS_CALLBACKS = {}
RELEASE_CALLBACKS = {}

def run(command):
    cmd = [
        "python", "/home/des/WORK/src/tools/webrepl_cli.py",
        "-p", "1234",
        "192.168.0.92",
        "-e", command
    ]
    try: subprocess.Popen(cmd)
    except: print('Ошибка выполнения команды')

# Регистрация колбеков
def register_press(name, callback):
    PRESS_CALLBACKS[name.upper()] = callback

def register_release(name, callback):
    RELEASE_CALLBACKS[name.upper()] = callback

# Универсальные обработчики
def on_press(direction, value=None):
    dir_up = direction.upper()
    print(f"▶ Нажата кнопка/поле: {dir_up}", "Value:" if value is not None else "", value if value is not None else "")
    
    # Если есть колбек для нажатия — вызываем
    if dir_up in PRESS_CALLBACKS:
        if value is not None:
            PRESS_CALLBACKS[dir_up](value)
        else:
            PRESS_CALLBACKS[dir_up]()
        return

    # Старые стандартные кнопки
    match dir_up:
        case 'UP': command = "asyncio.run(motor1.move(distance_cm=5, freq=10_000))"
        case 'DOWN': command = "asyncio.run(motor1.move(distance_cm=-5, freq=10_000))"
        case 'RIGHT': command = "asyncio.run(motor2.move(distance_cm=5, freq=10_000))"
        case 'LEFT': command = "asyncio.run(motor2.move(distance_cm=-5, freq=10_000))"
        case 'HOME': command = "go_home()"
        case 'STOP': command = "go_stop()"
        case _: return
    run(command)

def on_release(direction):
    dir_up = direction.upper()
    print(f"◀ Отпущена кнопка: {dir_up}")

    # Если есть колбек для отпускания — вызываем
    if dir_up in RELEASE_CALLBACKS:
        RELEASE_CALLBACKS[dir_up]()
        return

    # Старые стандартные кнопки
    match dir_up:
        case 'UP'|'DOWN': command = "motor1.stop()"
        case 'LEFT'|'RIGHT': command = "motor2.stop()"
        case 'HOME'|'STOP': return
        case _: return
    run(command)

# --- Сервер ---
def serve():
    with open("index.html", "r", encoding="utf-8") as f:
        HTML = f.read()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    s.bind(("0.0.0.0", 8081))
    s.listen(1)
    print("Открой http://localhost:8081")
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
                    value = data.get('value', None)
                    if action == 'press': on_press(dir, value)
                    elif action == 'release': on_release(dir)
                except Exception as e: 
                    print("Ошибка JSON:", e)
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")
            elif req.startswith('GET /misc/'):
                path = req.split(' ', 2)[1][1:]
                try:
                    with open(path, 'rb') as f: content = f.read()
                    if path.endswith('.svg'): ctype = 'image/svg+xml'
                    elif path.endswith('.png'): ctype = 'image/png'
                    elif path.endswith('.jpg') or path.endswith('.jpeg'): ctype = 'image/jpeg'
                    else: ctype = 'application/octet-stream'
                    cl.send(f"HTTP/1.1 200 OK\r\nContent-Type: {ctype}\r\n\r\n".encode())
                    cl.sendall(content)
                except: cl.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
            elif req.startswith('GET /style.css'):
                try:
                    with open('style.css', 'rb') as f: css = f.read()
                    cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/css; charset=utf-8\r\n\r\n")
                    cl.sendall(css)
                except: cl.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
            else:
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n")
                cl.sendall(HTML.encode())
        except Exception as e:
            print("⚠️  Ошибка:", e)
        finally:
            cl.close()


if __name__ == "__main__":
    # Пример: регистрируем колбеки
    register_press("ZERO", lambda: print("Применить/Zero"))
    register_press("X", lambda v: print("X изменено:", v))
    register_press("Y", lambda v: print("Y изменено:", v))
    register_press("SPEED", lambda v: print("Скорость изменена:", v))
    register_press("STEPLENGTH", lambda v: print("Длина шага:", v))
    register_press("0.1", lambda: print("Scale 0.1"))
    register_press("1", lambda: print("Scale 1"))
    register_press("10", lambda: print("Scale 10"))
    register_press("25", lambda: print("Scale 25"))
    register_press("50", lambda: print("Scale 50"))
    register_press("100", lambda: print("Scale 100"))

    try:
        serve()
    except KeyboardInterrupt:
        pass
