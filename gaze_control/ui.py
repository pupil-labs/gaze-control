import sys

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pupil_labs.real_time_screen_gaze import marker_generator

def create_marker(marker_id):
    marker = marker_generator.generate_marker(marker_id, flip_x=True, flip_y=True)

    image = QImage(10, 10, QImage.Format_Mono)
    image.fill(1)
    for y in range(marker.shape[0]):
        for x in range(marker.shape[1]):
            color = marker[y][x]//255
            image.setPixel(x+1, y+1, color)

    # Convert the QImage to a QPixmap
    return QPixmap.fromImage(image)

def point_to_tuple(qpoint):
    return (qpoint.x(), qpoint.y())

class TagWindow(QWidget):
    surface_changed = Signal()
    mouse_enable_changed = Signal(bool)
    dwell_radius_changed = Signal(int)
    dwell_time_changed = Signal(float)
    smoothing_changed = Signal(float)

    def __init__(self):
        super().__init__()

        self.setStyleSheet('* { font-size: 18pt }')

        self.markerIDs = []
        self.pixmaps = []
        for markerID in range(4):
            self.markerIDs.append(markerID)
            self.pixmaps.append(create_marker(markerID))

        self.point = (0, 0)
        self.clicked = False
        self.settings_visible = True
        self.visibleMarkerIds = []

        self.tabs = QTabWidget()
        self.forms = {
            'Tags': TagOptionsWidget(),
            'Mouse': MouseOptionsWidget(),
        }

        self.forms['Tags'].tag_size_changed.connect(lambda _: self.repaint())
        self.forms['Tags'].tag_brightness_changed.connect(lambda _: self.repaint())
        self.forms['Mouse'].smoothing_changed.connect(self.smoothing_changed.emit)
        self.forms['Mouse'].dwell_radius_changed.connect(self.dwell_radius_changed.emit)
        self.forms['Mouse'].dwell_time_changed.connect(self.dwell_time_changed.emit)
        self.forms['Mouse'].mouse_enabled_changed.connect(self.mouse_enable_changed.emit)

        for form_name, form in self.forms.items():
            self.tabs.addTab(form, form_name)

        self.instructions_label = QLabel('Right-click one of the tags to toggle settings view.')
        self.instructions_label.setAlignment(Qt.AlignHCenter)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignHCenter)

        self.setLayout(QGridLayout())
        self.layout().setSpacing(50)

        self.layout().addWidget(self.instructions_label, 0, 0, 1, 3)
        self.layout().addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), 1, 1, 1, 1)
        self.layout().addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 2, 0, 1, 1)
        self.layout().addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 2, 2, 1, 1)
        self.layout().addWidget(self.tabs, 3, 1, 1, 1)
        self.layout().addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), 4, 1, 1, 1)
        self.layout().addWidget(self.status_label, 5, 0, 1, 3)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.set_settings_visible(not self.settings_visible)

    def set_settings_visible(self, visible):
        self.settings_visible = visible

        if sys.platform.startswith('darwin'):
            self.hide()
            self.setWindowFlag(Qt.FramelessWindowHint, not visible)
            self.setWindowFlag(Qt.WindowStaysOnTopHint, not visible)
            self.setAttribute(Qt.WA_TranslucentBackground, not visible)

            if visible:
                self.show()
            else:
                self.showMaximized()

        self.update_mask()

    def set_status(self, status):
        self.status_label.setText(status)

    def set_clicked(self, clicked):
        self.clicked = clicked
        self.repaint()

    def update_point(self, norm_x, norm_y):
        tag_margin = 0.1 * self.get_marker_size()
        surface_size = (
            self.width() - 2*tag_margin,
            self.height() - 2*tag_margin,
        )

        self.point = (
            norm_x*surface_size[0] + tag_margin,
            (surface_size[1] - norm_y*surface_size[1]) + tag_margin
        )

        self.repaint()
        return self.mapToGlobal(QPoint(*self.point))

    def show_marker_feedback(self, markerIds):
        self.visibleMarkerIds = markerIds
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.settings_visible:
            if self.clicked:
                painter.setBrush(Qt.red)
            else:
                painter.setBrush(Qt.white)

            painter.drawEllipse(QPoint(*self.point), self.get_dwell_radius(), self.get_dwell_radius())

        for cornerIdx in range(4):
            cornerRect = self.get_corner_rect(cornerIdx)
            if cornerIdx not in self.visibleMarkerIds:
                painter.fillRect(cornerRect.marginsAdded(QMargins(5, 5, 5, 5)), QColor(255, 0, 0))

            painter.drawPixmap(cornerRect, self.pixmaps[cornerIdx])
            painter.fillRect(cornerRect, QColor(0, 0, 0, 255-self.get_tag_brightness()))

    def resizeEvent(self, event):
        self.update_mask()
        self.surface_changed.emit()

    def onTagSizeChanged(self, value):
        self.repaint()
        self.surface_changed.emit()

    def get_marker_size(self):
        return self.forms['Tags'].tag_size_input.value()

    def get_tag_brightness(self):
        return self.forms['Tags'].tag_brightness_input.value()

    def get_tag_padding(self):
        return self.get_marker_size()/8

    def get_dwell_radius(self):
        return self.forms['Mouse'].dwell_radius_input.value()

    def get_marker_verts(self):
        tag_padding = self.get_tag_padding()
        markers_verts = {}

        for cornerIdx, markerID in enumerate(self.markerIDs):
            rect = self.get_corner_rect(cornerIdx) - QMargins(tag_padding, tag_padding, tag_padding, tag_padding)

            markers_verts[markerID] = [
                point_to_tuple(rect.topLeft()),
                point_to_tuple(rect.topRight()),
                point_to_tuple(rect.bottomRight()),
                point_to_tuple(rect.bottomLeft()),
            ]

        return markers_verts

    def get_surface_size(self):
        return (self.width(), self.height())

    def update_mask(self):
        if self.settings_visible:
            mask = QRegion(0, 0, self.width(), self.height())

        else:
            mask = QRegion(0, 0, 0, 0)
            for cornerIdx in range(4):
                rect = self.get_corner_rect(cornerIdx).marginsAdded(QMargins(2, 2, 2, 2))
                mask = mask.united(rect)

        self.setMask(mask)


    def get_corner_rect(self, corner_idx):
        tag_size = self.get_marker_size()
        tag_size_padded = tag_size + self.get_tag_padding()*2

        if corner_idx == 0:
            return QRect(0, 0, tag_size_padded, tag_size_padded)

        elif corner_idx == 1:
            return QRect(self.width()-tag_size_padded, 0, tag_size_padded, tag_size_padded)

        elif corner_idx == 2:
            return QRect(self.width()-tag_size_padded, self.height()-tag_size_padded, tag_size_padded, tag_size_padded)

        elif corner_idx == 3:
            return QRect(0, self.height()-tag_size_padded, tag_size_padded, tag_size_padded)


class TagOptionsWidget(QWidget):
    tag_size_changed = Signal(int)
    tag_brightness_changed = Signal(int)

    def __init__(self):
        super().__init__()

        self.setLayout(QFormLayout())

        self.tag_size_input = QSpinBox()
        self.tag_size_input.setRange(10, 512)
        self.tag_size_input.setValue(256)
        self.tag_size_input.valueChanged.connect(self.tag_size_changed.emit)

        self.tag_brightness_input = QSpinBox()
        self.tag_brightness_input.setRange(0, 255)
        self.tag_brightness_input.setValue(128)
        self.tag_brightness_input.valueChanged.connect(self.tag_brightness_changed.emit)

        self.layout().addRow('Tag Size', self.tag_size_input)
        self.layout().addRow('Tag Brightness', self.tag_brightness_input)

class MouseOptionsWidget(QWidget):
    smoothing_changed = Signal(float)
    dwell_radius_changed = Signal(int)
    dwell_time_changed = Signal(float)
    mouse_enabled_changed = Signal(bool)

    def __init__(self):
        super().__init__()

        self.setLayout(QFormLayout())

        self.setLayout(QFormLayout())
        self.smoothing_input = QDoubleSpinBox()
        self.smoothing_input.setRange(0, .99)
        self.smoothing_input.setValue(0.8)
        self.smoothing_input.setSingleStep(0.1)
        self.smoothing_input.valueChanged.connect(self.smoothing_changed.emit)

        self.dwell_radius_input = QSpinBox()
        self.dwell_radius_input.setRange(0, 512)
        self.dwell_radius_input.setValue(25)
        self.dwell_radius_input.valueChanged.connect(self.dwell_radius_changed.emit)

        self.dwell_time_input = QDoubleSpinBox()
        self.dwell_time_input.setRange(0, 20)
        self.dwell_time_input.setValue(0.75)
        self.dwell_time_input.valueChanged.connect(self.dwell_time_changed.emit)

        self.mouse_enabled_input = QCheckBox('Mouse Control')
        self.mouse_enabled_input.setChecked(False)
        self.mouse_enabled_input.toggled.connect(self.mouse_enabled_changed.emit)

        self.layout().addRow('Smoothing', self.smoothing_input)
        self.layout().addRow('Dwell Radius', self.dwell_radius_input)
        self.layout().addRow('Dwell Time', self.dwell_time_input)
        self.layout().addRow('', self.mouse_enabled_input)
