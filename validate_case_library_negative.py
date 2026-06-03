"""Negative tests for case-library intake guardrails."""

from __future__ import annotations

import json
import sys
from typing import Any

from validate_case_library import (
    gold_admission_failures,
    validate_excluded_cases,
    validate_gold_cases,
    validate_reference_cases,
    validate_youtube_sources,
)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    checks = [
        check_gold_missing_event_source(),
        check_gold_rectified_birth_time(),
        check_reference_bad_source_url(),
        check_youtube_bad_url(),
        check_youtube_unknown_birth_cannot_be_gold(),
        check_excluded_cannot_be_gold_eligible(),
        check_good_gold_fixture_passes_admission(),
    ]
    failures = [failure for result in checks for failure in result]
    result = {
        "passed": not failures,
        "check_count": len(checks),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def check_gold_missing_event_source() -> list[str]:
    case = good_gold_case()
    case["known_events"][1].pop("source")
    failures = gold_admission_failures(case)
    return expect_contains(failures, "every event must include an external source", "gold_missing_event_source")


def check_gold_rectified_birth_time() -> list[str]:
    case = good_gold_case()
    case["birth_time_status"] = "rectified"
    failures = gold_admission_failures(case)
    return expect_contains(failures, "birth time appears inferred, rectified, or unknown", "gold_rectified_birth_time")


def check_reference_bad_source_url() -> list[str]:
    case = good_gold_case()
    case["known_events"][0]["source_url"] = "not-a-url"
    result = validate_reference_cases({"cases": [case]})
    return expect_contains(result["failures"], "source_url must be an http(s) URL", "reference_bad_source_url")


def check_youtube_bad_url() -> list[str]:
    result = validate_youtube_sources({
        "gold_cases_from_youtube": [],
        "youtube_case_sources": [
            {
                "source_id": "yt_bad_url",
                "video_title": "Bad URL",
                "url": "ftp://example.com/video",
                "classification": "reference_candidates",
                "gold_case_eligible": False,
                "birth_data_status": "unknown",
            }
        ],
    })
    return expect_contains(result["failures"], "url must be an http(s) URL", "youtube_bad_url")


def check_youtube_unknown_birth_cannot_be_gold() -> list[str]:
    result = validate_youtube_sources({
        "gold_cases_from_youtube": [],
        "youtube_case_sources": [
            {
                "source_id": "yt_unknown_gold",
                "video_title": "Unknown birth",
                "url": "https://www.youtube.com/watch?v=example",
                "classification": "reference_candidates",
                "gold_case_eligible": True,
                "birth_data_status": "unknown",
            }
        ],
    })
    return expect_contains(
        result["failures"],
        "cannot be gold eligible with birth_data_status='unknown'",
        "youtube_unknown_birth_cannot_be_gold",
    )


def check_excluded_cannot_be_gold_eligible() -> list[str]:
    result = validate_excluded_cases({
        "cases": [
            {
                "case_id": "excluded_bad_gold",
                "exclusion_reason": "Missing birth time.",
                "source_note": "Unverified forum repost.",
                "gold_case_eligible": True,
            }
        ],
    })
    return expect_contains(
        result["failures"],
        "gold_case_eligible must not be true for excluded cases",
        "excluded_cannot_be_gold_eligible",
    )


def check_good_gold_fixture_passes_admission() -> list[str]:
    result = validate_gold_cases({"cases": [good_gold_case()]})
    failures = []
    if result["failures"]:
        failures.append(f"good_gold_fixture_passes_admission: expected no failures, got {result['failures']}")
    if result["summary"].get("eligible_count") != 1:
        failures.append("good_gold_fixture_passes_admission: expected eligible_count=1")
    return failures


def good_gold_case() -> dict[str, Any]:
    return {
        "case_id": "fixture_gold_good",
        "birth_time_status": "recorded",
        "birth": {
            "year": 1990,
            "month": 1,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "gender": "男",
            "longitude": 120,
        },
        "known_events": [
            {
                "year": 2010,
                "month": 1,
                "day": 1,
                "domain": "career",
                "event": "Fixture full-date event.",
                "source": "Fixture registry",
                "source_url": "https://example.com/event-1",
            },
            {
                "year": 2012,
                "domain": "wealth",
                "event": "Fixture year event.",
                "source": "Fixture registry",
                "source_url": "https://example.com/event-2",
            },
            {
                "year": 2014,
                "domain": "marriage",
                "event": "Fixture year event.",
                "source": "Fixture registry",
            },
        ],
    }


def expect_contains(failures: list[str], expected: str, check_name: str) -> list[str]:
    if any(expected in failure for failure in failures):
        return []
    return [f"{check_name}: expected failure containing {expected!r}, got {failures!r}"]


if __name__ == "__main__":
    raise SystemExit(main())
