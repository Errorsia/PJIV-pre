import sys

from PySide6.QtWidgets import QApplication

from jiv.core import logic, service
from jiv.gui import adapter
from jiv.gui import gui
from jiv.config import build_config


class JIVMain:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.logic = logic.JIVLogic(build_config)
        self.gui = gui.MainWindow()
        self.adapters = adapter.AdapterManager(self.logic, self.gui)
        self.gui.adapter_signal_connect(self.adapters)

        self.gui.show()

        # self.logic.after_ui_launched(self.gui.winId())

        self.services = service.ServiceManager(self.logic, self.gui)

        self.gui.close_event.connect(self.handle_close_event)

        # self.app.aboutToQuit.connect(self.handle_close_event)

        sys.exit(self.app.exec())

    def handle_close_event(self):
        self.adapters.stop_all()
        self.services.stop_all()


if __name__ == "__main__":
    JIVMain()
