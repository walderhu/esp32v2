# # master (ESP1)
# from machine import UART
# import time

# uart = UART(1, tx=17, rx=16, baudrate=115200)
# while True:
#     uart.write("Hello ESP2\n")
#     time.sleep(1)



# # slave (ESP2)
# from machine import UART

# uart = UART(1, tx=17, rx=16, baudrate=115200)
# while True:
#     if uart.any():
#         print(uart.readline())
