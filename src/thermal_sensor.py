from machine import Pin
import onewire, ds18x20
import time

dat = Pin(13)
ds = ds18x20.DS18X20(onewire.OneWire(dat))

roms = ds.scan()
print("Found devices:", roms)

while True:
    ds.convert_temp(); time.sleep(0.1)
    temp = ds.read_temp(roms[0])
    print(f"\r\033[K", end='')
    print(f"Temperature: {temp:.2f} °C", end='')
   