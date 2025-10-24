import socket
import json
import subprocess

# --- Настройка WebREPL ---
python = "/home/des/miniforge3/envs/esp/bin/python"
webrepl = "/home/des/WORK/src/tools/webrepl_cli.py"
port = "-p 1234 192.168.0.92"
pro_run = f"{python} {webrepl} {port} -e"


def init():
    """Инициализация портала на ESP"""
    command = (
        f"{python} {webrepl} {port} -e "
        "\"import test2; "
        "m2=test2.Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90); "
        "m1=test2.Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60); "
        "m1.freq = 18_000; m2.freq = 18_000; "
        "p = test2.Portal(m2, m1); "
        "p.enable(True);\""
    )
    subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def exec(command):
    """Выполнить команду на ESP"""
    command = f'{pro_run} "{command}"'
    subprocess.run(command, shell=True, check=True)


# --- Глобальные переменные ---
STEP = 5
X = 0.0
Y = 0.0


# --- Колбеки ---
PRESS_CALLBACKS = {}
RELEASE_CALLBACKS = {}


def register_press(name, callback):
    PRESS_CALLBACKS[name.upper()] = callback


def register_release(name, callback):
    RELEASE_CALLBACKS[name.upper()] = callback


# --- Обработчик нажатий ---
def on_press(direction, value=None):
    global STEP, X, Y
    dir_up = direction.upper()
    print(f"▶ Нажата кнопка/поле: {dir_up}", "Value:" if value is not None else "", value if value is not None else "")

    # Обновляем X/Y из инпутов
    if dir_up == 'XINPUT':
        try:
            X = float(value)
            print(f"X обновлено: {X}")
        except Exception as e:
            print("Ошибка значения X:", e)
        return

    if dir_up == 'YINPUT':
        try:
            Y = float(value)
            print(f"Y обновлено: {Y}")
        except Exception as e:
            print("Ошибка значения Y:", e)
        return

    # При нажатии ZERO — отправляем координаты
    if dir_up == 'ZERO':
        print(f"📡 Перемещение к X={X}, Y={Y}")
        exec(f"p.x @= {X}; p.y @= {Y}")
        return

    # Если есть пользовательский колбек
    if dir_up in PRESS_CALLBACKS:
        if value is not None:
            PRESS_CALLBACKS[dir_up](value)
        else:
            PRESS_CALLBACKS[dir_up]()
        return

    # Управление порталами
    match dir_up:
        case 'UP': command = f"p.y += {STEP}"
        case 'DOWN': command = f"p.y -= {STEP}"
        case 'RIGHT': command = f"p.x += {STEP}"
        case 'LEFT': command = f"p.x -= {STEP}"
        case 'HOME': command = "p.home()"
        case 'STOP': command = "p.enable(False)"
        case _: return

    exec(command)


# --- HTTP сервер ---
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
                    if action == 'press':
                        on_press(dir, value)
                except Exception as e:
                    print("Ошибка JSON:", e)
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")
            elif req.startswith('GET /misc/'):
                path = req.split(' ', 2)[1][1:]
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                    if path.endswith('.svg'): ctype = 'image/svg+xml'
                    elif path.endswith('.png'): ctype = 'image/png'
                    elif path.endswith('.jpg') or path.endswith('.jpeg'): ctype = 'image/jpeg'
                    else: ctype = 'application/octet-stream'
                    cl.send(f"HTTP/1.1 200 OK\r\nContent-Type: {ctype}\r\n\r\n".encode())
                    cl.sendall(content)
                except:
                    cl.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
            elif req.startswith('GET /style.css'):
                try:
                    with open('style.css', 'rb') as f:
                        css = f.read()
                    cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/css; charset=utf-8\r\n\r\n")
                    cl.sendall(css)
                except:
                    cl.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
            else:
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n")
                cl.sendall(HTML.encode())
        except Exception as e:
            print("⚠️  Ошибка:", e)
        finally:
            cl.close()


# --- Запуск ---
if __name__ == "__main__":
    init()
    print("✅ ESP инициализирована. Ожидание команд...")

    register_press("SPEED", lambda v: exec(f"p.x.freq = {v}; p.y.freq = {v}"))
    register_press("STEPLENGTH", lambda v: print("Длина шага:", v))

    try: serve()
    except KeyboardInterrupt: pass
