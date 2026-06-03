"""Smoke-test the interactive report console flow."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PYTHON = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    input_text = "\n".join([
        "1990",
        "1",
        "1",
        "12",
        "0",
        "男",
        "",
        "2028",
        "7",
        "copy report",
        "prompt 事业和近几年运势怎么看？",
        "fb 2016 准 工作和关系都有变化",
        "事业适合什么方向？",
        "q",
        "",
    ])
    proc = subprocess.run(
        [str(PYTHON), "interactive_report.py"],
        input=input_text,
        text=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    failures: list[str] = []
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        failures.append(f"interactive process returned {proc.returncode}")
    for expected in ("AI 八字解盘", "AI 八字解盘报告", "命盘基本信息", "copy report", "已复制到剪贴板", "已记录反馈", "你的问题", "事业"):
        if expected not in output:
            failures.append(f"interactive output missing {expected}")
    for forbidden in ("一定死亡", "一定离婚", "一定破产", "建议买入", "诊断为"):
        if forbidden in output:
            failures.append(f"interactive output contains forbidden term {forbidden}")

    if failures:
        print("FAIL interactive_report")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS interactive_report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
