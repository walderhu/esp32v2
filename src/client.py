# deploy_client.py
import socket
import os
import time
import hashlib

ESP_IP = "192.168.1.4"       # IP ESP
ESP_PORT = 2323              # порт деплой сервера
PROJECT_DIR = "/home/des/WORK/src"  # локальный проект
CHECK_INTERVAL = 1.0         # период проверки изменений в секундах

file_hashes = {}
deployed_files = set()

def get_file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def scan_files():
    """Возвращает список изменённых или новых файлов"""
    changed_files = []
    current_files = set()
    for root, dirs, files in os.walk(PROJECT_DIR):
        for f in files:
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, PROJECT_DIR)
            current_files.add(rel_path)
            h = get_file_hash(path)
            if rel_path not in file_hashes or file_hashes[rel_path] != h:
                file_hashes[rel_path] = h
                changed_files.append((rel_path, path))
    return changed_files, current_files

def send_command(cmd, content=b""):
    """Отправка команды на ESP"""
    with socket.create_connection((ESP_IP, ESP_PORT)) as s:
        s.sendall(cmd.encode("utf-8") + b"\n" + content)
        resp = s.recv(1024)
    return resp.decode().strip()

def deploy_file(rel_path, full_path):
    size = os.path.getsize(full_path)
    with open(full_path, "rb") as f:
        content = f.read()
    resp = send_command(f"PUT {rel_path} {size}", content)
    print(f"PUT {rel_path}: {resp}")
    deployed_files.add(rel_path)

def delete_file(rel_path):
    resp = send_command(f"DEL {rel_path}")
    print(f"DEL {rel_path}: {resp}")
    deployed_files.discard(rel_path)
    file_hashes.pop(rel_path, None)

def get_remote_files():
    """Получаем список файлов на ESP"""
    resp = send_command("LIST")
    files = resp.split(",") if resp else []
    return set(files)

def main_loop():
    print("Synchronizing project...")
    global deployed_files

    # 1. Сканируем локальные файлы
    _, current_files = scan_files()
    
    # 2. Получаем файлы на ESP
    remote_files = get_remote_files()

    # 3. Удаляем лишние файлы с ESP
    for rel_path in remote_files - current_files:
        print("Deleting on ESP:", rel_path)
        delete_file(rel_path)

    # 4. Деплой новых/изменённых файлов
    changed, _ = scan_files()
    for rel_path, full_path in changed:
        print("Deploying:", rel_path)
        deploy_file(rel_path, full_path)

    # 5. Начинаем слежение в цикле
    while True:
        changed, current_files = scan_files()
        for rel_path, full_path in changed:
            print("Deploying:", rel_path)
            deploy_file(rel_path, full_path)
        # Проверяем лишние файлы в процессе
        remote_files = get_remote_files()
        for rel_path in remote_files - current_files:
            print("Deleting on ESP:", rel_path)
            delete_file(rel_path)
        deployed_files = current_files.copy()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
