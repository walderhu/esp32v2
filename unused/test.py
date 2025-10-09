import uasyncio as asyncio
from lib import wss_repl
import deploy_server

async def main():
    wss_repl.start()  # запускает WebSocket REPL
    await deploy_server.start_deploy_server()

asyncio.run(main())

