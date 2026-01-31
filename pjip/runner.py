from PySide6.QtCore import QRunnable


class TerminatePIDTask(QRunnable):
    def __init__(self, logic, pids):
        super().__init__()
        self.logic = logic
        self.pids = pids

    def run(self):
        if not self.pids:
            print("PID not found")
            return
        for pid in self.pids:
            try:
                self.logic.terminate_process(pid)
            except RuntimeError as err:
                print(err)