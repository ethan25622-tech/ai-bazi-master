# Validation Rules

## Supported Range

- This project supports zydx-compatible Bazi pillar validation from `1902-03-01` onward.
- Dates from `1902-01-01` through `1902-02-28` are outside the guaranteed compatibility range.
- For `1902-01-01` through `1902-02-28`, results are not guaranteed to match `zydx.top`.

## Validation Standard

- The reference standard for automated validation is `https://zydx.top/paipan.php`.
- Local pillar output is considered correct when year, month, day, and hour pillars match `zydx.top`.

## Verified Boundary

- The leap-year boundary case `1904-02-29 00:00` has been verified against `zydx.top`.
- The validated result for `1904-02-29 00:00` is `甲辰 丙寅 甲午 甲子`.

## Interpretation Safety Boundaries

- Rule-engine outputs are evidence-bearing candidate assessments, not absolute event predictions.
- `trigger_score` means attention priority only. It does not mean good luck, bad luck, danger, or certainty.
- Candidate and manual-review rules must keep `manual_review_required=true` or equivalent guard metadata.
- Health, finance, marriage, lawsuit, accident, death, disease, bankruptcy, and investment topics must use guarded/fallback wording.
- Forbidden direct claims include certain death, certain severe illness, certain divorce, certain bankruptcy, certain accident, certain lawsuit, and buy/sell investment advice.

## Luck And Daily Filter Boundaries

- Annual and monthly luck-cycle triggers must include structured guard fields when they are output through the stable schema.
- Flow-month windows are attention windows only. They do not independently assert major events.
- The daily filter may only run after an upper annual/monthly trigger and only when explicitly requested with `target_year` and `target_month`.
- Daily filter candidates are date-candidate filters only. They must not be described as auspicious days, inauspicious days, disaster days, or days when a specific event will certainly occur.
