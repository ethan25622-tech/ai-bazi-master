"""Validate structured luck-cycle guard fields."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from bazi_master.luck_guard import guard_daily_candidates
from bazi_master.master_engine import MasterEngine


FORBIDDEN_SAFE_WORDING_TERMS = (
    "一定离婚",
    "一定重病",
    "一定破产",
    "一定死亡",
    "必有灾",
    "必然出事",
    "某日一定发生",
)

GUARD_MATRIX_CASES = [
    {
        "name": "year_001_real_rule_cases_0_1992",
        "rule_id": "year_001",
        "source_type": "real",
        "source_file": "rule_cases.json",
        "source_index": 0,
        "target_year": 1992,
    },
    {
        "name": "year_002_real_rule_cases_0_1990",
        "rule_id": "year_002",
        "source_type": "real",
        "source_file": "rule_cases.json",
        "source_index": 0,
        "target_year": 1990,
    },
    {
        "name": "year_005_real_rule_cases_0_1992",
        "rule_id": "year_005",
        "source_type": "real",
        "source_file": "rule_cases.json",
        "source_index": 0,
        "target_year": 1992,
    },
    {
        "name": "luck_003_real_rule_cases_0_2048",
        "rule_id": "luck_003",
        "source_type": "real",
        "source_file": "rule_cases.json",
        "source_index": 0,
        "target_year": 2048,
    },
    {
        "name": "luck_004_real_dry_run_rule_cases_0_2028",
        "rule_id": "luck_004",
        "source_type": "real",
        "source_file": "rule_cases.json",
        "source_index": 0,
        "target_year": 2028,
        "also_seen_in": "luck_cycle_dry_run_report.json",
    },
    {
        "name": "luck_005_real_rule_cases_5_2030",
        "rule_id": "luck_005",
        "source_type": "real",
        "source_file": "rule_cases.json",
        "source_index": 5,
        "target_year": 2030,
    },
    {
        "name": "year_003_real_rule_cases_0_2050",
        "rule_id": "year_003",
        "source_type": "real",
        "source_file": "rule_cases.json",
        "source_index": 0,
        "target_year": 2050,
    },
    {
        "name": "year_004_real_rule_cases_0_2046",
        "rule_id": "year_004",
        "source_type": "real",
        "source_file": "rule_cases.json",
        "source_index": 0,
        "target_year": 2046,
    },
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    failures: list[str] = []
    matrix_rows: list[dict] = []
    engine = MasterEngine()

    for case in GUARD_MATRIX_CASES:
        triggers = _load_real_case_triggers(engine, case, failures)
        row = _expect_guard_matrix_case(triggers, case, failures)
        matrix_rows.append(row)

    sample = MasterEngine().analyze(
        1990,
        1,
        1,
        12,
        0,
        longitude=120.0,
        gender="男",
        target_year=2028,
    )
    luck_cycle = sample["assessments"]["luck_cycle"]
    annual = luck_cycle.get("annual", {})
    monthly = luck_cycle.get("monthly_windows", {})
    annual_triggers = annual.get("triggers", [])
    monthly_windows = monthly.get("windows", [])

    dayun_fanyin_sample = engine.analyze(
        1960,
        3,
        10,
        12,
        0,
        longitude=120.0,
        gender="\u7537",
        target_year=2028,
    )
    dayun_fanyin_triggers = dayun_fanyin_sample["assessments"]["luck_cycle"].get("annual", {}).get("triggers", [])
    _expect_guarded_rule(
        dayun_fanyin_triggers,
        "luck_006",
        "luck_006_dayun_tianke_dichong",
        failures,
        expected_level="high",
    )
    low_weight_dayun_triggers: dict[str, list[dict]] = {}
    low_weight_dayun_cases = {
        "luck_007": (1940, 2, 5, 12, 2020),
        "luck_008": (1940, 4, 5, 12, 2020),
    }
    for rule_id, params in low_weight_dayun_cases.items():
        year, month, day, hour, target_year = params
        sample = engine.analyze(
            year,
            month,
            day,
            hour,
            0,
            longitude=120.0,
            gender="\u7537",
            target_year=target_year,
        )
        triggers_for_rule = sample["assessments"]["luck_cycle"].get("annual", {}).get("triggers", [])
        low_weight_dayun_triggers[rule_id] = triggers_for_rule
        _expect_guarded_rule(
            triggers_for_rule,
            rule_id,
            f"{rule_id}_low_weight_dayun_branch_clash",
            failures,
            expected_level="medium",
        )
    annual_combination_sample = engine.analyze(
        1940,
        1,
        5,
        0,
        0,
        longitude=120.0,
        gender="\u7537",
        target_year=1995,
    )
    annual_combination_triggers = annual_combination_sample["assessments"]["luck_cycle"].get("annual", {}).get("triggers", [])
    _expect_guarded_rule(
        annual_combination_triggers,
        "year_007",
        "year_007_annual_combination_completion",
        failures,
        expected_level="medium",
    )
    annual_branch_fuyin_sample = engine.analyze(
        1990,
        1,
        1,
        12,
        0,
        longitude=120.0,
        gender="\u7537",
        target_year=2026,
    )
    annual_branch_fuyin_triggers = annual_branch_fuyin_sample["assessments"]["luck_cycle"].get("annual", {}).get("triggers", [])
    _expect_guarded_rule(
        annual_branch_fuyin_triggers,
        "year_008",
        "year_008_annual_branch_fuyin_downgrade",
        failures,
        expected_level="medium",
    )

    downgraded_monthly = [
        trigger
        for window in monthly_windows
        for trigger in window.get("triggered_rules", [])
        if isinstance(trigger.get("matched"), dict) and trigger["matched"].get("downgrade")
    ]
    if not downgraded_monthly:
        failures.append("monthly_single_layer_downgraded: expected at least one downgraded monthly trigger")
    for trigger in downgraded_monthly:
        if trigger.get("risk_guard_required") is not True:
            failures.append("monthly_single_layer_downgraded: downgraded trigger is not guarded")
        if trigger.get("direct_expression_allowed") is not False:
            failures.append("monthly_single_layer_downgraded: direct expression must be blocked")
        if "观察月份" not in trigger.get("safe_wording", ""):
            failures.append("monthly_single_layer_downgraded: safe wording should mark observation month")

    for window in monthly_windows:
        for trigger in window.get("triggered_rules", []):
            if trigger.get("direct_expression_allowed") is not False:
                failures.append("monthly_window_never_direct_event: monthly direct expression was allowed")
            if trigger.get("output_allowed") is not True:
                failures.append("monthly_window_never_direct_event: monthly output should remain allowed")

    blocked_daily = guard_daily_candidates([], annual={}, monthly={})
    if not blocked_daily:
        failures.append("daily_empty_guard: expected blocked daily guard record")
    else:
        item = blocked_daily[0]
        if item.get("output_allowed") is not False:
            failures.append("daily_empty_guard: output_allowed must be false without upper trigger")
        if item.get("risk_level") != "blocked":
            failures.append("daily_empty_guard: risk_level must be blocked")
        if "流日只能作为上层触发后的日期筛选，不能每日泛断" not in item.get("safe_wording", ""):
            failures.append("daily_empty_guard: missing daily anti-generic wording")

    safe_wordings = _collect_safe_wordings(annual_triggers, monthly_windows, blocked_daily)
    for text in safe_wordings:
        for term in FORBIDDEN_SAFE_WORDING_TERMS:
            if term in text:
                failures.append(f"forbidden_terms_scan: safe_wording contains {term}")

    result = {
        "guard_matrix_cases": matrix_rows,
        "guard_matrix_summary": {
            "total": len(matrix_rows),
            "real": sum(1 for row in matrix_rows if row.get("source_type") == "real"),
            "synthetic": sum(1 for row in matrix_rows if row.get("source_type") == "synthetic"),
            "passed": sum(1 for row in matrix_rows if row.get("passed")),
        },
        "annual_guard_summary": annual.get("guard_summary"),
        "dayun_fanyin_rule_ids": [trigger.get("rule_id") for trigger in dayun_fanyin_triggers],
        "low_weight_dayun_rule_ids": {
            rule_id: [trigger.get("rule_id") for trigger in triggers]
            for rule_id, triggers in low_weight_dayun_triggers.items()
        },
        "annual_combination_rule_ids": [trigger.get("rule_id") for trigger in annual_combination_triggers],
        "annual_branch_fuyin_rule_ids": [trigger.get("rule_id") for trigger in annual_branch_fuyin_triggers],
        "monthly_guard_summary": monthly.get("guard_summary"),
        "daily_empty_guard": blocked_daily[:1],
        "monthly_window_count": len(monthly_windows),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    Path("luck_guard_validation_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0 if not failures else 1


def _load_real_case_triggers(engine: MasterEngine, case: dict, failures: list[str]) -> list[dict]:
    source_file = Path(case["source_file"])
    try:
        cases = json.loads(source_file.read_text(encoding="utf-8"))
        source_case = cases[case["source_index"]]
        params = source_case.get("input", source_case)
        analysis = engine.analyze(
            int(params["year"]),
            int(params["month"]),
            int(params["day"]),
            int(params.get("hour", 0)),
            int(params.get("minute", 0)),
            longitude=float(params.get("longitude", 120.0)),
            gender=params.get("gender", "男" if int(params.get("sex", 1)) == 1 else "女"),
            target_year=int(case["target_year"]),
        )
    except Exception as exc:  # pragma: no cover - reported through validation output
        failures.append(f"{case['name']}: failed to load/analyze real source: {exc}")
        return []
    return analysis["assessments"]["luck_cycle"].get("annual", {}).get("triggers", [])


def _expect_guard_matrix_case(triggers: list[dict], case: dict, failures: list[str]) -> dict:
    case_failures: list[str] = []
    _expect_guarded_rule(
        triggers,
        case["rule_id"],
        case["name"],
        case_failures,
        expected_level="high",
    )
    failures.extend(case_failures)
    trigger = next((item for item in triggers if item.get("rule_id") == case["rule_id"]), {})
    return {
        "name": case["name"],
        "rule_id": case["rule_id"],
        "source_type": case["source_type"],
        "source_file": case["source_file"],
        "source_index": case["source_index"],
        "target_year": case["target_year"],
        "also_seen_in": case.get("also_seen_in"),
        "passed": not case_failures,
        "failures": case_failures,
        "matched_trigger": {
            "rule_id": trigger.get("rule_id"),
            "risk_guard_required": trigger.get("risk_guard_required"),
            "risk_level": trigger.get("risk_level"),
            "safe_wording": trigger.get("safe_wording"),
            "forbidden_assertions_count": len(trigger.get("forbidden_assertions", [])),
            "output_allowed": trigger.get("output_allowed"),
            "direct_expression_allowed": trigger.get("direct_expression_allowed"),
        },
    }


def _expect_guarded_rule(
    triggers: list[dict],
    rule_id: str,
    case_name: str,
    failures: list[str],
    *,
    expected_level: str,
) -> None:
    matched = [trigger for trigger in triggers if trigger.get("rule_id") == rule_id]
    if not matched:
        failures.append(f"{case_name}: missing {rule_id}")
        return
    trigger = matched[0]
    if trigger.get("risk_guard_required") is not True:
        failures.append(f"{case_name}: risk_guard_required must be true")
    if trigger.get("risk_level") != expected_level:
        failures.append(f"{case_name}: risk_level expected {expected_level}, got {trigger.get('risk_level')}")
    if trigger.get("output_allowed") is not True:
        failures.append(f"{case_name}: output_allowed must remain true")
    if trigger.get("direct_expression_allowed") is not False:
        failures.append(f"{case_name}: direct_expression_allowed must be false")
    if not trigger.get("safe_wording"):
        failures.append(f"{case_name}: missing safe_wording")
    if not trigger.get("forbidden_assertions"):
        failures.append(f"{case_name}: missing forbidden_assertions")


def _collect_safe_wordings(
    annual_triggers: list[dict],
    monthly_windows: list[dict],
    daily_candidates: list[dict],
) -> list[str]:
    texts = [str(trigger.get("safe_wording", "")) for trigger in annual_triggers]
    for window in monthly_windows:
        texts.extend(str(trigger.get("safe_wording", "")) for trigger in window.get("triggered_rules", []))
    texts.extend(str(item.get("safe_wording", "")) for item in daily_candidates)
    return [text for text in texts if text]


if __name__ == "__main__":
    raise SystemExit(main())
