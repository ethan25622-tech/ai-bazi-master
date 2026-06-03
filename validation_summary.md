# Validation Summary

## Current Result

- `random_cases`: 16 passed, 0 failed
- `edge_cases`: 18 passed, 0 failed
- `early_year_probe` / `year_1902_probe`: compatibility is verified from `1902-03-01` onward
- `run_rule_validation.cmd`: passed
- `run_calendar_validation.cmd`: passed
- `run_luck_validation.cmd`: passed
- `run_month_validation.cmd`: passed
- `run_phrase_validation.cmd`: passed
- `run_luck_guard_validation.cmd`: passed
- `run_dialogue_guard_validation.cmd`: passed
- `run_report_validation.cmd`: passed
- `run_interactive_validation.cmd`: passed
- `run_daily_filter_validation.cmd`: passed
- `run_case_library_validation.cmd`: passed
- `run_case_library_negative_validation.cmd`: passed
- `run_project_status_validation.cmd`: passed
- `run_all_validation.cmd`: passed

## Known Exception

- `1902-01-01` through `1902-02-28` are known exceptions.
- This early range is not guaranteed to match `zydx.top`.
- No further logic fix is planned for this range.

## Important Verified Cases

- `1904-02-29 00:00` passed after comparison with `zydx.top`.
- `23:00` day rollover cases passed.
- Li Chun year/month rollover cases passed.
- Solar-term month rollover cases passed.
- Modern leap-day cases passed, including `1988-02-29`, `2000-02-29`, and `2024-02-29`.

## Current Stable Layer

- Core rules from `rules/core_rules.json` and `rules/core_rules_b_expansion.json` are merged automatically.
- `RuleEngine` now emits executable candidate signals for `pattern_004` through `pattern_009`.
- `RuleEngine` now emits executable candidate signals for `medicine_type_001` through `medicine_type_009`.
- Annual and monthly luck-cycle triggers include structured guard fields.
- Luck-cycle execution now includes `luck_006` dayun tianke-dichong as a guarded attention signal.
- Low-weight dayun branch-clash triggers for year/hour pillars are available as guarded `luck_007`/`luck_008` signals.
- Annual sanhe/sanhui completion is available as guarded `year_007`, treated as theme aggregation rather than certain outcome.
- Annual branch-only fuyin is available as downgraded guarded `year_008`, not as full pillar fuyin or an event conclusion.
- Annual luck-cycle triggers now mark same-palace repeat activation and apply the configured attention bonus without changing the non-good/bad interpretation boundary.
- Monthly windows now consolidate repeated upper triggers on the same original pillar into one guarded window signal with `repeat_context`.
- `PhraseEngine` consumes guard fields and blocks direct expression when required.
- `PhraseEngine` also consumes guarded `daily_filter` candidates and blocked daily summaries.
- `DialogueEngine` end-to-end guard snapshots pass.
- `ReportEngine` now renders a readable full report for non-specialist testing.
- `ask_bazi.cmd` provides a simple interactive console flow: birth input, report output, then plain-text follow-up questions.
- `DailyFilterEngine` is available only as an explicit guarded date-candidate filter.
- `validate_project_status.py` now locks the project-level acceptance contract.

## Daily Filter Status

- `daily_filter` is absent by default.
- `daily_filter` is included only when both `target_year` and a valid 1-12 `target_month` are provided.
- Date candidates are limited, guarded, and marked `direct_expression_allowed=false`.
- v1 covers activated branch clashes, repeated monthly palace triggers, and existing combination windows.
- Candidate ranges now use solar-term flow-month boundaries and exclude partial boundary days.
- The daily filter does not perform daily fortune-telling and does not label dates as good, bad, or disaster dates.

## Case Library Status

- `case_library/gold_cases.json` exists and is intentionally empty until sources meet the gold admission policy.
- `case_library/reference_cases.json` currently contains reference-only material, not automatic regression cases.
- `case_library/youtube_candidate_sources.json` stores source leads and does not currently promote any YouTube item to gold.
- `case_library/excluded_cases.json` exists for rejected or blocked intake items and may remain empty.
- Gold admission requires complete birth time, non-rectified/non-inferred time source, at least three known events, at least one full-date event, and external event sourcing.
- Gold cases require source coverage for every known event; `source_url` is validated when present.
- Public cases requiring international timezone/calendar support remain reference-only until that support is explicitly validated for automatic regression.
- Negative guardrail tests verify that missing event sources, rectified birth times, bad URLs, unknown YouTube birth data, and excluded-case gold promotion are rejected.
