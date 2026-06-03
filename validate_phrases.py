"""Validate phrase-library safety and guarded-topic rules."""

from __future__ import annotations

import json
import sys

from bazi_master.knowledge_base import load_phrase_library
from bazi_master.phrase_engine import PhraseEngine


FORBIDDEN_OUTPUT_TERMS = (
    "一定离婚",
    "一定破产",
    "一定死亡",
    "一定出灾",
    "必死",
    "必破产",
    "必离婚",
    "必有灾",
)

MEDICINE_RULE_IDS = {f"medicine_type_{index:03d}" for index in range(1, 10)}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    library = load_phrase_library()
    failures: list[str] = []
    seen: set[str] = set()
    for phrase in library.get("phrases", []):
        phrase_id = phrase.get("phrase_id")
        if not phrase_id:
            failures.append("phrase missing phrase_id")
            continue
        if phrase_id in seen:
            failures.append(f"duplicate phrase_id {phrase_id}")
        seen.add(phrase_id)
        for field in ("domain", "status", "required_confidence", "fallback_phrase", "forbidden_claims"):
            if field not in phrase:
                failures.append(f"{phrase_id} missing {field}")
        if phrase.get("status") == "guarded_phrase" and not phrase.get("forbidden_claims"):
            failures.append(f"{phrase_id} guarded phrase must define forbidden_claims")
        if phrase.get("sensitivity") == "high" and phrase.get("status") != "guarded_phrase":
            failures.append(f"{phrase_id} high sensitivity phrase must be guarded")
        rendered_text = " ".join(
            str(phrase.get(field, ""))
            for field in ("modern_expression", "conservative_expression", "direct_expression", "fallback_phrase")
        )
        for term in FORBIDDEN_OUTPUT_TERMS:
            if term in rendered_text:
                failures.append(f"{phrase_id} contains forbidden output term {term}")

    selected = PhraseEngine().select(
        domain="health",
        assessments={"health": {"confidence": 0.5}, "strength": {"confidence": 0.5}},
        confidence=0.5,
        guarded=True,
    )
    if not selected:
        failures.append("health guarded phrase selection returned no result")
    elif not selected[0].get("used_fallback"):
        failures.append("health guarded phrase did not force fallback")

    medicine_selected = PhraseEngine().select(
        domain="overview",
        assessments={
            "strength": {
                "confidence": 0.6,
                "executable_rule_ids": ["medicine_type_001", "medicine_type_005"],
                "executable_notes": ["扶抑候选：日主偏强，优先复核泄、耗、制方向"],
                "executable_manual_review_required": True,
            }
        },
        confidence=0.6,
    )
    if not any(item.get("matched_rule_ids") for item in medicine_selected):
        failures.append("medicine executable rule did not select bound phrase")
    for item in medicine_selected:
        if any(str(rule_id).startswith("medicine_type_") for rule_id in item.get("matched_rule_ids", [])):
            if item.get("direct_expression") is not None:
                failures.append("medicine selected phrase exposed direct_expression")
            if "仍需结合全局" not in item.get("text", ""):
                failures.append("medicine selected phrase missing review guard")

    annual_selected = PhraseEngine().select(
        domain="luck_cycle",
        assessments={
            "luck_cycle": {
                "confidence": 0.75,
                "annual": {
                    "triggers": [
                        {
                            "rule_id": "year_005",
                            "status": "active_rule",
                            "summary": "流年干支与原局某柱天克地冲",
                            "risk_guard_required": True,
                            "risk_level": "high",
                            "safe_wording": "该信号只表示相关主题关注度提高，需结合现实背景观察，不构成确定事件判断。",
                            "forbidden_assertions": ["一定死亡", "一定破产", "一定出灾"],
                            "output_allowed": True,
                            "direct_expression_allowed": False,
                        }
                    ]
                },
            }
        },
        confidence=0.75,
        guarded=True,
    )
    if not annual_selected:
        failures.append("annual luck trigger did not select guarded phrase")
    elif not annual_selected[0].get("used_fallback"):
        failures.append("annual luck trigger did not force fallback")
    else:
        annual = annual_selected[0]
        if annual.get("direct_expression") is not None:
            failures.append("annual guarded trigger exposed direct_expression")
        if annual.get("direct_expression_allowed") is not False:
            failures.append("annual guarded trigger did not consume direct_expression_allowed=false")
        if "不构成确定事件判断" not in annual.get("text", ""):
            failures.append("annual guarded trigger did not use safe_wording")
        for forbidden in ("一定死亡", "一定破产", "一定出灾"):
            if forbidden not in annual.get("forbidden_claims", []):
                failures.append(f"annual guarded trigger missing forbidden assertion {forbidden}")

    monthly_selected = PhraseEngine().select(
        domain="luck_cycle",
        assessments={
            "luck_cycle": {
                "confidence": 0.75,
                "monthly_windows": {
                    "windows": [
                        {
                            "triggered_rules": [
                                {
                                    "rule_id": "liuyue_fanyin_original_day_or_month_branch_v1",
                                    "status": "active_rule",
                                    "interpretation": "流月反吟表示对应宫位在该月出现对冲、变动、拉扯或外部刺激。",
                                    "risk_guard_required": True,
                                    "risk_level": "medium",
                                    "safe_wording": "该判断仅作为月份窗口，不单独构成大事判断，也不直接判断吉凶。",
                                    "forbidden_assertions": ["一定离婚", "一定破财"],
                                    "output_allowed": True,
                                    "direct_expression_allowed": False,
                                }
                            ]
                        }
                    ]
                },
            }
        },
        confidence=0.75,
        guarded=True,
    )
    if not monthly_selected:
        failures.append("monthly guarded trigger did not select phrase")
    else:
        monthly = monthly_selected[0]
        if monthly.get("direct_expression") is not None:
            failures.append("monthly guarded trigger exposed direct_expression")
        if "月份窗口" not in monthly.get("text", ""):
            failures.append("monthly guarded trigger did not use safe_wording")
        for forbidden in ("一定离婚", "一定破财"):
            if forbidden not in monthly.get("forbidden_claims", []):
                failures.append(f"monthly guarded trigger missing forbidden assertion {forbidden}")

    daily_selected = PhraseEngine().select(
        domain="luck_cycle",
        assessments={
            "luck_cycle": {
                "confidence": 0.75,
                "daily_filter": {
                    "safe_wording": "该日期仅作为上层岁运或流月窗口内的候选筛选，不单独构成事件判断。",
                    "guard_summary": {
                        "risk_guarded_count": 1,
                        "high_risk_guarded_count": 0,
                        "blocked_count": 0,
                        "direct_expression_allowed": False,
                        "output_allowed": True,
                    },
                    "date_candidates": [
                        {
                            "rule_id": "daily_filter_chong_activated_branch_v1",
                            "date_window_type": "chong_activated_branch",
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
        confidence=0.75,
        guarded=True,
    )
    daily = next((item for item in daily_selected if "daily_filter_chong_activated_branch_v1" in item.get("matched_rule_ids", [])), None)
    if not daily:
        failures.append("daily filter guarded candidate did not select bound phrase")
    else:
        if daily.get("direct_expression") is not None:
            failures.append("daily filter guarded phrase exposed direct_expression")
        if daily.get("direct_expression_allowed") is not False:
            failures.append("daily filter guarded phrase did not block direct expression")
        if "不单独构成事件判断" not in daily.get("text", ""):
            failures.append("daily filter guarded phrase did not use candidate safe_wording")

    daily_summary_blocked = PhraseEngine().select(
        domain="luck_cycle",
        assessments={
            "luck_cycle": {
                "confidence": 0.5,
                "daily_filter": {
                    "safe_wording": "流日只能作为上层触发后的日期筛选，不能每日泛断。",
                    "output_policy": {"forbidden": ["每日泛断", "单凭流日输出重大判断"]},
                    "guard_summary": {
                        "risk_guarded_count": 1,
                        "high_risk_guarded_count": 0,
                        "blocked_count": 1,
                        "direct_expression_allowed": False,
                        "output_allowed": False,
                    },
                    "date_candidates": [],
                },
            }
        },
        confidence=0.5,
        guarded=True,
    )
    if not daily_summary_blocked:
        failures.append("daily filter blocked summary did not return conservative output")
    elif daily_summary_blocked[0].get("output_allowed") is not False:
        failures.append("daily filter blocked summary did not preserve output_allowed=false")

    blocked_selected = PhraseEngine().select(
        domain="luck_cycle",
        assessments={
            "luck_cycle": {
                "confidence": 0.5,
                "annual": {
                    "triggers": [
                        {
                            "rule_id": "luck_guard_001",
                            "status": "guard_rule",
                            "risk_guard_required": True,
                            "risk_level": "blocked",
                            "safe_wording": "流日只能作为上层触发后的日期筛选，不能每日泛断。",
                            "forbidden_assertions": ["每日泛断", "单凭流日输出重大判断"],
                            "output_allowed": False,
                            "direct_expression_allowed": False,
                        }
                    ]
                },
            }
        },
        confidence=0.5,
        guarded=True,
    )
    if not blocked_selected:
        failures.append("blocked guard did not return conservative output")
    else:
        blocked = blocked_selected[0]
        if blocked.get("output_allowed") is not False:
            failures.append("blocked guard did not preserve output_allowed=false")
        if blocked.get("direct_expression") is not None:
            failures.append("blocked guard exposed direct_expression")
        if "不能每日泛断" not in blocked.get("text", ""):
            failures.append("blocked guard missing safe wording")

    print(json.dumps({
        "phrase_count": len(library.get("phrases", [])),
        "guarded_health_selected": selected[:1],
        "medicine_selected": medicine_selected[:2],
        "annual_selected": annual_selected[:1],
        "monthly_selected": monthly_selected[:1],
        "daily_selected": daily_selected[:1],
        "daily_summary_blocked": daily_summary_blocked[:1],
        "blocked_selected": blocked_selected[:1],
        "failures": failures,
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
