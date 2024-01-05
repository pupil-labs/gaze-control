import numpy as np
import math

class DwellDetector():
    def __init__(self, minimum_delay_seconds, range_pixels):
        self.minimum_delay = minimum_delay_seconds
        self.range = range_pixels
        self.points = np.empty(shape=[0, 3])

        self.inDwell = False

    def set_duration(self, duration):
        self.minimum_delay = duration

    def set_range(self, range_pixels):
        self.range = range_pixels

    def add_point(self, x, y, timestamp):
        point = np.array([x, y, timestamp])

        self.points = np.append(self.points, [point], axis=0)
        if self.points[-1,2] - self.points[0,2] < self.minimum_delay:
            return False, False, None

        min_timestamp = timestamp - self.minimum_delay - .0001
        self.points = self.points[self.points[:,2] >= min_timestamp]

        center = np.mean(self.points[:,:2], axis=0)
        distances = np.sqrt(np.sum(self.points[:,:2] - center, axis=1)**2)

        if np.max(distances) < self.range:
            in_dwell = True
        else:
            in_dwell = False

        changed = in_dwell != self.inDwell
        self.inDwell = in_dwell

        return changed, in_dwell, center

