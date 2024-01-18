import os
import numpy as np

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtGui import QKeyEvent, QResizeEvent
from PySide6.QtWidgets import *

from widgets.marker_overlay import MarkerOverlay
from widgets.gaze_overlay import GazeOverlay
from widgets.keyboard import Keyboard
from widgets.selection_zoom import SelectionZoom
from widgets.mode_menu import ModeMenu
from widgets.calibration import CalibrationWidget
from widgets.speak_panel import SpeakPanel


class MainWindow(QWidget):
    surface_changed = Signal()
    hidden = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        # Make window transparent for mouse events such that any click will be passed through to the window below.
        self.setWindowFlag(Qt.WindowTransparentForInput)

        self.selection_zoom = SelectionZoom()

        self.keyboard = Keyboard(self)
        self.speak_panel = SpeakPanel(self)
        self.calibration_widget = CalibrationWidget(self)

        self.mode_menu = ModeMenu(self)
        self.marker_overlay = MarkerOverlay(self)
        self.gaze_overlay = GazeOverlay()
        self.gaze_overlay.setParent(self)

    def render_as_overlay(self, painter):
        self.render(painter, self.geometry().topLeft())
        overlay_widget_global_pos = self.gaze_overlay.mapToGlobal(
            self.gaze_overlay.geometry().topLeft()
        )
        self.gaze_overlay.render(painter, overlay_widget_global_pos)

    def update_data(self, eye_tracking_data):
        if eye_tracking_data.gaze is not None:
            gaze = QPoint(*eye_tracking_data.gaze)
            self.gaze_overlay.update_data(gaze, eye_tracking_data.dwell_process)

    def moveEvent(self, event):
        self.surface_changed.emit()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()

        return super().keyReleaseEvent(event)

    def resizeEvent(self, event):
        self.marker_overlay.resize(self.size())
        self.gaze_overlay.resize(self.size())
        self.keyboard.setGeometry(0, self.height() / 2, self.width(), self.height() / 2)
        self.speak_panel.setGeometry(0, 0, self.width(), self.height() / 2)
        self.calibration_widget.resize(self.size())
        self.mode_menu.setGeometry(
            0,
            self.height() * 0.2,
            self.width() * 0.1,
            self.height() * 0.6,
        )
