"""Structured rule layer built on top of the existing narrator output."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .knowledge_base import index_rules, load_core_rules, load_luck_rules, load_monthly_rules
from .schema import confidence_from_assessment, evidence_item, get_path


CORE_DOMAINS = {
    "pattern",
    "strength",
    "tiaohou",
    "yong_shen",
    "chong_he",
    "liuqin",
    "career",
    "wealth",
    "marriage",
    "health",
    "luck_cycle",
}

DOMAIN_RULE_IDS = {
    "pattern": "pattern_001",
    "strength": "strength_001",
    "tiaohou": "climate_001",
    "yong_shen": "climate_001",
    "chong_he": "flow_001",
    "liuqin": "liuqin.v1",
    "career": "pattern_001",
    "wealth": "pattern_003",
    "marriage": "liuqin.v1",
    "health": "health.v1",
    "luck_cycle": "luck_cycle.v1",
}

PATTERN_SIGNAL_GODS = {
    "pattern_004": {"正印", "偏印"},
    "pattern_005": {"食神"},
    "pattern_006": {"七杀"},
    "pattern_007": {"伤官"},
}

PATTERN_SIGNAL_NAMES = {
    "pattern_004": "印格",
    "pattern_005": "食神格",
    "pattern_006": "七杀格",
    "pattern_007": "伤官格",
}

STEM_PILLARS = {"年柱", "月柱", "时柱"}

RESOURCE_GODS = {"正印", "偏印"}
PEER_GODS = {"比肩", "劫财", "日主"}
OUTPUT_GODS = {"食神", "伤官"}
WEALTH_GODS = {"正财", "偏财"}
OFFICER_GODS = {"正官", "七杀"}

JIANLU_BRANCH_BY_DAY_MASTER = {
    "甲": "寅",
    "乙": "卯",
    "丙": "巳",
    "丁": "午",
    "戊": "巳",
    "己": "午",
    "庚": "申",
    "辛": "酉",
    "壬": "亥",
    "癸": "子",
}

YANG_BLADE_BRANCH_BY_DAY_MASTER = {
    "甲": "卯",
    "丙": "午",
    "戊": "午",
    "庚": "酉",
    "壬": "子",
}


class RuleEngine:
    """Normalize current rule results into evidence-bearing assessments.

    The class does not invent new Bazi conclusions.  It reads the structured
    result produced by the existing engine and wraps each domain with source,
    confidence, uncertainty, and conversation-ready metadata.
    """

    def __init__(self) -> None:
        self.core_rules = load_core_rules()
        self.luck_rules = load_luck_rules()
        self.monthly_rules = load_monthly_rules()
        self.rule_index = index_rules(self.core_rules, self.luck_rules, self.monthly_rules)

    def evaluate(self, analysis: dict[str, Any], domain: str | None = None) -> dict[str, Any]:
        if domain is not None and domain not in CORE_DOMAINS:
            raise ValueError(f"Unknown domain: {domain}. Expected one of {sorted(CORE_DOMAINS)}")

        selected = [domain] if domain else [
            "pattern",
            "strength",
            "tiaohou",
            "yong_shen",
            "chong_he",
            "liuqin",
            "career",
            "wealth",
            "marriage",
            "health",
            "luck_cycle",
        ]
        return {
            name: self._normalize_assessment(name, getattr(self, f"_eval_{name}")(analysis))
            for name in selected
        }

    def library_summary(self) -> dict[str, Any]:
        statuses: dict[str, int] = {}
        for rule in self.rule_index.values():
            status = str(rule.get("status", "active_rule"))
            statuses[status] = statuses.get(status, 0) + 1
        return {
            "core_rule_count": len(self.core_rules.get("rules", [])),
            "luck_rule_count": len(self.luck_rules.get("rules", [])),
            "monthly_rule_count": len(self.monthly_rules.get("rules", [])),
            "statuses": statuses,
        }

    def _normalize_assessment(self, domain: str, item: dict[str, Any]) -> dict[str, Any]:
        rule_id = item.get("rule_id") or DOMAIN_RULE_IDS.get(domain, f"{domain}.v1")
        rule = self.rule_index.get(rule_id, {})
        status = item.get("status") or rule.get("status", "active_rule")
        confidence = float(item.get("confidence", 0.5))
        triggered = bool(item.get("data")) or confidence >= 0.55
        manual_review = (
            status in {"manual_review", "candidate_rule"}
            or str(rule.get("subjectivity", "")).lower() == "high"
            or bool(item.get("executable_manual_review_required"))
            or confidence < 0.6
        )

        item["rule_id"] = rule_id
        item["status"] = status
        item["triggered"] = triggered
        item["manual_review_required"] = manual_review
        item["uncertainty"] = item.get("uncertainty") or rule.get("uncertainty")
        item["rule_source"] = rule.get("source", item.get("rule_source"))
        return item

    def _eval_pattern(self, analysis: dict[str, Any]) -> dict[str, Any]:
        raw = get_path(analysis, "assessment", "格局成败", default={}) or {}
        status = raw.get("成败状态", "未判定")
        confidence = 0.75 if status in ("成", "败", "救应") else 0.55
        provisional_reasons: list[str] = []
        if raw.get("本气透干") is False:
            provisional_reasons.append("月令本气未透，格局根力需降级看待")
            confidence = min(confidence, 0.68)
        if status not in ("成", "救应"):
            provisional_reasons.append("成败状态未达到稳定成格或救应")
        rule_hits = self._evaluate_pattern_expansion(analysis, raw)
        evidence = [
            evidence_item(
                key="pattern.primary",
                source="子平真诠八格成败救应规则",
                rule=str(raw.get("判定依据", "由月令十神与透干组合判定")),
                matched={
                    "月令": raw.get("月令"),
                    "月令本气": raw.get("月令本气"),
                    "月令十神": raw.get("月令十神"),
                    "本气透干": raw.get("本气透干"),
                    "其他透干十神": raw.get("其他透干十神"),
                },
                confidence=confidence,
                uncertainty=str(raw.get("备注", "格局判断需要与强弱、调候、大运合看。")),
            )
        ]
        evidence.extend(self._evidence_from_pattern_hits(rule_hits))
        data = deepcopy(raw)
        if rule_hits:
            data["B口可执行规则命中"] = rule_hits
        if provisional_reasons:
            data["格局降级原因"] = provisional_reasons
        return {
            "domain": "pattern",
            "summary": f"{raw.get('格局名称', '未知格局')}：{status}",
            "interpretation_policy": "格局只作为分析入口；若存在降级原因或复核信号，不可当作铁定成格。",
            "provisional_reasons": provisional_reasons,
            "data": data,
            "executable_rule_ids": [hit["rule_id"] for hit in rule_hits],
            "executable_notes": [
                note
                for hit in rule_hits
                for note in hit.get("notes", [])
            ],
            "executable_manual_review_required": any(
                hit.get("manual_review_required") for hit in rule_hits
            ),
            "confidence": confidence,
            "evidence": evidence,
        }

    def _evaluate_pattern_expansion(
        self,
        analysis: dict[str, Any],
        pattern_raw: dict[str, Any],
    ) -> list[dict[str, Any]]:
        ten_gods = get_path(analysis, "certain", "十神分布", default=[]) or []
        stem_gods = self._stem_god_counts(ten_gods)
        month_main = self._month_main_god(ten_gods)
        month_hidden = set(self._month_hidden_gods(ten_gods))
        month_branch = self._month_branch(ten_gods)
        day_master = get_path(analysis, "basic_info", "日主")
        current_pattern = str(pattern_raw.get("格局名称", ""))
        hits: list[dict[str, Any]] = []

        for rule_id, gods in PATTERN_SIGNAL_GODS.items():
            month_main_match = month_main in gods
            hidden_with_stem = bool(month_hidden & gods) and any(stem_gods.get(god, 0) for god in gods)
            stem_signal = {god: stem_gods.get(god, 0) for god in gods if stem_gods.get(god, 0)}
            if rule_id == "pattern_005":
                triggered = month_main_match or hidden_with_stem
            else:
                triggered = month_main_match or hidden_with_stem or bool(stem_signal)
            if not triggered:
                continue

            matched = {
                "月令主气十神": month_main,
                "月令藏干十神": sorted(month_hidden),
                "透干十神计数": stem_signal,
                "旧引擎主格": current_pattern,
            }
            status = "候选成立"
            confidence = 0.66 if month_main_match or hidden_with_stem else 0.58
            notes: list[str] = []

            if rule_id == "pattern_006":
                if stem_gods.get("食神", 0):
                    notes.append("食神制杀候选")
                if stem_gods.get("正印", 0) or stem_gods.get("偏印", 0):
                    notes.append("杀印相生候选")
                if stem_gods.get("正官", 0):
                    notes.append("官杀混杂复核")
            elif rule_id == "pattern_005":
                if stem_gods.get("偏印", 0):
                    notes.append("偏印夺食复核")
                if stem_gods.get("正财", 0) or stem_gods.get("偏财", 0):
                    notes.append("食神生财候选")
                if stem_gods.get("七杀", 0):
                    notes.append("食神制杀候选")
            elif rule_id == "pattern_007":
                if stem_gods.get("正官", 0):
                    notes.append("伤官见官")
                if stem_gods.get("正财", 0) or stem_gods.get("偏财", 0):
                    notes.append("伤官生财候选")
                if stem_gods.get("正印", 0) or stem_gods.get("偏印", 0):
                    notes.append("伤官配印候选")
            elif rule_id == "pattern_004":
                if stem_gods.get("正财", 0) or stem_gods.get("偏财", 0):
                    notes.append("财星破印复核")
                if stem_gods.get("正官", 0) or stem_gods.get("七杀", 0):
                    notes.append("官杀护印/化杀生身候选")

            hits.append({
                "rule_id": rule_id,
                "name": PATTERN_SIGNAL_NAMES[rule_id],
                "status": status,
                "confidence": confidence,
                "matched": matched,
                "notes": notes,
                "manual_review_required": self._pattern_rule_needs_review(rule_id),
            })

        jianlu_hit = self._evaluate_jianlu_yuejie(
            day_master=day_master,
            month_branch=month_branch,
            month_main=month_main,
            month_hidden=month_hidden,
            stem_gods=stem_gods,
            current_pattern=current_pattern,
        )
        if jianlu_hit:
            hits.append(jianlu_hit)

        yang_blade_hit = self._evaluate_yang_blade(
            day_master=day_master,
            month_branch=month_branch,
            stem_gods=stem_gods,
            current_pattern=current_pattern,
        )
        if yang_blade_hit:
            hits.append(yang_blade_hit)

        guard_hit = self._evaluate_pattern_guard(pattern_raw, hits, stem_gods)
        if guard_hit:
            hits.append(guard_hit)
        return hits

    def _stem_god_counts(self, ten_gods: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in ten_gods:
            if item.get("pillar") not in STEM_PILLARS:
                continue
            god = item.get("gan_god")
            if isinstance(god, str) and god != "日主":
                counts[god] = counts.get(god, 0) + 1
        return counts

    def _ten_god_counts(self, ten_gods: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in ten_gods:
            god = item.get("gan_god")
            if isinstance(god, str) and god != "日主":
                counts[god] = counts.get(god, 0) + 1
            for hidden in item.get("zhi_cang", []):
                hidden_god = hidden.get("god")
                if isinstance(hidden_god, str) and hidden_god != "日主":
                    counts[hidden_god] = counts.get(hidden_god, 0) + 1
        return counts

    def _month_main_god(self, ten_gods: list[dict[str, Any]]) -> str | None:
        for item in ten_gods:
            if item.get("pillar") != "月柱":
                continue
            for hidden in item.get("zhi_cang", []):
                if hidden.get("label") == "主气":
                    god = hidden.get("god")
                    return god if isinstance(god, str) else None
        return None

    def _month_hidden_gods(self, ten_gods: list[dict[str, Any]]) -> list[str]:
        for item in ten_gods:
            if item.get("pillar") != "月柱":
                continue
            return [
                hidden["god"]
                for hidden in item.get("zhi_cang", [])
                if isinstance(hidden.get("god"), str) and hidden.get("god") != "日主"
            ]
        return []

    def _month_branch(self, ten_gods: list[dict[str, Any]]) -> str | None:
        for item in ten_gods:
            if item.get("pillar") == "月柱":
                branch = item.get("zhi")
                return branch if isinstance(branch, str) else None
        return None

    def _evaluate_jianlu_yuejie(
        self,
        *,
        day_master: str | None,
        month_branch: str | None,
        month_main: str | None,
        month_hidden: set[str],
        stem_gods: dict[str, int],
        current_pattern: str,
    ) -> dict[str, Any] | None:
        is_jianlu = bool(day_master and month_branch == JIANLU_BRANCH_BY_DAY_MASTER.get(day_master))
        is_yuejie = month_main in {"比肩", "劫财", "日主"} or bool(month_hidden & {"比肩", "劫财", "日主"})
        if not (is_jianlu or is_yuejie):
            return None

        outlets: list[str] = []
        if stem_gods.get("正财", 0) or stem_gods.get("偏财", 0):
            outlets.append("财星出口候选")
        if stem_gods.get("正官", 0) or stem_gods.get("七杀", 0):
            outlets.append("官杀制劫候选")
        if stem_gods.get("食神", 0) or stem_gods.get("伤官", 0):
            outlets.append("食伤泄秀候选")
        if not outlets:
            outlets.append("比劫当令但出口不足，需人工复核")

        return {
            "rule_id": "pattern_009",
            "name": "建禄月劫",
            "status": "候选成立",
            "confidence": 0.66 if is_jianlu else 0.6,
            "matched": {
                "日主": day_master,
                "月支": month_branch,
                "月令主气十神": month_main,
                "月令藏干十神": sorted(month_hidden),
                "是否建禄": is_jianlu,
                "是否月劫": is_yuejie,
                "旧引擎主格": current_pattern,
                "透干十神计数": stem_gods,
            },
            "notes": outlets,
            "manual_review_required": self._pattern_rule_needs_review("pattern_009"),
        }

    def _pattern_rule_needs_review(self, rule_id: str) -> bool:
        rule = self.rule_index.get(rule_id, {})
        return (
            rule.get("status") in {"candidate_rule", "manual_review"}
            or str(rule.get("subjectivity", "")).lower() == "high"
        )

    def _evaluate_yang_blade(
        self,
        *,
        day_master: str | None,
        month_branch: str | None,
        stem_gods: dict[str, int],
        current_pattern: str,
    ) -> dict[str, Any] | None:
        if not day_master or month_branch != YANG_BLADE_BRANCH_BY_DAY_MASTER.get(day_master):
            return None

        notes: list[str] = []
        if stem_gods.get("正官", 0) or stem_gods.get("七杀", 0):
            notes.append("官杀制刃候选")
        if stem_gods.get("正印", 0) or stem_gods.get("偏印", 0):
            notes.append("印星助刃复核")
        if stem_gods.get("正财", 0) or stem_gods.get("偏财", 0):
            notes.append("财星耗刃候选")
        if not notes:
            notes.append("阳刃当令，需复核制化是否得宜")

        return {
            "rule_id": "pattern_008",
            "name": "阳刃格",
            "status": "候选成立",
            "confidence": 0.64,
            "matched": {
                "日主": day_master,
                "月支": month_branch,
                "阳刃映射": YANG_BLADE_BRANCH_BY_DAY_MASTER.get(day_master),
                "旧引擎主格": current_pattern,
                "透干十神计数": stem_gods,
            },
            "notes": notes,
            "manual_review_required": True,
        }

    def _evaluate_pattern_guard(
        self,
        pattern_raw: dict[str, Any],
        pattern_hits: list[dict[str, Any]],
        stem_gods: dict[str, int],
    ) -> dict[str, Any] | None:
        status = pattern_raw.get("成败状态")
        if status not in {"成", "救应"} and not pattern_hits:
            return None

        pattern_name = str(pattern_raw.get("格局名称", ""))
        breakers: list[str] = []
        protectors: list[str] = []
        if "正官" in pattern_name and stem_gods.get("伤官", 0):
            breakers.append("官格见伤")
            if stem_gods.get("正印", 0) or stem_gods.get("偏印", 0):
                protectors.append("印星护官")
            if stem_gods.get("正财", 0) or stem_gods.get("偏财", 0):
                protectors.append("财星通关")
        if "印" in pattern_name and (stem_gods.get("正财", 0) or stem_gods.get("偏财", 0)):
            breakers.append("印格见财")
            if stem_gods.get("比肩", 0) or stem_gods.get("劫财", 0):
                protectors.append("比劫制财护印")
            if stem_gods.get("正官", 0) or stem_gods.get("七杀", 0):
                protectors.append("官杀护印")
        if not breakers and not protectors:
            return None

        return {
            "rule_id": "medicine_type_009",
            "name": "格局护卫病药",
            "status": "护卫候选",
            "confidence": 0.62 if protectors else 0.55,
            "matched": {
                "旧引擎主格": pattern_name,
                "成败状态": status,
                "破格因素": breakers,
                "护卫候选": protectors,
                "透干十神计数": stem_gods,
            },
            "notes": ["后置规则，只提示护格/救格方向，不改写主格"],
            "manual_review_required": True,
        }

    def _evidence_from_pattern_hits(self, hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []
        for hit in hits:
            rule = self.rule_index.get(hit["rule_id"], {})
            evidence.append(
                evidence_item(
                    key=f"pattern.expansion.{hit['rule_id']}",
                    source=str(rule.get("source", "资料口 B 可执行规则")),
                    rule=str(rule.get("trigger", hit["name"])),
                    matched=hit.get("matched"),
                    confidence=float(hit.get("confidence", 0.6)),
                    uncertainty=str(rule.get("uncertainty", "候选规则需结合全局复核。")),
                )
            )
        return evidence

    def _eval_strength(self, analysis: dict[str, Any]) -> dict[str, Any]:
        raw = get_path(analysis, "assessment", "日主强弱", default={}) or {}
        ten_gods = get_path(analysis, "certain", "十神分布", default=[]) or []
        rule_hits = self._evaluate_strength_medicine(analysis, raw, ten_gods)
        confidence = confidence_from_assessment(raw, 0.6)
        evidence = [
            evidence_item(
                key="strength.three_axis",
                source="月令、根气、天干助泄三维评估",
                rule="得令、有根、有助分开判断，再给综合倾向。",
                matched={
                    "得令": raw.get("得令"),
                    "有根": raw.get("有根"),
                    "有助": raw.get("有助"),
                },
                confidence=confidence,
                uncertainty=str(raw.get("重要说明", "强弱不宜脱离格局单独定论。")),
            )
        ]
        evidence.extend(self._evidence_from_executable_hits("strength", rule_hits))
        data = deepcopy(raw)
        if rule_hits:
            data["B口可执行规则命中"] = rule_hits
        return {
            "domain": "strength",
            "summary": str(raw.get("综合倾向", "未判定")),
            "data": data,
            "executable_rule_ids": [hit["rule_id"] for hit in rule_hits],
            "executable_notes": [
                note
                for hit in rule_hits
                for note in hit.get("notes", [])
            ],
            "executable_manual_review_required": any(
                hit.get("manual_review_required") for hit in rule_hits
            ),
            "confidence": confidence,
            "evidence": evidence,
        }

    def _evaluate_strength_medicine(
        self,
        analysis: dict[str, Any],
        strength_raw: dict[str, Any],
        ten_gods: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tendency = str(strength_raw.get("综合倾向", ""))
        if tendency not in {"偏强", "过强", "偏弱", "过弱"}:
            return []

        stem_gods = self._stem_god_counts(ten_gods)
        all_gods = self._ten_god_counts(ten_gods)
        pattern_raw = get_path(analysis, "assessment", "格局成败", default={}) or {}
        follow_raw = get_path(analysis, "assessment", "从格检测", default={}) or {}
        strong = tendency in {"偏强", "过强"}
        weak = tendency in {"偏弱", "过弱"}
        hits: list[dict[str, Any]] = []

        hits.append({
            "rule_id": "medicine_type_001",
            "name": "扶抑病药",
            "status": "扶抑候选",
            "confidence": 0.6,
            "matched": {
                "综合倾向": tendency,
                "得令": strength_raw.get("得令"),
                "有根": strength_raw.get("有根"),
                "有助": strength_raw.get("有助"),
                "从格检测": follow_raw,
                "透干十神计数": stem_gods,
            },
            "notes": [
                "扶抑候选：日主偏强，优先复核泄、耗、制方向"
                if strong
                else "扶抑候选：日主偏弱，优先复核印、比扶助方向"
            ],
            "manual_review_required": True,
        })

        if strong:
            notes = []
            if any(all_gods.get(god, 0) for god in OUTPUT_GODS):
                notes.append("过旺泄耗候选：食伤泄旺")
            if any(all_gods.get(god, 0) for god in WEALTH_GODS):
                notes.append("过旺泄耗候选：财星耗旺")
            if any(all_gods.get(god, 0) for god in OFFICER_GODS):
                notes.append("过旺泄耗候选：官杀制旺")
            if not notes:
                notes.append("过旺泄耗制方向候选，现有可执行药神不足")
            hits.append({
                "rule_id": "medicine_type_005",
                "name": "过旺泄耗病药",
                "status": "泄耗制候选",
                "confidence": 0.58,
                "matched": {
                    "综合倾向": tendency,
                    "从格检测": follow_raw,
                    "全局十神计数": all_gods,
                    "旧引擎主格": pattern_raw.get("格局名称"),
                },
                "notes": notes,
                "manual_review_required": True,
            })

        if weak:
            notes = []
            if any(all_gods.get(god, 0) for god in RESOURCE_GODS):
                notes.append("过弱扶助候选：印星扶身")
            if any(all_gods.get(god, 0) for god in PEER_GODS):
                notes.append("过弱扶助候选：比劫帮身")
            if not notes:
                notes.append("过弱扶助方向候选，印比信号不足")
            hits.append({
                "rule_id": "medicine_type_006",
                "name": "过弱扶助病药",
                "status": "扶助候选",
                "confidence": 0.58,
                "matched": {
                    "综合倾向": tendency,
                    "从格检测": follow_raw,
                    "全局十神计数": all_gods,
                    "旧引擎主格": pattern_raw.get("格局名称"),
                },
                "notes": notes,
                "manual_review_required": True,
            })

            has_officer_pressure = any(all_gods.get(god, 0) for god in OFFICER_GODS)
            has_output_drain = any(all_gods.get(god, 0) for god in OUTPUT_GODS)
            if has_officer_pressure and has_output_drain:
                kx_notes = ["克泄交加候选：官杀克身与食伤泄身并见"]
                if not any(all_gods.get(god, 0) for god in RESOURCE_GODS | PEER_GODS):
                    kx_notes.append("印比承接不足复核")
                hits.append({
                    "rule_id": "medicine_type_008",
                    "name": "克泄交加病药",
                    "status": "克泄交加候选",
                    "confidence": 0.56,
                    "matched": {
                        "综合倾向": tendency,
                        "官杀计数": {god: all_gods.get(god, 0) for god in OFFICER_GODS},
                        "食伤计数": {god: all_gods.get(god, 0) for god in OUTPUT_GODS},
                        "印比计数": {god: all_gods.get(god, 0) for god in RESOURCE_GODS | PEER_GODS},
                    },
                    "notes": kx_notes,
                    "manual_review_required": True,
                })

        return hits

    def _eval_tiaohou(self, analysis: dict[str, Any]) -> dict[str, Any]:
        raw = get_path(analysis, "certain", "调候用神", default={}) or {}
        match = get_path(analysis, "assessment", "调候满足度", default={}) or {}
        rule_hits = self._evaluate_tiaohou_medicine(raw, match)
        confidence = 0.7 if raw and raw.get("首选用神") else 0.55
        evidence = [
            evidence_item(
                key="tiaohou.lookup",
                source=str(raw.get("数据来源", "穷通宝鉴调候用神表")),
                rule="按日主与月令查表，并检查原局是否透出首选/次选用神。",
                matched={
                    "日主": raw.get("日主"),
                    "月令": raw.get("月令"),
                    "首选用神": raw.get("首选用神"),
                    "次选用神": raw.get("次选用神"),
                    "原局已透首选": raw.get("原局已透首选"),
                    "原局已透次选": raw.get("原局已透次选"),
                },
                confidence=confidence,
                uncertainty=str(match.get("说明", "调候反映气候背景，不直接等同吉凶。")),
            )
        ]
        evidence.extend(self._evidence_from_executable_hits("tiaohou", rule_hits))
        data = {"调候用神": deepcopy(raw), "满足度": deepcopy(match)}
        if rule_hits:
            data["B口可执行规则命中"] = rule_hits
        return {
            "domain": "tiaohou",
            "summary": str(match.get("满足程度", raw.get("status", "调候查表"))),
            "data": data,
            "executable_rule_ids": [hit["rule_id"] for hit in rule_hits],
            "executable_notes": [
                note
                for hit in rule_hits
                for note in hit.get("notes", [])
            ],
            "executable_manual_review_required": any(
                hit.get("manual_review_required") for hit in rule_hits
            ),
            "confidence": confidence,
            "evidence": evidence,
        }

    def _evaluate_tiaohou_medicine(
        self,
        tiaohou_raw: dict[str, Any],
        match: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not tiaohou_raw:
            return []
        satisfaction = str(match.get("满足程度", ""))
        if "未透" not in satisfaction:
            return []

        notes: list[str] = []
        if "均未透" in satisfaction:
            notes.append("调候药不足候选：首选/次选均未透")
        elif "首选未透" in satisfaction:
            notes.append("调候药不足候选：首选未透，次选仅作候选")
        else:
            notes.append("调候病药候选：候神透出与受制情况需复核")

        return [{
            "rule_id": "medicine_type_002",
            "name": "调候病药",
            "status": "调候候选",
            "confidence": 0.6,
            "matched": {
                "日主": tiaohou_raw.get("日主"),
                "月令": tiaohou_raw.get("月令"),
                "首选用神": tiaohou_raw.get("首选用神"),
                "次选用神": tiaohou_raw.get("次选用神"),
                "原局已透首选": tiaohou_raw.get("原局已透首选"),
                "原局已透次选": tiaohou_raw.get("原局已透次选"),
                "满足程度": satisfaction,
                "忌神情况": match.get("忌神情况"),
            },
            "notes": notes,
            "manual_review_required": True,
        }]

    def _eval_yong_shen(self, analysis: dict[str, Any]) -> dict[str, Any]:
        raw = get_path(analysis, "assessment", "用神优先级", default={}) or {}
        confidence = 0.65
        return {
            "domain": "yong_shen",
            "summary": str(get_path(raw, "用神优先级", "第一优先", default="未判定")),
            "data": deepcopy(raw),
            "confidence": confidence,
            "evidence": [
                evidence_item(
                    key="yong_shen.priority",
                    source=str(get_path(raw, "用神优先级", "出处", default="用神优先级规则")),
                    rule="以格局用神为主，调候用神互参，并提示透干主事变化。",
                    matched=deepcopy(raw),
                    confidence=confidence,
                    uncertainty="用神最终取舍需要结合原局清浊、强弱与岁运。"
                )
            ],
        }

    def _eval_chong_he(self, analysis: dict[str, Any]) -> dict[str, Any]:
        facts = get_path(analysis, "certain", "地支刑冲合", default={}) or {}
        dynamic = get_path(analysis, "certain", "合冲动态判断", default={}) or {}
        ten_gods = get_path(analysis, "certain", "十神分布", default=[]) or []
        rule_hits = self._evaluate_chong_he_expansion(facts, dynamic, self._stem_god_counts(ten_gods))
        confidence = 0.7
        evidence = [
            evidence_item(
                key="chong_he.scan",
                source="天干五合、地支六合三合刑冲害固定关系表",
                rule="先扫描固定关系，再由动态规则提示是否成局或解冲。",
                matched={"facts": facts, "dynamic": dynamic},
                confidence=confidence,
                uncertainty=str(facts.get("备注", "合冲是否发用仍需结合位置、透干、岁运。")),
            )
        ]
        evidence.extend(self._evidence_from_chong_he_hits(rule_hits))
        data = {"facts": deepcopy(facts), "dynamic": deepcopy(dynamic)}
        if rule_hits:
            data["B口可执行规则命中"] = rule_hits
        return {
            "domain": "chong_he",
            "summary": "合冲刑害事实与动态判断",
            "data": data,
            "executable_rule_ids": [hit["rule_id"] for hit in rule_hits],
            "executable_notes": [
                note
                for hit in rule_hits
                for note in hit.get("notes", [])
            ],
            "executable_manual_review_required": any(
                hit.get("manual_review_required") for hit in rule_hits
            ),
            "confidence": confidence,
            "evidence": evidence,
        }

    def _evaluate_chong_he_expansion(
        self,
        facts: dict[str, Any],
        dynamic: dict[str, Any],
        stem_gods: dict[str, int],
    ) -> list[dict[str, Any]]:
        hits: list[dict[str, Any]] = []
        relation_hits = self._collect_relation_hits(facts)
        if relation_hits:
            notes = self._relation_risk_notes(dynamic)
            if not notes:
                notes = ["冲合刑害已见事实，需结合位置与用神人工复核"]
            hits.append({
                "rule_id": "medicine_type_007",
                "name": "冲合刑害病药",
                "status": "候选成立",
                "confidence": 0.62,
                "matched": {
                    "关系事实": relation_hits,
                    "动态判断": dynamic,
                },
                "notes": notes,
                "manual_review_required": True,
            })

        tongguan_notes = self._tongguan_notes(dynamic, stem_gods)
        if tongguan_notes:
            hits.append({
                "rule_id": "medicine_type_003",
                "name": "通关病药",
                "status": "通关候选",
                "confidence": 0.58,
                "matched": {
                    "动态判断": dynamic,
                    "透干十神计数": stem_gods,
                },
                "notes": tongguan_notes,
                "manual_review_required": True,
            })
        return hits

    def _collect_relation_hits(self, facts: dict[str, Any]) -> dict[str, list[Any]]:
        relation_hits: dict[str, list[Any]] = {}
        for key, value in facts.items():
            if key == "备注":
                continue
            if isinstance(value, list) and value:
                relation_hits[key] = deepcopy(value)
        return relation_hits

    def _relation_risk_notes(self, dynamic: dict[str, Any]) -> list[str]:
        notes: list[str] = []
        for item in dynamic.get("相冲分析", []):
            if not isinstance(item, dict):
                continue
            position = str(item.get("位置", ""))
            if "月支" in position:
                notes.append("月支受冲，月令/主格稳定性复核")
            if "日支" in position:
                notes.append("日支受冲，宫位与根气影响复核")
            he_jie = item.get("合解冲")
            if isinstance(he_jie, dict) and he_jie.get("能解"):
                notes.append("存在合解冲候选")
        return notes

    def _tongguan_notes(self, dynamic: dict[str, Any], stem_gods: dict[str, int]) -> list[str]:
        notes: list[str] = []
        for item in dynamic.get("相冲分析", []):
            if not isinstance(item, dict):
                continue
            he_jie = item.get("合解冲")
            if isinstance(he_jie, dict) and he_jie.get("能解"):
                notes.append("合解冲通关候选")
                break

        has_officer = bool(stem_gods.get("正官", 0) or stem_gods.get("七杀", 0))
        has_resource = bool(stem_gods.get("正印", 0) or stem_gods.get("偏印", 0))
        has_output = bool(stem_gods.get("食神", 0) or stem_gods.get("伤官", 0))
        has_wealth = bool(stem_gods.get("正财", 0) or stem_gods.get("偏财", 0))
        if has_officer and has_resource:
            notes.append("官杀-印-日主通关候选")
        if has_output and has_wealth and has_officer:
            notes.append("食伤-财-官杀通关候选")
        return notes

    def _evidence_from_chong_he_hits(self, hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []
        for hit in hits:
            rule = self.rule_index.get(hit["rule_id"], {})
            evidence.append(
                evidence_item(
                    key=f"chong_he.expansion.{hit['rule_id']}",
                    source=str(rule.get("source", "资料口 B 可执行规则")),
                    rule=str(rule.get("trigger", hit["name"])),
                    matched=hit.get("matched"),
                    confidence=float(hit.get("confidence", 0.58)),
                    uncertainty=str(rule.get("uncertainty", "候选规则需结合全局复核。")),
                )
            )
        return evidence

    def _evidence_from_executable_hits(
        self,
        domain: str,
        hits: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []
        for hit in hits:
            rule = self.rule_index.get(hit["rule_id"], {})
            evidence.append(
                evidence_item(
                    key=f"{domain}.expansion.{hit['rule_id']}",
                    source=str(rule.get("source", "资料口 B 可执行规则")),
                    rule=str(rule.get("trigger", hit["name"])),
                    matched=hit.get("matched"),
                    confidence=float(hit.get("confidence", 0.56)),
                    uncertainty=str(rule.get("uncertainty", "候选规则需结合全局复核。")),
                )
            )
        return evidence

    def _eval_liuqin(self, analysis: dict[str, Any]) -> dict[str, Any]:
        facts = get_path(analysis, "certain", "六亲对应", default={}) or {}
        quality = get_path(analysis, "assessment", "六亲质量", default={}) or {}
        confidence = 0.6
        return {
            "domain": "liuqin",
            "summary": "六亲对应与质量倾向",
            "data": {"对应": deepcopy(facts), "质量": deepcopy(quality)},
            "confidence": confidence,
            "evidence": [
                evidence_item(
                    key="liuqin.map",
                    source="十神六亲映射与原局质量评估",
                    rule="以性别、十神、宫位和喜忌倾向综合映射六亲。",
                    matched={"对应": facts, "质量": quality},
                    confidence=confidence,
                    uncertainty="六亲判断属于倾向，不等于具体亲属事件。"
                )
            ],
        }

    def _eval_career(self, analysis: dict[str, Any]) -> dict[str, Any]:
        pattern = self._eval_pattern(analysis)
        yong = self._eval_yong_shen(analysis)
        confidence = min(pattern["confidence"], yong["confidence"])
        return {
            "domain": "career",
            "summary": "事业主题以格局成败、官杀印食伤和用神优先级为主要依据。",
            "data": {"pattern": pattern["data"], "yong_shen": yong["data"]},
            "confidence": confidence,
            "evidence": pattern["evidence"] + yong["evidence"],
        }

    def _eval_wealth(self, analysis: dict[str, Any]) -> dict[str, Any]:
        pattern = self._eval_pattern(analysis)
        qing_zhuo = get_path(analysis, "assessment", "十神清浊", default={}) or {}
        rule_hits = self._evaluate_qing_zhuo_medicine(qing_zhuo)
        confidence = 0.58
        evidence = pattern["evidence"] + [
            evidence_item(
                key="wealth.qing_zhuo",
                source="十神清浊评估",
                rule="观察财星与格局、用神、忌神之间的清浊关系。",
                matched=qing_zhuo,
                confidence=confidence,
                uncertainty="财富结论必须结合大运流年，不宜只看原局。"
            )
        ]
        evidence.extend(self._evidence_from_executable_hits("wealth", rule_hits))
        data = {"pattern": pattern["data"], "十神清浊": deepcopy(qing_zhuo)}
        if rule_hits:
            data["B口可执行规则命中"] = rule_hits
        return {
            "domain": "wealth",
            "summary": "财富主题以财星、格局清浊、用神是否得力为依据。",
            "data": data,
            "executable_rule_ids": [hit["rule_id"] for hit in rule_hits],
            "executable_notes": [
                note
                for hit in rule_hits
                for note in hit.get("notes", [])
            ],
            "executable_manual_review_required": any(
                hit.get("manual_review_required") for hit in rule_hits
            ),
            "confidence": confidence,
            "evidence": evidence,
        }

    def _evaluate_qing_zhuo_medicine(self, qing_zhuo: dict[str, Any]) -> list[dict[str, Any]]:
        if not qing_zhuo:
            return []

        overall = get_path(qing_zhuo, "格局整体清浊", "结论", default="")
        taboo_seen = get_path(qing_zhuo, "忌神透干情况", "已透干", default=[]) or []
        taboo_seen = [item for item in taboo_seen if item != "无"]
        conflict = get_path(qing_zhuo, "并透相生相克", "两不相谋", default=[]) or []
        conflict = [item for item in conflict if item != "无"]
        if "浊" not in str(overall) and not taboo_seen and not conflict:
            return []

        notes = [f"清浊复核：格局整体{overall}"]
        if taboo_seen:
            notes.append(f"忌神透干复核：{','.join(map(str, taboo_seen))}")
        if conflict:
            notes.append(f"两不相谋候选：{','.join(map(str, conflict))}")

        return [{
            "rule_id": "medicine_type_004",
            "name": "清浊病药",
            "status": "清浊复核",
            "confidence": 0.56,
            "matched": {
                "格局整体清浊": get_path(qing_zhuo, "格局整体清浊", default={}),
                "忌神透干情况": get_path(qing_zhuo, "忌神透干情况", default={}),
                "并透相生相克": get_path(qing_zhuo, "并透相生相克", default={}),
            },
            "notes": notes,
            "manual_review_required": True,
        }]

    def _eval_marriage(self, analysis: dict[str, Any]) -> dict[str, Any]:
        liuqin = self._eval_liuqin(analysis)
        confidence = 0.55
        return {
            "domain": "marriage",
            "summary": "婚恋主题以配偶星、夫妻宫、六亲质量与合冲为主要依据。",
            "data": deepcopy(liuqin["data"]),
            "confidence": confidence,
            "evidence": liuqin["evidence"],
        }

    def _eval_health(self, analysis: dict[str, Any]) -> dict[str, Any]:
        raw = get_path(analysis, "certain", "健康对应", default={}) or {}
        confidence = 0.5
        return {
            "domain": "health",
            "summary": "健康只输出传统对应关系和风险观察点，不作医学判断。",
            "data": deepcopy(raw),
            "confidence": confidence,
            "evidence": [
                evidence_item(
                    key="health.mapping",
                    source=str(raw.get("数据来源", "渊海子平身体部位对应")),
                    rule="列出天干地支对应脏腑与身体部位。",
                    matched=raw,
                    confidence=confidence,
                    uncertainty=str(raw.get("重要说明", "不可替代医学诊断。")),
                )
            ],
        }

    def _eval_luck_cycle(self, analysis: dict[str, Any]) -> dict[str, Any]:
        raw = get_path(analysis, "certain", "大运", default={}) or {}
        confidence = 0.75 if raw else 0.5
        return {
            "domain": "luck_cycle",
            "summary": "大运列表已给出；指定 target_year 后接入大运/流年互动触发。",
            "data": deepcopy(raw),
            "confidence": confidence,
            "evidence": [
                evidence_item(
                    key="luck_cycle.dayun",
                    source="bazi_engine 大运算法",
                    rule="按男女阴阳顺逆与节气差换算起运岁数。",
                    matched=raw,
                    confidence=confidence,
                    uncertainty="大运/流年触发分只代表关注度，不直接代表吉凶；流月、流日仍为预留接口。"
                )
            ],
        }
