from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from widgets.marker_overlay import MarkerOverlay
from widgets.mode_menu import ModeMenu
from widgets.mode_menu_permanent import ModeMenuPermanent

from widgets import app_modes


class MainWindow(QWidget):
    surface_changed = Signal()
    hidden = Signal()

    def __init__(self, event_handlers):
        super().__init__()

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        # Make window transparent for mouse events such that any click will be passed through to the window below.
        self.setWindowFlag(Qt.WindowTransparentForInput)

        self.modes = {
            "View": app_modes.ViewMode(self, event_handlers),
            "Click": app_modes.ClickMode(self, event_handlers),
            "Zoom": app_modes.ZoomMode(self, event_handlers),
            "Keyboard": app_modes.KeyboardMode(self, event_handlers),
            "Speaker": app_modes.SpeakerMode(self, event_handlers),
        }
        self.current_mode = self.modes["View"]

        self.mode_menu_left = ModeMenu(self, ["View", "Click", "Zoom", "Keyboard"])
        self.mode_menu_left.mode_changed.connect(self._switch_modes)
        self.mode_menu_right = ModeMenu(self, ["Speaker"])
        self.mode_menu_right.mode_changed.connect(self._switch_modes)

        self.mode_menu_permanent = ModeMenuPermanent(
            self, ["View", "Click", "Zoom", "Keyboard", "Speaker"]
        )
        self.mode_menu_permanent.mode_changed.connect(self._switch_modes)

        self.marker_overlay = MarkerOverlay(self)

        self.current_mode.activate()

    def _switch_modes(self, mode):
        self.current_mode.deactivate()
        self.current_mode = self.modes[mode]
        self.current_mode.activate()

    def update_data(self, eye_tracking_data):
        self.current_mode.update_data(eye_tracking_data)

    def moveEvent(self, _):
        self.surface_changed.emit()

    def resizeEvent(self, _):
        for mode in self.modes.values():
            mode.resize(self.size())

        self.marker_overlay.resize(self.size())
        self.mode_menu_left.setGeometry(
            0,
            self.height() * 0.2,
            self.width() * 0.1,
            self.height() * 0.6,
        )
        self.mode_menu_right.setGeometry(
            self.width() * 0.9,
            self.height() * 0.2,
            self.width() * 0.1,
            self.height() * 0.6,
        )
        height_ratio = 0.65
        self.mode_menu_permanent.setGeometry(
            0,
            self.height() * (1 - height_ratio),
            self.width(),
            self.height() * height_ratio,
        )

    def render_as_overlay(self, painter):
        self.render(painter, self.geometry().topLeft())
