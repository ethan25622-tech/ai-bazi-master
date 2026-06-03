# AI Bazi Master Handoff

## Current State

The command-center layer is stable and validation-gated.

- Legacy chart calculation is bundled in `bazi_legacy/`; `BAZI_ENGINE_DIR` can override it for local development.
- Stable project interface lives in `bazi_master/`.
- Core executable rule signals are connected through `RuleEngine`.
- Annual, monthly, and explicit daily-filter timing outputs are guarded.
- Phrase and dialogue layers consume guard fields and block direct high-risk expression.
- Case-library intake is governed, with `gold_cases.json` intentionally empty.

## Stable Validation Gate

Use this as the main acceptance command:

```powershell
.\run_all_validation.cmd
```

The full suite currently covers:

- rule execution
- calendar boundary patch validation
- annual luck-cycle validation
- monthly window validation
- luck guard validation
- guarded daily-filter validation
- phrase safety validation
- DialogueEngine guard snapshots
- case-library intake validation
- case-library negative guardrails
- Mingli seed case validation
- project-level status contract

## Current Rule Surface

Core rule execution includes:

- `pattern_004` through `pattern_009`
- `medicine_type_001` through `medicine_type_009`

Luck-cycle execution includes:

- `luck_003` through `luck_008`
- `year_001` through `year_008`
- `luck_guard_001`
- `luck_guard_002`

Daily filtering is intentionally narrow:

- only appears when both `target_year` and `target_month` are provided
- only filters dates inside upper annual/monthly trigger windows
- does not perform daily fortune-telling
- does not label dates as good, bad, auspicious, inauspicious, or disaster dates

## Guard Contract

Guarded timing outputs must keep these fields:

- `risk_guard_required`
- `risk_level`
- `safe_wording`
- `forbidden_assertions`
- `output_allowed`
- `direct_expression_allowed`

If a rule is a candidate or manual-review signal, the output must stay
conservative and avoid absolute event claims.

Forbidden output classes remain:

- medical diagnosis
- investment advice
- certain divorce, death, disease, bankruptcy, accident, lawsuit, or disaster claims
- daily generic prediction
- specific-date certainty

## Case Library Policy

`case_library/gold_cases.json` may remain empty.  This is normal until a case
meets all gold criteria:

- complete birth year, month, day, hour, and minute
- birth time not inferred or rectified
- at least three known events
- at least one known event with year, month, and day
- external source coverage for known events
- validated timezone and calendar support for automatic regression

Public overseas cases remain reference-only until international timezone and
calendar support is explicitly validated.

## Remaining Work

These items are intentionally not completed in the current stable layer because
they require new source material, external verification, or larger product
decisions:

- collect and vet real gold cases
- validate international timezone/calendar support
- add broader real-case guard matrices
- extend daily filtering beyond v1 only after guard behavior remains stable
- add richer user-facing product workflows on top of the stable schema

## Do Not Regress

- Do not promote public reference cases into automatic regression without gold
  criteria.
- Do not make `daily_filter` appear without explicit `target_month`.
- Do not interpret `trigger_score` as good/bad or certainty.
- Do not bypass `PhraseEngine` guard consumption in dialogue output.
- Do not modify `1902-01-01` through `1902-02-28` compatibility unless a new
  calendar support decision is made.
