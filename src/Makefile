usbipd = "/mnt/c/Program Files/usbipd-win/usbipd.exe"
HOST = 192.168.0.129
PASS = 1234
CLI = python tools/webrepl_cli.py

.PHONY: put get ls repl deploy

FILE := $(word 2, $(MAKECMDGOALS))

default: deploy
	$(CLI) -p $(PASS) $(HOST); 
# 	@$(MAKE) repl

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

repl:
	@echo "🔌 Connecting to REPL..."
	@bash -c '\
	while true; do \
		echo "🔄  Deploying files before REPL..."; \
		$(MAKE) deploy; \
		echo "🔌 Connecting to REPL..."; \
		$(CLI) -p $(PASS) $(HOST) || true; \
		sleep 0.5; \
	done'



HASHFILE := .hashes.local
DEPLOYIGNORE := .hashes.local .hashes.local.new Makefile .vscode

deploy:
	@find . -type f $(foreach f,$(DEPLOYIGNORE),! -name '$(f)') | while read f; do \
		hash=$$(sha256sum "$$f" | cut -d' ' -f1); \
		echo "$$hash $$f"; \
	done > $(HASHFILE).new
	@while read line; do \
		hash=$$(echo $$line | cut -d' ' -f1); \
		file=$$(echo $$line | cut -d' ' -f2-); \
		old_hash=$$(grep -F "$$file" $(HASHFILE) 2>/dev/null | cut -d' ' -f1); \
		if [ "$$hash" != "$$old_hash" ]; then \
			echo "➡️  Uploading $$file -> /$$file ..."; \
			$(CLI) $$file $(HOST):/$$file -p $(PASS) > /dev/null 2>&1; \
		fi; \
	done < $(HASHFILE).new
	@mv $(HASHFILE).new $(HASHFILE)
	@echo "✅ Deploy complete."



attach:
	@PORT=$$(ls /dev/ttyUSB* 2>/dev/null | head -n1); \
	if [ -z "$$PORT" ]; then \
		${usbipd} bind --busid 1-3 >/dev/null 2>&1; \
		${usbipd} attach --wsl --busid 1-3 >/dev/null 2>&1 || true; \
	fi