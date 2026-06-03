"""Readable narrative report generator for the stable analysis schema."""

from __future__ import annotations

from typing import Any

from .judgment_synthesizer import JudgmentSynthesizer
from .knowledge_base import index_rules, load_core_rules, load_luck_rules, load_monthly_rules
from .lifestyle_advice import LifestyleAdviceEngine
from .luck_advice import LuckAdviceEngine
from .reading_synthesizer import ReadingSynthesizer


class ReportEngine:
    """Render a human-readable Bazi report from `MasterEngine.analyze(...)`.

    This layer does not create new rules.  It translates the existing chart,
    rule assessments, luck-cycle windows, and guard fields into plain Chinese
    that can be reviewed by non-specialists.
    """

    def __init__(self) -> None:
        self.rule_index = index_rules(load_core_rules(), load_luck_rules(), load_monthly_rules())
        self.judgment_synthesizer = JudgmentSynthesizer()
        self.reading_synthesizer = ReadingSynthesizer()
        self.luck_advice = LuckAdviceEngine()
        self.lifestyle_advice = LifestyleAdviceEngine()

    def render(self, analysis: dict[str, Any]) -> str:
        sections = [
            self._header(analysis),
            self._chart_summary(analysis),
            self._key_points(analysis),
            self._judgment_strength(analysis),
            self._structure_summary(analysis),
            self._readable_synthesis(analysis),
            self._evidence_basis(analysis),
            self._personality_and_capacity(analysis),
            self._career(analysis),
            self._wealth(analysis),
            self._marriage(analysis),
            self._health(analysis),
            self._lifestyle_application(analysis),
            self._past_validation(analysis),
            self._tradeoff_advice(analysis),
            self._dayun_integration(analysis),
            self._annual_advice(analysis),
            self._luck_cycle(analysis),
            self._closing(analysis),
        ]
        return "\n\n".join(section for section in sections if section.strip())

    def _key_points(self, analysis: dict[str, Any]) -> str:
        """Summarize the chart in plain language before detailed sections."""

        assessments = analysis.get("assessments", {})
        facts = analysis.get("facts", {})
        pattern = assessments.get("pattern", {})
        strength = assessments.get("strength", {})
        tiaohou = facts.get("tiaohou_yong_shen", {})
        relations = facts.get("relation_dynamics", {})
        pattern_ids = set(pattern.get("executable_rule_ids") or [])

        pattern_text = self._summary(pattern)
        strength_text = self._summary(strength)
        provisional = pattern.get("provisional_reasons") or []
        if provisional:
            pattern_text = f"{pattern_text}（先作格局入口，不作铁定成格）"
        lines = [
            f"这张盘不是单看一个神煞，也不是为了有结果而硬安格局；先把 **{pattern_text}** 作为分析入口，再看日主强弱为 **{strength_text}**。",
        ]
        if provisional:
            lines.append(f"格局降级原因：{self._join(provisional)}。所以后文会更重视交叉验证，而不是只按格局名下结论。")
        if isinstance(tiaohou, dict):
            first = self._join(tiaohou.get("首选用神", []))
            second = self._join(tiaohou.get("次选用神", []))
            present = self._join(tiaohou.get("原局已透首选", []))
            if first:
                text = f"调候上优先看 {first}"
                if second:
                    text += f"，其次看 {second}"
                if present:
                    text += f"；原局已经透出 {present}，说明这个方向不是完全没有根。"
                else:
                    text += "。"
                lines.append(text)

        if "pattern_005" in pattern_ids:
            lines.append("食神格信号出现时，重点不是玄乎地说“有福”，而是看一个人能不能把技能、经验、内容、服务稳定输出，并由此形成回报。")
        if "pattern_004" in pattern_ids:
            lines.append("印星信号出现时，说明学习、资质、贵在长期积累的能力值得看；但如果同时有财星破印或偏印夺食，就要看资源和输出之间是否互相打架。")
        if "pattern_007" in pattern_ids:
            lines.append("伤官信号出现时，表达和主见会更强；用得好是创造力，用得急就容易和规则、流程、权威发生摩擦。")
        if "pattern_009" in pattern_ids:
            lines.append("建禄月劫信号出现时，自主性和行动力会更强，但合作边界、资源分配、同辈竞争要讲清楚。")

        relation_text = self._relation_plain_text(relations)
        if relation_text:
            lines.append(relation_text)

        lines.append("所以测试这张盘时，不要只问“好不好”，更适合问：靠什么能力吃饭、适合什么工作环境、资源和表达是否冲突、哪几年哪些主题被引动。")
        return "## 本盘重点先看\n\n" + "\n".join(f"- {line}" for line in self._dedupe(lines))

    def _judgment_strength(self, analysis: dict[str, Any]) -> str:
        synthesized = self.judgment_synthesizer.synthesize(analysis)
        groups = [
            ("相对稳定，可以放心作为底座", synthesized.get("stable_observations", [])),
            ("倾向明显，但仍需结合现实验证", synthesized.get("supported_tendencies", [])),
            ("只作为复核点，暂不下定论", synthesized.get("review_points", [])),
        ]
        lines = [
            "这一段把系统能说的话分级，避免把所有信号都混成同一种确定度。"
        ]
        for title, items in groups:
            if not items:
                continue
            lines.append(f"**{title}**")
            for item in items[:5]:
                lines.append(f"- {item.get('title')}：{item.get('finding')}（边界：{item.get('boundary')}）")
        return "## 判断强度分级\n\n" + "\n".join(lines)

    def _header(self, analysis: dict[str, Any]) -> str:
        birth = analysis.get("input", {})
        gender = birth.get("gender") or "未填"
        minute = int(birth.get("minute") or 0)
        target_year = birth.get("target_year")
        title = "AI 八字解盘报告"
        birth_line = (
            f"出生信息：{birth.get('year')}年{birth.get('month')}月{birth.get('day')}日 "
            f"{birth.get('hour')}:{minute:02d}，性别：{gender}，经度：{birth.get('longitude')}。"
        )
        if target_year:
            birth_line += f" 本次同时查看 {target_year} 年的岁运窗口。"
        gender_note = (
            "性别口径：以下六亲、婚恋和部分岁运解读按输入性别处理；"
            "若性别未填，只能作中性解读，不能默认按男命或女命套用。"
        )
        return (
            f"# {title}\n\n{birth_line}\n\n"
            "说明：以下内容是结构化规则解读，不把倾向当成确定事件。\n"
            f"{gender_note}"
        )

    def _chart_summary(self, analysis: dict[str, Any]) -> str:
        chart = analysis.get("chart", {})
        pillars = chart.get("pillars", {})
        ten_gods = chart.get("ten_gods", [])
        pillar_text = "，".join(f"{name} {value}" for name, value in pillars.items())
        day_master = chart.get("day_master") or "未识别"
        month_command = chart.get("month_command") or "未识别"
        gods = []
        for item in ten_gods:
            pillar = item.get("pillar")
            gan_god = item.get("gan_god")
            if pillar and gan_god:
                gods.append(f"{pillar}天干为{gan_god}")
        god_text = "；".join(gods[:4])
        return (
            "## 一、命盘基本信息\n\n"
            f"四柱为：{pillar_text}。\n"
            f"日主是 **{day_master}**，月令为 **{month_command}**。"
            f"{' 十神分布上，' + god_text + '。' if god_text else ''}\n"
            "这一段主要用于确认盘面，不直接代表吉凶。"
        )

    def _structure_summary(self, analysis: dict[str, Any]) -> str:
        assessments = analysis.get("assessments", {})
        pattern = assessments.get("pattern", {})
        strength = assessments.get("strength", {})
        tiaohou = assessments.get("tiaohou", {})
        yong_shen = assessments.get("yong_shen", {})
        chong_he = assessments.get("chong_he", {})

        lines = [
            f"格局判断：{self._summary(pattern)}",
            f"日主强弱：{self._summary(strength)}",
            f"调候状态：{self._summary(tiaohou)}",
            f"用神方向：{self._summary(yong_shen)}",
        ]
        provisional = pattern.get("provisional_reasons") or []
        if provisional:
            lines.append(f"格局降级原因：{self._join(provisional)}")
        pattern_notes = self._notes(pattern)
        if pattern_notes:
            lines.append(f"格局复核点：{pattern_notes}")
        chong_notes = self._notes(chong_he)
        if chong_notes:
            lines.append(f"合冲刑害复核点：{chong_notes}")
        translation = self._structure_translation(analysis)
        if translation:
            lines.append(translation)
        return (
            "## 二、格局、强弱与用神\n\n"
            + "\n".join(f"- {line}" for line in lines)
            + "\n\n"
            "解读：这部分是整张命盘的骨架。现在系统会把格局和病药作为“分析入口/候选/复核点”输出，"
            "也就是说，它提示哪些方向值得看；如果证据不足，就宁可降级看待，不硬说已经成格。"
        )

    def _readable_synthesis(self, analysis: dict[str, Any]) -> str:
        synthesis = self.reading_synthesizer.synthesize(analysis)
        topics = synthesis.get("topics", {})
        lines = [synthesis.get("policy", "以下为综合解读层。")]
        overall = synthesis.get("overall", [])
        if overall:
            lines.append("**总判断**")
            for item in overall[:4]:
                lines.append(f"- {item}")

        topic_labels = [
            ("personality", "性格与能力"),
            ("career", "事业与工作方式"),
            ("wealth", "财务与资源"),
            ("relationship", "婚恋/合作关系"),
            ("health", "健康与生活节奏"),
        ]
        for key, label in topic_labels:
            topic = topics.get(key, {})
            if not isinstance(topic, dict):
                continue
            lines.append(f"**{label}**")
            for text in topic.get("conclusion", [])[:3]:
                lines.append(f"- 结论：{text}")
            manifestations = topic.get("likely_manifestations", [])
            if manifestations:
                lines.append(f"- 现实表现：{self._join(manifestations[:2])}")
            suggestions = topic.get("suggestions", [])
            if suggestions:
                lines.append(f"- 建议：{self._join(suggestions[:2])}")
            avoid = topic.get("avoid", [])
            if avoid:
                lines.append(f"- 避免：{self._join(avoid[:2])}")
            evidence = topic.get("evidence", [])
            if evidence:
                lines.append(f"- 依据摘要：{self._join(evidence[:3])}")
            boundary = topic.get("boundary")
            if boundary:
                lines.append(f"- 边界：{boundary}")
        return "## 三、综合解盘结论\n\n" + "\n".join(lines)

    def _evidence_basis(self, analysis: dict[str, Any]) -> str:
        assessments = analysis.get("assessments", {})
        blocks = [
            self._basis_block(
                "格局主线",
                assessments.get("pattern", {}),
                "先看月令和透干，再看是否有成格、破格、救应。这里不会只凭一个十神下结论。",
            ),
            self._basis_block(
                "强弱判断",
                assessments.get("strength", {}),
                "把得令、根气、天干助泄拆开看；如果信号互相抵消，就保留为中和或待复核。",
            ),
            self._basis_block(
                "调候与用神",
                assessments.get("tiaohou", {}),
                "调候只说明寒暖燥湿的优先方向，还要和格局、强弱互相校验。",
            ),
            self._basis_block(
                "合冲刑害",
                assessments.get("chong_he", {}),
                "先确认合冲刑害是不是客观存在，再看它落在哪个柱位、是否牵动月令或用神。",
            ),
            self._basis_block(
                "财务与清浊",
                assessments.get("wealth", {}),
                "财富部分不直接断收入，而是看财星、格局清浊、资源取舍是否互相支持。",
            ),
        ]
        blocks = [block for block in blocks if block]
        if not blocks:
            return ""
        intro = (
            "这一段专门说明“为什么这样看”。系统不会拿某一句资料单独断事，"
            "而是把盘面事实、资料库规则和其他模块的结果放在一起互相校验。"
        )
        return "## 四、判断依据与交叉验证\n\n" + intro + "\n\n" + "\n\n".join(blocks)

    def _basis_block(self, label: str, item: dict[str, Any], method: str) -> str:
        if not isinstance(item, dict):
            return ""
        evidences = [ev for ev in item.get("evidence", []) if isinstance(ev, dict)]
        sources = self._basis_sources(item, evidences)
        matched = self._basis_matched(evidences)
        rules = self._basis_rules(item)
        boundary = self._basis_boundary(item, evidences)

        lines = [f"**{label}**"]
        lines.append(f"- 判断方法：{method}")
        if matched:
            lines.append(f"- 盘面依据：{matched}")
        if sources:
            lines.append(f"- 资料依据：{sources}")
        if rules:
            lines.append(f"- 交叉验证：{rules}")
        if boundary:
            lines.append(f"- 结论边界：{boundary}")
        return "\n".join(lines)

    def _basis_sources(self, item: dict[str, Any], evidences: list[dict[str, Any]]) -> str:
        sources: list[str] = []
        rule_source = item.get("rule_source")
        if isinstance(rule_source, list):
            sources.extend(str(source) for source in rule_source if source)
        elif rule_source:
            sources.append(str(rule_source))
        for ev in evidences:
            source = ev.get("source")
            if source:
                sources.append(str(source))
        return self._join(self._dedupe(sources)[:4])

    def _basis_rules(self, item: dict[str, Any]) -> str:
        rule_ids = [str(rule_id) for rule_id in item.get("executable_rule_ids", []) if rule_id]
        notes = [str(note) for note in item.get("executable_notes", []) if note]
        names = []
        for rule_id in rule_ids:
            rule = self.rule_index.get(rule_id, {})
            name = rule.get("name") or rule_id
            status = rule.get("status")
            if status in {"candidate_rule", "manual_review"}:
                names.append(f"{name}作为候选/复核信号")
            else:
                names.append(str(name))
        parts = [*names[:4], *notes[:3]]
        if not parts:
            return ""
        return self._join(self._dedupe(parts))

    def _basis_boundary(self, item: dict[str, Any], evidences: list[dict[str, Any]]) -> str:
        boundaries: list[str] = []
        if item.get("manual_review_required") or item.get("executable_manual_review_required"):
            boundaries.append("需要结合全局复核，不按单一规则定吉凶。")
        for ev in evidences:
            uncertainty = ev.get("uncertainty")
            if uncertainty:
                boundaries.append(str(uncertainty))
        return "；".join(self._dedupe(boundaries)[:2])

    def _basis_matched(self, evidences: list[dict[str, Any]]) -> str:
        facts: list[str] = []
        for ev in evidences[:4]:
            matched = ev.get("matched")
            if not isinstance(matched, dict):
                continue
            facts.extend(self._flatten_matched(matched))
            if len(facts) >= 6:
                break
        return self._join(self._dedupe(facts)[:6])

    def _flatten_matched(self, matched: dict[str, Any]) -> list[str]:
        facts: list[str] = []
        preferred = [
            "日主",
            "月令",
            "月令本气",
            "月令十神",
            "月令主气十神",
            "本气透干",
            "首选用神",
            "次选用神",
            "原局已透首选",
            "成败状态",
            "破格因素",
            "护卫候选",
            "透干十神计数",
        ]
        for key in preferred:
            if key in matched:
                facts.append(f"{key}={self._format_value(matched[key])}")

        strength_keys = ["得令", "有根", "有助"]
        for key in strength_keys:
            value = matched.get(key)
            if isinstance(value, dict):
                conclusion = value.get("结论")
                basis = value.get("依据") or value.get("根气列表") or value.get("帮扶")
                if conclusion:
                    facts.append(f"{key}={conclusion}（{self._format_value(basis)}）")

        facts_node = matched.get("facts")
        if isinstance(facts_node, dict):
            for key in ["天干五合", "地支相冲", "地支六合", "地支相刑", "地支相害"]:
                value = facts_node.get(key)
                if value:
                    facts.append(f"{key}={self._format_value(value)}")

        dynamic = matched.get("dynamic") or matched.get("动态判断")
        if isinstance(dynamic, dict):
            clashes = dynamic.get("相冲分析") or []
            for clash in clashes[:2]:
                if isinstance(clash, dict) and clash.get("冲"):
                    facts.append(
                        f"{clash.get('冲')}，位置={clash.get('位置', '待定')}，冲力={clash.get('冲力', '待定')}"
                    )

        relation_facts = matched.get("关系事实")
        if isinstance(relation_facts, dict):
            for key, value in relation_facts.items():
                if value:
                    facts.append(f"{key}={self._format_value(value)}")

        return facts

    def _personality_and_capacity(self, analysis: dict[str, Any]) -> str:
        assessments = analysis.get("assessments", {})
        pattern_ids = set(assessments.get("pattern", {}).get("executable_rule_ids") or [])
        notes = []
        if "pattern_004" in pattern_ids:
            notes.append("印格信号较明显，适合靠学习、资质、专业承接和稳定方法积累优势。")
        if "pattern_005" in pattern_ids:
            notes.append("食神格信号提示稳定输出、技能沉淀、作品表达和服务能力值得重视。")
        if "pattern_006" in pattern_ids:
            notes.append("七杀格信号提示承压、竞争、执行力和规则边界是重要主题。")
        if "pattern_007" in pattern_ids:
            notes.append("伤官格信号提示表达、创新、质疑规则和自我主张较强，但要注意表达与规则之间的张力。")
        if "pattern_009" in pattern_ids:
            notes.append("建禄月劫信号提示自主性、行动力、同辈竞争和合作边界是重点。")
        if not notes:
            notes.append("从当前规则看，性格与能力模式需要结合格局、强弱、十神分布继续综合判断。")
        return "## 五、性格与能力模式\n\n" + "\n".join(f"- {line}" for line in notes)

    def _career(self, analysis: dict[str, Any]) -> str:
        career = analysis.get("assessments", {}).get("career", {})
        pattern = analysis.get("assessments", {}).get("pattern", {})
        notes = [
            self._summary(career),
            "事业判断优先看格局是否能承接、用神是否清楚，以及官杀、印、食伤之间是否形成有效配合。",
        ]
        executable = set(pattern.get("executable_rule_ids") or [])
        if "pattern_004" in executable:
            notes.append("适合重视专业资质、知识沉淀、规范平台、长期信用的方向。")
        if "pattern_005" in executable:
            notes.append("适合把技能、内容、经验或服务做成可见成果，靠持续输出打开空间。")
        if "pattern_006" in executable:
            notes.append("适合有目标、有压力、有规则的环境，但不宜把压力直接理解成坏事。")
        if "pattern_007" in executable:
            notes.append("表达和创意是优势，但正式场合要注意流程、证据和权责边界。")
        return "## 六、事业方向\n\n" + "\n".join(f"- {line}" for line in self._dedupe(notes))

    def _wealth(self, analysis: dict[str, Any]) -> str:
        wealth = analysis.get("assessments", {}).get("wealth", {})
        notes = [
            self._summary(wealth),
            "财运这里不直接断收入高低，而是看赚钱方式、资源取舍、结构是否清楚。",
        ]
        wealth_notes = self._notes(wealth)
        if wealth_notes:
            notes.append(f"财富复核点：{wealth_notes}")
        if "medicine_type_004" in set(wealth.get("executable_rule_ids") or []):
            notes.append("清浊病药提示：财务或事业选择上要先分清主次，不适合什么都抓。")
        return "## 七、财运与赚钱方式\n\n" + "\n".join(f"- {line}" for line in self._dedupe(notes))

    def _marriage(self, analysis: dict[str, Any]) -> str:
        marriage = analysis.get("assessments", {}).get("marriage", {})
        chong_he = analysis.get("assessments", {}).get("chong_he", {})
        notes = [
            self._summary(marriage),
            "婚恋不作确定事件判断，重点看夫妻宫、配偶星、合冲关系与现实互动方式。",
        ]
        chong_notes = self._notes(chong_he)
        if chong_notes:
            notes.append(f"关系互动复核点：{chong_notes}")
        return "## 八、婚恋与关系\n\n" + "\n".join(f"- {line}" for line in self._dedupe(notes))

    def _health(self, analysis: dict[str, Any]) -> str:
        health = analysis.get("assessments", {}).get("health", {})
        facts = analysis.get("facts", {}).get("health_mapping", {})
        notes = [
            self._summary(health),
            "健康部分只按传统对应关系做生活习惯提醒，不做医学诊断，也不替代医生意见。",
        ]
        day_mapping = facts.get("日主对应") if isinstance(facts, dict) else None
        if isinstance(day_mapping, dict):
            notes.append(
                f"日主对应的传统观察点：{day_mapping.get('脏腑')}、{day_mapping.get('身体部位')}。"
            )
        return "## 九、健康与生活习惯提醒\n\n" + "\n".join(f"- {line}" for line in self._dedupe(notes))

    def _lifestyle_application(self, analysis: dict[str, Any]) -> str:
        birth = analysis.get("input", {})
        start = birth.get("target_year")
        try:
            start_year = int(start) if start else None
        except (TypeError, ValueError):
            start_year = None
        advice = self.lifestyle_advice.build(analysis, start_year=start_year)
        lines = [advice.get("policy", "以下为传统生活取象建议。")]

        elements = advice.get("useful_elements", [])
        if elements:
            lines.append(f"- 当前优先取象：{self._join(elements)}。")
        careers = advice.get("career_types", [])
        if careers:
            lines.append(f"- 适合的工作类型：{self._join(careers[:10])}。")
        work_environment = advice.get("work_environment", [])
        if work_environment:
            lines.append(f"- 适合的工作环境：{self._join(work_environment[:8])}。")

        residence = advice.get("residence_guidance", {})
        if isinstance(residence, dict):
            environment = residence.get("environment", [])
            if environment:
                lines.append(f"- 适合的居住/办公环境：{self._join(environment[:8])}。")
            directions = residence.get("traditional_directions", [])
            if directions:
                lines.append(f"- 方位取象：{self._sentence_join(directions[:3])}")
            boundary = residence.get("boundary")
            if boundary:
                lines.append(f"- 方位边界：{boundary}")

        colors = advice.get("colors_and_materials", {})
        if isinstance(colors, dict):
            main_colors = colors.get("main_colors", [])
            materials = colors.get("materials", [])
            if main_colors:
                lines.append(f"- 适合参考的颜色：{self._join(main_colors[:8])}。")
            if materials:
                lines.append(f"- 适合参考的材质/物件感：{self._join(materials[:8])}。")
            if colors.get("usage"):
                lines.append(f"- 颜色用法：{colors.get('usage')}")

        objects = advice.get("daily_objects", [])
        if objects:
            lines.append(f"- 可用的日常物件：{self._join(objects[:10])}。")
        habits = advice.get("daily_habits", [])
        if habits:
            lines.append(f"- 日常增益做法：{self._join(habits[:8])}。")
        avoid = advice.get("avoid_overuse", [])
        if avoid:
            lines.append(f"- 不建议：{self._sentence_join(avoid[:4])}")

        dayun_adjustments = advice.get("dayun_lifestyle_adjustments", [])
        if dayun_adjustments:
            lines.append("**结合大运调整生活取象**")
            for item in dayun_adjustments[:3]:
                lines.append(f"- {item.get('period')}：{item.get('lifestyle_adjustment')}")
                if item.get("work_adjustment"):
                    lines.append(f"  - 工作：{item.get('work_adjustment')}")
                if item.get("money_adjustment"):
                    lines.append(f"  - 财务：{item.get('money_adjustment')}")
                if item.get("relationship_adjustment"):
                    lines.append(f"  - 关系：{item.get('relationship_adjustment')}")
                focus_years = item.get("focus_years", [])
                if focus_years:
                    year_text = []
                    for year in focus_years[:3]:
                        risk = self._join(year.get("risk_watch", []))
                        detail = f"{year.get('year')}年"
                        if year.get("action_focus"):
                            detail += f"看{self._strip_end_punctuation(year.get('action_focus'))}"
                        if risk:
                            detail += f"，防{self._strip_end_punctuation(risk)}"
                        year_text.append(detail)
                    lines.append(f"  - 这步运里优先观察：{self._join(year_text)}。")

        evidence = advice.get("evidence", [])
        if evidence:
            lines.append(f"- 参考依据：{self._join(evidence[:5])}。")
        return "## 十、生活应用与传统取象\n\n" + "\n".join(lines)

    def _past_validation(self, analysis: dict[str, Any]) -> str:
        validation = self.luck_advice.past_validation(analysis)
        years = validation.get("years", [])
        if not years:
            return ""
        lines = [
            validation.get("policy", "以下是过往经历校验点，供你核对准不准。"),
            "校验重点不是看有没有发生“大事”，而是看对应领域是否比平时更容易出现变化、牵动或重新安排。",
        ]
        for item in years:
            level = {
                "high_attention": "高关注",
                "medium_attention": "中关注",
                "low_attention": "低关注",
            }.get(item.get("attention_level"), "观察")
            lines.append(f"**{item.get('year')} 年（{item.get('year_pillar')}，{level}）**")
            triggers = item.get("year_specific_triggers", [])
            if triggers:
                lines.append(f"- 本年触发：{self._join(triggers[:3])}")
            background = item.get("dayun_background", [])
            if background:
                lines.append(f"- 大运背景：{self._join(background[:2])}")
            experiences = item.get("likely_past_experience", [])
            if experiences:
                lines.append("- 直接校验：")
                for experience in experiences[:4]:
                    lines.append(f"  - {experience}")
            challenges = item.get("possible_past_challenges", [])
            if challenges:
                lines.append("- 当年可能不顺/较卡的表现：")
                for challenge in challenges[:3]:
                    lines.append(f"  - {challenge}")
        return "## 十一、过往经历校验\n\n" + "\n".join(lines)

    def _tradeoff_advice(self, analysis: dict[str, Any]) -> str:
        birth = analysis.get("input", {})
        start = birth.get("target_year")
        try:
            start_year = int(start) if start else None
        except (TypeError, ValueError):
            start_year = None
        advice = self.luck_advice.structural_tradeoff_advice(analysis, start_year=start_year, years=8)
        items = advice.get("items", [])
        if not items:
            return ""
        lines = [advice.get("policy", "以下把命局中的取舍点接到未来大运流年。")]
        for item in items:
            lines.append(f"**取舍点：{item.get('topic')}**")
            lines.append(f"- 为什么要取舍：{item.get('structural_issue')} {item.get('why_it_matters')}")
            lines.append(f"- 总体做法：{item.get('future_strategy')}")
            sources = item.get("sources", [])
            if sources:
                lines.append(f"- 参考依据：{self._join(sources[:4])}")
            years = item.get("future_reference_years", [])
            if years:
                lines.append("- 结合未来年份看：")
                for year in years[:4]:
                    themes = self._join(year.get("matched_themes", [])) or "年度触发主题"
                    triggers = self._join(year.get("year_specific_triggers", [])[:2])
                    detail = f"{year.get('year')} 年（{year.get('year_pillar')}）：{themes}"
                    if triggers:
                        detail += f"；触发：{triggers}"
                    lines.append(f"  - {detail}。建议：{year.get('suggested_action')}")
        return "## 十二、取舍点与未来岁运应对\n\n" + "\n".join(lines)

    def _annual_advice(self, analysis: dict[str, Any]) -> str:
        birth = analysis.get("input", {})
        start = birth.get("target_year")
        try:
            start_year = int(start) if start else None
        except (TypeError, ValueError):
            start_year = None
        forecast = self.luck_advice.forecast_years(analysis, start_year=start_year, years=8)
        years = forecast.get("years", [])
        if not years:
            return ""
        lines = [
            forecast.get("policy", "以下只表示主题窗口、机会方向和避险做法，不代表吉凶或确定事件。")
        ]
        for item in years[:8]:
            level = {
                "high_attention": "高关注",
                "medium_attention": "中关注",
                "low_attention": "低关注",
            }.get(item.get("attention_level"), "观察")
            themes = self._join(item.get("main_themes", [])) or "主题待结合现实确认"
            lines.append(f"**{item.get('year')} 年（{item.get('year_pillar')}，{level}）**")
            lines.append(f"- 要注意的方面：{themes}。")
            focus = item.get("priority_focus")
            if focus:
                lines.append(f"- 本年行动重点：{focus}")
            year_triggers = item.get("year_specific_triggers", [])
            if year_triggers:
                lines.append(f"- 本年触发：{self._join(year_triggers[:3])}")
            dayun_background = item.get("dayun_background", [])
            if dayun_background:
                lines.append(f"- 大运背景：{self._join(dayun_background[:2])}")
            opportunities = item.get("opportunities", [])
            if opportunities:
                lines.append(f"- 可以把握：{self._join(opportunities[:2])}")
            pressure_points = item.get("pressure_points", [])
            if pressure_points:
                lines.append(f"- 需要特别注意：{self._join(pressure_points[:2])}")
            cautions = item.get("cautions", [])
            if cautions:
                lines.append(f"- 需要避开的坑：{self._join(cautions[:2])}")
            remedies = item.get("remedies", [])
            if remedies:
                lines.append(f"- 解药/做法：{self._join(remedies[:3])}")
            action_plan = item.get("action_plan", {})
            if isinstance(action_plan, dict):
                can_do = action_plan.get("can_do", [])
                first_steps = action_plan.get("first_steps", [])
                avoid = action_plan.get("avoid", [])
                checkpoints = action_plan.get("checkpoints", [])
                if can_do:
                    lines.append(f"- 具体可以做：{self._join(can_do[:2])}")
                if first_steps:
                    lines.append(f"- 第一步：{self._join(first_steps[:2])}")
                if avoid:
                    lines.append(f"- 不建议：{self._join(avoid[:2])}")
                if checkpoints:
                    lines.append(f"- 现实校验点：{self._join(checkpoints[:2])}")
        return "## 十四、未来年份提示与趋避建议\n\n" + "\n".join(lines)

    def _dayun_integration(self, analysis: dict[str, Any]) -> str:
        birth = analysis.get("input", {})
        start = birth.get("target_year")
        try:
            start_year = int(start) if start else None
        except (TypeError, ValueError):
            start_year = None
        overview = self.luck_advice.dayun_integration(analysis, start_year=start_year, max_periods=4)
        periods = overview.get("periods", [])
        if not periods:
            return ""
        lines = [
            overview.get("policy", "以下把原局主题放进大运里看。"),
        ]
        meta = []
        if overview.get("direction"):
            meta.append(f"排列方向：{overview.get('direction')}")
        if overview.get("start_luck_age"):
            meta.append(f"起运：{overview.get('start_luck_age')}")
        if overview.get("handover_year"):
            meta.append(f"交运公历年：{overview.get('handover_year')}")
        if meta:
            lines.append(f"- 大运基础：{self._join(meta)}")
        for period in periods:
            title = f"{period.get('start_year')}-{period.get('end_year')} 年，{period.get('age_range')}，{period.get('ganzhi')}大运"
            lines.append(f"**{title}**")
            stem_god = period.get("stem_ten_god")
            if stem_god:
                lines.append(f"- 大运十神：{stem_god}")
            stage_theme = period.get("stage_theme")
            if stage_theme:
                lines.append(f"- 阶段主题：{stage_theme}")
            lines.append(f"- 如何作用到命局：{period.get('main_effect_on_chart')}")
            good_side = period.get("good_side", []) or period.get("opportunities", [])
            if good_side:
                lines.append(f"- 好的用法：{self._sentence_join(good_side[:3])}")
            bad_side = period.get("bad_side", []) or period.get("pressure_points", [])
            if bad_side:
                lines.append(f"- 容易卡住/要防的地方：{self._sentence_join(bad_side[:3])}")
            career = period.get("career_guidance")
            if career:
                lines.append(f"- 事业怎么用：{career}")
            wealth = period.get("wealth_guidance")
            if wealth:
                lines.append(f"- 财务怎么用：{wealth}")
            relationship = period.get("relationship_guidance")
            if relationship:
                lines.append(f"- 关系怎么处理：{relationship}")
            health = period.get("health_rhythm")
            if health:
                lines.append(f"- 节奏与健康提醒：{health}")
            triggers = period.get("dayun_triggers", [])
            if triggers:
                lines.append(f"- 与原局互动：{self._join(triggers[:3])}")
            lines.append(f"- 阶段策略：{period.get('strategy')}")
            how_to_use = period.get("how_to_use", [])
            if how_to_use:
                lines.append(f"- 具体做法：{self._sentence_join(how_to_use[:4])}")
            decision_rules = period.get("decision_rules", {})
            if isinstance(decision_rules, dict):
                expand = decision_rules.get("can_expand_when")
                hold = decision_rules.get("should_hold_when")
                if expand or hold:
                    lines.append(f"- 推进/收缩规则：可推进：{expand or '主线清楚时再推进'}；先收缩：{hold or '信息不足时先收缩'}")
            focus_years = period.get("focus_years", [])
            if focus_years:
                lines.append("- 这步运里更要看的年份：")
                for year in focus_years[:4]:
                    level = {
                        "high_attention": "高关注",
                        "medium_attention": "中关注",
                        "low_attention": "低关注",
                    }.get(year.get("attention_level"), "观察")
                    why = self._join(year.get("why", [])[:2]) or "岁运主题叠加"
                    good = self._sentence_join(year.get("good_use", [])[:1])
                    risk = self._sentence_join(year.get("risk_watch", [])[:1])
                    detail = f"  - {year.get('year')} 年（{year.get('year_pillar')}，{level}）：{why}"
                    if good:
                        detail += f"；可把握：{self._strip_end_punctuation(good)}"
                    if risk:
                        detail += f"；要防：{self._strip_end_punctuation(risk)}"
                    action = year.get("action_focus")
                    if action:
                        detail += f"；行动：{self._strip_end_punctuation(action)}"
                    lines.append(detail)
            lines.append(f"- 提醒：{period.get('annual_note')}")
        return "## 十三、大运与命局结合\n\n" + "\n".join(lines)

    def _luck_cycle(self, analysis: dict[str, Any]) -> str:
        luck = analysis.get("assessments", {}).get("luck_cycle", {})
        if not isinstance(luck, dict):
            return ""
        lines = [self._summary(luck)]
        annual = luck.get("annual", {})
        if isinstance(annual, dict) and annual.get("triggers"):
            lines.append(f"{annual.get('target_year')} 年岁运触发：")
            for trigger in annual.get("triggers", [])[:6]:
                rule_name = self._rule_name(trigger.get("rule_id"))
                lines.append(
                    f"- {rule_name}：{trigger.get('summary')}。"
                    f"关注主题：{self._join(trigger.get('possible_domains', []))}。"
                    f"{trigger.get('safe_wording', '')}"
                )
        monthly = luck.get("monthly_windows", {})
        if isinstance(monthly, dict) and monthly.get("windows"):
            windows = monthly.get("windows", [])[:8]
            lines.append("流月窗口：")
            for window in windows:
                rules = [self._rule_name(rule.get("rule_id")) for rule in window.get("triggered_rules", [])]
                lines.append(f"- {window.get('month_name')}（{window.get('ganzhi')}）：{self._join(rules)}。{window.get('summary', '')}")
        daily = luck.get("daily_filter", {})
        if isinstance(daily, dict):
            lines.append("流日候选：")
            if daily.get("date_candidates"):
                dates = [
                    f"{item.get('date')}（{item.get('day_pillar')}）"
                    for item in daily.get("date_candidates", [])[:8]
                ]
                lines.append(f"- 候选日期：{self._join(dates)}。这些日期只作上层窗口内的观察点，不代表某日一定发生某事。")
            else:
                lines.append(f"- {daily.get('safe_wording', '当前不输出流日候选。')}")
        lines.append("提醒：岁运、流月、流日的分数只代表关注度，不代表吉凶，也不代表确定事件。")
        return "## 十五、大运、流年、流月与流日候选\n\n" + "\n".join(lines)

    def _closing(self, analysis: dict[str, Any]) -> str:
        hints = analysis.get("conversation_hints", {}).get("recommended_openers", [])
        follow = self._join(hints[:2]) if hints else "可以继续追问事业、财运、婚恋、健康或某一年流年。"
        return (
            "## 十六、你可以继续怎么问\n\n"
            f"{follow}\n\n"
            "本报告适合用于测试和复盘。若要做更精细判断，建议补充现实背景，例如行业、当前阶段、已发生事件和想看的年份。"
        )

    def _summary(self, item: dict[str, Any]) -> str:
        if not isinstance(item, dict):
            return "暂无结构化结论"
        return str(item.get("summary") or "暂无结构化结论")

    def _structure_translation(self, analysis: dict[str, Any]) -> str:
        assessments = analysis.get("assessments", {})
        facts = analysis.get("facts", {})
        pattern = assessments.get("pattern", {})
        strength = assessments.get("strength", {})
        tiaohou = facts.get("tiaohou_yong_shen", {})
        ids = set(pattern.get("executable_rule_ids") or [])
        parts = []

        pattern_summary = self._summary(pattern)
        if "食神格" in pattern_summary:
            parts.append("若食神格入口成立，现实上更看重稳定产出、专业手艺、内容表达、服务能力和口碑积累。")
        elif "正官格" in pattern_summary:
            parts.append("若正官格入口成立，现实上更看重规则、责任、职位秩序、长期信用和可被认可的专业表现。")
        elif "七杀格" in pattern_summary:
            parts.append("若七杀格入口成立，现实上容易遇到压力、竞争和高要求环境，关键在于能否被规则、学习或执行体系承接。")
        elif "伤官格" in pattern_summary:
            parts.append("若伤官格入口成立，现实上是表达、想法和不服僵化规则的力量较明显，关键在于能否转成作品、方案或解决问题的能力。")

        strength_summary = self._summary(strength)
        if "中和" in strength_summary:
            parts.append("强弱显示中和或信号矛盾时，不适合直接说身强身弱定一切，更适合看具体主题里哪一股力量先被引动。")
        elif "弱" in strength_summary:
            parts.append("日主偏弱时，现实上更要看支持系统、学习资源、稳定环境和恢复能力是否跟得上。")
        elif "强" in strength_summary:
            parts.append("日主偏强时，现实上更要看输出、规则、财务责任或目标压力能否把能量导出去。")

        if isinstance(tiaohou, dict):
            prompt = tiaohou.get("成格提示") or tiaohou.get("破格提示")
            if prompt:
                parts.append(f"调候提示的意思是：{prompt}")

        if "medicine_type_009" in ids:
            parts.append("格局护卫病药出现，说明这张盘不能只看主格名称，还要看有没有力量在保护或修复格局。")
        if "medicine_type_003" in set(assessments.get("chong_he", {}).get("executable_rule_ids") or []):
            parts.append("通关病药出现，说明冲突双方之间需要转换路径，现实里常表现为需要中介资源、制度流程、学习资质或第三种表达方式来缓和。")
        if "medicine_type_007" in set(assessments.get("chong_he", {}).get("executable_rule_ids") or []):
            parts.append("冲合刑害病药出现，说明盘里已有拉扯关系，测试时要看它落在哪些柱位，不能一见冲刑就断坏事。")

        return "现实翻译：" + " ".join(parts) if parts else ""

    def _relation_plain_text(self, relation_dynamics: Any) -> str:
        if not isinstance(relation_dynamics, dict):
            return ""
        clashes = relation_dynamics.get("相冲分析") or []
        if not clashes:
            return ""
        parts = []
        for item in clashes[:2]:
            if not isinstance(item, dict):
                continue
            clash = item.get("冲")
            position = item.get("位置")
            scope = item.get("影响范围")
            strength = item.get("冲力")
            if clash:
                parts.append(f"{clash}（{position or '位置待定'}，冲力{strength or '待定'}，主要牵动{scope or '相关主题'}）")
        if not parts:
            return ""
        return "盘里有合冲动态：" + "；".join(parts) + "。这类信息更适合理解为主题被牵动，不适合直接理解为坏事。"

    def _notes(self, item: dict[str, Any]) -> str:
        if not isinstance(item, dict):
            return ""
        notes = item.get("executable_notes") or []
        return self._join(notes[:5])

    def _join(self, items: Any) -> str:
        if not items:
            return ""
        if isinstance(items, str):
            return items
        return "、".join(str(item) for item in items if item)

    def _sentence_join(self, items: Any) -> str:
        if not items:
            return ""
        if isinstance(items, str):
            return items
        parts = [str(item).strip() for item in items if str(item).strip()]
        return " ".join(parts)

    def _strip_end_punctuation(self, text: Any) -> str:
        return str(text).strip().rstrip("。；;")

    def _rule_name(self, rule_id: Any) -> str:
        if not rule_id:
            return "触发信号"
        rule = self.rule_index.get(str(rule_id), {})
        trigger = rule.get("trigger")
        if isinstance(trigger, dict) and trigger.get("condition"):
            return str(trigger["condition"])
        return str(rule.get("name") or rule_id)

    def _format_value(self, value: Any) -> str:
        if value is None:
            return "未见"
        if isinstance(value, bool):
            return "是" if value else "否"
        if isinstance(value, list):
            if not value:
                return "未见"
            return "、".join(self._format_value(item) for item in value[:5])
        if isinstance(value, dict):
            parts = []
            for key, item in list(value.items())[:5]:
                parts.append(f"{key}:{self._format_value(item)}")
            return "；".join(parts)
        return str(value)

    def _dedupe(self, lines: list[str]) -> list[str]:
        result = []
        for line in lines:
            if line and line not in result:
                result.append(line)
        return result
