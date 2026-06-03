"""Validate lightweight case-library staging files.

This validator is separate from ``validate_mingli_cases.py``.  The files under
``case_library/`` are intake/staging datasets, not all formal regression cases.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CASE_LIBRARY_DIR = Path("case_library")
KNOWN_CLASSIFICATIONS = {"gold_case", "reference_case", "reference_candidates", "excluded_case"}
DISALLOWED_GOLD_BIRTH_STATUSES = {"rectified", "blogger_inferred", "unknown"}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate case-library staging datasets.")
    parser.add_argument("--case-library-dir", default=str(CASE_LIBRARY_DIR))
    parser.add_argument("--json-out", default="case_library_validation_report.json")
    args = parser.parse_args()

    root = Path(args.case_library_dir)
    failures: list[str] = []
    warnings: list[str] = []
    report: dict[str, Any] = {"case_library_dir": str(root), "datasets": {}}

    gold = load_json(root / "gold_cases.json", failures)
    reference = load_json(root / "reference_cases.json", failures)
    youtube = load_json(root / "youtube_candidate_sources.json", failures)
    excluded = load_json(root / "excluded_cases.json", failures)

    if gold is not None:
        gold_result = validate_gold_cases(gold)
        failures.extend(gold_result["failures"])
        warnings.extend(gold_result["warnings"])
        report["datasets"]["gold_cases"] = gold_result["summary"]
    if reference is not None:
        reference_result = validate_reference_cases(reference)
        failures.extend(reference_result["failures"])
        warnings.extend(reference_result["warnings"])
        report["datasets"]["reference_cases"] = reference_result["summary"]
    if youtube is not None:
        youtube_result = validate_youtube_sources(youtube)
        failures.extend(youtube_result["failures"])
        warnings.extend(youtube_result["warnings"])
        report["datasets"]["youtube_candidate_sources"] = youtube_result["summary"]
    if excluded is not None:
        excluded_result = validate_excluded_cases(excluded)
        failures.extend(excluded_result["failures"])
        warnings.extend(excluded_result["warnings"])
        report["datasets"]["excluded_cases"] = excluded_result["summary"]

    report["passed"] = not failures
    report["failures"] = failures
    report["warnings"] = warnings
    Path(args.json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if failures:
        print("FAIL case_library")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS case_library")
    print(json.dumps({"datasets": report["datasets"], "warnings": warnings}, ensure_ascii=False, indent=2))
    return 0


def load_json(path: Path, failures: list[str]) -> Any | None:
    if not path.exists():
        failures.append(f"{path} is missing")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"{path} is not valid JSON: {exc}")
        return None


def validate_gold_cases(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        failures.append("gold_cases.cases must be a list")
        cases = []

    seen: set[str] = set()
    eligible_count = 0
    for index, case in enumerate(cases, start=1):
        prefix = f"gold_cases[{index}]"
        if not isinstance(case, dict):
            failures.append(f"{prefix} must be an object")
            continue
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            failures.append(f"{prefix}.case_id must be non-empty text")
        elif case_id in seen:
            failures.append(f"{prefix}.case_id duplicates {case_id!r}")
        seen.add(str(case_id))
        gold_failures = gold_admission_failures(case)
        if gold_failures:
            failures.extend(f"{prefix}: {failure}" for failure in gold_failures)
        else:
            eligible_count += 1
        failures.extend(validate_event_urls(case.get("known_events") or case.get("life_events"), prefix))

    if not cases:
        warnings.append("gold_cases is empty; this is allowed until source material meets the admission policy")

    return {
        "failures": failures,
        "warnings": warnings,
        "summary": {"case_count": len(cases), "eligible_count": eligible_count},
    }


def validate_reference_cases(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        failures.append("reference_cases.cases must be a list")
        cases = []

    gold_ready = 0
    auto_regression_false = 0
    for index, case in enumerate(cases, start=1):
        prefix = f"reference_cases[{index}]"
        if not isinstance(case, dict):
            failures.append(f"{prefix} must be an object")
            continue
        if not case.get("case_id"):
            failures.append(f"{prefix}.case_id is required")
        if case.get("auto_regression") is False:
            auto_regression_false += 1
        failures.extend(validate_event_urls(case.get("known_events") or case.get("life_events"), prefix))
        gold_failures = gold_admission_failures(case)
        if not gold_failures:
            gold_ready += 1
            if case.get("auto_regression") is not False:
                warnings.append(f"{prefix} appears gold-eligible but should be reviewed before auto_regression=true")
        else:
            warnings.append(f"{prefix} remains reference-only: {'; '.join(gold_failures)}")

    return {
        "failures": failures,
        "warnings": warnings,
        "summary": {
            "case_count": len(cases),
            "gold_ready_candidates": gold_ready,
            "auto_regression_false_count": auto_regression_false,
        },
    }


def validate_youtube_sources(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    gold_cases = payload.get("gold_cases_from_youtube", [])
    sources = payload.get("youtube_case_sources", [])

    if not isinstance(gold_cases, list):
        failures.append("youtube_candidate_sources.gold_cases_from_youtube must be a list")
        gold_cases = []
    if not isinstance(sources, list):
        failures.append("youtube_candidate_sources.youtube_case_sources must be a list")
        sources = []

    for index, case in enumerate(gold_cases, start=1):
        gold_failures = gold_admission_failures(case)
        if gold_failures:
            failures.extend(f"youtube gold_cases_from_youtube[{index}]: {failure}" for failure in gold_failures)

    for index, source in enumerate(sources, start=1):
        prefix = f"youtube_case_sources[{index}]"
        if not isinstance(source, dict):
            failures.append(f"{prefix} must be an object")
            continue
        for key in ("source_id", "video_title", "url", "classification"):
            if not isinstance(source.get(key), str) or not source[key]:
                failures.append(f"{prefix}.{key} must be non-empty text")
        if isinstance(source.get("url"), str) and not is_http_url(source["url"]):
            failures.append(f"{prefix}.url must be an http(s) URL")
        classification = source.get("classification")
        if classification not in KNOWN_CLASSIFICATIONS:
            failures.append(f"{prefix}.classification must be one of {sorted(KNOWN_CLASSIFICATIONS)}")
        if source.get("gold_case_eligible") is True:
            warnings.append(f"{prefix} is marked gold_case_eligible=true; promote only after full admission check")
        if source.get("birth_data_status") in {"blogger_inferred", "unknown"}:
            if source.get("gold_case_eligible") is True:
                failures.append(f"{prefix} cannot be gold eligible with birth_data_status={source.get('birth_data_status')!r}")

    return {
        "failures": failures,
        "warnings": warnings,
        "summary": {
            "source_count": len(sources),
            "youtube_gold_count": len(gold_cases),
            "gold_eligible_flags": sum(1 for source in sources if isinstance(source, dict) and source.get("gold_case_eligible") is True),
        },
    }


def validate_excluded_cases(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        failures.append("excluded_cases.cases must be a list")
        cases = []

    seen: set[str] = set()
    for index, case in enumerate(cases, start=1):
        prefix = f"excluded_cases[{index}]"
        if not isinstance(case, dict):
            failures.append(f"{prefix} must be an object")
            continue
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            failures.append(f"{prefix}.case_id must be non-empty text")
        elif case_id in seen:
            failures.append(f"{prefix}.case_id duplicates {case_id!r}")
        seen.add(str(case_id))
        for key in ("exclusion_reason", "source_note"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                failures.append(f"{prefix}.{key} must be non-empty text")
        source_url = case.get("source_url")
        if source_url is not None and (not isinstance(source_url, str) or not is_http_url(source_url)):
            failures.append(f"{prefix}.source_url must be an http(s) URL when present")
        if case.get("gold_case_eligible") is True:
            failures.append(f"{prefix}.gold_case_eligible must not be true for excluded cases")

    if not cases:
        warnings.append("excluded_cases is empty; this is allowed until rejected intake items are recorded")

    return {
        "failures": failures,
        "warnings": warnings,
        "summary": {"case_count": len(cases)},
    }


def gold_admission_failures(case: Any) -> list[str]:
    if not isinstance(case, dict):
        return ["case must be an object"]
    failures: list[str] = []
    birth = case.get("birth")
    if not isinstance(birth, dict):
        return ["birth must be an object"]
    for field in ("year", "month", "day", "hour", "minute"):
        if not isinstance(birth.get(field), int):
            failures.append(f"birth.{field} must be an integer")
    if case.get("calendar_support") == "needs_international_timezone_support":
        failures.append("calendar/timezone support is not ready for automatic gold regression")
    status_text = " ".join(
        str(value).lower()
        for value in (
            case.get("birth_data_status"),
            case.get("birth_time_status"),
            (case.get("birth_time_reliability") or {}).get("level") if isinstance(case.get("birth_time_reliability"), dict) else "",
            (case.get("birth_time_reliability") or {}).get("note") if isinstance(case.get("birth_time_reliability"), dict) else "",
        )
    )
    if any(disallowed in status_text for disallowed in DISALLOWED_GOLD_BIRTH_STATUSES):
        failures.append("birth time appears inferred, rectified, or unknown")
    events = case.get("known_events") or case.get("life_events")
    if not isinstance(events, list) or len(events) < 3:
        failures.append("at least 3 known_events/life_events are required")
    else:
        full_date_events = [
            event for event in events
            if isinstance(event, dict)
            and isinstance(event.get("year"), int)
            and isinstance(event.get("month"), int)
            and isinstance(event.get("day"), int)
        ]
        if not full_date_events:
            failures.append("at least 1 event must include year, month, and day")
        sourced_events = [
            event for event in events
            if isinstance(event, dict) and isinstance(event.get("source"), str) and event["source"].strip()
        ]
        if len(sourced_events) != len(events):
            failures.append("every event must include an external source")
    return failures


def validate_event_urls(events: Any, prefix: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(events, list):
        return failures
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            continue
        source_url = event.get("source_url")
        if source_url is not None and (not isinstance(source_url, str) or not is_http_url(source_url)):
            failures.append(f"{prefix}.events[{index}].source_url must be an http(s) URL when present")
    return failures


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


if __name__ == "__main__":
    raise SystemExit(main())
