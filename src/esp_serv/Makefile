usbipd = "/mnt/c/Program Files/usbipd-win/usbipd.exe"
HOST = 192.168.0.123
PASS = 1234
CLI = /home/des/miniforge3/envs/esp/bin/python /home/des/WORK/src/tools/webrepl_client.py
RUN := $(CLI) -p $(PASS) $(HOST) -e 
.PHONY: put get ls repl deploy flash server
FILE := $(word 2, $(MAKECMDGOALS))
HASHFILE := .hash.db
default: repl
hash=$(sha256sum "$(FILE)" | cut -d' ' -f1)
old_hash=$(grep -F "$(FILE)" $(HASHFILE) 2>/dev/null | cut -d' ' -f1)

clean:
	@rm -rf .hash.*
	@$(RUN) "delete_all()"
	@$(RUN) "import machine; machine.soft_reset()"; sleep 1
	@$(RUN) "tree()"

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

s:
	@mpremote reset && echo "Success reboot ESP32/WROOM ✅" 

repl:
	@$(CLI) -p $(PASS) $(HOST);

FILE = html_serv.py
MODULE = $(basename $(FILE))
gg: s
	-@$(RUN) "import machine; machine.soft_reset()" > /dev/null; sleep 0.5
	-$(MAKE) --no-print-directory put FILE="$(FILE)"
	-$(RUN) "import $(basename $(FILE)); $(basename $(FILE)).test()" --verbose --exit
	-cmd.exe /c start "http://192.168.0.123/"