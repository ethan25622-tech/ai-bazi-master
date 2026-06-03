"""Schema helpers for the stable AI master output."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SUPPORTED_SCHEMA_VERSION = "ai-bazi-master.v1"


def confidence_from_assessment(value: Any, default: float = 0.6) -> float:
    """Extract a conservative confidence value from nested assessment data."""

    if isinstance(value, dict):
        raw = value.get("置信度", value.get("confidence"))
        if isinstance(raw, (int, float)):
            return float(raw)
    return default


def evidence_item(
    *,
    key: str,
    source: str,
    rule: str,
    confidence: float,
    matched: Any = None,
    uncertainty: str = "",
) -> dict[str, Any]:
    """Build one normalized evidence record."""

    return {
        "key": key,
        "source": source,
        "rule": rule,
        "matched": deepcopy(matched),
        "confidence": round(float(confidence), 2),
        "uncertainty": uncertainty,
    }


def get_path(data: dict[str, Any], *path: str, default: Any = None) -> Any:
    """Safely fetch a nested field from dictionaries."""

    current: Any = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current
