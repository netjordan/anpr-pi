from __future__ import annotations

import re
from dataclasses import dataclass

from anpr_pi.models import CountryGuess, PlateDetection


COUNTRY_NAMES: dict[str, str] = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DK": "Denmark",
    "EE": "Estonia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "GR": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LV": "Latvia",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ES": "Spain",
    "SE": "Sweden",
    "UK": "United Kingdom",
    "UNKNOWN": "Unknown",
}

OPENALPR_COUNTRY_MAP = {
    "gb": "UK",
    "uk": "UK",
    "eu": "UNKNOWN",
    "fr": "FR",
    "de": "DE",
    "it": "IT",
    "es": "ES",
    "nl": "NL",
}


@dataclass(frozen=True, slots=True)
class PlatePattern:
    code: str
    regex: re.Pattern[str]
    score: float
    reason: str


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern)


PATTERNS: list[PlatePattern] = [
    PlatePattern("UK", _compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{3}$"), 0.97, "UK current format"),
    PlatePattern("UK", _compile(r"^[A-Z][0-9]{1,3}[A-Z]{3}$"), 0.94, "UK prefix format"),
    PlatePattern("UK", _compile(r"^[A-Z]{3}[0-9]{1,3}[A-Z]$"), 0.94, "UK suffix format"),
    PlatePattern("IE", _compile(r"^[0-9]{2}[A-Z]{1,2}[0-9]{1,6}$"), 0.98, "Ireland year-county-serial format"),
    PlatePattern("ES", _compile(r"^[0-9]{4}[A-Z]{3}$"), 0.97, "Spain modern format"),
    PlatePattern("FR", _compile(r"^[A-Z]{2}[0-9]{3}[A-Z]{2}$"), 0.74, "France modern format"),
    PlatePattern("IT", _compile(r"^[A-Z]{2}[0-9]{3}[A-Z]{2}$"), 0.72, "Italy modern format"),
    PlatePattern("PT", _compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{2}$"), 0.91, "Portugal modern format"),
    PlatePattern("PT", _compile(r"^[0-9]{2}[A-Z]{2}[0-9]{2}$"), 0.89, "Portugal historical format"),
    PlatePattern("PT", _compile(r"^[0-9]{2}[0-9]{2}[A-Z]{2}$"), 0.87, "Portugal historical format"),
    PlatePattern("BE", _compile(r"^[0-9][A-Z]{3}[0-9]{3}$"), 0.95, "Belgium standard format"),
    PlatePattern("BE", _compile(r"^[A-Z][0-9]{3}[A-Z]{3}$"), 0.92, "Belgium vanity/newer style"),
    PlatePattern("NL", _compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{2}$"), 0.75, "Netherlands sidecode family"),
    PlatePattern("NL", _compile(r"^[0-9]{2}[A-Z]{2}[A-Z]{2}$"), 0.74, "Netherlands sidecode family"),
    PlatePattern("NL", _compile(r"^[A-Z]{2}[A-Z]{2}[0-9]{2}$"), 0.74, "Netherlands sidecode family"),
    PlatePattern("LU", _compile(r"^[A-Z]{2}[0-9]{4}$"), 0.80, "Luxembourg standard format"),
    PlatePattern("DK", _compile(r"^[A-Z]{2}[0-9]{5}$"), 0.93, "Denmark standard format"),
    PlatePattern("SE", _compile(r"^[A-Z]{3}[0-9]{2}[A-Z0-9]$"), 0.95, "Sweden standard format"),
    PlatePattern("FI", _compile(r"^[A-Z]{3}[0-9]{3}$"), 0.88, "Finland standard format"),
    PlatePattern("EE", _compile(r"^[0-9]{3}[A-Z]{3}$"), 0.90, "Estonia standard format"),
    PlatePattern("LV", _compile(r"^[A-Z]{2}[0-9]{4}$"), 0.86, "Latvia standard format"),
    PlatePattern("LT", _compile(r"^[A-Z]{3}[0-9]{3}$"), 0.83, "Lithuania standard format"),
    PlatePattern("PL", _compile(r"^[A-Z]{2,3}[A-Z0-9]{4,5}$"), 0.68, "Poland regional format"),
    PlatePattern("CZ", _compile(r"^[0-9][A-Z][0-9]{4}$"), 0.88, "Czechia standard format"),
    PlatePattern("SK", _compile(r"^[A-Z]{2}[0-9]{3}[A-Z]{2}$"), 0.82, "Slovakia standard format"),
    PlatePattern("SI", _compile(r"^[A-Z]{2}[A-Z0-9]{5,6}$"), 0.70, "Slovenia regional format"),
    PlatePattern("HR", _compile(r"^[A-Z]{2}[0-9]{3,4}[A-Z]{1,2}$"), 0.85, "Croatia regional format"),
    PlatePattern("RO", _compile(r"^[A-Z]{1,2}[0-9]{2,3}[A-Z]{3}$"), 0.90, "Romania county format"),
    PlatePattern("HU", _compile(r"^[A-Z]{3}[0-9]{3}$"), 0.75, "Hungary legacy format"),
    PlatePattern("HU", _compile(r"^[A-Z]{4}[0-9]{3}$"), 0.80, "Hungary current format"),
    PlatePattern("AT", _compile(r"^[A-Z]{1,3}[0-9]{1,6}[A-Z]{0,2}$"), 0.55, "Austria district format"),
    PlatePattern("DE", _compile(r"^[A-Z]{1,3}[A-Z]{1,2}[0-9]{1,4}$"), 0.55, "Germany district format"),
    PlatePattern("BG", _compile(r"^[A-Z]{1,2}[0-9]{4}[A-Z]{2}$"), 0.72, "Bulgaria standard format"),
    PlatePattern("GR", _compile(r"^[A-Z]{3}[0-9]{4}$"), 0.70, "Greece standard format"),
    PlatePattern("CY", _compile(r"^[A-Z]{3}[0-9]{3}$"), 0.72, "Cyprus standard format"),
    PlatePattern("MT", _compile(r"^[A-Z]{3}[0-9]{3}$"), 0.68, "Malta standard format"),
]


def normalize_plate(plate_text: str) -> str:
    text = plate_text.upper().strip()
    return re.sub(r"[^A-Z0-9]", "", text)


def guess_country(detection: PlateDetection) -> CountryGuess:
    normalized = normalize_plate(detection.plate_text)
    if not normalized:
        return CountryGuess("UNKNOWN", COUNTRY_NAMES["UNKNOWN"], 0.0, "empty plate text")

    engine_hint = _guess_from_engine_hint(detection)
    pattern_guess = _guess_from_pattern(normalized)

    if engine_hint and engine_hint.code != "UNKNOWN":
        if pattern_guess and pattern_guess.code == engine_hint.code:
            confidence = min(0.99, max(engine_hint.confidence, pattern_guess.confidence) + 0.03)
            return CountryGuess(engine_hint.code, COUNTRY_NAMES[engine_hint.code], confidence, "engine hint and pattern agree")
        return engine_hint

    if pattern_guess:
        return pattern_guess

    return CountryGuess("UNKNOWN", COUNTRY_NAMES["UNKNOWN"], 0.1, "no matching country heuristic")


def _guess_from_engine_hint(detection: PlateDetection) -> CountryGuess | None:
    raw = (detection.raw_country_hint or "").strip().lower()
    mapped = OPENALPR_COUNTRY_MAP.get(raw)
    if mapped is None:
        return None
    if mapped == "UNKNOWN":
        return CountryGuess(mapped, COUNTRY_NAMES[mapped], 0.25, f"weak engine country hint '{raw}'")
    return CountryGuess(mapped, COUNTRY_NAMES[mapped], 0.85, f"engine country hint '{raw}'")


def _guess_from_pattern(normalized_plate: str) -> CountryGuess | None:
    matches = [pattern for pattern in PATTERNS if pattern.regex.fullmatch(normalized_plate)]
    if not matches:
        return None
    best = max(matches, key=lambda item: item.score)
    return CountryGuess(best.code, COUNTRY_NAMES[best.code], best.score, best.reason)
