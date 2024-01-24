import numpy as np
import cv2

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .scaled_image_view import ScaledImageView
from image_conversion import qimage_from_frame


class GazeView(ScaledImageView):
    def __init__(self):
        super().__init__()
        self.gaze_circle_radius = 15.0
        self.gaze_point = None
        self.markers = None
        self.overlay_color = QColor(255, 0, 0, 77)
        self.marker_color = QColor(0, 255, 0, 77)

    def update_data(self, gaze, markers):
        self.gaze_point = gaze
        self.markers = markers
        self.update()

    def paintEvent(self, event):
        if self.image is None:
            return

        super().paintEvent(event)

        if self.gaze_point is not None:
            scale = self.render_rect.width() / self.image.width()
            offset = self.render_rect.topLeft()
            gaze_render_point = self.gaze_point * scale + offset

            with QPainter(self) as painter:
                painter.setBrush(self.overlay_color)
                painter.drawEllipse(
                    gaze_render_point,
                    self.gaze_circle_radius,
                    self.gaze_circle_radius,
                )

                painter.setBrush(self.marker_color)
                for marker in self.markers:
                    polygon = QPolygonF()
                    for x, y in marker:
                        p = QPointF(x, y) * scale + offset
                        polygon.append(p)
                    painter.drawPolygon(polygon)


class DebugWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.K = None
        self.K_inv = None
        self.D = None

        self.setLayout(QVBoxLayout())

        self.setWindowTitle("Debug Window - Scene Camera")
        self.resize(800, 600)

        self.gaze_view = GazeView()
        self.layout().addWidget(self.gaze_view, stretch=1)

        self.info_widget = QLabel()
        self.info_widget.setStyleSheet("font-family: monospace")
        self.info_widget.setText("Waiting for stream...")
        self.layout().addWidget(self.info_widget)

    def set_scene_calib(self, K, K_inv, D):
        self.K = K
        self.K_inv = K_inv
        self.D = D

    def update_data(self, data):
        if data is None:
            return

        markers = []
        for marker in data.markers:
            corners_undist = marker.as_dict()["vertices"].values()
            corners_dist = [self._distort_point(p) for p in corners_undist]
            markers.append(corners_dist)

        image = qimage_from_frame(data.scene.bgr_pixels)
        self.gaze_view.set_image(image)

        if data.raw_gaze is not None:
            device_info = QApplication.instance().eye_tracking_provider.device
            gaze_point = QPoint(*data.raw_gaze[:2])
            self.info_widget.setText(
                f"Connected to {device_info}. Gaze: {gaze_point.x(): 4d}, {gaze_point.y(): 4d}"
            )
            self.gaze_view.update_data(gaze_point, markers)

    def _distort_point(self, p):
        p_hom = np.array([p[0], p[1], 1])
        p_3d = self.K_inv @ p_hom

        p_dist = cv2.projectPoints(
            p_3d.reshape(1, 1, 3), np.zeros(3), np.zeros(3), self.K, self.D
        )[0].reshape(2)
        return p_dist
