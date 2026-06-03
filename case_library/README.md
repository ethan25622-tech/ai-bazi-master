# Case Library Intake

This directory stores staging datasets for case intake. These files are not all
automatic regression cases.

## Files

- `gold_cases.json`: strict automatic-regression candidates. This file may stay
  empty until a case satisfies the gold admission policy.
- `reference_cases.json`: useful reference cases for manual review, event
  tagging, and interpretation-quality discussion. Reference cases do not enter
  automatic regression by default.
- `youtube_candidate_sources.json`: YouTube or other source leads. These are
  intake leads only unless complete birth data and externally verifiable events
  are present.
- `excluded_cases.json`: rejected or blocked intake items. These should not be
  promoted until the exclusion reason is resolved.

## Gold Admission Policy

A case may enter `gold_cases.json` only when all of these are true:

- Birth year, month, day, hour, and minute are complete integers.
- Birth time is not merely rectified, blogger-inferred, or unknown.
- At least three known events are present.
- At least one known event includes year, month, and day.
- Every known event has a `source`; `source_url` is strongly preferred.
- Calendar and timezone support is validated for the birth location.

Public overseas cases that require international timezone/calendar support stay
reference-only until that support is explicitly validated for automatic
regression.

## Validation

Run:

```powershell
.\run_case_library_validation.cmd
```

Expected current state:

- `gold_cases`: empty, warning only.
- `reference_cases`: may contain reference-only public cases.
- `youtube_candidate_sources`: may contain source leads, with no gold promotion.
- `excluded_cases`: may stay empty until rejected intake items are recorded.
