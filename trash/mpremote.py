#!/usr/bin/env python3
import sys
from i2c.webrepl_cli import main as webrepl_main

DEFAULT_HOST = "192.168.0.248"
DEFAULT_PORT = 1234

args = sys.argv[1:]

host_set = any(arg for arg in args if not arg.startswith("-") and not arg in ["ls", "cp", "cat", "rm", "mkdir", "rmdir", "repl"])
port_set = any(arg.startswith("-p") for arg in args)

if not host_set:
    args.append(DEFAULT_HOST)

if not port_set:
    args.insert(0, "-p")
    args.insert(1, str(DEFAULT_PORT))

webrepl_main(args)
