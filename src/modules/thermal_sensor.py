from machine import Pin
import onewire, ds18x20
import time

TARGET_TEMP = 40
HYST = 3

sensor_pin = Pin(13)
heater = Pin(15, Pin.OUT)

ds = ds18x20.DS18X20(onewire.OneWire(sensor_pin))
roms = ds.scan()
if not roms: raise Exception("DS18B20 not found!")
print("Sensor:", roms[0])

while True:
    try:
        ds.convert_temp(); time.sleep(0.5)
        temp = float(ds.read_temp(roms[0]))
        print(f"\rTemperature: {temp:.2f}°C   ", end="")
        if temp < TARGET_TEMP - HYST:
            heater.on()
        elif temp > TARGET_TEMP + HYST:
            heater.off()
    except onewire.OneWireError: pass



# выключать в конце 
# PID
