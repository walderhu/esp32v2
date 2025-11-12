BOARD1 = 192.168.0.123
BOARD2 = 192.168.0.232
CLI = /home/des/miniforge3/envs/esp/bin/python /home/des/WORK/src/tools/webrepl_cli.py
PASS = 1234
FILE = TCP.py
MODULE = $(basename $(FILE))


# Сброс платы
reset:
	@$(CLI) -p $(PASS) $(BOARD2):/ -e "import machine; machine.soft_reset()" > /dev/null; sleep 0.5
	@$(CLI) -p $(PASS) $(BOARD1):/ -e "import machine; machine.soft_reset()" > /dev/null; sleep 0.5

# Основная сборка
main: reset
	$(CLI) -p $(PASS) $(FILE) $(BOARD1):/$(FILE) ; sleep 0.5
	$(CLI) -p $(PASS) $(FILE) $(BOARD2):/$(FILE) ; sleep 0.5

	$(CLI) -p $(PASS) $(BOARD1):/ -e "import $(MODULE)" --verbose --exit
	$(CLI) -p $(PASS) $(BOARD2):/ -e "import $(MODULE)" --verbose --exit

