from .app_mode import AppMode

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from eye_tracking_provider import EyeTrackingData
from widgets.gaze_overlay import GazeOverlay


class ViewMode(AppMode):
    keyPressed = Signal(str)

    def __init__(self, parent=None, event_handlers=None):
        super().__init__(parent, event_handlers)
        self.gaze_overlay = GazeOverlay(self)

    def _update_data(self, eye_tracking_data: EyeTrackingData):
        self.gaze_overlay.update_data(eye_tracking_data)

    def resize(self, size):
        super().resize(size)
        self.gaze_overlay.setGeometry(0, 0, size.width(), size.height())