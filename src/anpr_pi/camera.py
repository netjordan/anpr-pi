from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from anpr_pi.config import CameraConfig


@dataclass(slots=True)
class CameraStream:
    config: CameraConfig
    capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        self.capture = cv2.VideoCapture(self.config.device)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self.capture.set(cv2.CAP_PROP_FPS, self.config.fps)
        if not self.capture.isOpened():
            raise RuntimeError(f"Unable to open camera device: {self.config.device}")

    def read(self) -> np.ndarray:
        if self.capture is None:
            raise RuntimeError("Camera not opened")
        ok, frame = self.capture.read()
        if not ok or frame is None:
            raise RuntimeError("Failed to read frame from camera")
        return frame

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
