import numpy as np
import time
import joblib

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .target_presenter import TargetPresenter


class CalibrationWidget(QWidget):
    predictor_changed = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.calibration_step = None
        self.markers = None

        self.target_presenter = TargetPresenter(self)
        self.target_presenter.presentation_finished.connect(
            self.on_presentation_finished
        )
        self.map_to_scene_video = None

        self.setVisible(False)

    @property
    def map_to_scene_video(self):
        return self.target_presenter.map_to_scene_video

    @map_to_scene_video.setter
    def map_to_scene_video(self, value):
        self.target_presenter.map_to_scene_video = value

    def start(self, markers):
        self.setVisible(True)
        self.markers = markers
        self.calibration_step = "training"
        targets = self._generate_target_locations("training", markers)
        self.target_presenter.start(targets)

    def _generate_target_locations(self, mode, markers):
        width = self.width()
        height = self.height()
        training_steps = 7
        if mode == "training":
            hor_padd = 15
            ver_padd = 15
            hor_targets = np.linspace(hor_padd, width - hor_padd, training_steps)
            ver_targets = np.linspace(ver_padd, height - ver_padd, training_steps)
            targets = np.meshgrid(hor_targets, ver_targets)
            targets = np.array(list(zip(targets[0].flatten(), targets[1].flatten())))
        elif mode == "validation":
            hor_padd = 15 + width / ((training_steps - 1) * 2)
            ver_padd = 15 + height / ((training_steps - 1) * 2)
            hor_targets = np.linspace(hor_padd, width - hor_padd, training_steps - 1)
            ver_targets = np.linspace(ver_padd, height - ver_padd, training_steps - 1)
            targets = np.meshgrid(hor_targets, ver_targets)
            targets = np.array(list(zip(targets[0].flatten(), targets[1].flatten())))

        target_candidates = [QPoint(*t) for t in targets]
        targets = []
        for t in target_candidates:
            t_global = self.mapToGlobal(t)
            for m in markers:
                t_local = m.mapFromGlobal(t_global)
                overlap = False
                if m.rect().contains(t_local):
                    overlap = True
                    break

            if not overlap:
                targets.append(t)

        return targets

    def stop(self):
        self.setVisible(False)
        self.calibration_step = None
        self.target_presenter.stop()

    def update_data(self, eye_tracking_data):
        self.target_presenter.update_data(eye_tracking_data)

    def on_presentation_finished(self, gaze_data, target_data):
        if self.calibration_step == "training":
            np.save("training_gaze_data.npy", gaze_data)
            np.save("training_target_data.npy", target_data)
            self._estimate_predictor(gaze_data, target_data)
            self.predictor_changed.emit()
            self.calibration_step = "validation"
            targets = self._generate_target_locations("validation", self.markers)
            self.target_presenter.start(targets)
        elif self.calibration_step == "validation":
            np.save("validation_gaze_data.npy", gaze_data)
            np.save("validation_target_data.npy", target_data)
            self._validate_predictor(gaze_data, target_data)
            self.stop()

    def _estimate_predictor(self, gaze_data, target_data):
        predictor = Pipeline(
            [
                ("poly", PolynomialFeatures(degree=3, include_bias=True)),
                ("linear", LinearRegression()),
            ]
        )

        predictor.fit(gaze_data, target_data)
        joblib.dump(predictor, "predictor.pkl")

    def _validate_predictor(self, gaze_data, target_data):
        predictor = joblib.load("predictor.pkl")
        predictions = predictor.predict(gaze_data)
        error_orig = np.linalg.norm(gaze_data - target_data, axis=1).mean()
        error_corrected = np.linalg.norm(predictions - target_data, axis=1).mean()
        print(f"Error orig: {error_orig} \t Error corrected: {error_corrected}")

    def resizeEvent(self, event):
        self.target_presenter.resize(self.size())
