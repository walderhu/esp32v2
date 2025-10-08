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
deployed_dirs = set()

def get_file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def scan_files():
    """Возвращает список изменённых или новых файлов и текущие директории"""
    changed_files = []
    current_files = set()
    current_dirs = set()
    print("Scanning directory tree...")
    for root, dirs, files in os.walk(PROJECT_DIR):
        rel_root = os.path.relpath(root, PROJECT_DIR)
        if rel_root != '.':
            current_dirs.add(rel_root)
            print(f"Found dir: {rel_root}")
        for f in files:
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, PROJECT_DIR)
            current_files.add(rel_path)
            print(f"Found file: {rel_path}")
            h = get_file_hash(path)
            if rel_path not in file_hashes or file_hashes[rel_path] != h:
                file_hashes[rel_path] = h
                changed_files.append((rel_path, path))
    print(f"Total files scanned: {len(current_files)}, changed: {len(changed_files)}")
    return changed_files, current_files, current_dirs

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

def deploy_dir(rel_path):
    resp = send_command(f"MKDIR {rel_path}")
    print(f"MKDIR {rel_path}: {resp}")
    deployed_dirs.add(rel_path)

def delete_dir(rel_path):
    resp = send_command(f"DEL {rel_path}")
    print(f"DEL {rel_path}: {resp}")
    deployed_dirs.discard(rel_path)

def initial_sync():
    """Инициальный синк: деплоит всё дерево на старте, независимо от хэшей"""
    global deployed_files, deployed_dirs  # Declare globals at the start of the function
    print("Performing initial full sync...")
    # Сканируем всё
    all_files, current_files, current_dirs = scan_files()
    # Обновляем хэши для всех (даже если "не changed")
    for rel_path in current_files:
        full_path = os.path.join(PROJECT_DIR, rel_path)
        h = get_file_hash(full_path)
        file_hashes[rel_path] = h
    # Сначала создаём все директории
    all_dirs = current_dirs | deployed_dirs  # Now safe after global
    for rel_path in all_dirs:
        print("Initial deploying dir:", rel_path)
        deploy_dir(rel_path)
    # Деплоим все файлы (force all)
    for rel_path in current_files:
        full_path = os.path.join(PROJECT_DIR, rel_path)
        print("Initial deploying file:", rel_path)
        deploy_file(rel_path, full_path)
    # Удаляем лишние (если deployed больше current)
    to_delete_files = deployed_files - current_files
    for rel_path in to_delete_files:
        print("Initial deleting file:", rel_path)
        delete_file(rel_path)
    to_delete_dirs = deployed_dirs - current_dirs
    for rel_path in to_delete_dirs:
        print("Initial deleting dir:", rel_path)
        delete_dir(rel_path)
    # Обновляем tracked
    deployed_files = current_files.copy()
    deployed_dirs = current_dirs.copy()
    print("Initial sync completed.")

def main_loop():
    print("Watching for changes...")
    global deployed_files, deployed_dirs
    # Инициальный синк перед циклом
    initial_sync()
    while True:
        changed, current_files, current_dirs = scan_files()
        # Теперь только изменения (не all)
        # Сначала новые dirs
        new_dirs = current_dirs - deployed_dirs
        for rel_path in new_dirs:
            print("Deploying dir:", rel_path)
            deploy_dir(rel_path)
        # Изменённые файлы
        for rel_path, full_path in changed:
            print("Deploying file:", rel_path)
            deploy_file(rel_path, full_path)
        # Удаления файлов
        to_delete_files = deployed_files - current_files
        for rel_path in to_delete_files:
            print("Deleting file:", rel_path)
            delete_file(rel_path)
        # Удаления dirs (после файлов)
        to_delete_dirs = deployed_dirs - current_dirs
        for rel_path in to_delete_dirs:
            print("Deleting dir:", rel_path)
            delete_dir(rel_path)
        deployed_files = current_files.copy()
        deployed_dirs = current_dirs.copy()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()