import subprocess
import sys

import pyttsx3

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtGui import QKeyEvent, QResizeEvent
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QSoundEffect

from .gaze_button import GazeButton
from eye_tracking_provider import EyeTrackingData


class SpeakPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        if sys.platform != "darwin":
            self.engine = pyttsx3.init()

        main_layout = QGridLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.speak_btn = GazeButton("Speak")
        self.speak_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.speak_btn.setStyleSheet("background-color: #00ff00;")
        main_layout.addWidget(self.speak_btn, 0, 0, 1, 1)

        self.reset_btn = GazeButton("Reset")
        self.reset_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.reset_btn.setStyleSheet("background-color: #ff0000;")

        main_layout.addWidget(self.reset_btn, 1, 0, 1, 1)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("background-color: lightgray;")
        self.text_edit.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(48)
        self.text_edit.setFont(font)
        main_layout.addWidget(self.text_edit, 0, 2, 2, 4)

        self.setLayout(main_layout)

        self.speak_btn.clicked.connect(self.speak)
        self.reset_btn.clicked.connect(self.text_edit.clear)

        op = QGraphicsOpacityEffect(self)
        op.setOpacity(0.3)
        self.setGraphicsEffect(op)
        self.setAutoFillBackground(True)

    def update_data(self, eye_tracking_data: EyeTrackingData):
        clicked = eye_tracking_data.dwell_process == 1.0

        if clicked:
            gaze = QPoint(*eye_tracking_data.gaze)
            self.speak_btn.check_press(gaze)
            self.reset_btn.check_press(gaze)

    def _toggle_caps(self):
        self.caps = not self.caps

        for key in self.keys:
            if key.code.isalpha() and len(key.code) == 1:
                key.toggleCaps()

    def speak(self):
        text = "'" + self.text_edit.toPlainText() + "'"
        if sys.platform == "darwin":
            subprocess.run(["say", "-v", "Daniel", text])
        else:
            self.engine.say(text)
            self.engine.runAndWait()
