usbipd = "/mnt/c/Program Files/usbipd-win/usbipd.exe"
HOST = 192.168.0.123
# HOST = 192.168.0.92
PASS = 1234
CLI = python tools/webrepl_client.py
RUN := $(CLI) -p $(PASS) $(HOST) -e 
.PHONY: put get ls repl deploy flash server
FILE := $(word 2, $(MAKECMDGOALS))
default: repl

# blink:
# 	@$(RUN) "blink()" | sed '1,6d; $$d'

blink:
	$(RUN) "\
from machine import Pin; \
from time import sleep; \
led = Pin(2, Pin.OUT); \
for i in range(5): \
    led.value(1); sleep(0.1); \
    led.value(0); sleep(0.1)"


r:
	@$(RUN) "__KEYBOARD_INTERRUPT__"  | sed '1,6d; $$d'
	@$(RUN) "import machine; machine.soft_reset()"
hr:
	$(RUN) "import machine; machine.reset()"

put:
	@if [ -z "$(FILE)" ]; then \
		echo "Ошибка: укажите FILE=имя_файла"; \
		exit 1; \
	fi
	@if [ ! -f "$(HASHFILE)" ]; then touch $(HASHFILE); fi
	@hash=$$(sha256sum "$(FILE)" | cut -d' ' -f1); \
	old_hash=$$(grep -F "$(FILE)" $(HASHFILE) 2>/dev/null | cut -d' ' -f1); \
	if [ "$$hash" != "$$old_hash" ]; then \
		echo "➡️  Uploading $(FILE) ..."; \
		$(CLI) $(FILE) $(HOST):/$(FILE) -p $(PASS); \
		# Update hashfile \
		grep -v "$(FILE)" $(HASHFILE) > $(HASHFILE).tmp 2>/dev/null; \
		echo "$$hash $(FILE)" >> $(HASHFILE).tmp; \
		mv $(HASHFILE).tmp $(HASHFILE); \
	fi

get:
	@if [ -z "$(FILE)" ]; then \
		echo "Ошибка: укажите FILE=имя_файла"; \
		exit 1; \
	fi
	@echo "⬇️  Downloading $(FILE) ..."
	@$(CLI) $(HOST):/$(FILE) ./$(FILE) -p $(PASS)


HASHFILE := .hash.local
DEPLOYIGNORE := $(shell cat .deployignore | tr '\n' ' ')
DEPLOYIGNORE_FIND_EXCLUDE := $(foreach f,$(DEPLOYIGNORE),-name $(f) -o) -false

deploy:
	@if [ ! -f $(HASHFILE) ]; then \
		touch $(HASHFILE); \
	fi
	@# --- Создаем новые директории ---
	@existing_dirs=$$(awk '{print $$2}' $(HASHFILE) | xargs -n1 dirname | sort -u); \
	find . \( $(DEPLOYIGNORE_FIND_EXCLUDE) \) -prune -o -type d -print | while read dir; do \
	    if ! echo "$$existing_dirs" | grep -Fxq "$$dir"; then \
	        echo "📁 Creating $$dir ..."; \
	        $(RUN) "safe_mkdir('$$dir')"; \
	    fi; \
	done

	@# --- Загружаем измененные файлы ---
	@find . \( $(DEPLOYIGNORE_FIND_EXCLUDE) \) -prune -o -type f -print | while read file; do \
	    hash=$$(sha256sum "$$file" | cut -d' ' -f1); \
	    echo "$$hash $$file"; \
	done > $(HASHFILE).new

	@while read line; do \
	    hash=$$(echo $$line | cut -d' ' -f1); \
	    file=$$(echo $$line | cut -d' ' -f2-); \
	    old_hash=$$(grep -F "$$file" $(HASHFILE) 2>/dev/null | cut -d' ' -f1); \
	    if [ "$$hash" != "$$old_hash" ]; then \
	        echo "➡️  Uploading $$file -> /$$file ..."; \
	        $(CLI) $$file $(HOST):/$$file -p $(PASS) > /dev/null 2>&1; \
	    fi; \
	done < $(HASHFILE).new

	@# --- Удаляем файлы, которых больше нет на ПК ---
	@while read line; do \
	    file=$$(echo $$line | cut -d' ' -f2-); \
	    if [ ! -f "$$file" ]; then \
	        echo "🗑 Removing $$file from device ..."; \
	        $(MAKE) --no-print-directory rm FILE="$$file" || true; \
	    fi; \
	done < $(HASHFILE)

	@# --- Обновляем HASHFILE ---
	@mv $(HASHFILE).new $(HASHFILE)

d: deploy

clean:
	@rm -rf .hash.*
	@$(RUN) "delete_all()"
	@$(RUN) "import machine; machine.soft_reset()"; sleep 1
	@$(RUN) "tree()"

tree:
	@$(RUN) "tree()" | sed '1,3d; $$d'

ls:
	@$(RUN) "ls()" | sed '1,3d; $$d'

rm:
	@if [ "$(FILE)" = "all" ]; then \
		$(RUN) 'delete_all()' | sed '1,3d; $$d';\
		@$(MAKE) --no-print-directory clean; \
	else \
		if [ -f $(HASHFILE) ]; then \
			grep -v "/$(FILE)" $(HASHFILE) > $(HASHFILE).tmp && mv $(HASHFILE).tmp $(HASHFILE); \
		fi; \
		$(RUN) 'rm("$(FILE)")' | sed '1,3d; $$d';\
	fi

boot:
	mpremote fs cp boot.py config.json webrepl_cfg.py :
	mpremote run boot.py


t: deploy
	@$(RUN) "import thermal_sensor; thermal_sensor.main()"
	@$(CLI) -p $(PASS) $(HOST)

s:
# 	@$(RUN) "__KEYBOARD_INTERRUPT__"
	@$(RUN) "__KEYBOARD_INTERRUPT__"  | sed '1,6d; $$d'

reset:
	@$(RUN) "import machine; machine.reset()"

kill: reset

run:
	@if [ -z "$(FILE)" ]; then \
		echo "Ошибка: укажите FILE=имя_файла"; \
		exit 1; \
	fi
	@$(MAKE) --no-print-directory put FILE="$(FILE)"
	@MODULE=$$(basename "$(FILE)" .py); \
	$(RUN) "import $$MODULE; $$MODULE.main()"

repl:
	$(CLI) -p $(PASS) $(HOST);

clang:
	/home/des/miniforge3/envs/esp/bin/black "$(FILE)"



usbipd := "/mnt/c/Program Files/usbipd-win/usbipd.exe"
esptool="/home/des/miniforge3/bin/esptool"
bootfile="/home/des/WORK/.software/ESP32_GENERIC-20250911-v1.26.1.bin"
port="--port /dev/ttyUSB0"
bootfiles = boot.py config.json webrepl_cfg.py
src := /home/des/WORK/src
bootfiles := $(addprefix $(src)/, $(bootfiles))

flash:
	-$(usbipd) bind --busid 1-3
	-$(usbipd) attach --wsl --busid 1-3
	$(esptool) $(port) erase_flash
	$(esptool) --chip esp32 $(port) write_flash -z 0x1000 $(bootfile)
	mpremote cp $(bootfiles) :
	mpremote run $(src)/boot.py


server:
	@$(MAKE) --no-print-directory -C server

FILE = _tcp.py
MODULE = $(basename $(FILE))
gg:
	@$(RUN) "import machine; machine.soft_reset()" > /dev/null; sleep 0.5
	@$(MAKE) --no-print-directory put FILE="$(FILE)"
	-@$(RUN) "import $(basename $(FILE)); $(basename $(FILE)).test()" --verbose --exit
# 	-$(RUN) "import $(basename $(FILE)); $(basename $(FILE)).test()" --verbose 
