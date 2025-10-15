
import os
def isdir(path):
    try: entries = os.listdir(path)
    except OSError: return False
    return True



print(isdir('tools'))