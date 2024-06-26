from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import *

from pupil_labs.real_time_screen_gaze import marker_generator


class Marker(QWidget):
    brightness_changed = Signal(int)

    def __init__(self, marker_id, brightness=128):
        super().__init__()
        self.id = marker_id
        self.brightness = brightness

        self._pixmap = self._createMarker()
        self.setMinimumSize(150, 150)

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = value
        self._brightness_fill_color = QColor(0, 0, 0, 255-value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._pixmap)
        painter.fillRect(self.rect(), self._brightness_fill_color)

    def get_marker_verts(self):
        """Returns the markers coordinates in global screen space."""
        width = self.width()
        height = self.height()
        assert width == height or (width == 640 and height == 480)

        # The marker has a white border which should be ignored when calculating the vertex positions.
        rect = self.rect() - QMargins(
            width / 10,
            width / 10,
            width / 10,
            width / 10,
        )
        verts = [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight(),
        ]
        verts = [self.mapToGlobal(vert) for vert in verts]
        verts = [(vert.x(), vert.y()) for vert in verts]
        return verts

    def _createMarker(self):
        marker = marker_generator.generate_marker(self.id, flip_x=True, flip_y=True)
        image = QImage(10, 10, QImage.Format_Mono)
        image.fill(1)
        for y in range(marker.shape[0]):
            for x in range(marker.shape[1]):
                color = marker[y][x] // 255
                image.setPixel(x + 1, y + 1, color)

        # Convert the QImage to a QPixmap
        return QPixmap.fromImage(image)
