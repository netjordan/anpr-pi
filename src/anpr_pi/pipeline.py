from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2

from anpr_pi.alerts import AlertPlayer
from anpr_pi.anpr import OpenAlprCliEngine
from anpr_pi.camera import CameraStream
from anpr_pi.config import AppConfig
from anpr_pi.country import guess_country
from anpr_pi.models import PlateDetection
from anpr_pi.storage import AnprStorage


LOGGER = logging.getLogger(__name__)


class AnprPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.camera = CameraStream(config.camera)
        self.engine = OpenAlprCliEngine(config.anpr, config.pipeline)
        self.storage = AnprStorage(config.storage.database_path)
        self.alerts = AlertPlayer(config.alerts)
        self.cooldowns: dict[str, datetime] = {}

    def run_forever(self) -> None:
        self.storage.initialize()
        self.camera.open()
        LOGGER.info("ANPR pipeline started")
        try:
            while True:
                frame = self.camera.read()
                self._process_frame(frame)
                if self.config.pipeline.overlay_preview:
                    cv2.imshow("ANPR Preview", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                time.sleep(self.config.pipeline.frame_interval_ms / 1000)
        finally:
            self.camera.close()
            self.storage.close()
            cv2.destroyAllWindows()

    def _process_frame(self, frame) -> None:
        try:
            detections = self.engine.detect(frame)
        except Exception as exc:
            LOGGER.exception("ANPR detection failed: %s", exc)
            return

        for detection in detections:
            if self._is_in_cooldown(detection):
                continue

            country = guess_country(detection)
            snapshot_path = self._save_snapshot(frame, detection) if self.config.pipeline.save_snapshots else None
            result = self.storage.upsert_sighting(detection, country, snapshot_path)
            self.cooldowns[detection.plate_text] = datetime.now(timezone.utc)

            LOGGER.info(
                "plate=%s confidence=%.1f country=%s repeated=%s sightings=%s",
                detection.plate_text,
                detection.confidence,
                country.code,
                result.already_seen,
                result.sightings_count,
            )

            if result.already_seen and self.config.alerts.repeat_only:
                self.alerts.play_repeat_alert()
            elif not self.config.alerts.repeat_only:
                self.alerts.play_repeat_alert()

    def _is_in_cooldown(self, detection: PlateDetection) -> bool:
        last_seen = self.cooldowns.get(detection.plate_text)
        if last_seen is None:
            return False
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.config.pipeline.plate_cooldown_seconds)
        return last_seen > cutoff

    def _save_snapshot(self, frame, detection: PlateDetection) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{timestamp}_{detection.plate_text}.jpg"
        path = Path(self.config.pipeline.snapshot_dir).expanduser().resolve() / filename
        annotated = frame.copy()
        if detection.width > 0 and detection.height > 0:
            cv2.rectangle(
                annotated,
                (detection.x, detection.y),
                (detection.x + detection.width, detection.y + detection.height),
                (0, 255, 0),
                2,
            )
        cv2.putText(
            annotated,
            detection.plate_text,
            (max(0, detection.x), max(20, detection.y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        cv2.imwrite(str(path), annotated)
        return str(path)
