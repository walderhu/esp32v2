# master
from machine import I2C, Pin
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
SLAVE_ADDR = 0x42 

while True:
    try:
        i2c.writeto(SLAVE_ADDR, b"Hello ESP2")
        print("Sent data to slave")
        time.sleep(1)
    except Exception as e:
        print("I2C Error:", e)
        time.sleep(1)



# # slave
# from machine import Pin, I2C
# from i2cslave import I2CSlave

# i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
# slave = I2CSlave(i2c, 0x42)  # адрес slave

# while True:
#     event = slave.wait()
#     if event == I2CSlave.RECEIVE:
#         data = slave.read()
#         print("Got:", data)
#     elif event == I2CSlave.REQUEST:
#         slave.write(b"Pong")
