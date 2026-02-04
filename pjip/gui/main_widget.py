from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, \
    QSizePolicy, QStackedWidget, QLayout, QButtonGroup

from .pages import ToolPage, FunctionPage, SettingsPage, UpdatePage, AboutPage


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
        self.functions_page = FunctionPage()
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
        print(f'Signal: {name}, {value}')
        match name:
            case 'MonitorAdapter':
                self.tool_page.ui_change.emit(name, value)
                self.live_frame_change(value)
            case 'SuspendMonitorAdapter':
                self.tool_page.ui_change.emit(name, value)
            case 'UpdateAdapter':
                self.update_page.ui_change.emit(name, value)
            case 'GetStudentmainPasswordAdapter':
                self.functions_page.ui_change.emit(name, value)

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
