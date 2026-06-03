"""Build controlled LLM prompts from the local Bazi evidence package."""

from __future__ import annotations

import json
from typing import Any

from .judgment_synthesizer import JudgmentSynthesizer
from .knowledge_base import index_rules, load_core_rules, load_luck_rules, load_monthly_rules
from .lifestyle_advice import LifestyleAdviceEngine
from .luck_advice import LuckAdviceEngine
from .reading_synthesizer import ReadingSynthesizer


class LLMContextBuilder:
    """Create a bounded "decoding password" for GPT/Claude style interpreters.

    The builder does not ask the model to recalculate the chart.  It packages
    local engine facts, rule sources, evidence, conflicts, and safety limits so
    an external LLM can translate the result into readable Chinese without
    inventing unsupported claims.
    """

    def __init__(self) -> None:
        self.rule_index = index_rules(load_core_rules(), load_luck_rules(), load_monthly_rules())
        self.judgment_synthesizer = JudgmentSynthesizer()
        self.reading_synthesizer = ReadingSynthesizer()
        self.luck_advice = LuckAdviceEngine()
        self.lifestyle_advice = LifestyleAdviceEngine()

    def build_context(self, analysis: dict[str, Any], user_question: str | None = None) -> dict[str, Any]:
        assessments = analysis.get("assessments", {})
        return {
            "purpose": "把本地命理规则引擎生成的证据包翻译成普通人能看懂的解盘，不重新排盘，不自由发挥。",
            "user_question": user_question or "请输出一份完整解盘，重点说明事业、财运、关系、健康提醒和岁运窗口。",
            "chart": self._chart(analysis),
            "readable_synthesis": self.reading_synthesizer.synthesize(analysis),
            "judgment_strength": self.judgment_synthesizer.synthesize(analysis),
            "core_findings": self._core_findings(assessments),
            "evidence_chains": self._evidence_chains(assessments),
            "cross_checks": self._cross_checks(assessments),
            "lifestyle_application": self._lifestyle_application(analysis),
            "past_experience_validation": self._past_experience_validation(analysis),
            "structural_tradeoff_future_advice": self._structural_tradeoff_future_advice(analysis),
            "dayun_integration": self._dayun_integration(analysis),
            "annual_opportunity_and_remedy": self._annual_opportunity_and_remedy(analysis),
            "luck_cycle": self._luck_cycle(assessments.get("luck_cycle", {})),
            "guardrails": self._guardrails(),
            "output_contract": self._output_contract(),
        }

    def render_prompt(self, analysis: dict[str, Any], user_question: str | None = None) -> str:
        context = self.build_context(analysis, user_question)
        payload = json.dumps(context, ensure_ascii=False, indent=2)
        return (
            "你是一名负责把八字规则证据翻译成白话的命理解读助手。\n"
            "重要：你不能重新排盘，不能补造资料，不能把候选信号说成定论。\n"
            "你只能根据下面的“本地解盘证据包”做综合解释。\n\n"
            "请严格按以下原则工作：\n"
            "1. 先综合多条证据，再下保守结论；不要引用单条规则断章取义。\n"
            "2. 遇到 manual_review_required、candidate、复核、冲突信号、provisional_reasons 时，要说“入口/倾向/需要结合现实验证”，不要绝对化。\n"
            "3. 解释每个主要结论时，都要说明依据来自哪些盘面事实和资料规则。\n"
            "4. 输出要面向普通人，少用术语；必须用术语时，立刻翻译成现实含义。\n"
            "5. 健康、婚恋、财务、事故、疾病、死亡、投资等主题必须保守，不做确定事件判断。\n"
            "6. 岁运、流月、流日只代表关注度和时间窗口，不代表吉凶，不代表某事必然发生。\n\n"
            "7. 优先参考 readable_synthesis 输出主题结论；judgment_strength 用于校验哪些话能展开、哪些只能作为观察问题。\n\n"
            "8. annual_opportunity_and_remedy 只用于说明哪些年份哪些主题值得把握、如何趋避，不可说成必然好运或必然灾祸；其中 pressure_points 要翻译成需要特别注意的压力点，action_plan 要翻译成具体行动清单。\n\n"
            "9. dayun_integration 必须用于说明命局主题在十年大运中如何被放大、修正或卡住；不能只讲原局，不讲大运背景。\n\n"
            "10. past_experience_validation 用于直接给出可回看核对的经历主题，不要改写成提问清单，也不要说成百分百发生。\n\n"
            "11. 遇到“需要取舍、分主次、合作边界、护格救应”等内容，必须结合 structural_tradeoff_future_advice 说明未来哪些年份更适合调整，并标明依据来源。\n\n"
            "12. 性别必须按证据包里的 gender 字段处理；gender 为空或未填时，只能做中性解读，不能默认按男命或女命解释。\n\n"
            "13. 不要为了完整解盘硬安格局；如果 pattern 有 provisional_reasons 或复核信号，要把格局说成分析入口，而不是铁定成格。\n\n"
            "14. lifestyle_application 只能作为传统生活取象参考：可以讲适合的职业类型、工作环境、居住环境、颜色、材质、日常物件和大运调整，但不能说成绝对旺运，也不能建议盲目搬家、辞职、投资或大额消费。\n\n"
            "本地解盘证据包如下：\n"
            "```json\n"
            f"{payload}\n"
            "```\n\n"
            "请按 output_contract 指定格式输出。"
        )

    def _chart(self, analysis: dict[str, Any]) -> dict[str, Any]:
        chart = analysis.get("chart", {})
        facts = analysis.get("facts", {})
        birth = analysis.get("input", {})
        return {
            "gender": birth.get("gender"),
            "gender_policy": "六亲、婚恋和部分岁运解读必须按输入性别处理；性别为空时不得默认男命或女命。",
            "pillars": chart.get("pillars", {}),
            "day_master": chart.get("day_master"),
            "month_command": chart.get("month_command"),
            "ten_gods": chart.get("ten_gods", []),
            "tiaohou_yong_shen": facts.get("tiaohou_yong_shen", {}),
            "relation_dynamics": self._compact(facts.get("relation_dynamics", {}), max_chars=1400),
            "health_mapping": facts.get("health_mapping", {}),
        }

    def _core_findings(self, assessments: dict[str, Any]) -> dict[str, Any]:
        domains = [
            "pattern",
            "strength",
            "tiaohou",
            "yong_shen",
            "chong_he",
            "career",
            "wealth",
            "marriage",
            "health",
        ]
        result: dict[str, Any] = {}
        for domain in domains:
            item = assessments.get(domain, {})
            if not isinstance(item, dict):
                continue
            result[domain] = {
                "summary": item.get("summary"),
                "manual_review_required": bool(
                    item.get("manual_review_required") or item.get("executable_manual_review_required")
                ),
                "executable_rule_ids": item.get("executable_rule_ids", []),
                "executable_notes": item.get("executable_notes", []),
                "provisional_reasons": item.get("provisional_reasons", []),
                "interpretation_policy": item.get("interpretation_policy"),
                "rule_sources": item.get("rule_source", []),
            }
        return result

    def _evidence_chains(self, assessments: dict[str, Any]) -> list[dict[str, Any]]:
        chains: list[dict[str, Any]] = []
        for domain, item in assessments.items():
            if not isinstance(item, dict):
                continue
            for ev in item.get("evidence", [])[:6]:
                if not isinstance(ev, dict):
                    continue
                chains.append(
                    {
                        "domain": domain,
                        "source": ev.get("source"),
                        "rule": ev.get("rule"),
                        "matched_facts": self._matched_facts(ev.get("matched")),
                        "confidence": ev.get("confidence"),
                        "uncertainty": ev.get("uncertainty"),
                    }
                )
                if len(chains) >= 28:
                    return chains
        return chains

    def _cross_checks(self, assessments: dict[str, Any]) -> list[str]:
        checks: list[str] = []
        pattern = assessments.get("pattern", {})
        strength = assessments.get("strength", {})
        tiaohou = assessments.get("tiaohou", {})
        chong_he = assessments.get("chong_he", {})
        wealth = assessments.get("wealth", {})

        if isinstance(pattern, dict):
            checks.append(f"格局主线：{pattern.get('summary')}；复核点：{self._join(pattern.get('executable_notes', []))}")
        if isinstance(strength, dict):
            checks.append(f"强弱校验：{strength.get('summary')}。若为中和或矛盾，不要用单纯身强身弱覆盖格局判断。")
        if isinstance(tiaohou, dict):
            checks.append(f"调候校验：{tiaohou.get('summary')}。调候只说明气候优先方向，需与格局、强弱合看。")
        if isinstance(chong_he, dict) and chong_he.get("executable_notes"):
            checks.append(f"合冲校验：{self._join(chong_he.get('executable_notes'))}。合冲只表示结构被牵动，不直接等于坏事。")
        if isinstance(wealth, dict) and wealth.get("executable_notes"):
            checks.append(f"清浊/财务校验：{self._join(wealth.get('executable_notes'))}。财务主题只谈方式与取舍，不断收入高低。")

        return [item for item in checks if item and "None" not in item]

    def _luck_cycle(self, luck_cycle: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(luck_cycle, dict):
            return {}
        annual = luck_cycle.get("annual", {})
        monthly = luck_cycle.get("monthly_windows", {})
        daily = luck_cycle.get("daily_filter", {})
        return {
            "summary": luck_cycle.get("summary"),
            "annual_triggers": [self._trigger_item(trigger) for trigger in annual.get("triggers", [])[:8]]
            if isinstance(annual, dict)
            else [],
            "monthly_windows": [
                {
                    "month_name": window.get("month_name"),
                    "ganzhi": window.get("ganzhi"),
                    "summary": window.get("summary"),
                    "triggered_rules": [self._trigger_item(rule) for rule in window.get("triggered_rules", [])[:4]],
                    "guard_summary": window.get("guard_summary"),
                }
                for window in monthly.get("windows", [])[:8]
            ]
            if isinstance(monthly, dict)
            else [],
            "daily_filter": self._compact(daily, max_chars=1600) if isinstance(daily, dict) else {},
        }

    def _annual_opportunity_and_remedy(self, analysis: dict[str, Any]) -> dict[str, Any]:
        target_year = analysis.get("input", {}).get("target_year")
        try:
            start_year = int(target_year) if target_year else None
        except (TypeError, ValueError):
            start_year = None
        return self.luck_advice.forecast_years(analysis, start_year=start_year, years=8)

    def _past_experience_validation(self, analysis: dict[str, Any]) -> dict[str, Any]:
        return self.luck_advice.past_validation(analysis)

    def _lifestyle_application(self, analysis: dict[str, Any]) -> dict[str, Any]:
        target_year = analysis.get("input", {}).get("target_year")
        try:
            start_year = int(target_year) if target_year else None
        except (TypeError, ValueError):
            start_year = None
        return self.lifestyle_advice.build(analysis, start_year=start_year)

    def _structural_tradeoff_future_advice(self, analysis: dict[str, Any]) -> dict[str, Any]:
        target_year = analysis.get("input", {}).get("target_year")
        try:
            start_year = int(target_year) if target_year else None
        except (TypeError, ValueError):
            start_year = None
        return self.luck_advice.structural_tradeoff_advice(analysis, start_year=start_year, years=8)

    def _dayun_integration(self, analysis: dict[str, Any]) -> dict[str, Any]:
        target_year = analysis.get("input", {}).get("target_year")
        try:
            start_year = int(target_year) if target_year else None
        except (TypeError, ValueError):
            start_year = None
        return self.luck_advice.dayun_integration(analysis, start_year=start_year, max_periods=4)

    def _trigger_item(self, trigger: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(trigger, dict):
            return {}
        rule_id = str(trigger.get("rule_id", ""))
        rule = self.rule_index.get(rule_id, {})
        rule_trigger = rule.get("trigger", {})
        return {
            "rule_id": rule_id,
            "rule_name_or_condition": rule.get("name") or rule_trigger.get("condition") if isinstance(rule_trigger, dict) else rule_id,
            "summary": trigger.get("summary"),
            "possible_domains": trigger.get("possible_domains", []),
            "evidence": trigger.get("evidence"),
            "risk_guard_required": trigger.get("risk_guard_required"),
            "risk_level": trigger.get("risk_level"),
            "safe_wording": trigger.get("safe_wording"),
            "output_allowed": trigger.get("output_allowed"),
            "direct_expression_allowed": trigger.get("direct_expression_allowed"),
        }

    def _guardrails(self) -> dict[str, Any]:
        return {
            "must_not": [
                "不要输出确定灾祸、确定疾病、确定死亡、确定离婚、确定破产、确定事故。",
                "不要给医学诊断、治疗方案、投资买卖建议。",
                "不要在 gender 为空或未填时默认按男命或女命解释。",
                "不要为了追求完整结果而硬安格局、硬断身强身弱或硬给吉凶。",
                "不要把 trigger_score 解释成吉凶分或危险程度。",
                "不要把流日候选说成吉日、凶日、灾日。",
                "不要为了完整而补造没有出现在证据包里的出生信息、事件、职业、家庭背景。",
            ],
            "must_do": [
                "每个主题都说明依据链：盘面事实 + 资料规则 + 交叉校验。",
                "格局存在降级原因时，用“格局入口/候选/复核”表达，不说铁定成格。",
                "涉及六亲、婚恋、配偶星、子女星时，先确认 gender 字段；没有性别就用中性措辞。",
                "把候选/复核点翻译成现实中的观察方向。",
                "遇到证据冲突时说明冲突，而不是强行定论。",
                "给出可验证的问题，例如行业、阶段、过往年份、现实事件。",
            ],
        }

    def _output_contract(self) -> dict[str, Any]:
        return {
            "format": [
                "一、先给总判断：用 3-5 条白话说明本盘最重要的主线。",
                "二、判断强度：分清哪些是稳定底座、哪些是倾向、哪些只是复核点。",
                "三、依据链：说明这些判断分别来自哪些盘面事实、资料规则和交叉验证。",
                "四、事业与能力：讲适合的工作方式、环境、优势和需要避开的用法。",
                "五、财务与资源：讲赚钱方式、资源取舍、合作边界，不断收入高低。",
                "六、婚恋与关系：讲互动模式和复核点，不断确定事件。",
                "七、健康与生活习惯：只做传统观察和生活节奏提醒，不诊断。",
                "八、生活应用与传统取象：讲适合的职业类型、工作环境、居住/办公环境、颜色、材质、日常物件和大运阶段调整；必须说明这些只是传统参考，不是绝对旺运。",
                "九、过往经历校验：直接列出最值得回看的年份和可能经历主题，不要只问问题。",
                "十、结构取舍与未来应对：凡是提到需要取舍、分主次、合作边界，都要接未来年份和参考依据。",
                "十一、大运与命局结合：说明当前和未来几步大运如何承接命局主题、哪些地方可用、哪些地方要防。",
                "十二、如果有流年/流月/流日：只讲关注窗口和主题，不讲必然事件。",
                "十三、未来年份建议：列出值得注意的年份、本年行动重点、可把握的机会、需要特别注意的压力点、需要避开的坑、解药/行动做法，并把 action_plan 写成“具体可以做、第一步、不建议、现实校验点”。",
                "十四、最后列出 3-5 个最值得用户补充验证的问题。",
            ],
            "tone": "像一个谨慎但能讲人话的命理老师，少说规则编号，多说现实含义。",
        }

    def _matched_facts(self, matched: Any) -> Any:
        if not isinstance(matched, dict):
            return matched
        facts: dict[str, Any] = {}
        keys = [
            "日主",
            "月令",
            "月令本气",
            "月令十神",
            "月令主气十神",
            "本气透干",
            "首选用神",
            "次选用神",
            "原局已透首选",
            "成败状态",
            "破格因素",
            "护卫候选",
            "透干十神计数",
            "关系事实",
            "动态判断",
            "facts",
            "dynamic",
        ]
        for key in keys:
            if key in matched:
                facts[key] = self._compact(matched[key], max_chars=900)
        if not facts:
            return self._compact(matched, max_chars=900)
        return facts

    def _compact(self, value: Any, *, max_chars: int) -> Any:
        text = json.dumps(value, ensure_ascii=False, default=str)
        if len(text) <= max_chars:
            return value
        return text[:max_chars] + "...（已截断，完整证据在本地 analysis 中）"

    def _join(self, value: Any) -> str:
        if not value:
            return ""
        if isinstance(value, str):
            return value
        return "、".join(str(item) for item in value if item)
