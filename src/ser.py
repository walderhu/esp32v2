import subprocess

python = "/home/des/miniforge3/envs/esp/bin/python"
webrepl = "/home/des/WORK/src/tools/webrepl_cli.py"
port =  "-p 1234 192.168.0.92"
pro_run = f"{python} {webrepl} {port} -e"

def init():
    command = (
        "/home/des/miniforge3/envs/esp/bin/python "
        "/home/des/WORK/src/tools/webrepl_cli.py "
        "-p 1234 192.168.0.92 -e "
        "\"import test2; "
        "m2=test2.Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90); "
        "m1=test2.Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60); "
        "p = test2.Portal(m2, m1); "
        "p.enable(True);\""
    )
    subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def exec(command):
    command = f'{pro_run} "{command}"'
    subprocess.run(command, shell=True, check=True)


init()
exec('p.x.freq = 30_000; p.y.freq = 30_000')
exec('p.x += 20')