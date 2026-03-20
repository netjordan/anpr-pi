from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class CameraConfig:
    device: int | str = 0
    width: int = 1280
    height: int = 720
    fps: int = 15


@dataclass(slots=True)
class PipelineConfig:
    frame_interval_ms: int = 750
    plate_cooldown_seconds: int = 20
    min_confidence: float = 78.0
    save_snapshots: bool = True
    snapshot_dir: str = "./data/snapshots"
    overlay_preview: bool = False


@dataclass(slots=True)
class StorageConfig:
    database_path: str = "./data/anpr.db"


@dataclass(slots=True)
class AlertsConfig:
    enabled: bool = True
    repeat_only: bool = True
    sound_path: str = "./data/repeat_alert.wav"
    frequency_hz: int = 880
    duration_ms: int = 180
    repeat_count: int = 2
    repeat_gap_ms: int = 100


@dataclass(slots=True)
class AnprConfig:
    command: str = "alpr"
    country_scope: str = "eu"
    top_n: int = 5


@dataclass(slots=True)
class AppConfig:
    camera: CameraConfig
    pipeline: PipelineConfig
    storage: StorageConfig
    alerts: AlertsConfig
    anpr: AnprConfig

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        return cls(
            camera=CameraConfig(**data.get("camera", {})),
            pipeline=PipelineConfig(**data.get("pipeline", {})),
            storage=StorageConfig(**data.get("storage", {})),
            alerts=AlertsConfig(**data.get("alerts", {})),
            anpr=AnprConfig(**data.get("anpr", {})),
        )


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    config = AppConfig.from_dict(raw)
    ensure_runtime_dirs(config)
    return config


def ensure_runtime_dirs(config: AppConfig) -> None:
    Path(config.storage.database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    Path(config.pipeline.snapshot_dir).expanduser().resolve().mkdir(parents=True, exist_ok=True)
    Path(config.alerts.sound_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
