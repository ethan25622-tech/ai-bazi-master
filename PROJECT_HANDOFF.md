# AI Bazi Master Handoff / 项目交接说明

## Current State / 当前状态

The command-center layer is stable and validation-gated.
当前项目框架层已经稳定，并且有验证命令守门。

- Legacy chart calculation is bundled in `bazi_legacy/`; `BAZI_ENGINE_DIR` can override it for local development.
- 旧版排盘脚本已内置在 `bazi_legacy/`；本地开发时也可以用 `BAZI_ENGINE_DIR` 覆盖。
- Stable project interface lives in `bazi_master/`.
- 稳定项目接口在 `bazi_master/`。
- Core executable rule signals are connected through `RuleEngine`.
- 核心可执行规则信号已接入 `RuleEngine`。
- Annual, monthly, and explicit daily-filter timing outputs are guarded.
- 大运/流年、流月，以及显式流日筛选输出都已接入安全守门。
- Phrase and dialogue layers consume guard fields and block direct high-risk expression.
- 表达层和对话层会消费 guard 字段，阻止高风险直断表达。
- Case-library intake is governed, with `gold_cases.json` intentionally empty.
- 命例库入库已有规则，当前 `gold_cases.json` 为空是有意保持的正常状态。

## Stable Validation Gate / 稳定验证命令

Use this as the main acceptance command:
主要验收命令：

```powershell
.\run_all_validation.cmd
```

The full suite currently covers:
完整验证目前覆盖：

- rule execution
- 规则执行
- calendar boundary patch validation
- 历法边界补丁验证
- annual luck-cycle validation
- 大运/流年验证
- monthly window validation
- 流月窗口验证
- luck guard validation
- 岁运 guard 验证
- guarded daily-filter validation
- 流日候选筛选 guard 验证
- phrase safety validation
- 表达安全验证
- DialogueEngine guard snapshots
- DialogueEngine 端到端 guard 快照
- case-library intake validation
- 命例库入库验证
- case-library negative guardrails
- 命例库反例守门
- Mingli seed case validation
- 命理种子样例验证
- project-level status contract
- 项目级状态契约

## Current Rule Surface / 当前规则范围

Core rule execution includes:

- `pattern_004` through `pattern_009`
- `medicine_type_001` through `medicine_type_009`

Luck-cycle execution includes:

- `luck_003` through `luck_008`
- `year_001` through `year_008`
- `luck_guard_001`
- `luck_guard_002`

Daily filtering is intentionally narrow:
流日筛选刻意保持窄范围：

- only appears when both `target_year` and `target_month` are provided
- 只有同时提供 `target_year` 和 `target_month` 时才出现
- only filters dates inside upper annual/monthly trigger windows
- 只在上层大运/流年/流月已触发的窗口内筛日期
- does not perform daily fortune-telling
- 不做每日泛断
- does not label dates as good, bad, auspicious, inauspicious, or disaster dates
- 不把日期标成吉日、凶日、灾日

## Guard Contract / 安全守门契约

Guarded timing outputs must keep these fields:

- `risk_guard_required`
- `risk_level`
- `safe_wording`
- `forbidden_assertions`
- `output_allowed`
- `direct_expression_allowed`

If a rule is a candidate or manual-review signal, the output must stay
conservative and avoid absolute event claims.
如果某条规则只是候选或人工复核信号，输出必须保持保守，避免绝对事件断语。

Forbidden output classes remain:
禁止输出类型包括：

- medical diagnosis
- 医学诊断
- investment advice
- 投资买卖建议
- certain divorce, death, disease, bankruptcy, accident, lawsuit, or disaster claims
- 一定离婚、死亡、重病、破产、事故、诉讼、灾祸等确定断语
- daily generic prediction
- 每日泛断
- specific-date certainty
- 某日一定发生某事

## Case Library Policy / 命例库规则

`case_library/gold_cases.json` may remain empty.  This is normal until a case
meets all gold criteria:
`case_library/gold_cases.json` 可以保持为空。在案例满足全部 gold 标准之前，
这属于正常状态：

- complete birth year, month, day, hour, and minute
- birth time not inferred or rectified
- at least three known events
- at least one known event with year, month, and day
- external source coverage for known events
- validated timezone and calendar support for automatic regression

Public overseas cases remain reference-only until international timezone and
calendar support is explicitly validated.
海外公开人物案例在国际时区/历法支持明确验证前，仍保持 reference-only。

## Remaining Work / 后续工作

These items are intentionally not completed in the current stable layer because
they require new source material, external verification, or larger product
decisions:
下面这些事项暂未放入当前稳定层，因为它们需要新资料、外部验证或更大的产品决策：

- collect and vet real gold cases
- validate international timezone/calendar support
- add broader real-case guard matrices
- extend daily filtering beyond v1 only after guard behavior remains stable
- add richer user-facing product workflows on top of the stable schema

## Do Not Regress / 不要回退的边界

- Do not promote public reference cases into automatic regression without gold
  criteria.
- Do not make `daily_filter` appear without explicit `target_month`.
- Do not interpret `trigger_score` as good/bad or certainty.
- Do not bypass `PhraseEngine` guard consumption in dialogue output.
- Do not modify `1902-01-01` through `1902-02-28` compatibility unless a new
  calendar support decision is made.
