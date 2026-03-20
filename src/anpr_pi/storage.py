from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from anpr_pi.models import CountryGuess, PlateDetection


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class SeenPlateResult:
    vehicle_id: int
    plate_text: str
    already_seen: bool
    sightings_count: int


class AnprStorage:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path).expanduser().resolve()
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row

    def initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_text TEXT NOT NULL UNIQUE,
                country_code TEXT NOT NULL,
                country_name TEXT NOT NULL,
                country_confidence REAL NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                sightings_count INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS sightings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                seen_at TEXT NOT NULL,
                confidence REAL NOT NULL,
                country_reason TEXT NOT NULL,
                image_path TEXT,
                bbox_x INTEGER NOT NULL DEFAULT 0,
                bbox_y INTEGER NOT NULL DEFAULT 0,
                bbox_width INTEGER NOT NULL DEFAULT 0,
                bbox_height INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
            );

            CREATE INDEX IF NOT EXISTS idx_sightings_vehicle_id ON sightings(vehicle_id);
            CREATE INDEX IF NOT EXISTS idx_sightings_seen_at ON sightings(seen_at);
            """
        )
        self.connection.commit()

    def upsert_sighting(
        self,
        detection: PlateDetection,
        country: CountryGuess,
        image_path: str | None,
    ) -> SeenPlateResult:
        now = utc_now_iso()
        existing = self.connection.execute(
            "SELECT id, sightings_count FROM vehicles WHERE plate_text = ?",
            (detection.plate_text,),
        ).fetchone()

        if existing is None:
            cursor = self.connection.execute(
                """
                INSERT INTO vehicles (
                    plate_text, country_code, country_name, country_confidence,
                    first_seen_at, last_seen_at, sightings_count
                ) VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    detection.plate_text,
                    country.code,
                    country.name,
                    country.confidence,
                    now,
                    now,
                ),
            )
            vehicle_id = int(cursor.lastrowid)
            already_seen = False
            sightings_count = 1
        else:
            vehicle_id = int(existing["id"])
            sightings_count = int(existing["sightings_count"]) + 1
            self.connection.execute(
                """
                UPDATE vehicles
                SET country_code = ?, country_name = ?, country_confidence = ?,
                    last_seen_at = ?, sightings_count = ?
                WHERE id = ?
                """,
                (
                    country.code,
                    country.name,
                    country.confidence,
                    now,
                    sightings_count,
                    vehicle_id,
                ),
            )
            already_seen = True

        self.connection.execute(
            """
            INSERT INTO sightings (
                vehicle_id, seen_at, confidence, country_reason, image_path,
                bbox_x, bbox_y, bbox_width, bbox_height
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vehicle_id,
                now,
                detection.confidence,
                country.reason,
                image_path,
                detection.x,
                detection.y,
                detection.width,
                detection.height,
            ),
        )
        self.connection.commit()
        return SeenPlateResult(vehicle_id, detection.plate_text, already_seen, sightings_count)

    def close(self) -> None:
        self.connection.close()
