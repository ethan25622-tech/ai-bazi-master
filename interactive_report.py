"""Interactive console entry for readable Bazi reports and follow-up questions."""

from __future__ import annotations

import sys

from bazi_master.clipboard import copy_text
from bazi_master.dialogue_engine import DialogueEngine
from bazi_master.feedback_store import append_feedback
from bazi_master.llm_context_builder import LLMContextBuilder
from bazi_master.master_engine import MasterEngine
from bazi_master.report_engine import ReportEngine


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    print("AI 八字解盘")
    print("请按提示输入出生信息。直接回车会使用默认值。")
    print()

    year = ask_int("出生年份，例如 1990", min_value=1902)
    month = ask_int("出生月份 1-12", min_value=1, max_value=12)
    day = ask_int("出生日 1-31", min_value=1, max_value=31)
    hour = ask_int("出生小时 0-23", min_value=0, max_value=23)
    minute = ask_int("出生分钟 0-59", default=0, min_value=0, max_value=59)
    gender = ask_gender()
    longitude = ask_float("出生地经度，国内不确定可直接回车用 120", default=120.0)
    target_year = ask_optional_int("想看哪一年流年？不看可直接回车")
    target_month = None
    if target_year is not None:
        target_month = ask_optional_int("想看该年的第几个节气流月 1-12？不看流日候选可直接回车", min_value=1, max_value=12)

    engine = MasterEngine()
    analysis = engine.analyze(
        year,
        month,
        day,
        hour,
        minute,
        longitude=longitude,
        gender=gender,
        target_year=target_year,
        target_month=target_month,
    )

    print()
    report_text = ReportEngine().render(analysis)
    print("=" * 72)
    print(report_text)
    print("=" * 72)
    print()

    dialogue = DialogueEngine()
    print("你现在可以直接输入想问的问题。")
    print("例如：我适合什么事业方向？ 2028年要注意什么？ 财运怎么看？")
    print("输入 copy report 可复制本地报告。")
    print("输入 prompt 会生成给 GPT/Claude 的受控解盘提示词，并自动复制到剪贴板。")
    print("也可以直接输入 prompt 事业怎么看，把问题一起放进提示词。")
    print("输入 prompt show 可同时打印完整提示词。")
    print("输入 fb 年份 准/不准/部分准 备注，可记录过往校验反馈。")
    print("输入 q、quit、退出 可结束。")
    print()

    while True:
        question = input("你的问题：").strip()
        if question.lower() in {"q", "quit", "exit"} or question in {"退出", "结束"}:
            print("已结束。")
            return 0
        lowered = question.lower()
        if lowered in {"copy report", "copy", "复制报告", "复制"}:
            ok, message = copy_text(report_text)
            print()
            print(message)
            if not ok:
                print(report_text)
            print()
            continue
        if lowered.startswith("fb ") or question.startswith("反馈 "):
            result = save_feedback_command(question, analysis)
            print()
            print(result)
            print()
            continue
        if lowered in {"prompt", "llm", "gpt", "claude", "prompt show"} or lowered.startswith("prompt "):
            prompt_question = None
            show_prompt = lowered == "prompt show"
            if lowered.startswith("prompt ") and not show_prompt:
                prompt_question = question.split(" ", 1)[1].strip() or None
            prompt = LLMContextBuilder().render_prompt(analysis, prompt_question)
            ok, message = copy_text(prompt)
            print()
            print(message)
            if not ok or show_prompt:
                print()
                print(prompt)
            print()
            continue
        if not question:
            continue
        reply = dialogue.reply(question, {}, analysis)
        print()
        print(reply.get("answer", "当前没有足够信息回答这个问题。"))
        follow_up = reply.get("follow_up") or []
        if follow_up:
            print()
            print("可继续追问：" + "；".join(str(item) for item in follow_up))
        print()


def save_feedback_command(command: str, analysis: dict) -> str:
    parts = command.split(maxsplit=3)
    if len(parts) < 4:
        return "反馈格式：fb 年份 准/不准/部分准 备注。例如：fb 2016 准 工作和关系都有变化"
    _, year_text, verdict, note = parts
    try:
        year = int(year_text)
    except ValueError:
        return "年份需要是数字，例如：fb 2016 准 工作和关系都有变化"
    if verdict not in {"准", "不准", "部分准", "一般", "待核实"}:
        return "结果请写：准、不准、部分准、一般、待核实。"
    saved = append_feedback(analysis, year, verdict, note)
    return f"已记录反馈：{year} 年，{verdict}。保存到 {saved['path']}"


def ask_int(label: str, *, default: int | None = None, min_value: int | None = None, max_value: int | None = None) -> int:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{label}{suffix}：").strip()
        if not raw and default is not None:
            return default
        try:
            value = int(raw)
        except ValueError:
            print("请输入整数。")
            continue
        if min_value is not None and value < min_value:
            print(f"不能小于 {min_value}。")
            continue
        if max_value is not None and value > max_value:
            print(f"不能大于 {max_value}。")
            continue
        return value


def ask_optional_int(label: str, *, min_value: int | None = None, max_value: int | None = None) -> int | None:
    while True:
        raw = input(f"{label}：").strip()
        if not raw:
            return None
        try:
            value = int(raw)
        except ValueError:
            print("请输入整数，或直接回车跳过。")
            continue
        if min_value is not None and value < min_value:
            print(f"不能小于 {min_value}。")
            continue
        if max_value is not None and value > max_value:
            print(f"不能大于 {max_value}。")
            continue
        return value


def ask_float(label: str, *, default: float) -> float:
    while True:
        raw = input(f"{label} [{default}]：").strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            print("请输入数字，或直接回车使用默认值。")


def ask_gender() -> str:
    while True:
        raw = input("性别 男/女：").strip()
        if raw in {"男", "女"}:
            return raw
        if raw.lower() in {"m", "male"}:
            return "男"
        if raw.lower() in {"f", "female"}:
            return "女"
        print("请输入 男 或 女。")


if __name__ == "__main__":
    raise SystemExit(main())
