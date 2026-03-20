from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

from anpr_pi.config import AnprConfig, PipelineConfig
from anpr_pi.models import PlateDetection


class OpenAlprCliEngine:
    def __init__(self, config: AnprConfig, pipeline: PipelineConfig) -> None:
        self.config = config
        self.pipeline = pipeline
        if not Path(config.command).exists() and shutil.which(config.command) is None:
            raise FileNotFoundError(
                f"ANPR command '{config.command}' was not found. Install OpenALPR or set an absolute command path."
            )

    def detect(self, frame: np.ndarray) -> list[PlateDetection]:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
            image_path = Path(handle.name)
        try:
            cv2.imwrite(str(image_path), frame)
            process = subprocess.run(
                [
                    self.config.command,
                    "-j",
                    "-n",
                    str(self.config.top_n),
                    "-c",
                    self.config.country_scope,
                    str(image_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if process.returncode != 0:
                stderr = process.stderr.strip() or process.stdout.strip()
                raise RuntimeError(f"ANPR command failed: {stderr}")
            return self._parse_output(process.stdout)
        finally:
            image_path.unlink(missing_ok=True)

    def _parse_output(self, payload: str) -> list[PlateDetection]:
        data = json.loads(payload)
        results: list[PlateDetection] = []
        for item in data.get("results", []):
            best = item.get("plate", "").upper()
            confidence = float(item.get("confidence", 0.0))
            if not best or confidence < self.pipeline.min_confidence:
                continue
            coordinates = item.get("coordinates", [])
            xs = [point["x"] for point in coordinates] if coordinates else [0, 0]
            ys = [point["y"] for point in coordinates] if coordinates else [0, 0]
            candidates = [candidate["plate"].upper() for candidate in item.get("candidates", [])]
            results.append(
                PlateDetection(
                    plate_text=best,
                    confidence=confidence,
                    x=min(xs),
                    y=min(ys),
                    width=max(xs) - min(xs),
                    height=max(ys) - min(ys),
                    raw_country_hint=item.get("country"),
                    raw_region_hint=item.get("region"),
                    candidates=candidates,
                )
            )
        return results
