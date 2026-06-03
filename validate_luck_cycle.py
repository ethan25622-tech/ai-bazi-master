"""Dry-run the luck-cycle v1 engine against a fixed chart."""

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
    annual = analysis["assessments"]["luck_cycle"].get("annual", {})
    triggers = annual.get("triggers", [])
    failures: list[str] = []
    if annual.get("target_year") != 2028:
        failures.append("target_year missing from annual luck-cycle output")
    if not triggers:
        failures.append("expected at least one annual trigger for dry-run chart")
    for trigger in triggers:
        for field in ("rule_id", "status", "triggered", "trigger_score", "uncertainty"):
            if field not in trigger:
                failures.append(f"{trigger.get('rule_id', '<unknown>')} missing {field}")
    repeat_triggers = {
        trigger.get("rule_id"): trigger
        for trigger in triggers
        if trigger.get("repeat_context", {}).get("same_palace_repeat") is True
    }
    for rule_id in ("luck_004", "year_001"):
        trigger = repeat_triggers.get(rule_id)
        if not trigger:
            failures.append(f"{rule_id} should carry same-palace repeat context")
            continue
        repeat_context = trigger.get("repeat_context", {})
        if repeat_context.get("repeat_pillar") != "日柱":
            failures.append(f"{rule_id} repeat_pillar should be 日柱")
        if repeat_context.get("score_bonus") != 10:
            failures.append(f"{rule_id} score_bonus should follow same_palace_repeat_bonus=10")
        if "吉凶" not in repeat_context.get("note", ""):
            failures.append(f"{rule_id} repeat note should preserve non-good/bad boundary")

    dayun_fanyin = MasterEngine().analyze(
        1960,
        3,
        10,
        12,
        0,
        longitude=120.0,
        gender="\u7537",
        target_year=2028,
    )["assessments"]["luck_cycle"].get("annual", {})
    dayun_fanyin_trigger = next(
        (trigger for trigger in dayun_fanyin.get("triggers", []) if trigger.get("rule_id") == "luck_006"),
        None,
    )
    if not dayun_fanyin_trigger:
        failures.append("luck_006 should trigger for dayun tianke-dichong sample")
    else:
        if dayun_fanyin_trigger.get("risk_guard_required") is not True:
            failures.append("luck_006 must be guarded")
        if dayun_fanyin_trigger.get("risk_level") != "high":
            failures.append("luck_006 risk_level should be high")
        if dayun_fanyin_trigger.get("direct_expression_allowed") is not False:
            failures.append("luck_006 direct expression must be blocked")

    low_weight_dayun_samples = [
        ("luck_007", (1940, 2, 5, 12, 2020), "\u5e74\u67f1"),
        ("luck_008", (1940, 4, 5, 12, 2020), "\u65f6\u67f1"),
    ]
    low_weight_results: dict[str, list[str]] = {}
    for rule_id, params, expected_pillar in low_weight_dayun_samples:
        year, month, day, hour, target_year = params
        sample_annual = MasterEngine().analyze(
            year,
            month,
            day,
            hour,
            0,
            longitude=120.0,
            gender="\u7537",
            target_year=target_year,
        )["assessments"]["luck_cycle"].get("annual", {})
        sample_triggers = sample_annual.get("triggers", [])
        low_weight_results[rule_id] = [trigger.get("rule_id") for trigger in sample_triggers]
        trigger = next((item for item in sample_triggers if item.get("rule_id") == rule_id), None)
        if not trigger:
            failures.append(f"{rule_id} should trigger for low-weight dayun branch clash sample")
            continue
        if trigger.get("matched", {}).get("pillar") != expected_pillar:
            failures.append(f"{rule_id} should match {expected_pillar}")
        if trigger.get("risk_guard_required") is not True:
            failures.append(f"{rule_id} must be guarded")
        if trigger.get("risk_level") != "medium":
            failures.append(f"{rule_id} risk_level should be medium")
        if trigger.get("direct_expression_allowed") is not False:
            failures.append(f"{rule_id} direct expression must be blocked")

    annual_combination = MasterEngine().analyze(
        1940,
        1,
        5,
        0,
        0,
        longitude=120.0,
        gender="\u7537",
        target_year=1995,
    )["assessments"]["luck_cycle"].get("annual", {})
    annual_combination_trigger = next(
        (trigger for trigger in annual_combination.get("triggers", []) if trigger.get("rule_id") == "year_007"),
        None,
    )
    if not annual_combination_trigger:
        failures.append("year_007 should trigger for annual sanhe/sanhui completion sample")
    else:
        if annual_combination_trigger.get("matched", {}).get("combination") not in {"sanhe", "sanhui"}:
            failures.append("year_007 should include combination type")
        if not annual_combination_trigger.get("matched", {}).get("original_pillars"):
            failures.append("year_007 should include original pillar evidence")
        if annual_combination_trigger.get("risk_level") != "medium":
            failures.append("year_007 risk_level should be medium")
        if annual_combination_trigger.get("direct_expression_allowed") is not False:
            failures.append("year_007 direct expression must be blocked")

    annual_branch_fuyin = MasterEngine().analyze(
        1990,
        1,
        1,
        12,
        0,
        longitude=120.0,
        gender="\u7537",
        target_year=2026,
    )["assessments"]["luck_cycle"].get("annual", {})
    annual_branch_fuyin_trigger = next(
        (trigger for trigger in annual_branch_fuyin.get("triggers", []) if trigger.get("rule_id") == "year_008"),
        None,
    )
    if not annual_branch_fuyin_trigger:
        failures.append("year_008 should trigger for annual branch fuyin downgrade sample")
    else:
        matched = annual_branch_fuyin_trigger.get("matched", {})
        if matched.get("match_type") != "branch_fuyin" or matched.get("downgrade") is not True:
            failures.append("year_008 should be marked as downgraded branch_fuyin")
        if annual_branch_fuyin_trigger.get("risk_level") != "medium":
            failures.append("year_008 risk_level should be medium")
        if annual_branch_fuyin_trigger.get("direct_expression_allowed") is not False:
            failures.append("year_008 direct expression must be blocked")

    print(json.dumps({
        "target_year": annual.get("target_year"),
        "year_pillar": annual.get("year_pillar"),
        "trigger_count": len(triggers),
        "top_rule_ids": [trigger.get("rule_id") for trigger in triggers[:5]],
        "same_palace_repeat_rule_ids": sorted(repeat_triggers),
        "dayun_fanyin_rule_ids": [trigger.get("rule_id") for trigger in dayun_fanyin.get("triggers", [])],
        "low_weight_dayun_rule_ids": low_weight_results,
        "annual_combination_rule_ids": [trigger.get("rule_id") for trigger in annual_combination.get("triggers", [])],
        "annual_branch_fuyin_rule_ids": [trigger.get("rule_id") for trigger in annual_branch_fuyin.get("triggers", [])],
        "failures": failures,
    }, ensure_ascii=False, indent=2))
    Path("luck_cycle_dry_run_report.json").write_text(
        json.dumps(annual, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
