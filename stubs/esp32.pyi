"""
esp32 — функциональность, специфичная для микроконтроллеров ESP32.

Эта заглушка предназначена для эмуляции модуля `esp32` под CPython,
чтобы обеспечивать совместимость кода, автодополнение и статическую проверку типов.

Оригинал: https://docs.micropython.org/en/latest/library/esp32.html
"""

from typing import Any, Optional, Tuple, List


# ==========================================================================
# Константы
# ==========================================================================

WAKEUP_ALL_LOW = 0
"""Используется для esp32.wake_on_ext0/ext1 — пробуждение при низком уровне на всех пинах."""

WAKEUP_ANY_HIGH = 1
"""Используется для esp32.wake_on_ext0/ext1 — пробуждение при высоком уровне на любом пине."""

HEAP_DATA = 0
"""Тип области кучи ESP-IDF: данные."""

HEAP_EXEC = 1
"""Тип области кучи ESP-IDF: исполняемая."""


# ==========================================================================
# Функции
# ==========================================================================

def wake_on_touch(wake: bool) -> None:
    """Включает или выключает пробуждение от сенсорных пинов.

    :param wake: True — разрешить пробуждение, False — запретить.
    """
    print(f"[esp32] wake_on_touch({wake})")


def wake_on_ulp(wake: bool) -> None:
    """Разрешает пробуждение от ULP (Ultra Low Power) сопроцессора."""
    print(f"[esp32] wake_on_ulp({wake})")


def wake_on_ext0(pin: Any, level: int) -> None:
    """Настраивает EXT0 как источник пробуждения.

    :param pin: Объект Pin или None.
    :param level: esp32.WAKEUP_ALL_LOW или esp32.WAKEUP_ANY_HIGH
    """
    print(f"[esp32] wake_on_ext0(pin={pin}, level={level})")


def wake_on_ext1(pins: Optional[list], level: int) -> None:
    """Настраивает EXT1 как источник пробуждения.

    :param pins: Список пинов или None.
    :param level: esp32.WAKEUP_ALL_LOW или esp32.WAKEUP_ANY_HIGH
    """
    print(f"[esp32] wake_on_ext1(pins={pins}, level={level})")


def gpio_deep_sleep_hold(enable: bool) -> None:
    """Разрешает сохранение состояния GPIO во время deep-sleep."""
    print(f"[esp32] gpio_deep_sleep_hold({enable})")


def raw_temperature() -> int:
    """Возвращает "сырое" значение встроенного термодатчика ESP32."""
    print("[esp32] raw_temperature()")
    return 25


def idf_heap_info(capabilities: int) -> list:
    """Возвращает информацию о куче ESP-IDF.

    :param capabilities: esp32.HEAP_DATA или esp32.HEAP_EXEC
    :return: Список кортежей (total, free, largest, min_free)
    """
    return [(240, 0, 0, 0), (79912, 35712, 35512, 35108)]


def idf_task_info() -> Tuple[int, list]:
    """Возвращает информацию о задачах FreeRTOS/ESP-IDF."""
    return (12345, [("task", "Running", 5, 123, 512, 0)])


# ==========================================================================
# Класс Partition
# ==========================================================================

class Partition:
    """Доступ к разделам (partitions) флеш-памяти ESP32."""

    BOOT = 0
    """Следующий раздел для загрузки."""

    RUNNING = 1
    """Текущий активный раздел."""

    TYPE_APP = 0
    """Тип раздела: приложение (прошивка)."""

    TYPE_DATA = 1
    """Тип раздела: данные (nvs, phy, otadata и т.п.)."""

    def __init__(self, id: Any, block_size: int = 4096):
        """Создает объект раздела флеша.

        :param id: Метка раздела, Partition.BOOT, Partition.RUNNING или имя.
        :param block_size: Размер блока в байтах (по умолчанию 4096).
        """
        self.id = id
        self.block_size = block_size
        self.label = "mock_partition"

    @classmethod
    def find(cls, type=TYPE_APP, subtype=0xFF, label=None, block_size=4096) -> List["Partition"]:
        """Ищет разделы по типу/подтипу/метке."""
        return [cls("factory", block_size)]

    def info(self) -> tuple:
        """Возвращает информацию о разделе: (type, subtype, addr, size, label, encrypted)."""
        return (self.TYPE_APP, 0xFF, 0x1000, 1024 * 1024, self.label, False)

    def readblocks(self, block_num: int, buf: bytearray, offset: int = 0) -> None:
        """Читает данные из раздела."""
        print(f"[Partition] readblocks(block={block_num}, len={len(buf)}, offset={offset})")

    def writeblocks(self, block_num: int, buf: bytes, offset: int = 0) -> None:
        """Пишет данные в раздел."""
        print(f"[Partition] writeblocks(block={block_num}, len={len(buf)}, offset={offset})")

    def ioctl(self, cmd: int, arg: Any) -> Any:
        """Управление низкоуровневым вводом/выводом раздела."""
        return 0

    def set_boot(self) -> None:
        """Устанавливает раздел как загрузочный при следующем старте."""
        print("[Partition] set_boot()")

    def get_next_update(self) -> "Partition":
        """Возвращает следующий OTA-раздел."""
        return Partition("ota_1")

    @classmethod
    def mark_app_valid_cancel_rollback(cls) -> None:
        """Помечает текущую прошивку как успешную и отменяет откат."""
        print("[Partition] mark_app_valid_cancel_rollback()")


# ==========================================================================
# Класс PCNT (Pulse Counter)
# ==========================================================================

class PCNT:
    """Аппаратный счётчик импульсов ESP32."""

    INCREMENT = 1
    DECREMENT = -1
    IGNORE = 0
    HOLD = 2
    REVERSE = 3

    IRQ_ZERO = 0x01
    IRQ_MIN = 0x02
    IRQ_MAX = 0x04
    IRQ_THRESHOLD0 = 0x08
    IRQ_THRESHOLD1 = 0x10

    def __init__(self, id: int, **kwargs):
        """Создаёт экземпляр счётчика импульсов."""
        self.id = id
        self.value_count = 0
        print(f"[PCNT] init id={id}, kwargs={kwargs}")

    def init(self, **kwargs) -> None:
        """Инициализирует счётчик с новыми параметрами."""
        print(f"[PCNT] init({kwargs})")

    def value(self, value: Optional[int] = None) -> int:
        """Возвращает текущее значение счётчика. При value=0 — сбрасывает."""
        if value == 0:
            old = self.value_count
            self.value_count = 0
            return old
        return self.value_count

    def irq(self, handler=None, trigger=IRQ_ZERO):
        """Настраивает обработчик прерываний для счётчика."""
        print(f"[PCNT] irq(handler={handler}, trigger={trigger})")
        return self


# ==========================================================================
# Класс RMT
# ==========================================================================

class RMT:
    """RMT — Remote Control Module (точная генерация импульсов)."""

    PULSE_MAX = 32767
    """Максимальное значение длительности импульса."""

    def __init__(self, channel: int, *, pin=None, clock_div: int = 8,
                 idle_level: bool = False, tx_carrier: Optional[Tuple[int, int, int]] = None):
        """Создаёт экземпляр RMT-канала.

        :param channel: Номер канала (0–7).
        :param pin: Объект Pin, к которому привязан RMT.
        :param clock_div: Делитель частоты (1–255).
        :param idle_level: Уровень, удерживаемый при простое.
        :param tx_carrier: (freq, duty, level) — параметры несущей частоты.
        """
        self.channel = channel
        self.pin = pin
        self.clock_divider = clock_div
        self.idle_level = idle_level
        self.tx_carrier = tx_carrier
        self._loop = False
        print(f"[RMT] Init channel={channel}, pin={pin}, div={clock_div}, tx_carrier={tx_carrier}")

    @classmethod
    def source_freq(cls) -> int:
        """Возвращает частоту источника (обычно 80 MHz)."""
        return 80_000_000

    def clock_div(self) -> int:
        """Возвращает установленный делитель частоты."""
        return self.clock_divider

    def wait_done(self, *, timeout=0) -> bool:
        """Блокирует выполнение до завершения передачи или таймаута."""
        print(f"[RMT] wait_done(timeout={timeout})")
        return True

    def loop(self, enable_loop: bool) -> None:
        """Включает или выключает циклический режим передачи."""
        print(f"[RMT] loop({enable_loop})")
        self._loop = enable_loop

    def write_pulses(self, duration, data=True) -> None:
        """Передаёт последовательность импульсов.

        Поддерживаются три режима:
          1. duration — список длительностей; data — начальный уровень (True/False)
          2. duration — число; data — список уровней
          3. duration и data — списки одинаковой длины
        """
        print(f"[RMT] write_pulses(duration={duration}, data={data})")

    @staticmethod
    def bitstream_channel(value: Optional[int] = None) -> int:
        """Устанавливает или возвращает канал, используемый для machine.bitstream()."""
        if value is not None:
            print(f"[RMT] bitstream_channel set to {value}")
        return 7


# ==========================================================================
# Класс ULP
# ==========================================================================

class ULP:
    """ULP — Ultra-Low-Power сопроцессор."""

    def __init__(self):
        print("[ULP] init()")

    def set_wakeup_period(self, period_index: int, period_us: int) -> None:
        """Устанавливает период пробуждения в микросекундах."""
        print(f"[ULP] set_wakeup_period(index={period_index}, period_us={period_us})")

    def load_binary(self, load_addr: int, program_binary: bytes) -> None:
        """Загружает бинарный код ULP-программы по указанному адресу."""
        print(f"[ULP] load_binary(addr={load_addr}, size={len(program_binary)})")

    def run(self, entry_point: int) -> None:
        """Запускает ULP-программу с заданной точки входа."""
        print(f"[ULP] run(entry={entry_point})")


# ==========================================================================
# Класс NVS (Non-Volatile Storage)
# ==========================================================================

class NVS:
    """NVS — API доступа к энергонезависимому хранилищу (NVS)."""

    def __init__(self, namespace: str):
        """Открывает пространство имён (создаёт, если отсутствует)."""
        self.namespace = namespace
        self.store = {}
        print(f"[NVS] init namespace={namespace}")

    def set_i32(self, key: str, value: int) -> None:
        """Сохраняет 32-битное целое значение по ключу."""
        self.store[key] = int(value)

    def get_i32(self, key: str) -> int:
        """Читает 32-битное целое значение."""
        return int(self.store.get(key, 0))

    def set_blob(self, key: str, value: bytes) -> None:
        """Сохраняет бинарные данные по ключу."""
        self.store[key] = bytes(value)

    def get_blob(self, key: str, buffer: bytearray) -> int:
        """Читает бинарные данные в буфер. Возвращает фактический размер."""
        blob = self.store.get(key, b"")
        n = min(len(blob), len(buffer))
        buffer[:n] = blob[:n]
        return n

    def erase_key(self, key: str) -> None:
        """Удаляет запись по ключу."""
        self.store.pop(key, None)

    def commit(self) -> None:
        """Подтверждает изменения и записывает в flash."""
        print("[NVS] commit()")
