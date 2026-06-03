"""大运/流年 v1 trigger engine.

This engine scores attention-worthy annual triggers.  Scores are not luck
scores and never mean "good" or "bad" by themselves.
"""

from __future__ import annotations

from typing import Any

from .knowledge_base import load_luck_rules, load_monthly_rules
from .luck_guard import build_guard_summary, guard_annual_triggers, guard_monthly_windows


STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
MONTH_BRANCHES = "寅卯辰巳午未申酉戌亥子丑"
MONTH_NAMES = ["寅月", "卯月", "辰月", "巳月", "午月", "未月", "申月", "酉月", "戌月", "亥月", "子月", "丑月"]
SANHE_SETS = [set(item) for item in (("申", "子", "辰"), ("亥", "卯", "未"), ("寅", "午", "戌"), ("巳", "酉", "丑"))]
SANHUI_SETS = [set(item) for item in (("寅", "卯", "辰"), ("巳", "午", "未"), ("申", "酉", "戌"), ("亥", "子", "丑"))]
CHONG = {
    ("子", "午"), ("午", "子"), ("丑", "未"), ("未", "丑"),
    ("寅", "申"), ("申", "寅"), ("卯", "酉"), ("酉", "卯"),
    ("辰", "戌"), ("戌", "辰"), ("巳", "亥"), ("亥", "巳"),
}
LIU_HE = {
    ("子", "丑"), ("丑", "子"), ("寅", "亥"), ("亥", "寅"),
    ("卯", "戌"), ("戌", "卯"), ("辰", "酉"), ("酉", "辰"),
    ("巳", "申"), ("申", "巳"), ("午", "未"), ("未", "午"),
}
STEM_KE = {
    ("甲", "戊"), ("甲", "己"), ("乙", "戊"), ("乙", "己"),
    ("丙", "庚"), ("丙", "辛"), ("丁", "庚"), ("丁", "辛"),
    ("戊", "壬"), ("戊", "癸"), ("己", "壬"), ("己", "癸"),
    ("庚", "甲"), ("庚", "乙"), ("辛", "甲"), ("辛", "乙"),
    ("壬", "丙"), ("壬", "丁"), ("癸", "丙"), ("癸", "丁"),
}


class LuckCycleEngine:
    """Evaluate大运 + 流年 triggers for one target year."""

    def __init__(self) -> None:
        self.rule_set = load_luck_rules()
        self.rules = {rule["rule_id"]: rule for rule in self.rule_set.get("rules", [])}
        self.monthly_rule_set = load_monthly_rules()
        self.monthly_rules = {rule["rule_id"]: rule for rule in self.monthly_rule_set.get("rules", [])}

    def evaluate_year(self, analysis: dict[str, Any], target_year: int) -> dict[str, Any]:
        pillars = analysis.get("chart", {}).get("pillars", {})
        dayun = analysis.get("facts", {}).get("dayun") or {}
        current_dayun = self._current_dayun(dayun, target_year)
        year_gz = ganzhi_year(target_year)
        triggers: list[dict[str, Any]] = []

        if current_dayun:
            dy_gz = current_dayun.get("干支", "")
            triggers.extend(self._dayun_triggers(dy_gz, pillars))
            if dy_gz == year_gz:
                triggers.append(self._trigger("year_003", year_gz, current_dayun, ["大运主题集中显化"]))

        triggers.extend(self._year_triggers(year_gz, pillars))
        triggers = self._apply_repeat_bonuses(triggers)
        triggers = guard_annual_triggers(self._rank(triggers))
        return {
            "target_year": target_year,
            "year_pillar": year_gz,
            "current_dayun": current_dayun,
            "trigger_score_note": "分数只代表关注度，不代表吉凶。",
            "triggers": triggers,
            "guard_summary": build_guard_summary(triggers),
            "top_domains": self._top_domains(triggers),
            "daily_filter_policy": self.rule_set.get("score_strategy", {}).get(
                "single_daily_trigger_guard",
                "单一流日不输出重要日",
            ),
        }

    def evaluate_months(self, analysis: dict[str, Any], target_year: int) -> dict[str, Any]:
        annual = self.evaluate_year(analysis, target_year)
        pillars = analysis.get("chart", {}).get("pillars", {})
        original_branches = [branch(value) for value in pillars.values() if value]
        dayun_branch = branch((annual.get("current_dayun") or {}).get("干支", ""))
        year_branch = branch(annual.get("year_pillar", ""))
        context_branches = [item for item in [*original_branches, dayun_branch, year_branch] if item]
        activated = self._annual_activated_branches(annual, pillars)

        windows = []
        for index, month_branch in enumerate(MONTH_BRANCHES):
            month_gz = month_ganzhi(target_year, index)
            triggers = []
            triggers.extend(self._monthly_fuyin_fanyin(month_branch, pillars))
            triggers.extend(self._monthly_chong_activated(month_branch, activated))
            triggers.extend(self._monthly_complete_sets(month_branch, context_branches, original_branches))
            triggers = self._merge_monthly_repeat_triggers(triggers)
            triggers = self._rank(triggers)
            if triggers:
                windows.append({
                    "month_index": index + 1,
                    "month_name": MONTH_NAMES[index],
                    "ganzhi": month_gz,
                    "level": "month_window",
                    "summary": "本月是岁运主题的月份窗口，不单独断大事。",
                    "triggered_rules": triggers,
                    "output_policy_note": "该判断仅作为月份窗口，不单独构成大事判断。",
                })
        windows = guard_monthly_windows(windows, annual)
        return {
            "target_year": target_year,
            "calendar_boundary": self.monthly_rule_set.get("rule_set", {}).get("calendar_boundary", {}),
            "global_policy": self.monthly_rule_set.get("rule_set", {}).get("principles", []),
            "windows": windows,
            "guard_summary": build_guard_summary([
                trigger
                for window in windows
                for trigger in window.get("triggered_rules", [])
                if isinstance(trigger, dict)
            ]),
        }

    def _dayun_triggers(self, dayun_gz: str, pillars: dict[str, str]) -> list[dict[str, Any]]:
        if not dayun_gz:
            return []
        triggers = []
        dy_branch = branch(dayun_gz)
        if (dy_branch, branch(pillars.get("\u6708\u67f1", ""))) in CHONG:
            triggers.append(self._trigger("luck_003", dayun_gz, {"pillar": "\u6708\u67f1"}, ["career_platform", "family_structure"]))
        if (dy_branch, branch(pillars.get("\u65e5\u67f1", ""))) in CHONG:
            triggers.append(self._trigger("luck_004", dayun_gz, {"pillar": "\u65e5\u67f1"}, ["relationship", "collaboration", "housing"]))
        if (dy_branch, branch(pillars.get("\u5e74\u67f1", ""))) in CHONG:
            triggers.append(self._trigger("luck_007", dayun_gz, {"pillar": "\u5e74\u67f1"}, ["family_background", "external_environment"]))
        if (dy_branch, branch(pillars.get("\u65f6\u67f1", ""))) in CHONG:
            triggers.append(self._trigger("luck_008", dayun_gz, {"pillar": "\u65f6\u67f1"}, ["long_term_plan", "future_outcome"]))
        for pillar_name, pillar_gz in pillars.items():
            if dayun_gz == pillar_gz:
                triggers.append(self._trigger("luck_005", dayun_gz, {"pillar": pillar_name}, ["repeat_theme"]))
            if is_tian_ke_di_chong(dayun_gz, pillar_gz):
                triggers.append(self._trigger("luck_006", dayun_gz, {"pillar": pillar_name}, ["change", "movement", "conflict"]))
        return triggers

    def _year_triggers(self, year_gz: str, pillars: dict[str, str]) -> list[dict[str, Any]]:
        triggers = []
        y_branch = branch(year_gz)
        if (y_branch, branch(pillars.get("日柱", ""))) in CHONG:
            triggers.append(self._trigger("year_001", year_gz, {"pillar": "日柱"}, ["婚恋", "合作", "居住"]))
        if (y_branch, branch(pillars.get("月柱", ""))) in CHONG:
            triggers.append(self._trigger("year_002", year_gz, {"pillar": "月柱"}, ["事业", "家庭", "工作环境"]))
        for pillar_name, pillar_gz in pillars.items():
            if year_gz == pillar_gz:
                triggers.append(self._trigger("year_004", year_gz, {"pillar": pillar_name}, ["旧事重现"]))
            elif y_branch == branch(pillar_gz):
                triggers.append(self._trigger(
                    "year_008",
                    year_gz,
                    {"pillar": pillar_name, "branch": y_branch, "downgrade": True, "match_type": "branch_fuyin"},
                    ["旧事重现", "主题回响"],
                ))
            if is_tian_ke_di_chong(year_gz, pillar_gz):
                triggers.append(self._trigger("year_005", year_gz, {"pillar": pillar_name}, ["变化", "迁动", "冲突"]))
            if (y_branch, branch(pillar_gz)) in LIU_HE:
                triggers.append(self._trigger("year_006", year_gz, {"pillar": pillar_name}, ["合作", "牵连"]))
        combination = self._year_complete_combination(y_branch, pillars)
        if combination:
            triggers.append(self._trigger("year_007", year_gz, combination, ["combination", "theme_aggregation"]))
        return triggers

    def _year_complete_combination(self, year_branch: str, pillars: dict[str, str]) -> dict[str, Any] | None:
        original = [
            {"pillar": pillar_name, "branch": branch(pillar_gz)}
            for pillar_name, pillar_gz in pillars.items()
            if branch(pillar_gz)
        ]
        original_branches = {item["branch"] for item in original}
        for combo_name, combo_sets in (("sanhe", SANHE_SETS), ("sanhui", SANHUI_SETS)):
            for combo in combo_sets:
                if year_branch not in combo:
                    continue
                needed = combo - {year_branch}
                if needed.issubset(original_branches):
                    return {
                        "combination": combo_name,
                        "branches": sorted(combo),
                        "year_branch": year_branch,
                        "original_pillars": [
                            item for item in original if item["branch"] in needed
                        ],
                    }
        return None

    def _trigger(
        self,
        rule_id: str,
        ganzhi: str,
        matched: dict[str, Any] | None,
        fallback_domains: list[str],
    ) -> dict[str, Any]:
        rule = self.rules.get(rule_id, {})
        return {
            "rule_id": rule_id,
            "status": rule.get("status", "active_rule"),
            "level": rule.get("level"),
            "triggered": True,
            "trigger_score": rule.get("trigger_score", 0),
            "ganzhi": ganzhi,
            "possible_domains": rule.get("possible_domains", fallback_domains),
            "affected_palace": rule.get("affected_palace", []),
            "summary": rule.get("trigger", {}).get("condition", rule.get("name", rule_id)),
            "matched": matched or {},
            "evidence": rule.get("evidence", {}),
            "uncertainty": rule.get("uncertainty", "需结合喜忌与现实背景。"),
            "output_policy": rule.get("output_policy", {}),
        }

    def _current_dayun(self, dayun: dict[str, Any], target_year: int) -> dict[str, Any] | None:
        steps = dayun.get("大运列表") or []
        current = None
        for step in steps:
            start = int(step.get("起始年", 0))
            if start <= target_year:
                current = step
        return current

    def _rank(self, triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(triggers, key=lambda item: item.get("trigger_score", 0), reverse=True)

    def _apply_repeat_bonuses(self, triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        bonus = int(self.rule_set.get("score_strategy", {}).get("same_palace_repeat_bonus", 0))
        if not bonus:
            return triggers

        by_pillar: dict[str, list[dict[str, Any]]] = {}
        for trigger in triggers:
            pillar = trigger.get("matched", {}).get("pillar")
            if isinstance(pillar, str) and pillar:
                by_pillar.setdefault(pillar, []).append(trigger)

        for pillar, pillar_triggers in by_pillar.items():
            if len(pillar_triggers) < 2:
                continue
            rule_ids = [str(trigger.get("rule_id")) for trigger in pillar_triggers]
            for trigger in pillar_triggers:
                base_score = int(trigger.get("trigger_score", 0))
                trigger["trigger_score_base"] = base_score
                trigger["trigger_score"] = base_score + bonus
                trigger["repeat_context"] = {
                    "same_palace_repeat": True,
                    "repeat_pillar": pillar,
                    "repeat_rule_ids": rule_ids,
                    "score_bonus": bonus,
                    "note": "同一宫位被大运/流年重复引动；分数只代表关注度，不代表吉凶。",
                }
        return triggers

    def _top_domains(self, triggers: list[dict[str, Any]]) -> list[str]:
        scores: dict[str, int] = {}
        for trigger in triggers:
            for domain in trigger.get("possible_domains", []):
                scores[domain] = scores.get(domain, 0) + int(trigger.get("trigger_score", 0))
        return [name for name, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:5]]

    def _monthly_trigger(self, rule_id: str, month_branch: str, matched: dict[str, Any]) -> dict[str, Any]:
        rule = self.monthly_rules[rule_id]
        return {
            "rule_id": rule_id,
            "status": rule.get("status", "active_rule"),
            "triggered": True,
            "trigger_score": rule.get("trigger_score", 0),
            "month_branch": month_branch,
            "affected_palace": rule.get("affected_palace", []),
            "possible_domains": rule.get("possible_domains", []),
            "interpretation": rule.get("interpretation", ""),
            "matched": matched,
            "evidence": rule.get("evidence", []),
            "uncertainty": rule.get("uncertainty", ""),
            "output_policy": rule.get("output_policy", {}),
        }

    def _annual_activated_branches(self, annual: dict[str, Any], pillars: dict[str, str]) -> list[dict[str, Any]]:
        activated = []
        for trigger in annual.get("triggers", []):
            pillar = trigger.get("matched", {}).get("pillar")
            if pillar and pillar in pillars:
                activated.append({"pillar": pillar, "branch": branch(pillars[pillar]), "rule_id": trigger.get("rule_id")})
        return activated

    def _monthly_fuyin_fanyin(self, month_branch: str, pillars: dict[str, str]) -> list[dict[str, Any]]:
        triggers = []
        for pillar in ("日柱", "月柱"):
            original_branch = branch(pillars.get(pillar, ""))
            if not original_branch:
                continue
            if month_branch == original_branch:
                triggers.append(self._monthly_trigger(
                    "liuyue_fuyin_original_day_or_month_branch_v1",
                    month_branch,
                    {"pillar": pillar, "branch": original_branch, "downgrade": True},
                ))
            if (month_branch, original_branch) in CHONG:
                triggers.append(self._monthly_trigger(
                    "liuyue_fanyin_original_day_or_month_branch_v1",
                    month_branch,
                    {"pillar": pillar, "branch": original_branch, "downgrade": True},
                ))
        return triggers

    def _monthly_chong_activated(self, month_branch: str, activated: list[dict[str, Any]]) -> list[dict[str, Any]]:
        triggers = []
        for item in activated:
            if (month_branch, item["branch"]) in CHONG:
                triggers.append(self._monthly_trigger(
                    "liuyue_branch_chong_year_activated_key_branch_v1",
                    month_branch,
                    item,
                ))
        return triggers

    def _merge_monthly_repeat_triggers(self, triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        index_by_key: dict[tuple[str, str, str, str], int] = {}
        bonus = int(self.rule_set.get("score_strategy", {}).get("same_palace_repeat_bonus", 0))
        for trigger in triggers:
            matched = trigger.get("matched", {}) if isinstance(trigger.get("matched"), dict) else {}
            key = (
                str(trigger.get("rule_id", "")),
                str(trigger.get("month_branch", "")),
                str(matched.get("pillar", "")),
                str(matched.get("branch", "")),
            )
            if not key[0] or not key[2] or not key[3] or key not in index_by_key:
                index_by_key[key] = len(merged)
                merged.append(trigger)
                continue

            existing = merged[index_by_key[key]]
            existing_matched = existing.setdefault("matched", {})
            upper_rule_ids = existing_matched.setdefault("upper_rule_ids", [])
            existing_upper = existing_matched.get("rule_id")
            new_upper = matched.get("rule_id")
            for rule_id in (existing_upper, new_upper):
                if rule_id and rule_id not in upper_rule_ids:
                    upper_rule_ids.append(rule_id)
            if upper_rule_ids and "upper_rule_id" not in existing_matched:
                existing_matched["upper_rule_id"] = upper_rule_ids[0]
            if "trigger_score_base" not in existing:
                existing["trigger_score_base"] = int(existing.get("trigger_score", 0))
                existing["trigger_score"] = int(existing.get("trigger_score", 0)) + bonus
            existing["repeat_context"] = {
                "same_palace_repeat": True,
                "repeat_pillar": matched.get("pillar"),
                "repeat_rule_ids": upper_rule_ids,
                "score_bonus": bonus,
                "note": "同一宫位被上层岁运重复引动；分数只代表关注度，不代表吉凶。",
            }
        return merged

    def _monthly_complete_sets(
        self,
        month_branch: str,
        context_branches: list[str],
        original_branches: list[str],
    ) -> list[dict[str, Any]]:
        triggers = []
        present = set(context_branches)
        original = set(original_branches)
        for group_name, groups in (("三合", SANHE_SETS), ("三会", SANHUI_SETS)):
            for group in groups:
                if month_branch in group and len((group - {month_branch}) & present) >= 2:
                    touches_original = bool(group & original)
                    triggers.append(self._monthly_trigger(
                        "liuyue_complete_sanhe_sanhui_from_original_dayun_liunian_v1",
                        month_branch,
                        {"combination": group_name, "branches": sorted(group), "downgrade": not touches_original},
                    ))
        return triggers


def ganzhi_year(year: int) -> str:
    index = (year - 4) % 60
    return STEMS[index % 10] + BRANCHES[index % 12]


def month_ganzhi(bazi_year: int, month_index: int) -> str:
    """Return the month pillar for month_index 0=寅, 11=丑."""

    year_stem_index = (bazi_year - 4) % 10
    yin_start = (year_stem_index % 5) * 2 + 2
    return STEMS[(yin_start + month_index) % 10] + MONTH_BRANCHES[month_index]


def stem(ganzhi: str) -> str:
    return ganzhi[0] if ganzhi else ""


def branch(ganzhi: str) -> str:
    return ganzhi[1] if len(ganzhi) > 1 else ""


def is_tian_ke_di_chong(left: str, right: str) -> bool:
    return (stem(left), stem(right)) in STEM_KE and (branch(left), branch(right)) in CHONG

