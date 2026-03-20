from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PlateDetection:
    plate_text: str
    confidence: float
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    raw_country_hint: str | None = None
    raw_region_hint: str | None = None
    candidates: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CountryGuess:
    code: str
    name: str
    confidence: float
    reason: str
