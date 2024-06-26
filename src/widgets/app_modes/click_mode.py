from .app_mode import AppMode

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from eye_tracking_provider import EyeTrackingData
from widgets.gaze_overlay import GazeOverlay


class ClickMode(AppMode):
    mouse_moved = Signal(QPoint)
    mouse_clicked = Signal(QPoint)

    def __init__(self, parent=None, event_handlers=None):
        super().__init__(parent, event_handlers)
        self.gaze_overlay = GazeOverlay(self)

        self.mouse_moved.connect(self.event_handlers["on_mouse_move"])
        self.mouse_clicked.connect(self.event_handlers["on_mouse_click"])

    def _update_data(self, eye_tracking_data: EyeTrackingData):
        self.gaze_overlay.update_data(eye_tracking_data)

        if eye_tracking_data.gaze is None:
            return

        p = QPoint(*eye_tracking_data.gaze)
        if eye_tracking_data.dwell_process != 1.0:
            pass
            # TODO: moving the mouse like this is too laggy
            # self.mouse_moved.emit(p)
        else:
            self.mouse_clicked.emit(p)

    def resize(self, size):
        super().resize(size)
        self.gaze_overlay.setGeometry(0, 0, size.width(), size.height())
