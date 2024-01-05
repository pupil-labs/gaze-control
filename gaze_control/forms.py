from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
    QWidget,
)


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
