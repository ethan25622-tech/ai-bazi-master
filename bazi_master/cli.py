"""Command line entrypoint for the stable AI Bazi master layer."""

from __future__ import annotations

import argparse
import json
import sys

from .clipboard import copy_text
from .dialogue_engine import DialogueEngine
from .llm_context_builder import LLMContextBuilder
from .master_engine import MasterEngine
from .report_engine import ReportEngine


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run the AI Bazi master stable schema.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--hour", type=int, required=True)
    parser.add_argument("--minute", type=int, default=0)
    parser.add_argument("--longitude", type=float, default=120.0)
    parser.add_argument("--gender", choices=["男", "女"])
    parser.add_argument("--target-year", type=int, help="Optional annual luck-cycle year to evaluate.")
    parser.add_argument("--target-month", type=int, help="Optional flow-month index for guarded daily filtering.")
    parser.add_argument("--question", help="Optional user question for DialogueEngine.")
    parser.add_argument("--reply-only", action="store_true", help="Print only the dialogue reply when --question is used.")
    parser.add_argument("--report", action="store_true", help="Print a readable full report instead of raw JSON.")
    parser.add_argument("--llm-prompt", action="store_true", help="Print a controlled GPT/Claude prompt from local evidence.")
    parser.add_argument("--copy", action="store_true", help="Copy the final output to the Windows clipboard as well.")
    parser.add_argument("--copy-only", action="store_true", help="Copy the final output to clipboard without printing the long text.")
    parser.add_argument("--include-legacy", action="store_true", help="Keep legacy narrator payload in output.")
    args = parser.parse_args()

    engine = MasterEngine()
    analysis = engine.analyze(
        args.year,
        args.month,
        args.day,
        args.hour,
        args.minute,
        longitude=args.longitude,
        gender=args.gender,
        target_year=args.target_year,
        target_month=args.target_month,
    )
    if args.report:
        return emit(ReportEngine().render(analysis), copy=args.copy or args.copy_only, copy_only=args.copy_only)

    if args.llm_prompt:
        return emit(LLMContextBuilder().render_prompt(analysis, args.question), copy=args.copy or args.copy_only, copy_only=args.copy_only)

    if not args.include_legacy:
        analysis.pop("legacy", None)

    if args.question:
        reply = DialogueEngine().reply(args.question, {}, analysis)
        payload = reply if args.reply_only else {"analysis": analysis, "reply": reply}
    else:
        payload = analysis

    return emit(json.dumps(payload, ensure_ascii=False, indent=2), copy=args.copy or args.copy_only, copy_only=args.copy_only)


def emit(text: str, *, copy: bool = False, copy_only: bool = False) -> int:
    if copy:
        ok, message = copy_text(text)
        print(message, file=sys.stderr if not ok else sys.stdout)
        if not ok:
            if copy_only:
                print(text)
            return 1
    if not copy_only:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
