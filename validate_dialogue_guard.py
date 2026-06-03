"""End-to-end DialogueEngine guard snapshot validation.

This validator calls DialogueEngine.reply() and scans rendered dialogue output
only.  Forbidden terms inside forbidden_claims / forbidden_assertions are policy
lists, so they are intentionally not treated as rendered violations.
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from bazi_master.dialogue_engine import DialogueEngine


FORBIDDEN_OUTPUT_TERMS = (
    "一定离婚",
    "一定破产",
    "一定死亡",
    "一定出灾",
    "必死",
    "必有灾",
    "某日一定发生",
    "建议买入",
    "建议卖出",
    "一定重病",
    "一定事故",
    "必然发生大事",
    "诊断为",
    "治疗方案",
)

SAFE_EQUIVALENTS = (
    "不构成确定事件判断",
    "不等于确定事件",
    "不单独构成大事判断",
    "不能每日泛断",
    "只做生活习惯提醒",
    "不能诊断疾病",
    "不能替代医生意见",
    "复核点",
    "结构倾向",
)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    dialogue = DialogueEngine()
    rows: list[dict[str, Any]] = []

    snapshots = [
        (
            "annual_chong_day_branch",
            "2028年感情合作要注意什么？",
            _annual_analysis(
                "year_001",
                "流年冲日支，关系、合作或居住主题关注度升高。",
                "该信号只表示相关主题关注度提高，需要结合现实背景观察，不构成确定事件判断。",
                ["一定离婚", "一定分手", "一定出灾"],
            ),
            {
                "domain": "luck_cycle",
                "rule_ids": {"year_001"},
                "guarded": True,
                "safe_text": True,
                "direct_blocked": True,
            },
        ),
        (
            "annual_chong_month_branch",
            "2026年事业工作环境如何？",
            _annual_analysis(
                "year_002",
                "流年冲月支，事业、家庭或工作环境主题关注度升高。",
                "该信号只表示工作环境或阶段节奏值得观察，不构成确定失业、变故或灾祸判断。",
                ["一定失业", "一定出灾", "一定破产"],
            ),
            {
                "domain": "luck_cycle",
                "rule_ids": {"year_002"},
                "guarded": True,
                "safe_text": True,
                "direct_blocked": True,
            },
        ),
        (
            "annual_tianke_dichong",
            "1992年运势有没有大变化？",
            _annual_analysis(
                "year_005",
                "流年干支与原局某柱天克地冲，变化、迁动或冲突主题关注度升高。",
                "该信号只表示相关主题关注度提高，需要结合现实背景观察，不构成确定事件判断。",
                ["一定死亡", "一定破产", "一定出灾"],
            ),
            {
                "domain": "luck_cycle",
                "rule_ids": {"year_005"},
                "guarded": True,
                "safe_text": True,
                "direct_blocked": True,
                "must_contain_any": ("不构成确定事件判断",),
            },
        ),
        (
            "monthly_window",
            "2028年哪个月份要注意？",
            _monthly_analysis(),
            {
                "domain": "luck_cycle",
                "rule_ids": {"liuyue_fanyin_original_day_or_month_branch_v1"},
                "guarded": True,
                "safe_text": True,
                "direct_blocked": True,
                "must_contain_any": ("月份窗口", "观察月份"),
            },
        ),
        (
            "medicine_type_002_health",
            "健康身体怎么样？",
            _medicine_analysis(
                domain="health",
                rule_id="medicine_type_002",
                summary="调候病药只提示寒暖燥湿与节奏适配问题。",
                note="调候候选：只做生活习惯提醒，不能诊断疾病，也不能替代医生意见。",
            ),
            {
                "domain": "health",
                "rule_ids": {"medicine_type_002"},
                "safe_text": True,
                "direct_blocked": True,
                "must_contain_any": ("只做生活习惯提醒", "不能诊断疾病", "不能替代医生意见"),
            },
        ),
        (
            "medicine_type_004_wealth",
            "财运有没有问题？",
            _medicine_analysis(
                domain="wealth",
                rule_id="medicine_type_004",
                summary="清浊复核提示结构中可能存在混杂、并见或用忌不清。",
                note="清浊复核：只作复核点和结构倾向，不等于确定事件。",
                include_pattern=True,
            ),
            {
                "domain": "wealth",
                "rule_ids": {"medicine_type_004"},
                "safe_text": True,
                "direct_blocked": True,
                "must_contain_any": ("复核", "结构倾向", "不等于确定事件"),
            },
        ),
        (
            "daily_guard_blocked",
            "2028年某日会不会出事？",
            _blocked_daily_analysis(),
            {
                "domain": "luck_cycle",
                "rule_ids": {"luck_guard_001"},
                "blocked": True,
                "safe_text": True,
                "direct_blocked": True,
                "must_contain_any": ("流日只能作为上层触发后的日期筛选",),
            },
        ),
        (
            "daily_filter_candidates",
            "2028年哪些日子只能作候选观察？",
            _daily_filter_candidate_analysis(),
            {
                "domain": "luck_cycle",
                "rule_ids": {"daily_filter_chong_activated_branch_v1"},
                "guarded": True,
                "safe_text": True,
                "direct_blocked": True,
                "must_contain_any": ("不单独构成事件判断", "日期候选筛选"),
            },
        ),
    ]

    for name, question, analysis, expect in snapshots:
        reply = dialogue.reply(question, {}, analysis)
        failures = validate_reply(reply, expect)
        rows.append({
            "name": name,
            "question": question,
            "domain": reply.get("domain"),
            "passed": not failures,
            "failures": failures,
            "answer": reply.get("answer"),
            "phrases": reply.get("phrases", []),
            "follow_up": reply.get("follow_up", []),
        })
        print(f"{'PASS' if not failures else 'FAIL'} {len(rows)}: {name}")
        for failure in failures:
            print(f"  - {failure}")

    Path("dialogue_guard_snapshot_report.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0 if all(row["passed"] for row in rows) else 1


def validate_reply(reply: dict[str, Any], expect: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if reply.get("domain") != expect.get("domain"):
        failures.append(f"domain expected {expect.get('domain')}, got {reply.get('domain')}")

    rendered = rendered_text(reply)
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term in rendered:
            failures.append(f"rendered output contains forbidden term: {term}")

    phrases = reply.get("phrases", [])
    phrase_rule_ids = {
        rule_id
        for phrase in phrases
        for rule_id in phrase.get("matched_rule_ids", [])
        if rule_id
    }
    missing_rules = set(expect.get("rule_ids", set())) - phrase_rule_ids
    if missing_rules:
        failures.append(f"missing matched rule ids in phrases: {sorted(missing_rules)}")

    if expect.get("direct_blocked"):
        for phrase in phrases:
            if phrase.get("direct_expression_allowed") is False and phrase.get("direct_expression") is not None:
                failures.append(f"{phrase.get('phrase_id')} exposed direct_expression despite guard")

    if expect.get("guarded") and not any(phrase.get("risk_guard_required") for phrase in phrases):
        failures.append("expected at least one risk_guard_required phrase")

    if expect.get("blocked"):
        first = phrases[0] if phrases else {}
        if first.get("phrase_id") != "guard_blocked_output" and first.get("output_allowed") is not False:
            failures.append("blocked case did not return guard_blocked_output or equivalent blocked phrase")

    if expect.get("safe_text") and not contains_safe_wording(reply):
        failures.append("missing safe wording or equivalent conservative expression")

    needles = tuple(expect.get("must_contain_any", ()))
    if needles and not any(needle in rendered for needle in needles):
        failures.append(f"rendered output missing one of: {list(needles)}")

    if "确定事件判断" in rendered and "不构成确定事件判断" not in rendered:
        failures.append("output references definite event judgment without negation")

    return failures


def rendered_text(reply: dict[str, Any]) -> str:
    parts: list[str] = [str(reply.get("answer", ""))]
    parts.extend(str(item) for item in reply.get("follow_up", []))
    for phrase in reply.get("phrases", []):
        parts.append(str(phrase.get("text", "")))
        if phrase.get("direct_expression") is not None:
            parts.append(str(phrase.get("direct_expression")))
    for evidence in reply.get("evidence", []):
        if isinstance(evidence, dict):
            parts.append(str(evidence.get("uncertainty", "")))
    return "\n".join(parts)


def contains_safe_wording(reply: dict[str, Any]) -> bool:
    text = rendered_text(reply)
    extra_safe = (
        "不构成确定事件判断",
        "不等于确定事件",
        "不单独构成事件判断",
        "不单独构成大事判断",
        "不能每日泛断",
    )
    return any(needle in text for needle in (*SAFE_EQUIVALENTS, *extra_safe))


def _chart() -> dict[str, Any]:
    return {
        "pillars": {"年柱": "己巳", "月柱": "丙子", "日柱": "丙寅", "时柱": "甲午"},
        "day_master": "丙",
    }


def _annual_analysis(
    rule_id: str,
    summary: str,
    safe_wording: str,
    forbidden_assertions: list[str],
) -> dict[str, Any]:
    return {
        "chart": _chart(),
        "assessments": {
            "luck_cycle": {
                "domain": "luck_cycle",
                "summary": "流年触发岁运关注信号；分数只代表关注度，不代表吉凶。",
                "confidence": 0.75,
                "evidence": [
                    {
                        "key": f"luck_cycle.{rule_id}",
                        "source": "luck_cycle",
                        "rule": summary,
                        "matched": {"rule_id": rule_id},
                        "confidence": 0.75,
                        "uncertainty": "大运/流年触发分只代表关注度，不直接代表吉凶。",
                    }
                ],
                "annual": {
                    "triggers": [
                        {
                            "rule_id": rule_id,
                            "status": "active_rule",
                            "summary": summary,
                            "risk_guard_required": True,
                            "risk_level": "high" if rule_id == "year_005" else "medium",
                            "safe_wording": safe_wording,
                            "forbidden_assertions": forbidden_assertions,
                            "output_allowed": True,
                            "direct_expression_allowed": False,
                        }
                    ],
                    "guard_summary": {
                        "risk_guarded_count": 1,
                        "high_risk_guarded_count": 1 if rule_id == "year_005" else 0,
                        "blocked_count": 0,
                        "direct_expression_allowed": False,
                        "output_allowed": True,
                    },
                },
                "monthly_windows": {"windows": [], "guard_summary": {}},
            }
        },
    }


def _monthly_analysis() -> dict[str, Any]:
    return {
        "chart": _chart(),
        "assessments": {
            "luck_cycle": {
                "domain": "luck_cycle",
                "summary": "流月窗口 1 个；流月只用于定位岁运主题更容易显化的月份窗口。",
                "confidence": 0.75,
                "evidence": [
                    {
                        "key": "luck_cycle.monthly_window",
                        "source": "monthly_windows",
                        "rule": "流月反吟原局日支或月支",
                        "matched": {"month": 7},
                        "confidence": 0.7,
                        "uncertainty": "流月窗口不单独构成大事判断，也不直接判断吉凶。",
                    }
                ],
                "annual": {"triggers": [], "guard_summary": {}},
                "monthly_windows": {
                    "windows": [
                        {
                            "month": 7,
                            "triggered_rules": [
                                {
                                    "rule_id": "liuyue_fanyin_original_day_or_month_branch_v1",
                                    "status": "active_rule",
                                    "interpretation": "流月反吟表示对应宫位在该月出现对冲、变动、拉扯或外部刺激。",
                                    "risk_guard_required": True,
                                    "risk_level": "medium",
                                    "safe_wording": "该判断仅作为月份窗口，不单独构成大事判断，也不直接判断吉凶。",
                                    "forbidden_assertions": ["一定离婚", "一定破财", "某月一定发生"],
                                    "output_allowed": True,
                                    "direct_expression_allowed": False,
                                }
                            ],
                            "guard_summary": {
                                "risk_guarded_count": 1,
                                "high_risk_guarded_count": 0,
                                "blocked_count": 0,
                                "direct_expression_allowed": False,
                                "output_allowed": True,
                            },
                        }
                    ],
                    "guard_summary": {
                        "risk_guarded_count": 1,
                        "high_risk_guarded_count": 0,
                        "blocked_count": 0,
                        "direct_expression_allowed": False,
                        "output_allowed": True,
                    },
                },
            }
        },
    }


def _medicine_analysis(
    *,
    domain: str,
    rule_id: str,
    summary: str,
    note: str,
    include_pattern: bool = False,
) -> dict[str, Any]:
    assessments: dict[str, Any] = {
        domain: {
            "domain": domain,
            "summary": summary,
            "confidence": 0.7,
            "evidence": [
                {
                    "key": f"{domain}.{rule_id}",
                    "source": "rule_engine",
                    "rule": summary,
                    "matched": {"rule_id": rule_id},
                    "confidence": 0.7,
                    "uncertainty": "该提示只作为复核点，不等于确定事件。",
                }
            ],
            "executable_rule_ids": [rule_id],
            "executable_notes": [note],
            "executable_manual_review_required": True,
        },
        "yong_shen": {"summary": "用于满足表达层证据键的辅助结构。", "confidence": 0.7},
    }
    if include_pattern:
        assessments["pattern"] = {"summary": "用于满足清浊复核证据键。", "confidence": 0.7}
    return {"chart": _chart(), "assessments": assessments}


def _blocked_daily_analysis() -> dict[str, Any]:
    analysis = {
        "chart": _chart(),
        "assessments": {
            "luck_cycle": {
                "domain": "luck_cycle",
                "summary": "流日候选被守门器阻断，不输出具体事件判断。",
                "confidence": 0.5,
                "evidence": [
                    {
                        "key": "luck_guard.daily",
                        "source": "luck_guard",
                        "rule": "流日只作上层触发后的日期筛选",
                        "matched": {},
                        "confidence": 0.5,
                        "uncertainty": "单一流日不构成事件判断。",
                    }
                ],
                "annual": {
                    "triggers": [
                        {
                            "rule_id": "luck_guard_001",
                            "status": "guard_rule",
                            "summary": "流日只能作为上层触发后的日期筛选",
                            "risk_guard_required": True,
                            "risk_level": "blocked",
                            "safe_wording": "流日只能作为上层触发后的日期筛选，不能每日泛断。",
                            "forbidden_assertions": ["每日泛断", "单凭流日输出重大判断"],
                            "output_allowed": False,
                            "direct_expression_allowed": False,
                        }
                    ],
                    "guard_summary": {
                        "risk_guarded_count": 1,
                        "high_risk_guarded_count": 0,
                        "blocked_count": 1,
                        "direct_expression_allowed": False,
                        "output_allowed": False,
                    },
                },
                "monthly_windows": {"windows": [], "guard_summary": {}},
            }
        },
    }
    return deepcopy(analysis)


def _daily_filter_candidate_analysis() -> dict[str, Any]:
    analysis = {
        "chart": _chart(),
        "assessments": {
            "luck_cycle": {
                "domain": "luck_cycle",
                "summary": "daily_filter 只输出上层窗口内的日期候选，不做事件判断。",
                "confidence": 0.75,
                "evidence": [
                    {
                        "key": "daily_filter.candidate",
                        "source": "daily_filter_engine",
                        "rule": "流日候选",
                        "matched": {"rule_id": "daily_filter_chong_activated_branch_v1"},
                        "confidence": 0.65,
                        "uncertainty": "流日仅作为窗口内的日期筛选，不单独构成事件判断。",
                    }
                ],
                "daily_filter": {
                    "safe_wording": "该日期仅作为上层岁运或流月窗口内的候选筛选，不单独构成事件判断。",
                    "guard_summary": {
                        "risk_guarded_count": 1,
                        "high_risk_guarded_count": 1,
                        "blocked_count": 0,
                        "direct_expression_allowed": False,
                        "output_allowed": True,
                    },
                    "date_candidates": [
                        {
                            "date": "2028-08-15",
                            "day_pillar": "壬申",
                            "date_window_type": "chong_activated_branch",
                            "rule_id": "daily_filter_chong_activated_branch_v1",
                            "risk_guard_required": True,
                            "risk_level": "high",
                            "safe_wording": "该日期仅作为上层岁运或流月窗口内的候选筛选，不单独构成事件判断。",
                            "forbidden_assertions": ["每日泛断", "某日一定发生某事"],
                            "output_allowed": True,
                            "direct_expression_allowed": False,
                        }
                    ],
                },
            }
        },
    }
    return deepcopy(analysis)


if __name__ == "__main__":
    raise SystemExit(main())
