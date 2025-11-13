# git clone --recursive https://github.com/micropython/micropython.git # done 
# git clone https://github.com/vostraga/micropython-esp32-twai.git # done

# Создаём каталоги
mkdir -p "$HOME/Documents/dev_iot/opt/upy/tools/esp_idf_v5.4.1/esp_tool"
cd "$HOME/Documents/dev_iot/opt/upy/tools/esp_idf_v5.4.1"
# Клонируем ESP-IDF
git clone -j8 -b v5.4.1 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
# Устанавливаем инструменты и активируем среду
./install.sh
. ./export.sh

# в ~/.bashrc можно добавить это
# unset IDF_TOOLS_PATH
# export IDF_PATH="$HOME/Documents/dev_iot/opt/upy/tools/esp_idf_v5.4.1/esp-idf"
# cd "$IDF_PATH"
# ./install.sh        # на всякий случай — чтобы убедиться, что всё скачано
# . ./export.sh       # активируем среду


cd ~/WORK/src/micropython
make -C mpy-cross  # Собираем кросс-компилятор для .py → .mpy
cd ports/esp32
rm -f *.lock
make submodules


mkdir -p ~/WORK/src/micropython/cmodules
cp -r ~/WORK/src/micropython-esp32-twai ~/WORK/src/micropython/cmodules/
# esptool.py chip_id
sed -i 's/mp_raise_\([A-Za-z_]*\)(\"\([^"]*\)\")/mp_raise_\1(MP_ERROR_TEXT("\2"))/g' /home/des/WORK/src/micropython-esp32-twai/src_can_v2/mod_can.c
sed -i 's/mp_raise_\([A-Za-z_]*\)(\"\([^"]*\)\")/mp_raise_\1(MP_ERROR_TEXT("\2"))/g' /home/des/WORK/src/micropython-esp32-twai/src_can_v2/mod_can.c

idf.py -D MICROPY_BOARD=ESP32_GENERIC \
       -D USER_C_MODULES="../../../../micropython-esp32-twai/src_can_v2/micropython.cmake" \
       -B build_ESP32_GENERIC build
# ожидается что файл в /home/des/WORK/src/micropython-esp32-twai/src_can_v2/micropython.cmake

# esptool.py chip_id
ls /dev/ttyUSB*

esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 \
    build_ESP32_GENERIC/bootloader/bootloader.bin \
    0x8000 build_ESP32_GENERIC/partition_table/partition-table.bin \
    0x10000 build_ESP32_GENERIC/micropython.bin



# mpremote connect /dev/ttyUSB0
# repl: 
# import CAN
# dev = CAN(0, tx=5, rx=4, mode=CAN.LOOPBACK, bitrate=50000)
# dev.any() # False


# https://chatgpt.com/c/6914e414-0efc-8331-bc66-68a1b8a54015










#############################
#############################
#############################

unset IDF_TOOLS_PATH
export IDF_PATH="$HOME/Documents/dev_iot/opt/upy/tools/esp_idf_v5.4.1/esp-idf"
cd "$IDF_PATH"
./install.sh        # на всякий случай — чтобы убедиться, что всё скачано
. ./export.sh       # активируем среду


if [[ "$CONDA_DEFAULT_ENV" != "esp" ]]; then
    conda deactivate
    conda activate esp
fi

if [[ ! -e /dev/ttyUSB0 ]]; then
    usbipd detach --busid 1-3
    usbipd bind --busid 1-3
    usbipd attach --wsl --busid 1-3

    for i in {1..100}; do
        if [[ -e /dev/ttyUSB0 ]]; then
            break
        fi
        sleep 0.01
    done

    if [[ ! -e /dev/ttyUSB0 ]]; then
        echo "❌ Ошибка: устройство /dev/ttyUSB0 так и не появилось."
        return 1
    fi
fi
cd ~/WORK/src/micropython/ports/esp32

ls /dev/ttyUSB*

esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 \
    build_ESP32_GENERIC/bootloader/bootloader.bin \
    0x8000 build_ESP32_GENERIC/partition_table/partition-table.bin \
    0x10000 build_ESP32_GENERIC/micropython.bin

