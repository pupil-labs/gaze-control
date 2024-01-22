from .app_mode import AppMode

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtGui import QKeyEvent, QResizeEvent
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QSoundEffect

from eye_tracking_provider import EyeTrackingData


class KeyboardMode(AppMode):
    def __init__(self, parent=None, event_handlers=None):
        super().__init__(parent, event_handlers)

        self.keyboard = Keyboard(self)
        self.keyboard.keyPressed.connect(event_handlers["on_key_pressed"])

    def _update_data(self, eye_tracking_data: EyeTrackingData):
        self.keyboard.update_data(eye_tracking_data)

    def resize(self, size):
        super().resize(size)
        self.keyboard.setGeometry(0, size.height() / 2, size.width(), size.height() / 2)


class Keyboard(QWidget):
    keyPressed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.caps = False
        self.qwerty_keys = "qwertyuiopasdfghjklzxcvbnm"

        layout = QGridLayout()

        for i in range(20):
            layout.setColumnStretch(i, 1)
        for i in range(8):
            layout.setRowStretch(i, 1)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self._add_basic_keys(layout)
        self._add_special_keys(layout)
        self.setLayout(layout)

        for key in self.keys:
            if key.code == "CAPS":
                key.clicked.connect(self._toggle_caps)
            else:
                key.clicked.connect(self.keyPressed.emit)

        op = QGraphicsOpacityEffect(self)
        op.setOpacity(0.5)
        self.setGraphicsEffect(op)
        self.setAutoFillBackground(True)

    def _add_basic_keys(self, layout):
        row_idx = 0
        col_idx = 0
        self.keys = []
        for idx, key in enumerate(self.qwerty_keys):
            if idx in [10, 19]:
                row_idx += 1
                col_idx = 0
            k = Key(key)
            self.keys.append(k)
            layout.addWidget(k, row_idx * 2, col_idx * 2 + row_idx, 2, 2)
            col_idx += 1

    def _add_special_keys(self, layout):
        k = Key("CAPS", code="CAPS")
        self.keys.append(k)
        layout.addWidget(k, 6, 2, 2, 2)

        k = Key("SPACE", code=" ")
        self.keys.append(k)
        layout.addWidget(k, 6, 4, 2, 4)

        k = Key("backspace", code="backspace")
        self.keys.append(k)
        layout.addWidget(k, 6, 8, 2, 4)

        k = Key("enter", code="enter")
        self.keys.append(k)
        layout.addWidget(k, 6, 12, 2, 4)

    def update_data(self, eye_tracking_data):
        if eye_tracking_data.gaze is None:
            return

        gaze = QPoint(*eye_tracking_data.gaze)
        click = eye_tracking_data.dwell_process == 1.0
        for key in self.keys:
            key.update_data(gaze, click)

    def _toggle_caps(self):
        self.caps = not self.caps

        for key in self.keys:
            if key.code.isalpha() and len(key.code) == 1:
                key.toggleCaps()


class Key(QPushButton):
    clicked = Signal(str)

    def __init__(self, label, code=None):
        self.code = code
        if code is None:
            self.code = label
        super().__init__(label)
        self.setStyleSheet(
            "background-color: white; margin:0; border: 1px solid black; padding:0; color: black; border-radius: 10px; font-size: 20px;"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.key_sound = QSoundEffect()
        self.key_sound.setSource(QUrl.fromLocalFile("key-stroke.wav"))

    def update_data(self, point: QPoint, click: bool):
        point = self.mapFromGlobal(point)
        if self.rect().contains(point):
            self.set_highlight(True)
            if click:
                self.key_sound.play()
                self.clicked.emit(self.code)
        else:
            self.set_highlight(False)

    def set_highlight(self, highlight):
        if highlight:
            self.setStyleSheet(
                "background-color: white; margin:0; border: 1px solid black; padding:0; color: black; border-radius: 10px; font-size: 20px;"
            )
        else:
            self.setStyleSheet(
                "background-color: #b3b3b3; margin:0; border: 1px solid black; padding:0; color: black; border-radius: 10px; font-size: 20px;"
            )

    def toggleCaps(self):
        if self.text().isupper():
            self.setText(self.text().lower())
            self.code = self.code.lower()
        else:
            self.setText(self.text().upper())
            self.code = self.code.upper()