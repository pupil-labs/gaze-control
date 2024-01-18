from collections import namedtuple
import numpy as np
import joblib
import os
import cv2

from pupil_labs.real_time_screen_gaze.gaze_mapper import GazeMapper
from pupil_labs.realtime_api import GazeData

from .raw_data_receiver import RawDataReceiver
from .marker import Marker
from .dwell_detector import DwellDetector


EyeTrackingData = namedtuple(
    "EyeTrackingData",
    [
        "timestamp",
        "gaze",
        "detected_markers",
        "dwell_process",
        "scene",
        "raw_gaze",
        "surf_to_img_trans",
    ],
)


class EyeTrackingProvider(RawDataReceiver):
    def __init__(self, markers, screen_size):
        super().__init__()
        self.markers = markers
        self.screen_size = screen_size

        self.load_predictor()

        self.surface = None
        self.gazeMapper = None
        self.dwell_detector = DwellDetector()

    def load_predictor(self):
        self.predictor = None
        if os.path.exists("predictor.pkl"):
            self.predictor = joblib.load("predictor.pkl")
            print("Loaded predictor.")
        else:
            print("No predictor found. Providing uncorrected gaze.")

    def connect(self, auto_discover=False, ip=None, port=None):
        result = super().connect(auto_discover, ip, port)

        if result is None:
            return None
        else:
            self.K = self.scene_calibration["scene_camera_matrix"][0]
            self.K_inv = np.linalg.inv(self.K)
            self.D = self.scene_calibration["scene_distortion_coefficients"][0]
            self.gazeMapper = GazeMapper(self.scene_calibration)
            self.update_surface()
            return result

    def update_surface(self):
        if self.gazeMapper is None:
            return

        self.gazeMapper.clear_surfaces()
        verts = {
            i: self.markers[i].get_marker_verts() for i in range(len(self.markers))
        }
        self.surface = self.gazeMapper.add_surface(verts, self.screen_size)

    def receive(self) -> EyeTrackingData:
        raw_data = super().receive()

        if raw_data is None:
            return None

        mapped_gaze, detected_markers, surf_to_img_trans = self._map_gaze(
            raw_data.scene, raw_data.raw_gaze
        )

        dwell_process = self.dwell_detector.addPoint(
            mapped_gaze, raw_data.raw_gaze.timestamp_unix_seconds
        )

        eye_tracking_data = EyeTrackingData(
            raw_data.raw_gaze.timestamp_unix_seconds,
            mapped_gaze,
            detected_markers,
            dwell_process,
            raw_data.scene,
            raw_data.raw_gaze,
            surf_to_img_trans,
        )

        return eye_tracking_data

    def _map_gaze(self, frame, gaze):
        assert self.surface is not None

        if self.predictor is not None:
            g = np.array([gaze.x, gaze.y])
            g = self.predictor.predict([g])[0]
            gaze = GazeData(g[0], g[1], gaze[2], gaze[3])

        result = self.gazeMapper.process_frame(frame, gaze)

        detected_markers = [int(marker.uid.split(":")[-1]) for marker in result.markers]
        gaze = None

        if self.surface.uid in result.mapped_gaze:
            for surface_gaze in result.mapped_gaze[self.surface.uid]:
                gaze = surface_gaze.x, surface_gaze.y
                gaze = (
                    gaze[0] * self.screen_size[0],
                    (1 - gaze[1]) * self.screen_size[1],
                )
        surf_to_img_trans = None
        if result.located_aois[self.surface.uid] is not None:
            surf_to_img_trans = result.located_aois[
                self.surface.uid
            ].transform_matrix_from_surface_to_image_undistorted

        return gaze, detected_markers, surf_to_img_trans

    def map_to_scene_video(self, screen_point, transform):
        screen_point = screen_point[0] / self.screen_size[0], 1 - (
            screen_point[1] / self.screen_size[1]
        )

        g_hom = np.array([screen_point[0], screen_point[1], 1])
        g_scene_undist_hom = transform @ g_hom
        g_scene_undist_3d = self.K_inv @ g_scene_undist_hom

        g_scene_dist_2d = cv2.projectPoints(
            g_scene_undist_3d.reshape(1, 1, 3), np.zeros(3), np.zeros(3), self.K, self.D
        )[0].reshape(2)
        return g_scene_dist_2d


class DummyEyeTrackingProvider:
    def __init__(self, markers, screen_size, use_calibrated_gaze):
        self.dwell_detector = DwellDetector()
        self.device = "dummy_device"

    def receive(self) -> EyeTrackingData:
        import time
        import pyautogui

        ts = time.time()

        p = pyautogui.position()
        # TODO: For some reason the resolution of the app is not actually equal to the screen resolution. You have to devide it by the primaryScreen.devicePixelRatio() to correctly place it.
        p = p[0] / 1.25, p[1] / 1.25

        dwell_process = self.dwell_detector.addPoint(p, ts)

        scene_img = np.zeros((1600, 1200, 3), dtype=np.uint8)
        scene = type("", (object,), {"bgr_pixels": scene_img})()

        raw_gaze = type(
            "", (object,), {"timestamp_unix_seconds": ts, "x": 500, "y": 500}
        )()

        eye_tracking_data = EyeTrackingData(ts, p, [], dwell_process, scene, raw_gaze)

        return eye_tracking_data

    def connect(self, auto_discover=False, ip=None, port=None):
        return "dummy_ip", 1234

    def update_surface(self):
        pass

    def close(self):
        pass
