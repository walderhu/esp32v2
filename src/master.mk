BOARD1 = 192.168.0.123
BOARD2 = 192.168.0.232
CLI = /home/des/miniforge3/envs/esp/bin/python /home/des/WORK/src/tools/webrepl_cli.py
PASS = 1234
FILE = master.py

MODULE = $(basename $(FILE))
HASHFILE = .hashes
put:
	@if [ -z "$(FILE)" ]; then \
		echo "Ошибка: укажите FILE=имя_файла"; \
		exit 1; \
	fi
	@if [ ! -f "$(HASHFILE)" ]; then touch $(HASHFILE); fi
	@hash=$$(sha256sum "$(FILE)" | cut -d' ' -f1); \
	old_hash=$$(grep -F "$(FILE)" $(HASHFILE) 2>/dev/null | cut -d' ' -f1); \
	if [ "$$hash" != "$$old_hash" ]; then \
		echo "➡️  Uploading $(FILE) to $(HOST)..."; \
		$(CLI) $(FILE) $(HOST):/$(FILE) -p $(PASS); \
		grep -v "$(FILE)" $(HASHFILE) > $(HASHFILE).tmp 2>/dev/null; \
		echo "$$hash $(FILE)" >> $(HASHFILE).tmp; \
		mv $(HASHFILE).tmp $(HASHFILE); \
	fi

reset:
	@$(CLI) -p $(PASS) $(BOARD1) -e "import machine; machine.soft_reset()" > /dev/null; sleep 0.5
	@$(CLI) -p $(PASS) $(BOARD2) -e "import machine; machine.soft_reset()" > /dev/null; sleep 0.5

main: reset
	$(MAKE) --no-print-directory put FILE="$(FILE)" HOST="$(BOARD1)"
	sleep 1
	$(MAKE) --no-print-directory put FILE="$(FILE)" HOST="$(BOARD2)"

# Запуск bundle на обеих платах
	$(CLI) -p $(PASS) $(BOARD1) -e "import $(MODULE); $(MODULE).bundle(board=1)" --verbose --exit
	sleep 1
	$(CLI) -p $(PASS) $(BOARD2) -e "import $(MODULE); $(MODULE).bundle(board=2)" --verbose --exit

