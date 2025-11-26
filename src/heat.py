from machine import Pin
import onewire, ds18x20
import time

# === настройки ===
TARGET_TEMP = 60
HYST = 3

# Пины — подставь свои номера
sensor_pin = Pin(13)
set_pin = Pin(15, Pin.OUT)    # подаём импульс для "вкл"
reset_pin = Pin(16, Pin.OUT)  # подаём импульс для "выкл"

# Если модуль требует активный низкий сигнал, поменяй эти флаги
SET_ACTIVE_HIGH = True   # True если лог.1 = включить
RESET_ACTIVE_HIGH = True # True если лог.1 = выключить

# Вспомогательные функции для подачи короткого импульса (безопасно)
PULSE_MS = 120  # длительность импульса, обычно 50-200 ms — проверь документацию реле

def _pulse(pin, active_high=True):
    # никогда не держим оба канала одновременно активными
    if pin is set_pin:
        other = reset_pin
    else:
        other = set_pin
    # гарантируем, что другой канал не активен
    if (other.value() == 1 and ((other is set_pin and SET_ACTIVE_HIGH) or (other is reset_pin and RESET_ACTIVE_HIGH))):
        # выключаем другой канал безопасно
        if other is set_pin:
            _deactivate_pin(other, SET_ACTIVE_HIGH)
        else:
            _deactivate_pin(other, RESET_ACTIVE_HIGH)

    # активируем выбранный
    if active_high:
        pin.on()
    else:
        pin.off()
    time.sleep_ms(PULSE_MS)
    # деактивируем
    if active_high:
        pin.off()
    else:
        pin.on()

def _activate_pin(pin, active_high=True):
    if active_high:
        pin.on()
    else:
        pin.off()

def _deactivate_pin(pin, active_high=True):
    if active_high:
        pin.off()
    else:
        pin.on()

def heater_on():
    _pulse(set_pin, SET_ACTIVE_HIGH)

def heater_off():
    _pulse(reset_pin, RESET_ACTIVE_HIGH)

# === DS18B20 init ===
ow = onewire.OneWire(sensor_pin)
ds = ds18x20.DS18X20(ow)

roms = ds.scan()
if not roms:
    raise Exception("DS18B20 not found!")
rom = roms[0]
print("Sensor:", rom)

# начальное состояние — считаем что выключено
_deactivate_pin(set_pin, SET_ACTIVE_HIGH)
_deactivate_pin(reset_pin, RESET_ACTIVE_HIGH)

# цикл управления
while True:
    try:
        ds.convert_temp()
        time.sleep_ms(750)  # время конвертации для 12-bit
        temp = ds.read_temp(rom)
        # иногда read_temp может вернуть None — проверим
        if temp is None:
            raise Exception("Ошибка чтения температуры (None)")
        print(f"\rTemperature: {temp:.2f}°C   ", end="")

        if temp < TARGET_TEMP - HYST:
            heater_on()
        elif temp > TARGET_TEMP + HYST:
            heater_off()

    except Exception as e:
        # можно ловить специфично onewire.OneWireError, если доступно:
        # from onewire import OneWireError
        # except OneWireError:
        print("\nОшибка датчика или шины OneWire:", e)
        # при ошибке — безопасно выключаем нагрев
        heater_off()
        time.sleep(1)
