from .app_mode import AppMode

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from eye_tracking_provider import EyeTrackingData
from widgets.keyboard import Keyboard


class KeyboardMode(AppMode):
    def __init__(self, parent=None, event_handlers=None):
        super().__init__(parent, event_handlers)

        self.keyboard = Keyboard(self)
        self.keyboard.keyPressed.connect(event_handlers["on_key_pressed"])

    def _update_data(self, eye_tracking_data: EyeTrackingData):
        self.keyboard.update_data(eye_tracking_data)

    def resize(self, size):
        super().resize(size)
        height_ratio = 0.65
        self.keyboard.setGeometry(
            0,
            size.height() * (1 - height_ratio),
            size.width(),
            size.height() * height_ratio,
        )
