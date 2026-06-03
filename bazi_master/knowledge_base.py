"""Load local rule, phrase, validation, and case-library data."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_core_rules() -> dict[str, Any]:
    base = read_json(PROJECT_ROOT / "rules" / "core_rules.json")
    expansion_path = PROJECT_ROOT / "rules" / "core_rules_b_expansion.json"
    if not expansion_path.exists():
        return base
    expansion = read_json(expansion_path)
    merged = dict(base)
    merged["rule_set"] = {
        **base.get("rule_set", {}),
        "merged_sources": [
            base.get("rule_set", {}).get("name", "core_rules"),
            expansion.get("rule_set", {}).get("name", "core_rules_b_expansion"),
        ],
    }
    merged["rules"] = [*base.get("rules", []), *expansion.get("rules", [])]
    return merged


@lru_cache(maxsize=1)
def load_luck_rules() -> dict[str, Any]:
    return read_json(PROJECT_ROOT / "rules" / "luck_cycle_rules.json")


@lru_cache(maxsize=1)
def load_monthly_rules() -> dict[str, Any]:
    return read_json(PROJECT_ROOT / "rules" / "monthly_cycle_rules.json")


@lru_cache(maxsize=1)
def load_phrase_library() -> dict[str, Any]:
    return read_json(PROJECT_ROOT / "phrases" / "phrase_library.json")


@lru_cache(maxsize=1)
def load_calendar_cases() -> dict[str, Any]:
    return read_json(PROJECT_ROOT / "validation_cases" / "calendar_validation_cases.json")


def index_rules(*rule_sets: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for rule_set in rule_sets:
        for rule in rule_set.get("rules", []):
            indexed[rule["rule_id"]] = rule
    return indexed
