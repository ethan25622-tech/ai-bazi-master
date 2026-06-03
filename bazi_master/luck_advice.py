"""Conservative annual opportunity and remedy advice from luck triggers."""

from __future__ import annotations

from datetime import date
from typing import Any

from .luck_cycle_engine import LuckCycleEngine


STEM_ELEMENT = {
    "甲": ("木", "阳"), "乙": ("木", "阴"),
    "丙": ("火", "阳"), "丁": ("火", "阴"),
    "戊": ("土", "阳"), "己": ("土", "阴"),
    "庚": ("金", "阳"), "辛": ("金", "阴"),
    "壬": ("水", "阳"), "癸": ("水", "阴"),
}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
BRANCH_REALM = {
    "子": "水气、人际流动、思维与资源暗线",
    "丑": "湿土、储蓄、承载、旧资源整理",
    "寅": "木气启动、学习、生发、项目开端",
    "卯": "木气扩展、人际连接、表达和生长",
    "辰": "湿土、水木余气、资源整合与拖延问题",
    "巳": "火气启动、表达、执行、显化",
    "午": "火气旺、曝光、行动、压力释放",
    "未": "燥土、成果收束、责任和资源分配",
    "申": "金气启动、规则、竞争、技术和变动",
    "酉": "金气聚焦、标准、审美、制度和取舍",
    "戌": "燥土、旧结构、责任、规则压力",
    "亥": "水木之地、学习、迁动、暗线资源",
}

TEN_GOD_STAGE_PROFILE = {
    "比肩": {
        "good_side": ["适合把自主性、个人品牌、执行节奏和同辈协作建立起来。", "能用在独立项目、稳定自我节奏、争取更清楚的话语权上。"],
        "bad_side": ["容易因为太想按自己的方式来，和同辈、团队或合作方产生资源边界问题。", "事情多时容易硬扛，反而把可合作的部分变成消耗。"],
        "career": "事业上适合争取更明确的职责边界和独立成果，不宜什么都自己扛。",
        "wealth": "财务上先分清个人投入、团队投入和人情往来，避免资源边界模糊。",
        "relationship": "关系里要讲清楚空间、分工和期待，少用沉默或硬撑代替沟通。",
        "health": "节奏上要防长期紧绷，尤其在竞争、赶工、协作拉扯时要保留恢复时间。",
        "expand_when": "当主线目标清楚、资源边界清楚、合作责任清楚时，可以推进。",
        "hold_when": "当同辈竞争、人情压力或资源分配还没讲清时，先收缩。",
    },
    "劫财": {
        "good_side": ["适合打开行动力、人脉连接和资源整合入口。", "能用在团队协作、市场拓展、共同项目和快速试错上。"],
        "bad_side": ["容易出现人情消耗、分账不清、别人来分资源或自己冲动投入。", "机会看起来热闹时，反而更要防主线被分散。"],
        "career": "事业上适合做协作和拓展，但必须先定规则、分工和退出条件。",
        "wealth": "财务上要防合伙、借贷、人情账和冲动投入，先保现金流。",
        "relationship": "关系里容易因朋友、同事、合作资源牵动情绪，边界要比平时更清楚。",
        "health": "节奏上要防社交和事务过密，导致休息被挤压。",
        "expand_when": "当合作能服务主线、账目清楚、责任可追踪时，可以推进。",
        "hold_when": "当只靠口头承诺、人情热度或短期冲动时，先收缩。",
    },
    "食神": {
        "good_side": ["适合稳定输出技能、内容、作品、服务和口碑。", "能用在把经验产品化、课程化、流程化或长期交付上。"],
        "bad_side": ["容易舒服但推进慢，或把输出做散，缺少可衡量成果。", "若同时被压力或偏印牵制，容易想很多、做得少。"],
        "career": "事业上重点是持续交付，把能力做成作品、案例、服务包或标准流程。",
        "wealth": "财务上适合靠技能和稳定服务换回报，不宜只追短线热度。",
        "relationship": "关系里适合用温和表达和稳定陪伴解决问题，少用逃避拖延。",
        "health": "节奏上重在规律作息、饮食和可持续输出，避免长期懒散或过度享受。",
        "expand_when": "当输出能稳定复用、客户或平台反馈清楚时，可以推进。",
        "hold_when": "当只有灵感没有交付、只有兴趣没有结构时，先收缩。",
    },
    "伤官": {
        "good_side": ["适合表达观点、做创新方案、解决旧规则里的低效问题。", "能用在内容、技术、咨询、策划、产品和需要差异化的方向。"],
        "bad_side": ["容易和规则、上级、流程产生摩擦，话说太满会带来反噬。", "能力强但表达太急时，别人先感受到冲突，而不是价值。"],
        "career": "事业上适合提出方案和改进流程，但要用证据、数据和交付物承接表达。",
        "wealth": "财务上适合靠方案、技术、内容或创意变现，但要防冲动换赛道。",
        "relationship": "关系里要减少挑剔式表达，重要话题先讲事实和需求，再讲判断。",
        "health": "节奏上要防脑力过载、情绪急躁和作息被创作/工作打乱。",
        "expand_when": "当方案已有验证、表达有证据、规则边界清楚时，可以推进。",
        "hold_when": "当只是想反抗、想证明自己或情绪很满时，先收缩。",
    },
    "正财": {
        "good_side": ["适合建立稳定收入、预算、长期客户和可持续现金流。", "能用在职业稳定、资源管理、家庭责任和现实落地上。"],
        "bad_side": ["容易被现实责任绑住，或因为太求稳定错过必要升级。", "钱和责任压上来时，容易只顾眼前收支，忽略能力升级。"],
        "career": "事业上适合做稳定岗位、稳定客户、稳定项目，重视可持续交付。",
        "wealth": "财务上重点是预算、现金流、固定支出和长期回报，不宜高杠杆。",
        "relationship": "关系里容易谈到现实责任、钱、家庭安排，适合提前讲清分工。",
        "health": "节奏上要防长期为现实压力透支身体，尤其是固定责任压得太满时。",
        "expand_when": "当现金流稳定、预算有余地、投入产出能算清时，可以推进。",
        "hold_when": "当固定支出过高、债务或承诺太重时，先收缩。",
    },
    "偏财": {
        "good_side": ["适合看机会、客户、项目、市场资源和外部流动。", "能用在副业、商务拓展、资源交换和阶段性项目上。"],
        "bad_side": ["容易机会太多、投入太散，或把风险看成机会。", "财务上若边界不清，容易在人情、合作和项目成本里消耗。"],
        "career": "事业上适合拓展客户和项目，但要筛掉不服务主线的机会。",
        "wealth": "财务上必须先设投入上限、止损线和回款节点，不把命理当投资依据。",
        "relationship": "关系里要防因钱、资源、人情往来造成误会，最好提前讲清。",
        "health": "节奏上要防应酬、奔波和机会焦虑带来的消耗。",
        "expand_when": "当机会能带来长期信用、明确回款或资源沉淀时，可以推进。",
        "hold_when": "当只看到收益、看不清成本和退出条件时，先收缩。",
    },
    "正官": {
        "good_side": ["适合进入更规范的平台、承担职责、建立长期信用。", "能用在职位、资质、制度、流程和可被认可的专业表现上。"],
        "bad_side": ["容易怕出错、被规则束住，或为了稳定牺牲弹性。", "责任变多时，若没有方法和授权，会变成长期压力。"],
        "career": "事业上适合走规范化、职位化、资质化路线，把责任做成信用。",
        "wealth": "财务上适合稳健配置和长期积累，不宜为了面子承担过重责任。",
        "relationship": "关系里要防只讲道理和标准，忽略真实感受。",
        "health": "节奏上要防长期压抑和责任感过重，保持固定休息与运动。",
        "expand_when": "当规则清楚、职责匹配、平台能承接能力时，可以推进。",
        "hold_when": "当只有责任增加、资源和权限没有增加时，先收缩。",
    },
    "七杀": {
        "good_side": ["适合把压力、竞争、目标和高要求转成执行力。", "能用在攻坚项目、职位跃迁、考试考核、管理训练和抗压能力建立上。"],
        "bad_side": ["容易被压力推着走，出现急躁、冲突、焦虑或过度冒险。", "如果缺少规则和支持系统，竞争会变成消耗，而不是成长。"],
        "career": "事业上要把目标拆成规则、证据、节点和交付物，少靠硬冲。",
        "wealth": "财务上不适合在压力下冒进投入，尤其要防为了翻身而加大风险。",
        "relationship": "关系里不要把外部压力带回亲密关系或合作关系，重要决定留缓冲。",
        "health": "节奏上要防压力型透支，睡眠、运动和情绪出口比平时更重要。",
        "expand_when": "当目标清楚、规则清楚、有资源支撑且能分阶段执行时，可以推进。",
        "hold_when": "当压力很大但信息不足、资源不足或情绪很急时，先收缩。",
    },
    "正印": {
        "good_side": ["适合补学历、资质、方法论、专业背书和稳定支持系统。", "能用在学习进修、平台保护、贵人资源和长期积累上。"],
        "bad_side": ["容易依赖安全感，行动变慢，或一直准备但不输出。", "资源太舒服时，反而会拖延真正的成果转化。"],
        "career": "事业上适合靠专业、资质、方法和平台承接机会，同时要有交付。",
        "wealth": "财务上适合长期稳健，不宜因为安全感不足而过度保守或过度囤资源。",
        "relationship": "关系里容易需要理解和支持，也要避免过度退回自己的世界。",
        "health": "节奏上适合修复身体和作息，但不能只休养不行动。",
        "expand_when": "当学习能转成证书、作品、职位或服务成果时，可以推进。",
        "hold_when": "当只是不断准备、不断犹豫、没有输出节点时，先收缩。",
    },
    "偏印": {
        "good_side": ["适合研究专业方法、非标准资源、深度学习和独特技能。", "能用在技术、研究、咨询、玄学、心理、内容结构和小众专业上。"],
        "bad_side": ["容易想得深但表达少，或陷入怀疑、孤立和过度内耗。", "如果和输出系统冲突，会出现懂得多但落地慢。"],
        "career": "事业上适合深耕专业壁垒，但必须配一个可见输出形式。",
        "wealth": "财务上不宜只靠隐性能力，要把专业翻译成别人愿意付费的服务。",
        "relationship": "关系里要防想太多不说清，重要感受用简单语言表达。",
        "health": "节奏上要防睡眠、焦虑、过度思考和作息不稳定。",
        "expand_when": "当研究能转成产品、方案、课程、服务或清楚案例时，可以推进。",
        "hold_when": "当信息越看越多、行动越来越少时，先收缩。",
    },
}


DOMAIN_ACTIONS = {
    "事业": {
        "opportunity": "适合整理职位目标、项目责任、长期平台和可被看见的专业成果。",
        "remedy": "把任务拆成流程、证据和交付物，少靠临场情绪硬冲。",
    },
    "事业平台": {
        "opportunity": "适合观察工作平台、组织结构、上级要求或合作框架的变化机会。",
        "remedy": "提前备份方案，重要决定留书面记录，避免在结构变化中被动应对。",
    },
    "工作环境": {
        "opportunity": "适合调整工作节奏、协作方式和岗位边界。",
        "remedy": "先稳住日常秩序，再谈扩张或跳转。",
    },
    "合作": {
        "opportunity": "适合发展合作、客户连接、资源互换和共同项目。",
        "remedy": "合作前把权责、费用、边界、退出条件讲清楚。",
    },
    "婚恋": {
        "opportunity": "适合修正互动方式、增进沟通，或重新审视亲密关系需求。",
        "remedy": "避免把压力直接投射到关系里，重要话题用事实和边界沟通。",
    },
    "居住": {
        "opportunity": "适合整理居住环境、长期规划和生活动线。",
        "remedy": "搬迁、装修、置业类决定要留预算余地，不宜只凭一时冲动。",
    },
    "财务": {
        "opportunity": "适合梳理收入结构、资源配置和长期现金流。",
        "remedy": "先分清主次，不做高杠杆和冲动投资，不把命理当买卖建议。",
    },
    "迁动": {
        "opportunity": "适合关注出差、迁移、转岗、环境调整带来的新入口。",
        "remedy": "变化年前先做备用计划，把证件、合同、预算和时间表准备好。",
    },
    "阶段性变化": {
        "opportunity": "适合主动更新阶段目标，处理拖延已久的结构问题。",
        "remedy": "把变化变成计划，而不是等事情推着走。",
    },
    "旧事重现": {
        "opportunity": "适合复盘旧项目、旧关系、旧资源，看看能否重新整理利用。",
        "remedy": "不要用旧习惯处理旧问题，先复盘再行动。",
    },
}

RULE_ACTIONS = {
    "year_006": {
        "opportunity": "六合类信号适合把握合作、连接、协商、资源整合的机会。",
        "remedy": "合也可能是牵绊，合作前要确认边界和实际收益。",
    },
    "year_007": {
        "opportunity": "三合/三会类信号适合把分散资源聚成一个主题或项目。",
        "remedy": "聚合不等于一定有利，要看是否服务于主线，不要什么都往身上揽。",
    },
    "year_001": {
        "opportunity": "日支被引动时，关系、合作、居住和内在状态会更值得主动调整。",
        "remedy": "少做极端关系判断，先处理沟通、作息、边界和现实压力。",
    },
    "year_002": {
        "opportunity": "月令/月支被引动时，事业平台、家庭结构或工作环境更值得观察。",
        "remedy": "先稳平台与节奏，重大变化要做两套方案。",
    },
    "year_005": {
        "opportunity": "天克地冲/反吟类信号适合主动处理变化，更新旧结构。",
        "remedy": "不宜把冲动当决断；合同、出行、财务、关系沟通都要留缓冲。",
    },
    "year_003": {
        "opportunity": "岁运并临表示主题叠加，适合集中处理一个阶段主线。",
        "remedy": "避免同时开太多战线，越是主题集中越要减法管理。",
    },
    "year_004": {
        "opportunity": "伏吟类信号适合复盘旧主题、旧项目、旧习惯。",
        "remedy": "不要把重复当宿命，重点是换一种处理方式。",
    },
}


class LuckAdviceEngine:
    """Summarize annual windows as opportunities, caution points, and remedies."""

    def __init__(self) -> None:
        self.luck_engine = LuckCycleEngine()

    def forecast_years(
        self,
        analysis: dict[str, Any],
        *,
        start_year: int | None = None,
        years: int = 8,
    ) -> dict[str, Any]:
        start = start_year or date.today().year
        end = start + max(1, years) - 1
        items = [self.year_advice(analysis, year) for year in range(start, end + 1)]
        items = [item for item in items if item.get("attention_level") != "none"]
        return {
            "start_year": start,
            "end_year": end,
            "policy": "以下只表示主题窗口、机会方向和避险做法，不代表吉凶或确定事件。",
            "years": items[:years],
        }

    def past_validation(
        self,
        analysis: dict[str, Any],
        *,
        end_year: int | None = None,
        years_back: int = 18,
        max_items: int = 6,
    ) -> dict[str, Any]:
        birth_year = self._birth_year(analysis)
        end = end_year or date.today().year - 1
        start = max(birth_year + 8, end - max(1, years_back) + 1)
        items = []
        for year in range(start, end + 1):
            advice = self.year_advice(analysis, year)
            if advice.get("attention_level") == "none":
                continue
            validation = self._validation_points(advice)
            if not validation:
                continue
            advice["likely_past_experience"] = validation
            advice["possible_past_challenges"] = self._past_challenge_points(advice)
            advice["validation_note"] = "用于回看是否应验；表示该年主题更容易被引动，不代表一定发生同一件事。"
            items.append(advice)
        items.sort(key=lambda item: self._past_rank(item), reverse=True)
        return {
            "start_year": start,
            "end_year": end,
            "policy": "以下是过往经历校验点：系统直接给出较可能被引动的主题，供你核对准不准；仍不作绝对事件判断。",
            "years": items[:max_items],
        }

    def structural_tradeoff_advice(
        self,
        analysis: dict[str, Any],
        *,
        start_year: int | None = None,
        years: int = 8,
    ) -> dict[str, Any]:
        tradeoffs = self._tradeoff_points(analysis)
        if not tradeoffs:
            return {
                "policy": "未发现需要单独展开的取舍点。",
                "items": [],
            }
        forecast = self.forecast_years(analysis, start_year=start_year, years=years)
        forecast_years = forecast.get("years", [])
        items = []
        for tradeoff in tradeoffs:
            matched_years = self._match_tradeoff_years(tradeoff, forecast_years)
            items.append({
                **tradeoff,
                "future_reference_years": matched_years,
                "policy": "取舍建议必须结合未来岁运窗口执行；年份只代表主题更值得观察，不代表确定吉凶。",
            })
        return {
            "policy": "以下把命局中的取舍点接到未来大运流年，用来指导何时主动调整、何时保守处理。",
            "items": items,
        }

    def dayun_integration(
        self,
        analysis: dict[str, Any],
        *,
        start_year: int | None = None,
        max_periods: int = 4,
    ) -> dict[str, Any]:
        dayun = analysis.get("facts", {}).get("dayun") or {}
        steps = dayun.get("大运列表") or []
        if not steps:
            return {
                "policy": "未取得大运列表，暂不能做命运结合。",
                "periods": [],
            }
        anchor_year = start_year or date.today().year
        selected = [
            step for step in steps
            if int(step.get("起始年", 0) or 0) + 9 >= anchor_year
        ][:max_periods]
        if not selected:
            selected = steps[-max_periods:]

        return {
            "policy": "以下把原局主题放进大运里看：大运代表阶段背景，流年是在阶段背景上触发具体年份；不把大运直接说成好坏。",
            "direction": dayun.get("排列方向"),
            "start_luck_age": dayun.get("起运岁数"),
            "handover_year": dayun.get("交运公历年"),
            "periods": [self._dayun_period(analysis, step) for step in selected],
        }

    def _dayun_period(self, analysis: dict[str, Any], step: dict[str, Any]) -> dict[str, Any]:
        start_year = int(step.get("起始年", 0) or 0)
        start_age = int(step.get("起始岁", 0) or 0)
        ganzhi = str(step.get("干支", ""))
        annual = self.luck_engine.evaluate_year(analysis, start_year) if start_year else {}
        dayun_triggers = [
            trigger for trigger in annual.get("triggers", [])
            if str(trigger.get("rule_id", "")).startswith("luck_")
        ]
        domains = self._dedupe([
            str(domain)
            for trigger in dayun_triggers
            for domain in trigger.get("possible_domains", [])
            if domain
        ])
        rule_ids = [str(trigger.get("rule_id")) for trigger in dayun_triggers if trigger.get("rule_id")]
        stem_god = self._ten_god_for_stem(analysis, ganzhi[:1])
        branch_theme = BRANCH_REALM.get(ganzhi[1:2], "阶段背景待结合原局确认")
        profile = self._ten_god_profile(stem_god)
        focus_years = self._dayun_focus_years(analysis, start_year)
        return {
            "step": step.get("步"),
            "ganzhi": ganzhi,
            "start_year": start_year,
            "end_year": start_year + 9 if start_year else None,
            "age_range": f"{start_age}-{start_age + 9}岁" if start_age else "",
            "stem_ten_god": stem_god,
            "branch_theme": branch_theme,
            "dayun_trigger_rule_ids": rule_ids,
            "dayun_triggers": [
                self._clean_summary(str(trigger.get("summary")))
                for trigger in dayun_triggers[:4]
                if trigger.get("summary")
            ],
            "stage_theme": self._dayun_stage_theme(stem_god, branch_theme, domains, rule_ids),
            "main_effect_on_chart": self._dayun_effect_text(stem_god, branch_theme, rule_ids, domains),
            "good_side": self._dedupe([*profile.get("good_side", []), *self._dayun_opportunities(stem_god, domains)])[:4],
            "bad_side": self._dedupe([*profile.get("bad_side", []), *self._dayun_pressure_points(rule_ids, domains)])[:4],
            "opportunities": self._dayun_opportunities(stem_god, domains),
            "pressure_points": self._dayun_pressure_points(rule_ids, domains),
            "career_guidance": self._dayun_domain_guidance("career", profile, rule_ids, domains),
            "wealth_guidance": self._dayun_domain_guidance("wealth", profile, rule_ids, domains),
            "relationship_guidance": self._dayun_domain_guidance("relationship", profile, rule_ids, domains),
            "health_rhythm": self._dayun_domain_guidance("health", profile, rule_ids, domains),
            "strategy": self._dayun_strategy(stem_god, rule_ids, domains),
            "how_to_use": self._dayun_how_to_use(stem_god, rule_ids, domains),
            "decision_rules": {
                "can_expand_when": profile.get("expand_when") or "现实反馈清楚、主线明确、资源能承接时再推进。",
                "should_hold_when": profile.get("hold_when") or "信息不足、资源不足、情绪过急或同一问题反复卡住时先收缩。",
            },
            "focus_years": focus_years,
            "annual_note": "该步大运是十年背景，具体应期仍需叠加流年、流月和现实事件验证。",
        }

    def _dayun_effect_text(self, stem_god: str, branch_theme: str, rule_ids: list[str], domains: list[str]) -> str:
        parts = []
        if stem_god:
            parts.append(f"天干透出{stem_god}，说明这十年会反复碰到与{self._ten_god_plain(stem_god)}有关的主题。")
        if branch_theme:
            parts.append(f"地支背景偏向{branch_theme}。")
        if rule_ids:
            parts.append("与原局存在大运级互动，表示这步运不只是背景，也会触发原局某些宫位或结构。")
        if domains:
            parts.append(f"重点观察领域：{self._join(domains[:4])}。")
        return "".join(parts) or "该步大运需结合流年进一步判断。"

    def _dayun_opportunities(self, stem_god: str, domains: list[str]) -> list[str]:
        items = []
        if stem_god in {"正官", "七杀"}:
            items.append("适合把责任、规则、职位目标、竞争压力转成长期能力。")
        if stem_god in {"正印", "偏印"}:
            items.append("适合补学习、资质、方法论、专业背书和稳定支持系统。")
        if stem_god in {"食神", "伤官"}:
            items.append("适合把技能、表达、作品、服务和解决方案做成可见成果。")
        if stem_god in {"正财", "偏财"}:
            items.append("适合梳理收入结构、客户资源、项目回报和资源配置。")
        if stem_god in {"比肩", "劫财"}:
            items.append("适合建立自主性、行动力、团队协作和资源边界。")
        if any(domain in {"合作", "婚恋", "关系或合作拉扯"} for domain in domains):
            items.append("合作、人脉和关系议题会更容易成为阶段入口。")
        if any(domain in {"事业平台", "工作环境", "阶段性变化"} for domain in domains):
            items.append("事业平台、岗位节奏和阶段目标适合主动调整。")
        return self._dedupe(items)[:4] or ["把这步运当作阶段背景，先观察现实中最先被引动的主题。"]

    def _dayun_pressure_points(self, rule_ids: list[str], domains: list[str]) -> list[str]:
        items = []
        if "luck_003" in rule_ids:
            items.append("大运冲月支，平台、家庭、工作环境或主线节奏更容易被推着调整。")
        if "luck_004" in rule_ids:
            items.append("大运冲日支，关系、合作、居住和个人稳定性需要特别留缓冲。")
        if "luck_005" in rule_ids:
            items.append("大运伏吟原局某柱，旧主题会反复出现，不能只靠旧办法处理。")
        if "luck_006" in rule_ids:
            items.append("大运天克地冲原局某柱，阶段变化感较强，合同、迁动、合作和方向切换不宜冲动。")
        if any(domain in {"财务"} for domain in domains):
            items.append("财务资源被引动时，注意现金流、分账、预算和投入产出。")
        if any(domain in {"合作", "婚恋", "关系或合作拉扯"} for domain in domains):
            items.append("关系合作被引动时，注意权责不清、口头承诺和情绪化决定。")
        return self._dedupe(items)[:4] or ["压力点暂不放大，重点看流年是否重复触发同一主题。"]

    def _dayun_strategy(self, stem_god: str, rule_ids: list[str], domains: list[str]) -> str:
        if "luck_006" in rule_ids:
            return "这步运先做风险缓冲：合同、迁动、合作、岗位变化都要有备选方案，再谈扩张。"
        if "luck_004" in rule_ids:
            return "这步运先稳关系和生活底盘：边界、作息、住处、合作节奏要讲清楚。"
        if "luck_003" in rule_ids:
            return "这步运先稳平台和主线：工作环境、家庭责任、学习体系不要同时失序。"
        if stem_god in {"食神", "伤官"}:
            return "这步运宜把输出变成作品和方案，用持续交付承接机会。"
        if stem_god in {"正官", "七杀"}:
            return "这步运宜把压力制度化，靠规则、证据、资质和长期信用承接。"
        if stem_god in {"正财", "偏财"}:
            return "这步运宜先管资源和现金流，机会再多也要分主次。"
        return "这步运先定阶段主线，再用流年判断何时推进、何时收缩。"

    def _ten_god_profile(self, stem_god: str) -> dict[str, Any]:
        return TEN_GOD_STAGE_PROFILE.get(stem_god, {})

    def _dayun_stage_theme(
        self,
        stem_god: str,
        branch_theme: str,
        domains: list[str],
        rule_ids: list[str],
    ) -> str:
        theme = self._ten_god_plain(stem_god) if stem_god else "阶段主线"
        if rule_ids:
            return f"这十年的主线是把{theme}放进现实结构里处理；因为大运与原局有互动，越要看关系、平台、资源或居住节奏是否被反复牵动。"
        if domains:
            return f"这十年的主线是围绕{theme}建立更稳定的阶段方法，重点落在{self._join(domains[:3])}。"
        if branch_theme:
            return f"这十年的背景偏向{branch_theme}，适合先观察现实里哪条主线最先被带动。"
        return "这十年先当作阶段背景看，不单独下吉凶结论，重点叠加流年验证。"

    def _dayun_domain_guidance(
        self,
        key: str,
        profile: dict[str, Any],
        rule_ids: list[str],
        domains: list[str],
    ) -> str:
        base = str(profile.get(key) or "")
        additions: list[str] = []
        rule_set = set(rule_ids)
        domain_set = set(domains)
        if key == "career":
            if "luck_003" in rule_set:
                additions.append("月支被冲时，工作平台、团队规则、家庭责任和学习系统要先稳住。")
            if "luck_006" in rule_set:
                additions.append("天克地冲类互动出现时，岗位切换、合作签约和方向调整要先做备选方案。")
            if domain_set & {"事业平台", "工作环境", "阶段性变化"}:
                additions.append("如果现实中已经有换团队、换岗位、换目标的苗头，优先把主线和交付物写清楚。")
        elif key == "wealth":
            if domain_set & {"财务"}:
                additions.append("财务主题被引动时，重点不是猜收入高低，而是管预算、回款、分账和投入产出。")
            if "luck_006" in rule_set:
                additions.append("变化强的阶段不适合重仓冒进，重大支出要留缓冲。")
        elif key == "relationship":
            if "luck_004" in rule_set:
                additions.append("日支被冲时，合作、亲密关系、居住和个人状态都要留沟通缓冲。")
            if domain_set & {"合作", "婚恋", "关系或合作拉扯"}:
                additions.append("关系主题被带动时，先谈责任、费用、边界和退出条件。")
        elif key == "health":
            if rule_set & {"luck_003", "luck_004", "luck_006"}:
                additions.append("有冲动或变化信号时，生活节奏比结论更重要，先稳睡眠、饮食、运动和情绪出口。")
            if domain_set & {"迁动", "居住", "阶段性变化"}:
                additions.append("迁动或环境调整阶段，要防作息被打乱。")
        text = " ".join([item for item in [base, *additions] if item])
        return text or "先观察这步运在现实中最先牵动哪个领域，再决定是推进还是收缩。"

    def _dayun_how_to_use(self, stem_god: str, rule_ids: list[str], domains: list[str]) -> list[str]:
        items: list[str] = []
        if stem_god in {"正官", "七杀"}:
            items.extend([
                "把压力拆成目标、规则、时间表和交付物，不用情绪硬扛。",
                "凡是职位、考核、合同、管理相关事项，先留证据和备选方案。",
            ])
        elif stem_god in {"食神", "伤官"}:
            items.extend([
                "把表达和技能变成可见成果：作品、案例、服务包、课程或方案。",
                "先小范围验证，再放大输出，避免只凭灵感扩张。",
            ])
        elif stem_god in {"正财", "偏财"}:
            items.extend([
                "先做现金流表、投入上限和退出条件，再看机会大小。",
                "把主收入、副机会、人情合作分开管理。",
            ])
        elif stem_god in {"正印", "偏印"}:
            items.extend([
                "把学习、资质和研究转成可交付成果，避免一直准备。",
                "建立稳定支持系统，但不要把安全感当成拖延理由。",
            ])
        elif stem_god in {"比肩", "劫财"}:
            items.extend([
                "把自主目标、合作边界、资源分配写清楚。",
                "适合组队或独立推进，但不适合口头模糊合作。",
            ])
        if "luck_004" in rule_ids:
            items.append("关系、合作、居住类决定不要在情绪最高点做，至少留一轮沟通缓冲。")
        if "luck_003" in rule_ids:
            items.append("平台、家庭、工作环境要先稳基本盘，再谈扩张。")
        if "luck_006" in rule_ids:
            items.append("遇到变化时先做 A/B 方案，再决定是否切换方向。")
        if any(domain in {"财务"} for domain in domains):
            items.append("财务动作先看现金流和风险上限，不把关注度当收益判断。")
        return self._dedupe(items)[:5] or ["先定十年主线，再用每年触发点决定推进、观察或收缩。"]

    def _dayun_focus_years(self, analysis: dict[str, Any], start_year: int, max_items: int = 4) -> list[dict[str, Any]]:
        if not start_year:
            return []
        candidates: list[dict[str, Any]] = []
        for year in range(start_year, start_year + 10):
            advice = self.year_advice(analysis, year)
            if advice.get("attention_level") == "none":
                continue
            candidates.append({
                "year": year,
                "year_pillar": advice.get("year_pillar"),
                "attention_level": advice.get("attention_level"),
                "why": self._dedupe([
                    *advice.get("year_specific_triggers", [])[:2],
                    *advice.get("dayun_background", [])[:1],
                ])[:3],
                "good_use": advice.get("opportunities", [])[:2],
                "risk_watch": advice.get("pressure_points", [])[:2],
                "action_focus": advice.get("priority_focus"),
            })
        candidates.sort(key=lambda item: self._focus_year_rank(str(item.get("attention_level"))), reverse=True)
        selected = sorted(candidates[:max_items], key=lambda item: int(item.get("year") or 0))
        return selected

    def _focus_year_rank(self, attention_level: str) -> int:
        return {
            "high_attention": 3,
            "medium_attention": 2,
            "low_attention": 1,
        }.get(attention_level, 0)

    def year_advice(self, analysis: dict[str, Any], target_year: int) -> dict[str, Any]:
        annual = self.luck_engine.evaluate_year(analysis, target_year)
        triggers = annual.get("triggers", [])
        year_triggers = [trigger for trigger in triggers if str(trigger.get("rule_id", "")).startswith("year_")]
        dayun_triggers = [trigger for trigger in triggers if str(trigger.get("rule_id", "")).startswith("luck_")]
        top = [*year_triggers[:4], *dayun_triggers[:2]]
        domains = self._dedupe([
            str(domain)
            for trigger in top
            for domain in trigger.get("possible_domains", [])
            if domain
        ])
        rule_ids = [str(trigger.get("rule_id")) for trigger in top if trigger.get("rule_id")]
        score = sum(int(trigger.get("trigger_score", 0)) for trigger in year_triggers[:4])
        attention = self._attention_level(score, year_triggers or dayun_triggers[:2])
        return {
            "year": target_year,
            "year_pillar": annual.get("year_pillar"),
            "attention_level": attention,
            "main_themes": domains[:5],
            "rule_ids": rule_ids,
            "priority_focus": self._priority_focus(rule_ids, domains),
            "year_specific_triggers": [
                self._clean_summary(str(trigger.get("summary")))
                for trigger in year_triggers[:4]
                if trigger.get("summary")
            ],
            "dayun_background": [
                self._clean_summary(str(trigger.get("summary")))
                for trigger in dayun_triggers[:3]
                if trigger.get("summary")
            ],
            "trigger_summaries": [self._clean_summary(str(trigger.get("summary"))) for trigger in top if trigger.get("summary")],
            "opportunities": self._opportunities(rule_ids, domains),
            "pressure_points": self._pressure_points(rule_ids, domains, top),
            "cautions": self._cautions(rule_ids, domains, top),
            "remedies": self._remedies(rule_ids, domains),
            "action_plan": self._action_plan(rule_ids, domains, top),
            "safe_wording": "该年只代表相关主题关注度提高；可主动规划，不作确定吉凶判断。",
        }

    def _tradeoff_points(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        assessments = analysis.get("assessments", {})
        points = []
        wealth = assessments.get("wealth", {})
        if isinstance(wealth, dict) and "medicine_type_004" in set(wealth.get("executable_rule_ids") or []):
            points.append({
                "topic": "财务/事业取舍",
                "structural_issue": "清浊病药提示资源、财务或事业选择上需要分清主次。",
                "why_it_matters": "如果什么都抓，容易让主线变浊，表现为精力分散、资源配置不清、赚钱方式摇摆。",
                "future_strategy": "遇到事业、财务、合作被岁运引动的年份，优先做减法：确定主收入/主项目/主合作，再处理次要机会。",
                "preferred_year_themes": ["事业", "事业平台", "工作环境", "财务", "合作", "阶段性变化"],
                "sources": self._sources_for(wealth, [
                    "资料口3：清浊纯杂、去留、官杀混杂、食伤混杂相关规则拆解",
                    "子平真诠·论用神纯杂",
                    "滴天髓·清浊",
                ]),
            })

        chong_he = assessments.get("chong_he", {})
        if isinstance(chong_he, dict) and "medicine_type_007" in set(chong_he.get("executable_rule_ids") or []):
            points.append({
                "topic": "关系/合作边界",
                "structural_issue": "冲合刑害病药提示盘中已有拉扯关系，需看它是否牵动月令、用神或关键宫位。",
                "why_it_matters": "遇到岁运重复引动时，容易表现为合作边界、关系沟通、居住或工作节奏被重新安排。",
                "future_strategy": "遇到冲日支、冲月支、反吟、伏吟或合作合动年份，先定边界、合同、节奏和退出条件，再谈扩张。",
                "preferred_year_themes": ["婚恋", "合作", "居住", "工作环境", "阶段性变化", "迁动", "关系或合作拉扯"],
                "sources": self._sources_for(chong_he, [
                    "资料口3：冲合刑害、合化、根气损益相关规则拆解",
                    "天干五合、地支六合三合刑冲害固定关系表",
                    "子平真诠·刑冲会合解法",
                ]),
            })

        pattern = assessments.get("pattern", {})
        if isinstance(pattern, dict) and "medicine_type_009" in set(pattern.get("executable_rule_ids") or []):
            points.append({
                "topic": "格局护卫/救应",
                "structural_issue": "格局护卫病药提示主格不能只看名称，还要看有没有力量保护或修复格局。",
                "why_it_matters": "当未来年份引动事业、规则、印星、表达或合作时，处理方式会影响格局是变清还是变复杂。",
                "future_strategy": "遇到事业平台、合作、表达输出被引动的年份，优先保主线：资质、规则、专业信用、稳定输出要排在短期机会前面。",
                "preferred_year_themes": ["事业", "事业平台", "工作环境", "合作", "旧事重现", "阶段性变化"],
                "sources": self._sources_for(pattern, [
                    "资料口3：成格、破格、救格、护格相关规则拆解",
                    "子平真诠·论用神成败救应",
                ]),
            })
        return points

    def _match_tradeoff_years(self, tradeoff: dict[str, Any], forecast_years: list[dict[str, Any]]) -> list[dict[str, Any]]:
        preferred = set(tradeoff.get("preferred_year_themes", set()))
        matches = []
        for item in forecast_years:
            themes = set(item.get("main_themes", []))
            overlap = sorted(preferred & themes)
            year_triggers = item.get("year_specific_triggers", [])
            if not overlap and not year_triggers:
                continue
            if not overlap and item.get("attention_level") != "high_attention":
                continue
            matches.append({
                "year": item.get("year"),
                "year_pillar": item.get("year_pillar"),
                "attention_level": item.get("attention_level"),
                "matched_themes": overlap[:4],
                "year_specific_triggers": year_triggers[:3],
                "suggested_action": self._tradeoff_year_action(tradeoff, item),
            })
        return matches[:4]

    def _tradeoff_year_action(self, tradeoff: dict[str, Any], year_item: dict[str, Any]) -> str:
        topic = tradeoff.get("topic")
        if topic == "财务/事业取舍":
            return "这一年若出现新项目、新合作或资源变化，先列三张表：主收入来源、最耗精力事项、可推迟事项；先保主线和预算，再决定接不接新机会。"
        if topic == "关系/合作边界":
            return "这一年若关系或合作被引动，先把分工、付款/回报、沟通频率、退出条件写清楚；情绪上头时不立刻做关系结论。"
        if topic == "格局护卫/救应":
            return "这一年优先保护专业信用、稳定输出和长期平台；短期机会要先问是否损害资质、规则、口碑和主业节奏。"
        return "结合该年触发主题做现实取舍：先写主目标、底线、可放弃项，再行动。"

    def _sources_for(self, assessment: dict[str, Any], fallback: list[str]) -> list[str]:
        sources = []
        rule_source = assessment.get("rule_source")
        if isinstance(rule_source, list):
            sources.extend(str(item) for item in rule_source if item)
        elif rule_source:
            sources.append(str(rule_source))
        for evidence in assessment.get("evidence", [])[:4]:
            if isinstance(evidence, dict) and evidence.get("source"):
                sources.append(str(evidence["source"]))
        sources.extend(fallback)
        return self._dedupe(sources)[:5]

    def _validation_points(self, advice: dict[str, Any]) -> list[str]:
        domains = set(advice.get("main_themes", []))
        rule_text = "、".join(advice.get("year_specific_triggers", []))
        rule_ids = set(advice.get("rule_ids", []))
        points = []
        if "year_001" in rule_ids:
            points.append("优先核对关系/合作/居住/个人状态：是否出现关系重新谈边界、合作分工变化、住处或作息节奏被打乱。")
        if "year_002" in rule_ids:
            points.append("优先核对工作平台/家庭结构/学习环境：是否有换团队、换任务、上级要求变化、家庭事务牵动精力。")
        if "year_003" in rule_ids:
            points.append("优先核对阶段主线叠加：是否某个主题在这一年反复出现，导致不得不集中处理。")
        if "year_004" in rule_ids:
            points.append("优先核对旧事重现：是否旧项目、旧关系、旧习惯、旧问题在这一年重新浮上来。")
        if "year_005" in rule_ids:
            points.append("优先核对明显变动：是否有计划被打断、外部压力增大、出行迁动、岗位/合作/关系需要重新协调。")
        if "year_006" in rule_ids:
            points.append("优先核对连接机会：是否出现新合作、客户资源、介绍牵线、关系缓和或某种绑定关系。")
        if "year_007" in rule_ids:
            points.append("优先核对资源聚合：是否项目、圈层、人脉、学习/工作资源在这一年集中到同一主题上。")
        if "year_008" in rule_ids:
            points.append("优先核对同类主题回响：是否某类人事物、工作模式或情绪状态重复出现。")
        if domains & {"事业", "事业平台", "工作环境", "阶段性变化"} and not any("工作" in item or "平台" in item for item in points):
            points.append("事业/学习/平台环境上较可能有调整：重点核对任务内容、协作对象、考核要求或节奏变化。")
        if (domains & {"合作", "婚恋", "关系或合作拉扯"} or "日支" in rule_text) and not any("关系" in item or "合作" in item for item in points):
            points.append("关系或合作上较可能有拉扯：重点核对沟通方式、分工边界、承诺兑现和亲密关系节奏。")
        if domains & {"居住", "迁动", "环境调整"} and not any("居住" in item or "出行" in item or "迁动" in item for item in points):
            points.append("居住、出行、工作地点或生活动线较可能出现调整，未必是搬家，也可能是通勤、办公地点或日常安排变化。")
        if domains & {"财务"}:
            points.append("财务资源较可能需要重排：重点核对收入方式、支出压力、预算取舍、项目投入产出是否变化。")
        if not points and advice.get("dayun_background"):
            points.append("该年虽未必有明显单年触发，但处在大运背景变化期，现实中可能有持续性的压力、方向调整或环境变化。")
        return self._dedupe(points)[:4]

    def _past_challenge_points(self, advice: dict[str, Any]) -> list[str]:
        domains = set(advice.get("main_themes", []))
        rule_ids = set(advice.get("rule_ids", []))
        points = []
        if "year_001" in rule_ids:
            points.append("可能较卡：关系、合作、居住或个人状态容易被打乱，表现为沟通成本上升、边界重谈、情绪或作息不稳。")
        if "year_002" in rule_ids:
            points.append("可能较卡：工作平台、团队规则、家庭事务或学习环境有压力，表现为被要求调整、换节奏或承担额外责任。")
        if "year_003" in rule_ids:
            points.append("可能较卡：同一主题叠加变重，容易感觉事情集中、压力重复，很难同时兼顾多条线。")
        if "year_004" in rule_ids or "year_008" in rule_ids:
            points.append("可能较卡：旧问题反复出现，若仍用旧办法处理，容易重复消耗。")
        if "year_005" in rule_ids:
            points.append("可能较卡：变化来得急，计划、合同、出行、岗位、合作或关系安排容易被打断，需要重新协调。")
        if "year_006" in rule_ids or "year_007" in rule_ids:
            points.append("可能较卡：机会、人情、合作或资源聚合变多，但边界不清时容易变成牵绊、分心或额外负担。")
        if domains & {"财务"}:
            points.append("财务上可能较卡：预算、分账、支出压力或项目投入产出需要重新核算。")
        if domains & {"迁动", "环境调整"}:
            points.append("环境上可能较卡：通勤、搬动、办公方式、出差或生活动线容易增加额外成本。")
        return self._dedupe(points)[:3]

    def _past_rank(self, advice: dict[str, Any]) -> int:
        level_score = {
            "high_attention": 300,
            "medium_attention": 180,
            "low_attention": 80,
        }.get(str(advice.get("attention_level")), 0)
        year_trigger_score = 30 * len(advice.get("year_specific_triggers", []))
        validation_score = 10 * len(advice.get("likely_past_experience", []))
        return level_score + year_trigger_score + validation_score

    def _birth_year(self, analysis: dict[str, Any]) -> int:
        try:
            return int(analysis.get("input", {}).get("year") or 1902)
        except (TypeError, ValueError):
            return 1902

    def _ten_god_for_stem(self, analysis: dict[str, Any], other_stem: str) -> str:
        day_master = str(analysis.get("chart", {}).get("day_master") or "")
        if day_master not in STEM_ELEMENT or other_stem not in STEM_ELEMENT:
            return ""
        day_element, day_yin_yang = STEM_ELEMENT[day_master]
        other_element, other_yin_yang = STEM_ELEMENT[other_stem]
        same_polarity = day_yin_yang == other_yin_yang
        if other_element == day_element:
            return "比肩" if same_polarity else "劫财"
        if GENERATES[other_element] == day_element:
            return "偏印" if same_polarity else "正印"
        if GENERATES[day_element] == other_element:
            return "食神" if same_polarity else "伤官"
        if CONTROLS[day_element] == other_element:
            return "偏财" if same_polarity else "正财"
        if CONTROLS[other_element] == day_element:
            return "七杀" if same_polarity else "正官"
        return ""

    def _ten_god_plain(self, ten_god: str) -> str:
        return {
            "比肩": "自主、同辈、竞争、协作边界",
            "劫财": "资源分配、同伴、人情、竞争",
            "食神": "稳定输出、技能、作品、服务",
            "伤官": "表达、创新、规则张力、方案能力",
            "正财": "稳定收入、预算、现实资源",
            "偏财": "项目机会、客户、资源流动",
            "正官": "规则、责任、职位、长期信用",
            "七杀": "压力、竞争、目标、执行",
            "正印": "学习、资质、保护、稳定支持",
            "偏印": "专业方法、研究、非标准资源、内在支持",
        }.get(ten_god, ten_god)

    def _attention_level(self, score: int, triggers: list[dict[str, Any]]) -> str:
        if not triggers:
            return "none"
        if any(trigger.get("risk_level") == "high" for trigger in triggers[:3]) or score >= 180:
            return "high_attention"
        if score >= 90:
            return "medium_attention"
        return "low_attention"

    def _opportunities(self, rule_ids: list[str], domains: list[str]) -> list[str]:
        items = []
        for rule_id in rule_ids:
            action = RULE_ACTIONS.get(rule_id, {})
            if action.get("opportunity"):
                items.append(action["opportunity"])
        for domain in domains:
            action = DOMAIN_ACTIONS.get(domain, {})
            if action.get("opportunity"):
                items.append(action["opportunity"])
        if not items:
            items.append("适合把该年出现的主题当成复盘和调整窗口，先观察现实中哪个领域最先被引动。")
        return self._dedupe(items)[:4]

    def _cautions(self, rule_ids: list[str], domains: list[str], triggers: list[dict[str, Any]]) -> list[str]:
        items = []
        if any(rule_id in {"year_001", "year_002", "year_003", "year_004", "year_005"} for rule_id in rule_ids):
            items.append("不要把岁运触发直接理解为坏事，重点看现实中是否已有同类压力或变化。")
        if any(trigger.get("repeat_context", {}).get("same_palace_repeat") for trigger in triggers):
            items.append("同一宫位被重复引动时，相关主题更值得提前安排，避免临时应付。")
        if any(domain in {"婚恋", "合作"} for domain in domains):
            items.append("关系与合作类主题要避免口头约定不清。")
        if any(domain in {"财务", "事业平台", "工作环境"} for domain in domains):
            items.append("事业财务类主题要避免同时贪多、冲动扩张或高风险决策。")
        if not items:
            items.append("避免用单一年份给人生大事下定论，先做现实背景核验。")
        return self._dedupe(items)[:4]

    def _pressure_points(self, rule_ids: list[str], domains: list[str], triggers: list[dict[str, Any]]) -> list[str]:
        items = []
        rule_set = set(rule_ids)
        domain_set = set(domains)
        if "year_005" in rule_set:
            items.append("天克地冲/反吟类年份，压力点在变化过急：合同、出行、合作、岗位、财务安排要留缓冲。")
        if "year_001" in rule_set:
            items.append("日支被冲或引动时，压力点在关系、合作、居住和个人状态，避免在情绪高点做分合或去留决定。")
        if "year_002" in rule_set:
            items.append("月支/月令被冲或引动时，压力点在工作平台、家庭结构、团队规则和学习环境，不宜临时硬扛。")
        if "year_003" in rule_set:
            items.append("岁运并临类年份，压力点在主题叠加，容易一件事反复压上来，越要少开战线。")
        if "year_004" in rule_set or "year_008" in rule_set:
            items.append("伏吟/同支回响类年份，压力点在旧问题重现，避免用旧习惯处理旧矛盾。")
        if "year_006" in rule_set or "year_007" in rule_set:
            items.append("合动/聚合类年份不全是好事，压力点在牵连变多、边界变模糊、资源被分散。")
        if domain_set & {"财务"}:
            items.append("财务主题被引动时，特别注意预算、分账、债务、人情往来和高风险投入。")
        if domain_set & {"合作", "婚恋", "关系或合作拉扯"}:
            items.append("关系合作主题被引动时，特别注意口头承诺、责任不清、冷处理和情绪化沟通。")
        if any(trigger.get("repeat_context", {}).get("same_palace_repeat") for trigger in triggers):
            items.append("同一宫位重复触发时，相关问题不宜拖延，越拖越容易变成被动处理。")
        if not items:
            items.append("本年压力点不宜扩大解释，先观察现实中哪个领域出现阻滞、反复或额外成本。")
        return self._dedupe(items)[:4]

    def _remedies(self, rule_ids: list[str], domains: list[str]) -> list[str]:
        items = []
        for rule_id in rule_ids:
            action = RULE_ACTIONS.get(rule_id, {})
            if action.get("remedy"):
                items.append(action["remedy"])
        for domain in domains:
            action = DOMAIN_ACTIONS.get(domain, {})
            if action.get("remedy"):
                items.append(action["remedy"])
        items.extend([
            "把关注主题提前写成计划：目标、边界、预算、时间表、可退出方案。",
            "用现实反馈校验命理信号：看工作、关系、财务、健康作息中哪一项先出现变化。",
        ])
        return self._dedupe(items)[:5]

    def _action_plan(
        self,
        rule_ids: list[str],
        domains: list[str],
        triggers: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        """Turn abstract luck-cycle hints into conservative practical actions."""

        can_do: list[str] = []
        first_steps: list[str] = []
        avoid: list[str] = []
        checkpoints: list[str] = []
        domain_set = set(domains)
        rule_set = set(rule_ids)

        if domain_set & {"事业", "事业平台", "工作环境"}:
            can_do.extend([
                "把岗位、项目、客户或考试目标重新排优先级，选一个主线持续推进。",
                "主动整理作品、简历、证书、项目复盘或可交付成果，让能力被看见。",
            ])
            first_steps.extend([
                "先列出当前最重要的 3 件事：哪件能带来长期信用，哪件只是消耗精力。",
                "把关键任务拆成时间表、交付物和负责人，减少临时应付。",
            ])
            avoid.extend([
                "不要同时开太多项目，也不要因为一时不顺就马上推翻主线。",
                "重要协作尽量留文字确认，避免口头理解不一致。",
            ])
            checkpoints.append("核对工作中是否出现新上级、新规则、新任务、换团队、换方向或考核标准变化。")

        if "阶段性变化" in domain_set:
            can_do.append("适合把拖着没处理的阶段问题做一次整理：目标、关系、项目、作息或环境，选最卡的一项先动。")
            first_steps.append("先写一个本年主问题：到底是方向不清、资源不够、关系拉扯，还是执行节奏乱。")
            avoid.append("不要同时重启太多人生模块，先处理最影响全局的一项。")
            checkpoints.append("核对这一年是否有某个老问题反复出现，逼你重新安排阶段目标。")

        if domain_set & {"财务"}:
            can_do.extend([
                "梳理收入来源、固定支出、项目投入和现金流，把主收入与副机会分开看。",
                "适合做预算、降负债、清理低效支出或复盘赚钱方式。",
            ])
            first_steps.extend([
                "先写出本年最该保住的收入来源，以及最容易失控的支出项。",
                "新投入先设上限和退出条件，再看收益空间。",
            ])
            avoid.extend([
                "不要把命理信号当投资买卖依据，也不要为了追机会加杠杆。",
                "避免人情合作、模糊分账和没有退出机制的投入。",
            ])
            checkpoints.append("核对收入结构、支出压力、合作分账或项目投入产出是否比平时更需要调整。")

        if domain_set & {"合作", "婚恋", "关系或合作拉扯"} or "year_001" in rule_set:
            can_do.extend([
                "适合修正沟通方式，重新谈清合作分工、关系边界和彼此期待。",
                "关系议题先处理现实压力，再讨论对错输赢。",
            ])
            first_steps.extend([
                "先把对方真正要什么、自己能给什么、不能接受什么写清楚。",
                "重要约定拆成时间、责任、费用、边界四项确认。",
            ])
            avoid.extend([
                "不要在情绪高点做分合、合作去留、搬迁等重大决定。",
                "不要用猜测代替沟通，也不要让长期问题继续模糊下去。",
            ])
            checkpoints.append("核对关系、合作、亲密互动或居住节奏是否需要重新定边界。")

        if domain_set & {"居住", "迁动", "环境调整"}:
            can_do.extend([
                "适合整理居住、通勤、办公地点、出差安排和生活动线。",
                "如果有搬迁、装修、换城市或换工位想法，先做成本和时间评估。",
            ])
            first_steps.extend([
                "先准备证件、合同、预算、时间表和备用方案。",
                "把必须变的、可以等的、不能冒险的事项分开。",
            ])
            avoid.extend([
                "不要只凭一时冲动搬迁、签约或大额购置。",
                "环境变化前先留缓冲期，避免工作和生活同时失序。",
            ])
            checkpoints.append("核对是否有通勤、住处、办公方式、出差频率或生活节奏改变。")

        if "year_003" in rule_set:
            can_do.insert(0, "适合集中解决一个反复出现的阶段主线，不适合四面出击。")
            first_steps.insert(0, "选一个最关键主题做 90 天计划，其余事项降级处理。")
            avoid.insert(0, "避免把所有问题都放在同一年硬推，越集中越要做减法。")

        if "year_004" in rule_set or "year_008" in rule_set:
            can_do.insert(0, "适合复盘旧项目、旧关系、旧习惯，看看哪些能修复，哪些该结束。")
            first_steps.insert(0, "先找出重复出现的问题模式：是人、规则、钱、时间，还是自己的处理方式。")
            avoid.insert(0, "不要用旧办法处理旧问题，否则容易只是重复消耗。")

        if "year_005" in rule_set:
            can_do.insert(0, "适合提前处理变化：合同、出行、岗位、合作、财务安排都留缓冲。")
            first_steps.insert(0, "任何大决定先等一轮信息确认，再做备选方案 A/B。")
            avoid.insert(0, "不要把外部压力下的冲动当成最终判断。")

        if "year_006" in rule_set or "year_007" in rule_set:
            can_do.insert(0, "可以主动连接资源、合作、人脉或项目，把分散机会聚到一个清晰主题上。")
            first_steps.insert(0, "先判断合作是否服务主线：能不能带来长期信用、能力沉淀或稳定回报。")
            avoid.insert(0, "合动和聚合不等于都要接，边界不清的机会宁可慢一点。")

        if any(trigger.get("repeat_context", {}).get("same_palace_repeat") for trigger in triggers):
            checkpoints.append("同一主题被重复引动，现实中若已经有苗头，就优先提前安排，而不是等到临时处理。")

        if not can_do:
            can_do.append("先把这一年当作观察窗口，记录最先被引动的现实领域，再决定动作。")
        if not first_steps:
            first_steps.append("先做一页纸计划：目标、现实限制、可用资源、最小下一步。")
        if not avoid:
            avoid.append("避免只凭单一年份做重大人生结论，先看现实证据是否配合。")
        if not checkpoints:
            checkpoints.append("用现实反馈校验：哪一类主题在这一年比平时更常被提起或被迫处理。")

        return {
            "can_do": self._dedupe(can_do)[:4],
            "first_steps": self._dedupe(first_steps)[:4],
            "avoid": self._dedupe(avoid)[:4],
            "checkpoints": self._dedupe(checkpoints)[:4],
        }

    def _priority_focus(self, rule_ids: list[str], domains: list[str]) -> str:
        domain_set = set(domains)
        rule_set = set(rule_ids)
        if "year_005" in rule_set:
            return "变化管理：先稳住合同、出行、合作、岗位或财务安排，重大决定留缓冲。"
        if "year_003" in rule_set:
            return "主线收束：这一年更适合集中处理一个核心主题，少开新战线。"
        if "year_007" in rule_set:
            return "资源聚合：把人脉、项目、学习或工作资源集中到一个清晰主题上。"
        if "year_006" in rule_set:
            return "合作连接：可以主动协商、牵线和整合资源，但要先定边界。"
        if "year_004" in rule_set or "year_008" in rule_set:
            return "旧事复盘：重点看重复出现的人、事、习惯，换一种处理方式。"
        if domain_set & {"事业", "事业平台", "工作环境"}:
            return "事业节奏：把岗位、项目、平台规则和可见成果放在第一位。"
        if domain_set & {"财务"}:
            return "资源取舍：先保现金流和主收入，副机会要看投入产出。"
        if domain_set & {"合作", "婚恋", "关系或合作拉扯"} or "year_001" in rule_set:
            return "关系边界：先谈清分工、期待、责任和退出条件。"
        if domain_set & {"居住", "迁动", "环境调整"}:
            return "环境调整：先做预算、时间表和备用方案，再决定搬动或切换。"
        if "阶段性变化" in domain_set:
            return "阶段整理：先找出最卡的现实问题，再做小步调整。"
        return "观察调整：先记录现实中最先被引动的领域，再决定动作。"

    def _dedupe(self, items: list[str]) -> list[str]:
        result = []
        for item in items:
            if item and item not in result:
                result.append(item)
        return result

    def _join(self, items: list[Any]) -> str:
        return "、".join(str(item) for item in items if item)

    def _clean_summary(self, text: str) -> str:
        return text
