from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout, \
    QSizePolicy, QStackedWidget, QLayout, QButtonGroup

from Jiv_enmus import SuspendState, UpdateState


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

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def adapter_signal_connect(self, adapter):
        # self.adapter = adapter
        self.main_widget.adapter_signal_connect(adapter)


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.adapter = None
        self.live_frame = None

        self.TASKBAR_BTN_HEIGHT = 32
        self.TASKBAR_BTN_WIDTH = int(self.TASKBAR_BTN_HEIGHT * 2)
        self.SPACING = 4

        self.SIDEBAR_HEIGHT = self.TASKBAR_BTN_HEIGHT + self.SPACING * 2  # Fixed height

        self.sidebar = self.sidebar_layout = None
        self.sidebar_tabs = self.sidebar_button_group = None

        self.pages = None
        self.toolkit_page = self.about_page = self.settings_page = self.update_page = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 4, 5, 5)
        main_layout.setSpacing(2)

        # Sidebar
        self.sidebar = QWidget()
        self.sidebar_layout = QHBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(self.SPACING, self.SPACING, self.SPACING, self.SPACING)
        # self.sidebar_layout.setSpacing(self.SPACING)

        self.sidebar_tabs = [
            "Tools",
            "Settings",
            "Updates",
            "Info"
        ]

        self.sidebar_button_group = QButtonGroup(self)
        self.sidebar_button_group.setExclusive(True)

        base_btn_style = f"""
            QPushButton {{
                background-color: #e6e6e6;
                border-radius: {self.TASKBAR_BTN_HEIGHT // 4}px; 
                padding: 0px;
                font-weight: bold; 
            }}
            QPushButton:hover {{
                background-color: #dcdcdc;
            }}
            QPushButton:pressed {{
                background-color: #cbcbcb;
            }}
            QPushButton:checked {{
                background-color: #4a90e2;
                color: white;
            }}
        """

        sidebar_container = QWidget()
        sidebar_container_layout = QHBoxLayout(sidebar_container)
        sidebar_container_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_container_layout.setSpacing(self.SPACING)

        sidebar_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sidebar_container_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        for index, name in enumerate(self.sidebar_tabs):
            btn = QPushButton(name)
            btn.setFixedSize(self.TASKBAR_BTN_WIDTH, self.TASKBAR_BTN_HEIGHT)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(base_btn_style)
            btn.setToolTip(name)
            self.sidebar_button_group.addButton(btn, index)
            sidebar_container_layout.addWidget(btn)

        self.sidebar_button_group.buttons()[0].setChecked(True)

        self.sidebar_layout.addWidget(sidebar_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Issue in placing sidebar buttons in center
        # self.sidebar_layout.addStretch()

        self.sidebar.setFixedHeight(self.SIDEBAR_HEIGHT)
        self.sidebar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.sidebar.setObjectName("sidebar")

        self.live_frame = QWidget()
        self.live_frame.setObjectName("live_frame")

        self.live_frame.setStyleSheet("""
            #live_frame {
                background-color: #eeeeee; 
                border-radius: 10px;
                font-size: 24px;
                border: 4px solid #cccccc;
                color: #455A64;   
            }
        """)

        live_frame_layout = QVBoxLayout(self.live_frame)
        live_frame_layout.setContentsMargins(5, 5, 5, 5)
        live_frame_layout.setSpacing(5)

        # Stack pages
        self.pages = QStackedWidget()
        self.toolkit_page = ToolkitPage()
        self.pages.addWidget(self.toolkit_page)
        self.settings_page = PageUpdating()
        self.pages.addWidget(self.settings_page)
        self.update_page = UpdatePage()
        self.pages.addWidget(self.update_page)
        self.about_page = PageUpdating()
        self.pages.addWidget(self.about_page)

        self.sidebar_button_group.idClicked.connect(self.pages.setCurrentIndex)

        live_frame_layout.addWidget(self.pages)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.live_frame, 1)

        self.setLayout(main_layout)

    def adapter_signal_connect(self, adapter):
        self.adapter = adapter
        self.adapter.ui_change.connect(self.signal_handler)

        self.toolkit_page.set_adapter(self.adapter)
        self.update_page.set_adapter(self.adapter)

    def signal_handler(self, name, value):
        print(f'Signal in main widget: {name}, {value}')
        match name:
            case 'MonitorAdapter':
                self.toolkit_page.ui_change.emit(name, value)
                self.live_frame_change(value)
            case 'SuspendMonitorAdapter':
                self.toolkit_page.ui_change.emit(name, value)
            case 'UpdateAdapter':
                self.update_page.ui_change.emit(name, value)

    def live_frame_change(self, studentmain_running_state):
        if studentmain_running_state:
            self.live_frame.setStyleSheet("""
                #live_frame {
                    background-color: #eeeeee; 
                    border-radius: 10px;
                    font-size: 24px;
                    /*border: 4px solid #E66926; */
                    border: 4px solid #E6A56E;
                    color: #455A64;   
                }
            """)
        else:
            self.live_frame.setStyleSheet("""
                #live_frame {
                    background-color: #eeeeee; 
                    border-radius: 10px;
                    font-size: 24px;
                    border: 4px solid #3DC766;
                    color: #455A64;   
                }
            """)


class ToolkitPage(QWidget):
    ui_change = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.studentmain_state = None
        self.kill_run_btn = self.suspend_resume_btn = self.run_taskmgr_btn = self.clean_ifeo_debuggers_btn = None
        self.label_studentmain_state = None
        self.adapter = None
        self.init_ui()

        self.signal_connect()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(3, 3, 3, 3)
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

        self.kill_run_btn = QPushButton("Kill studentmain")
        self.kill_run_btn.clicked.connect(self.handle_studentmain)

        self.suspend_resume_btn = QPushButton("Not detect")
        self.suspend_resume_btn.clicked.connect(self.handle_studentmain_suspend)

        self.run_taskmgr_btn = QPushButton("Run Taskmgr")
        self.run_taskmgr_btn.clicked.connect(self.run_taskmgr)


        self.clean_ifeo_debuggers_btn = QPushButton("Clean IFEO")
        self.clean_ifeo_debuggers_btn.clicked.connect(self.clean_ifeo_debuggers)

        # test_button = QPushButton("Test")
        # test_button.clicked.connect(lambda: print('Test button triggered'))

        for i, btn in enumerate([self.kill_run_btn, self.suspend_resume_btn, self.run_taskmgr_btn, self.clean_ifeo_debuggers_btn]):
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
                            background-color: #cdcdcd; 
                        }
                    """)
            # cec2ff - b3b3f1 - dcb6d5 - cf8ba9 - b15e6c

        main_layout.addWidget(self.label_studentmain_state)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def signal_connect(self):
        self.ui_change.connect(self.signal_handler)

    def signal_handler(self, name, value):
        match name:
            case 'MonitorAdapter':
                self.set_studentmain_state(value)
            case 'SuspendMonitorAdapter':
                self.set_studentmain_suspend_state(value)

    def set_adapter(self, adapter):
        self.adapter = adapter

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
            self.kill_run_btn.setText("Kill studentmain")
        else:
            self.label_studentmain_state.setStyleSheet("""
                                        background-color: #D3FDE3; 
                                        border-radius: 10px;
                                        font-size: 24px;
                                        border: 3px solid #cccccc;
                                        /* color: #16DC2D;   */
                                        color: green;
                                        """)
            self.kill_run_btn.setText("Run studentmain")

    def handle_studentmain(self):
        if self.studentmain_state:
            self.adapter.terminate_studentmain()
        else:
            self.adapter.start_studentmain()

    def set_studentmain_suspend_state(self, state):
        match state:
            case SuspendState.NOT_FOUND:
                self.suspend_resume_btn.setText('Not found')
                self.suspend_resume_btn.setDisabled(True)
            case SuspendState.RUNNING:
                self.suspend_resume_btn.setText('Suspend')
                self.suspend_resume_btn.setEnabled(True)
            case SuspendState.SUSPENDED:
                self.suspend_resume_btn.setText('Resume')

    def handle_studentmain_suspend(self):
        self.adapter.suspend_resume_studentmain()

    def run_taskmgr(self):
        self.run_taskmgr_btn.setDisabled(True)
        self.adapter.run_taskmgr()
        self.run_taskmgr_btn.setEnabled(True)

    def clean_ifeo_debuggers(self):
        self.adapter.clean_ifeo_debuggers()


class UpdatePage(QWidget):
    ui_change = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.studentmain_state = None
        self.update_state_label = None
        self.current_version_label = None
        self.get_update_btn = None
        self.adapter = None
        self.current_version = None

        self.init_ui()

        self.signal_connect()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.setSpacing(5)

        self.current_version_label = QLabel()
        self.current_version_label.setWordWrap(True)

        self.current_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_version_label.setStyleSheet("""
                                    background-color: #eeeeee; 
                                    border-radius: 10px;
                                    font-size: 24px;
                                    border: 3px solid #cccccc;
                                    color: #455A64;   
                                    """)
        self.current_version_label.setText(f'Current version: N / a')
        self.current_version_label.setFixedHeight(50)

        self.update_state_label = QLabel()
        self.update_state_label.setWordWrap(True)

        self.update_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_state_label.setStyleSheet("""
                                    background-color: #eeeeee; 
                                    border-radius: 10px;
                                    font-size: 24px;
                                    border: 3px solid #cccccc;
                                    color: #455A64;   
                                    """)
        self.update_state_label.setText(f'Getting updates')
        # self.update_state_label.setFixedHeight(100)

        button_layout = QGridLayout()

        self.get_update_btn = QPushButton("Get updates")
        self.get_update_btn.clicked.connect(self.get_update)

        for i, btn in enumerate([self.get_update_btn]):
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
                            background-color: #cdcdcd; 
                        }
                    """)

        main_layout.addWidget(self.current_version_label)
        main_layout.addWidget(self.update_state_label)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def signal_connect(self):
        self.ui_change.connect(self.signal_handler)

    def signal_handler(self, name, value):
        # print(f'Signal in toolkit page: {name}, {value}')
        match name:
            case 'UpdateAdapter':
                self.update_update_label(value)

    def set_adapter(self, adapter):
        self.adapter = adapter

        self.current_version = self.adapter.get_current_version()
        self.current_version_label.setText(f'Current version: {self.current_version}')

    def get_update(self):
        self.update_state_label.setText(f'Getting updates')

        self.adapter.get_update()

    def update_update_label(self, state_package):
        state, content = state_package

        if state == UpdateState.FIND_LATEST:
            self.update_state_label.setText(f'A new version is available: {content}')
        elif state == UpdateState.IS_LATEST:
            self.update_state_label.setText('You are already using the latest version')
        elif state == UpdateState.NOT_FOUND:
            self.update_state_label.setText('No updates found')
        elif state == UpdateState.ERROR:
            self.update_state_label.setText('An error has occurred while checking for updates.')
        else:
            self.update_state_label.setText("Unexpected state. Please contact the developers.")


class PageUpdating(QWidget):
    def __init__(self):
        super().__init__()
        self.updating_label = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.setSpacing(5)

        self.updating_label = QLabel()
        self.updating_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.updating_label.setText('Page Updating')
        self.updating_label.setStyleSheet("""
                                        background-color: #efefef; 
                                        /* border-radius: 10px; */
                                        font-size: 24px;
                                        /* border: 3px solid #cccccc; */
                                        /* border: 1px solid #bbbbbb; */
                                        color: green; 
                                        font-weight: bold; 
                                        """)

        main_layout.addWidget(self.updating_label)
        self.setLayout(main_layout)
