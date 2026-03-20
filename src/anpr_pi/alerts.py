from __future__ import annotations

import math
import shutil
import struct
import subprocess
import time
import wave
from pathlib import Path

from anpr_pi.config import AlertsConfig


class AlertPlayer:
    def __init__(self, config: AlertsConfig) -> None:
        self.config = config
        self.sound_path = Path(config.sound_path).expanduser().resolve()
        self._ensure_sound_file()

    def play_repeat_alert(self) -> None:
        if not self.config.enabled:
            return

        player = self._detect_player()
        if player is None:
            print("\a", end="", flush=True)
            return

        for index in range(self.config.repeat_count):
            subprocess.run([player, str(self.sound_path)], check=False, capture_output=True)
            if index < self.config.repeat_count - 1:
                time.sleep(self.config.repeat_gap_ms / 1000)

    def _ensure_sound_file(self) -> None:
        if self.sound_path.exists():
            return
        sample_rate = 44100
        amplitude = 16000
        tone_length_seconds = self.config.duration_ms / 1000
        frame_count = int(sample_rate * tone_length_seconds)
        with wave.open(str(self.sound_path), "w") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(sample_rate)
            for index in range(frame_count):
                sample = amplitude * math.sin(2 * math.pi * self.config.frequency_hz * index / sample_rate)
                handle.writeframes(struct.pack("<h", int(sample)))

    def _detect_player(self) -> str | None:
        for candidate in ("aplay", "paplay", "afplay"):
            path = shutil.which(candidate)
            if path:
                return path
        return None
