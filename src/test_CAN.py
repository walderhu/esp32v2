import asyncio
import CAN

dev = CAN(0, extframe=False, tx=5, rx=4, mode=CAN.LOOPBACK, bitrate=50000, auto_restart=False)


# - identifier of can packet (int)
# - extended packet (bool)
# - rtr packet (bool)
# - data frame (0..8 bytes)

async def reader():
    while True:
        if dev.any():
            data = dev.recv()
            print(f"RECEIVED: id:{hex(data[0])}, ex:{data[1]}, rtr:{data[2]}, data:{data[3]}")
        await asyncio.sleep(0.01)

async def sender():
    counter = 0
    while True:
        # Send a message once per second
        msg_id = 0x123  # CAN message identifier
        # Use list of bytes instead of bytes object
        msg_data = [counter & 0xFF, (counter >> 8) & 0xFF]
        
        # Correct parameter order: data first, then ID
        dev.send(msg_data, msg_id)  # data, id
        
        print(f"SENT: id:{hex(msg_id)}, data:{msg_data}")
        counter += 1
        await asyncio.sleep(1)  # Send message once per second

async def main():
    # Start both tasks concurrently
    read_task = asyncio.create_task(reader())
    send_task = asyncio.create_task(sender())
    
    # Wait for both tasks (this will run forever)
    await asyncio.gather(read_task, send_task)

# Run the example
loop = asyncio.get_event_loop()
loop.run_until_complete(main())