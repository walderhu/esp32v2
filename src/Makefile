usbipd = "/mnt/c/Program Files/usbipd-win/usbipd.exe"
# HOST = 192.168.0.92
# HOST = 192.168.0.129
HOST = 192.168.1.5

PASS = 1234
# CLI = python tools/webrepl_cli.py
# CLI2 = python tools/cli.py
CLI = python tools/webrepl_client.py
CLI2 = python tools/webrepl_client.py


.PHONY: put get ls repl deploy

FILE := $(word 2, $(MAKECMDGOALS))

default: deploy
	@$(CLI) -p $(PASS) $(HOST); 
	
blink:
	echo $(CLI) -p $(PASS) $(HOST) -e "blink()"

repl: deploy
	$(CLI) -p $(PASS) $(HOST); 

r:
	$(CLI) -p $(PASS) $(HOST) -e "import machine; machine.reset()"

put:
	@if [ -z "$(FILE)" ]; then \
		echo "Ошибка: укажите FILE=имя_файла"; \
		exit 1; \
	fi
	@echo "➡️  Uploading $(FILE) ..."
	@$(CLI) $(FILE) $(HOST):/$(FILE) -p $(PASS)

get:
	@if [ -z "$(FILE)" ]; then \
		echo "Ошибка: укажите FILE=имя_файла"; \
		exit 1; \
	fi
	@echo "⬇️  Downloading $(FILE) ..."
	@$(CLI) $(HOST):/$(FILE) ./$(FILE) -p $(PASS)


HASHFILE := .hash.local
DEPLOYIGNORE := .hash.local .hash.local.new Makefile .vscode .gitignore .git trash server serva.py
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
	
	@# --- Визуализация дерева ---
	@$(MAKE) --no-print-directory tree

d: deploy


gg: deploy
	$(CLI) -p $(PASS) $(HOST) -e "import uasyncio as asyncio, StepperPWM; asyncio.run(StepperPWM.test())"
# 	$(CLI) -p $(PASS) $(HOST) -e "import uasyncio as asyncio, StepperPWM; asyncio.run(StepperPWM.main())"
# 	$(CLI) -p $(PASS) $(HOST);
	$(CLI) -p $(PASS) $(HOST) -e "import machine; machine.soft_reset()"

clean:
	@rm -rf .hash.local.new .hash.local

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


test:
	@echo "hello"
