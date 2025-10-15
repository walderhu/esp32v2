#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import struct
import traceback

try:
    import usocket as socket
except ImportError:
    import socket

# Define to 1 to use builtin "uwebsocket" module of MicroPython
USE_BUILTIN_UWEBSOCKET = 0
# Treat this remote directory as a root for file transfers
SANDBOX = ""
#SANDBOX = "/tmp/webrepl/"
DEBUG = 0

WEBREPL_REQ_S = "<2sBBQLH64s"
WEBREPL_PUT_FILE = 1
WEBREPL_GET_FILE = 2
WEBREPL_GET_VER = 3
WEBREPL_FRAME_TXT = 0x81
WEBREPL_FRAME_BIN = 0x82


def debugmsg(msg):
    if DEBUG:
        print(msg)


if USE_BUILTIN_UWEBSOCKET:
    from uwebsocket import websocket
else:
    class websocket:

        def __init__(self, s):
            self.s = s
            self.buf = b""

        def write(self, data, frame=WEBREPL_FRAME_BIN):
            l = len(data)
            if l < 126:
                hdr = struct.pack(">BB", frame, l)
            else:
                hdr = struct.pack(">BBH", frame, 126, l)
            self.s.send(hdr)
            self.s.send(data)

        def recvexactly(self, sz):
            res = b""
            while sz:
                data = self.s.recv(sz)
                if not data:
                    break
                res += data
                sz -= len(data)
            return res

        def read(self, size, text_ok=False):
            if not self.buf:
                while True:
                    hdr = self.recvexactly(2)
                    if len(hdr) != 2:
                        raise AssertionError("Websocket header truncated")
                    fl, sz = struct.unpack(">BB", hdr)
                    if sz == 126:
                        hdr = self.recvexactly(2)
                        if len(hdr) != 2:
                            raise AssertionError("Websocket extended header truncated")
                        (sz,) = struct.unpack(">H", hdr)
                    if fl == 0x82:
                        break
                    if text_ok and fl == 0x81:
                        break
                    debugmsg("Got unexpected websocket record of type %x, skipping it" % fl)
                    while sz:
                        skip = self.s.recv(sz)
                        debugmsg("Skip data: %s" % skip)
                        sz -= len(skip)
                data = self.recvexactly(sz)
                if len(data) != sz:
                    raise AssertionError("Websocket payload truncated")
                self.buf = data

            d = self.buf[:size]
            self.buf = self.buf[size:]
            if len(d) != size:
                raise AssertionError("Requested %d bytes, got %d" % (size, len(d)))
            return d

        def ioctl(self, req, val):
            assert req == 9 and val == 2


def login(ws, passwd):
    # дождёмся приглашения пароля (последний ':' перед пробел)
    while True:
        c = ws.read(1, text_ok=True)
        if c == b":":
            assert ws.read(1, text_ok=True) == b" "
            break
    ws.write(passwd.encode("utf-8") + b"\r")


def read_resp(ws):
    data = ws.read(4)
    sig, code = struct.unpack("<2sH", data)
    if sig != b"WB":
        raise Exception("Unexpected response signature: %r" % (sig,))
    return code


def send_req(ws, op, sz=0, fname=b""):
    rec = struct.pack(WEBREPL_REQ_S, b"WA", op, 0, 0, sz, len(fname), fname)
    debugmsg("%r %d" % (rec, len(rec)))
    ws.write(rec)


def get_ver(ws):
    send_req(ws, WEBREPL_GET_VER)
    d = ws.read(3)
    d = struct.unpack("<BBB", d)
    return d


def do_repl(ws):
    import termios, select

    class ConsolePosix:
        def __init__(self):
            self.infd = sys.stdin.fileno()
            self.infile = sys.stdin.buffer.raw
            self.outfile = sys.stdout.buffer.raw
            self.orig_attr = termios.tcgetattr(self.infd)

        def enter(self):
            # attr is: [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]
            attr = termios.tcgetattr(self.infd)
            attr[0] &= ~(termios.BRKINT | termios.ICRNL | termios.INPCK | termios.ISTRIP | termios.IXON)
            attr[1] = 0
            attr[2] = attr[2] & ~(termios.CSIZE | termios.PARENB) | termios.CS8
            attr[3] = 0
            attr[6][termios.VMIN] = 1
            attr[6][termios.VTIME] = 0
            termios.tcsetattr(self.infd, termios.TCSANOW, attr)

        def exit(self):
            termios.tcsetattr(self.infd, termios.TCSANOW, self.orig_attr)

        def readchar(self):
            res = select.select([self.infd], [], [], 0)
            if res[0]:
                return self.infile.read(1)
            else:
                return None

        def write(self, buf):
            self.outfile.write(buf)

    console = ConsolePosix()
    console.enter()
    try:
        while True:
            sel = select.select([console.infd, ws.s], [], [])
            c = console.readchar()
            if c:
                if c == b"\x1d":  # ctrl-], exit
                    break
                else:
                    ws.write(c, WEBREPL_FRAME_TXT)
            if ws.s in sel[0]:
                c = ws.read(1, text_ok=True)
                while c is not None:
                    oc = ord(c)
                    if oc in (8, 9, 10, 13, 27) or oc >= 32:
                        console.write(c)
                    else:
                        console.write(b"[%02x]" % ord(c))
                    if ws.buf:
                        c = ws.read(1)
                    else:
                        c = None
    finally:
        console.exit()


def put_file(ws, local_file, remote_file):
    if not os.path.isfile(local_file):
        raise Exception("Local file not found: %s" % local_file)
    try:
        sz = os.stat(local_file)[6]
    except Exception:
        sz = os.path.getsize(local_file)
    dest_fname = (SANDBOX + remote_file).encode("utf-8")
    rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_PUT_FILE, 0, 0, sz, len(dest_fname), dest_fname)
    debugmsg("%r %d" % (rec, len(rec)))
    # write header in two parts as original code did
    ws.write(rec[:10])
    ws.write(rec[10:])
    code = read_resp(ws)
    if code != 0:
        raise Exception("PUT request rejected by remote (code %d)" % code)
    cnt = 0
    with open(local_file, "rb") as f:
        while True:
            sys.stdout.write("Sent %d of %d bytes\r" % (cnt, sz))
            sys.stdout.flush()
            buf = f.read(1024)
            if not buf:
                break
            ws.write(buf)
            cnt += len(buf)
    sys.stdout.write("\n")
    code = read_resp(ws)
    if code != 0:
        raise Exception("PUT failed after transfer (code %d)" % code)


def get_file(ws, local_file, remote_file):
    src_fname = (SANDBOX + remote_file).encode("utf-8")
    rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_GET_FILE, 0, 0, 0, len(src_fname), src_fname)
    debugmsg("%r %d" % (rec, len(rec)))
    ws.write(rec)
    code = read_resp(ws)
    if code != 0:
        raise Exception("GET request rejected by remote (code %d)" % code)
    with open(local_file, "wb") as f:
        cnt = 0
        while True:
            ws.write(b"\0")
            data = ws.read(2)
            if not data or len(data) != 2:
                raise Exception("Failed to read size from remote")
            (sz,) = struct.unpack("<H", data)
            if sz == 0:
                break
            while sz:
                buf = ws.read(sz)
                if not buf:
                    raise OSError("Remote closed stream unexpectedly")
                cnt += len(buf)
                f.write(buf)
                sz -= len(buf)
                sys.stdout.write("Received %d bytes\r" % cnt)
                sys.stdout.flush()
    sys.stdout.write("\n")
    code = read_resp(ws)
    if code != 0:
        raise Exception("GET failed after transfer (code %d)" % code)


def client_handshake(sock):
    cl = sock.makefile("rwb", 0)
    cl.write(b"""\
GET / HTTP/1.1\r
Host: echo.websocket.org\r
Connection: Upgrade\r
Upgrade: websocket\r
Sec-WebSocket-Key: foo\r
\r
""")
    l = cl.readline()
#    print(l)
    while 1:
        l = cl.readline()
        if l == b"\r\n":
            break
#        sys.stdout.write(l)


def exec_code(ws, code, done_marker="<<<WEBREPL_DONE>>>", idle_timeout=0.4):
    """
    Send code and wait for a marker or idle timeout.
    """
    if "machine.reset" in code:
        ws.write(code.encode("utf-8") + b'\r', WEBREPL_FRAME_TXT)
        print("[sent reset, not waiting for output]")
        return

    import select, time

    payload = code + "\rprint(%r)\r" % done_marker
    ws.write(payload.encode("utf-8"), WEBREPL_FRAME_TXT)

    start = time.time()
    buf = b""
    marker_bytes = done_marker.encode("utf-8")
    sock = ws.s

    try:
        while True:
            r, _, _ = select.select([sock], [], [], idle_timeout)
            if not r:
                break
            try:
                b = ws.read(1, text_ok=True)
            except AssertionError:
                break
            if not b:
                break
            buf += b
            if marker_bytes in buf:
                idx = buf.find(marker_bytes)
                out = buf[:idx]
                try:
                    sys.stdout.buffer.write(out)
                    sys.stdout.buffer.flush()
                except Exception:
                    sys.stdout.write(out.decode('utf-8', 'replace'))
                    sys.stdout.flush()
                return
            if time.time() - start > 30:
                break
    except KeyboardInterrupt:
        pass

    if buf:
        try:
            sys.stdout.buffer.write(buf)
            sys.stdout.buffer.flush()
        except Exception:
            sys.stdout.write(buf.decode('utf-8', 'replace'))
            sys.stdout.flush()


def help(rc=0):
    exename = sys.argv[0].rsplit("/", 1)[-1]
    print("%s - Access REPL, perform remote file operations via MicroPython WebREPL protocol" % exename)
    print("Arguments:")
    print("  [-p password] [-e code] <host>                            - Access the remote REPL or execute code")
    print("  [-p password] <host>:<remote_file> <local_file> - Copy remote file to local file")
    print("  [-p password] <local_file> <host>:<remote_file> - Copy local file to remote file")
    print("Examples:")
    print("  %s 192.168.4.1" % exename)
    print("  %s script.py 192.168.4.1:/another_name.py" % exename)
    print("  %s -p password 192.168.4.1:/app/script.py ." % exename)
    print("  %s -p password -e \"print('hi')\" 192.168.4.1" % exename)
    sys.exit(rc)


def error(msg):
    print(msg)
    sys.exit(1)


def parse_remote(remote):
    # Input like "host:port:path" or "host:path" or "host"
    if ":" not in remote:
        return (remote, 8266, "/")
    # split host:rest
    hostport, fname = remote.split(":", 1)
    if fname == "":
        fname = "/"
    host = hostport
    port = 8266
    # allow host:port (no path) if rest is digits
    if fname.isdigit():
        port = int(fname)
        fname = "/"
    # if host contains colon (IPv6 style), user can pass " [..]" - keep simple
    if ":" in hostport and hostport.count(":") == 1:
        host, port = hostport.split(":")
        port = int(port)
    return (host, port, fname)


def main():
    passwd = None
    code_to_exec = None
    args = sys.argv[1:]
    i = 0
    # parse -p and -e options (order-independent)
    while i < len(args):
        if args[i] == '-p':
            if i + 1 >= len(args):
                help(1)
            passwd = args.pop(i + 1)
            args.pop(i)
            continue
        if args[i] == '-e':
            if i + 1 >= len(args):
                help(1)
            code_to_exec = args.pop(i + 1)
            args.pop(i)
            continue
        i += 1

    if not args and not code_to_exec:
        help(1)

    # If there is one arg and it looks like a host (without colon path) -> host for repl/exec
    host_arg = args[0] if args else None

    try:
        if passwd is None:
            import getpass
            passwd = getpass.getpass()

        # Determine operation
        if code_to_exec:
            op = "exec"
            if not host_arg:
                help(1)
            host, port, _ = parse_remote(host_arg + ":")
        elif len(args) == 1:
            op = "repl"
            host, port, _ = parse_remote(args[0] + ":")
        elif ":" in args[0]:
            op = "get"
            host, port, src_file = parse_remote(args[0])
            dst_file = args[1]
            if os.path.isdir(dst_file):
                basename = src_file.rsplit("/", 1)[-1]
                dst_file = os.path.join(dst_file, basename)
        else:
            op = "put"
            host, port, dst_file = parse_remote(args[1])
            src_file = args[0]
            if dst_file.endswith("/"):
                basename = src_file.rsplit("/", 1)[-1]
                dst_file = dst_file + basename

        if op in ("get", "put"):
            print(src_file, "->", dst_file)

        # connect
        s = socket.socket()
        ai = socket.getaddrinfo(host, port)
        addr = ai[0][4]
        s.connect(addr)
        client_handshake(s)

        ws = websocket(s)
        login(ws, passwd)
        # print("Remote WebREPL version:", get_ver(ws)) #!

        ws.ioctl(9, 2)

        if op == "exec":
            exec_code(ws, code_to_exec)
        elif op == "repl":
            do_repl(ws)
        elif op == "get":
            get_file(ws, dst_file, src_file)
        elif op == "put":
            put_file(ws, src_file, dst_file)

        s.close()
        sys.exit(0)

    except Exception as e:
        # Print traceback for debugging during deploy
        print("Error during operation:", str(e))
        traceback.print_exc()
        try:
            s.close()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
