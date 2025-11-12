BOARD1 = 192.168.0.123
BOARD2 = 192.168.0.232
CLI = /home/des/miniforge3/envs/esp/bin/python /home/des/WORK/src/tools/webrepl_cli.py
PASS = 1234
# FILE = master.py
FILE = i2c.py

MODULE = $(basename $(FILE))

put:
	$(CLI) $(FILE) $(HOST):/$(FILE) -p $(PASS); 

reset:
	@$(CLI) -p $(PASS) $(BOARD2) -e "import machine; machine.soft_reset()" > /dev/null; sleep 0.5
	@$(CLI) -p $(PASS) $(BOARD1) -e "import machine; machine.soft_reset()" > /dev/null; sleep 0.5

main: reset
# 	$(MAKE) --no-print-directory put FILE="$(FILE)" HOST="$(BOARD2)"
# 	$(MAKE) --no-print-directory put FILE="$(FILE)" HOST="$(BOARD1)"
# 	$(CLI) -p $(PASS) $(BOARD1) -e "import $(MODULE); $(MODULE).bundle(board=1)" --verbose --exit
# 	$(CLI) -p $(PASS) $(BOARD2) -e "import $(MODULE); $(MODULE).bundle(board=2)" --verbose --exit
	$(CLI) -p $(PASS) $(BOARD1) -e "import $(MODULE)" --verbose --exit
	$(CLI) -p $(PASS) $(BOARD2) -e "import $(MODULE)" --verbose 

