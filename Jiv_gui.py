from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QGridLayout, QVBoxLayout

from Jiv_enmus import SuspendState


class MainWindow(QMainWindow):
    close_event = Signal()

    def __init__(self):
        super().__init__()
        self.initialization_window()

        self.adapter = None

        # Set central widget
        self.main_widget = MainWidget()
        self.setCentralWidget(self.main_widget)

    def closeEvent(self, event):
        self.close_event.emit()
        event.accept()

    def initialization_window(self):
        self.setWindowTitle("Jiv test")
        self.setMinimumSize(360, 480)
        self.resize(360, 480)

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def adapter_signal_connect(self, adapter):
        self.adapter = adapter
        self.main_widget.adapter_signal_connect(adapter)


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.studentmain_state = None
        self.kill_run = self.suspend_resume = None
        self.label_studentmain_state = None
        self.adapter = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        self.label_studentmain_state = QLabel()

        self.label_studentmain_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_studentmain_state.setStyleSheet("""
                                    background-color: #eeeeee; 
                                    border-radius: 10px;
                                    font-size: 24px;
                                    border: 3px solid #cccccc;
                                    color: #455A64;   
                                    """)
        self.label_studentmain_state.setText(f'Not detecting')
        # self.label_studentmain_state.setFixedHeight(100)

        button_layout = QGridLayout()

        self.kill_run = QPushButton("Kill studentmain")
        self.kill_run.clicked.connect(self.handle_studentmain)

        self.suspend_resume = QPushButton("Not detect")
        self.suspend_resume.clicked.connect(self.handle_studentmain_suspend)

        for i, btn in enumerate([self.kill_run, self.suspend_resume]):
            btn.setMinimumHeight(50)
            button_layout.addWidget(btn, i // 2, i % 2)
            btn.setStyleSheet("""
                        QPushButton {
                            font: 20px;
                            border: 2px solid #cccccc; 
                            border-radius: 8px;        
                            background-color: #eeeeee; 
                            color: #333;               
                        }
                        QPushButton:hover {
                            background-color: #dedede; 
                        }
                        QPushButton:pressed {
                            background-color: #dddddd; 
                        }
                    """)
            # cec2ff - b3b3f1 - dcb6d5 - cf8ba9 - b15e6c

        main_layout.addWidget(self.label_studentmain_state)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def adapter_signal_connect(self, adapter):
        self.adapter = adapter
        self.adapter.ui_change.connect(self.signal_handler)

    def signal_handler(self, name, value):
        print(f'Signal: {name}, {value}')
        match name:
            case 'MonitorAdapter':
                self.set_studentmain_state(value)
            case 'SuspendMonitorAdapter':
                self.set_studentmain_suspend_state(value)


    def set_studentmain_state(self, state):
        status = "not running" if not state else "running"
        self.label_studentmain_state.setText(f"Studentmain: {status}")
        self.studentmain_state = state
        
        if state:
            self.label_studentmain_state.setStyleSheet("""
                                        background-color: #FFE5E0; 
                                        border-radius: 10px;
                                        font-size: 24px;
                                        border: 3px solid #cccccc;
                                        color: #E66926;   
                                        """)
            self.kill_run.setText("Kill studentmain")
        else:
            self.label_studentmain_state.setStyleSheet("""
                                        background-color: #D3FDE3; 
                                        border-radius: 10px;
                                        font-size: 24px;
                                        border: 3px solid #cccccc;
                                        color: #16DC2D;   
                                        """)
            self.kill_run.setText("Run studentmain")


    def handle_studentmain(self):
        if self.studentmain_state:
            self.adapter.terminate_studentmain()
        else:
            self.adapter.start_studentmain()

    def set_studentmain_suspend_state(self, state):
        match state:
            case SuspendState.NOT_FOUND:
                self.suspend_resume.setText('Not found')
                self.suspend_resume.setDisabled(True)
            case SuspendState.RUNNING:
                self.suspend_resume.setText('Suspend')
                self.suspend_resume.setEnabled(True)
            case SuspendState.SUSPENDED:
                self.suspend_resume.setText('Resume')

    def handle_studentmain_suspend(self):
        self.adapter.suspend_resume_studentmain()

