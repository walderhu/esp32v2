# deploy_server.py
import socket
import os

PORT = 2323
BUFFER_SIZE = 1024


def remove_path(path):
    try:
        st = os.stat(path)
        if st[0] & 0x4000:  # S_IFDIR
            for entry in os.listdir(path):
                remove_path(path + "/" + entry)
            os.rmdir(path)
        else:
            os.remove(path)
    except OSError:
        pass
    
    
def handle_client(conn, addr):
    print("Connection from", addr)
    buf = b""
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            buf += data

            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.decode().strip()
                words = line.split()
                if not words:
                    conn.sendall(b"ERROR\n")
                    continue

                cmd = words[0]

                if cmd == "MKDIR":
                    if len(words) < 2:
                        conn.sendall(b"ERROR\n")
                        continue
                    dir_name = ' '.join(words[1:])
                    path = ""
                    for p in dir_name.split("/"):
                        path = path + "/" + p if path else p
                        try:
                            os.mkdir(path)
                        except OSError:
                            pass
                    conn.sendall(b"OK\n")

                elif cmd == "PUT":
                    if len(words) < 3:
                        conn.sendall(b"ERROR\n")
                        continue
                    fname = ' '.join(words[1:-1])  # всё кроме последнего как имя файла (на случай пробелов в пути)
                    try:
                        fsize = int(words[-1])
                    except ValueError:
                        conn.sendall(b"ERROR\n")
                        continue

                    # Создаём директории
                    path = ""
                    for p in fname.split("/")[:-1]:
                        path = path + "/" + p if path else p
                        try:
                            os.mkdir(path)
                        except OSError:
                            pass

                    # Читаем контент (остальное без изменений)
                    while len(buf) < fsize:
                        chunk = conn.recv(BUFFER_SIZE)
                        if not chunk:
                            break
                        buf += chunk
                    content, buf = buf[:fsize], buf[fsize:]

                    with open(fname, "wb") as f:
                        f.write(content)
                    conn.sendall(b"OK\n")

                elif cmd == "DEL":
                    if len(words) < 2:
                        conn.sendall(b"ERROR\n")
                        continue
                    fname = ' '.join(words[1:])
                    remove_path(fname)  
                    conn.sendall(b"OK\n")

                elif cmd == "LIST":
                    files = ",".join(os.listdir())
                    conn.sendall(files.encode() + b"\n")

                else:
                    conn.sendall(b"UNKNOWN\n")
    finally:
        conn.close()
        print("Connection closed")


# def start_deploy_server():
#     s = socket.socket()
#     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     s.bind(("0.0.0.0", PORT))
#     s.listen(5)
#     print(f"Deploy server listening on port {PORT}")

#     try:
#         while True:
#             try:
#                 conn, addr = s.accept()
#                 handle_client(conn, addr)
#             except KeyboardInterrupt:
#                 print("Server interrupted with Ctrl+C")
#                 break
#     except Exception as e: 
#         print("Server error:", e)
#     finally:
#         s.close()
#         print("Server stopped")






















# def start_deploy_server():
#     s = socket.socket()
#     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     s.bind(("0.0.0.0", PORT))
#     s.listen(5)
#     print(f"Deploy server listening on port {PORT}")

#     import time; start = time.time()

#     try:
#         while True:
#             if time.time() - start > 5:
#                 print("Time limit reached, stopping server.")
#                 break
#             try:
#                 s.settimeout(0.5)
#                 conn, addr = s.accept()
#                 handle_client(conn, addr)
#             except OSError:
#                 pass
#             except KeyboardInterrupt:
#                 print("Server interrupted with Ctrl+C")
#                 break
#     except Exception as e: 
#         print("Server error:", e)
#     finally:
#         s.close()
#         print("Server stopped")

















import uasyncio as asyncio
import socket

async def start_deploy_server():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT))
    s.listen(5)
    print(f"Deploy server listening on port {PORT}")
    
    s.setblocking(False)  # обязательно, чтобы не блокировать цикл
    loop = asyncio.get_event_loop()

    try:
        while True:
            try:
                conn, addr = s.accept()
                loop.create_task(handle_client(conn, addr))
            except OSError:
                await asyncio.sleep(0.1)  # ждём, не блокируя REPL
    finally:
        s.close()
        print("Server stopped")

asyncio.create_task(start_deploy_server())
print("Server started in background — REPL свободен")
