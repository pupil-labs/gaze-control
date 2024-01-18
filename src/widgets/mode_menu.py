import time

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .gaze_button import GazeButton


class ModeMenu(QWidget):
    mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.enabled = True

        self.disappear_timeout = 3.0
        self.lost_focus_at = None

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.buttons = []

        btn = GazeButton("View")
        btn.clicked.connect(lambda: self.mode_changed.emit("View"))
        layout.addWidget(btn)
        self.buttons.append(btn)

        btn = GazeButton("Click")
        btn.clicked.connect(lambda: self.mode_changed.emit("Click"))
        layout.addWidget(btn)
        self.buttons.append(btn)

        btn = GazeButton("Zoom")
        btn.clicked.connect(lambda: self.mode_changed.emit("Zoom"))
        layout.addWidget(btn)
        self.buttons.append(btn)

        btn = GazeButton("Keyboard")
        btn.clicked.connect(lambda: self.mode_changed.emit("Keyboard"))
        layout.addWidget(btn)
        self.buttons.append(btn)

        btn = GazeButton("Speak")
        btn.clicked.connect(lambda: self.mode_changed.emit("Speak"))
        layout.addWidget(btn)
        self.buttons.append(btn)

        self.setLayout(layout)

        self.setVisible(False)

        op = QGraphicsOpacityEffect(self)
        op.setOpacity(0.5)
        self.setGraphicsEffect(op)
        self.setAutoFillBackground(True)

    def update_data(self, eye_tracking_data):
        if not self.enabled:
            return False

        mode_change = False
        if self.isVisible():
            if eye_tracking_data.gaze is None:
                return
            gaze = QPoint(*eye_tracking_data.gaze)

            if eye_tracking_data.dwell_process == 1.0:
                for btn in self.buttons:
                    if btn.check_press(gaze):
                        mode_change = True
                        self.setVisible(False)

            p = self.mapFromGlobal(gaze)
            if self.rect().contains(p):
                self.lost_focus_at = None
            else:
                if self.lost_focus_at is None:
                    self.lost_focus_at = time.time()
                else:
                    if time.time() - self.lost_focus_at > self.disappear_timeout:
                        self.setVisible(False)
                        self.lost_focus_at = None

        return mode_change
