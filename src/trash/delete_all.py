import os

except_files = ['config.json', 'boot.py', 'webrepl_cfg.py']
def delete_all(path="/"):
    for filename in os.listdir(path):
        filepath = path + filename
        try:
            if filepath in except_files: continue
            if 'stat' in dir(os):
                mode = os.stat(filepath)[0]
                if mode & 0x4000:  # папка (директория)
                    delete_all(filepath + "/")
                    os.rmdir(filepath)
                    print("Deleted directory:", filepath)
                else:
                    os.remove(filepath)
                    print("Deleted file:", filepath)
            else:
                os.remove(filepath)
                print("Deleted file:", filepath)
        except Exception as e:
            print("Error deleting", filepath, ":", e)

delete_all()
