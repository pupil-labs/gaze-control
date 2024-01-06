from enum import Enum, auto

import pyautogui

registered_actions = []

class Action:
    def __init_subclass__(cls):
        registered_actions.append(cls)


class ScreenEdge(Enum):
    TOP_LEFT = auto()
    TOP = auto()
    TOP_RIGHT = auto()
    LEFT = auto()
    RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM = auto()
    BOTTOM_RIGHT = auto()

    def __str__(self):
        return self.name.replace('_', ' ').title()


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


class DoNothingAction(Action):
    friendly_name = 'Do Nothing'


class Debug_Action(Action):
    friendly_name = 'Debug'

    def __init__(self):
        self._message = 'FLAG'
    
    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, value):
        self._message = value

    def execute(self):
        print('Debug action:', self._message)


class Scroll_Action(Action):
    friendly_name = 'Scroll'

    def __init__(self):
        self._direction = Direction.UP
        self._magnitude = 1
    
    @property
    def direction(self) -> Direction:
        return self._direction
    
    @direction.setter
    def direction(self, value):
        self._direction = value

    @property
    def magnitude(self) -> int:
        return self._magnitude

    @magnitude.setter
    def magnitude(self, value):
        self._magnitude = value

    def execute(self):
        magnitude = self._magnitude
        if self._direction in [Direction.LEFT, Direction.DOWN]:
            magnitude *= -1

        if self._direction in [Direction.LEFT, Direction.RIGHT]:
            pyautogui.hscroll(magnitude)
        else:
            pyautogui.scroll(magnitude)
