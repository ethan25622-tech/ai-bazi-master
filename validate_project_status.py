"""Validate the project-level acceptance contract.

This is a lightweight final gate.  It does not replace the domain validators;
it checks that the command center still exposes the expected validation
surface, rule/phrase assets, and guarded daily-filter integration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from bazi_master.knowledge_base import load_luck_rules, load_phrase_library
from bazi_master.master_engine import MasterEngine


ROOT = Path(__file__).resolve().parent

REQUIRED_COMMANDS = [
    "run_rule_validation.cmd",
    "run_calendar_validation.cmd",
    "run_luck_validation.cmd",
    "run_month_validation.cmd",
    "run_luck_guard_validation.cmd",
    "run_daily_filter_validation.cmd",
    "run_phrase_validation.cmd",
    "run_dialogue_guard_validation.cmd",
    "run_report_validation.cmd",
    "run_interactive_validation.cmd",
    "run_llm_context_validation.cmd",
    "run_case_library_validation.cmd",
    "run_case_library_negative_validation.cmd",
    "run_mingli_validation.cmd",
    "run_project_status_validation.cmd",
]

REQUIRED_FILES = [
    "bazi_master/calendar_terms.py",
    "bazi_master/luck_cycle_engine.py",
    "bazi_master/luck_guard.py",
    "bazi_master/daily_filter_engine.py",
    "bazi_master/phrase_engine.py",
    "bazi_master/dialogue_engine.py",
    "bazi_master/report_engine.py",
    "bazi_master/llm_context_builder.py",
    "bazi_master/clipboard.py",
    "bazi_master/feedback_store.py",
    "rules/core_rules.json",
    "rules/core_rules_b_expansion.json",
    "rules/luck_cycle_rules.json",
    "rules/monthly_cycle_rules.json",
    "phrases/phrase_library.json",
    "case_library/README.md",
    "case_library/gold_cases.json",
    "case_library/reference_cases.json",
    "case_library/youtube_candidate_sources.json",
    "case_library/excluded_cases.json",
    "PROJECT_HANDOFF.md",
    "run_report.cmd",
    "run_llm_prompt.cmd",
    "run_llm_prompt_copy.cmd",
    "1.cmd",
    "2.cmd",
    "启动.cmd",
    "双击启动.bat",
    "ask_bazi.cmd",
    "validate_llm_context.py",
    "interactive_report.py",
    "validation_summary.md",
]

REQUIRED_LUCK_RULES = {
    "luck_003",
    "luck_004",
    "luck_005",
    "luck_006",
    "luck_007",
    "luck_008",
    "year_001",
    "year_002",
    "year_003",
    "year_004",
    "year_005",
    "year_006",
    "year_007",
    "year_008",
    "luck_guard_001",
    "luck_guard_002",
}

REQUIRED_PHRASES = {
    "luck_annual_change_window",
    "luck_month_window",
    "luck_daily_filter_window",
    "medicine_002_climate",
}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    failures: list[str] = []
    failures.extend(validate_files())
    failures.extend(validate_run_all())
    failures.extend(validate_luck_rules())
    failures.extend(validate_phrases())
    failures.extend(validate_master_daily_filter_contract())
    failures.extend(validate_case_library_policy())

    result = {
        "passed": not failures,
        "required_commands": REQUIRED_COMMANDS,
        "required_luck_rules": sorted(REQUIRED_LUCK_RULES),
        "required_phrases": sorted(REQUIRED_PHRASES),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    Path("project_status_validation_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0 if not failures else 1


def validate_files() -> list[str]:
    failures = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            failures.append(f"missing required file: {relative}")
    return failures


def validate_run_all() -> list[str]:
    path = ROOT / "run_all_validation.cmd"
    if not path.exists():
        return ["missing run_all_validation.cmd"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    failures = []
    for command in REQUIRED_COMMANDS:
        if command not in text:
            failures.append(f"run_all_validation.cmd does not call {command}")
    return failures


def validate_luck_rules() -> list[str]:
    rule_set = load_luck_rules()
    rule_ids = {str(rule.get("rule_id")) for rule in rule_set.get("rules", [])}
    return [f"luck rule missing from loaded rule set: {rule_id}" for rule_id in sorted(REQUIRED_LUCK_RULES - rule_ids)]


def validate_phrases() -> list[str]:
    phrase_set = load_phrase_library()
    phrase_ids = {str(phrase.get("phrase_id")) for phrase in phrase_set.get("phrases", [])}
    failures = [f"phrase missing from loaded library: {phrase_id}" for phrase_id in sorted(REQUIRED_PHRASES - phrase_ids)]
    daily_phrase = next(
        (phrase for phrase in phrase_set.get("phrases", []) if phrase.get("phrase_id") == "luck_daily_filter_window"),
        None,
    )
    if isinstance(daily_phrase, dict):
        bindings = set(daily_phrase.get("rule_bindings", []))
        for rule_id in {
            "daily_filter_chong_activated_branch_v1",
            "daily_filter_repeat_month_palace_trigger_v1",
            "daily_filter_complete_existing_combination_v1",
            "luck_guard_001",
        }:
            if rule_id not in bindings:
                failures.append(f"daily filter phrase missing rule binding {rule_id}")
    return failures


def validate_master_daily_filter_contract() -> list[str]:
    failures = []
    engine = MasterEngine()
    base = engine.analyze(1990, 1, 1, 12, 0, longitude=120.0, gender="男", target_year=2028)
    luck_cycle = base.get("assessments", {}).get("luck_cycle", {})
    if "daily_filter" in luck_cycle:
        failures.append("daily_filter should not appear unless target_month is explicit")

    with_month = engine.analyze(
        1990,
        1,
        1,
        12,
        0,
        longitude=120.0,
        gender="男",
        target_year=2028,
        target_month=7,
    )
    daily = with_month.get("assessments", {}).get("luck_cycle", {}).get("daily_filter")
    if not isinstance(daily, dict):
        failures.append("daily_filter should appear when target_year and target_month are explicit")
        return failures
    if daily.get("target_month") != 7:
        failures.append("daily_filter should echo target_month")
    if daily.get("guard_summary", {}).get("direct_expression_allowed") is not False:
        failures.append("daily_filter guard summary should block direct expression")
    for candidate in daily.get("date_candidates", []):
        if candidate.get("direct_expression_allowed") is not False:
            failures.append("daily_filter candidate should block direct expression")
    return failures


def validate_case_library_policy() -> list[str]:
    failures = []
    gold = read_json(ROOT / "case_library/gold_cases.json")
    reference = read_json(ROOT / "case_library/reference_cases.json")
    if not isinstance(gold, dict):
        failures.append("gold_cases.json must be an object")
    elif gold.get("cases") not in ([], None):
        failures.append("gold_cases.json should remain empty until gold policy is met")
    if not isinstance(reference, dict):
        failures.append("reference_cases.json must be an object")
    else:
        for index, case in enumerate(reference.get("cases", []), start=1):
            if case.get("auto_regression") is not False:
                failures.append(f"reference_cases[{index}] must not be automatic regression")
    return failures


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
