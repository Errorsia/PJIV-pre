class RuntimeStatus:
    def __init__(self, logic):
        self.logic = logic
        self.pid = None
        self.current_process_name = None
        self.argv = None
        self.gui = None
        self.window_handle = None

        self.get_current_pid()
        self.get_current_process_name()
        self.get_argv()
        self.get_studentmain_info()

    def get_current_pid(self):
        self.pid = self.logic.get_current_pid()
        print(f'PID: {self.pid}')

    def get_current_process_name(self):
        self.current_process_name = self.logic.get_current_process_name()
        print(self.current_process_name)

    def get_argv(self):
        self.argv = self.logic.get_argv()
        print(self.argv)

    def get_studentmain_info(self):
        self.studentmain_directory = self.logic.studentmain_directory
        self.studentmain_path = self.logic.studentmain_path
        print(self.studentmain_path)

    def ui_launched(self, gui):
        self.gui = gui
        self.get_hwnd()

    def get_hwnd(self):
        self.window_handle = self.gui.winId()
