"""Append-only local feedback records for reading calibration."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_DIR = PROJECT_ROOT / "feedback"
FEEDBACK_PATH = FEEDBACK_DIR / "reading_feedback.jsonl"


def append_feedback(analysis: dict[str, Any], year: int | None, verdict: str, note: str) -> dict[str, Any]:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "birth": {
            "year": analysis.get("input", {}).get("year"),
            "month": analysis.get("input", {}).get("month"),
            "day": analysis.get("input", {}).get("day"),
            "hour": analysis.get("input", {}).get("hour"),
            "minute": analysis.get("input", {}).get("minute"),
            "gender": analysis.get("input", {}).get("gender"),
        },
        "chart": analysis.get("chart", {}).get("pillars", {}),
        "target_year": year,
        "verdict": verdict,
        "note": note,
    }
    with FEEDBACK_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {
        "path": str(FEEDBACK_PATH),
        "record": record,
    }
