"""Validate the structured Mingli case library."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mingli-case-library.v1"
THEMES = {
    "overview",
    "pattern",
    "strength",
    "tiaohou",
    "yong_shen",
    "chong_he",
    "liuqin",
    "career",
    "wealth",
    "marriage",
    "health",
    "luck_cycle",
}
PRIVACY_LEVELS = {"synthetic_fixture", "anonymized", "consented_public", "internal_redacted"}
REVIEW_STATUSES = {"seed", "draft", "verified", "needs_review", "retired"}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate Mingli case-library records.")
    parser.add_argument("--cases", default="mingli_cases.json")
    parser.add_argument(
        "--check-chart",
        action="store_true",
        help="Also run MasterEngine and compare expected_chart fields when present.",
    )
    parser.add_argument(
        "--check-rules",
        action="store_true",
        help="Also run MasterEngine and compare judgement_notes against assessments.",
    )
    parser.add_argument("--json-out")
    args = parser.parse_args()

    payload = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    failures = validate_library(payload)

    if args.check_chart:
        failures.extend(validate_engine_expectations(payload, check_chart=True, check_rules=False))
    if args.check_rules:
        failures.extend(validate_engine_expectations(payload, check_chart=False, check_rules=True))

    result = {
        "cases": args.cases,
        "passed": not failures,
        "failures": failures,
        "case_count": len(payload.get("cases", [])) if isinstance(payload, dict) else 0,
    }

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if failures:
        print(f"FAIL {args.cases}")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS {args.cases}: {result['case_count']} case(s)")
    return 0


def validate_library(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["root must be an object"]

    if payload.get("schema_version") != SCHEMA_VERSION:
        failures.append(f"schema_version must be {SCHEMA_VERSION!r}")

    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        failures.append("cases must be a non-empty list")
        return failures

    seen_ids: set[str] = set()
    for index, case in enumerate(cases, start=1):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            failures.append(f"{prefix} must be an object")
            continue
        failures.extend(validate_case(case, prefix, seen_ids))
    return failures


def validate_case(case: dict[str, Any], prefix: str, seen_ids: set[str]) -> list[str]:
    failures: list[str] = []
    case_id = require_text(case, "id", prefix, failures)
    require_text(case, "title", prefix, failures)

    if case_id:
        if case_id in seen_ids:
            failures.append(f"{prefix}.id duplicates {case_id!r}")
        seen_ids.add(case_id)

    privacy = case.get("privacy")
    if privacy not in PRIVACY_LEVELS:
        failures.append(f"{prefix}.privacy must be one of {sorted(PRIVACY_LEVELS)}")

    failures.extend(validate_source(case.get("source"), f"{prefix}.source"))
    failures.extend(validate_birth(case.get("birth"), f"{prefix}.birth"))
    failures.extend(validate_themes(case.get("themes"), f"{prefix}.themes"))
    failures.extend(validate_life_events(case.get("life_events"), f"{prefix}.life_events"))
    failures.extend(validate_questions(case.get("questions"), f"{prefix}.questions"))
    failures.extend(validate_judgement_notes(case.get("judgement_notes"), f"{prefix}.judgement_notes"))
    failures.extend(validate_review(case.get("review"), f"{prefix}.review"))
    return failures


def validate_source(source: Any, prefix: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(source, dict):
        return [f"{prefix} must be an object"]
    require_text(source, "type", prefix, failures)
    require_text(source, "reference", prefix, failures)
    require_text(source, "consent", prefix, failures)
    reliability = source.get("reliability")
    if not isinstance(reliability, (int, float)) or not 0 <= reliability <= 1:
        failures.append(f"{prefix}.reliability must be a number from 0 to 1")
    return failures


def validate_birth(birth: Any, prefix: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(birth, dict):
        return [f"{prefix} must be an object"]
    for key in ("year", "month", "day", "hour", "minute"):
        if not isinstance(birth.get(key), int):
            failures.append(f"{prefix}.{key} must be an integer")
    if isinstance(birth.get("year"), int) and birth["year"] < 1902:
        failures.append(f"{prefix}.year must be 1902 or later")
    if isinstance(birth.get("month"), int) and not 1 <= birth["month"] <= 12:
        failures.append(f"{prefix}.month must be from 1 to 12")
    if isinstance(birth.get("day"), int) and not 1 <= birth["day"] <= 31:
        failures.append(f"{prefix}.day must be from 1 to 31")
    if isinstance(birth.get("hour"), int) and not 0 <= birth["hour"] <= 23:
        failures.append(f"{prefix}.hour must be from 0 to 23")
    if isinstance(birth.get("minute"), int) and not 0 <= birth["minute"] <= 59:
        failures.append(f"{prefix}.minute must be from 0 to 59")
    if not isinstance(birth.get("longitude"), (int, float)):
        failures.append(f"{prefix}.longitude must be a number")
    if birth.get("gender") not in ("男", "女", None):
        failures.append(f"{prefix}.gender must be 男, 女, or null")
    return failures


def validate_themes(themes: Any, prefix: str) -> list[str]:
    if not isinstance(themes, list) or not themes:
        return [f"{prefix} must be a non-empty list"]
    failures = []
    for theme in themes:
        if theme not in THEMES:
            failures.append(f"{prefix} contains unknown theme {theme!r}")
    return failures


def validate_life_events(events: Any, prefix: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(events, list) or not events:
        return [f"{prefix} must be a non-empty list"]
    for index, event in enumerate(events, start=1):
        item = f"{prefix}[{index}]"
        if not isinstance(event, dict):
            failures.append(f"{item} must be an object")
            continue
        require_text(event, "period", item, failures)
        require_text(event, "event", item, failures)
        if event.get("theme") not in THEMES:
            failures.append(f"{item}.theme must be one of {sorted(THEMES)}")
        confidence = event.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            failures.append(f"{item}.confidence must be a number from 0 to 1")
    return failures


def validate_questions(questions: Any, prefix: str) -> list[str]:
    failures: list[str] = []
    if questions is None:
        return failures
    if not isinstance(questions, list):
        return [f"{prefix} must be a list when present"]
    for index, question in enumerate(questions, start=1):
        item = f"{prefix}[{index}]"
        if not isinstance(question, dict):
            failures.append(f"{item} must be an object")
            continue
        if question.get("theme") not in THEMES:
            failures.append(f"{item}.theme must be one of {sorted(THEMES)}")
        require_text(question, "question", item, failures)
        focus = question.get("expected_answer_focus")
        if focus is not None and (not isinstance(focus, list) or not all(isinstance(x, str) and x for x in focus)):
            failures.append(f"{item}.expected_answer_focus must be a list of text values")
    return failures


def validate_judgement_notes(notes: Any, prefix: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(notes, list) or not notes:
        return [f"{prefix} must be a non-empty list"]
    for index, note in enumerate(notes, start=1):
        item = f"{prefix}[{index}]"
        if not isinstance(note, dict):
            failures.append(f"{item} must be an object")
            continue
        if note.get("theme") not in THEMES:
            failures.append(f"{item}.theme must be one of {sorted(THEMES)}")
        require_text(note, "quality_target", item, failures)
        keys = note.get("evidence_keys")
        if not isinstance(keys, list) or not all(isinstance(key, str) and key for key in keys):
            failures.append(f"{item}.evidence_keys must be a non-empty list of text values")
    return failures


def validate_review(review: Any, prefix: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(review, dict):
        return [f"{prefix} must be an object"]
    if review.get("status") not in REVIEW_STATUSES:
        failures.append(f"{prefix}.status must be one of {sorted(REVIEW_STATUSES)}")
    require_text(review, "last_verified", prefix, failures)
    require_text(review, "reviewer", prefix, failures)
    return failures


def validate_engine_expectations(payload: dict[str, Any], *, check_chart: bool, check_rules: bool) -> list[str]:
    from bazi_master.master_engine import MasterEngine

    failures: list[str] = []
    engine = MasterEngine()
    for index, case in enumerate(payload.get("cases", []), start=1):
        if not isinstance(case, dict):
            continue
        birth = case.get("birth", {})
        analysis = engine.analyze(
            birth["year"],
            birth["month"],
            birth["day"],
            birth["hour"],
            birth.get("minute", 0),
            longitude=birth.get("longitude", 120),
            gender=birth.get("gender"),
        )
        label = f"cases[{index}] {case.get('id', '')}"
        if check_chart and isinstance(case.get("expected_chart"), dict):
            for failure in compare_expected_chart(analysis.get("chart", {}), case["expected_chart"]):
                failures.append(f"{label}: {failure}")
        if check_rules:
            for failure in compare_judgement_notes(analysis.get("assessments", {}), case.get("judgement_notes", [])):
                failures.append(f"{label}: {failure}")
    return failures


def compare_expected_chart(actual_chart: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key in ("pillars", "day_master", "month_command"):
        if key in expected and actual_chart.get(key) != expected[key]:
            failures.append(f"expected_chart.{key}: expected {expected[key]!r}, got {actual_chart.get(key)!r}")
    return failures


def compare_judgement_notes(assessments: dict[str, Any], notes: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(notes, list):
        return ["judgement_notes must be a list for rule checks"]
    for index, note in enumerate(notes, start=1):
        if not isinstance(note, dict):
            continue
        theme = note.get("theme")
        assessment = assessments.get(theme)
        if not isinstance(assessment, dict):
            failures.append(f"judgement_notes[{index}].theme {theme!r} has no assessment output")
            continue
        expected_summary = note.get("expected_summary")
        if expected_summary is not None and assessment.get("summary") != expected_summary:
            failures.append(
                f"judgement_notes[{index}].expected_summary: "
                f"expected {expected_summary!r}, got {assessment.get('summary')!r}"
            )
        actual_keys = {
            evidence.get("key")
            for evidence in assessment.get("evidence", [])
            if isinstance(evidence, dict)
        }
        for evidence_key in note.get("evidence_keys", []):
            if evidence_key not in actual_keys:
                failures.append(f"judgement_notes[{index}].evidence_keys missing {evidence_key!r}")
    return failures


def require_text(data: dict[str, Any], key: str, prefix: str, failures: list[str]) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{prefix}.{key} must be non-empty text")
        return ""
    return value


if __name__ == "__main__":
    raise SystemExit(main())
