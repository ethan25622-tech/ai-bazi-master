"""Solar-term boundary overrides for stable calendar validation.

The legacy engine keeps a low-order Meeus fallback.  This module provides a
small provider hook so validated HKO/NAOJ boundary instants can override the
fallback at second precision without editing the legacy script in ``C:\ai tools``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable


# Local UTC+8 instants.  Keys are (Gregorian year, solar longitude).
# Only the 12 monthly "jie" are needed for Bazi year/month boundaries.
JIEQI_OVERRIDES_UTC8 = {
    (2024, 315): datetime(2024, 2, 4, 16, 27, 8),   # Li Chun
    (2024, 345): datetime(2024, 3, 5, 10, 22, 46),  # Jing Zhe
    (2024, 75): datetime(2024, 6, 5, 12, 9, 54),    # Mang Zhong
    (2024, 255): datetime(2024, 12, 6, 23, 17, 3),  # Da Xue
    (2025, 285): datetime(2025, 1, 5, 10, 32, 46),  # Xiao Han
}


def local_datetime_to_jdn(moment: datetime) -> float:
    """Convert a naive local datetime to the same local JDN scale as the engine."""

    year = moment.year
    month = moment.month
    day = moment.day
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    day_fraction = (
        moment.hour / 24.0
        + moment.minute / 1440.0
        + moment.second / 86400.0
        + moment.microsecond / 86400_000000.0
    )
    return (
        int(365.25 * (year + 4716))
        + int(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
        + day_fraction
    )


def patched_get_jieqi_jdn(original: Callable[[int, int], float]) -> Callable[[int, int], float]:
    """Return a ``_get_jieqi_jdn`` wrapper with validated overrides."""

    def _wrapped(year: int, target_lon: int) -> float:
        override = JIEQI_OVERRIDES_UTC8.get((year, target_lon))
        if override is not None:
            return local_datetime_to_jdn(override)
        return original(year, target_lon)

    return _wrapped


def apply_to_module(engine_module: Any) -> None:
    """Patch a loaded legacy ``bazi_engine`` module once."""

    if getattr(engine_module, "_HKO_JIEQI_PATCHED", False):
        return
    original = engine_module._get_jieqi_jdn
    engine_module._get_jieqi_jdn = patched_get_jieqi_jdn(original)
    engine_module._HKO_JIEQI_PATCHED = True
