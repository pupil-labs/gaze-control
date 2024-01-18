from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtGui import QKeyEvent, QResizeEvent
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QSoundEffect

from eye_tracking_provider import EyeTrackingData


class SpeakPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QGridLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.speak_btn = QPushButton("Speak")
        self.speak_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.speak_btn.setStyleSheet("background-color: #00ff00;")
        main_layout.addWidget(self.speak_btn, 0, 0, 1, 1)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.reset_btn.setStyleSheet("background-color: #ff0000;")
        main_layout.addWidget(self.reset_btn, 1, 0, 1, 1)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("background-color: lightgray;")
        self.text_edit.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(48)
        self.text_edit.setFont(font)
        # self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.text_edit, 0, 2, 2, 4)

        self.setLayout(main_layout)

        op = QGraphicsOpacityEffect(self)
        op.setOpacity(0.5)
        self.setGraphicsEffect(op)
        self.setAutoFillBackground(True)

    def update_data(self, eye_tracking_data: EyeTrackingData):
        pass

    def _toggle_caps(self):
        self.caps = not self.caps

        for key in self.keys:
            if key.code.isalpha() and len(key.code) == 1:
                key.toggleCaps()
