#!/usr/bin/env python3
import requests
import re
import os
import subprocess
import tempfile
from urllib.parse import urljoin

# Настройки
BOARD_URL = "https://micropython.org/download/ESP32_GENERIC/"
PORT = "/dev/ttyUSB0"
BAUD = "460800"

def get_latest_firmware_url():
    html = requests.get(BOARD_URL, timeout=10).text
    # Ищем все .bin файлы
    matches = re.findall(r'href="([^"]+\.bin)"', html)
    stable_bins = [m for m in matches if "preview" not in m]
    if not stable_bins:
        raise RuntimeError("❌ Не найдено стабильных .bin на странице.")
    latest_path = stable_bins[0]
    # Делаем абсолютный URL
    latest_url = urljoin(BOARD_URL, latest_path)
    return latest_url

def download_firmware(url):
    print(f"⬇️  Скачиваю прошивку:\n{url}")
    r = requests.get(url, stream=True, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"Ошибка HTTP {r.status_code}: {url}")
    filename = os.path.join(tempfile.gettempdir(), os.path.basename(url))
    with open(filename, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    print(f"✅ Сохранено во временный файл: {filename}")
    return filename


def flash_firmware(bin_path):
    print("⚙️  Стираю flash...")
    subprocess.run(["esptool.py", "--chip", "esp32", "--port", PORT, "erase_flash"], check=True)

    print("⚙️  Прошиваю чип (на 115200 бод)...")
    subprocess.run([
        "esptool.py", "--chip", "esp32", "--port", PORT,
        "--baud", "115200",
        "write_flash", "-z",
        "--flash_mode", "dio",
        "--flash_freq", "40m",
        "--flash_size", "4MB",
        "0x1000", bin_path
    ], check=True)

    print("🎉 Готово! Установлена последняя версия MicroPython.")


def main():
    print("🔍 Поиск последней прошивки MicroPython для ESP32...")
    url = get_latest_firmware_url()
    bin_path = download_firmware(url)
    flash_firmware(bin_path)

if __name__ == "__main__":
    main()
