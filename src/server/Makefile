
all: clean
	@ngrok http 8081 > ngrok.log 2>&1 &
	@echo "▶ Запускаем сервер..."
# 	@cmd.exe /c start https://jazlynn-englacial-undoubtfully.ngrok-free.dev/
	@python server.py 


clean:
	@echo "🔹 Освобождаем порт 8081..."
	@fuser -k 8081/tcp 2>/dev/null || true
	@sleep 0.5
	@# Проверяем, остались ли процессы
	@while lsof -i tcp:8081 >/dev/null 2>&1; do \
		echo "Порт 8081 всё ещё занят, убиваем процесс..."; \
		pids=$$(lsof -ti tcp:8081); \
		[ -n "$$pids" ] && kill -9 $$pids; \
		sleep 0.2; \
	done
	@echo "✅ Порт 8081 свободен"

# test:
# 	sudo ufw allow 8081/tcp
# 	ifconfig
# 	ip addr show eth0

# 	pip install pyngrok
# 	ngrok config add-authtoken 341CRwebVYMqowAL05AUXmqOMhD_5oZr9QAff1MsGWDCSuv7q
# 	ngrok http 8081
