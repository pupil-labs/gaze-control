import itertools
import time

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtGui import QPaintEvent
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QSoundEffect

from widgets.gaze_button import GazeButton, ButtonStyle
from gaze_event_type import GazeEventType
import actions

from enum import Enum


class Page(Enum):
    LETTERS = 0
    CAPS = 1
    SPECIAL = 2


class Keyboard(QWidget):
    keyPressed = Signal(str)

    def __init__(self, parent=None, opacity=0.6):
        super().__init__(parent)

        self.opacity = opacity
        self.caps = False
        self.page_change_sound = QSoundEffect()
        self.page_change_sound.setSource(QUrl.fromLocalFile("key-stroke.wav"))

        layout = QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.n_rows = 4
        self.n_cols = 10
        for i in range(self.n_cols):
            layout.setColumnStretch(i, 1)
        for i in range(self.n_rows):
            layout.setRowStretch(i, 1)

        self.last_page_change_ts = 0
        self.pages = {}

        qwerty = "qwertyuiopasdfghjklzxcvbnm"
        key_codes = [*qwerty] + ["space", "backspace"]
        regular_style = ButtonStyle(background_color="white")
        hover_style = ButtonStyle(background_color="lightgray")
        self.pages[Page.LETTERS] = self._generate_page(
            layout, key_codes, regular_style, hover_style
        )

        key_codes = [*qwerty.upper()] + ["space", "backspace"]
        regular_style = ButtonStyle(background_color="#FFCCCB")
        hover_style = ButtonStyle(background_color="white")
        self.pages[Page.CAPS] = self._generate_page(
            layout, key_codes, regular_style, hover_style
        )

        key_codes = [*"1234567890-+=@#$%^*()_!?,."] + ["enter"]
        regular_style = ButtonStyle(background_color="lightblue")
        hover_style = ButtonStyle(background_color="white")
        self.pages[Page.SPECIAL] = self._generate_page(
            layout, key_codes, regular_style, hover_style
        )
        self._set_page(Page.LETTERS, sound=False)

        self.keys = list(itertools.chain.from_iterable(self.pages.values()))

        self.setLayout(layout)

        self._setup_edge_actions()

        if self.opacity != 1.0:
            op = QGraphicsOpacityEffect(self)
            op.setOpacity(opacity)
            self.setGraphicsEffect(op)
            self.setAutoFillBackground(True)

    def _generate_page(self, layout, codes, regular_style, hover_style):
        keys = []
        for idx, key in enumerate(codes):
            row_idx = idx // self.n_cols
            col_idx = idx % self.n_cols
            if row_idx == 2:
                col_idx += 1

            k = GazeButton(key, regular_style=regular_style, hover_style=hover_style)
            keys.append(k)
            layout.addWidget(k, row_idx, col_idx, 1, 1)

        for key in keys:
            key.clicked.connect(lambda v: self.keyPressed.emit(v))

        return keys

    def _setup_edge_actions(self):
        edge_action_configs = []

        a_config = actions.EdgeActionConfig()
        a = actions.KeyPressAction("page")
        a_config.action = a
        a_config.event = GazeEventType.GAZE_ENTER
        a_config.screen_edge = actions.ScreenEdge.RIGHT_BOTTOM
        edge_action_configs.append(a_config)
        a.key_pressed.connect(self._toggle_special)

        a_config = actions.EdgeActionConfig()
        a = actions.KeyPressAction("caps")
        a_config.action = a
        a_config.event = GazeEventType.GAZE_ENTER
        a_config.screen_edge = actions.ScreenEdge.LEFT_BOTTOM
        edge_action_configs.append(a_config)
        a.key_pressed.connect(self._toggle_caps)

        self.edge_action_handler = actions.EdgeActionHandler(
            QApplication.primaryScreen(), edge_action_configs
        )

    def _set_page(self, value: Page, sound=True):
        if time.time() - self.last_page_change_ts < 1.5:
            return
        self.last_page_change_ts = time.time()
        if sound:
            self.page_change_sound.play()

        self.current_page = value
        for page, keys in self.pages.items():
            if page == value:
                for key in keys:
                    key.setVisible(True)
            else:
                for key in keys:
                    key.setVisible(False)

    def update_data(self, eye_tracking_data):
        if eye_tracking_data.gaze is None:
            return

        for key in self.keys:
            key.update_data(eye_tracking_data)

        self.edge_action_handler.update_data(eye_tracking_data)

    def _toggle_caps(self):
        if self.current_page == Page.CAPS:
            self._set_page(Page.LETTERS)
        else:
            self._set_page(Page.CAPS)

    def _toggle_special(self):
        if self.current_page == Page.SPECIAL:
            self._set_page(Page.LETTERS)
        else:
            self._set_page(Page.SPECIAL)

    def paintEvent(self, event: QPaintEvent) -> None:
        if self.opacity == 1.0:
            with QPainter(self) as painter:
                painter.setBrush(Qt.gray)
                painter.drawRect(self.rect())

        return super().paintEvent(event)
