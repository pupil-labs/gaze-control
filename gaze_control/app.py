from pupil_labs.realtime_api.simple import discover_one_device
from pupil_labs.real_time_screen_gaze.gaze_mapper import GazeMapper

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

import pyautogui

from .ui import TagWindow
from .dwell_detector import DwellDetector

pyautogui.FAILSAFE = False

class PupilPointerApp(QApplication):
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
        self.tag_window.mouse_enable_changed.connect(self.setMouseEnabled)
        self.tag_window.smoothing_changed.connect(self.setSmoothing)


        self.pollTimer = QTimer()
        self.pollTimer.setInterval(1000/30)
        self.pollTimer.timeout.connect(self.poll)

        self.surface = None
        self.first_poll = True

        self.mouse_position = None
        self.gaze_mapper = None

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

    def setMouseEnabled(self, enabled):
        self.mouse_enabled = enabled

    def setSmoothing(self, value):
        self.smoothing = value

    def poll(self):
        frame_and_gaze = self.device.receive_matched_scene_video_frame_and_gaze(timeout_seconds=1/15)

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
