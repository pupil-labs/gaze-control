from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from eye_tracking_provider import EyeTrackingData


class GazeOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gaze_circle_radius = 20.0
        self.gaze = None
        self.dwell_process = 0.0

        self.brush_color = QColor(Qt.red)
        self.brush_color.setAlphaF(0.3)

        self.killed_pen = QPen()
        self.killed_pen.setWidth(10)
        self.killed_pen.setColor(self.brush_color)

    def update_data(self, eye_tracking_data: EyeTrackingData):
        if eye_tracking_data.gaze is None:
            return

        self.gaze = QPoint(*eye_tracking_data.gaze)
        self.dwell_process = eye_tracking_data.dwell_process
        self.update()

    def paintEvent(self, event):
        if self.gaze is None:
            return

        if self.isVisible():
            render_point = self.mapFromGlobal(self.gaze)
            with QPainter(self) as painter:
                if QApplication.instance().pause_switch_active:
                    painter.setPen(self.killed_pen)
                    painter.drawLine(
                        render_point.x() - self.gaze_circle_radius,
                        render_point.y() - self.gaze_circle_radius,
                        render_point.x() + self.gaze_circle_radius,
                        render_point.y() + self.gaze_circle_radius,
                    )
                    painter.drawLine(
                        render_point.x() - self.gaze_circle_radius,
                        render_point.y() + self.gaze_circle_radius,
                        render_point.x() + self.gaze_circle_radius,
                        render_point.y() - self.gaze_circle_radius,
                    )
                else:
                    painter.setBrush(self.brush_color)
                    painter.drawEllipse(
                        render_point,
                        self.gaze_circle_radius,
                        self.gaze_circle_radius,
                    )

                    green = QColor(Qt.green)
                    green.setAlphaF(0.3)
                    painter.setBrush(green)
                    painter.drawEllipse(
                        render_point,
                        self.gaze_circle_radius * self.dwell_process,
                        self.gaze_circle_radius * self.dwell_process,
                    )
