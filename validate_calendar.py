"""Validate candidate calendar boundary cases without mixing in interpretation tests."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from bazi_master.knowledge_base import load_calendar_cases
from bazi_master.master_engine import MasterEngine


KNOWN_PRECISION_GAPS: set[str] = set()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate candidate calendar cases.")
    parser.add_argument("--strict", action="store_true", help="Fail known solar-term precision gaps too.")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    dataset = load_calendar_cases()
    engine = MasterEngine()
    rows: list[dict[str, Any]] = []

    for case in dataset.get("calendar_cases_zi_23", []):
        input_data = case["input"]
        expected = case["expected"]
        analysis = engine.analyze(
            input_data["year"],
            input_data["month"],
            input_data["day"],
            input_data["hour"],
            input_data.get("minute", 0),
            longitude=float(input_data.get("longitude", 120)),
            gender=input_data.get("gender"),
        )
        actual = _pillars(analysis)
        failures = [
            f"{key}: expected {value!r}, got {actual.get(key)!r}"
            for key, value in expected.items()
            if key.endswith("_pillar") and actual.get(key) != value
        ]
        status = "PASS"
        if failures and case["case_id"] in KNOWN_PRECISION_GAPS:
            status = "KNOWN_GAP"
        elif failures:
            status = "FAIL"
        rows.append({"case_id": case["case_id"], "status": status, "failures": failures})
        print(f"{status} {case['case_id']}")
        for failure in failures:
            print(f"  - {failure}")

    if args.json_out:
        from pathlib import Path

        Path(args.json_out).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    hard_failures = [row for row in rows if row["status"] == "FAIL" or (args.strict and row["status"] == "KNOWN_GAP")]
    return 0 if not hard_failures else 1


def _pillars(analysis: dict[str, Any]) -> dict[str, str]:
    pillars = analysis.get("chart", {}).get("pillars", {})
    return {
        "year_pillar": pillars.get("年柱"),
        "month_pillar": pillars.get("月柱"),
        "day_pillar": pillars.get("日柱"),
        "hour_pillar": pillars.get("时柱"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
