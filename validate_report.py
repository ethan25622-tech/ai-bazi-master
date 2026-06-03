"""Validate readable report output for non-specialist testing."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from bazi_master.master_engine import MasterEngine
from bazi_master.report_engine import ReportEngine


REQUIRED_SECTIONS = [
    "命盘基本信息",
    "判断强度分级",
    "格局、强弱与用神",
    "综合解盘结论",
    "判断依据与交叉验证",
    "性格与能力模式",
    "事业方向",
    "财运与赚钱方式",
    "婚恋与关系",
    "健康与生活习惯提醒",
    "生活应用与传统取象",
    "过往经历校验",
    "取舍点与未来岁运应对",
    "大运与命局结合",
    "未来年份提示与趋避建议",
    "大运、流年、流月与流日候选",
    "你可以继续怎么问",
]

FORBIDDEN_TERMS = [
    "一定离婚",
    "一定死亡",
    "一定破产",
    "一定重病",
    "必死",
    "必有灾",
    "建议买入",
    "建议卖出",
    "诊断为",
    "治疗方案",
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    analysis = MasterEngine().analyze(
        1990,
        1,
        1,
        12,
        0,
        longitude=120.0,
        gender="男",
        target_year=2028,
        target_month=7,
    )
    report = ReportEngine().render(analysis)
    failures: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in report:
            failures.append(f"missing report section: {section}")
    for term in FORBIDDEN_TERMS:
        if term in report:
            failures.append(f"report contains forbidden term: {term}")
    for term in ("四柱为", "日主是", "性别口径", "不能默认按男命", "相对稳定", "倾向明显", "复核点", "格局判断", "分析入口", "不硬说已经成格", "综合解读层", "结论：", "现实表现", "依据摘要", "事业判断", "生活应用与传统取象", "适合的工作类型", "适合的居住/办公环境", "适合参考的颜色", "可用的日常物件", "结合大运调整生活取象", "过往经历校验", "直接校验", "当年可能不顺", "取舍点", "参考依据", "结合未来年份看", "大运与命局结合", "阶段主题", "如何作用到命局", "好的用法", "容易卡住", "事业怎么用", "财务怎么用", "关系怎么处理", "具体做法", "推进/收缩规则", "这步运里更要看的年份", "阶段策略", "本年行动重点", "本年触发", "大运背景", "可以把握", "需要特别注意", "压力点", "解药/做法", "具体可以做", "第一步", "不建议", "现实校验点", "需要避开的坑", "岁运触发", "流月窗口"):
        if term not in report:
            failures.append(f"report missing readable anchor: {term}")
    if len(report) < 1200:
        failures.append("report is too short to be a useful full reading")

    result = {
        "passed": not failures,
        "length": len(report),
        "failures": failures,
        "preview": report[:1000],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    Path("report_validation_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    Path("sample_report.md").write_text(report, encoding="utf-8")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
