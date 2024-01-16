import numpy as np
import time
import joblib

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtGui import QKeyEvent, QResizeEvent
from PySide6.QtWidgets import *

from widgets.marker_overlay import MarkerOverlay
from widgets.gaze_overlay import GazeOverlay
from widgets.keyboard import Keyboard


class CalibrationWidget(QWidget):
    key_pressed = Signal(QKeyEvent)

    def __init__(self, parent):
        super().__init__(parent)
        self.map_to_scene_video = None
        self.target_radius = 10
        self.targets = self._generate_target_locations("training")
        self.target_locations_validation = self._generate_target_locations("validation")
        self.total_target_time = 2.0
        self.target_acquisition_time = 0.75

        self.target_location = None
        self.target_color = None
        self.calibration_idx = None
        self.time = None

        self.training_data = []
        self.training_labels = []

        self.setStyleSheet("background:gray;")
        self.setVisible(False)

    def _generate_target_locations(self, mode):
        width = self.width()
        height = self.height()

        hor_padd = width * 0.11
        ver_padd = height * 0.015
        hor_targets = np.linspace(hor_padd, width - hor_padd, 6)
        ver_targets = np.linspace(ver_padd, height * 0.15, 3)
        top_targets = np.meshgrid(hor_targets, ver_targets)
        top_targets = np.array(
            list(zip(top_targets[0].flatten(), top_targets[1].flatten()))
        )

        hor_padd = width * 0.11
        ver_padd = height * 0.015
        hor_targets = np.linspace(hor_padd, width - hor_padd, 6)
        ver_targets = np.linspace(height - height * 0.15, height - ver_padd, 3)
        bot_targets = np.meshgrid(hor_targets, ver_targets)
        bot_targets = np.array(
            list(zip(bot_targets[0].flatten(), bot_targets[1].flatten()))
        )

        hor_padd = width * 0.015
        hor_targets = np.linspace(hor_padd, width - hor_padd, 8)
        ver_padd = height * 0.2
        ver_targets = np.linspace(ver_padd, height - ver_padd, 6)
        center_targets = np.meshgrid(hor_targets, ver_targets)
        center_targets = np.array(
            list(zip(center_targets[0].flatten(), center_targets[1].flatten()))
        )

        # hor_padd = width * 0.11
        # ver_padd = height * 0.015
        # hor_targets = np.linspace(hor_padd, width - hor_padd, 2)
        # ver_targets = np.linspace(ver_padd, height * 0.15, 2)
        # top_targets = np.meshgrid(hor_targets, ver_targets)
        # top_targets = np.array(
        #     list(zip(top_targets[0].flatten(), top_targets[1].flatten()))
        # )

        # hor_padd = width * 0.11
        # ver_padd = height * 0.015
        # hor_targets = np.linspace(hor_padd, width - hor_padd, 2)
        # ver_targets = np.linspace(height - height * 0.15, height - ver_padd, 2)
        # bot_targets = np.meshgrid(hor_targets, ver_targets)
        # bot_targets = np.array(
        #     list(zip(bot_targets[0].flatten(), bot_targets[1].flatten()))
        # )

        # hor_padd = width * 0.015
        # hor_targets = np.linspace(hor_padd, width - hor_padd, 2)
        # ver_padd = height * 0.2
        # ver_targets = np.linspace(ver_padd, height - ver_padd, 2)
        # center_targets = np.meshgrid(hor_targets, ver_targets)
        # center_targets = np.array(
        #     list(zip(center_targets[0].flatten(), center_targets[1].flatten()))
        # )

        targets = np.concatenate([top_targets, center_targets, bot_targets])

        if mode == "validation":
            targets[:, 0] *= 0.8
            targets[:, 0] += width * 0.1
            targets[:, 1] *= 0.8
            targets[:, 1] += height * 0.1

        targets = [QPoint(*t) for t in targets]
        return targets

    def start(self):
        self.setVisible(True)
        self.calibration_idx = 0
        self.target_start = time.time()
        self.target_duration = 0.0

    def stop(self):
        self.setVisible(False)
        self.calibration_idx = None
        self.target_start = None
        self.target_duration = None
        self.time = None

    def update_data(self, eye_tracking_data):
        self.target_location, self.target_color = self._current_target()
        if self.target_location is None:
            return

        if self.target_duration > self.target_acquisition_time:
            trans = eye_tracking_data.surf_to_img_trans
            target_location_scene = None
            if trans is not None:
                t = (
                    self.target_location.x(),
                    self.target_location.y(),
                )
                target_location_scene = self.map_to_scene_video(t, trans)
            self.training_data.append(eye_tracking_data.raw_gaze)
            self.training_labels.append(target_location_scene)

        self.update()

    def _current_target(self):
        if self.target_start is None:
            target_location = None
            target_color = None
        else:
            self.target_duration = time.time() - self.target_start
            if self.target_duration > self.total_target_time:
                self.calibration_idx += 1
                self.target_start = time.time()
                self.target_duration = 0.0

            if self.calibration_idx >= len(self.targets):
                np.save("training_data.npy", np.array(self.training_data))
                np.save("training_labels.npy", np.array(self.training_labels))
                self.stop()
                target_location = None
                target_color = None
            else:
                target_location = self.targets[self.calibration_idx]

            if (
                self.target_duration
                and self.target_duration > self.target_acquisition_time
            ):
                target_color = QColor(Qt.green)
            else:
                target_color = QColor(Qt.red)

        return target_location, target_color

    def paintEvent(self, event):
        if self.isVisible():
            with QPainter(self) as painter:
                painter.fillRect(self.rect(), Qt.gray)

                if self.target_location is not None:
                    painter.setBrush(self.target_color)
                    painter.drawEllipse(
                        self.target_location,
                        self.target_radius,
                        self.target_radius,
                    )

    def resizeEvent(self, event):
        self.targets = self._generate_target_locations("training")
        self.target_locations_validation = self._generate_target_locations("validation")
        self.update()
