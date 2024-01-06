from enum import Enum, auto

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .actions import (
    Action,
    registered_actions,
    ScreenEdge,
)
from .property_widget import (
    create_property_widget,
    get_properties
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


class ActionOptionsWidget(QWidget):
    edge_action_changed = Signal(ScreenEdge, Action)

    def __init__(self):
        super().__init__()

        self.setLayout(QVBoxLayout())

        for edge in ScreenEdge:
            edge_action_widget = ActionWidget(str(edge))
            self.layout().addWidget(edge_action_widget)
            edge_action_widget.action_changed.connect(lambda action, edge=edge: self.on_action_changed(edge, action))

    def on_action_changed(self, edge, action):
        QApplication.instance().set_edge_action(edge, action)


class ActionWidget(QWidget):
    action_changed = Signal(object)

    def __init__(self, label_text):
        super().__init__()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel(label_text))

        self.action_selector = QComboBox()
        for action in registered_actions:
            self.action_selector.addItem(action.friendly_name, action)

        self.action_selector.currentIndexChanged.connect(self.on_action_index_changed)

        self.layout().addWidget(self.action_selector)

        self.parameters_container = QWidget()
        self.parameters_container.setLayout(QFormLayout())

        self.layout().addWidget(self.parameters_container)

    def on_action_index_changed(self, idx):
        action_cls = self.action_selector.itemData(idx)
        action = action_cls()
        self.set_value(action)

        self.action_changed.emit(action)

    def set_value(self, action):
        param_layout = self.parameters_container.layout()
        while param_layout.count() > 0:
            w = param_layout.takeAt(0).widget()
            w.setParent(None)

        props = get_properties(action.__class__)
        for property_name, prop in props.items():
            widget = create_property_widget(prop)
            widget.setValue(prop.fget(action))
            widget.valueChanged.connect(lambda v, prop=prop: prop.fset(action, v))

            param_layout.addRow(property_name, widget)
