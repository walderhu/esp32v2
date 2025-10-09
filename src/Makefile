HOST = 192.168.0.232
PASS = 1234
CLI = python tools/webrepl_cli.py

.PHONY: put get ls repl deploy

FILE := $(word 2, $(MAKECMDGOALS))


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
	@$(CLI) -p $(PASS) $(HOST)

deploy:
	@echo "🚀 Deploying *.py files..."
	@for f in *.py; do \
		[ -f "$$f" ] || continue; \
		echo "➡️ Uploading $$f ..."; \
		$(CLI) $$f $(HOST):/$$f -p $(PASS); \
	done
	@echo "✅ Deploy complete."
