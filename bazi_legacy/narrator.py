# ==============================================================================
# narrator.py —— 八字分层输出引擎 v2.0
#
# 核心原则：确定的和待判断的必须分开
#
# 确定层 (certain)：脚本直接计算，结果唯一，无歧义
#   - 四柱干支、真太阳时
#   - 全柱十神分布（每个干支对日主的关系）
#   - 月令本气 + 格局名称
#   - 地支刑冲合（事实扫描）
#   - 调候用神（查表结果，原文照录）
#   - 大运干支序列 + 起运岁数
#
# 待判断层 (assessment)：脚本给出依据和倾向，但明确标注不确定性
#   - 格局成败状态（成/败/救应）+ 原典依据
#   - 日主强弱倾向（得令/有根/有助三维度分开列）
#   - 调候是否满足（查表结果与原局对照）
#
# 不做层 (out_of_scope)：明确声明脚本不处理
#   - 吉凶断语
#   - 大运流年互动
#   - 具体事件预测
# ==============================================================================

import json
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from bazi_engine import BaziChart
from evaluator import (
    PatternManager, SituationReader,
    get_ten_god, GAN_WU_XING, ZHI_CANG_GAN,
    SHENG, XIANG_CHONG, GAN_HE, ZHI_LIU_HE, ZHI_SAN_HE,
    YANG_GAN,
)
from tiao_hou_yong_shen import query_yong_shen
from advanced_patterns import (
    check_cong_ge, check_hua_qi_ge, check_jian_ge,
    assess_yong_shen_priority, assess_ge_ju_level,
    assess_tou_gan_strength, assess_chong_he_dynamic,
    assess_qing_zhuo,
    build_liuqin_map, verify_liuqin, assess_liuqin_quality,
)


# ==============================================================================
# 月令旺相休囚死强度表
# ==============================================================================

YUE_LING_STRENGTH = {
    "木": {"寅":4,"卯":4,"辰":1,"巳":0.5,"午":0.5,"未":0.5,
            "申":0,"酉":0,"戌":0.5,"亥":3,"子":3,"丑":1},
    "火": {"寅":3,"卯":3,"辰":1,"巳":4,"午":4,"未":1,
            "申":0,"酉":0,"戌":0.5,"亥":0,"子":0,"丑":0.5},
    "土": {"寅":0.5,"卯":0,"辰":4,"巳":3,"午":3,"未":4,
            "申":1,"酉":1,"戌":4,"亥":0.5,"子":0,"丑":4},
    "金": {"寅":0,"卯":0,"辰":3,"巳":0,"午":0,"未":0.5,
            "申":4,"酉":4,"戌":1,"亥":1,"子":1,"丑":3},
    "水": {"寅":1,"卯":0.5,"辰":0.5,"巳":0,"午":0,"未":0,
            "申":3,"酉":3,"戌":0,"亥":4,"子":4,"丑":3},
}

KE = {"木":"土","土":"水","水":"火","火":"金","金":"木"}


# ==============================================================================
# 确定层：全柱十神分布
# ==============================================================================

def _build_ten_gods_map(chart: BaziChart) -> dict:
    """
    列出四柱八字每个字对日主的十神关系。
    天干和地支分开，地支按藏干列出（主气/中气/余气）。
    结果唯一，无歧义。
    """
    ri = chart.ri_gan
    pillars = [
        ("年", chart.nian_gan, chart.nian_zhi),
        ("月", chart.yue_gan,  chart.yue_zhi),
        ("日", chart.ri_gan,   chart.ri_zhi),
        ("时", chart.shi_gan,  chart.shi_zhi),
    ]

    result = []
    for pos, gan, zhi in pillars:
        # 天干十神
        gan_god = get_ten_god(ri, gan) if gan != ri else "日主"

        # 地支藏干十神（主气/中气/余气）
        cang = ZHI_CANG_GAN.get(zhi, [])
        zhi_gods = []
        labels = ["主气", "中气", "余气"]
        for i, cg in enumerate(cang):
            zhi_gods.append({
                "gan":   cg,
                "label": labels[i] if i < len(labels) else "余气",
                "god":   get_ten_god(ri, cg),
            })

        result.append({
            "pillar":   pos + "柱",
            "gan":      gan,
            "gan_god":  gan_god,
            "zhi":      zhi,
            "zhi_cang": zhi_gods,
        })

    return result


# ==============================================================================
# 确定层：地支刑冲合扫描
# ==============================================================================

# 地支相刑（三刑 + 自刑）
XIANG_XING = [
    ({"寅","巳","申"}, "寅巳申三刑"),
    ({"丑","戌","未"}, "丑戌未三刑"),
    ({"子","卯"},      "子卯相刑"),
    ({"辰","辰"},      "辰自刑"),
    ({"午","午"},      "午自刑"),
    ({"酉","酉"},      "酉自刑"),
    ({"亥","亥"},      "亥自刑"),
]

# 地支相害
XIANG_HAI = [
    ({"子","未"}, "子未相害"),
    ({"丑","午"}, "丑午相害"),
    ({"寅","巳"}, "寅巳相害"),  # 注：与三刑有重叠，独立列出
    ({"卯","辰"}, "卯辰相害"),
    ({"申","亥"}, "申亥相害"),
    ({"酉","戌"}, "酉戌相害"),
]


def _scan_zhi_relations(chart: BaziChart) -> dict:
    """
    扫描四柱地支的所有刑冲合害关系。
    只报告事实，不做吉凶判断。
    """
    zhis = [chart.nian_zhi, chart.yue_zhi, chart.ri_zhi, chart.shi_zhi]
    zhi_set  = set(zhis)
    zhi_list = list(zhis)  # 保留重复（用于自刑检测）

    chong, liu_he, san_he, xing, hai = [], [], [], [], []

    # 相冲
    for i, z1 in enumerate(zhi_list):
        for j, z2 in enumerate(zhi_list):
            if i < j and (z1, z2) in XIANG_CHONG:
                chong.append(f"{z1}{z2}相冲")

    # 六合
    for (za, zb), label in [
        (("子","丑"),"子丑合土"),(("寅","亥"),"寅亥合木"),
        (("卯","戌"),"卯戌合火"),(("辰","酉"),"辰酉合金"),
        (("巳","申"),"巳申合水"),(("午","未"),"午未合火"),
    ]:
        if za in zhi_set and zb in zhi_set:
            liu_he.append(label)

    # 三合局
    san_he_defs = [
        ({"申","子","辰"}, "申子辰三合水局"),
        ({"寅","午","戌"}, "寅午戌三合火局"),
        ({"巳","酉","丑"}, "巳酉丑三合金局"),
        ({"亥","卯","未"}, "亥卯未三合木局"),
    ]
    for combo, label in san_he_defs:
        if combo <= zhi_set:
            san_he.append(label)

    # 相刑
    for combo, label in XIANG_XING:
        if len(combo) == 2:
            c = list(combo)
            if c[0] == c[1]:  # 自刑：需出现两次
                if zhi_list.count(c[0]) >= 2:
                    xing.append(label)
            else:
                if combo <= zhi_set:
                    xing.append(label)
        else:
            if combo <= zhi_set:
                xing.append(label)

    # 相害
    for combo, label in XIANG_HAI:
        if combo <= zhi_set:
            hai.append(label)

    # 天干五合
    gans = [chart.nian_gan, chart.yue_gan, chart.ri_gan, chart.shi_gan]
    gan_he_found = []
    gan_he_defs = [
        (("甲","己"),"甲己合土"),(("乙","庚"),"乙庚合金"),
        (("丙","辛"),"丙辛合水"),(("丁","壬"),"丁壬合木"),
        (("戊","癸"),"戊癸合火"),
    ]
    gan_set = set(gans)
    for (g1, g2), label in gan_he_defs:
        if g1 in gan_set and g2 in gan_set:
            gan_he_found.append(label)

    return {
        "天干五合": gan_he_found,
        "地支相冲": chong,
        "地支六合": liu_he,
        "地支三合": san_he,
        "地支相刑": xing,
        "地支相害": hai,
        "备注": "以上为事实扫描，合冲是否成立需结合间隔位置进一步判断",
    }


# ==============================================================================
# 确定层：调候用神（查表，原文照录）
# ==============================================================================

def _build_tiaohou(chart: BaziChart) -> dict:
    """
    查《穷通宝鉴》调候用神表，原文照录，不做额外推断。
    """
    result = query_yong_shen(chart.ri_gan, chart.yue_ling)
    if not result:
        return {"status": "查表未命中", "ri_gan": chart.ri_gan, "yue_ling": chart.yue_ling}

    # 原局天干中有哪些调候用神已透干
    all_gans = {chart.nian_gan, chart.yue_gan, chart.shi_gan}  # 排除日主
    shou_xuan  = result.get("首选用神", [])
    ci_xuan    = result.get("次选用神", [])
    ji_shen    = result.get("忌神", [])

    shou_tou   = [g for g in shou_xuan if g in all_gans]
    ci_tou     = [g for g in ci_xuan   if g in all_gans]
    ji_tou     = [g for g in ji_shen   if isinstance(g, str) and g in all_gans]

    return {
        "日主":     chart.ri_gan,
        "月令":     chart.yue_ling,
        "首选用神": shou_xuan,
        "次选用神": ci_xuan,
        "忌神":     ji_shen,
        "原局已透首选": shou_tou,
        "原局已透次选": ci_tou,
        "原局已透忌神": ji_tou,
        "成格提示": result.get("成格条件", ""),
        "破格提示": result.get("破格条件", ""),
        "数据来源": f"《穷通宝鉴》{chart.ri_gan}日主{chart.yue_ling}条目（原文照录）",
    }


# ==============================================================================
# 确定层：大运列表
# ==============================================================================

def _build_dayun(chart: BaziChart) -> Optional[dict]:
    """大运数据直接来自 bazi_engine，已经过算法验证。"""
    if not chart.dayun:
        return None
    d = chart.dayun
    return {
        "排列方向":   d["direction"],
        "起运岁数":   f"{d['qi_yun_year_int']}岁{d['qi_yun_month_rem']}月",
        "交运公历年": d["qi_yun_calendar_year"],
        "起运天数":   d["qi_yun_days"],
        "大运列表": [
            {
                "步": i + 1,
                "干支": step["ganzhi"],
                "起始年": step["start_year"],
                "起始岁": step["age"],
            }
            for i, step in enumerate(d["dayun_list"])
        ],
    }


# ==============================================================================
# 待判断层：日主强弱（三维度分开，不合并成单一结论）
# ==============================================================================

def _assess_strength(chart: BaziChart) -> dict:
    """
    日主强弱三维度独立评估。
    不给"身强/身弱"的唯一结论，而是把三个维度的证据分别列出。
    综合倾向只给方向性描述，置信度标注。

    三个维度来自《子平真诠》核心原则：
      得令：月令是否帮身（最重要）
      有根：地支是否有日主五行的根气
      有助：天干是否有比劫或印绶帮扶
    """
    ri      = chart.ri_gan
    ri_wx   = GAN_WU_XING[ri]
    all_gans = [chart.nian_gan, chart.yue_gan, chart.ri_gan, chart.shi_gan]
    all_zhis = [chart.nian_zhi, chart.yue_zhi, chart.ri_zhi, chart.shi_zhi]
    non_ri   = [g for g in all_gans if g != ri]

    # ── 得令 ──────────────────────────────────────────────────────────────────
    ling_score = YUE_LING_STRENGTH.get(ri_wx, {}).get(chart.yue_zhi, 0)
    if ling_score >= 3:
        de_ling_verdict = "得令"
        de_ling_note    = f"月令{chart.yue_zhi}对{ri_wx}强度={ling_score}（旺/相）"
    elif ling_score >= 1:
        de_ling_verdict = "中性"
        de_ling_note    = f"月令{chart.yue_zhi}对{ri_wx}强度={ling_score}（休）"
    else:
        de_ling_verdict = "失令"
        de_ling_note    = f"月令{chart.yue_zhi}对{ri_wx}强度={ling_score}（囚/死）"

    # ── 有根 ──────────────────────────────────────────────────────────────────
    roots = []
    for zhi in all_zhis:
        for i, cg in enumerate(ZHI_CANG_GAN.get(zhi, [])):
            if GAN_WU_XING.get(cg) == ri_wx:
                weight = ["主气", "中气", "余气"][i] if i < 3 else "余气"
                roots.append(f"{zhi}藏{cg}（{weight}）")

    you_gen_verdict = "有根" if roots else "无根"

    # ── 有助 ──────────────────────────────────────────────────────────────────
    helpers  = []   # 比劫 + 印绶（帮扶日主）
    drainers = []   # 官杀 + 财星 + 食伤（克泄日主）

    for g in non_ri:
        god = get_ten_god(ri, g)
        if god in ("比肩", "劫财"):
            helpers.append(f"{g}（{god}）")
        elif god in ("正印", "偏印"):
            helpers.append(f"{g}（{god}）")
        elif god in ("正官", "七杀"):
            drainers.append(f"{g}（{god}·克）")
        elif god in ("正财", "偏财"):
            drainers.append(f"{g}（{god}·耗）")
        elif god in ("食神", "伤官"):
            drainers.append(f"{g}（{god}·泄）")

    if len(helpers) > len(drainers):
        you_zhu_verdict = "帮扶多于克泄"
    elif len(helpers) < len(drainers):
        you_zhu_verdict = "克泄多于帮扶"
    else:
        you_zhu_verdict = "帮扶克泄持平"

    # ── 综合倾向 ──────────────────────────────────────────────────────────────
    # 只给倾向，不给唯一结论
    # 得令 > 有根 > 有助（权重参考《子平真诠》"月令为提纲"原则）
    strong_signals = sum([
        ling_score >= 3,            # 得令
        len(roots) >= 2,            # 有根且根多
        len(helpers) > len(drainers),  # 天干帮扶多
    ])
    weak_signals = sum([
        ling_score == 0,            # 失令且死地
        len(roots) == 0,            # 无根
        len(drainers) > len(helpers) + 1,  # 克泄明显多于帮扶
    ])

    if strong_signals >= 2 and weak_signals == 0:
        tendency = "偏强"
        conf     = 0.80
    elif strong_signals >= 2 and weak_signals == 1:
        tendency = "中和偏强"
        conf     = 0.65
    elif weak_signals >= 2 and strong_signals == 0:
        tendency = "偏弱"
        conf     = 0.80
    elif weak_signals >= 2 and strong_signals == 1:
        tendency = "中和偏弱"
        conf     = 0.65
    else:
        tendency = "中和（信号矛盾，需进一步判断）"
        conf     = 0.50

    return {
        "得令": {
            "结论": de_ling_verdict,
            "依据": de_ling_note,
        },
        "有根": {
            "结论": you_gen_verdict,
            "根气列表": roots if roots else ["无日主五行根气"],
        },
        "有助": {
            "结论": you_zhu_verdict,
            "帮扶": helpers if helpers else ["无"],
            "克泄": drainers if drainers else ["无"],
        },
        "综合倾向": tendency,
        "置信度":   conf,
        "重要说明": (
            "以上三个维度是独立事实，综合倾向仅供参考。"
            "强弱最终判断需结合格局整体，不宜单独定论。"
        ),
    }


# ==============================================================================
# 待判断层：格局成败（来自 PatternManager，附原典依据）
# ==============================================================================

def _assess_pattern(chart: BaziChart, s: SituationReader) -> dict:
    """
    格局成败判定。依据严格来自《子平真诠》，附出处。
    同时检测月令本气是否透干（透干则格局根力更足）。
    """
    pm     = PatternManager()
    result = pm.analyze(chart)

    # 月令本气是否透干
    non_ri = [g for g in [chart.nian_gan, chart.yue_gan, chart.shi_gan]]
    ben_qi_tou = s.yue_ben_qi in non_ri

    # 透干的十神（除月令本气外，去重）
    seen = set()
    other_tou = []
    for g in non_ri:
        god = get_ten_god(chart.ri_gan, g)
        if god not in ("日主", "未知") and g != s.yue_ben_qi and g not in seen:
            seen.add(g)
            other_tou.append({"干": g, "十神": god})

    return {
        "月令":       chart.yue_ling,
        "月令本气":   s.yue_ben_qi,
        "月令十神":   s.pattern_god,
        "本气透干":   ben_qi_tou,
        "格局名称":   result["main_pattern"],
        "成败状态":   result["status"],   # 成 / 败 / 救应
        "判定依据":   result["reason"],   # 严格来自原典
        "其他透干十神": other_tou,
        "备注": (
            "格局名称和成败状态依据《子平真诠》八格成败救应规则，"
            "本气未透干时格局根力相对偏弱。"
            "其他透干十神可能影响格局发用方向，需综合判断。"
        ),
    }


# ==============================================================================
# 待判断层：调候满足度对照
# ==============================================================================

def _assess_tiaohou_match(tiaohou: dict, chart: BaziChart) -> dict:
    """
    把调候查表结果与原局实际对照，给出满足程度。
    不做吉凶结论，只报告"有无"和"程度"。
    """
    shou  = tiaohou.get("首选用神", [])
    ci    = tiaohou.get("次选用神", [])
    ji    = tiaohou.get("忌神", [])
    s_tou = tiaohou.get("原局已透首选", [])
    c_tou = tiaohou.get("原局已透次选", [])
    j_tou = tiaohou.get("原局已透忌神", [])

    if not shou:
        return {"满足度": "无调候数据"}

    if s_tou:
        degree = "首选用神已透干"
    elif c_tou:
        degree = "次选用神已透干，首选未透"
    elif not s_tou and not c_tou:
        degree = "调候用神均未透干"
    else:
        degree = "部分满足"

    ji_note = f"忌神{j_tou}已透干，需注意" if j_tou else "忌神未透干"

    return {
        "满足程度": degree,
        "忌神情况": ji_note,
        "说明": "调候判断来自《穷通宝鉴》，仅反映寒暖燥湿的气候背景，不直接等同格局成败",
    }


# ==============================================================================
# 主引擎
# ==============================================================================

class NarratorEngine:
    """
    八字分层输出引擎 v2.0

    用法：
        engine = NarratorEngine()
        result = engine.narrate(1989, 5, 20, 15, 30, gender="男")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    """

    def narrate(
        self,
        year: int, month: int, day: int,
        hour: int, minute: int = 0,
        longitude: float = 116.4,
        gender: Optional[str] = None,
    ) -> dict:

        chart   = BaziChart(year, month, day, hour, minute,
                            longitude=longitude, gender=gender)
        s       = SituationReader(chart)
        tiaohou = _build_tiaohou(chart)

        return {
            # ── 基本信息 ──────────────────────────────────────────────────────
            "basic_info": {
                "公历":   f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
                "真太阳时": f"{chart.tst_hour:02d}:{chart.tst_minute:02d}",
                "经度":   longitude,
                "性别":   gender or "未提供",
                "四柱": {
                    "年柱": chart.nian_zhu,
                    "月柱": chart.yue_zhu,
                    "日柱": chart.ri_zhu,
                    "时柱": chart.shi_zhu,
                },
                "日主": chart.ri_gan,
                "月令": chart.yue_ling,
            },

            # ── 确定层 ────────────────────────────────────────────────────────
            "certain": {
                "_说明": "以下内容由脚本直接计算，结果唯一，无歧义",
                "十神分布":    _build_ten_gods_map(chart),
                "地支刑冲合": _scan_zhi_relations(chart),
                "合冲动态判断": assess_chong_he_dynamic(chart),
                "调候用神":   tiaohou,
                "大运":       _build_dayun(chart),
                "健康对应":   _build_health_map(chart),
                "六亲对应":   build_liuqin_map(chart),
            },

            # ── 待判断层 ──────────────────────────────────────────────────────
            "assessment": {
                "_说明": "以下内容脚本给出依据和倾向，但存在不确定性，标注置信度",
                "从格检测":   check_cong_ge(chart),
                "化气格检测": check_hua_qi_ge(chart),
                "格局成败":   _assess_pattern(chart, s),
                "兼格检测":   check_jian_ge(
                                  chart,
                                  _assess_pattern(chart, s)["格局名称"]
                              ),
                "用神优先级": assess_yong_shen_priority(
                                  chart,
                                  _assess_pattern(chart, s)["格局名称"],
                                  _assess_pattern(chart, s)["成败状态"],
                                  tiaohou,
                              ),
                "十神清浊":   assess_qing_zhuo(
                                  chart,
                                  _assess_pattern(chart, s)["格局名称"],
                                  _assess_strength(chart),
                              ),
                "格局高低":   assess_ge_ju_level(
                                  chart,
                                  _assess_pattern(chart, s)["格局名称"],
                                  _assess_pattern(chart, s)["成败状态"],
                                  _assess_strength(chart),
                              ),
                "透干力量":   assess_tou_gan_strength(chart),
                "日主强弱":   _assess_strength(chart),
                "调候满足度": _assess_tiaohou_match(tiaohou, chart),
                "六亲质量":   assess_liuqin_quality(
                                  chart,
                                  _assess_pattern(chart, s)["格局名称"],
                                  _assess_pattern(chart, s)["成败状态"],
                              ),
            },

            # ── 不做层 ────────────────────────────────────────────────────────
            "out_of_scope": [
                "吉凶断语：脚本不输出，需人工结合格局与大运流年综合判断",
                "大运流年互动：脚本只提供大运干支，不分析与本命的具体作用",
                "具体事件预测：财富、婚姻、健康等具体断法不在脚本范围内",
            ],
        }


def _build_health_map(chart: BaziChart) -> dict:
    """
    根据四柱天干地支，列出对应的脏腑和身体部位。
    数据来自《渊海子平·论疾病》，原文照录，结果唯一无歧义。

    注意：
    - 此表只列对应关系，不做吉凶判断
    - 某个部位对应的天干地支弱或受克，才涉及健康风险，该判断属于待判断层
    - 出处：《渊海子平·论疾病》
    """
    all_gans = [chart.nian_gan, chart.yue_gan, chart.ri_gan, chart.shi_gan]
    all_zhis = [chart.nian_zhi, chart.yue_zhi, chart.ri_zhi, chart.shi_zhi]

    # 天干对应（去重，保留出现位置）
    gan_health = []
    seen_gans = set()
    pos_names = ["年干", "月干", "日干", "时干"]
    for i, g in enumerate(all_gans):
        if g not in seen_gans:
            seen_gans.add(g)
            gan_health.append({
                "位置":   pos_names[i],
                "天干":   g,
                "脏腑":   GAN_ZANGFU.get(g, ""),
                "身体部位": GAN_SHENTI.get(g, ""),
            })

    # 地支对应（去重）
    zhi_health = []
    seen_zhis = set()
    pos_names_z = ["年支", "月支", "日支", "时支"]
    for i, z in enumerate(all_zhis):
        if z not in seen_zhis:
            seen_zhis.add(z)
            zhi_health.append({
                "位置":     pos_names_z[i],
                "地支":     z,
                "身体部位": ZHI_SHENTI.get(z, ""),
            })

    # 日主对应（重点标出）
    ri_gan = chart.ri_gan
    return {
        "日主对应": {
            "天干":   ri_gan,
            "脏腑":   GAN_ZANGFU.get(ri_gan, ""),
            "身体部位": GAN_SHENTI.get(ri_gan, ""),
            "说明":   "日主天干对应的脏腑为先天体质重点关注部位",
        },
        "四柱天干脏腑对应": gan_health,
        "四柱地支部位对应": zhi_health,
        "数据来源": "《渊海子平·论疾病》（原文照录）",
        "重要说明": (
            "此表为固定对应关系，不做吉凶判断。"
            "具体健康风险需结合该天干地支在命局中是否受克、是否失令等因素综合判断，"
            "该判断不在脚本范围内。"
        ),
    }


# ==============================================================================
# 命令行入口
# ==============================================================================

if __name__ == "__main__":
    engine = NarratorEngine()
    print("八字分层输出引擎 v2.0")
    print("─" * 48)
    while True:
        raw = input("\n时间(年,月,日,时,分，q退出): ").strip()
        if raw.lower() == "q":
            break
        try:
            parts = [int(x.strip()) for x in raw.replace("，", ",").split(",")]
            g = input("性别(男/女，回车跳过): ").strip() or None
            if g not in ("男", "女"):
                g = None
            result = engine.narrate(*parts, gender=g)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            import traceback
            print(f"错误: {e}")
            traceback.print_exc()

# ==============================================================================
# 健康对应表（确定层）
# 出处：《渊海子平》论疾病
# 天干对应脏腑，地支对应身体部位
# ==============================================================================

# 天干对应脏腑
# 出处：《渊海子平·论疾病》
# '甲肝，乙胆，丙小肠，丁心，戊胃，己脾乡，庚是大肠，辛属肺，壬是膀胱，癸肾脏'
GAN_ZANGFU = {
    "甲": "肝", "乙": "胆",
    "丙": "小肠", "丁": "心",
    "戊": "胃",  "己": "脾",
    "庚": "大肠", "辛": "肺",
    "壬": "膀胱", "癸": "肾",
}

# 天干对应身体部位
# 出处：《渊海子平·论疾病》
# '甲头，乙项，丙肩求，丁心，戊胁，己属腹，庚係人脐，辛为股，壬脛，癸足自来求'
GAN_SHENTI = {
    "甲": "头", "乙": "项（颈）",
    "丙": "肩", "丁": "心胸",
    "戊": "胁", "己": "腹",
    "庚": "脐", "辛": "股（大腿）",
    "壬": "胫（小腿）", "癸": "足",
}

# 地支对应身体部位
# 出处：《渊海子平·论疾病》
# '子疝气，丑肚腹，寅臂肢，卯目手，辰背胸，巳面齿，午心腹，未脾胸，申咳疾，酉肝肺，戌背肺，亥头肝'
ZHI_SHENTI = {
    "子": "疝气（泌尿生殖）",
    "丑": "肚腹",
    "寅": "臂肢",
    "卯": "目、手",
    "辰": "背、胸",
    "巳": "面、齿",
    "午": "心腹",
    "未": "脾、胸",
    "申": "咳疾（肺气）",
    "酉": "肝、肺",
    "戌": "背、肺",
    "亥": "头、肝",
}

