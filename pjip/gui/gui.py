from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMainWindow

from .main_widget import MainWidget


class MainWindow(QMainWindow):
    close_event = Signal()

    def __init__(self):
        super().__init__()
        self.initialization_window()

        # self.adapter = None

        # Set central widget
        self.main_widget = MainWidget()
        self.setCentralWidget(self.main_widget)

    def closeEvent(self, event):
        self.close_event.emit()
        event.accept()

    def initialization_window(self):
        self.setWindowTitle("Jiv test")
        self.setMinimumSize(366, 488)
        self.resize(366, 488)

        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def adapter_signal_connect(self, adapter):
        # self.adapter = adapter
        self.main_widget.adapter_signal_connect(adapter)
