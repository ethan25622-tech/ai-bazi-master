"""Dry-run the monthly-cycle v1 window engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from bazi_master.master_engine import MasterEngine


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    analysis = MasterEngine().analyze(
        1990,
        1,
        1,
        12,
        0,
        longitude=120.0,
        gender="男",
        target_year=2028,
    )
    monthly = analysis["assessments"]["luck_cycle"].get("monthly_windows", {})
    windows = monthly.get("windows", [])
    failures: list[str] = []
    if not windows:
        failures.append("expected at least one monthly window")
    for window in windows:
        if window.get("level") != "month_window":
            failures.append(f"{window.get('ganzhi')} level must be month_window")
        if "不单独构成大事判断" not in window.get("output_policy_note", ""):
            failures.append(f"{window.get('ganzhi')} missing output policy guard")
        seen_trigger_keys: set[tuple[str, str, str]] = set()
        for trigger in window.get("triggered_rules", []):
            for field in ("rule_id", "trigger_score", "uncertainty", "output_policy"):
                if field not in trigger:
                    failures.append(f"{window.get('ganzhi')} trigger missing {field}")
            matched = trigger.get("matched", {}) if isinstance(trigger.get("matched"), dict) else {}
            trigger_key = (
                str(trigger.get("rule_id", "")),
                str(matched.get("pillar", "")),
                str(matched.get("branch", "")),
            )
            if trigger_key in seen_trigger_keys and all(trigger_key):
                failures.append(f"{window.get('ganzhi')} has duplicate trigger {trigger_key}")
            seen_trigger_keys.add(trigger_key)

    repeat_windows = [
        window for window in windows
        for trigger in window.get("triggered_rules", [])
        if trigger.get("repeat_context", {}).get("same_palace_repeat") is True
    ]
    if not repeat_windows:
        failures.append("expected at least one monthly same-palace repeat context")
    for window in repeat_windows:
        for trigger in window.get("triggered_rules", []):
            repeat_context = trigger.get("repeat_context", {})
            if repeat_context.get("same_palace_repeat") is not True:
                continue
            if repeat_context.get("repeat_pillar") != "日柱":
                failures.append(f"{window.get('ganzhi')} repeat_pillar should be 日柱")
            if not {"luck_004", "year_001"}.issubset(set(repeat_context.get("repeat_rule_ids", []))):
                failures.append(f"{window.get('ganzhi')} repeat_rule_ids should include luck_004 and year_001")
            if "吉凶" not in repeat_context.get("note", ""):
                failures.append(f"{window.get('ganzhi')} repeat note should preserve non-good/bad boundary")

    print(json.dumps({
        "target_year": monthly.get("target_year"),
        "window_count": len(windows),
        "top_windows": [
            {
                "ganzhi": window.get("ganzhi"),
                "rules": [trigger.get("rule_id") for trigger in window.get("triggered_rules", [])[:3]],
            }
            for window in windows[:5]
        ],
        "failures": failures,
    }, ensure_ascii=False, indent=2))
    Path("month_cycle_dry_run_report.json").write_text(
        json.dumps(monthly, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
