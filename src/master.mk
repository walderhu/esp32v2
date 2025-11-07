BOARD1 = 192.168.0.123
BOARD2 = 192.168.0.232
CLI = /home/des/miniforge3/envs/esp/bin/python /home/des/WORK/src/tools/webrepl_cli.py
PASS = 1234
FILE = master.py

MODULE = $(basename $(FILE))
HASHFILE = .hashes
put:
	hash=$$(sha256sum "$(FILE)" | cut -d' ' -f1); \
	old_hash=$$(grep -F "$(FILE) $(HOST)" $(HASHFILE) 2>/dev/null | cut -d' ' -f3); \
	if [ "$$hash" != "$$old_hash" ]; then \
		echo "➡️  Uploading $(FILE) to $(HOST)..."; \
		$(CLI) $(FILE) $(HOST):/$(FILE) -p $(PASS); \
		grep -v "$(FILE) $(HOST)" $(HASHFILE) > $(HASHFILE).tmp 2>/dev/null; \
		echo "$(FILE) $(HOST) $$hash" >> $(HASHFILE).tmp; \
		mv $(HASHFILE).tmp $(HASHFILE); \
	fi


reset:
	@$(CLI) -p $(PASS) $(BOARD1) -e "import machine; machine.soft_reset()" > /dev/null; sleep 0.5
	@$(CLI) -p $(PASS) $(BOARD2) -e "import machine; machine.soft_reset()" > /dev/null; sleep 0.5

main: reset
	$(MAKE) --no-print-directory put FILE="$(FILE)" HOST="$(BOARD1)"
	$(MAKE) --no-print-directory put FILE="$(FILE)" HOST="$(BOARD2)"
	$(CLI) -p $(PASS) $(BOARD1) -e "import $(MODULE); $(MODULE).bundle(board=1)" --verbose --exit
	$(CLI) -p $(PASS) $(BOARD2) -e "import $(MODULE); $(MODULE).bundle(board=2)" --verbose --exit

