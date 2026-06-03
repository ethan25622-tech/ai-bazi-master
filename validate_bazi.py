"""Compare a local Bazi script against zydx.top results.

The local command is called once per case.  It receives the case JSON on stdin
and must print JSON containing either:
  {"pillars": {"year": "己巳", "month": "丙子", "day": "丙寅", "hour": "戊子"}}
or:
  {"year": "己巳", "month": "丙子", "day": "丙寅", "hour": "戊子"}
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from zydx_client import Pillars, birth_from_mapping, fetch_zydx_result


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate local Bazi output against zydx.top.")
    parser.add_argument("--cases", default="cases.json", help="JSON file with birth cases.")
    parser.add_argument("--local-cmd", required=True, help="Command that reads one case JSON from stdin and prints JSON.")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    failures: list[dict[str, Any]] = []

    for index, case in enumerate(cases, start=1):
        birth = birth_from_mapping(case)
        expected = fetch_zydx_result(birth, timeout=args.timeout)
        actual = run_local(args.local_cmd, case, timeout=args.timeout)
        diff = compare_pillars(expected.pillars, actual)

        label = f"{birth.year:04d}-{birth.month:02d}-{birth.day:02d} {birth.hour:02d}:{birth.minute:02d}"
        if diff:
            failures.append({"case": case, "expected": asdict(expected.pillars), "actual": asdict(actual), "diff": diff})
            print(f"FAIL {index}: {label} {diff}")
        else:
            print(f"PASS {index}: {label} {asdict(actual)}")

    if failures:
        print("\nFailures:")
        print(json.dumps(failures, ensure_ascii=False, indent=2))
        return 1
    return 0


def run_local(command: str, case: dict[str, Any], timeout: int) -> Pillars:
    completed = subprocess.run(
        command,
        input=json.dumps(case, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Local command failed with exit {completed.returncode}:\n{completed.stderr}")
    payload = json.loads(completed.stdout)
    raw = payload.get("pillars", payload)
    return Pillars(year=raw["year"], month=raw["month"], day=raw["day"], hour=raw["hour"])


def compare_pillars(expected: Pillars, actual: Pillars) -> dict[str, dict[str, str]]:
    diff: dict[str, dict[str, str]] = {}
    for key in ("year", "month", "day", "hour"):
        expected_value = getattr(expected, key)
        actual_value = getattr(actual, key)
        if expected_value != actual_value:
            diff[key] = {"expected": expected_value, "actual": actual_value}
    return diff


if __name__ == "__main__":
    sys.exit(main())
