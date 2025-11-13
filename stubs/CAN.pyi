"""
Functions related to the CAN bus.
MicroPython module: https://docs.micropython.org/en/latest/library/machine.CAN.html

The ``machine.CAN`` class provides access to the CAN controller on ESP32 boards.
Only one CAN controller is supported (bus 0). The driver supports normal,
listen-only, silent, and loopback modes. It uses the ESP-IDF TWAI driver
under the hood.

---
Module: 'machine' on micropython-v1.26.0-esp32-ESP32_GENERIC
"""
# MCU: {'variant': '', 'build': '', 'arch': 'xtensa', 'port': 'esp32', 'board': 'ESP32_GENERIC', 'board_id': 'ESP32_GENERIC', 'mpy': 'v6.3', 'ver': 'v1.26.0', 'family': 'micropython', 'cpu': 'ESP32', 'version': 'v1.26.0'}
# Stubber: v1.26.0
from __future__ import annotations
from typing import Any, Callable, List, Tuple, Optional, overload
from _typeshed import Incomplete
from typing_extensions import Final

# CAN modes
NORMAL: Final[int] = 0
SLEEP: Final[int] = -1
LOOPBACK: Final[int] = -2
SILENT: Final[int] = 1
SILENT_LOOPBACK: Final[int] = -3
LISTEN_ONLY: Final[int] = 2

# Filter modes
FILTER_RAW_SINGLE: Final[int] = 1
FILTER_RAW_DUAL: Final[int] = 2
FILTER_ADDRESS: Final[int] = 3

# Message flags
RTR: Final[int] = 1
EXTENDED_ID: Final[int] = 2
FD_F: Final[int] = 3
BRS: Final[int] = 4

# Receive errors
CRC: Final[int] = 1
FORM: Final[int] = 2
OVERRUN: Final[int] = 3
ESI: Final[int] = 4

# Send errors
ARB: Final[int] = 1
NACK: Final[int] = 2
ERR: Final[int] = 3

# Alert flags
ALERT_ALL: Final[int] = ...
ALERT_TX_IDLE: Final[int] = ...
ALERT_TX_SUCCESS: Final[int] = ...
ALERT_BELOW_ERR_WARN: Final[int] = ...
ALERT_ERR_ACTIVE: Final[int] = ...
ALERT_RECOVERY_IN_PROGRESS: Final[int] = ...
ALERT_BUS_RECOVERED: Final[int] = ...
ALERT_ARB_LOST: Final[int] = ...
ALERT_ABOVE_ERR_WARN: Final[int] = ...
ALERT_BUS_ERROR: Final[int] = ...
ALERT_TX_FAILED: Final[int] = ...
ALERT_RX_QUEUE_FULL: Final[int] = ...
ALERT_ERR_PASS: Final[int] = ...
ALERT_BUS_OFF: Final[int] = ...

class CAN:
    """
    Construct a CAN object on the given bus.

    Usage::

        from machine import CAN
        can = CAN(0, mode=CAN.NORMAL, tx=4, rx=5, bitrate=500000)
    """
    def __init__(
        self,
        bus: int,
        *,
        mode: int = NORMAL,
        prescaler: int = 8,
        sjw: int = 3,
        bs1: int = 15,
        bs2: int = 4,
        auto_restart: bool = False,
        bitrate: int = 500000,
        extframe: bool = False,
        tx: int = 4,
        rx: int = 5,
        clkout: int = -1,
        bus_off: int = -1,
        tx_queue: int = 1,
        rx_queue: int = 1,
    ) -> None:
        """
        Initialize the CAN controller.

        :param bus: Must be 0 (only one controller supported).
        :param mode: One of the ``CAN.*`` mode constants.
        :param bitrate: CAN bitrate in bits per second (e.g. 500000 for 500kbps).
        :param extframe: Use extended 29-bit IDs.
        :param tx: TX pin number.
        :param rx: RX pin number.
        :param tx_queue: TX queue length.
        :param rx_queue: RX queue length.
        """
        ...

    def init(
        self,
        *,
        mode: int = NORMAL,
        prescaler: int = 8,
        sjw: int = 3,
        bs1: int = 15,
        bs2: int = 4,
        auto_restart: bool = False,
        bitrate: int = 500000,
        extframe: bool = False,
        tx: int = 4,
        rx: int = 5,
        clkout: int = -1,
        bus_off: int = -1,
        tx_queue: int = 1,
        rx_queue: int = 1,
    ) -> None:
        """
        Reconfigure and start the CAN controller. Must be called after ``deinit()``.
        """
        ...

    def deinit(self) -> None:
        """Stop and deinitialize the CAN controller."""
        ...

    def restart(self) -> None:
        """Restart the controller after bus-off state."""
        ...

    def state(self) -> int:
        """
        Return the current state of the controller.

        Possible values:
        - ``CAN.STOPPED``
        - ``CAN.ERROR_ACTIVE``
        - ``CAN.ERROR_WARNING``
        - ``CAN.ERROR_PASSIVE``
        - ``CAN.BUS_OFF``
        - ``CAN.RECOVERING``
        """
        ...

    def info(self, list: Optional[list] = None) -> dict:
        """
        Get diagnostic information about the CAN controller.

        Returns a dictionary with keys:
        - ``state``
        - ``msgs_to_tx``
        - ``msgs_to_rx``
        - ``tx_error_counter``
        - ``rx_error_counter``
        - ``tx_failed_count``
        - ``rx_missed_count``
        - ``arb_lost_count``
        - ``bus_error_count``
        """
        ...

    def any(self) -> bool:
        """Return ``True`` if any message is waiting in the RX queue."""
        ...

    def send(
        self,
        data: Sequence[int],
        id: int,
        *,
        timeout: int = 0,
        rtr: bool = False,
        extframe: bool = False,
    ) -> None:
        """
        Send a CAN message.

        :param data: List or tuple of up to 8 bytes.
        :param id: CAN message identifier (11-bit or 29-bit if ``extframe=True``).
        :param timeout: Timeout in milliseconds (0 = non-blocking).
        :param rtr: Request remote transmission.
        :param extframe: Use extended 29-bit ID.
        """
        ...

    def recv(
        self,
        list: Optional[list] = None,
        *,
        timeout: int = 5000,
    ) -> Tuple[int, bool, bool, bytes]:
        """
        Receive a CAN message.

        :param list: Optional list of length 4 to store result (reused for efficiency).
        :param timeout: Timeout in milliseconds.

        Returns tuple ``(id, extframe, rtr, data)`` or fills the provided list.
        """
        ...

    def set_filters(
        self,
        bank: int,
        mode: int,
        params: Sequence[int],
        *,
        rtr: bool = False,
        extframe: bool = False,
    ) -> None:
        """
        Configure hardware acceptance filters.

        :param bank: Filter bank (only 0 supported).
        :param mode: One of ``FILTER_RAW_SINGLE``, ``FILTER_RAW_DUAL``, ``FILTER_ADDRESS``.
        :param params: ``[id, mask]`` for raw modes.
        """
        ...

    def clearfilter(self) -> None:
        """Clear all filters (accept all messages)."""
        ...

    def irq_recv(self, callback: Optional[Callable[[int], None]]) -> None:
        """
        Set a callback for RX events.

        The callback receives an integer:
        - 0: message pending
        - 1: queue full
        - 2: queue overflow
        - 3: FIFO overrun
        """
        ...

    def irq_send(self, callback: Optional[Callable[[int], None]]) -> None:
        """
        Set a callback for TX events.

        The callback receives an integer:
        - 0: TX idle
        - 1: TX success
        - 2: TX failed
        - 3: TX retried
        """
        ...

    def clear_tx_queue(self) -> bool:
        """Clear the transmit queue. Returns ``True`` on success."""
        ...

    def clear_rx_queue(self) -> bool:
        """Clear the receive queue. Returns ``True`` on success."""
        ...

    def get_alerts(self) -> int:
        """Return current alert flags (bitmask of ``ALERT_*`` constants)."""
        ...

    # Constants
    class Mode:
        NORMAL: Final[int] = NORMAL
        SLEEP: Final[int] = SLEEP
        LOOPBACK: Final[int] = LOOPBACK
        SILENT: Final[int] = SILENT
        SILENT_LOOPBACK: Final[int] = SILENT_LOOPBACK
        LISTEN_ONLY: Final[int] = LISTEN_ONLY

    class State:
        STOPPED: Final[int] = ...
        ERROR_ACTIVE: Final[int] = ...
        ERROR_WARNING: Final[int] = ...
        ERROR_PASSIVE: Final[int] = ...
        BUS_OFF: Final[int] = ...
        RECOVERING: Final[int] = ...

    class MessageFlags:
        RTR: Final[int] = RTR
        EXTENDED_ID: Final[int] = EXTENDED_ID
        FD_F: Final[int] = FD_F
        BRS: Final[int] = BRS

    class RecvErrors:
        CRC: Final[int] = CRC
        FORM: Final[int] = FORM
        OVERRUN: Final[int] = OVERRUN
        ESI: Final[int] = ESI

    class SendErrors:
        ARB: Final[int] = ARB
        NACK: Final[int] = NACK
        ERR: Final[int] = ERR