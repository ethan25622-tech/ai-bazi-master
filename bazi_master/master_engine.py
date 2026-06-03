"""Top-level stable analysis engine for the AI Bazi master."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .bridge import load_core
from .daily_filter_engine import DailyFilterEngine
from .luck_cycle_engine import LuckCycleEngine
from .rule_engine import RuleEngine
from .schema import SUPPORTED_SCHEMA_VERSION


class MasterEngine:
    """Produce the v1 stable schema without changing the legacy engine."""

    def __init__(self, rule_engine: RuleEngine | None = None) -> None:
        core = load_core()
        self._narrator = core["NarratorEngine"]()
        self._rule_engine = rule_engine or RuleEngine()
        self._luck_engine = LuckCycleEngine()
        self._daily_filter_engine = DailyFilterEngine()

    def analyze(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int = 0,
        *,
        longitude: float = 120.0,
        gender: str | None = None,
        target_year: int | None = None,
        target_month: int | None = None,
    ) -> dict[str, Any]:
        legacy = self._narrator.narrate(
            year,
            month,
            day,
            hour,
            minute,
            longitude=longitude,
            gender=gender,
        )
        rules = self._rule_engine.evaluate(legacy)
        schema = self._build_schema(
            legacy,
            rules,
            year,
            month,
            day,
            hour,
            minute,
            longitude,
            gender,
            target_year,
            target_month,
        )
        if target_year is not None:
            annual = self._luck_engine.evaluate_year(schema, target_year)
            monthly = self._luck_engine.evaluate_months(schema, target_year)
            schema["assessments"]["luck_cycle"]["annual"] = annual
            schema["assessments"]["luck_cycle"]["monthly_windows"] = monthly
            schema["assessments"]["luck_cycle"]["summary"] = (
                f"{target_year} 年触发 {len(annual.get('triggers', []))} 条岁运关注信号；"
                f"流月窗口 {len(monthly.get('windows', []))} 个；分数只代表关注度，不代表吉凶。"
            )
            for trigger in annual.get("triggers", []):
                evidence_record = {
                    "key": f"luck_cycle.{trigger.get('rule_id')}",
                    "source": trigger.get("evidence", {}).get("source", "luck_cycle_rules_v2"),
                    "rule": trigger.get("summary"),
                    "matched": trigger.get("matched", {}),
                    "confidence": 0.65,
                    "uncertainty": trigger.get("uncertainty"),
                }
                schema["evidence"].append(evidence_record)
                schema["assessments"]["luck_cycle"].setdefault("evidence", []).append(evidence_record)
            if target_month is not None:
                daily = self._daily_filter_engine.evaluate(
                    schema,
                    target_year,
                    target_month,
                    annual=annual,
                    monthly_windows=monthly,
                )
                schema["assessments"]["luck_cycle"]["daily_filter"] = daily["daily_filter"]
        return schema

    def _build_schema(
        self,
        legacy: dict[str, Any],
        rules: dict[str, Any],
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        longitude: float,
        gender: str | None,
        target_year: int | None,
        target_month: int | None,
    ) -> dict[str, Any]:
        basic = legacy.get("basic_info", {})
        evidence = []
        for item in rules.values():
            evidence.extend(item.get("evidence", []))

        return {
            "schema_version": SUPPORTED_SCHEMA_VERSION,
            "input": {
                "calendar": "solar",
                "year": year,
                "month": month,
                "day": day,
                "hour": hour,
                "minute": minute,
                "gender": gender,
                "longitude": longitude,
                "target_year": target_year,
                "target_month": target_month,
                "timezone_policy": "China-standard-time compatible; true solar time adjusted by longitude",
                "day_boundary_policy": "default 23:00 Zi-hour boundary; 00:00 is kept as optional school setting",
                "supported_range": "1902-03-01 onward for zydx-compatible pillar validation",
            },
            "chart": {
                "pillars": deepcopy(basic.get("四柱", {})),
                "day_master": basic.get("日主"),
                "month_command": basic.get("月令"),
                "true_solar_time": basic.get("真太阳时"),
                "ten_gods": deepcopy(legacy.get("certain", {}).get("十神分布", [])),
            },
            "facts": {
                "relations": deepcopy(legacy.get("certain", {}).get("地支刑冲合", {})),
                "relation_dynamics": deepcopy(legacy.get("certain", {}).get("合冲动态判断", {})),
                "tiaohou_yong_shen": deepcopy(legacy.get("certain", {}).get("调候用神", {})),
                "dayun": deepcopy(legacy.get("certain", {}).get("大运")),
                "health_mapping": deepcopy(legacy.get("certain", {}).get("健康对应", {})),
                "liuqin_mapping": deepcopy(legacy.get("certain", {}).get("六亲对应", {})),
            },
            "assessments": rules,
            "rule_library": self._rule_engine.library_summary(),
            "evidence": evidence,
            "conversation_hints": {
                "recommended_openers": [
                    "你最想先看事业、财运、婚恋、健康，还是近年运势？",
                    "如果要看流年，请补充具体年份或当前关注的事件类型。",
                ],
                "boundaries": [
                    "不把倾向当成确定事件。",
                    "不输出医疗、法律、投资等高风险决策建议。",
                    "具体年份判断必须结合大运、流年和用户反馈校验。",
                ],
                "style": "证据保守：先给倾向，再给依据、置信度和不确定点。",
            },
            "legacy": legacy,
        }
