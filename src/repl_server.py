import uasyncio as asyncio
import sys
import io

clients = set()

        
async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print("REPL client:", addr)
    await writer.awrite(b"Welcome to MicroPython REPL!\n>>> ")

    code_lines = []

    try:
        while True:
            data = await reader.read(128)
            if not data:
                break
            lines = data.decode().split("\n")
            for line in lines:
                line = line.rstrip()
                code_lines.append(line)
                
                # Пустая строка — конец блока
                if line == "" or line.startswith(">>>"):
                    code_str = "\n".join(code_lines).strip()
                    if code_str:
                        try:
                            exec(code_str, globals())
                        except Exception as e:
                            await writer.awrite(("Error: " + str(e) + "\n").encode())
                    code_lines = []
                    await writer.awrite(b">>> ")

    finally:
        await writer.aclose()
        print("Client disconnected:", addr)


async def start_repl_server(port=1234):
    server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    print(f"REPL server started on port {port}")

    while True:
        await asyncio.sleep(3600)
