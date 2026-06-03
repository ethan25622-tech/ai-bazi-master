"""Validate controlled GPT/Claude prompt generation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from bazi_master.llm_context_builder import LLMContextBuilder
from bazi_master.master_engine import MasterEngine


REQUIRED_TERMS = [
    "本地解盘证据包",
    "不能重新排盘",
    "不能把候选信号说成定论",
    "盘面事实",
    "资料规则",
    "交叉验证",
    "output_contract",
    "core_findings",
    "evidence_chains",
    "readable_synthesis",
    "judgment_strength",
    "lifestyle_application",
    "past_experience_validation",
    "structural_tradeoff_future_advice",
    "dayun_integration",
    "annual_opportunity_and_remedy",
    "guardrails",
    "gender",
    "不能默认按男命",
    "硬安格局",
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    analysis = MasterEngine().analyze(
        1990,
        1,
        1,
        12,
        0,
        longitude=120.0,
        gender="男",
        target_year=2028,
        target_month=7,
    )
    builder = LLMContextBuilder()
    context = builder.build_context(analysis, "事业和近几年运势怎么看？")
    prompt = builder.render_prompt(analysis, "事业和近几年运势怎么看？")

    failures: list[str] = []
    for term in REQUIRED_TERMS:
        if term not in prompt:
            failures.append(f"prompt missing required term: {term}")

    if context.get("chart", {}).get("pillars") != analysis.get("chart", {}).get("pillars"):
        failures.append("context should preserve local chart pillars")
    if context.get("chart", {}).get("gender") != "男":
        failures.append("context should preserve input gender")
    if "不得默认男命" not in json.dumps(context.get("chart", {}), ensure_ascii=False):
        failures.append("chart should include gender policy")
    if not context.get("evidence_chains"):
        failures.append("context should include evidence chains")
    if not context.get("cross_checks"):
        failures.append("context should include cross checks")
    readable = context.get("readable_synthesis", {})
    if not readable.get("topics"):
        failures.append("context should include readable synthesis topics")
    if "conclusion" not in json.dumps(readable, ensure_ascii=False):
        failures.append("readable synthesis should include conclusions")
    strength = context.get("judgment_strength", {})
    if not strength.get("stable_observations"):
        failures.append("context should include stable observations")
    if not strength.get("supported_tendencies"):
        failures.append("context should include supported tendencies")
    if "判断强度" not in json.dumps(context.get("output_contract", {}), ensure_ascii=False):
        failures.append("output contract should ask the LLM to distinguish judgement strength")
    annual_advice = context.get("annual_opportunity_and_remedy", {})
    if not annual_advice.get("years"):
        failures.append("context should include annual opportunity/remedy years")
    annual_text = json.dumps(annual_advice, ensure_ascii=False)
    for term in ("opportunities", "pressure_points", "cautions", "remedies"):
        if term not in annual_text:
            failures.append(f"annual opportunity/remedy should include {term}")
    past_validation = context.get("past_experience_validation", {})
    if not past_validation.get("years"):
        failures.append("context should include past experience validation years")
    if "likely_past_experience" not in json.dumps(past_validation, ensure_ascii=False):
        failures.append("past validation should include direct likely experience points")
    if "possible_past_challenges" not in json.dumps(past_validation, ensure_ascii=False):
        failures.append("past validation should include possible challenge points")
    tradeoff = context.get("structural_tradeoff_future_advice", {})
    if "取舍" not in json.dumps(tradeoff, ensure_ascii=False):
        failures.append("context should include structural tradeoff future advice")
    if "sources" not in json.dumps(tradeoff, ensure_ascii=False):
        failures.append("tradeoff advice should include sources")
    lifestyle = context.get("lifestyle_application", {})
    lifestyle_text = json.dumps(lifestyle, ensure_ascii=False)
    for term in ("career_types", "residence_guidance", "colors_and_materials", "daily_objects", "dayun_lifestyle_adjustments"):
        if term not in lifestyle_text:
            failures.append(f"lifestyle application should include {term}")
    dayun = context.get("dayun_integration", {})
    if not dayun.get("periods"):
        failures.append("context should include dayun integration periods")
    dayun_text = json.dumps(dayun, ensure_ascii=False)
    for term in ("pressure_points", "stage_theme", "good_side", "bad_side", "career_guidance", "wealth_guidance", "relationship_guidance", "focus_years"):
        if term not in dayun_text:
            failures.append(f"dayun integration should include {term}")
    if "不要输出确定灾祸" not in json.dumps(context.get("guardrails", {}), ensure_ascii=False):
        failures.append("context should include high-risk output guardrails")
    pattern = context.get("core_findings", {}).get("pattern", {})
    if pattern.get("provisional_reasons") is None:
        failures.append("pattern finding should expose provisional reasons")
    if "重新排盘" not in prompt:
        failures.append("prompt should explicitly forbid recalculation")
    if len(prompt) < 2500:
        failures.append("prompt too short to frame an external LLM")
    copy_proc = subprocess.run(
        [
            str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"),
            "-m",
            "bazi_master.cli",
            "--llm-prompt",
            "--copy-only",
            "--year",
            "1990",
            "--month",
            "1",
            "--day",
            "1",
            "--hour",
            "12",
            "--minute",
            "0",
            "--longitude",
            "120",
            "--gender",
            "男",
            "--target-year",
            "2028",
            "--target-month",
            "7",
            "--question",
            "事业和近几年运势怎么看？",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    if copy_proc.returncode != 0:
        failures.append(f"copy-only prompt command failed: {copy_proc.stderr or copy_proc.stdout}")
    if "已复制到剪贴板" not in (copy_proc.stdout + copy_proc.stderr):
        failures.append("copy-only prompt command should report clipboard copy")
    if "本地解盘证据包" in copy_proc.stdout:
        failures.append("copy-only prompt command should not print the full prompt")

    result = {
        "passed": not failures,
        "prompt_length": len(prompt),
        "evidence_chain_count": len(context.get("evidence_chains", [])),
        "cross_check_count": len(context.get("cross_checks", [])),
        "failures": failures,
        "preview": prompt[:1200],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    Path("llm_prompt_sample.txt").write_text(prompt, encoding="utf-8")
    Path("llm_context_validation_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
