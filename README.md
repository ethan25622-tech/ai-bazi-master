# AI Bazi Master Command Center / AI 八字解读项目

This workspace is now the command center for the AI Bazi master project.  It
bundles the legacy calculation scripts in `bazi_legacy/`, and adds a stable
orchestration layer in `bazi_master`.

这是 AI 八字解读项目的公开测试版。项目把基础排盘、规则资料库、格局/强弱/用神判断、
大运流年流月提示、安全表达层和可读报告组合在一起，目标是让不懂八字的人也能阅读和测试。

For a compact handoff of the current stable state, validation gate, guard
contract, and remaining non-blocking work, see `PROJECT_HANDOFF.md`.

## Privacy Before Public Testing / 公开测试前的隐私提醒

Do not commit private birth data, personal feedback, raw chat logs, bot offsets,
clipboard dumps, or generated local reports.  The repository `.gitignore`
excludes local feedback and generated artifacts such as:

请不要提交私人出生信息、个人反馈原文、聊天记录、机器人 offset、剪贴板缓存或本地生成报告。
仓库的 `.gitignore` 已排除这些本地文件：

- `feedback/`
- `.telegram_offset`
- `clipboard_fallback.txt`
- `sample_report.md`
- `llm_prompt_sample.txt`
- `*_validation_report.json`
- `*_dry_run_report.json`

Public case files should only contain synthetic fixtures, anonymized cases, or
public reference cases that follow the policy in `case_library/README.md`.

公开案例文件只应包含合成样例、匿名案例，或符合 `case_library/README.md`
规则的公开参考案例。

## Feedback / 反馈

Public testers can submit feedback through GitHub Issues:
公开测试者可以通过 GitHub Issues 提交反馈：

https://github.com/ethan25622-tech/ai-bazi-master/issues/new/choose

Please do not post real names, phone numbers, addresses, private chat logs,
ID/passport information, or another person's full birth data without permission.
For details, see `FEEDBACK.md`.

请不要公开发布真实姓名、电话、地址、私人聊天记录、身份证/护照信息，
或未经允许的他人完整出生信息。详情见 `FEEDBACK.md`。

## Stable Master Interface / 稳定使用入口

Run the simple interactive version:
运行最简单的交互版：

```powershell
.\ask_bazi.cmd
```

It will ask for birth date, gender, optional target year/month, print a readable report, then let you type follow-up questions in plain text.
它会依次询问生日、性别、可选流年/流月，然后输出可读解盘，并允许你继续用普通文字追问。

Run a structured analysis:
运行结构化分析：

```powershell
.\run_master.cmd --year 1990 --month 1 --day 1 --hour 0 --minute 0 --longitude 120 --gender 男
```

Ask through the dialogue layer:

```powershell
.\run_master.cmd --year 1990 --month 1 --day 1 --hour 0 --longitude 120 --gender 男 --question 事业怎么样
```

Print only the conversational answer:

```powershell
.\run_master.cmd --year 1990 --month 1 --day 1 --hour 0 --longitude 120 --gender 男 --question 事业怎么样 --reply-only
```

Print a readable full report for non-specialist testing:

```powershell
.\run_report.cmd --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --target-month 7
```

This report is the current product-facing text layer. It translates the structured chart, rule signals, luck-cycle windows, and safety guards into a plain-language reading.

The output schema is `ai-bazi-master.v1`:

- `input`: birth data, gender, longitude, and time policy
- `chart`: pillars, day master, month command, true solar time, ten gods
- `facts`: deterministic facts such as relations, dayun, tiaohou, liuqin
- `assessments`: evidence-bearing rule results by domain
- `evidence`: normalized source/rule/matched/uncertainty records
- `conversation_hints`: safe prompts and boundaries for the AI layer

Run rule regression checks:

```powershell
.\run_rule_validation.cmd --cases .\rule_cases.json
```

Run the full local validation suite:

```powershell
.\run_all_validation.cmd
```

Run the final project acceptance contract:

```powershell
.\run_project_status_validation.cmd
```

Run annual luck-cycle dry-run checks:

```powershell
.\run_luck_validation.cmd
```

Run monthly window checks:

```powershell
.\run_month_validation.cmd
```

Run structured luck guard checks:

```powershell
.\run_luck_guard_validation.cmd
```

Run dialogue end-to-end guard checks:

```powershell
.\run_dialogue_guard_validation.cmd
```

Run interactive console smoke checks:

```powershell
.\run_interactive_validation.cmd
```

Run readable report checks:

```powershell
.\run_report_validation.cmd
```

Run guarded daily date-candidate filter checks:

```powershell
.\run_daily_filter_validation.cmd
```

Run case-library intake checks:

```powershell
.\run_case_library_validation.cmd
```

Run case-library guardrail negative checks:

```powershell
.\run_case_library_negative_validation.cmd
```

`run_project_status_validation.cmd` checks the project-level contract: required
commands are present in the full suite, key rule/phrase assets are loadable,
daily filtering remains explicit-only and guarded, and reference cases are not
promoted to automatic regression.

Run phrase safety checks:

```powershell
.\run_phrase_validation.cmd
```

Run candidate calendar boundary checks:

```powershell
.\run_calendar_validation.cmd
```

`validate_calendar.py` uses the 23:00 Zi-hour day boundary candidate set by
default.  Solar-term precision gaps are reported as `KNOWN_GAP` unless
`--strict` is passed; this keeps the issue visible without mixing calendar
engine repair into interpretation-rule validation.

Evaluate a specific year through the master interface:

```powershell
.\run_master.cmd --year 1990 --month 1 --day 1 --hour 12 --longitude 120 --gender 男 --target-year 2028 --question 2028年事业怎么样 --reply-only
```

Evaluate guarded daily date candidates inside a specific flow-month window:

```powershell
.\run_master.cmd --year 1990 --month 1 --day 1 --hour 12 --longitude 120 --gender 男 --target-year 2028 --target-month 7
```

`target_month` is optional, uses the 1-12 solar flow-month index, and only
works when `target_year` is also present.
When `target_month` is omitted, the master output does not include
`daily_filter`.  The daily filter is not a daily prediction engine; it only
returns guarded date candidates inside an already-triggered annual/monthly
window.  v1 supports guarded candidates for activated branch clashes, repeated
monthly palace triggers, and existing combination windows.  It does not scan all
days or create auspicious/inauspicious date labels.
Candidate dates use solar-term flow-month boundaries and exclude partial
boundary days at date precision.

## Current Rule and Safety Layer

The current stable layer has moved beyond rule storage.  `RuleEngine` now emits
executable candidate signals for the core pattern and medicine rules, including
`pattern_004` through `pattern_009` and `medicine_type_001` through
`medicine_type_009`.  These signals include:

- `executable_rule_ids`
- `executable_notes`
- `executable_manual_review_required`
- evidence records

Candidate and manual-review rules stay conservative.  They describe structure,
review points, and attention windows; they do not produce absolute good/bad or
event-certain conclusions.

Luck-cycle output is guarded by `bazi_master/luck_guard.py`.  Annual triggers,
monthly windows, and daily date candidates carry structured safety fields:

- `risk_guard_required`
- `risk_level`
- `safe_wording`
- `forbidden_assertions`
- `output_allowed`
- `direct_expression_allowed`

`PhraseEngine` consumes these guard fields.  If direct expression is blocked it
uses fallback or conservative wording, and if output is blocked it returns a
guarded block message.  It now consumes annual triggers, monthly windows, and
guarded `daily_filter` candidates through the same path.  `DialogueEngine` uses the safe phrase text returned by
`PhraseEngine`; end-to-end snapshots are covered by
`run_dialogue_guard_validation.cmd`.

Annual luck-cycle output also marks same-palace repeat activation when multiple
annual/dayun triggers touch the same original pillar.  The configured bonus is
an attention-priority bonus only; it is not a good/bad or event-certainty score.
Monthly windows use the same boundary: repeated upper triggers for the same
original pillar are consolidated into one guarded monthly rule with
`repeat_context`, so the report can show repeated activation without duplicating
the same window signal.
The annual/dayun trigger set includes guarded dayun checks for branch clashes,
fuyin, dayun tianke-dichong (`luck_006`), plus low-weight year/hour branch
clashes (`luck_007`/`luck_008`).  These are timing attention signals only and
always pass through the guard layer.
Annual flow-year combinations also include guarded sanhe/sanhui completion
(`year_007`), kept as a theme-aggregation signal rather than a success/failure
judgment.
Annual branch-only fuyin is available as downgraded `year_008`.  It marks a
repeated original branch as a review point, not as a full pillar fuyin or an
event conclusion.

## Daily Filter Boundary

`DailyFilterEngine` is a guarded date-candidate filter, not a standalone daily
fortune engine.

- It is only attached to `MasterEngine` when both `target_year` and
  `target_month` are explicitly provided.
- It never runs by default for a whole year.
- It does not label dates as auspicious, inauspicious, or disaster dates.
- It does not claim that a specific event will happen on a specific day.
- Every date candidate goes through `guard_daily_candidates(...)`.
- Candidate ranges are full dates inside the solar-term month; boundary days are
  excluded until time-of-day filtering is implemented.

## Mingli Case Library

The lightweight intake files live under `case_library/`:

- `gold_cases.json`: strict automatic-regression candidates. This file may stay
  empty until cases meet the gold policy.
- `reference_cases.json`: public or otherwise useful reference cases that are
  not yet safe for automatic regression.
- `youtube_candidate_sources.json`: YouTube/source leads. Most stay candidate
  sources unless complete birth data and externally verifiable events are
  present.
- `excluded_cases.json`: rejected or blocked intake items that must not be
  promoted until the exclusion reason is resolved.

Gold case admission requires complete birth year/month/day/hour/minute, birth
time that is not merely inferred or rectified, at least three known events, at
least one event with year/month/day, externally sourced events, and validated
calendar/timezone support for automatic regression. Reference cases are not
regression cases unless promoted through this policy. Validate the staging
library with:

```powershell
.\run_case_library_validation.cmd
```

Guardrail negative tests are also available:

```powershell
.\run_case_library_negative_validation.cmd
```

Step 8 adds a structured case library in `mingli_cases.json`.  It is meant for
anonymized real cases, consented public cases, and synthetic seed fixtures used
to train and check interpretation quality.

Validate the case-library structure:

```powershell
.\run_mingli_validation.cmd --cases .\mingli_cases.json
```

Optionally compare recorded chart expectations against the current
`MasterEngine` output:

```powershell
.\run_mingli_validation.cmd --cases .\mingli_cases.json --check-chart
```

Check judgement summaries and evidence keys against the current rule layer:

```powershell
.\run_mingli_validation.cmd --cases .\mingli_cases.json --check-rules
```

Each case should keep these parts filled:

- `birth`: solar birth data, gender, longitude, and time fields
- `validation_priority`: P0/P1/P2/P3 machine-use priority
- `birth_time_reliability`: source level, precise-validation flag, dispute, and note
- `expected_chart`: optional stable chart fields for regression checks
- `themes`: business, wealth, marriage, health, luck-cycle, or core rule tags
- `life_events`: observed facts, with period, theme, outcome, and confidence
- `questions`: sample user questions and expected answer focus
- `judgement_notes`: expected rule summaries, evidence keys, and quality target
- `review`: seed/draft/verified lifecycle status

Priority policy:

- `P0`: AA or birth-record-grade time; may enter automatic regression tests.
- `P1`: A/B or otherwise credible time; use with caution or manual review.
- `P2`: weak/controversial time; use only as interpretation-quality reference.
- `P3`: missing birth time; use only for event labels, not precise chart checks.

Chinese public-figure records collected from public sources are kept under
`public_case_candidates` until manually promoted into formal `cases`.

## Validation Harness

This workspace contains a small standard-library validator for comparing a
local Bazi script with `https://zydx.top/paipan.php`.

See `RULES.md` for the supported date range and validation policy. In short,
the project targets zydx-compatible validation from `1902-03-01` onward.
`1902-01-01` through `1902-02-28` are known exceptions and are not guaranteed
to match `zydx.top`.

Fetch one standard answer:

```powershell
$env:PYTHONIOENCODING='utf-8'
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\zydx_client.py --year 1990 --month 1 --day 1 --hour 0 --minute 0 --sex 1
```

Run comparisons:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\validate_bazi.py --cases .\cases.json --local-cmd "python C:\path\to\your_bazi_script.py"
```

This repo also includes `local_bazi_adapter.py`, which connects the validator to
the bundled `bazi_legacy/bazi_engine.py`.  Developers can override the engine
location with `BAZI_ENGINE_DIR` if they keep a local copy elsewhere:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\validate_bazi.py --cases .\cases.json --local-cmd "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe .\local_bazi_adapter.py"
```

The local command receives each case as JSON on stdin and should print JSON:

```json
{
  "pillars": {
    "year": "己巳",
    "month": "丙子",
    "day": "丙寅",
    "hour": "戊子"
  }
}
```

Once your existing排盘脚本 is available, the next step is to adapt either the
script itself or a thin wrapper so it emits this JSON shape, then fix any
pillar mismatches case by case.

For zydx comparison, the adapter passes `longitude=120` so your engine uses
clock time rather than shifting to a different true-solar-time longitude.
