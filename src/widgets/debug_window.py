import numpy as np
import cv2

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .scaled_image_view import ScaledImageView
from image_conversion import qimage_from_frame
from eye_tracking_provider import EyeTrackingData


class GazeView(ScaledImageView):
    def __init__(self):
        super().__init__()
        self.gaze_circle_radius = 15.0
        self.gaze_point = None
        self.surface_points = None
        self.overlay_color = QColor(255, 0, 0, 77)
        self.surface_color = QColor(255, 0, 255, 200)

    def update_data(self, gaze, surface_points):
        self.gaze_point = gaze
        self.surface_points = surface_points
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

                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(self.surface_color, 3))
                painter.setBrush(Qt.NoBrush)
                polygon = QPolygonF()
                for p in self.surface_points:
                    p = QPointF(*p) * scale + offset
                    polygon.append(p)
                painter.drawPolygon(polygon)


class DebugWindow(QWidget):
    def __init__(self, distort_point, map_surface_to_scene_video):
        super().__init__()
        self.distort_point = distort_point
        self.map_surface_to_scene_video = map_surface_to_scene_video
        self.setLayout(QVBoxLayout())

        self.setWindowTitle("Debug Window - Scene Camera")
        self.resize(800, 600)

        self.gaze_view = GazeView()
        self.layout().addWidget(self.gaze_view, stretch=1)

        self.info_widget = QLabel()
        self.info_widget.setStyleSheet("font-family: monospace")
        self.info_widget.setText("Waiting for stream...")
        self.layout().addWidget(self.info_widget)

    def update_data(self, data: EyeTrackingData):
        if data is None:
            return

        image = qimage_from_frame(data.scene.bgr_pixels)
        self.gaze_view.set_image(image)

        if data.raw_gaze is not None:
            device_info = QApplication.instance().eye_tracking_provider.device
            gaze_point = QPoint(*data.raw_gaze[:2])
            self.info_widget.setText(
                f"Connected to {device_info}. Gaze: {gaze_point.x(): 4d}, {gaze_point.y(): 4d}"
            )

            surface_points = []
            if data.surf_to_img_trans is not None:
                h_steps = np.linspace(0, 1600, 10)
                v_steps = np.linspace(0, 1200, 10)
                surf_border_points = [(0, s) for s in v_steps]
                surf_border_points += [(s, 1) for s in h_steps]
                surf_border_points += [(1, s) for s in v_steps[::-1]]
                surf_border_points += [(s, 0) for s in h_steps[::-1]]
                surface_points = [
                    self.map_surface_to_scene_video(p, data.surf_to_img_trans)
                    for p in surf_border_points
                ]

            self.gaze_view.update_data(gaze_point, surface_points)
