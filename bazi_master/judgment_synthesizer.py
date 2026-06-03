"""Conservative synthesis of rule evidence into judgement strength bands."""

from __future__ import annotations

from typing import Any


class JudgmentSynthesizer:
    """Group existing evidence into stable, tendency, and review-only findings."""

    def synthesize(self, analysis: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        assessments = analysis.get("assessments", {})
        chart = analysis.get("chart", {})
        facts = analysis.get("facts", {})
        result = {
            "stable_observations": [],
            "supported_tendencies": [],
            "review_points": [],
        }

        self._add_chart_facts(result, chart, facts)
        self._add_pattern(result, assessments)
        self._add_strength(result, assessments)
        self._add_tiaohou(result, assessments, facts)
        self._add_chong_he(result, assessments)
        self._add_life_topics(result, assessments)
        self._add_luck(result, assessments)
        return result

    def _add_chart_facts(self, result: dict[str, list[dict[str, Any]]], chart: dict[str, Any], facts: dict[str, Any]) -> None:
        pillars = chart.get("pillars", {})
        if pillars:
            self._push(
                result,
                "stable_observations",
                "盘面基础",
                f"四柱已排出：{self._join([f'{k}{v}' for k, v in pillars.items()])}。",
                "这是排盘事实，用来作为后续判断底座；本身不代表吉凶。",
            )
        day_master = chart.get("day_master")
        month_command = chart.get("month_command")
        if day_master or month_command:
            self._push(
                result,
                "stable_observations",
                "日主与月令",
                f"日主为{day_master or '未识别'}，月令为{month_command or '未识别'}。",
                "日主和月令是格局、强弱、调候的共同参照点。",
            )

        relations = facts.get("relation_dynamics", {})
        if isinstance(relations, dict):
            clashes = relations.get("相冲分析") or []
            if clashes:
                text = []
                for item in clashes[:2]:
                    if isinstance(item, dict) and item.get("冲"):
                        text.append(f"{item.get('冲')}，位置{item.get('位置', '待定')}，冲力{item.get('冲力', '待定')}")
                if text:
                    self._push(
                        result,
                        "stable_observations",
                        "合冲事实",
                        f"盘中已见{self._join(text)}。",
                        "这说明相关柱位被牵动，但不能直接翻译成坏事或确定事件。",
                    )

    def _add_pattern(self, result: dict[str, list[dict[str, Any]]], assessments: dict[str, Any]) -> None:
        pattern = assessments.get("pattern", {})
        if not isinstance(pattern, dict):
            return
        summary = pattern.get("summary")
        ids = set(pattern.get("executable_rule_ids") or [])
        notes = pattern.get("executable_notes") or []
        if summary:
            reasons = pattern.get("provisional_reasons") or []
            boundary = "它来自月令定格、透干和成败救应规则，但仍要被强弱、调候和合冲复核。"
            if reasons:
                boundary += f" 降级原因：{self._join(reasons)}。"
            self._push(
                result,
                "supported_tendencies",
                "格局入口",
                f"可以先以“{summary}”作为分析入口，而不是铁定结论。",
                boundary,
            )
        if ids & {"pattern_004", "pattern_005", "pattern_006", "pattern_007", "pattern_009"}:
            translated = []
            if "pattern_004" in ids:
                translated.append("学习、资质、专业系统和长期积累值得看")
            if "pattern_005" in ids:
                translated.append("技能输出、内容/作品、服务能力值得看")
            if "pattern_006" in ids:
                translated.append("承压、竞争、执行和规则边界值得看")
            if "pattern_007" in ids:
                translated.append("表达、创意、规则摩擦和成果转化值得看")
            if "pattern_009" in ids:
                translated.append("自主性、同辈竞争和合作边界值得看")
            self._push(
                result,
                "supported_tendencies",
                "能力结构",
                f"较适合从{self._join(translated)}这些现实方向理解。",
                "这些是格局候选信号的现实翻译，不等于职业定论。",
            )
        if pattern.get("manual_review_required") and notes:
            self._push(
                result,
                "review_points",
                "格局复核",
                self._join(notes[:4]),
                "这些点需要结合全局和现实背景复核，不建议单条定论。",
            )

    def _add_strength(self, result: dict[str, list[dict[str, Any]]], assessments: dict[str, Any]) -> None:
        strength = assessments.get("strength", {})
        if not isinstance(strength, dict):
            return
        summary = str(strength.get("summary") or "")
        if "中和" in summary or "矛盾" in summary:
            self._push(
                result,
                "supported_tendencies",
                "强弱口径",
                "强弱不宜硬判成单纯身强或身弱。",
                "这类盘更适合看格局、调候和具体主题谁先被引动。",
            )
        elif "弱" in summary:
            self._push(
                result,
                "supported_tendencies",
                "强弱口径",
                "日主偏弱时，支持系统、学习资源、稳定环境和恢复能力更重要。",
                "仍需看是否从格、是否有印比承接，不能只按弱论。",
            )
        elif "强" in summary:
            self._push(
                result,
                "supported_tendencies",
                "强弱口径",
                "日主偏强时，输出、责任、规则、目标压力或资源承接更重要。",
                "仍需看是否从旺或格局是否需要顺泄，不宜硬制。",
            )

    def _add_tiaohou(self, result: dict[str, list[dict[str, Any]]], assessments: dict[str, Any], facts: dict[str, Any]) -> None:
        tiaohou = assessments.get("tiaohou", {})
        raw = facts.get("tiaohou_yong_shen", {})
        if not isinstance(tiaohou, dict):
            return
        first = raw.get("首选用神") if isinstance(raw, dict) else None
        present = raw.get("原局已透首选") if isinstance(raw, dict) else None
        summary = tiaohou.get("summary")
        if first:
            line = f"调候优先方向为{self._join(first)}"
            if present:
                line += f"，且原局已透{self._join(present)}"
            line += "。"
            self._push(
                result,
                "supported_tendencies",
                "调候取向",
                line,
                "调候说明气候和五行活性方向，应与格局用神交叉看，不单独定成败。",
            )
        elif summary:
            self._push(result, "review_points", "调候取向", str(summary), "调候证据不足时只作背景参考。")

    def _add_chong_he(self, result: dict[str, list[dict[str, Any]]], assessments: dict[str, Any]) -> None:
        chong_he = assessments.get("chong_he", {})
        if not isinstance(chong_he, dict):
            return
        notes = chong_he.get("executable_notes") or []
        if notes:
            self._push(
                result,
                "review_points",
                "合冲刑害",
                self._join(notes[:4]),
                "合冲刑害只表示结构互动和主题被牵动，需要看位置、距离、用神和岁运重复触发。",
            )

    def _add_life_topics(self, result: dict[str, list[dict[str, Any]]], assessments: dict[str, Any]) -> None:
        wealth = assessments.get("wealth", {})
        if isinstance(wealth, dict) and wealth.get("executable_notes"):
            self._push(
                result,
                "review_points",
                "财务资源",
                self._join((wealth.get("executable_notes") or [])[:4]),
                "这里更适合判断赚钱方式、资源取舍和主次，不直接断收入高低。",
            )
        health = assessments.get("health", {})
        if isinstance(health, dict) and health.get("summary"):
            self._push(
                result,
                "stable_observations",
                "健康提醒口径",
                str(health.get("summary")),
                "健康只按传统对应关系做生活习惯提醒，不作医学诊断。",
            )

    def _add_luck(self, result: dict[str, list[dict[str, Any]]], assessments: dict[str, Any]) -> None:
        luck = assessments.get("luck_cycle", {})
        if not isinstance(luck, dict):
            return
        annual = luck.get("annual", {})
        if isinstance(annual, dict) and annual.get("triggers"):
            triggers = annual.get("triggers", [])[:3]
            texts = [str(trigger.get("summary")) for trigger in triggers if trigger.get("summary")]
            if texts:
                self._push(
                    result,
                    "supported_tendencies",
                    "岁运窗口",
                    f"{annual.get('target_year')} 年可重点观察：{self._join(texts)}。",
                    "岁运触发只代表关注度和主题引动，不代表吉凶或确定事件。",
                )

    def _push(
        self,
        result: dict[str, list[dict[str, Any]]],
        bucket: str,
        title: str,
        finding: str,
        boundary: str,
    ) -> None:
        if not finding:
            return
        result[bucket].append(
            {
                "title": title,
                "finding": finding,
                "boundary": boundary,
            }
        )

    def _join(self, value: Any) -> str:
        if not value:
            return ""
        if isinstance(value, str):
            return value
        return "、".join(str(item) for item in value if item)
