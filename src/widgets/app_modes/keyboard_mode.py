import itertools
import time
from .app_mode import AppMode

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QSoundEffect

from eye_tracking_provider import EyeTrackingData

from widgets.gaze_button import GazeButton, ButtonStyle
from gaze_event_type import GazeEventType
import actions

from enum import Enum


class KeyboardMode(AppMode):
    def __init__(self, parent=None, event_handlers=None):
        super().__init__(parent, event_handlers)

        self.keyboard = Keyboard(self)
        self.keyboard.keyPressed.connect(event_handlers["on_key_pressed"])

    def _update_data(self, eye_tracking_data: EyeTrackingData):
        self.keyboard.update_data(eye_tracking_data)

    def resize(self, size):
        super().resize(size)
        height_ratio = 0.55
        self.keyboard.setGeometry(
            0,
            size.height() * (1 - height_ratio),
            size.width(),
            size.height() * height_ratio,
        )


class Page(Enum):
    LETTERS = 0
    CAPS = 1
    SPECIAL = 2


class Keyboard(QWidget):
    keyPressed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.page_change_sound = QSoundEffect()
        self.page_change_sound.setSource(QUrl.fromLocalFile("key-stroke.wav"))
        self.last_page_change_ts = 0

        self.pages = {}
        qwerty = "qwertyuiopasdfghjklzxcvbnm"
        key_codes = [*qwerty] + ["space"]
        self.pages[Page.LETTERS] = self._create_page(
            key_codes,
            ButtonStyle(),
            ButtonStyle(background_color="lightgray"),
        )
        key_codes = [*qwerty.upper()] + ["space"]
        self.pages[Page.CAPS] = self._create_page(
            key_codes,
            ButtonStyle("#FFCCCB"),
            ButtonStyle(background_color="white"),
        )
        key_codes = [*"1234567890-=!@#$%^*()_+,."] + ["backspace", "enter"]
        self.pages[Page.SPECIAL] = self._create_page(
            key_codes,
            ButtonStyle("lightblue"),
            ButtonStyle(background_color="white"),
        )

        self._set_page(Page.LETTERS)

        self.keys = list(itertools.chain.from_iterable(self.pages.values()))

        self._setup_edge_actions()

        op = QGraphicsOpacityEffect(self)
        op.setOpacity(0.6)
        self.setGraphicsEffect(op)
        self.setAutoFillBackground(True)

    def _arrange_keys(self, keys):
        width = self.width() / 10
        height = self.height() / 10 * 4  # 3 * 1.1
        # * math.sqrt(3) / 2

        row_idx = 0
        col_idx = 0
        margin_left = 0
        for idx, key in enumerate(keys):
            if idx in [10, 19]:
                row_idx += 1
                col_idx = 0
                margin_left += width / 2
            x = margin_left + col_idx * width

            y = row_idx * height * (3 / 4)
            key.setGeometry(x, y, width, height)
            col_idx += 1

    def _create_page(self, key_codes, regular_style, hover_style):
        keys = []
        for key in key_codes:
            k = Key(
                key, regular_style=regular_style, hover_style=hover_style, parent=self
            )
            keys.append(k)

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

    def _set_page(self, value: Page):
        if time.time() - self.last_page_change_ts < 1.5:
            return
        self.last_page_change_ts = time.time()
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

    def resizeEvent(self, _):
        for page in self.pages.values():
            self._arrange_keys(page)


class Key(GazeButton):
    def toggleCaps(self):
        if self.text().isupper():
            self.setText(self.text().lower())
            self.code = self.code.lower()
        else:
            self.setText(self.text().upper())
            self.code = self.code.upper()
