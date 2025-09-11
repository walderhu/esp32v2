from machine import Pin
import uasyncio as asyncio
import machine
import logging
import config
import time

STEP_PIN = 14
DIR_PIN = 15
ENABLE_PIN = 13
SWITCH_PIN = 17

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

class StepperEngineError(Exception):
    def __init__(self, message):
        super().__init__(message)


class StepperEngine:
    def __init__(self, step_pin=STEP_PIN, dir_pin=DIR_PIN, enable_pin=ENABLE_PIN):
        self._step_pin = Pin(step_pin, Pin.OUT)
        self._dir_pin = Pin(dir_pin, Pin.OUT)
        self._enable_pin = Pin(enable_pin, Pin.OUT)
        self._switch_pin = Pin(switch_pin, Pin.IN, Pin.PULL_UP)

        self._last_switch_state = self._switch_pin.value()
        self._last_change = time.ticks_ms()
        self._debounce_delay = 50  # мс


    async def _debounced_switch(self) -> bool:
        """
        Фильтрация дребезга контактов
        Получаем состояние концевика, сравниваем с последним его состоянием
        Если мы засекли изменение, смотрим не помеха ли это, с помощью
        отслеживания времени фикс. сигнала, если оно больше self._debounce_delay[мс]
        то мы засчитываем изменение и отправляем результат
        """
        current_state = self._switch_pin.value()
        if current_state != self._last_switch_state:
            tt = time.ticks_diff(time.ticks_ms(), self._last_change)
            if tt > self._debounce_delay:
                self._last_switch_state = current_state
                self._last_change = time.ticks_ms()
                result: bool = (current_state == 0)
                return result   
        return False

    
    async def __aenter__(self):
        self._enable_pin.value(0)
        return self


    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                raise StepperEngineError(exc_type)
        finally:
            self._enable_pin.value(1)


    async def step(self, direction=1, delay_ms=1):
        assert int(direction) in (0, 1), "Направление должно быть 0 или 1"
        self._dir_pin.value(direction)
        self._step_pin.value(1)
        await asyncio.sleep_ms(delay)
        self._step_pin.value(0)
        await asyncio.sleep_ms(delay)
        
        
    async def move(self, steps, delay_ms=1):
        _dir = steps > 0
        steps = abs(steps)
        for _ in range(steps):
            await eng.step(direction=_dir)


    async def move_to_rail_end(self, direction=1, speed_ms=1, timeout=30):
        """
        Функция для движения шагового двигателя до срабатывания концевого выключателя.
        :param direction: Направление движения (0 - в обратном направлении, 1 - в прямом)
        :param speed_ms: Задержка между шагами в миллисекундах
        :param timeout: Максимальное время движения в секундах
        :raises StepperEngineError: Если движение не завершится до истечения таймаута        
        """
        self._dir_pin.value(direction)
        start_time = time.ticks_ms()
        
        while True:
            tt = time.ticks_diff(time.ticks_ms(), start_time)
            if tt > timeout * 1000:
                raise StepperEngineError("Таймаут достижения упора")
            
            if await self._debounced_switch():
                log.info("Достигнут концевой выключатель")
                return

            await self.step(delay_ms=speed_ms)


async def homing_sequence():
    """
    Процедура поиска нулевой точки
    """
    async with StepperEngine() as eng:
        try:
            # Движение в обратном направлении до упора
            await eng.move_to_rail_end(direction=0, speed_ms=2)
            log.info("Нулевая точка найдена")
            
            # Отъезд от упора на безопасное расстояние
            await eng.move(500, delay_ms=1, direction=1)
            
        except StepperEngineError as e:
            log.error(f"Ошибка инициализации: {e}")
            eng.emergency_stop()

async def main():
    await homing_sequence()
    log.info("Система готова к работе")
