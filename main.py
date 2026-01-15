import sys

from PySide6.QtWidgets import QApplication

from pjip.core import logic, service
from pjip.config.runtime_status import RuntimeStatus
from pjip.gui import adapter
from pjip.gui import gui
from pjip.config import build_config


class JIVMain:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.logic = logic.JIVLogic(build_config)
        self.runtime_status = RuntimeStatus(self.logic)
        self.gui = gui.MainWindow()
        self.adapters = adapter.AdapterManager(self.logic, self.gui, self.runtime_status)
        self.gui.adapter_signal_connect(self.adapters)

        self.gui.show()

        self.runtime_status.ui_launched(self.gui)

        # self.logic.after_ui_launched(self.gui.winId())

        self.services = service.ServiceManager(self.logic, self.runtime_status)

        self.gui.close_event.connect(self.handle_close_event)

        # self.app.aboutToQuit.connect(self.handle_close_event)

        sys.exit(self.app.exec())

    def handle_close_event(self):
        self.adapters.quit_all()
        self.services.stop_all()


if __name__ == "__main__":
    JIVMain()
