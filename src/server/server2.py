import socket

def handler(req): 
    print(req)


def serve():
    with open("index.html", "r", encoding="utf-8") as f: HTML = f.read()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    s.bind(("0.0.0.0", 8081))
    s.listen(1)
    print("Открой https://jazlynn-englacial-undoubtfully.ngrok-free.dev/")

    while True:
        cl, addr = s.accept()
        try:
            req = cl.recv(4096).decode(errors='ignore')
            if req.startswith('GET /misc/'):
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
                handler(req)
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n")
                cl.sendall(HTML.encode())
        except Exception as e: print("⚠️  Ошибка:", e)
        finally: cl.close()


if __name__ == "__main__":
    try: serve()
    except KeyboardInterrupt: pass
