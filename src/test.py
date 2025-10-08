import repl_server
import uasyncio as asyncio

async def main():
    asyncio.create_task(repl_server.start_repl_server(1234))
    while True: await asyncio.sleep(60)

asyncio.run(main())