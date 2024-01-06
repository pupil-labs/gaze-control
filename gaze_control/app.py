from pupil_labs.realtime_api.simple import discover_one_device
from pupil_labs.real_time_screen_gaze.gaze_mapper import GazeMapper

from PySide6.QtCore import (
    QRect,
    QTimer,
)
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCursor

import pyautogui

from .ui import TagWindow
from .dwell_detector import DwellDetector
from .actions import ScreenEdge

pyautogui.FAILSAFE = False

class PupilPointerApp(QApplication):
    @staticmethod
    def instance():
        return QApplication.instance()

    def __init__(self):
        super().__init__()

        self.setApplicationDisplayName('Pupil Pointer')
        self.mouse_enabled = False

        self.tag_window = TagWindow()

        self.device = None
        self.dwell_detector = DwellDetector(.75, 75)
        self.smoothing = 0.8

        self.tag_window.surface_changed.connect(self.on_surface_chhanged)

        self.tag_window.dwell_time_changed.connect(self.dwell_detector.set_duration)
        self.tag_window.dwell_radius_changed.connect(self.dwell_detector.set_range)
        self.tag_window.mouse_enable_changed.connect(self.set_mouse_enabled)
        self.tag_window.smoothing_changed.connect(self.set_smoothing)

        self.pollTimer = QTimer()
        self.pollTimer.setInterval(1000/30)
        self.pollTimer.timeout.connect(self.poll)

        self.surface = None
        self.first_poll = True

        self.mouse_position = None
        self.gaze_mapper = None


        w = self.primaryScreen().size().width()
        h = self.primaryScreen().size().height()

        size = 500
        self.edge_regions = {
            ScreenEdge.TOP_LEFT:     QRect(-size, -size, size, size),
            ScreenEdge.TOP:          QRect(    0, -size,    w, size),
            ScreenEdge.TOP_RIGHT:    QRect(    w, -size, size, size),
            ScreenEdge.LEFT:         QRect(-size,     0, size,    h),
            ScreenEdge.RIGHT:        QRect(    w,     0, size,    h),
            ScreenEdge.BOTTOM_LEFT:  QRect(-size,     h, size, size),
            ScreenEdge.BOTTOM:       QRect(    0,     h,    w, size),
            ScreenEdge.BOTTOM_RIGHT: QRect(    w,     h, size, size),
        }

        self.edge_actions = {}


    def on_surface_chhanged(self):
        self.update_surface()

    def start(self):
        self.device = discover_one_device(max_search_duration_seconds=0.25)

        if self.device is None:
            QTimer.singleShot(1000, self.start)
            return

        calibration = self.device.get_calibration()
        self.gaze_mapper = GazeMapper(calibration)

        self.tag_window.set_status(f'Connected to {self.device}. One moment...')

        self.update_surface()
        self.pollTimer.start()
        self.first_poll = True

    def update_surface(self):
        if self.gaze_mapper is None:
            return

        self.gaze_mapper.clear_surfaces()
        self.surface = self.gaze_mapper.add_surface(
            self.tag_window.get_marker_verts(),
            self.tag_window.get_surface_size()
        )

    def set_mouse_enabled(self, enabled):
        self.mouse_enabled = enabled

    def set_smoothing(self, value):
        self.smoothing = value

    def set_edge_action(self, edge, action):
        self.edge_actions[edge] = action

    def poll(self):
        frame_and_gaze = self.device.receive_matched_scene_video_frame_and_gaze(timeout_seconds=1/30)

        if frame_and_gaze is None:
            return

        else:
            self.tag_window.set_status(f'Streaming data from {self.device}')
            self.first_poll = False

        frame, gaze = frame_and_gaze
        result = self.gaze_mapper.process_frame(frame, gaze)

        markerIds = [int(marker.uid.split(':')[-1]) for marker in result.markers]
        self.tag_window.show_marker_feedback(markerIds)

        if self.surface.uid in result.mapped_gaze:
            for surface_gaze in result.mapped_gaze[self.surface.uid]:
                if self.mouse_position is None:
                    self.mouse_position = [surface_gaze.x, surface_gaze.y]

                else:
                    self.mouse_position[0] = self.mouse_position[0] * self.smoothing + surface_gaze.x * (1.0 - self.smoothing)
                    self.mouse_position[1] = self.mouse_position[1] * self.smoothing + surface_gaze.y * (1.0 - self.smoothing)

                mouse_point = self.tag_window.update_point(*self.mouse_position)

                changed, dwell, dwell_position = self.dwell_detector.add_point(mouse_point.x(), mouse_point.y(), gaze.timestamp_unix_seconds)
                if changed and dwell:
                    print('dwell at', dwell_position)

                    for edge,rect in self.edge_regions.items():
                        if rect.contains(mouse_point) and edge in self.edge_actions:
                            action = self.edge_actions[edge]
                            action.execute()
                            break
                    else:
                        self.tag_window.set_clicked(True)
                        if self.mouse_enabled:
                            pyautogui.click(x=dwell_position[0], y=dwell_position[1])
                else:
                    self.tag_window.set_clicked(False)

                if self.mouse_enabled:
                    QCursor().setPos(mouse_point)

    def exec(self):
        self.tag_window.set_status('Looking for a device...')
        self.tag_window.showMaximized()
        QTimer.singleShot(1000, self.start)
        super().exec()

        if self.device is not None:
            self.device.close()

def run():
    app = PupilPointerApp()
    app.exec()
