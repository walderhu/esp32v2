usbipd = "/mnt/c/Program Files/usbipd-win/usbipd.exe"
# HOST = 192.168.0.92
HOST = 192.168.0.129
PASS = 1234
CLI = python tools/webrepl_cli.py

.PHONY: put get ls repl deploy

FILE := $(word 2, $(MAKECMDGOALS))

default: deploy
	$(CLI) -p $(PASS) $(HOST); 
	
# 	$(CLI) -p $(PASS) $(HOST) -e "import uasyncio as asyncio, StepperPWM; asyncio.run(StepperPWM.main())"
#   python webrepl_cli.py -p 1234 192.168.0.92 -e "import uasyncio as asyncio; [t.cancel() for t in asyncio.all_tasks(asyncio.get_event_loop())]; asyncio.get_event_loop().stop()"
# 	python webrepl_cli.py -p 1234 192.168.0.92 -e "import uasyncio; uasyncio.get_event_loop().stop()"


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
DEPLOYIGNORE := .hash.local .hash.local.new Makefile .vscode .gitignore .git trash server
DEPLOYIGNORE_FIND_EXCLUDE := $(foreach f,$(DEPLOYIGNORE),-name $(f) -o) -false

# deploy:
# 	@find . \( $(DEPLOYIGNORE_FIND_EXCLUDE) \) -prune -o -type f -print | while read f; do \
# 		hash=$$(sha256sum "$$f" | cut -d' ' -f1); \
# 		echo "$$hash $$f"; \
# 	done > $(HASHFILE).new
# 	@while read line; do \
# 		hash=$$(echo $$line | cut -d' ' -f1); \
# 		file=$$(echo $$line | cut -d' ' -f2-); \
# 		old_hash=$$(grep -F "$$file" $(HASHFILE) 2>/dev/null | cut -d' ' -f1); \
# 		if [ "$$hash" != "$$old_hash" ]; then \
# 			echo "➡️  Uploading $$file -> /$$file ..."; \
# 			python tools/cli.py $$file $(HOST):/$$file -p $(PASS) > /dev/null 2>&1; \
# 		fi; \
# 	done < $(HASHFILE).new
# 	@mv $(HASHFILE).new $(HASHFILE)
# # 	@echo "✅ Deploy complete."
# 	@$(MAKE) --no-print-directory tree

deploy:
	@find . \( $(DEPLOYIGNORE_FIND_EXCLUDE) \) -prune -o -type d -print | while read dir; do \
		$(CLI) -p $(PASS) $(HOST) -e "safe_mkdir('$$dir')"; \
	done
	@find . \( $(DEPLOYIGNORE_FIND_EXCLUDE) \) -prune -o -type f -print | while read file; do \
		hash=$$(sha256sum "$$file" | cut -d' ' -f1); \
		echo "$$hash $$file"; \
	done > $(HASHFILE).new
	@while read line; do \
		hash=$$(echo $$line | cut -d' ' -f1); \
		file=$$(echo $$line | cut -d' ' -f2-); \
		old_hash=$$(grep -F "$$file" $(HASHFILE) 2>/dev/null | cut -d' ' -f1); \
		if [ "$$hash" != "$$old_hash" ]; then \
			echo "➡️  Uploading $$file -> /$$file ..."; \
			python tools/cli.py $$file $(HOST):/$$file -p $(PASS) > /dev/null 2>&1; \
		fi; \
	done < $(HASHFILE).new
	@mv $(HASHFILE).new $(HASHFILE)
	@$(MAKE) --no-print-directory tree
	@ rm -rf .hash.local.tmp





gg: deploy
	$(CLI) -p $(PASS) $(HOST) -e "import uasyncio as asyncio, StepperPWM; asyncio.run(StepperPWM.main())"
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
# 	@$(CLI) -p $(PASS) $(HOST) -e "tree()"
	@$(CLI) -p $(PASS) $(HOST) -e "tree()" | sed '1,3d; $$d'


ls:
	@$(CLI) -p $(PASS) $(HOST) -e "ls()"

rm:
	@if [ "$(FILE)" = "all" ]; then \
		$(CLI) -p $(PASS) $(HOST) -e 'delete_all()'; \
		$(MAKE) --no-print-directory clean; \
	else \
		if [ -f $(HASHFILE) ]; then \
			grep -v "/$(FILE)" $(HASHFILE) > $(HASHFILE).tmp && mv $(HASHFILE).tmp $(HASHFILE); \
		fi; \
		$(CLI) -p $(PASS) $(HOST) -e 'rm("$(FILE)")'; \
	fi
	$(MAKE) --no-print-directory tree; \


test:
	$(CLI) -p $(PASS) $(HOST) -e "safe_mkdir('tools')"; 
	@$(CLI) -p $(PASS) $(HOST) -e "tree()"


boot:
	mpremote fs cp boot.py config.json webrepl_cfg.py :
	mpremote run boot.py
