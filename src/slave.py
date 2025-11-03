from machine import UART, Pin
uart = UART(1, baudrate=115200, tx=Pin(17), rx=Pin(16))  # подбери пины
uart.write("Hello from A\n")
