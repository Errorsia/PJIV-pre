class RuntimeStatus:
    def __init__(self, logic):
        self.logic = logic
        self.pid = None

        self.get_current_pid()

    def get_current_pid(self):
        self.pid = self.logic.get_current_pid()
        print(self.pid)
