#!/usr/bin/env mp

import sys; sys.path.append('/remote')

def include(name: str): 
    if not name.endswith('.py'): name = f'{name}.py'
    with open(f'/remote/{name}') as f: exec(f.read())  
