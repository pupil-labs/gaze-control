import typing
from enum import Enum

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QSpinBox,
)


def create_property_widget(prop):
    hints = typing.get_type_hints(prop.fget)

    type_hint = str
    if 'return' in hints:
        type_hint = hints['return']

    property_doc = PropertyDocumentation(prop)
    widget = None

    if type_hint == bool:
        widget = QCheckBox()
        widget.setValue = widget.setChecked
        widget.getValue = widget.isChecked
        widget.valueChanged = widget.stateChanged

    elif type_hint == int:
        widget = QSpinBox()

        if 'min' in property_doc.hints:
            widget.setMinimum(int(property_doc.hints['min']))

        if 'max' in property_doc.hints:
            widget.setMaximum(int(property_doc.hints['max']))

    elif type_hint == float:
        widget = QDoubleSpinBox()

        if 'min' in property_doc.hints:
            widget.setMinimum(float(property_doc.hints['min']))

        if 'max' in property_doc.hints:
            widget.setMaximum(float(property_doc.hints['max']))

        if 'decimals' in property_doc.hints:
            widget.setDecimals(int(property_doc.hints['decimals']))

    elif issubclass(type_hint, Enum):
        widget = EnumCombo(type_hint)

    else:
        widget = QLineEdit()
        widget.setValue = widget.setText
        widget.getValue = widget.text
        widget.valueChanged = widget.textChanged

    widget.setToolTip(property_doc.shortDescription)

    return widget

def get_class_properties(cls: type):
	properties = {}
	for key, value in cls.__dict__.items():
		if isinstance(value, property):
			properties[key] = value

	return properties

def get_properties(cls: type):
	properties = {}
	for kls in reversed(cls.mro()):
		class_props = get_class_properties(kls)
		for prop_name, prop in class_props.items():
			properties[prop_name] = prop

	return properties


class PropertyDocumentation():
    def __init__(self, prop):
        self.shortDescription = ''
        self.longDescription = ''
        self.hints = {}

        if prop.fget.__doc__ is None:
            return

        lines = []
        lineIdx = -1
        for line in prop.fget.__doc__.strip().split('\n'):
            line = line.strip()
            if len(line) > 0:
                lineIdx += 1
                if lineIdx == 0 and not line.startswith(':'):
                    self.shortDescription = line
                else:
                    lines.append(line)

        if len(lines) == 0:
            return

        for line in lines:
            if line.startswith(':'):
                left, right = line.split(maxsplit=1)
                self.hints[left[1:]] = right

            else:
                self.longDescription += '\n' + line

        self.longDescription = self.longDescription.strip()



class EnumCombo(QComboBox):
    valueChanged = Signal(object)

    def __init__(self, enumClass):
        super().__init__()

        for e in enumClass:
            label = str(e)

            if label == f'{enumClass.__name__}.{e.name}':
                label = e.name.replace('_', ' ').title()

            self.addItem(label, e)

        self.currentIndexChanged.connect(self.onIndexChanged)

    def getValue(self):
        return self.currentData()

    def setValue(self, value):
        self.setCurrentIndex(self.findData(value))

    def onIndexChanged(self, idx):
        self.valueChanged.emit(self.currentData())



