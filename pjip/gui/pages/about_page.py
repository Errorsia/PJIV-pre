from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout

from pjip.gui.main_widget import PageUpdating
from pjip.gui.pages.page_format import RequireNameMixin


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