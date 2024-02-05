import subprocess
import sys

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import pyttsx3

from .app_mode import AppMode
from eye_tracking_provider import EyeTrackingData
from widgets.keyboard import Keyboard
from widgets.gaze_button import GazeButton, ButtonStyle


class SpeakerMode(AppMode):
    def __init__(self, parent=None, event_handlers=None):
        super().__init__(parent, event_handlers)
        # self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        if sys.platform != "darwin":
            self.engine = pyttsx3.init()

        self._create_text_form()

        self.keyboard = Keyboard(self, opacity=1.0)
        self.keyboard.keyPressed.connect(event_handlers["on_key_pressed"])

    def _create_text_form(self):
        self.text_form = QWidget(self)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.speak_btn = GazeButton(
            "Speak",
            regular_style=ButtonStyle(background_color="#6eff5e"),
            hover_style=ButtonStyle(background_color="#a8fc9f"),
        )
        self.speak_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addWidget(self.speak_btn, 0, 0, 1, 1)
        self.speak_btn.clicked.connect(self._speak)

        self.reset_btn = GazeButton(
            "Reset",
            regular_style=ButtonStyle(background_color="#ff6969"),
            hover_style=ButtonStyle(background_color="#fc9f9f"),
        )
        self.reset_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addWidget(self.reset_btn, 1, 0, 1, 1)
        self.reset_btn.clicked.connect(self._clear_text)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("background-color: lightgray;")
        self.text_edit.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(48)
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit, 0, 2, 2, 4)

        self.text_form.setLayout(layout)

    def activate(self):
        super().activate()
        self._set_window_transparency_for_input(False)
        self.activateWindow()
        self.text_edit.setFocus()

    def deactivate(self):
        super().deactivate()
        self._set_window_transparency_for_input(True)

    def _set_window_transparency_for_input(self, value):
        is_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowTransparentForInput, value)
        if is_visible:
            self.show()

    def _update_data(self, eye_tracking_data: EyeTrackingData):
        self.speak_btn.update_data(eye_tracking_data)
        self.reset_btn.update_data(eye_tracking_data)
        self.keyboard.update_data(eye_tracking_data)

    def _speak(self):
        text = "'" + self.text_edit.toPlainText() + "'"
        if sys.platform == "darwin":
            subprocess.run(["say", "-v", "Daniel", text])
        else:
            self.engine.say(text)
            self.engine.runAndWait()
        self._clear_text()

    def _clear_text(self):
        self.text_edit.clear()
        self.text_edit.setAlignment(Qt.AlignCenter)

    def resize(self, size):
        super().resize(size)
        height_ratio = 0.65
        self.text_form.setGeometry(
            0,
            0,
            size.width(),
            size.height() * (1 - height_ratio),
        )
        self.keyboard.setGeometry(
            0,
            size.height() * (1 - height_ratio),
            size.width(),
            size.height() * height_ratio,
        )
