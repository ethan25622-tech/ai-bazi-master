"""Traditional lifestyle application layer for readable Bazi reports."""

from __future__ import annotations

from typing import Any

from .luck_advice import LuckAdviceEngine


ELEMENT_PROFILES = {
    "木": {
        "colors": ["绿色", "青色", "浅蓝绿色"],
        "materials": ["木质", "纸本", "棉麻", "植物"],
        "work_environments": ["教育培训", "内容策划", "文化出版", "咨询辅导", "成长型项目", "产品孵化"],
        "residence": ["采光柔和", "通风好", "靠近绿地", "适合有书桌和植物的空间"],
        "direction": "传统取象偏东方、东南方，现实上对应生发、学习、绿植和通风。",
        "objects": ["绿植", "木质书桌", "书架", "笔记本", "学习计划板"],
        "daily_actions": ["保持学习输入", "整理长期计划", "做内容沉淀", "让空间有生长感"],
    },
    "火": {
        "colors": ["红色", "紫色", "暖橙色", "暖白色"],
        "materials": ["灯光", "电子设备", "影像", "香薰", "暖色织物"],
        "work_environments": ["传播表达", "品牌营销", "直播影像", "设计展示", "教育演讲", "前台曝光型岗位"],
        "residence": ["采光充足", "温暖明亮", "避免长期阴冷潮湿", "适合有稳定照明的工作区"],
        "direction": "传统取象偏南方，现实上对应光照、曝光、表达和温暖环境。",
        "objects": ["台灯", "暖光灯", "展示墙", "红橙点缀物", "日程提醒工具"],
        "daily_actions": ["固定输出", "增加表达机会", "保持运动出汗", "避免昼夜颠倒"],
    },
    "土": {
        "colors": ["黄色", "米色", "咖色", "大地色"],
        "materials": ["陶瓷", "石材", "皮革", "收纳柜", "厚重织物"],
        "work_environments": ["运营管理", "地产家居", "供应链", "项目管理", "行政后勤", "稳定服务"],
        "residence": ["地气稳定", "收纳清楚", "少杂乱", "适合稳定作息和固定动线"],
        "direction": "传统取象偏中宫、东北、西南，现实上对应稳定、承载、收纳和长期责任。",
        "objects": ["收纳柜", "陶瓷杯", "计划本", "预算表", "稳定座椅"],
        "daily_actions": ["做预算", "整理空间", "固定作息", "把计划落成步骤"],
    },
    "金": {
        "colors": ["白色", "金色", "银色", "灰色"],
        "materials": ["金属", "玻璃", "精密工具", "规则表格", "清洁用品"],
        "work_environments": ["金融风控", "法律合规", "技术工程", "数据分析", "审计质检", "制度标准"],
        "residence": ["空间整洁", "线条清楚", "物品少而精", "适合有明确分区的工作台"],
        "direction": "传统取象偏西方、西北方，现实上对应规则、标准、技术、边界和取舍。",
        "objects": ["金属笔", "文件夹", "清单工具", "机械键盘", "计时器"],
        "daily_actions": ["建立标准", "清理冗余", "训练边界", "用数据和证据说话"],
    },
    "水": {
        "colors": ["黑色", "深蓝色", "灰蓝色"],
        "materials": ["水景", "镜面", "流动线条", "玻璃", "深色织物"],
        "work_environments": ["信息流通", "贸易物流", "研究分析", "心理咨询", "跨地域业务", "流动型资源整合"],
        "residence": ["安静", "湿度适中", "动线流畅", "适合靠近水域但不过度潮湿"],
        "direction": "传统取象偏北方，现实上对应流动、信息、思考、迁移和资源暗线。",
        "objects": ["水杯", "深色笔记本", "加湿/除湿工具", "资料库", "行程管理工具"],
        "daily_actions": ["整理信息", "保持睡眠", "做复盘", "给情绪和思考留流动空间"],
    },
}


PATTERN_CAREER_TYPES = {
    "pattern_004": ["专业资质型", "教育研究型", "知识服务型", "平台背书型"],
    "pattern_005": ["技能输出型", "内容作品型", "服务体验型", "手艺口碑型"],
    "pattern_006": ["目标攻坚型", "管理执行型", "竞争压力型", "风控训练型"],
    "pattern_007": ["表达创意型", "方案策划型", "技术改进型", "产品咨询型"],
    "pattern_009": ["自主经营型", "团队协作型", "同辈竞争型", "资源边界型"],
}


class LifestyleAdviceEngine:
    """Translate existing evidence into traditional but bounded life advice."""

    def __init__(self) -> None:
        self.luck_advice = LuckAdviceEngine()

    def build(self, analysis: dict[str, Any], *, start_year: int | None = None) -> dict[str, Any]:
        useful_elements = self._useful_elements(analysis)
        profiles = [ELEMENT_PROFILES[element] for element in useful_elements if element in ELEMENT_PROFILES]
        return {
            "policy": (
                "以下是传统生活取象层：职业、居住、颜色、材质和物件只作为环境与行为建议，"
                "不等于绝对旺运，也不能替代现实选择。"
            ),
            "useful_elements": useful_elements,
            "career_types": self._career_types(analysis, useful_elements),
            "work_environment": self._work_environment(profiles),
            "residence_guidance": self._residence_guidance(profiles),
            "colors_and_materials": self._colors_and_materials(profiles, useful_elements),
            "daily_objects": self._daily_objects(profiles),
            "daily_habits": self._daily_habits(profiles),
            "avoid_overuse": self._avoid_overuse(analysis, useful_elements),
            "dayun_lifestyle_adjustments": self._dayun_lifestyle_adjustments(analysis, start_year=start_year),
            "evidence": self._evidence(analysis),
        }

    def _useful_elements(self, analysis: dict[str, Any]) -> list[str]:
        facts = analysis.get("facts", {})
        tiaohou = facts.get("tiaohou_yong_shen", {})
        elements: list[str] = []
        if isinstance(tiaohou, dict):
            for key in ("首选用神", "次选用神", "原局已透首选"):
                for item in tiaohou.get(key, []) or []:
                    element = self._stem_element(str(item))
                    if element:
                        elements.append(element)
        assessments = analysis.get("assessments", {})
        yong_summary = str(assessments.get("yong_shen", {}).get("summary") or "")
        for element in ELEMENT_PROFILES:
            if element in yong_summary:
                elements.append(element)
        if not elements:
            day_master = str(analysis.get("chart", {}).get("day_master") or "")
            fallback = self._stem_element(day_master)
            if fallback:
                elements.append(fallback)
        return self._dedupe(elements)[:3]

    def _career_types(self, analysis: dict[str, Any], useful_elements: list[str]) -> list[str]:
        pattern_ids = set(analysis.get("assessments", {}).get("pattern", {}).get("executable_rule_ids") or [])
        items: list[str] = []
        for rule_id in pattern_ids:
            items.extend(PATTERN_CAREER_TYPES.get(str(rule_id), []))
        for element in useful_elements:
            profile = ELEMENT_PROFILES.get(element, {})
            items.extend(profile.get("work_environments", [])[:3])
        return self._dedupe(items)[:10] or ["先看能长期积累信用、作品、资质或稳定客户的工作类型。"]

    def _work_environment(self, profiles: list[dict[str, Any]]) -> list[str]:
        items: list[str] = []
        for profile in profiles:
            items.extend(profile.get("work_environments", [])[:4])
        items.extend([
            "更适合有明确主线、可积累成果、能复盘成长的环境。",
            "若环境长期混乱、权责不清、只靠临场消耗，需要谨慎。",
        ])
        return self._dedupe(items)[:8]

    def _residence_guidance(self, profiles: list[dict[str, Any]]) -> dict[str, Any]:
        environment: list[str] = []
        directions: list[str] = []
        for profile in profiles:
            environment.extend(profile.get("residence", [])[:3])
            if profile.get("direction"):
                directions.append(str(profile["direction"]))
        return {
            "environment": self._dedupe(environment)[:8] or ["优先选择能稳定作息、通风采光适中、动线清楚的居住环境。"],
            "traditional_directions": self._dedupe(directions)[:3],
            "boundary": "方位只按传统五行取象参考，不建议为了方位牺牲现实通勤、预算、安全和生活质量。",
        }

    def _colors_and_materials(self, profiles: list[dict[str, Any]], useful_elements: list[str]) -> dict[str, Any]:
        colors: list[str] = []
        materials: list[str] = []
        for profile in profiles:
            colors.extend(profile.get("colors", [])[:4])
            materials.extend(profile.get("materials", [])[:4])
        return {
            "main_colors": self._dedupe(colors)[:8] or ["选择让自己稳定、清爽、能保持行动力的颜色。"],
            "materials": self._dedupe(materials)[:8],
            "usage": "适合作为衣服、桌面、随身小物、房间点缀的辅助取象；不用全身同色，也不必迷信单一颜色。",
            "based_on": useful_elements,
        }

    def _daily_objects(self, profiles: list[dict[str, Any]]) -> list[str]:
        items: list[str] = []
        for profile in profiles:
            items.extend(profile.get("objects", [])[:4])
        return self._dedupe(items)[:10] or ["固定书桌", "计划本", "收纳工具"]

    def _daily_habits(self, profiles: list[dict[str, Any]]) -> list[str]:
        items: list[str] = []
        for profile in profiles:
            items.extend(profile.get("daily_actions", [])[:4])
        items.extend(["定期复盘现实反馈", "把命理建议落成可执行清单"])
        return self._dedupe(items)[:10]

    def _avoid_overuse(self, analysis: dict[str, Any], useful_elements: list[str]) -> list[str]:
        items = [
            "颜色、方位、物件只是辅助，不要代替行业选择、能力训练和现实判断。",
            "不建议为了所谓旺运盲目搬家、辞职、投资或大额消费。",
        ]
        strength = str(analysis.get("assessments", {}).get("strength", {}).get("summary") or "")
        if "中和" in strength or "矛盾" in strength:
            items.append("强弱信号不宜硬判时，生活取象也要少量试用、观察反馈，不要一次性大改。")
        if useful_elements:
            items.append(f"当前优先取象为{self._join(useful_elements)}，但仍需和大运、流年及现实状态交叉验证。")
        return items

    def _dayun_lifestyle_adjustments(
        self,
        analysis: dict[str, Any],
        *,
        start_year: int | None,
    ) -> list[dict[str, Any]]:
        dayun = self.luck_advice.dayun_integration(analysis, start_year=start_year, max_periods=3)
        periods = dayun.get("periods", []) if isinstance(dayun, dict) else []
        items: list[dict[str, Any]] = []
        for period in periods:
            stem_god = str(period.get("stem_ten_god") or "")
            focus_years = period.get("focus_years", [])
            items.append({
                "period": f"{period.get('start_year')}-{period.get('end_year')} {period.get('ganzhi')}大运",
                "stage_theme": period.get("stage_theme"),
                "work_adjustment": period.get("career_guidance"),
                "money_adjustment": period.get("wealth_guidance"),
                "relationship_adjustment": period.get("relationship_guidance"),
                "lifestyle_adjustment": self._dayun_lifestyle_text(stem_god, period),
                "focus_years": [
                    {
                        "year": year.get("year"),
                        "attention_level": year.get("attention_level"),
                        "action_focus": year.get("action_focus"),
                        "risk_watch": year.get("risk_watch", [])[:1],
                    }
                    for year in focus_years[:3]
                ],
            })
        return items

    def _dayun_lifestyle_text(self, stem_god: str, period: dict[str, Any]) -> str:
        if stem_god in {"正官", "七杀"}:
            return "这步运生活上要重视规则感、作息、运动和压力出口；桌面与工作区宜清楚有序，减少临时硬扛。"
        if stem_god in {"正印", "偏印"}:
            return "这步运适合补学习、证书、方法论和安静空间；但要给输出设截止日期，避免只准备不行动。"
        if stem_god in {"食神", "伤官"}:
            return "这步运适合增加表达、作品、展示和稳定输出；生活上要防熬夜和脑力过载。"
        if stem_god in {"正财", "偏财"}:
            return "这步运要把预算、现金流、收纳和项目成本管清楚；生活物件宜实用，不宜为机会感冲动消费。"
        if stem_god in {"比肩", "劫财"}:
            return "这步运要把个人空间、合作边界和资源分配讲清楚；生活上适合减少人情消耗。"
        return "这步运先观察现实里最先被牵动的领域，再调整工作、居住、颜色和日常习惯。"

    def _evidence(self, analysis: dict[str, Any]) -> list[str]:
        chart = analysis.get("chart", {})
        assessments = analysis.get("assessments", {})
        facts = analysis.get("facts", {})
        evidence = [
            f"日主：{chart.get('day_master')}",
            f"月令：{chart.get('month_command')}",
            f"格局：{assessments.get('pattern', {}).get('summary')}",
            f"强弱：{assessments.get('strength', {}).get('summary')}",
        ]
        tiaohou = facts.get("tiaohou_yong_shen")
        if tiaohou:
            evidence.append(f"调候用神：{tiaohou}")
        return [item for item in evidence if item and "None" not in item]

    def _stem_element(self, stem: str) -> str:
        return {
            "甲": "木", "乙": "木",
            "丙": "火", "丁": "火",
            "戊": "土", "己": "土",
            "庚": "金", "辛": "金",
            "壬": "水", "癸": "水",
        }.get(stem, "")

    def _dedupe(self, items: list[str]) -> list[str]:
        result = []
        for item in items:
            if item and item not in result:
                result.append(item)
        return result

    def _join(self, items: list[Any]) -> str:
        return "、".join(str(item) for item in items if item)
