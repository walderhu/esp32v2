
class Portal:
    """
    Синхронный интерфейс для портала на двух шаговиках (X и Y).
    """
    def __init__(self, motor_x: StepperPWMAsync, motor_y: StepperPWMAsync, ratio_yx=1.0):
        """
        ratio_yx — коэффициент скорости для второго мотора относительно первого
        (например, если моторы двигают одну ось с разными передачами).
        """
        self.x = motor_x
        self.y = motor_y
        self.ratio_yx = ratio_yx

    # ======= ВСПОМОГАТЕЛЬНОЕ =======
    def _run(self, coro):
        """Запуск асинхронной задачи синхронно."""
        try:
            asyncio.run(coro)
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro)

    # ======= ПУБЛИЧНЫЕ МЕТОДЫ =======
    def enable(self, state=True):
        """Включить или выключить оба мотора."""
        self.x.enable(state)
        self.y.enable(state)

    def stop(self):
        """Остановить оба мотора."""
        self.x.stop()
        self.y.stop()

    def home(self, freq=12000):
        """Возврат к концевикам синхронно для обоих моторов."""
        async def _home():
            tasks = [asyncio.create_task(self.x.home(freq=freq)),
                     asyncio.create_task(self.y.home(freq=int(freq*self.ratio_yx)))]
            await asyncio.gather(*tasks)
        self._run(_home())

    def move_accel(self, x_cm=None, y_cm=None, max_freq=20000, accel_ratio=0.2):
        """Синхронное перемещение с плавным ускорением."""
        async def _move():
            tasks = []
            if x_cm is not None:
                tasks.append(asyncio.create_task(self.x.move_accel(distance_cm=x_cm,
                                max_freq=max_freq, accel_ratio=accel_ratio)))
            if y_cm is not None:
                tasks.append(asyncio.create_task(self.y.move_accel(distance_cm=y_cm,
                                max_freq=int(max_freq*self.ratio_yx), accel_ratio=accel_ratio)))
            if tasks:  # Не виснем, если нет задач
                await asyncio.gather(*tasks)
        self._run(_move())

    def move_to(self, x_mm=None, y_mm=None, freq=10000):
        """Простое перемещение без ускорения (абсолютные позиции в мм)."""
        async def _move():
            tasks = []
            if x_mm is not None:
                tasks.append(asyncio.create_task(self.x.move_to(target_mm=x_mm, freq=freq)))
            if y_mm is not None:
                tasks.append(asyncio.create_task(self.y.move_to(target_mm=y_mm, freq=int(freq*self.ratio_yx))))
            if tasks:  # Не виснем
                await asyncio.gather(*tasks)
        self._run(_move())

    def deinit(self):
        """Деинициализация PWM."""
        self.x.deinit()
        self.y.deinit()

    def __enter__(self):
        self.enable(True)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type: 
                raise exc_type(exc) from tb
        finally:
            self.enable(False)
            self.deinit()
            
            
            
            
            
def test():  # Синхронная функция
    m1 = StepperPWMAsync(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, lead_mm=2.475, limit_coord=65)
    m2 = StepperPWMAsync(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, lead_mm=2.475, limit_coord=90)

    with Portal(m1, m2, ratio_yx=90/64) as portal:
        portal.home(freq=12_000)
        print("Home done")
        portal.move_to(x_mm=300, y_mm=40, freq=12_000)
        print("Move to 30/40 done")
        portal.move_to(x_mm=100, y_mm=10, freq=15_000)
        print("Move to 10/10 done")
        print(f"Final pos: X={m1.current_coord:.2f}cm, Y={m2.current_coord:.2f}cm")

# Запуск: import serva2; serva2.test()  # НЕ asyncio.run(serva2.test()), т.к. test() не корутина!