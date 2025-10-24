import socket
import json
import subprocess



import subprocess

python = "/home/des/miniforge3/envs/esp/bin/python"
webrepl = "/home/des/WORK/src/tools/webrepl_cli.py"
port =  "-p 1234 192.168.0.92"
pro_run = f"{python} {webrepl} {port} -e"

def init():
    command = (
        "/home/des/miniforge3/envs/esp/bin/python "
        "/home/des/WORK/src/tools/webrepl_cli.py "
        "-p 1234 192.168.0.92 -e "
        "\"import test2; "
        "m2=test2.Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90); "
        "m1=test2.Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60); "
        "p = test2.Portal(m2, m1); "
        "p.enable(True);\""
    )
    subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def exec(command):
    command = f'{pro_run} "{command}"'
    subprocess.run(command, shell=True, check=True)




STEP = 5
X = 0
Y = 0









PRESS_CALLBACKS = {}
RELEASE_CALLBACKS = {}



def register_press(name, callback):
    PRESS_CALLBACKS[name.upper()] = callback

def register_release(name, callback):
    RELEASE_CALLBACKS[name.upper()] = callback

def on_press(direction, value=None):
    global STEP, Y, X
    dir_up = direction.upper()
    print(f"▶ Нажата кнопка/поле: {dir_up}", "Value:" if value is not None else "", value if value is not None else "")
    
    if dir_up in PRESS_CALLBACKS:
        if value is not None: PRESS_CALLBACKS[dir_up](value)
        else: PRESS_CALLBACKS[dir_up]()
        return
    
    if dir_up == 'XINPUT': X = float(value)
    if dir_up == 'YINPUT': Y = float(value)
    if dir_up == 'ZERO': exec(f'p.x @= {X}; p.y @= {Y}')

    match dir_up:
        case 'UP': command = f"p.y += {STEP}"
        case 'DOWN': command = f"p.y -= {STEP}"
        case 'RIGHT': command = f"p.x += {STEP}"
        case 'LEFT': command = f"p.x -= {STEP}"
        case 'HOME': command = "p.home()"
        case 'STOP': command = "go_stop()"
        case _: return
    exec(command)

# def on_release(direction):
#     dir_up = direction.upper()
#     print(f"◀ Отпущена кнопка: {dir_up}")

#     # Если есть колбек для отпускания — вызываем
#     if dir_up in RELEASE_CALLBACKS:
#         RELEASE_CALLBACKS[dir_up]()
#         return

#     # Старые стандартные кнопки
#     match dir_up:
#         case 'UP'|'DOWN': command = "motor1.stop()"
#         case 'LEFT'|'RIGHT': command = "motor2.stop()"
#         case 'HOME'|'STOP': return
#         case _: return
#     exec(command)

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
                    # elif action == 'release': on_release(dir)
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
    init()
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

    try: serve()
    except KeyboardInterrupt: pass
