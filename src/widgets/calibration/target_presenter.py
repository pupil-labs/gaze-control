import time
import numpy as np
from PySide6.QtCore import *
from PySide6.QtCore import Qt
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QWidget


class TargetPresenter(QWidget):
    presentation_finished = Signal((np.ndarray, np.ndarray))

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.map_to_scene_video = None
        self.setStyleSheet("background:gray;")

        self.targets = None
        self.target_radius = 10
        self.total_target_time = 2.0
        self.target_acquisition_time = 0.75

        self.stop()

    def start(self, targets):
        self.targets = targets
        self.calibration_idx = 0
        self.target_start = time.time()
        self.target_duration = 0.0

        self.collected_gaze_positions = []
        self.collected_target_locations = []

    def stop(self):
        self.targets = None
        self.calibration_idx = None
        self.target_start = None
        self.target_duration = None
        self.target_location = None
        self.target_color = None

    def update_data(self, eye_tracking_data):
        if eye_tracking_data is None:
            return

        self.target_location, self.target_color = self._current_target()
        if self.target_location is None:
            return

        if self.target_duration > self.target_acquisition_time:
            trans = eye_tracking_data.surf_to_img_trans
            if trans is None:
                return

            t = (
                self.target_location.x(),
                self.target_location.y(),
            )
            target_location_scene = self.map_to_scene_video(t, trans)
            self.collected_gaze_positions.append(eye_tracking_data.raw_gaze[:2])
            self.collected_target_locations.append(target_location_scene)

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
                self.stop()
                self.presentation_finished.emit(
                    np.array(self.collected_gaze_positions),
                    np.array(self.collected_target_locations),
                )
                return None, None
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

    def paintEvent(self, _: QPaintEvent):
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
