usbipd = "/mnt/c/Program Files/usbipd-win/usbipd.exe"
HOST = 192.168.0.92
# HOST = 192.168.0.129
# HOST = 192.168.1.5

PASS = 1234
# CLI = python tools/webrepl_cli.py
# CLI2 = python tools/cli.py
CLI = python tools/webrepl_client.py
CLI2 = python tools/webrepl_client.py


.PHONY: put get ls repl deploy flash

FILE := $(word 2, $(MAKECMDGOALS))

# default: deploy
# 	$(CLI) -p $(PASS) $(HOST);

default: repl
# 	@$(MAKE) --no-print-directory s
# 	@$(CLI) -p $(PASS) $(HOST) -e "import machine; machine.soft_reset()" | sed '1,3d; $$d'; sleep 1
# 	@$(MAKE) --no-print-directory run FILE="StepperPWM.py" | sed '1,3d; $$d'
# 	@$(MAKE) --no-print-directory repl
# 	sleep 10
# 	@$(MAKE) s

blink:
	echo $(CLI) -p $(PASS) $(HOST) -e "blink()"

r:
	@$(CLI) -p $(PASS) $(HOST) -e "__KEYBOARD_INTERRUPT__"  | sed '1,6d; $$d'
	@$(CLI) -p $(PASS) $(HOST) -e "import machine; machine.soft_reset()"
hr:
	$(CLI) -p $(PASS) $(HOST) -e "import machine; machine.reset()"

# put:
# 	@if [ -z "$(FILE)" ]; then \
# 		echo "Ошибка: укажите FILE=имя_файла"; \
# 		exit 1; \
# 	fi
# 	@echo "➡️  Uploading $(FILE) ..."
# 	@$(CLI) $(FILE) $(HOST):/$(FILE) -p $(PASS)

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
# 	else \
# 		echo "✅ $(FILE) is up to date"; \

get:
	@if [ -z "$(FILE)" ]; then \
		echo "Ошибка: укажите FILE=имя_файла"; \
		exit 1; \
	fi
	@echo "⬇️  Downloading $(FILE) ..."
	@$(CLI) $(HOST):/$(FILE) ./$(FILE) -p $(PASS)


HASHFILE := .hash.local
DEPLOYIGNORE := .hash.local .hash.local.new Makefile .vscode .gitignore .git trash server
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
	        $(CLI) -p $(PASS) $(HOST) -e "safe_mkdir('$$dir')"; \
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
	        $(CLI2) $$file $(HOST):/$$file -p $(PASS) > /dev/null 2>&1; \
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

# 	@# --- Визуализация дерева ---
# 	@$(MAKE) --no-print-directory tree

d: deploy

clean:
	@rm -rf .hash.*

clean-esp: clean
	mpremote run trash/delete_all.py
	mpremote cp config.json boot.py webrepl_cfg.py :
	mpremote run boot.py
	mpremote ls

tree:
	@$(CLI) -p $(PASS) $(HOST) -e "tree()" | sed '1,3d; $$d'

ls:
	@$(CLI) -p $(PASS) $(HOST) -e "ls()" | sed '1,3d; $$d'

rm:
	@if [ "$(FILE)" = "all" ]; then \
		$(CLI) -p $(PASS) $(HOST) -e 'delete_all()' | sed '1,3d; $$d';\
		@$(MAKE) --no-print-directory clean; \
	else \
		if [ -f $(HASHFILE) ]; then \
			grep -v "/$(FILE)" $(HASHFILE) > $(HASHFILE).tmp && mv $(HASHFILE).tmp $(HASHFILE); \
		fi; \
		$(CLI) -p $(PASS) $(HOST) -e 'rm("$(FILE)")' | sed '1,3d; $$d';\
	fi

boot:
	mpremote fs cp boot.py config.json webrepl_cfg.py :
	mpremote run boot.py


t: deploy
	@$(CLI) -p $(PASS) $(HOST) -e "import thermal_sensor; thermal_sensor.main()"
	@$(CLI) -p $(PASS) $(HOST)

s:
# 	@$(CLI) -p $(PASS) $(HOST) -e "__KEYBOARD_INTERRUPT__"
	@$(CLI) -p $(PASS) $(HOST) -e "__KEYBOARD_INTERRUPT__"  | sed '1,6d; $$d'

reset:
	@$(CLI) -p $(PASS) $(HOST) -e "import machine; machine.reset()"

kill: reset

run:
	@if [ -z "$(FILE)" ]; then \
		echo "Ошибка: укажите FILE=имя_файла"; \
		exit 1; \
	fi
	@$(MAKE) --no-print-directory put FILE="$(FILE)"
	@MODULE=$$(basename "$(FILE)" .py); \
	$(CLI) -p $(PASS) $(HOST) -e "import $$MODULE; $$MODULE.main()"

repl:
	@$(CLI) -p $(PASS) $(HOST);

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





FILE = serva2.py
MODULE = $(basename $(FILE))
gg:
# 	@$(CLI) -p $(PASS) $(HOST) -e "__KEYBOARD_INTERRUPT__"  | sed '1,6d; $$d'
	@$(CLI) -p $(PASS) $(HOST) -e "import machine; machine.soft_reset()"; sleep 1
	@$(MAKE) --no-print-directory put FILE="$(FILE)"
	@$(CLI) -p $(PASS) $(HOST) -e "import $(basename $(FILE)); asyncio.run($(basename $(FILE)).test())"
	@$(CLI) -p $(PASS) $(HOST);

