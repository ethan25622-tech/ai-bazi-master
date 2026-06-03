"""Conservative daily date-candidate filter for upper luck-cycle triggers.

This module does not render daily predictions.  It only narrows an already
triggered annual/monthly window into a small list of guarded date candidates.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .luck_cycle_engine import BRANCHES, CHONG, STEMS, branch
from .luck_guard import build_guard_summary, guard_daily_candidates


JIE_LONGITUDES = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]


DEFAULT_OUTPUT_POLICY = {
    "role": "仅作为上层岁运/月令窗口内的日期候选筛选",
    "forbidden": [
        "每日泛断",
        "某日一定发生某事",
        "死亡、疾病、破产、离婚、事故等确定判断",
        "投资买卖建议",
        "吉日、凶日、灾日标签",
    ],
}
SAFE_WORDING = "以下日期只表示上层触发窗口内关注度较高，不构成事件判断。"
BLOCKED_WORDING = "流日只能作为上层触发后的日期筛选，不能每日泛断。"
ANNUAL_ONLY_WORDING = "已有年度触发，但目标流月未形成窗口；第一阶段不单独筛选流日候选。"
INVALID_MONTH_WORDING = "target_month must be a flow-month index from 1 to 12; daily_filter is blocked for invalid month input."


class DailyFilterEngine:
    """Build guarded date candidates inside an existing upper trigger window."""

    def evaluate(
        self,
        analysis: dict[str, Any],
        target_year: int,
        target_month: int,
        annual: dict[str, Any] | None = None,
        monthly_windows: dict[str, Any] | None = None,
        max_candidates: int = 5,
        filter_policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        policy = {
            "require_monthly_window": True,
            "allow_annual_only_downgrade": True,
            "block_without_upper_trigger": True,
            "candidate_scope": "month_window_only",
        }
        if filter_policy:
            policy.update(filter_policy)
        max_candidates = max(0, min(int(max_candidates), 8))
        if target_month < 1 or target_month > 12:
            blocked = guard_daily_candidates([], annual={}, monthly={})
            guard_summary = build_guard_summary(blocked)
            guard_summary["invalid_target_month"] = True
            return self._result(
                target_year,
                target_month,
                max_candidates,
                [],
                guard_summary,
                output_allowed=False,
                safe_wording=INVALID_MONTH_WORDING,
            )

        annual = annual or {}
        monthly_windows = monthly_windows or {}
        has_annual = bool(annual.get("triggers"))
        target_window = self._target_window(monthly_windows, target_month)
        has_month_window = bool(target_window)

        if not has_annual and not has_month_window:
            blocked = guard_daily_candidates([], annual={}, monthly={})
            return self._result(
                target_year,
                target_month,
                max_candidates,
                [],
                build_guard_summary(blocked),
                output_allowed=False,
                safe_wording=BLOCKED_WORDING,
            )

        if has_annual and not has_month_window and policy["allow_annual_only_downgrade"]:
            return self._result(
                target_year,
                target_month,
                max_candidates,
                [],
                {
                    "risk_guarded_count": 0,
                    "high_risk_guarded_count": 0,
                    "blocked_count": 0,
                    "direct_expression_allowed": False,
                    "output_allowed": True,
                    "downgrade": True,
                },
                output_allowed=True,
                safe_wording=ANNUAL_ONLY_WORDING,
            )

        raw_candidates = self._build_monthly_candidates(
            analysis,
            target_year,
            target_month,
            target_window,
            max_candidates,
        )
        guarded_candidates = guard_daily_candidates(
            raw_candidates[:max_candidates],
            annual=annual,
            monthly={"windows": [target_window] if target_window else []},
        )
        return self._result(
            target_year,
            target_month,
            max_candidates,
            guarded_candidates[:max_candidates],
            build_guard_summary(guarded_candidates),
            output_allowed=True,
            safe_wording=SAFE_WORDING,
        )

    def _build_monthly_candidates(
        self,
        analysis: dict[str, Any],
        target_year: int,
        target_month: int,
        target_window: dict[str, Any] | None,
        max_candidates: int,
    ) -> list[dict[str, Any]]:
        if not target_window:
            return []
        candidates = []
        seen_dates: set[str] = set()
        for trigger in target_window.get("triggered_rules", []):
            matched = trigger.get("matched", {}) if isinstance(trigger.get("matched"), dict) else {}
            matched_branch = matched.get("branch")
            rule_id = trigger.get("rule_id", "")
            if matched_branch and rule_id == "liuyue_branch_chong_year_activated_key_branch_v1":
                candidates.extend(
                    self._scan_dates_for_branch_relation(
                        target_year,
                        target_month,
                        matched_branch,
                        relation="chong",
                        rule_id="daily_filter_chong_activated_branch_v1",
                        window=target_window,
                        upper_trigger=trigger,
                        seen_dates=seen_dates,
                        max_needed=max_candidates - len(candidates),
                    )
                )
            if matched_branch and rule_id in {
                "liuyue_fuyin_original_day_or_month_branch_v1",
                "liuyue_fanyin_original_day_or_month_branch_v1",
            }:
                relation = "same" if "fuyin" in rule_id else "chong"
                candidates.extend(
                    self._scan_dates_for_branch_relation(
                        target_year,
                        target_month,
                        matched_branch,
                        relation=relation,
                        rule_id="daily_filter_repeat_month_palace_trigger_v1",
                        window=target_window,
                        upper_trigger=trigger,
                        seen_dates=seen_dates,
                        max_needed=max_candidates - len(candidates),
                    )
                )
            if rule_id == "liuyue_complete_sanhe_sanhui_from_original_dayun_liunian_v1":
                completion_branch = trigger.get("month_branch")
                if completion_branch:
                    candidates.extend(
                        self._scan_dates_for_branch_relation(
                            target_year,
                            target_month,
                            completion_branch,
                            relation="same",
                            rule_id="daily_filter_complete_existing_combination_v1",
                            window=target_window,
                            upper_trigger=trigger,
                            seen_dates=seen_dates,
                            max_needed=max_candidates - len(candidates),
                            extra_matched={
                                "combination": matched.get("combination"),
                                "branches": matched.get("branches", []),
                            },
                        )
                    )
            if len(candidates) >= max_candidates:
                break
        return candidates[:max_candidates]

    def _scan_dates_for_branch_relation(
        self,
        target_year: int,
        target_month: int,
        target_branch: str,
        *,
        relation: str,
        rule_id: str,
        window: dict[str, Any],
        upper_trigger: dict[str, Any],
        seen_dates: set[str],
        max_needed: int,
        extra_matched: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if max_needed <= 0:
            return []
        matched = []
        for current in self._flow_month_dates(target_year, target_month):
            day_pillar = day_ganzhi(current)
            day_branch = branch(day_pillar)
            relation_matches = (
                day_branch == target_branch if relation == "same" else (day_branch, target_branch) in CHONG
            )
            if not relation_matches:
                continue
            date_text = current.isoformat()
            if date_text in seen_dates:
                continue
            seen_dates.add(date_text)
            matched_payload = {
                "upper_rule_id": upper_trigger.get("rule_id"),
                "upper_window_ganzhi": window.get("ganzhi"),
                "pillar": (upper_trigger.get("matched") or {}).get("pillar"),
                "branch": target_branch,
                "relation": relation,
            }
            if extra_matched:
                matched_payload.update(extra_matched)
            matched.append({
                "date": date_text,
                "day_pillar": day_pillar,
                "date_window_type": rule_id.replace("daily_filter_", "").replace("_v1", ""),
                "rule_id": rule_id,
                "trigger_score": 35,
                "matched": matched_payload,
                "evidence": [
                    "上层 annual/monthly 已形成触发窗口",
                    "流日仅作为该窗口内的日期候选筛选",
                ],
                "output_policy": DEFAULT_OUTPUT_POLICY,
            })
            if len(matched) >= max_needed:
                break
        return matched

    def _target_window(self, monthly_windows: dict[str, Any], target_month: int) -> dict[str, Any] | None:
        for window in monthly_windows.get("windows", []):
            if isinstance(window, dict) and int(window.get("month_index", 0)) == int(target_month):
                return window
        return None

    def _flow_month_dates(self, target_year: int, target_month: int) -> list[date]:
        solar_term_dates = self._solar_term_month_dates(target_year, target_month)
        if solar_term_dates:
            return solar_term_dates
        return self._approx_month_dates(target_year, target_month)

    def _solar_term_month_dates(self, target_year: int, target_month: int) -> list[date]:
        try:
            from .bridge import ensure_engine_path
            from .calendar_terms import apply_to_module

            ensure_engine_path()
            import bazi_engine  # type: ignore

            apply_to_module(bazi_engine)
            start_lon = JIE_LONGITUDES[target_month - 1]
            end_lon = JIE_LONGITUDES[target_month % 12]
            start_year = target_year + 1 if target_month == 12 else target_year
            end_year = target_year + 1 if target_month >= 11 else target_year
            start_dt = _jdn_to_datetime(bazi_engine._get_jieqi_jdn(start_year, start_lon))  # type: ignore[attr-defined]
            end_dt = _jdn_to_datetime(bazi_engine._get_jieqi_jdn(end_year, end_lon))  # type: ignore[attr-defined]
        except Exception:
            return []

        # Date-level filtering cannot express a partial solar-term boundary day,
        # so v1 keeps only full dates strictly inside the solar month.
        start = start_dt.date() + timedelta(days=1)
        end = end_dt.date()
        if end <= start:
            return []
        days = []
        current = start
        while current < end:
            days.append(current)
            current += timedelta(days=1)
        return days

    def _approx_month_dates(self, target_year: int, target_month: int) -> list[date]:
        # Fallback only; normal v1 filtering uses solar-term flow-month dates.
        if target_month <= 10:
            month = target_month + 1
            year = target_year
        elif target_month == 11:
            month = 12
            year = target_year
        else:
            month = 1
            year = target_year + 1
        start = date(year, month, 1)
        days = []
        current = start
        while current.month == month:
            days.append(current)
            current += timedelta(days=1)
        return days

    def _result(
        self,
        target_year: int,
        target_month: int,
        max_candidates: int,
        candidates: list[dict[str, Any]],
        guard_summary: dict[str, Any],
        *,
        output_allowed: bool,
        safe_wording: str,
    ) -> dict[str, Any]:
        guard_summary = dict(guard_summary)
        guard_summary.setdefault("output_allowed", output_allowed)
        guard_summary.setdefault("direct_expression_allowed", False)
        date_range = self._candidate_date_range(target_year, target_month)
        return {
            "daily_filter": {
                "target_year": target_year,
                "target_month": target_month,
                "level": "date_filter",
                "scope": "upper_trigger_date_candidates",
                "date_range_policy": "solar_term_full_dates_excluding_boundary_days",
                "candidate_date_range": date_range,
                "output_policy": DEFAULT_OUTPUT_POLICY,
                "safe_wording": safe_wording,
                "date_candidates": candidates,
                "guard_summary": guard_summary,
                "max_candidates": max_candidates,
            }
        }

    def _candidate_date_range(self, target_year: int, target_month: int) -> dict[str, Any]:
        if target_month < 1 or target_month > 12:
            return {"valid": False, "reason": "invalid_target_month"}
        days = self._flow_month_dates(target_year, target_month)
        if not days:
            return {"valid": False, "reason": "no_candidate_dates"}
        return {
            "valid": True,
            "start_date": days[0].isoformat(),
            "end_date": days[-1].isoformat(),
            "included_day_count": len(days),
        }


def day_ganzhi(day: date) -> str:
    """Return sexagenary day pillar using a validated project anchor.

    The calendar validation corpus includes 2024-02-05 as 己亥.  v1 only uses
    this for candidate filtering, not standalone day judgment.
    """

    anchor = date(2024, 2, 5)
    anchor_index = sexagenary_index("己亥")
    index = (anchor_index + (day - anchor).days) % 60
    return STEMS[index % 10] + BRANCHES[index % 12]


def sexagenary_index(pillar: str) -> int:
    stem_index = STEMS.index(pillar[0])
    branch_index = BRANCHES.index(pillar[1])
    for index in range(60):
        if index % 10 == stem_index and index % 12 == branch_index:
            return index
    raise ValueError(f"Invalid pillar: {pillar}")


def _jdn_to_datetime(jdn: float) -> datetime:
    """Convert the engine's local JDN scale back to a naive local datetime."""

    value = jdn + 0.5
    z = int(value)
    f = value - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day_value = b - d - int(30.6001 * e) + f
    day = int(day_value)
    fraction = day_value - day
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    seconds = int(round(fraction * 86400))
    if seconds >= 86400:
        seconds -= 86400
        base = date(year, month, day) + timedelta(days=1)
        year, month, day = base.year, base.month, base.day
    hour = seconds // 3600
    minute = (seconds % 3600) // 60
    second = seconds % 60
    return datetime(year, month, day, hour, minute, second)
