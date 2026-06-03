"""Synthesize rule evidence into readable life-topic conclusions."""

from __future__ import annotations

from typing import Any


class ReadingSynthesizer:
    """Build a human-facing layer above raw rule assessments.

    The rule engine is intentionally conservative and often emits candidates or
    review points.  This layer does not make new metaphysical claims; it groups
    existing evidence into practical conclusions, conditions, and actions.
    """

    def synthesize(self, analysis: dict[str, Any]) -> dict[str, Any]:
        assessments = analysis.get("assessments", {})
        return {
            "policy": "以下为综合解读层：先把多条规则证据合成可读结论，再保留依据和边界；不把候选信号说成定论。",
            "overall": self._overall(analysis),
            "topics": {
                "personality": self._personality(assessments),
                "career": self._career(assessments),
                "wealth": self._wealth(assessments),
                "relationship": self._relationship(assessments),
                "health": self._health(assessments),
            },
        }

    def _overall(self, analysis: dict[str, Any]) -> list[str]:
        assessments = analysis.get("assessments", {})
        pattern = assessments.get("pattern", {})
        strength = assessments.get("strength", {})
        tiaohou = assessments.get("tiaohou", {})
        chong_he = assessments.get("chong_he", {})
        lines = []
        pattern_summary = self._summary(pattern)
        strength_summary = self._summary(strength)
        if pattern_summary:
            lines.append(
                f"格局层先把{pattern_summary}当作分析入口，再用强弱、调候和合冲来校验；"
                "若有降级原因或复核信号，不按铁定成格处理。"
            )
        if strength_summary:
            lines.append(f"强弱目前显示为{strength_summary}，因此更适合看具体主题如何发用，而不是简单分成好坏。")
        if self._ids(tiaohou):
            lines.append("调候信号说明环境、节奏和长期承接方式很重要，适合把建议落到作息、平台、学习和节奏管理上。")
        if self._ids(chong_he):
            lines.append("合冲刑害说明盘里有被牵动的关系或宫位，现实中更应关注边界、协调和变化管理。")
        return lines[:4]

    def _personality(self, assessments: dict[str, Any]) -> dict[str, Any]:
        pattern_ids = self._ids(assessments.get("pattern", {}))
        conclusions = []
        manifestations = []
        suggestions = []
        if "pattern_004" in pattern_ids:
            conclusions.append("学习吸收、资质积累、专业系统化是重要优势。")
            manifestations.append("更容易通过长期学习、证书、方法论、稳定平台来形成竞争力。")
            suggestions.append("把知识和经验沉淀成固定流程、作品集、课程、文档或可复用方法。")
        if "pattern_005" in pattern_ids:
            conclusions.append("输出能力值得重点看，适合把技能、经验、内容或服务做成成果。")
            manifestations.append("适合靠稳定产出、作品表达、服务体验或专业手艺获得认可。")
            suggestions.append("定期交付可见成果，比只停留在想法和兴趣上更有用。")
        if "pattern_006" in pattern_ids:
            conclusions.append("承压、竞争和执行力是重要主题，但需要规则承接。")
            manifestations.append("在目标明确、压力清楚、有制度边界的环境中更容易激发行动力。")
            suggestions.append("把压力转成计划、指标和训练，不要变成长期紧绷。")
        if "pattern_007" in pattern_ids:
            conclusions.append("表达、创意、质疑和改进意识较强。")
            manifestations.append("容易看到规则问题，也容易在流程、权威或标准面前有自己的判断。")
            suggestions.append("正式场合先讲证据和方案，再表达不满或修改意见。")
        if "pattern_009" in pattern_ids:
            conclusions.append("自主性和行动力较强，但合作边界要清楚。")
            manifestations.append("不喜欢被过度控制，遇到同辈竞争或资源分配时会更敏感。")
            suggestions.append("适合有自主空间的任务，同时提前讲清资源、权限和分工。")
        if not conclusions:
            conclusions.append("当前能力模式还不能只按单一格局定性，需要结合现实经历校验。")
            suggestions.append("先观察自己更靠学习资质、稳定输出、承压执行，还是表达创意获得优势。")
        return self._topic(
            conclusion=conclusions,
            manifestations=manifestations,
            suggestions=suggestions,
            evidence=self._evidence_labels(assessments.get("pattern", {})),
            boundary="能力模式是结构倾向，不等于职业或性格定论。",
        )

    def _career(self, assessments: dict[str, Any]) -> dict[str, Any]:
        pattern = assessments.get("pattern", {})
        pattern_ids = self._ids(pattern)
        strength = self._summary(assessments.get("strength", {}))
        conclusions = []
        manifestations = []
        suggestions = []
        avoid = []

        if "正官格" in self._summary(pattern):
            conclusions.append("若正官格入口成立，事业上更看重规则、责任、平台信用和可被认可的专业表现。")
            manifestations.append("适合制度清楚、评价标准明确、能积累长期信用的环境。")
            suggestions.append("把工作成果做成可审查、可交付、可被上级或客户确认的形式。")
            avoid.append("避免只靠临场发挥或情绪表达处理正式责任。")
        if "pattern_004" in pattern_ids:
            conclusions.append("专业资质、学习系统和稳定平台可以成为事业支点。")
            suggestions.append("优先补证书、方法论、行业知识和长期可信背书。")
        if "pattern_005" in pattern_ids:
            conclusions.append("技能输出和服务成果是事业打开空间的关键。")
            suggestions.append("建立固定输出节奏：作品、案例、服务流程或内容栏目。")
        if "pattern_007" in pattern_ids:
            conclusions.append("表达和改进意识是优势，但要和规则配合使用。")
            suggestions.append("提出意见时同时给替代方案、证据和执行步骤。")
            avoid.append("避免在规则场景里只表达对错，不给解决方案。")
        if "pattern_006" in pattern_ids:
            conclusions.append("适合有挑战和目标的工作，但压力需要制度化管理。")
            suggestions.append("把竞争压力拆成训练计划、复盘指标和稳定作息。")
        if "中和" in strength or "矛盾" in strength:
            manifestations.append("强弱不宜硬判时，事业判断应优先看环境是否能承接主线，而不是单看个人冲劲。")

        return self._topic(
            conclusion=conclusions or ["事业方向需要从格局、用神和现实行业共同校验，暂不宜单点定论。"],
            manifestations=manifestations,
            suggestions=suggestions or ["先选一个能积累长期信用的主线，再用副项目测试机会。"],
            avoid=avoid,
            evidence=self._evidence_labels(pattern, assessments.get("strength", {}), assessments.get("tiaohou", {})),
            boundary="事业建议只说明更适合的工作方式和发力点，不等于职位高低或成败保证。",
        )

    def _wealth(self, assessments: dict[str, Any]) -> dict[str, Any]:
        wealth = assessments.get("wealth", {})
        pattern_ids = self._ids(assessments.get("pattern", {}))
        wealth_ids = self._ids(wealth)
        conclusions = []
        manifestations = []
        suggestions = []
        avoid = []
        if "medicine_type_004" in wealth_ids:
            conclusions.append("财务和事业选择上最重要的是分主次，先保主线再看副机会。")
            manifestations.append("容易遇到资源很多但方向分散、项目都想接、投入产出不够清楚的情况。")
            suggestions.append("把收入来源分成主收入、成长型机会、消耗型机会三类，先保第一类。")
            avoid.append("避免同时抓太多项目、模糊分账、人情合作和高风险投入。")
        if "pattern_005" in pattern_ids:
            conclusions.append("更适合靠技能、内容、经验、服务或作品形成回报。")
            suggestions.append("让赚钱方式和稳定输出绑定，而不是只靠临时机会。")
        if "pattern_004" in pattern_ids:
            conclusions.append("知识、资质、信任背书会影响资源质量。")
            suggestions.append("可把学习、证书、专业口碑当成长期财务能力的一部分。")
        if not conclusions:
            conclusions.append("当前财务判断更适合看赚钱方式和资源配置，不适合直接断收入高低。")
            suggestions.append("先复盘收入来源、支出压力、合作分账和项目回报是否清楚。")
        return self._topic(
            conclusion=conclusions,
            manifestations=manifestations,
            suggestions=suggestions,
            avoid=avoid,
            evidence=self._evidence_labels(wealth, assessments.get("pattern", {})),
            boundary="财务部分不提供投资建议，也不判断具体盈亏。",
        )

    def _relationship(self, assessments: dict[str, Any]) -> dict[str, Any]:
        chong_he = assessments.get("chong_he", {})
        ids = self._ids(chong_he)
        conclusions = []
        manifestations = []
        suggestions = []
        avoid = []
        if "medicine_type_007" in ids or chong_he.get("executable_notes"):
            conclusions.append("关系和合作里要重点看边界、节奏、责任分配和沟通方式。")
            manifestations.append("容易在合作、亲密关系、居住或工作节奏上出现重新协调。")
            suggestions.append("重要关系先谈清期待、分工、时间、费用和退出条件。")
            avoid.append("避免一见冲合就断好坏，也避免在情绪高点做去留决定。")
        else:
            conclusions.append("关系判断需要结合配偶星、夫妻宫、六亲和现实互动继续校验。")
            suggestions.append("先观察沟通方式、承诺兑现、边界感和现实压力如何影响关系。")
        return self._topic(
            conclusion=conclusions,
            manifestations=manifestations,
            suggestions=suggestions,
            avoid=avoid,
            evidence=self._evidence_labels(chong_he, assessments.get("marriage", {})),
            boundary="婚恋与合作只讲互动模式和复核点，不断确定事件。",
        )

    def _health(self, assessments: dict[str, Any]) -> dict[str, Any]:
        health = assessments.get("health", {})
        tiaohou_ids = self._ids(assessments.get("tiaohou", {}))
        suggestions = ["保持规律作息、压力管理、冷热环境和运动恢复的稳定性。"]
        if "medicine_type_002" in tiaohou_ids:
            suggestions.insert(0, "调候信号出现时，生活上更要重视睡眠、环境冷热、节奏和恢复。")
        return self._topic(
            conclusion=["健康部分只作为传统对应和生活习惯提醒。"],
            manifestations=["可观察压力、作息、环境变化对状态的影响。"],
            suggestions=suggestions,
            evidence=self._evidence_labels(health, assessments.get("tiaohou", {})),
            boundary="不作医学诊断，不替代医生意见。",
        )

    def _topic(
        self,
        *,
        conclusion: list[str],
        manifestations: list[str] | None = None,
        suggestions: list[str] | None = None,
        avoid: list[str] | None = None,
        evidence: list[str] | None = None,
        boundary: str,
    ) -> dict[str, Any]:
        return {
            "conclusion": self._dedupe(conclusion)[:4],
            "likely_manifestations": self._dedupe(manifestations or [])[:4],
            "suggestions": self._dedupe(suggestions or [])[:4],
            "avoid": self._dedupe(avoid or [])[:4],
            "evidence": self._dedupe(evidence or [])[:6],
            "boundary": boundary,
        }

    def _evidence_labels(self, *items: Any) -> list[str]:
        labels = []
        for item in items:
            if not isinstance(item, dict):
                continue
            summary = item.get("summary")
            if summary:
                labels.append(f"结论摘要：{summary}")
            for reason in item.get("provisional_reasons") or []:
                labels.append(f"降级原因：{reason}")
            for rule_id in item.get("executable_rule_ids") or []:
                labels.append(f"可执行规则：{rule_id}")
            for note in item.get("executable_notes") or []:
                labels.append(f"复核信号：{note}")
        return labels

    def _ids(self, item: Any) -> set[str]:
        if not isinstance(item, dict):
            return set()
        return {str(rule_id) for rule_id in item.get("executable_rule_ids") or []}

    def _summary(self, item: Any) -> str:
        if not isinstance(item, dict):
            return ""
        return str(item.get("summary") or "")

    def _dedupe(self, items: list[str]) -> list[str]:
        result = []
        for item in items:
            if item and item not in result:
                result.append(item)
        return result
