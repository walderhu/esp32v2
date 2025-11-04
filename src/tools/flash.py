#!/usr/bin/env python3
"""
Flash MicroPython на ESP32 с автоопределением порта и последней стабильной прошивкой.
"""

import requests
import re
import os
import subprocess
import tempfile
import sys
import serial.tools.list_ports
from urllib.parse import urljoin

# === НАСТРОЙКИ ===
BOARD_URL = "https://micropython.org/download/ESP32_GENERIC/"
BAUD_ERASE = "460800"
BAUD_FLASH = "115200"
FLASH_MODE = "dio"
FLASH_FREQ = "40m"
FLASH_SIZE = "4MB"
ADDRESS = "0x1000"


def get_latest_firmware_url():
    print("Поиск последней прошивки MicroPython для ESP32...")
    try:
        html = requests.get(BOARD_URL, timeout=15).text
    except requests.RequestException as e:
        print(f"Ошибка подключения к {BOARD_URL}: {e}")
        sys.exit(1)

    # Ищем .bin файлы, исключаем preview
    matches = re.findall(r'href="([^"]+\.bin)"', html)
    stable_bins = [m for m in matches if "preview" not in m and "v1." in m]
    if not stable_bins:
        print("Не найдено стабильных .bin файлов.")
        sys.exit(1)

    latest_path = stable_bins[0]
    latest_url = urljoin(BOARD_URL, latest_path)
    print(f"Найдена прошивка: {latest_path}")
    return latest_url


def download_firmware(url):
    print(f"Скачиваю:\n{url}")
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Ошибка скачивания: {e}")
        sys.exit(1)

    filename = os.path.join(tempfile.gettempdir(), os.path.basename(url))
    with open(filename, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    print(f"Сохранено: {filename}")
    return filename


def find_esp_port():
    print("Ищу подключённый ESP32...")
    ports = serial.tools.list_ports.comports()
    esp_ports = []

    for p in ports:
        desc = p.description.lower()
        dev = p.device
        if "cp210" in desc or "ch340" in desc or "esp" in desc or "silicon" in desc:
            esp_ports.append(p)

    if not esp_ports:
        print("ESP32 не найден!")
        print("Подключи плату и проверь:")
        print("  ls /dev/tty*")
        print("  dmesg | tail -10")
        sys.exit(1)

    if len(esp_ports) > 1:
        print("Найдено несколько портов:")
        for i, p in enumerate(esp_ports):
            print(f"  [{i}] {p.device} — {p.description}")
        choice = input(f"Выбери порт [0-{len(esp_ports)-1}]: ")
        try:
            return esp_ports[int(choice)].device
        except:
            print("Неверный выбор.")
            sys.exit(1)

    port = esp_ports[0].device
    print(f"Использую порт: {port}")
    return port


def check_port_access(port):
    if not os.access(port, os.R_OK | os.W_OK):
        print(f"Нет доступа к {port}")
        print("Добавь себя в группу dialout:")
        print("  sudo usermod -a -G dialout $USER")
        print("  → Перезайди в систему")
        sys.exit(1)


def flash_firmware(bin_path, port):
    print("Стираю flash...")
    try:
        subprocess.run([
            "esptool.py", "--chip", "esp32", "--port", port,
            "--baud", BAUD_ERASE, "erase_flash"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при стирании flash: {e}")
        print("Проверь:")
        print("  - Плата подключена?")
        print("  - Порт не занят? (закрой minicom, screen, VS Code)")
        print("  - Права на порт? (группа dialout)")
        sys.exit(1)

    print("Прошиваю MicroPython...")
    try:
        subprocess.run([
            "esptool.py", "--chip", "esp32", "--port", port,
            "--baud", BAUD_FLASH,
            "write_flash", "-z",
            "--flash_mode", FLASH_MODE,
            "--flash_freq", FLASH_FREQ,
            "--flash_size", FLASH_SIZE,
            ADDRESS, bin_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка прошивки: {e}")
        sys.exit(1)

    print("Готово! MicroPython установлен.")
    print(f"Подключись: screen {port} 115200")


def main():
    url = get_latest_firmware_url()
    bin_path = download_firmware(url)
    port = find_esp_port()
    check_port_access(port)
    flash_firmware(bin_path, port)


if __name__ == "__main__":
    # Убедись, что esptool установлен
    try:
        subprocess.run(["esptool.py", "--help"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("esptool.py не найден!")
        print("Установи: pip install esptool")
        sys.exit(1)

    main()