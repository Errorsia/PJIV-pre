from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QGridLayout, QVBoxLayout


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
        self.button1 = None
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

        self.button1 = QPushButton("Kill studentmain")
        self.button1.clicked.connect(self.handle_studentmain)

        button2 = QPushButton("Test")
        button2.clicked.connect(lambda: print('Test button'))

        for i, btn in enumerate([self.button1, button2]):
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
            self.button1.setText("Kill studentmain")
        else:
            self.label_studentmain_state.setStyleSheet("""
                                        background-color: #D3FDE3; 
                                        border-radius: 10px;
                                        font-size: 24px;
                                        border: 3px solid #cccccc;
                                        color: #16DC2D;   
                                        """)
            self.button1.setText("Run studentmain")


    def handle_studentmain(self):
        if self.studentmain_state:
            self.adapter.terminate_studentmain()
        else:
            self.adapter.start_studentmain()
