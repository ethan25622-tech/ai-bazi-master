"""Generate a detailed local-vs-ZYDX Bazi validation report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from zydx_client import birth_from_mapping, fetch_zydx_result


PILLAR_KEYS = ("year", "month", "day", "hour")
PILLAR_LABELS = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Create detailed Bazi validation report.")
    parser.add_argument("--cases", required=True)
    parser.add_argument("--local-cmd", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []

    for index, case in enumerate(cases, start=1):
        birth = birth_from_mapping(case)
        expected = fetch_zydx_result(birth, timeout=args.timeout)
        actual = run_local(args.local_cmd, case, timeout=args.timeout)
        diffs = {
            key: {"local": actual[key], "zydx": getattr(expected.pillars, key)}
            for key in PILLAR_KEYS
            if actual[key] != getattr(expected.pillars, key)
        }
        rows.append({
            "index": index,
            "case": case,
            "input": f"{birth.year:04d}-{birth.month:02d}-{birth.day:02d} {birth.hour:02d}:{birth.minute:02d}",
            "sex": "女" if birth.sex == 0 else "男",
            "local": actual,
            "zydx": asdict(expected.pillars),
            "solar": expected.solar,
            "lunar": expected.lunar,
            "jieqi": expected.jieqi,
            "match": not diffs,
            "diffs": diffs,
        })
        print(f"{'PASS' if not diffs else 'FAIL'} {index}: {rows[-1]['input']}")

    Path(args.out).write_text(render_markdown(args.cases, rows), encoding="utf-8")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(row["match"] for row in rows) else 1


def run_local(command: str, case: dict[str, Any], timeout: int) -> dict[str, str]:
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
    return {key: raw[key] for key in PILLAR_KEYS}


def render_markdown(cases_path: str, rows: list[dict[str, Any]]) -> str:
    total = len(rows)
    passed = sum(1 for row in rows if row["match"])
    failed = total - passed
    lines = [
        "# Bazi Validation Report",
        "",
        f"- Cases: `{cases_path}`",
        f"- Total: {total}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "| # | 输入 | 性别 | 本地排盘 | 网站排盘 | 结论 |",
        "|---:|---|---|---|---|---|",
    ]
    for row in rows:
        local = pillars_text(row["local"])
        zydx = pillars_text(row["zydx"])
        verdict = "一致" if row["match"] else "不一致: " + diff_text(row["diffs"])
        lines.append(f"| {row['index']} | {row['input']} | {row['sex']} | {local} | {zydx} | {verdict} |")

    lines.extend(["", "## Details", ""])
    for row in rows:
        lines.extend([
            f"### {row['index']}. {row['input']} {row['sex']}",
            "",
            f"- 本地: {pillars_text(row['local'])}",
            f"- 网站: {pillars_text(row['zydx'])}",
            f"- 结论: {'一致' if row['match'] else '不一致'}",
        ])
        if row["diffs"]:
            lines.append(f"- 差异: {diff_text(row['diffs'])}")
        if row.get("solar"):
            lines.append(f"- 网站公历: {row['solar']}")
        if row.get("lunar"):
            lines.append(f"- 网站农历: {row['lunar']}")
        if row.get("jieqi"):
            lines.append(f"- 网站节气: {row['jieqi'].replace(chr(13), '').replace(chr(10), ' / ')}")
        lines.append("")
    return "\n".join(lines)


def pillars_text(pillars: dict[str, str]) -> str:
    return " ".join(f"{PILLAR_LABELS[key]}{pillars[key]}" for key in PILLAR_KEYS)


def diff_text(diffs: dict[str, dict[str, str]]) -> str:
    return "；".join(
        f"{PILLAR_LABELS[key]} 本地 {value['local']} / 网站 {value['zydx']}"
        for key, value in diffs.items()
    )


if __name__ == "__main__":
    sys.exit(main())
