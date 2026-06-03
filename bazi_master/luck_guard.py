"""Structured guard fields for luck-cycle timing outputs.

The guard layer does not judge events.  It only marks how cautiously a
luck-cycle trigger may be rendered by later output layers.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


HIGH_GUARD_RULE_IDS = {
    "luck_003",
    "luck_004",
    "luck_005",
    "luck_006",
    "year_001",
    "year_002",
    "year_003",
    "year_004",
    "year_005",
    "liuyue_branch_chong_year_activated_key_branch_v1",
    "liuyue_fuyin_original_day_or_month_branch_v1",
    "liuyue_fanyin_original_day_or_month_branch_v1",
    "liuyue_window_only_no_major_event_judgment_v1",
}

LOW_OR_MEDIUM_GUARD_RULE_IDS = {
    "luck_007",
    "luck_008",
    "year_006",
    "year_007",
    "year_008",
    "liuyue_complete_sanhe_sanhui_from_original_dayun_liunian_v1",
    "liuyue_stem_reveals_dayun_liunian_triggered_ten_god_v1",
}

HIGH_RISK_TERMS = (
    "死亡",
    "重病",
    "疾病",
    "离婚",
    "分手",
    "破产",
    "破财",
    "事故",
    "诉讼",
    "官非",
    "投资损失",
    "失业",
    "离职",
    "出灾",
)

DEFAULT_FORBIDDEN_ASSERTIONS = [
    "一定离婚",
    "一定分手",
    "一定重病",
    "一定死亡",
    "一定破产",
    "一定破财",
    "一定出事故",
    "一定诉讼",
    "一定投资损失",
    "一定失业",
    "一定离职",
    "必然发生大事",
]

GENERAL_SAFE_WORDING = "该信号只表示相关主题关注度提高，需结合现实背景观察，不构成确定事件判断。"
MONTH_SAFE_WORDING = "该判断仅作为月份窗口，不单独构成大事判断，也不直接判断吉凶。"
OBSERVATION_MONTH_WORDING = "该流月触发仅作为观察月份处理，提示短期主题更容易被看见，不单独构成事件判断。"
DAILY_BLOCKED_WORDING = "流日只能作为上层触发后的日期筛选，不能每日泛断。"


def guard_annual_triggers(triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach guard fields to annual and dayun triggers."""

    return [_guard_trigger(trigger, scope="annual") for trigger in triggers]


def guard_monthly_windows(
    windows: list[dict[str, Any]],
    annual: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Attach guard fields to every monthly window trigger."""

    guarded_windows = []
    has_upper_trigger = bool((annual or {}).get("triggers"))
    for window in windows:
        guarded_window = deepcopy(window)
        guarded_rules = []
        for trigger in guarded_window.get("triggered_rules", []):
            guarded_rules.append(
                _guard_trigger(
                    trigger,
                    scope="monthly",
                    force_guard=True,
                    force_direct_block=True,
                    single_layer=not has_upper_trigger,
                )
            )
        guarded_window["triggered_rules"] = guarded_rules
        guarded_window["guard_summary"] = _guard_summary(guarded_rules)
        guarded_windows.append(guarded_window)
    return guarded_windows


def guard_daily_candidates(
    candidates: list[dict[str, Any]],
    annual: dict[str, Any] | None = None,
    monthly: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Guard future daily candidates without creating a daily engine.

    If no upper annual/monthly trigger exists, daily output is blocked.  This
    keeps daily timing as a future date-filtering surface only.
    """

    has_upper_trigger = _has_upper_trigger(annual, monthly)
    if not has_upper_trigger and not candidates:
        return [
            {
                "rule_id": "luck_guard_001",
                "scope": "daily_filter",
                "risk_guard_required": True,
                "risk_level": "blocked",
                "safe_wording": DAILY_BLOCKED_WORDING,
                "forbidden_assertions": ["每日泛断", "单凭流日输出重大判断", *DEFAULT_FORBIDDEN_ASSERTIONS],
                "output_allowed": False,
                "direct_expression_allowed": False,
            }
        ]

    guarded_candidates = []
    for candidate in candidates:
        guarded_candidates.append(
            _guard_trigger(
                candidate,
                scope="daily",
                force_guard=True,
                force_direct_block=True,
                block_output=not has_upper_trigger,
            )
        )
    return guarded_candidates


def build_guard_summary(triggers: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a compact summary for an already guarded trigger list."""

    return _guard_summary(triggers)


def _guard_trigger(
    trigger: dict[str, Any],
    *,
    scope: str,
    force_guard: bool = False,
    force_direct_block: bool = False,
    single_layer: bool = False,
    block_output: bool = False,
) -> dict[str, Any]:
    guarded = deepcopy(trigger)
    rule_id = str(guarded.get("rule_id", ""))
    output_policy = guarded.get("output_policy", {})
    existing_forbidden = _policy_forbidden(output_policy)
    matched = guarded.get("matched", {})
    downgraded = bool(isinstance(matched, dict) and matched.get("downgrade"))

    risk_required = (
        force_guard
        or rule_id in HIGH_GUARD_RULE_IDS
        or rule_id in LOW_OR_MEDIUM_GUARD_RULE_IDS
        or _contains_high_risk_text(guarded)
        or bool(existing_forbidden)
        or single_layer
        or downgraded
        or block_output
    )
    risk_level = _risk_level(rule_id, scope, downgraded, single_layer, block_output, guarded)
    safe_wording = _safe_wording(scope, downgraded, block_output, risk_level)

    guarded["risk_guard_required"] = risk_required
    guarded["risk_level"] = risk_level
    guarded["safe_wording"] = safe_wording
    guarded["forbidden_assertions"] = _forbidden_assertions(existing_forbidden, block_output)
    guarded["output_allowed"] = not block_output
    guarded["direct_expression_allowed"] = False if (
        risk_required or force_direct_block or scope in {"monthly", "daily"}
    ) else True
    return guarded


def _risk_level(
    rule_id: str,
    scope: str,
    downgraded: bool,
    single_layer: bool,
    block_output: bool,
    trigger: dict[str, Any],
) -> str:
    if block_output:
        return "blocked"
    if rule_id in HIGH_GUARD_RULE_IDS:
        return "medium" if downgraded and scope == "monthly" else "high"
    if rule_id == "year_006":
        return "medium"
    if rule_id in LOW_OR_MEDIUM_GUARD_RULE_IDS:
        return "medium"
    if single_layer or downgraded:
        return "medium"
    if _contains_high_risk_text(trigger):
        return "high"
    return "low"


def _safe_wording(scope: str, downgraded: bool, block_output: bool, risk_level: str) -> str:
    if block_output:
        return DAILY_BLOCKED_WORDING
    if scope == "monthly":
        if downgraded:
            return OBSERVATION_MONTH_WORDING
        return MONTH_SAFE_WORDING
    if scope == "daily":
        return DAILY_BLOCKED_WORDING if risk_level == "blocked" else (
            "该日期仅作为上层岁运或流月窗口内的候选筛选，不单独构成事件判断。"
        )
    return GENERAL_SAFE_WORDING


def _policy_forbidden(output_policy: Any) -> list[str]:
    if not isinstance(output_policy, dict):
        return []
    forbidden = output_policy.get("forbidden", [])
    if isinstance(forbidden, str):
        return [forbidden]
    if isinstance(forbidden, list):
        return [str(item) for item in forbidden if item]
    return []


def _forbidden_assertions(existing: list[str], block_output: bool) -> list[str]:
    assertions = [*existing, *DEFAULT_FORBIDDEN_ASSERTIONS]
    if block_output:
        assertions = ["每日泛断", "单凭流日输出重大判断", *assertions]
    deduped = []
    for item in assertions:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _contains_high_risk_text(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_high_risk_text(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_high_risk_text(item) for item in value)
    text = str(value)
    return any(term in text for term in HIGH_RISK_TERMS)


def _has_upper_trigger(annual: dict[str, Any] | None, monthly: dict[str, Any] | None) -> bool:
    if isinstance(annual, dict) and annual.get("triggers"):
        return True
    if isinstance(monthly, dict):
        return any(window.get("triggered_rules") for window in monthly.get("windows", []) if isinstance(window, dict))
    return False


def _guard_summary(triggers: list[dict[str, Any]]) -> dict[str, Any]:
    guarded = [trigger for trigger in triggers if trigger.get("risk_guard_required")]
    blocked = [trigger for trigger in triggers if trigger.get("output_allowed") is False]
    high = [trigger for trigger in triggers if trigger.get("risk_level") == "high"]
    return {
        "risk_guarded_count": len(guarded),
        "high_risk_guarded_count": len(high),
        "blocked_count": len(blocked),
        "direct_expression_allowed": not guarded,
        "output_allowed": not blocked,
    }
