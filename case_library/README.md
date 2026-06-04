# Case Library Intake / 命例库入库说明

This directory stores staging datasets for case intake. These files are not all
automatic regression cases.
这个目录用于存放命例入库阶段的数据。这里的文件并不都等于自动回归测试案例。

## Files / 文件用途

- `gold_cases.json`: strict automatic-regression candidates. This file may stay
  empty until a case satisfies the gold admission policy.
- `gold_cases.json`：严格自动回归候选。没有符合标准的案例前，这个文件可以为空。
- `reference_cases.json`: useful reference cases for manual review, event
  tagging, and interpretation-quality discussion. Reference cases do not enter
  automatic regression by default.
- `reference_cases.json`：参考命例，用于人工复核、事件标注和解读质量讨论。
  reference case 默认不进入自动回归。
- `youtube_candidate_sources.json`: YouTube or other source leads. These are
  intake leads only unless complete birth data and externally verifiable events
  are present.
- `youtube_candidate_sources.json`：YouTube 或其他资料线索。除非出生信息完整且事件可外部验证，
  否则只作为线索，不直接用于自动验证。
- `excluded_cases.json`: rejected or blocked intake items. These should not be
  promoted until the exclusion reason is resolved.
- `excluded_cases.json`：被拒绝或暂时阻塞的候选。排除原因解决前不应升级。

## Gold Admission Policy / Gold Case 入库门槛

A case may enter `gold_cases.json` only when all of these are true:
只有同时满足以下条件，案例才可以进入 `gold_cases.json`：

- Birth year, month, day, hour, and minute are complete integers.
- 出生年、月、日、时、分完整。
- Birth time is not merely rectified, blogger-inferred, or unknown.
- 出生时辰不是纯校正、博主推断或未知。
- At least three known events are present.
- 至少有 3 个已知事件。
- At least one known event includes year, month, and day.
- 至少 1 个事件有完整年月日。
- Every known event has a `source`; `source_url` is strongly preferred.
- 每个已知事件都有 `source`；强烈建议也有 `source_url`。
- Calendar and timezone support is validated for the birth location.
- 出生地点对应的历法和时区支持已验证。

Public overseas cases that require international timezone/calendar support stay
reference-only until that support is explicitly validated for automatic
regression.
需要国际时区/历法支持的海外公开案例，在自动回归支持明确验证前，保持 reference-only。

## Validation / 验证

Run:
运行：

```powershell
.\run_case_library_validation.cmd
```

Expected current state:
当前预期状态：

- `gold_cases`: empty, warning only.
- `gold_cases`：为空，只给 warning，不算失败。
- `reference_cases`: may contain reference-only public cases.
- `reference_cases`：可以包含 reference-only 的公开案例。
- `youtube_candidate_sources`: may contain source leads, with no gold promotion.
- `youtube_candidate_sources`：可以包含资料线索，但不自动升 gold。
- `excluded_cases`: may stay empty until rejected intake items are recorded.
- `excluded_cases`：没有被拒案例前可以为空。
