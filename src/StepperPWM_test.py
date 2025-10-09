from machine import Pin, PWM
import time

STEP = PWM(Pin(14))   
DIR = Pin(15, Pin.OUT)
ENA = Pin(13, Pin.OUT)

def run_pwm(direction=1, freq=20000, duration=3):
    ENA.off()                # включить драйвер (обычно ENA низкий — активный)
    DIR.value(direction)     # направление
    STEP.freq(freq)          # установить частоту
    STEP.duty_u16(32768)     # 50% ШИМ (импульсы идут)
    time.sleep(duration)     # крутиться duration секунд
    STEP.duty_u16(0)         # остановить импульсы
    time.sleep(0.2)


def main():
    freq = 10000 
    # print("Едем вперёд...")
    # run_pwm(direction=1, freq=freq, duration=1)
    print("Пауза 1 сек...")
    time.sleep(1)
    print("Едем назад...")
    run_pwm(direction=0, freq=freq, duration=1)
    print("Готово.")
