import subprocess


class JIVLogic:
    def __init__(self):
        pass

    @staticmethod
    def get_studentmain_state():
        state = subprocess.run("tasklist|find /i \"studentmain.exe\"", shell=True).returncode
        print(not state)
        return not state
