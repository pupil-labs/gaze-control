from collections import namedtuple
import numpy as np
import cv2
import joblib
import os

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

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
        "dwell_process",
        "scene",
        "raw_gaze",
        "surf_to_img_trans",
    ],
)


def pixmap2array(pixmap):
    qimage = pixmap.toImage()
    qimage = qimage.convertToFormat(QImage.Format_RGB888)
    array = np.ndarray(
        (qimage.height(), qimage.width(), 3),
        buffer=qimage.constBits(),
        strides=[qimage.bytesPerLine(), 3, 1],
        dtype=np.uint8,
    )
    return array


class EyeTrackingProvider(RawDataReceiver):
    def __init__(self, markers, screen_size, use_calibrated_gaze=True):
        super().__init__()
        self.markers = markers
        self.screen_size = screen_size
        self.K = None
        self.K_inv = None
        self.D = None

        self.predictor = None
        if use_calibrated_gaze and os.path.exists("predictor.pkl"):
            self.predictor = joblib.load("predictor.pkl")
        else:
            print("No predictor found. Providing uncorrected gaze.")

        self.dwell_detector = DwellDetector()

    def connect(self, auto_discover=False, ip=None, port=None):
        result = super().connect(auto_discover, ip, port)

        if result is None:
            return None
        else:
            self.K = self.scene_calibration["scene_camera_matrix"][0]
            self.K_inv = np.linalg.inv(self.K)
            self.D = self.scene_calibration["scene_distortion_coefficients"][0]
            return result

    def receive(self) -> EyeTrackingData:
        raw_data = super().receive()

        if raw_data is None:
            return None

        mapped_gaze, surf_to_img_trans = self._map_gaze(
            raw_data.scene, raw_data.raw_gaze
        )

        if self.predictor is not None and mapped_gaze is not None:
            mapped_gaze = self.predictor.predict([mapped_gaze])[0]

        dwell_process = self.dwell_detector.addPoint(mapped_gaze, raw_data.timestamp)

        eye_tracking_data = EyeTrackingData(
            raw_data.timestamp,
            mapped_gaze,
            dwell_process,
            raw_data.scene,
            raw_data.raw_gaze,
            surf_to_img_trans,
        )

        return eye_tracking_data

    def _map_gaze(self, frame, gaze):
        app = QApplication.instance()
        screen = app.main_window.screen()
        screen_image = screen.grabWindow()
        screen_image = pixmap2array(screen_image)

        screen_image = cv2.resize(screen_image, None, fx=0.25, fy=0.25)

        scene_image = frame.bgr_pixels
        scene_image = cv2.resize(scene_image, None, fx=1 / 3, fy=1 / 3)
        # screen_image = cv2.resize(screen_image, (400, 300))

        sift = cv2.SIFT_create()

        screen_kp, screen_desc = sift.detectAndCompute(screen_image, None)
        scene_kp, scene_desc = sift.detectAndCompute(scene_image, None)

        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(screen_desc, scene_desc, k=2)
        # store all the good matches as per Lowe's ratio test.
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)

        MIN_MATCH_COUNT = 10
        if len(good) > MIN_MATCH_COUNT:
            screen_pts = np.float32([screen_kp[m.queryIdx].pt for m in good]).reshape(
                -1, 1, 2
            )
            screen_pts *= 4

            scene_pts = np.float32([scene_kp[m.trainIdx].pt for m in good]).reshape(
                -1, 1, 2
            )
            scene_pts *= 3

            scene_to_screen_trans, mask = cv2.findHomography(
                scene_pts, screen_pts, cv2.RANSAC, 5.0
            )

            gaze = scene_to_screen_trans @ np.array([gaze.x, gaze.y, 1])
            gaze = gaze[:2] / gaze[2]

            return gaze, scene_to_screen_trans
        else:
            return None, None

    def distort_point(self, p):
        p_hom = np.array([p[0], p[1], 1])
        p_3d = self.K_inv @ p_hom

        p_dist = cv2.projectPoints(
            p_3d.reshape(1, 1, 3), np.zeros(3), np.zeros(3), self.K, self.D
        )[0].reshape(2)
        return p_dist

    def map_surface_to_scene_video(self, surface_point, transform):
        g_hom = np.array([surface_point[0], surface_point[1], 1])
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
        p = p[0] - 200, p[1]

        dwell_process = self.dwell_detector.addPoint(p, ts)

        scene_img = np.zeros((1600, 1200, 3), dtype=np.uint8)
        scene = type("", (object,), {"bgr_pixels": scene_img})()

        raw_gaze = GazeData(500, 500, True, ts)

        eye_tracking_data = EyeTrackingData(
            ts, p, [], dwell_process, scene, raw_gaze, [], None
        )

        return eye_tracking_data

    def connect(self, auto_discover=False, ip=None, port=None):
        return "dummy_ip", 1234

    def update_surface(self):
        pass

    def distort_point(self, p):
        pass

    def map_surface_to_scene_video(self, surface_point, transform):
        pass

    def close(self):
        pass
