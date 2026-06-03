"""Validate stable rule-layer expectations against fixture cases."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from bazi_master.knowledge_base import load_core_rules, load_luck_rules, load_monthly_rules
from bazi_master.master_engine import MasterEngine


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate rule-engine output against expected cases.")
    parser.add_argument("--cases", default="rule_cases.json")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    library_failures = validate_rule_libraries()
    for failure in library_failures:
        print(f"LIBRARY FAIL {failure}")
    if library_failures:
        return 1

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    engine = MasterEngine()
    rows: list[dict[str, Any]] = []

    for index, case in enumerate(cases, start=1):
        analysis = engine.analyze(**case["input"])
        failures = compare_expectations(analysis, case.get("expect", {}))
        rows.append({
            "index": index,
            "name": case.get("name", f"case-{index}"),
            "passed": not failures,
            "failures": failures,
        })
        print(f"{'PASS' if not failures else 'FAIL'} {index}: {rows[-1]['name']}")
        for failure in failures:
            print(f"  - {failure}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(row["passed"] for row in rows) else 1


def validate_rule_libraries() -> list[str]:
    allowed_statuses = {"active_rule", "candidate_rule", "manual_review", "guard_rule"}
    failures: list[str] = []
    seen: set[str] = set()
    libraries = (("core", load_core_rules()), ("luck", load_luck_rules()), ("monthly", load_monthly_rules()))
    for library_name, library in libraries:
        for index, rule in enumerate(library.get("rules", []), start=1):
            rule_id = rule.get("rule_id")
            if not rule_id:
                failures.append(f"{library_name}[{index}] missing rule_id")
                continue
            if rule_id in seen:
                failures.append(f"duplicate rule_id {rule_id}")
            seen.add(rule_id)
            status = rule.get("status")
            if status not in allowed_statuses:
                failures.append(f"{rule_id} invalid status {status!r}")
            for field in ("domain", "trigger", "uncertainty"):
                if field not in rule:
                    failures.append(f"{rule_id} missing {field}")
    return failures


def compare_expectations(analysis: dict[str, Any], expect: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for dotted_path, expected in flatten(expect).items():
        actual = read_dotted_path(analysis, dotted_path)
        if actual != expected:
            failures.append(f"{dotted_path}: expected {expected!r}, got {actual!r}")
    return failures


def flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten(value, path))
        else:
            result[path] = value
    return result


def read_dotted_path(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


if __name__ == "__main__":
    raise SystemExit(main())
