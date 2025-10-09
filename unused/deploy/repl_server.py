# repl_server.py — устойчивый Telnet REPL для ESP32 (MicroPython 1.22+)
# Поддержка многострочных блоков, корректное удержание соединения, вывод ошибок

import usocket as socket
import uselect
import sys
import uos
import gc
import io
import errno

HOST = ""      # слушаем все интерфейсы
PORT = 1234    # порт Telnet-REPL


def run():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    print("Telnet REPL server running on port", PORT)

    while True:
        client, addr = s.accept()
        print("Telnet client connected:", addr)
        try:
            client.setblocking(False)
            client.send(b"Welcome to MicroPython REPL!\r\n>>> ")

            poll = uselect.poll()
            poll.register(client, uselect.POLLIN)

            buffer = ""
            code_lines = []
            incomplete = False

            while True:
                res = poll.poll(100)
                if not res:
                    continue

                try:
                    data = client.recv(256)
                    if not data:
                        continue
                except OSError as e:
                    if len(e.args) > 0 and e.args[0] == errno.EAGAIN:
                        continue
                    else:
                        raise

                buffer += data.decode(errors="ignore")

                # ждём перевода строки
                if "\r" not in buffer and "\n" not in buffer:
                    continue

                # отделяем строку
                line, _, rest = buffer.partition("\n")
                buffer = rest
                line = line.rstrip("\r\n")

                # пустая строка — просто новое приглашение
                if not line.strip() and not incomplete:
                    client.send(b">>> ")
                    continue

                code_lines.append(line)
                src = "\n".join(code_lines)

                # проверяем завершённость конструкции
                try:
                    compile(src, "<stdin>", "exec")
                    incomplete = False
                except SyntaxError as e:
                    if "unexpected EOF" in str(e):
                        incomplete = True
                        client.send(b"... ")
                        continue
                    else:
                        incomplete = False

                # выполняем код
                output_stream = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = output_stream
                try:
                    exec(src, globals(), globals())
                except Exception as e:
                    sys.print_exception(e, output_stream)
                sys.stdout = old_stdout

                result = output_stream.getvalue()
                if result:
                    client.send(result.encode())

                code_lines.clear()
                incomplete = False
                client.send(b">>> ")
                gc.collect()

        except Exception as e:
            print("Client error:", e)
        finally:
            print("Telnet client disconnected:", addr)
            try:
                client.close()
            except:
                pass
            gc.collect()
