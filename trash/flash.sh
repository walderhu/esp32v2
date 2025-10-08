usbipd detach --busid 1-3; usbipd bind --busid 1-3; usbipd attach --wsl --busid 1-3 
/home/des/miniforge3/bin/esptool --port /dev/ttyUSB0 erase_flash
/home/des/miniforge3/bin/esptool --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 /home/des/core/esp/recovery/fw.bin
