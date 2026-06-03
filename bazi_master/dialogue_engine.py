"""Conversation layer that answers from structured analysis only."""

from __future__ import annotations

import re
from typing import Any

from .phrase_engine import PhraseEngine


DOMAIN_KEYWORDS = {
    "career": ("事业", "工作", "职业", "升职", "官", "名声", "学业"),
    "wealth": ("财", "钱", "收入", "投资", "生意", "财富"),
    "marriage": ("婚", "恋", "感情", "伴侣", "夫妻", "桃花"),
    "health": ("健康", "身体", "病", "疾", "体质"),
    "luck_cycle": ("大运", "流年", "年份", "今年", "明年", "运势"),
    "pattern": ("格局", "成格", "败格", "用神"),
    "strength": ("强弱", "身强", "身弱", "日主"),
}

DOMAIN_LABELS = {
    "career": "事业",
    "wealth": "财运",
    "marriage": "婚恋",
    "health": "健康",
    "luck_cycle": "岁运",
    "pattern": "格局",
    "strength": "日主强弱",
    "overview": "总览",
}


class DialogueEngine:
    """Render conservative answers from the stable analysis schema."""

    def __init__(self, phrase_engine: PhraseEngine | None = None) -> None:
        self._phrase_engine = phrase_engine or PhraseEngine()

    def classify(self, user_question: str) -> str:
        text = user_question or ""
        if re.search(r"\d{4}\s*年", text):
            return "luck_cycle"
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return domain
        return "overview"

    def reply(
        self,
        user_question: str,
        profile: dict[str, Any] | None,
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        domain = self.classify(user_question)
        assessments = analysis.get("assessments", {})
        selected = assessments.get(domain) if domain != "overview" else None
        if selected is None:
            selected_items = [
                assessments.get("pattern"),
                assessments.get("strength"),
                assessments.get("yong_shen"),
                assessments.get("luck_cycle"),
            ]
            selected_items = [item for item in selected_items if item]
        else:
            selected_items = [selected]

        confidence = min((item.get("confidence", 0.5) for item in selected_items), default=0.5)
        phrase_suggestions = self._phrase_engine.select(
            domain=domain,
            assessments=assessments,
            confidence=confidence,
            guarded=domain in {"wealth", "marriage", "health", "luck_cycle"},
        )
        conclusion = self._build_conclusion(domain, selected_items, analysis, phrase_suggestions)
        return {
            "domain": domain,
            "answer": conclusion,
            "confidence": confidence,
            "evidence": [ev for item in selected_items for ev in item.get("evidence", [])],
            "phrases": phrase_suggestions,
            "follow_up": self._follow_up(domain),
            "profile_used": profile or {},
        }

    def _build_conclusion(
        self,
        domain: str,
        selected_items: list[dict[str, Any]],
        analysis: dict[str, Any],
        phrases: list[dict[str, Any]] | None = None,
    ) -> str:
        pillars = analysis.get("chart", {}).get("pillars", {})
        title = " / ".join(str(v) for v in pillars.values()) if pillars else "命盘"
        if not selected_items:
            return f"{title}：当前没有足够结构化规则回答这个问题。"

        summaries = "；".join(str(item.get("summary", "未判定")) for item in selected_items)
        uncertainty = self._first_uncertainty(selected_items)
        phrase_text = ""
        if phrases:
            phrase_text = f" 表达层建议：{phrases[0].get('text')}"
        if domain == "overview":
            return f"{title} 的总览倾向：{summaries}。这些是规则层结论，{uncertainty}{phrase_text}"
        label = DOMAIN_LABELS.get(domain, domain)
        return f"{title} 在“{label}”主题上的倾向：{summaries.rstrip('。')}。{uncertainty}{phrase_text}"

    def _first_uncertainty(self, selected_items: list[dict[str, Any]]) -> str:
        for item in selected_items:
            for evidence in item.get("evidence", []):
                uncertainty = evidence.get("uncertainty")
                if uncertainty:
                    return str(uncertainty)
        return "需要结合用户反馈与岁运进一步校验。"

    def _follow_up(self, domain: str) -> list[str]:
        if domain == "luck_cycle":
            return ["请指定想看的年份。", "说明这一年关注事业、财运、婚恋还是健康。"]
        if domain == "overview":
            return ["可以继续追问事业、财运、婚恋、健康或某一年流年。"]
        return ["可以补充具体事件背景，我会只沿用已有证据链继续分析。"]
