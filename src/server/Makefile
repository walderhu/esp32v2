
all: 
	@fuser -k 8081/tcp || true
	@ngrok http 8081 > ngrok.log 2>&1 &
	@sleep 1
	@echo "▶ Запускаем сервер..."
	@python server.py


clean:
	@echo "🔹 Освобождаем порт 8081..."
	fuser -k 8081/tcp || true
	@sleep 1

# test:
# 	sudo ufw allow 8081/tcp
# 	ifconfig
# 	ip addr show eth0

# 	pip install pyngrok
# 	ngrok config add-authtoken 341CRwebVYMqowAL05AUXmqOMhD_5oZr9QAff1MsGWDCSuv7q
# 	ngrok http 8081
