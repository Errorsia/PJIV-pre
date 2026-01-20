from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout, \
    QSizePolicy, QStackedWidget, QLayout, QButtonGroup, QRadioButton, QLineEdit

from pjip.core.enums import SuspendState, UpdateState


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

        self.pages = self.stack_pages = None
        self.tool_page = self.functions_page = self.about_page = self.settings_page = self.update_page = None

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

        # Init stack_pages
        self.tool_page = ToolPage()
        self.functions_page = FunctionsPage()
        self.settings_page = SettingsPage()
        self.update_page = UpdatePage()
        self.about_page = AboutPage()

        self.pages = [
            self.tool_page,
            self.functions_page,
            self.settings_page,
            self.update_page,
            # self.about_page,
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

        for index, widget in enumerate(self.pages):
            page_name = widget.page_name
            btn = QPushButton(page_name)
            btn.setFixedSize(self.TASKBAR_BTN_WIDTH, self.TASKBAR_BTN_HEIGHT)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(base_btn_style)
            btn.setToolTip(page_name)
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

        # Stack stack_pages
        self.stack_pages = QStackedWidget()
        for page in self.pages:
            self.stack_pages.addWidget(page)
        self.sidebar_button_group.idClicked.connect(self.stack_pages.setCurrentIndex)

        live_frame_layout.addWidget(self.stack_pages)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.live_frame, 1)

        self.setLayout(main_layout)

    def adapter_signal_connect(self, adapter):
        self.adapter = adapter
        self.adapter.ui_change.connect(self.signal_handler)

        self.tool_page.set_adapter(self.adapter)
        self.functions_page.set_adapter(self.adapter)
        self.update_page.set_adapter(self.adapter)

    def signal_handler(self, name, value):
        print(f'Signal in main widget: {name}, {value}')
        match name:
            case 'MonitorAdapter':
                self.tool_page.ui_change.emit(name, value)
                self.live_frame_change(value)
            case 'SuspendMonitorAdapter':
                self.tool_page.ui_change.emit(name, value)
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

class RequireNameMixin:
    required_methods = ["set_page_name"]

    def __init_subclass__(cls):
        super().__init_subclass__()
        for method in cls.required_methods:
            if not hasattr(cls, method):
                raise TypeError(f"{cls.__name__} must implement {method}()")


class ToolPage(QWidget):
    ui_change = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.page_name = None
        self.studentmain_state = None
        self.kill_run_btn = self.suspend_resume_btn = self.run_taskmgr_btn = self.clean_ifeo_debuggers_btn = None
        self.label_studentmain_state = None
        self.adapter = None
        self.set_page_name()
        self.init_ui()

        self.signal_connect()

    def set_page_name(self):
        self.page_name = 'Tools'

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

        for i, btn in enumerate(
                [self.kill_run_btn, self.suspend_resume_btn, self.run_taskmgr_btn, self.clean_ifeo_debuggers_btn]):
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


class FunctionsPage(QWidget, RequireNameMixin):
    ui_change = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.page_name = None
        self.adapter = None
        self.custom_terminate_btn = None
        self.custom_process_input = None

        self.set_page_name()
        self.init_ui()
        
    def set_page_name(self):
        self.page_name = 'Function'

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.setSpacing(5)

        custom_terminate_frame = QWidget()
        custom_terminate_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        custom_terminate_frame.setObjectName("custom_terminate_frame")

        custom_terminate_frame.setStyleSheet("""
            #custom_terminate_frame {
                background-color: #eeeeee; 
                border-radius: 10px;
                font-size: 24px;
                border: 2px solid #bbbbbb;
                color: #455A64;   
            }
            QRadioButton {
                font-size: 16px;
            }
            QRadioButton::indicator {
                width: 24px;
                height: 24px;
            }
        """)

        custom_terminate_layout = QVBoxLayout(custom_terminate_frame)
        custom_terminate_layout.setContentsMargins(12, 5, 10, 5)
        custom_terminate_layout.setSpacing(3)

        custom_terminate_title_label = QLabel("Terminate Process")
        custom_terminate_title_label.setStyleSheet("""
            background-color: #eeeeee; 
            border-radius: 10px;
            font-size: 20px;
            color: #455A64;   
        """)

        custom_terminate_box_layout = QHBoxLayout()

        self.custom_process_input = QLineEdit()
        self.custom_process_input.setPlaceholderText("Enter PID or process name")
        self.custom_process_input.setFixedHeight(42)
        self.custom_process_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.custom_process_input.setStyleSheet("""
            QLineEdit {
                font: 16px;
                padding: 2px;
                border: 2px solid #F8C8DC;
                border-radius: 8px;
                background-color: #FFF0F5;
                color: #C94F7C;
            }
            QLineEdit:focus {
                border: 2px solid #C94F7C;
                background-color: #FDF6FA;
            }
        """)

        # self.custom_terminate_btn = QPushButton(" Kill ")
        self.custom_terminate_btn = QPushButton("Kill Process")
        self.custom_terminate_btn.setFixedHeight(42)
        self.custom_terminate_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 4px;
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
        self.custom_terminate_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.custom_terminate_btn.clicked.connect(self.custom_terminate)

        custom_terminate_box_layout.addWidget(self.custom_process_input)
        custom_terminate_box_layout.addWidget(self.custom_terminate_btn)

        custom_terminate_layout.addWidget(custom_terminate_title_label)
        custom_terminate_layout.addLayout(custom_terminate_box_layout)

        studentmain_pwd_frame = QWidget()
        studentmain_pwd_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        studentmain_pwd_frame.setObjectName("studentmain_pwd_frame")

        studentmain_pwd_frame.setStyleSheet("""
            #studentmain_pwd_frame {
                background-color: #eeeeee; 
                border-radius: 10px;
                font-size: 24px;
                border: 2px solid #bbbbbb;
                color: #455A64;   
            }
            QRadioButton {
                font-size: 16px;
            }
            QRadioButton::indicator {
                width: 24px;
                height: 24px;
            }
        """)

        studentmain_pwd_layout = QVBoxLayout(studentmain_pwd_frame)
        studentmain_pwd_layout.setContentsMargins(12, 5, 10, 5)
        studentmain_pwd_layout.setSpacing(3)

        studentmain_pwd_title_label = QLabel("Studentmain Password")
        studentmain_pwd_title_label.setStyleSheet("""
            background-color: #eeeeee; 
            border-radius: 10px;
            font-size: 20px;
            color: #455A64;   
        """)

        studentmain_pwd_box_layout = QHBoxLayout()

        self.custom_process_input = QLineEdit()
        self.custom_process_input.setPlaceholderText("Enter PID or process name")
        self.custom_process_input.setFixedHeight(42)
        self.custom_process_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.custom_process_input.setStyleSheet("""
            QLineEdit {
                font: 16px;
                padding: 2px;
                border: 2px solid #F8C8DC;
                border-radius: 8px;
                background-color: #FFF0F5;
                color: #C94F7C;
            }
            QLineEdit:focus {
                border: 2px solid #C94F7C;
                background-color: #FDF6FA;
            }
        """)

        # self.studentmain_pwd_btn = QPushButton(" Kill ")
        self.studentmain_pwd_btn = QPushButton(" Copy ")
        self.studentmain_pwd_btn.setFixedHeight(42)
        self.studentmain_pwd_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 4px;
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
        self.studentmain_pwd_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.studentmain_pwd_btn.clicked.connect(lambda : print('studentmain_pwd_btn clicked'))

        studentmain_pwd_box_layout.addWidget(self.custom_process_input)
        studentmain_pwd_box_layout.addWidget(self.studentmain_pwd_btn)

        studentmain_pwd_layout.addWidget(studentmain_pwd_title_label)
        studentmain_pwd_layout.addLayout(studentmain_pwd_box_layout)


        #
        main_layout.addWidget(custom_terminate_frame)
        main_layout.addWidget(studentmain_pwd_frame)
        main_layout.addStretch(1)

        self.setLayout(main_layout)

    def set_adapter(self, adapter):
        self.adapter = adapter


    def custom_terminate(self):
        process_info = self.custom_process_input.text().strip()
        if process_info:
            self.adapter.terminate_custom_process(process_info)
            self.custom_process_input.setText('')



class SettingsPage(QWidget, RequireNameMixin):
    ui_change = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.page_name = None
        self.adapter = None
        self.set_page_name()
        self.init_ui()
        
    def set_page_name(self):
        self.page_name = 'Settings'

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.setSpacing(5)

        terminate_options = QWidget()
        terminate_options.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        terminate_options.setObjectName("terminate_options_frame")

        terminate_options.setStyleSheet("""
                    #terminate_options_frame {
                        background-color: #eeeeee; 
                        border-radius: 10px;
                        font-size: 24px;
                        border: 2px solid #bbbbbb;
                        color: #455A64;   
                    }
                    
                    QRadioButton {
                        font-size: 16px;
                    }
                    QRadioButton::indicator {
                        width: 24px;
                        height: 24px;
                    }
                """)

        terminate_options_frame_layout = QVBoxLayout(terminate_options)
        terminate_options_frame_layout.setContentsMargins(12, 5, 10, 5)
        terminate_options_frame_layout.setSpacing(3)

        label_terminate_options = QLabel()
        label_terminate_options.setStyleSheet("""
                                            background-color: #eeeeee; 
                                            border-radius: 10px;
                                            font-size: 20px;
                                            color: #455A64;   
                                            """)
        label_terminate_options.setText(f'Terminate options')
        label_terminate_options.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        terminate_options_group = QButtonGroup()
        terminate_options_group.setExclusive(True)

        opt1 = QRadioButton("TerminateProcess")
        opt1.toggled.connect(lambda checked: print("Btn 1 State:", checked))
        opt1.setChecked(True)
        opt1.setDisabled(True)
        opt2 = QRadioButton("NtTerminateProcess")
        opt2.toggled.connect(lambda checked: print("Btn 2 State:", checked))
        opt2.setDisabled(True)
        # opt3 = QRadioButton("Option C")

        terminate_options_group.addButton(opt1)
        terminate_options_group.addButton(opt2)
        # group.addButton(opt3)

        terminate_options_frame_layout.addWidget(label_terminate_options)
        terminate_options_frame_layout.addWidget(opt1)
        terminate_options_frame_layout.addWidget(opt2)
        # terminate_options_frame_layout.addWidget(opt3)

        main_layout.addWidget(terminate_options)
        main_layout.addStretch(1)

        self.setLayout(main_layout)


class UpdatePage(QWidget, RequireNameMixin):
    ui_change = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.page_name = None
        self.studentmain_state = None
        self.update_state_label = None
        self.current_version_label = None
        self.get_update_btn = None
        self.adapter = None
        self.current_version = None

        self.set_page_name()
        self.init_ui()

        self.signal_connect()
        
    def set_page_name(self):
        self.page_name = 'Updates'

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
                                    border: 2px solid #cccccc;
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
                                    border: 2px solid #cccccc;
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


class AboutPage(QWidget, RequireNameMixin):
    ui_change = Signal(str, object)

    def __init__(self):
        super().__init__()
        self.page_name = None

        self.set_page_name()
        self.init_ui()

    def set_page_name(self):
        self.page_name = 'About'

    def init_ui(self):
        main_layout = QVBoxLayout()
        # main_layout.setContentsMargins(3, 3, 3, 3)
        # main_layout.setSpacing(5)

        page_updating = PageUpdating()

        main_layout.addWidget(page_updating)

        self.setLayout(main_layout)


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
