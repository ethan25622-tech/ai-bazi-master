"""Short free-text mobile entrypoint for OpenClaw.

This keeps phone commands compact while still routing to the existing stable
engines. It intentionally uses conservative parsing and asks for missing birth
fields instead of guessing.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from io import StringIO
from contextlib import redirect_stdout

from bazi_master.cli import emit
from bazi_master.dialogue_engine import DialogueEngine
from bazi_master.llm_context_builder import LLMContextBuilder
from bazi_master.master_engine import MasterEngine
from bazi_master.report_engine import ReportEngine
from validate_project_status import main as status_main


HELP = """手机短命令入口

直接让 OpenClaw 在项目目录运行：
  .\\m.cmd 验收
  .\\m.cmd 全测
  .\\m.cmd 提示词 1990-1-1 12:00 男 2028 事业怎么样
  .\\m.cmd 报告 1990-1-1 12点 男 2028年7月
  .\\m.cmd 回答 1990-1-1 12点 男 2028 事业怎么样

可省略：
  分钟默认 0，经度默认 120。

常用模式：
  提示词 / prompt：返回可粘贴到 Claude/GPT 的完整提示词
  报告 / report：返回本地白话报告
  回答 / reply：只返回本地简短回答
  json：返回稳定 JSON
  验收 / status：跑项目验收
  全测 / validate：跑完整验证
"""


@dataclass
class Parsed:
    mode: str
    year: int | None = None
    month: int | None = None
    day: int | None = None
    hour: int | None = None
    minute: int = 0
    longitude: float = 120.0
    gender: str | None = None
    target_year: int | None = None
    target_month: int | None = None
    question: str | None = None


def main() -> int:
    text = " ".join(sys.argv[1:]).strip()
    if not text or text.lower() in {"help", "-h", "--help", "帮助", "用法"}:
        print(HELP)
        return 0

    tg_code = False
    if text.startswith("tg "):
        tg_code = True
        text = text[3:].strip()
    elif text.startswith("复制 "):
        tg_code = True
        text = text[3:].strip()

    if tg_code:
        buffer = StringIO()
        with redirect_stdout(buffer):
            code = run_text(text)
        output = buffer.getvalue()
        print_as_telegram_blocks(output)
        return code

    return run_text(text)


def run_text(text: str) -> int:
    parsed = parse(text)
    if parsed.mode == "status":
        return status_main()
    if parsed.mode == "validate":
        import subprocess

        return subprocess.call(["cmd", "/c", "run_all_validation.cmd"])

    missing = [
        name
        for name, value in [
            ("出生年", parsed.year),
            ("出生月", parsed.month),
            ("出生日", parsed.day),
            ("出生小时", parsed.hour),
            ("性别", parsed.gender),
        ]
        if value is None
    ]
    if missing:
        print("还缺这些信息：" + "、".join(missing))
        print("例：.\\m.cmd 提示词 1990-1-1 12:00 男 2028 事业怎么样")
        return 2

    assert parsed.year is not None
    assert parsed.month is not None
    assert parsed.day is not None
    assert parsed.hour is not None
    assert parsed.gender is not None

    analysis = MasterEngine().analyze(
        parsed.year,
        parsed.month,
        parsed.day,
        parsed.hour,
        parsed.minute,
        longitude=parsed.longitude,
        gender=parsed.gender,
        target_year=parsed.target_year,
        target_month=parsed.target_month,
    )

    if parsed.mode == "report":
        return emit(ReportEngine().render(analysis))
    if parsed.mode == "reply":
        question = parsed.question or "请综合解读。"
        return emit(DialogueEngine().reply(question, {}, analysis))
    if parsed.mode == "json":
        import json

        analysis.pop("legacy", None)
        return emit(json.dumps(analysis, ensure_ascii=False, indent=2))

    question = parsed.question
    return emit(LLMContextBuilder().render_prompt(analysis, question))


def print_as_telegram_blocks(text: str) -> None:
    text = text.rstrip()
    if not text:
        print("没有输出。")
        return

    chunks = split_chunks(text, 3000)
    total = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        if total > 1:
            print(f"[{index}/{total}]")
        print("```text")
        print(chunk.replace("```", "'''"))
        print("```")
        if index != total:
            print()


def split_chunks(text: str, limit: int) -> list[str]:
    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


def parse(text: str) -> Parsed:
    normalized = normalize(text)
    mode = parse_mode(normalized)
    parsed = Parsed(mode=mode)

    parsed.gender = parse_gender(normalized)
    birth_span = parse_birth(normalized)
    if birth_span:
        parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute = birth_span[:5]
    parsed.longitude = parse_longitude(normalized)
    parsed.target_year, parsed.target_month = parse_target(normalized, parsed.year)
    parsed.question = parse_question(normalized, parsed)
    return parsed


def normalize(text: str) -> str:
    replacements = {
        "，": " ",
        "。": " ",
        "：": ":",
        "；": " ",
        "、": " ",
        "　": " ",
        "/": "-",
        ".": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def parse_mode(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ["全测", "完整验证", "validate"]):
        return "validate"
    if any(word in lower for word in ["验收", "状态", "status"]):
        return "status"
    if any(word in lower for word in ["报告", "report"]):
        return "report"
    if any(word in lower for word in ["回答", "简答", "reply"]):
        return "reply"
    if "json" in lower:
        return "json"
    return "prompt"


def parse_gender(text: str) -> str | None:
    if re.search(r"(^|\s)(男|男性|乾造|male|m)(\s|$)", text, re.I):
        return "男"
    if re.search(r"(^|\s)(女|女性|坤造|female|f)(\s|$)", text, re.I):
        return "女"
    return None


def parse_birth(text: str) -> tuple[int, int, int, int, int] | None:
    patterns = [
        r"(?P<y>19\d{2}|20\d{2})\s*[-年]\s*(?P<m>\d{1,2})\s*[-月]\s*(?P<d>\d{1,2})\s*(?:日|号)?\s*(?P<h>\d{1,2})(?::(?P<mi>\d{1,2}))?",
        r"(?P<y>19\d{2}|20\d{2})\s*[-年]\s*(?P<m>\d{1,2})\s*[-月]\s*(?P<d>\d{1,2})\s*(?:日|号)?\s*(?P<h>\d{1,2})\s*点\s*(?P<mi>\d{1,2})?\s*分?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            year = int(match.group("y"))
            month = int(match.group("m"))
            day = int(match.group("d"))
            hour = int(match.group("h"))
            minute = int(match.group("mi") or 0)
            return year, month, day, hour, minute
    return None


def parse_longitude(text: str) -> float:
    match = re.search(r"(?:经度|longitude|lng)\s*[:=]?\s*(\d{2,3}(?:\.\d+)?)", text, re.I)
    if match:
        return float(match.group(1))
    return 120.0


def parse_target(text: str, birth_year: int | None) -> tuple[int | None, int | None]:
    years = [int(value) for value in re.findall(r"(19\d{2}|20\d{2})", text)]
    target_year = next((year for year in years if year != birth_year), None)

    target_month = None
    if target_year is not None:
        after_year = text[text.find(str(target_year)) + 4 :]
        month_match = re.search(r"(?<!\d)(1[0-2]|[1-9])\s*(?:月|流月)", after_year)
        if month_match:
            target_month = int(month_match.group(1))
    return target_year, target_month


def parse_question(text: str, parsed: Parsed) -> str | None:
    cleanup = text
    cleanup = re.sub(r"\b(prompt|report|reply|json|status|validate)\b", " ", cleanup, flags=re.I)
    cleanup = re.sub(r"(提示词|报告|回答|简答|验收|状态|全测|完整验证)", " ", cleanup)
    cleanup = re.sub(r"(19\d{2}|20\d{2})\s*[-年]\s*\d{1,2}\s*[-月]\s*\d{1,2}\s*(?:日|号)?\s*\d{1,2}(?::\d{1,2})?\s*(?:点\s*\d{0,2}\s*分?)?", " ", cleanup)
    cleanup = re.sub(r"(^|\s)(男|男性|乾造|女|女性|坤造|male|female|m|f)(\s|$)", " ", cleanup, flags=re.I)
    cleanup = re.sub(r"(?:经度|longitude|lng)\s*[:=]?\s*\d{2,3}(?:\.\d+)?", " ", cleanup, flags=re.I)
    if parsed.target_year is not None:
        cleanup = cleanup.replace(str(parsed.target_year), " ")
    if parsed.target_month is not None:
        cleanup = re.sub(rf"(?<!\d){parsed.target_month}\s*(月|流月)", " ", cleanup)
    cleanup = re.sub(r"\s+", " ", cleanup).strip()
    return cleanup or None


if __name__ == "__main__":
    raise SystemExit(main())
