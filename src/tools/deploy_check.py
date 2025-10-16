import sys, json, subprocess

host, passwd, cli, local_file, remote_file, remote_hashfile = sys.argv[1:]

with open(remote_file) as f:
    try:
        remote = json.loads(f.read())
    except:
        remote = {}

local = {}
with open(local_file) as f:
    for line in f:
        file, hash = line.strip().split()
        local[file] = hash

for file, h in local.items():
    if remote.get(file) != h:
        print(f"Uploading {file} ...")
        subprocess.run([cli, file, f"{host}:/{file}", "-p", passwd])

# Обновляем хеши на ESP32
subprocess.run([cli, "-p", passwd, host, "-e",
                f'import ujson; f=open("{remote_hashfile}","w"); ujson.dump({local},f); f.close()'])
