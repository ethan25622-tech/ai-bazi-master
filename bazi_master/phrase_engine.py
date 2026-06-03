"""Select conservative modern phrases from the phrase library."""

from __future__ import annotations

from typing import Any

from .knowledge_base import load_phrase_library


SENSITIVE_DOMAINS = ("健康", "婚恋", "财运", "风险", "大运流年")
GUARDED_DOMAINS = {"wealth", "marriage", "health", "luck_cycle"}
MEDICINE_PREFIX = "medicine_type_"


class PhraseEngine:
    """A v1 selector using domain, confidence, and sensitivity gates.

    Machine-condition evaluation is intentionally conservative for v1.  The
    engine checks required evidence domains and confidence, then chooses a
    guarded/fallback expression for sensitive topics.
    """

    def __init__(self) -> None:
        self.library = load_phrase_library()
        self.phrases = self.library.get("phrases", [])

    def select(
        self,
        *,
        domain: str,
        assessments: dict[str, Any],
        confidence: float,
        guarded: bool = False,
    ) -> list[dict[str, Any]]:
        signals = self._collect_rule_signals(assessments)
        candidates = [
            phrase
            for phrase in self.phrases
            if self._domain_matches(domain, phrase) or self._rule_matches(phrase, signals["rule_ids"])
        ]
        selected = []
        if signals["blocked_guards"]:
            selected.append(self._blocked_selection(signals["blocked_guards"][0]))
        for phrase in candidates:
            required = float(phrase.get("required_confidence", 0.6))
            has_evidence = self._has_evidence(phrase, assessments)
            matched_rules = sorted(set(phrase.get("rule_bindings", [])) & signals["rule_ids"])
            has_rule_match = bool(matched_rules)
            guard = self._guard_for_rules(matched_rules, signals)
            is_medicine = any(rule_id.startswith(MEDICINE_PREFIX) for rule_id in matched_rules)
            manual_review = bool(signals["manual_review_required"] and has_rule_match)
            domain_guarded = guarded or domain in GUARDED_DOMAINS
            direct_allowed = guard.get("direct_expression_allowed") is not False
            output_allowed = guard.get("output_allowed") is not False
            use_fallback = (
                confidence < required
                or phrase.get("status") == "guarded_phrase"
                or domain_guarded
                or manual_review
                or guard.get("risk_guard_required")
                or not direct_allowed
                or not output_allowed
            )
            if not has_evidence and not has_rule_match and confidence < required:
                continue
            if output_allowed:
                text = phrase.get("fallback_phrase") if use_fallback else phrase.get("conservative_expression")
                text = self._with_safe_wording(text, guard.get("safe_wording"))
            else:
                text = guard.get("safe_wording") or "该触发目前只作为内部筛选信号，不输出具体事件判断。"
            forbidden_claims = self._merge_forbidden(
                phrase.get("forbidden_claims", []),
                guard.get("forbidden_assertions", []),
            )
            selected.append({
                "phrase_id": phrase["phrase_id"],
                "status": phrase.get("status"),
                "sensitivity": phrase.get("sensitivity"),
                "confidence_required": required,
                "used_fallback": use_fallback,
                "text": self._with_review_guard(text, manual_review, is_medicine),
                "direct_expression": None if use_fallback or is_medicine or not direct_allowed else phrase.get("direct_expression"),
                "forbidden_claims": forbidden_claims,
                "evidence_keys": phrase.get("evidence_keys", []),
                "matched_rule_ids": matched_rules,
                "executable_notes": [
                    note for note in signals["notes"] if not matched_rules or self._note_applies(note, matched_rules)
                ][:5],
                "manual_review_required": manual_review,
                "risk_guard_required": bool(guard.get("risk_guard_required")),
                "risk_level": guard.get("risk_level"),
                "output_allowed": output_allowed,
                "direct_expression_allowed": direct_allowed,
            })
        selected.sort(key=lambda item: (not item["matched_rule_ids"], item["used_fallback"]))
        return selected[:3]

    def _domain_matches(self, domain: str, phrase: dict[str, Any]) -> bool:
        phrase_domain = str(phrase.get("domain", ""))
        aliases = {
            "career": "事业",
            "wealth": "财",
            "marriage": "婚恋",
            "health": "健康",
            "luck_cycle": "大运流年",
            "pattern": "",
            "strength": "",
            "overview": "",
        }
        needle = aliases.get(domain, domain)
        return not needle or needle in phrase_domain

    def _rule_matches(self, phrase: dict[str, Any], rule_ids: set[str]) -> bool:
        bindings = set(phrase.get("rule_bindings", []))
        return bool(bindings & rule_ids)

    def _has_evidence(self, phrase: dict[str, Any], assessments: dict[str, Any]) -> bool:
        keys = phrase.get("evidence_keys", [])
        if not keys:
            return True
        normalized = set(assessments)
        aliases = {
            "yong_shen": "yong_shen",
            "strength": "strength",
            "pattern": "pattern",
            "chong_he": "chong_he",
            "luck_cycle": "luck_cycle",
            "liuqin": "liuqin",
            "health_mapping": "health",
        }
        return any(aliases.get(key, key) in normalized for key in keys)

    def _collect_rule_signals(self, assessments: dict[str, Any]) -> dict[str, Any]:
        rule_ids: set[str] = set()
        notes: list[str] = []
        guards: dict[str, list[dict[str, Any]]] = {}
        blocked_guards: list[dict[str, Any]] = []
        manual_review_required = False

        for item in assessments.values():
            if not isinstance(item, dict):
                continue
            rule_ids.update(str(rule_id) for rule_id in item.get("executable_rule_ids", []) if rule_id)
            notes.extend(str(note) for note in item.get("executable_notes", []) if note)
            manual_review_required = manual_review_required or bool(item.get("executable_manual_review_required"))

        luck_cycle = assessments.get("luck_cycle", {})
        if isinstance(luck_cycle, dict):
            annual = luck_cycle.get("annual", {})
            if isinstance(annual, dict):
                for trigger in annual.get("triggers", []):
                    if isinstance(trigger, dict) and trigger.get("rule_id"):
                        rule_id = str(trigger["rule_id"])
                        rule_ids.add(rule_id)
                        notes.append(str(trigger.get("summary", "")))
                        self._add_guard(rule_id, trigger, guards, blocked_guards)
                        manual_review_required = manual_review_required or trigger.get("status") in {
                            "candidate_rule",
                            "manual_review",
                            "guard_rule",
                        } or bool(trigger.get("risk_guard_required"))
            monthly = luck_cycle.get("monthly_windows", {})
            if isinstance(monthly, dict):
                for window in monthly.get("windows", []):
                    if not isinstance(window, dict):
                        continue
                    for trigger in window.get("triggered_rules", []):
                        if isinstance(trigger, dict) and trigger.get("rule_id"):
                            rule_id = str(trigger["rule_id"])
                            rule_ids.add(rule_id)
                            notes.append(str(trigger.get("interpretation", "")))
                            self._add_guard(rule_id, trigger, guards, blocked_guards)
                            manual_review_required = manual_review_required or trigger.get("status") in {
                                "candidate_rule",
                                "manual_review",
                                "guard_rule",
                            } or bool(trigger.get("risk_guard_required"))
            daily_filter = luck_cycle.get("daily_filter", {})
            if isinstance(daily_filter, dict):
                guard_summary = daily_filter.get("guard_summary", {})
                if isinstance(guard_summary, dict) and guard_summary.get("output_allowed") is False:
                    blocked_guard = {
                        "rule_id": "luck_guard_001",
                        "risk_guard_required": True,
                        "risk_level": guard_summary.get("risk_level", "blocked"),
                        "safe_wording": daily_filter.get("safe_wording"),
                        "forbidden_assertions": daily_filter.get("output_policy", {}).get("forbidden", []),
                        "output_allowed": False,
                        "direct_expression_allowed": False,
                    }
                    rule_ids.add("luck_guard_001")
                    guards.setdefault("luck_guard_001", []).append(blocked_guard)
                    blocked_guards.append(blocked_guard)
                    manual_review_required = True
                for candidate in daily_filter.get("date_candidates", []):
                    if isinstance(candidate, dict) and candidate.get("rule_id"):
                        rule_id = str(candidate["rule_id"])
                        rule_ids.add(rule_id)
                        notes.append(str(candidate.get("date_window_type", "")))
                        self._add_guard(rule_id, candidate, guards, blocked_guards)
                        manual_review_required = manual_review_required or bool(candidate.get("risk_guard_required"))

        return {
            "rule_ids": rule_ids,
            "notes": [note for note in notes if note],
            "guards": guards,
            "blocked_guards": blocked_guards,
            "manual_review_required": manual_review_required,
        }

    def _with_review_guard(self, text: str | None, manual_review: bool, is_medicine: bool) -> str:
        base = text or ""
        if not manual_review and not is_medicine:
            return base
        prefix = "可作为复核点，提示某种结构倾向；仍需结合全局，不等于确定事件。"
        if base.startswith(prefix):
            return base
        return f"{prefix}{base}"

    def _note_applies(self, note: str, matched_rules: list[str]) -> bool:
        if not matched_rules:
            return True
        if any(rule_id.startswith(MEDICINE_PREFIX) for rule_id in matched_rules):
            return "候选" in note or "复核" in note or "通关" in note or "调候" in note
        return True

    def _add_guard(
        self,
        rule_id: str,
        trigger: dict[str, Any],
        guards: dict[str, list[dict[str, Any]]],
        blocked_guards: list[dict[str, Any]],
    ) -> None:
        guard = {
            "rule_id": rule_id,
            "risk_guard_required": bool(trigger.get("risk_guard_required")),
            "risk_level": trigger.get("risk_level"),
            "safe_wording": trigger.get("safe_wording"),
            "forbidden_assertions": trigger.get("forbidden_assertions", []),
            "output_allowed": trigger.get("output_allowed", True),
            "direct_expression_allowed": trigger.get("direct_expression_allowed", True),
        }
        if (
            guard["risk_guard_required"]
            or guard["output_allowed"] is False
            or guard["direct_expression_allowed"] is False
            or guard["safe_wording"]
            or guard["forbidden_assertions"]
        ):
            guards.setdefault(rule_id, []).append(guard)
        if guard["output_allowed"] is False:
            blocked_guards.append(guard)

    def _guard_for_rules(self, matched_rules: list[str], signals: dict[str, Any]) -> dict[str, Any]:
        guards = [
            guard
            for rule_id in matched_rules
            for guard in signals.get("guards", {}).get(rule_id, [])
        ]
        if not guards:
            return {}
        safe_wording = next((guard.get("safe_wording") for guard in guards if guard.get("safe_wording")), None)
        risk_levels = [str(guard.get("risk_level", "")) for guard in guards]
        risk_rank = {"": 0, "low": 1, "medium": 2, "high": 3, "blocked": 4}
        risk_level = max(risk_levels, key=lambda item: risk_rank.get(item, 0), default=None)
        return {
            "risk_guard_required": any(guard.get("risk_guard_required") for guard in guards),
            "risk_level": risk_level,
            "safe_wording": safe_wording,
            "forbidden_assertions": self._merge_forbidden(
                *[guard.get("forbidden_assertions", []) for guard in guards]
            ),
            "output_allowed": all(guard.get("output_allowed", True) is not False for guard in guards),
            "direct_expression_allowed": all(
                guard.get("direct_expression_allowed", True) is not False for guard in guards
            ),
        }

    def _with_safe_wording(self, text: str | None, safe_wording: str | None) -> str:
        base = text or ""
        if not safe_wording:
            return base
        if base.startswith(safe_wording):
            return base
        return f"{safe_wording}{base}"

    def _merge_forbidden(self, *groups: list[str]) -> list[str]:
        merged: list[str] = []
        for group in groups:
            for item in group or []:
                text = str(item)
                if text and text not in merged:
                    merged.append(text)
        return merged

    def _blocked_selection(self, guard: dict[str, Any]) -> dict[str, Any]:
        return {
            "phrase_id": "guard_blocked_output",
            "status": "guarded_phrase",
            "sensitivity": "high",
            "confidence_required": 1.0,
            "used_fallback": True,
            "text": guard.get("safe_wording") or "该触发目前只作为内部筛选信号，不输出具体事件判断。",
            "direct_expression": None,
            "forbidden_claims": guard.get("forbidden_assertions", []),
            "evidence_keys": ["luck_cycle"],
            "matched_rule_ids": [guard.get("rule_id")] if guard.get("rule_id") else [],
            "executable_notes": [],
            "manual_review_required": True,
            "risk_guard_required": True,
            "risk_level": guard.get("risk_level", "blocked"),
            "output_allowed": False,
            "direct_expression_allowed": False,
        }
