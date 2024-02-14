import numpy as np
import cv2

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .scaled_image_view import ScaledImageView


class ScreenshotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        self.setWindowTitle("Debug Window - Scene Camera")
        self.resize(800, 600)

        self.screen_view = ScaledImageView()
        self.layout().addWidget(self.screen_view, stretch=1)

    def update_data(self):
        app = QApplication.instance()
        screen = app.main_window.screen()
        image = screen.grabWindow()
        self.screen_view.set_image(image)
