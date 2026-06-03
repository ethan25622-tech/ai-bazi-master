"""Validate daily_filter v1 as a guarded date-candidate framework."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from bazi_master.daily_filter_engine import DailyFilterEngine
from bazi_master.master_engine import MasterEngine


FORBIDDEN_DISPLAY_TERMS = (
    "每日泛断",
    "某日一定发生",
    "一定死亡",
    "一定重病",
    "一定离婚",
    "一定破产",
    "一定事故",
    "投资买入",
    "投资卖出",
    "吉日",
    "凶日",
    "灾日",
)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    failures: list[str] = []
    engine = DailyFilterEngine()
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
    if "daily_filter" in analysis["assessments"]["luck_cycle"]:
        failures.append("master_engine_default: daily_filter must not appear without target_month")

    analysis_with_month = MasterEngine().analyze(
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
    master_daily = analysis_with_month["assessments"]["luck_cycle"].get("daily_filter")
    if not master_daily:
        failures.append("master_engine_target_month: expected daily_filter when target_year and target_month are set")
    elif master_daily.get("target_month") != 7:
        failures.append("master_engine_target_month: daily_filter should echo target_month")

    analysis_without_year = MasterEngine().analyze(
        1990,
        1,
        1,
        12,
        0,
        longitude=120.0,
        gender="男",
        target_month=7,
    )
    if "daily_filter" in analysis_without_year["assessments"]["luck_cycle"]:
        failures.append("master_engine_target_month_without_year: daily_filter requires target_year")

    luck_cycle = analysis["assessments"]["luck_cycle"]
    annual = luck_cycle["annual"]
    monthly = luck_cycle["monthly_windows"]

    invalid_month = engine.evaluate(analysis, 2028, 13, annual=annual, monthly_windows=monthly)["daily_filter"]
    if invalid_month["date_candidates"]:
        failures.append("invalid_target_month: date_candidates must be empty")
    if invalid_month["guard_summary"].get("output_allowed") is not False:
        failures.append("invalid_target_month: output_allowed must be false")
    if invalid_month["guard_summary"].get("invalid_target_month") is not True:
        failures.append("invalid_target_month: guard summary must mark invalid_target_month")
    if invalid_month.get("candidate_date_range", {}).get("valid") is not False:
        failures.append("invalid_target_month: candidate date range must be invalid")

    blocked = engine.evaluate(analysis, 2028, 7, annual={}, monthly_windows={})["daily_filter"]
    if blocked["date_candidates"]:
        failures.append("daily_without_upper_trigger_blocked: date_candidates must be empty")
    if blocked["guard_summary"].get("output_allowed") is not False:
        failures.append("daily_without_upper_trigger_blocked: output_allowed must be false")
    if blocked["guard_summary"].get("risk_guarded_count", 0) < 1:
        failures.append("daily_without_upper_trigger_blocked: blocked guard should be counted")
    if "流日只能作为上层触发后的日期筛选" not in blocked.get("safe_wording", ""):
        failures.append("daily_without_upper_trigger_blocked: missing anti-generic safe wording")

    annual_only = engine.evaluate(analysis, 2028, 2, annual=annual, monthly_windows={"windows": []})["daily_filter"]
    if annual_only["date_candidates"]:
        failures.append("annual_only_downgraded: first phase should not emit annual-only candidates")
    if annual_only["guard_summary"].get("downgrade") is not True:
        failures.append("annual_only_downgraded: expected downgrade guard summary")
    if annual_only["guard_summary"].get("direct_expression_allowed") is not False:
        failures.append("annual_only_downgraded: direct expression must stay blocked")

    monthly_result = engine.evaluate(
        analysis,
        2028,
        7,
        annual=annual,
        monthly_windows=monthly,
        max_candidates=3,
    )["daily_filter"]
    candidates = monthly_result["date_candidates"]
    if not candidates:
        failures.append("monthly_window_outputs_limited_candidates: expected at least one guarded candidate")
    if len(candidates) > 3:
        failures.append("max_candidates_enforced: expected <= 3 candidates")
    if monthly_result.get("max_candidates") != 3:
        failures.append("max_candidates_enforced: result should echo max_candidates")
    if monthly_result.get("candidate_date_range", {}).get("valid") is not True:
        failures.append("solar_term_date_range: expected valid candidate date range")
    if monthly_result.get("candidate_date_range", {}).get("start_date") == "2028-08-03":
        failures.append("solar_term_date_range: should not use Gregorian month start approximation")
    for candidate in candidates:
        if candidate.get("direct_expression_allowed") is not False:
            failures.append("monthly_window_outputs_limited_candidates: direct expression must be blocked")
        if candidate.get("risk_guard_required") is not True:
            failures.append("monthly_window_outputs_limited_candidates: candidate must be guarded")
        if candidate.get("output_allowed") is not True:
            failures.append("monthly_window_outputs_limited_candidates: guarded candidate should remain output allowed")
        matched = candidate.get("matched", {})
        if not matched.get("upper_rule_id") and not matched.get("upper_window_ganzhi"):
            failures.append("daily_candidates_require_upper_evidence: missing upper evidence")

    combination_result = engine.evaluate(
        analysis,
        2028,
        3,
        annual=annual,
        monthly_windows=monthly,
        max_candidates=3,
    )["daily_filter"]
    combination_candidates = [
        candidate for candidate in combination_result["date_candidates"]
        if candidate.get("rule_id") == "daily_filter_complete_existing_combination_v1"
    ]
    if not combination_candidates:
        failures.append("complete_existing_combination: expected guarded daily candidates")
    for candidate in combination_candidates:
        matched = candidate.get("matched", {})
        if matched.get("upper_rule_id") != "liuyue_complete_sanhe_sanhui_from_original_dayun_liunian_v1":
            failures.append("complete_existing_combination: missing upper monthly combination rule")
        if not matched.get("branches"):
            failures.append("complete_existing_combination: missing combination branches evidence")
        if candidate.get("direct_expression_allowed") is not False:
            failures.append("complete_existing_combination: direct expression must be blocked")

    display_text = _collect_candidate_display_text([monthly_result, combination_result])
    for text in display_text:
        for term in FORBIDDEN_DISPLAY_TERMS:
            if term in text:
                failures.append(f"forbidden_terms_scan: display text contains {term}")

    result = {
        "blocked_guard_summary": blocked["guard_summary"],
        "annual_only_guard_summary": annual_only["guard_summary"],
        "invalid_month_guard_summary": invalid_month["guard_summary"],
        "monthly_candidate_count": len(candidates),
        "monthly_candidates": candidates,
        "combination_candidate_count": len(combination_candidates),
        "combination_candidates": combination_candidates,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    Path("daily_filter_validation_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0 if not failures else 1


def _collect_candidate_display_text(results: list[dict]) -> list[str]:
    texts = []
    for result in results:
        for candidate in result.get("date_candidates", []):
            texts.append(str(candidate.get("safe_wording", "")))
            texts.extend(str(item) for item in candidate.get("evidence", []))
            texts.append(str(candidate.get("date_window_type", "")))
    return [text for text in texts if text]


if __name__ == "__main__":
    raise SystemExit(main())
