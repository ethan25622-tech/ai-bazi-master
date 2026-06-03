# ==============================================================================
# advanced_patterns.py —— 《子平真诠》进阶格局判断
#
# 实现内容（全部原文有据，标注出处）：
#   A. 从格判断（从财、从煞）         《四十七、论杂格》
#   B. 化气格判断（五种化气）         《四、论十干配合性情》
#                                     《四十七、论杂格》
#                                     《五、论十干合而不合》
#   C. 兼格识别（7种组合）            《十、论用神变化》等各论
#   D. 用神优先级                     《八、论用神》
#                                     《十四、论用神配气候得失》
#   E. 格局高低评估                   《十二、论用神格局高低》
#
# 设计原则：
#   - 每条规则标注原典出处
#   - 每个函数只做判断，返回结构化结果
#   - 不确定的情况明确说明，不强行给结论
# ==============================================================================

from typing import Optional
from evaluator import (
    get_ten_god, GAN_WU_XING, ZHI_CANG_GAN,
    SHENG, KE, GAN_HE, ZHI_LIU_HE, ZHI_SAN_HE, YANG_GAN,
)
from bazi_engine import BaziChart, DI_ZHI, TIAN_GAN


# ==============================================================================
# 工具函数
# ==============================================================================

def _all_gans(chart: BaziChart) -> list:
    return [chart.nian_gan, chart.yue_gan, chart.ri_gan, chart.shi_gan]

def _non_ri_gans(chart: BaziChart) -> list:
    return [g for g in _all_gans(chart) if g != chart.ri_gan]

def _all_zhis(chart: BaziChart) -> list:
    return [chart.nian_zhi, chart.yue_zhi, chart.ri_zhi, chart.shi_zhi]

def _all_cang_gans(chart: BaziChart) -> list:
    """四柱地支所有藏干（含重复）"""
    result = []
    for zhi in _all_zhis(chart):
        result.extend(ZHI_CANG_GAN.get(zhi, []))
    return result

def _ri_wx(chart: BaziChart) -> str:
    return GAN_WU_XING[chart.ri_gan]

def _has_ten_god(chart: BaziChart, god: str) -> bool:
    """四柱天干（除日主）中是否存在指定十神"""
    return any(get_ten_god(chart.ri_gan, g) == god
               for g in _non_ri_gans(chart))

def _has_ten_god_in_root(chart: BaziChart, god: str) -> bool:
    """地支藏干中是否存在指定十神"""
    ri = chart.ri_gan
    return any(get_ten_god(ri, cg) == god
               for cg in _all_cang_gans(chart))

def _ri_has_root(chart: BaziChart) -> bool:
    """
    日主是否有根（地支藏干含日主五行）。
    出处：《十二、论用神格局高低》
    '身强煞露而食神又旺……三者皆备，极等之贵'
    '煞强食旺而身无根……以其无力也'
    """
    ri_wx = _ri_wx(chart)
    return any(GAN_WU_XING.get(cg) == ri_wx
               for cg in _all_cang_gans(chart))


# ==============================================================================
# A. 从格判断
# 出处：《四十七、论杂格》
# ==============================================================================

def check_cong_ge(chart: BaziChart) -> dict:
    """
    检测从格是否成立。
    当前实现从财格和从煞格两种。

    从财格成立：四柱皆财而身无气，舍而从之。
    从财破格：透印则不从；有官煞则不从。

    从煞格成立：四柱皆煞，日主无根，舍而从之。
    从煞破格：有伤食则煞受制而不从；有印则印化煞而不从。
    """
    ri      = chart.ri_gan
    ri_wx   = _ri_wx(chart)
    non_ri  = _non_ri_gans(chart)
    cang    = _all_cang_gans(chart)
    all_g   = _all_gans(chart)

    # ── 基础条件：日主无根 ────────────────────────────────────────────────────
    ri_has_root = _ri_has_root(chart)

    # 天干（除日主）的十神列表
    tg_gods = [get_ten_god(ri, g) for g in non_ri]
    # 地支藏干十神
    zhi_gods = [get_ten_god(ri, cg) for cg in cang]
    all_gods = tg_gods + zhi_gods

    # ── 从财格 ────────────────────────────────────────────────────────────────
    # 成立：日主无根 + 四柱财星为主（无印绶、无官杀护身）
    has_cai_tg  = any(g in ("正财","偏财") for g in tg_gods)
    has_yin_tg  = any(g in ("正印","偏印") for g in tg_gods)
    has_guan_tg = any(g in ("正官","七杀") for g in tg_gods)
    has_bj_tg   = any(g in ("比肩","劫财") for g in tg_gods)
    has_cai_zhi = any(g in ("正财","偏财") for g in zhi_gods)
    has_yin_zhi = any(g in ("正印","偏印") for g in zhi_gods)
    has_bj_zhi  = any(g in ("比肩","劫财") for g in zhi_gods)

    cong_cai_result = None
    if has_cai_tg and not ri_has_root:
        # 检查破格条件
        if has_yin_tg or has_yin_zhi:
            cong_cai_result = {
                "格名":   "从财格（破）",
                "成立":   False,
                "原因":   "透印则身赖印生而不从，格不成",
                "出处":   "《四十七、论杂格》",
            }
        elif has_guan_tg:
            cong_cai_result = {
                "格名":   "从财格（破）",
                "成立":   False,
                "原因":   "有官煞则无从财兼从煞之理，格不成",
                "出处":   "《四十七、论杂格》",
            }
        elif has_bj_tg or has_bj_zhi:
            cong_cai_result = {
                "格名":   "从财格（破）",
                "成立":   False,
                "原因":   "日主虽无地支根气，天干仍有比劫护身，难以从财",
                "出处":   "《四十七、论杂格》（推论）",
            }
        else:
            cong_cai_result = {
                "格名":   "从财格",
                "成立":   True,
                "原因":   "四柱皆财而身无气，舍而从之，格成大贵",
                "出处":   "《四十七、论杂格》",
                "用神":   "财星，喜食伤生财，喜官星流通",
                "忌神":   "印绶（夺财）、比劫（分财）",
            }

    # ── 从煞格 ────────────────────────────────────────────────────────────────
    has_sha_tg  = any(g == "七杀" for g in tg_gods)
    has_shi_tg  = any(g in ("食神","伤官") for g in tg_gods)
    has_sha_zhi = any(g == "七杀" for g in zhi_gods)

    cong_sha_result = None
    if has_sha_tg and not ri_has_root:
        if has_shi_tg:
            cong_sha_result = {
                "格名":   "从煞格（破）",
                "成立":   False,
                "原因":   "有伤食则煞受制而不从",
                "出处":   "《四十七、论杂格》",
            }
        elif has_yin_tg or has_yin_zhi:
            cong_sha_result = {
                "格名":   "从煞格（破）",
                "成立":   False,
                "原因":   "有印则印以化煞而不从",
                "出处":   "《四十七、论杂格》",
            }
        else:
            cong_sha_result = {
                "格名":   "从煞格",
                "成立":   True,
                "原因":   "四柱皆煞，日主无根，舍而从之，格成大贵",
                "出处":   "《四十七、论杂格》",
                "用神":   "七杀，喜财星生煞，喜印化煞",
                "忌神":   "食伤（制煞）、比劫（帮身抗煞）",
            }

    # ── 汇总 ──────────────────────────────────────────────────────────────────
    candidates = [r for r in [cong_cai_result, cong_sha_result] if r]

    if not candidates:
        return {
            "从格检测": "未入从格",
            "说明":     "日主有根或不满足从格条件，按正常八格处理",
        }

    # 若有成立的从格，正常八格逻辑失效
    cheng_li = [r for r in candidates if r.get("成立")]
    if cheng_li:
        return {
            "从格检测":   "从格成立",
            "格局":       cheng_li[0],
            "重要说明":   "从格成立时，正常八格成败规则失效，用神完全反转",
            "出处":       "《四十七、论杂格》",
        }
    else:
        return {
            "从格检测": "从格条件触发但破格",
            "详情":     candidates,
            "说明":     "具备从格外形但破格，按正常八格处理，格局稳定性略降",
        }


# ==============================================================================
# B. 化气格判断
# 出处：《四、论十干配合性情》《四十七、论杂格》《五、论十干合而不合》
# ==============================================================================

# 五种化气：(干1, 干2, 化出五行, 化出天干举例, 月令支持地支)
HUA_QI_DEFS = [
    ("甲", "己", "土", ["戊","己"], {"辰","戌","丑","未"}),
    ("乙", "庚", "金", ["庚","辛"], {"申","酉","辰","丑"}),
    ("丙", "辛", "水", ["壬","癸"], {"亥","子","申","辰"}),
    ("丁", "壬", "木", ["甲","乙"], {"寅","卯","亥","未"}),
    ("戊", "癸", "火", ["丙","丁"], {"巳","午","寅","戌"}),
]

# 化出五行对应月令强度支持的月支
HUA_YUE_LING_SUPPORT = {
    "土": {"辰","戌","丑","未"},
    "金": {"申","酉","辰","丑"},
    "水": {"亥","子","申","辰"},
    "木": {"寅","卯","亥","未"},
    "火": {"巳","午","寅","戌"},
}

# 三合局对化神的支持
SAN_HE_HUA = {
    "水": {"申","子","辰"},
    "火": {"寅","午","戌"},
    "金": {"巳","酉","丑"},
    "木": {"亥","卯","未"},
}


def check_hua_qi_ge(chart: BaziChart) -> dict:
    """
    检测化气格是否成立。

    成立条件（三级，从高到低）：
      最高：化出之物得时乘令，四支局全（三合全）
      次高：生于化神月令，或有两支化神地支
      基本：日干与他干相合，有化神月令支持

    假化条件（任一即假化）：
      1. 日带根苗劫印（日主有比劫或印）
      2. 化神不足（月令不支持化出五行）
      3. 闲神来伤化气

    出处：
      《四、论十干配合性情》《四十七、论杂格》《五、论十干合而不合》
    """
    ri      = chart.ri_gan
    all_g   = _all_gans(chart)
    non_ri  = _non_ri_gans(chart)
    zhis    = set(_all_zhis(chart))
    yue_zhi = chart.yue_zhi

    results = []

    for g1, g2, hua_wx, hua_gans, support_zhis in HUA_QI_DEFS:
        # 日主必须是合化对中的一个
        if ri not in (g1, g2):
            continue
        # 另一个合化干必须透出
        other = g2 if ri == g1 else g1
        if other not in non_ri:
            continue

        # ── 假化检测（出处：《五、论十干合而不合》）────────────────────────
        jia_hua_reasons = []

        # 假化①：日带根苗劫印（日主五行在地支有根，或天干有比劫/印）
        ri_wx = GAN_WU_XING[ri]
        has_ri_root = any(GAN_WU_XING.get(cg) == ri_wx
                         for cg in _all_cang_gans(chart))
        has_bj = any(get_ten_god(ri, g) in ("比肩","劫财") for g in non_ri)
        has_yin = any(get_ten_god(ri, g) in ("正印","偏印") for g in non_ri)
        if has_ri_root or has_bj or has_yin:
            jia_hua_reasons.append(
                "日带根苗劫印（日主有根气或比劫印绶），化而不化"
            )

        # 假化②：化神不足（月令不支持化出五行）
        yue_support = yue_zhi in HUA_YUE_LING_SUPPORT.get(hua_wx, set())
        if not yue_support:
            jia_hua_reasons.append(
                f"化神不足：月令{yue_zhi}不支持化出{hua_wx}，化而不化"
            )

        # 假化③：闲神来伤化气（化出五行被克制）
        hua_ke_wx = KE.get(hua_wx, "")  # 克化出五行的五行
        has_ke_hua = any(GAN_WU_XING.get(g) == hua_ke_wx for g in non_ri)
        if has_ke_hua:
            jia_hua_reasons.append(
                f"闲神伤化气：天干有{hua_ke_wx}克制化出之{hua_wx}"
            )

        if jia_hua_reasons:
            results.append({
                "化气名称": f"{g1}{g2}化{hua_wx}（假化）",
                "成立":     False,
                "假化原因": jia_hua_reasons,
                "出处":     "《五、论十干合而不合》",
            })
            continue

        # ── 成立等级（出处：《四十七、论杂格》）────────────────────────────
        # 三合全支
        san_he_full = SAN_HE_HUA.get(hua_wx, set()) <= zhis
        # 地支有两个以上支持化神
        zhi_support_count = len(zhis & support_zhis)

        if san_he_full and yue_support:
            grade = "最高（四支局全，得时乘令）"
            detail = f"地支三合{hua_wx}局完整，且月令{yue_zhi}支持化{hua_wx}"
        elif yue_support and zhi_support_count >= 2:
            grade = "次高（月令支持，地支有两位）"
            detail = f"月令{yue_zhi}支持化{hua_wx}，地支有{zhi_support_count}位化神地"
        elif yue_support:
            grade = "基本成立（月令支持）"
            detail = f"月令{yue_zhi}支持化{hua_wx}，但地支化气不够完整"
        else:
            # 理论上不应到达此处（已在假化②排除），保留为兜底
            grade = "存疑"
            detail = "月令不支持，化气存疑"

        results.append({
            "化气名称":   f"{g1}{g2}化{hua_wx}",
            "成立":       True,
            "成立等级":   grade,
            "判断依据":   detail,
            "用神":       f"化出之{hua_wx}，喜生扶化神之物",
            "忌神":       f"克制{hua_wx}之物，及破化之比劫印绶",
            "出处":       "《四、论十干配合性情》《四十七、论杂格》",
        })

    if not results:
        return {"化气格检测": "未入化气格", "说明": "日主未与他干构成天干五合，或条件不足"}

    cheng_li = [r for r in results if r.get("成立")]
    if cheng_li:
        return {
            "化气格检测": "化气格成立",
            "格局":       cheng_li[0],
            "重要说明":   "化气格成立时，正常八格逻辑失效，以化出之物为用神",
        }
    return {
        "化气格检测": "化气条件触发但假化",
        "详情":       results,
        "说明":       "具备化气外形但为假化，按正常八格处理",
    }


# ==============================================================================
# C. 兼格识别
# 出处：各论章节，详见每条规则
# ==============================================================================

def check_jian_ge(chart: BaziChart, primary_pattern: str) -> dict:
    """
    在主格基础上识别兼格组合。
    只有主格成立（status=成或救应）时才检测兼格。

    出处总则：
    '杂气透干会支，一透则一用，兼透则兼用'
    ——《十六、论杂气如何取用》
    """
    ri     = chart.ri_gan
    non_ri = _non_ri_gans(chart)
    zhis   = set(_all_zhis(chart))
    gods   = {get_ten_god(ri, g) for g in non_ri}
    cang_gods = {get_ten_god(ri, cg) for cg in _all_cang_gans(chart)}

    jian_ge_found = []

    # ── 兼格组合一：正官格兼用财印 ──────────────────────────────────────────
    # 出处：《三十一、论正官》
    # 条件：财印并透，两不相碍（财克印则相碍）
    if primary_pattern == "正官格":
        has_cai = any(g in ("正财","偏财") for g in gods)
        has_yin = any(g in ("正印","偏印") for g in gods)
        if has_cai and has_yin:
            # 判断财印是否相碍（财五行是否克印五行）
            cai_gans = [g for g in non_ri if get_ten_god(ri,g) in ("正财","偏财")]
            yin_gans = [g for g in non_ri if get_ten_god(ri,g) in ("正印","偏印")]
            xiang_ai = any(
                KE.get(GAN_WU_XING[c]) == GAN_WU_XING[y]
                for c in cai_gans for y in yin_gans
            )
            if not xiang_ai:
                jian_ge_found.append({
                    "兼格名":   "正官格兼用财印",
                    "成立":     True,
                    "条件":     "财印并透，两不相碍",
                    "用神":     "财生官，印护官，两全其美",
                    "出处":     "《三十一、论正官》",
                })
            else:
                jian_ge_found.append({
                    "兼格名":   "正官格财印同透（相碍）",
                    "成立":     False,
                    "条件":     "财克印，两相碍，兼格不成",
                    "出处":     "《三十一、论正官》",
                })

    # ── 兼格组合二：财格兼用食印 ─────────────────────────────────────────────
    # 出处：《三十三、论财》
    # 条件：食与印两不相碍，或有暗官而去食护官
    if primary_pattern in ("正财格", "偏财格"):
        has_shi = "食神" in gods
        has_yin = any(g in ("正印","偏印") for g in gods)
        has_guan_hidden = any(g in ("正官","七杀") for g in cang_gods)
        if has_shi and has_yin:
            shi_gans = [g for g in non_ri if get_ten_god(ri,g) == "食神"]
            yin_gans = [g for g in non_ri if get_ten_god(ri,g) in ("正印","偏印")]
            xiang_ai = any(
                KE.get(GAN_WU_XING[s]) == GAN_WU_XING[y]
                for s in shi_gans for y in yin_gans
            )
            jian_ge_found.append({
                "兼格名":   "财格兼用食印",
                "成立":     not xiang_ai,
                "条件":     "食与印两不相碍" if not xiang_ai else "食印相碍（印克食），兼格不成",
                "用神":     "食神生财，印护日主，相辅相成" if not xiang_ai else None,
                "出处":     "《三十三、论财》",
            })
        elif has_shi and has_guan_hidden:
            jian_ge_found.append({
                "兼格名":   "财格兼暗官（去食护官）",
                "成立":     True,
                "条件":     "有暗官而去食护官，贵格",
                "出处":     "《三十三、论财》",
            })

    # ── 兼格组合三：印格用煞兼带食伤 ────────────────────────────────────────
    # 出处：《三十五、论印绶》
    # 条件：用煞而有制（食伤制煞），生身而有泄，贵格
    if primary_pattern in ("正印格", "偏印格"):
        has_sha = "七杀" in gods
        has_shi_shang = any(g in ("食神","伤官") for g in gods)
        if has_sha and has_shi_shang:
            jian_ge_found.append({
                "兼格名":   "印格用煞兼带食伤",
                "成立":     True,
                "条件":     "用煞而有制，生身而有泄，不论身旺印重，皆为贵格",
                "用神":     "七杀生印，食伤制煞，三者流通",
                "出处":     "《三十五、论印绶》",
            })

    # ── 兼格组合四：印重财轻兼露食伤 ────────────────────────────────────────
    # 出处：《三十五、论印绶》
    # 条件：印重财轻而兼露食伤，财与食相生，可就富
    if primary_pattern in ("正印格", "偏印格"):
        has_cai = any(g in ("正财","偏财") for g in gods)
        has_shi_shang = any(g in ("食神","伤官") for g in gods)
        if has_cai and has_shi_shang and not ("正官" in gods or "七杀" in gods):
            jian_ge_found.append({
                "兼格名":   "印重财轻兼露食伤",
                "成立":     True,
                "条件":     "印重财轻而兼露伤食，财与食相生，轻而不轻",
                "用神":     "食伤生财，以财制印，偏向富而非贵",
                "出处":     "《三十五、论印绶》",
            })

    # ── 兼格组合五：印格兼透官煞（合煞留官）────────────────────────────────
    # 出处：《三十五、论印绶》
    # 条件：官煞混透，有合煞或有制
    if primary_pattern in ("正印格", "偏印格"):
        has_guan = "正官" in gods
        has_sha  = "七杀" in gods
        sha_gans = [g for g in non_ri if get_ten_god(ri,g) == "七杀"]
        sha_he_qu = any(
            (sg, og) in GAN_HE
            for sg in sha_gans
            for og in non_ri if og != sg
        )
        has_shi = "食神" in gods
        if has_guan and has_sha:
            if sha_he_qu:
                jian_ge_found.append({
                    "兼格名":   "印格兼透官煞（合煞留官）",
                    "成立":     True,
                    "条件":     "官煞混透，合煞留官，官格取清，贵格",
                    "出处":     "《三十五、论印绶》",
                })
            elif has_shi:
                jian_ge_found.append({
                    "兼格名":   "印格兼透官煞（食神制煞）",
                    "成立":     True,
                    "条件":     "官煞混透，食神制煞，官煞有制，贵格",
                    "出处":     "《三十五、论印绶》",
                })

    # ── 兼格组合六：伤官格兼用财印 ───────────────────────────────────────────
    # 出处：《四十一、论伤官》
    # 条件：财印相克本不并用，但干头两清不相碍则可
    if primary_pattern == "伤官格":
        has_cai = any(g in ("正财","偏财") for g in gods)
        has_yin = any(g in ("正印","偏印") for g in gods)
        if has_cai and has_yin:
            cai_gans = [g for g in non_ri if get_ten_god(ri,g) in ("正财","偏财")]
            yin_gans = [g for g in non_ri if get_ten_god(ri,g) in ("正印","偏印")]
            xiang_ai = any(
                KE.get(GAN_WU_XING[c]) == GAN_WU_XING[y]
                for c in cai_gans for y in yin_gans
            )
            jian_ge_found.append({
                "兼格名":   "伤官格兼用财印",
                "成立":     not xiang_ai,
                "条件":     "干头两清不相碍，调停中和，遂为贵格"
                            if not xiang_ai
                            else "财印相克相碍，兼格不成，反损格局",
                "出处":     "《四十一、论伤官》",
            })

    # ── 兼格组合七：建禄逢官兼带财印 ────────────────────────────────────────
    # 出处：《四十五、论建禄月劫》
    # 条件：以官隔之，使财印两不相伤
    if primary_pattern in ("比肩格（建禄/月劫）", "劫财格（建禄/月劫）"):
        has_guan = "正官" in gods
        has_cai  = any(g in ("正财","偏财") for g in gods)
        has_yin  = any(g in ("正印","偏印") for g in gods)
        if has_guan and has_cai and has_yin:
            jian_ge_found.append({
                "兼格名":   "建禄逢官兼带财印",
                "成立":     True,
                "条件":     "以官隔之，使财印两不相伤，身强值三奇，其格便大",
                "用神":     "正官为主，财生官，印护官",
                "出处":     "《四十五、论建禄月劫》",
            })

    if not jian_ge_found:
        return {
            "兼格检测": "无兼格",
            "说明":     "天干未透出构成兼格的十神组合，以主格单用",
        }

    cheng_li = [j for j in jian_ge_found if j.get("成立")]
    return {
        "兼格检测":     "发现兼格组合",
        "兼格列表":     jian_ge_found,
        "成立兼格数":   len(cheng_li),
        "总则出处":     "《十六、论杂气如何取用》：杂气透干会支，一透则一用，兼透则兼用",
    }


# ==============================================================================
# D. 用神优先级
# 出处：《八、论用神》《十四、论用神配气候得失》《十、论用神变化》
# ==============================================================================

def assess_yong_shen_priority(
    chart: BaziChart,
    primary_pattern: str,
    pattern_status: str,
    tiaohou_result: dict,
) -> dict:
    """
    判断格局用神与调候用神的优先级关系，
    以及透干主事是否覆盖月令本气。

    核心原则：
    1. 月令为主（绝对基准）
       '八字用神，专求月令' ——《八、论用神》
    2. 透干主事可覆盖未透的月令本气
       '不透甲而透丙，则如知府不临郡，而同知得以作主'
       ——《十、论用神变化》
    3. 格局用神第一，调候用神互参
       '论命惟以月令用神为主，然亦须配气候而互参之'
       ——《十四、论用神配气候得失》
    4. 调候为急时可权变（特殊情况）
       '伤官见官……而金水见之，反为秀气……调候为急，权而用之'
       ——《十四、论用神配气候得失》
    """
    ri      = chart.ri_gan
    non_ri  = _non_ri_gans(chart)
    yue_zhi = chart.yue_zhi

    # 月令本气是否透干
    from evaluator import ZHI_CANG_GAN as ZCGC
    ben_qi = ZCGC.get(yue_zhi, [""])[0]
    ben_qi_tou = ben_qi in non_ri

    # 透干主事十神（非月令本气中透出的十神）
    tou_gan_gods = {}
    for g in non_ri:
        god = get_ten_god(ri, g)
        if god not in ("日主","未知") and g != ben_qi:
            tou_gan_gods[god] = g

    # 调候用神
    tiaohou_shou = tiaohou_result.get("首选用神", [])
    tiaohou_ci   = tiaohou_result.get("次选用神", [])
    tiaohou_all  = tiaohou_shou + tiaohou_ci

    # 格局用神（从主格名提取）
    ge_ju_yong = _extract_pattern_yong_shen(primary_pattern, pattern_status)

    # 是否存在冲突（格局用神在调候忌神中，或调候用神在格局忌神中）
    tiaohou_ji = tiaohou_result.get("忌神", [])
    conflict = any(y in tiaohou_ji for y in ge_ju_yong if isinstance(y, str))

    # 透干是否改变主事方向
    if tou_gan_gods and not ben_qi_tou:
        zhuan_guo = True
        zhuan_desc = (
            f"月令本气{ben_qi}未透干，"
            f"天干透出{'、'.join(f'{g}（{god}）' for god,g in tou_gan_gods.items())}主事。"
            f"出处：《十、论用神变化》'不透甲而透丙，则如同知得以作主'"
        )
    else:
        zhuan_guo = False
        zhuan_desc = f"月令本气{ben_qi}已透干，月令主事正常"

    return {
        "用神优先级": {
            "第一优先": "格局用神（月令定格）",
            "第二优先": "调候用神（气候互参）",
            "出处":     "《十四、论用神配气候得失》",
        },
        "格局用神": ge_ju_yong,
        "调候用神": {"首选": tiaohou_shou, "次选": tiaohou_ci},
        "透干主事变化": {
            "发生变化": zhuan_guo,
            "说明":     zhuan_desc,
        },
        "格局调候冲突": {
            "存在冲突": conflict,
            "说明": (
                "格局用神与调候忌神有重叠，需权变处理。"
                "出处：《十四、论用神配气候得失》'调候为急，权而用之'"
            ) if conflict else "格局用神与调候方向一致，无冲突",
        },
    }


def _extract_pattern_yong_shen(pattern_name: str, status: str) -> list:
    """从格局名称推断格局用神（简化映射）"""
    mapping = {
        "正官格": ["正官","财星","印绶"],
        "七杀格": ["食神","印绶"],
        "正印格": ["正印","七杀","正官"],
        "偏印格": ["偏印","七杀"],
        "食神格": ["食神","财星"],
        "伤官格": ["伤官","财星","印绶"],
        "正财格": ["正财","食神","正官"],
        "偏财格": ["偏财","食神","正官"],
    }
    for key, yong in mapping.items():
        if key in pattern_name:
            return yong
    return ["待定（需结合格局详情）"]


# ==============================================================================
# E. 格局高低评估
# 出处：《十二、论用神格局高低》《十一、论用神纯杂》
# ==============================================================================

def assess_ge_ju_level(
    chart: BaziChart,
    primary_pattern: str,
    pattern_status: str,
    strength_result: dict,
) -> dict:
    """
    格局高低评估。

    维度（出处：《十二、论用神格局高低》）：
    1. 用神是否透干有力（有根 + 得令 + 透干三者全）
    2. 格局是否纯粹（《十一、论用神纯杂》）
    3. 有情 vs 无情（用神与日主是否配合得宜）
    4. 身与格局是否相称

    原文说明：
    '八字既有用神，必有格局，有格局必有高低……
     然其理之大纲，亦在有情、有力无力之间而已'
    ——《十二、论用神格局高低》
    """
    ri     = chart.ri_gan
    non_ri = _non_ri_gans(chart)
    zhis   = _all_zhis(chart)
    cang   = _all_cang_gans(chart)
    gods   = [get_ten_god(ri, g) for g in non_ri]

    ge_ju_yong = _extract_pattern_yong_shen(primary_pattern, pattern_status)
    score = 0
    dimensions = []

    # ── 维度1：用神透干有力 ───────────────────────────────────────────────────
    # 有力 = 透干 + 有根（地支有用神五行的根）
    # 出处：'身强煞露而食神又旺……三者皆备，极等之贵，以其有力也'
    yong_tou  = []
    yong_you_gen = []
    for yong in ge_ju_yong:
        # 找对应天干
        tou_gans = [g for g in non_ri
                    if get_ten_god(ri, g) == yong or
                    (yong in ("财星",) and get_ten_god(ri,g) in ("正财","偏财")) or
                    (yong in ("印绶",) and get_ten_god(ri,g) in ("正印","偏印"))]
        if tou_gans:
            yong_tou.append(yong)
            # 检查根
            for tg in tou_gans:
                tg_wx = GAN_WU_XING.get(tg, "")
                if any(GAN_WU_XING.get(cg) == tg_wx for cg in cang):
                    yong_you_gen.append(yong)
                    break

    if yong_tou and yong_you_gen:
        score += 3
        dimensions.append({
            "维度": "用神透干有力",
            "评分": "+3",
            "依据": f"用神{'、'.join(yong_tou)}透干，且{'、'.join(yong_you_gen)}有地支根气",
            "出处": "《十二、论用神格局高低》",
        })
    elif yong_tou:
        score += 1
        dimensions.append({
            "维度": "用神透干但无根",
            "评分": "+1",
            "依据": f"用神{'、'.join(yong_tou)}透干，但无地支根气，力量偏弱",
            "出处": "《十二、论用神格局高低》",
        })
    else:
        score += 0
        dimensions.append({
            "维度": "用神未透干",
            "评分": "0",
            "依据": "用神未透干，格局力量不足",
            "出处": "《十二、论用神格局高低》",
        })

    # ── 维度2：格局纯粹度 ────────────────────────────────────────────────────
    # 纯：互用而两相得；杂：互用而两不相谋
    # 出处：《十一、论用神纯杂》
    # 简化判断：忌神是否透干
    ji_shen_map = {
        "正官格": ["伤官"],
        "七杀格": ["正财","偏财"],  # 财生煞为忌
        "正印格": ["正财","偏财"],
        "偏印格": ["正财","偏财","食神"],
        "食神格": ["偏印"],
        "伤官格": ["正官"],
        "正财格": ["比肩","劫财","七杀"],
        "偏财格": ["比肩","劫财","七杀"],
    }
    ji_list = []
    for key, ji in ji_shen_map.items():
        if key in primary_pattern:
            ji_list = ji
            break

    ji_tou = [g for g in gods if g in ji_list]
    if not ji_tou:
        score += 2
        dimensions.append({
            "维度": "格局纯粹",
            "评分": "+2",
            "依据": "忌神未透干，格局清纯",
            "出处": "《十一、论用神纯杂》：纯者吉，互用而两相得者是也",
        })
    else:
        score += 0
        dimensions.append({
            "维度": "格局混杂",
            "评分": "0",
            "依据": f"忌神{'、'.join(ji_tou)}已透干，格局不纯",
            "出处": "《十一、论用神纯杂》：杂者凶，互用而两不相谋者是也",
        })

    # ── 维度3：身与格局相称 ──────────────────────────────────────────────────
    # 出处：'煞强食旺而身无根……以其无力也，是皆格之低而无用者也'
    # 日主太弱而格局偏强（官杀格）= 不称；日主太强而格局偏弱 = 不称
    strength_tendency = strength_result.get("综合倾向", "")
    is_guan_sha = any(k in primary_pattern for k in ("正官","七杀"))
    is_yin_bj   = any(k in primary_pattern for k in ("印","比","劫","建禄"))

    if is_guan_sha and "偏弱" in strength_tendency:
        score += 0
        dimensions.append({
            "维度": "身弱格重（不称）",
            "评分": "0",
            "依据": "官杀格而日主偏弱，身不任格，格局偏低",
            "出处": "《十二、论用神格局高低》：煞强食旺而身无根……以其无力也",
        })
    elif is_yin_bj and "偏强" in strength_tendency:
        score += 1
        dimensions.append({
            "维度": "身旺格局有力",
            "评分": "+1",
            "依据": "印比格而日主偏强，身格相称",
            "出处": "《十二、论用神格局高低》",
        })
    else:
        score += 1
        dimensions.append({
            "维度": "身格基本相称",
            "评分": "+1",
            "依据": "日主强弱与格局基本相称",
            "出处": "《十二、论用神格局高低》",
        })

    # ── 格局成败加减分 ────────────────────────────────────────────────────────
    if pattern_status == "败":
        score -= 3
        dimensions.append({
            "维度": "格局已破（减分）",
            "评分": "-3",
            "依据": "格局败格，高低评估意义降低",
        })
    elif pattern_status == "救应":
        score -= 1
        dimensions.append({
            "维度": "有救应（小减）",
            "评分": "-1",
            "依据": "格局有破有救，较纯粹成格略低一等",
        })

    # ── 等级划分 ──────────────────────────────────────────────────────────────
    # 满分 6（维度1:3 + 维度2:2 + 维度3:1）
    if score >= 5:
        level = "高等"
        level_desc = "有情兼有力，用神透干有根，格局清纯，身格相称"
    elif score >= 3:
        level = "中等"
        level_desc = "条件部分满足，格局有成立基础但有不足"
    elif score >= 1:
        level = "次等"
        level_desc = "多项条件不足，格局偏低"
    else:
        level = "下等"
        level_desc = "用神无力或格局已破，格之低而无用"

    return {
        "格局等级":   level,
        "等级描述":   level_desc,
        "综合得分":   score,
        "满分":       6,
        "各维度评估": dimensions,
        "原典说明": (
            "格局高低变化甚微，'或一字而有千钧之力，或半字而败全局之美'，"
            "此评估为大略，不可机械套用。"
            "出处：《十二、论用神格局高低》"
        ),
    }


# ==============================================================================
# F. 透干力量轻重评估
# 出处：《三命通会》《渊海子平》，原文逐条标注
# ==============================================================================

# 透干位置权重
# 出处：《三命通会·卷二·论遁月时》
# '年為本月為苗日為花時為實，苗無根不生實無花不結'
# 《渊海子平·论月令》'月令有用神，得父母力；年有用神，得祖宗力；时有用神，得子孙力'
PILLAR_WEIGHT = {
    "年": 0.8,   # 祖宗之力，根基但距日主较远
    "月": 1.0,   # 提纲，力量最重，得父母力
    "日": 0.0,   # 日主本身，不计入透干力量
    "时": 0.9,   # 子孙之力，紧贴日主，力量次于月
}

def assess_tou_gan_strength(chart: BaziChart) -> dict:
    """
    评估四柱天干的透干力量轻重。

    综合四条原典规则：
    1. 同一十神多透：正官一位最好，多则成败；七杀一位聪明，多则先清后浊
       出处：《三命通会·卷十·看命口诀》
    2. 透干有根 vs 无根：地支无财官，天干虽透，行好运亦不济事
       出处：《三命通会·卷十·看命口诀》
    3. 月令得令加成：月令为命，取用凭于生月
       出处：《渊海子平·继善篇》
    4. 透干位置：月令用神得父母力，年上得祖宗力，时上得子孙力
       出处：《渊海子平·论月令》
    """
    ri      = chart.ri_gan
    ri_wx   = GAN_WU_XING[ri]
    non_ri  = _non_ri_gans(chart)
    cang    = _all_cang_gans(chart)
    zhis    = _all_zhis(chart)

    # 月令强度表（复用 narrator.py 里的逻辑）
    yue_ling_strength = {
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

    # 四柱位置名
    positions = [
        ("年", chart.nian_gan),
        ("月", chart.yue_gan),
        ("日", chart.ri_gan),
        ("时", chart.shi_gan),
    ]

    # 统计每个十神出现次数
    god_count: dict = {}
    for g in non_ri:
        god = get_ten_god(ri, g)
        if god not in ("日主", "未知"):
            god_count[god] = god_count.get(god, 0) + 1

    results = []
    for pos, gan in positions:
        if gan == ri:
            continue
        god   = get_ten_god(ri, gan)
        gan_wx = GAN_WU_XING[gan]
        if god in ("日主", "未知"):
            continue

        # ── 规则1：同一十神多透评级 ─────────────────────────────────────────
        # 出处：《三命通会·卷十·看命口诀》
        count = god_count.get(god, 1)
        if god == "正官":
            if count == 1:
                multi_note = "正官一位，君子贵人，纯粹最佳"
                multi_score = 1.0
            else:
                multi_note = f"正官{count}见，多则成败，力量反减"
                multi_score = 0.4
        elif god == "七杀":
            if count == 1:
                multi_note = "七杀一位，聪明伶俐"
                multi_score = 1.0
            else:
                multi_note = f"七杀{count}见，先清后浊，力量混杂"
                multi_score = 0.5
        elif god in ("正财", "偏财"):
            if count == 1:
                multi_note = "财一位，务要得时，富贵成家"
                multi_score = 1.0
            elif count == 2:
                multi_note = "财二位，性气减半"
                multi_score = 0.5
            else:
                multi_note = f"财{count}位，耗气身衰"
                multi_score = 0.2
        elif god in ("正印", "偏印"):
            multi_note = "印不论位数，格中不宜见财破印"
            multi_score = 1.0
        else:
            multi_note = ""
            multi_score = 1.0

        # ── 规则2：透干有根 vs 无根 ─────────────────────────────────────────
        # 出处：《三命通会·卷十》'地支無財官只是天干透出，雖行好運亦不濟事'
        # 出处：《三命通会·卷五》'天干透者易去，月支所藏者難去'
        root_zhis = [z for z in zhis
                     if any(GAN_WU_XING.get(cg) == gan_wx
                            for cg in ZHI_CANG_GAN.get(z, []))]
        has_root  = len(root_zhis) > 0
        root_count = len(root_zhis)

        if has_root:
            root_score = min(1.0, 0.6 + root_count * 0.2)
            root_note  = (f"地支{root_zhis}有根，根气稳固"
                         + ("（多根有力）" if root_count >= 2 else ""))
        else:
            root_score = 0.3
            root_note  = "地支无根，天干虽透，行运亦不济事"

        # ── 规则3：月令得令加成 ──────────────────────────────────────────────
        # 出处：《渊海子平·继善篇》'欲知贵贱，先观月令乃提纲'
        ling_score_val = yue_ling_strength.get(gan_wx, {}).get(chart.yue_zhi, 0)
        if ling_score_val >= 3:
            ling_mult  = 1.3
            ling_note  = f"得令（月令对{gan_wx}强度{ling_score_val}），力量加成"
        elif ling_score_val >= 1:
            ling_mult  = 1.0
            ling_note  = f"月令中性（强度{ling_score_val}）"
        else:
            ling_mult  = 0.7
            ling_note  = f"失令（月令对{gan_wx}强度{ling_score_val}），力量折减"

        # ── 规则4：透干位置权重 ──────────────────────────────────────────────
        # 出处：《渊海子平·论月令》
        pos_weight = PILLAR_WEIGHT.get(pos, 1.0)
        pos_note = {
            "年": "年干主祖宗根基，距日主较远",
            "月": "月干紧贴月令，力量最重，得父母力",
            "时": "时干紧贴日主，得子孙力",
        }.get(pos, "")

        # ── 综合力量评分（0–10）────────────────────────────────────────────
        raw_score = multi_score * root_score * ling_mult * pos_weight * 10
        final_score = round(min(10.0, raw_score), 1)

        if final_score >= 7:
            level = "强"
        elif final_score >= 4:
            level = "中"
        else:
            level = "弱"

        results.append({
            "位置":     pos + "干",
            "天干":     gan,
            "十神":     god,
            "力量等级": level,
            "综合得分": final_score,
            "规则明细": {
                "多透评级": {"评语": multi_note, "系数": multi_score},
                "有根情况": {"评语": root_note,  "系数": round(root_score, 2)},
                "月令影响": {"评语": ling_note,  "系数": ling_mult},
                "位置权重": {"评语": pos_note,   "系数": pos_weight},
            },
        })

    # 同一十神多透的汇总警示
    warnings = []
    for god, cnt in god_count.items():
        if god == "正官" and cnt > 1:
            warnings.append({
                "十神": "正官",
                "出现次数": cnt,
                "警示": "正官多见，多则反主成败",
                "出处": "《三命通会·卷十·看命口诀》",
            })
        if god == "七杀" and cnt > 1:
            warnings.append({
                "十神": "七杀",
                "出现次数": cnt,
                "警示": "七杀多见，先清后浊",
                "出处": "《三命通会·卷十·看命口诀》",
            })
        if god in ("正财", "偏财") and cnt >= 3:
            warnings.append({
                "十神": "财星",
                "出现次数": cnt,
                "警示": "财三位四位，耗气身衰",
                "出处": "《三命通会·卷十·看命口诀》",
            })

    return {
        "各干力量详情": results,
        "多透警示":     warnings,
        "规则说明": [
            "透干力量 = 多透系数 × 有根系数 × 月令系数 × 位置权重",
            "出处：《三命通会·卷十·看命口诀》《渊海子平·继善篇》《渊海子平·论月令》",
            "天干透者易去，月支所藏者难去——《三命通会·卷五》",
            "地支无财官只是天干透出，虽行好运亦不济事——《三命通会·卷十》",
        ],
    }


# ==============================================================================
# G. 合冲动态判断
# 出处：《渊海子平》，原文逐条标注
# ==============================================================================

# 地支相冲对（用于动态判断）
CHONG_PAIRS = [
    ("子", "午"), ("丑", "未"), ("寅", "申"),
    ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
]

# 地支六合（用于判断合能否解冲）
LIU_HE_PAIRS = [
    ("子", "丑"), ("寅", "亥"), ("卯", "戌"),
    ("辰", "酉"), ("巳", "申"), ("午", "未"),
]

# 地支三合局（局全才能解冲）
SAN_HE_GROUPS = [
    ({"申", "子", "辰"}, "水"),
    ({"寅", "午", "戌"}, "火"),
    ({"巳", "酉", "丑"}, "金"),
    ({"亥", "卯", "未"}, "木"),
]

# 四柱位置距离（用于判断冲力轻重）
# 出处：《渊海子平·幽微赋》
# '年月冲者，难为祖业；日时冲者，妻子招迟'
POSITION_PAIRS = {
    (0, 1): ("年", "月"),  # 年月相邻，冲力最重
    (1, 2): ("月", "日"),  # 月日相邻
    (2, 3): ("日", "时"),  # 日时相邻
    (0, 2): ("年", "日"),  # 年日相隔
    (1, 3): ("月", "时"),  # 月时相隔
    (0, 3): ("年", "时"),  # 年时最远，冲力最轻
}


def assess_chong_he_dynamic(chart: BaziChart) -> dict:
    """
    合冲动态判断：在事实扫描基础上，判断合能否解冲、冲力轻重。

    核心规则（全部原文有据）：

    规则1：年月冲 vs 日时冲，影响范围不同
      '年月冲者，难为祖业；日时冲者，妻子招迟'
      出处：《渊海子平·幽微赋》

    规则2：合能解冲的条件
      '柱内申辰来合局，即成江海发涛声'（三合局能解冲）
      出处：《渊海子平·论子》

    规则3：合不能完全解冲的情况
      '近无亥卯形难变，远带刑冲库亦开'（距离远的合力量弱）
      出处：《渊海子平·论未》

    规则4：阳刃逢冲合均不宜
      '不可一合一冲也'
      出处：《渊海子平·论阳刃》

    规则5：辰戌丑未逢冲反而可发
      '辰戌丑未遇刑冲，无人不发'
      出处：《渊海子平·碧渊赋》
    """
    zhis = _all_zhis(chart)  # [年支, 月支, 日支, 时支]
    zhi_set = set(zhis)

    chong_analysis  = []
    he_jie_analysis = []

    # ── 扫描所有相冲 ─────────────────────────────────────────────────────────
    for i in range(4):
        for j in range(i + 1, 4):
            z1, z2 = zhis[i], zhis[j]
            if (z1, z2) in CHONG_PAIRS or (z2, z1) in CHONG_PAIRS:
                pos_pair = POSITION_PAIRS.get((i, j), ("?", "?"))
                pos_names = ["年", "月", "日", "时"]

                # 冲力轻重判断
                # 出处：《渊海子平·幽微赋》
                if (i, j) in [(0, 1), (1, 2), (2, 3)]:  # 相邻柱
                    chong_weight = "重"
                    chong_note   = "相邻两柱相冲，冲力较重"
                elif (i, j) == (0, 3):                   # 年时最远
                    chong_weight = "轻"
                    chong_note   = "年时相隔最远，冲力最轻"
                else:
                    chong_weight = "中"
                    chong_note   = "隔柱相冲，冲力居中"

                # 特殊规则：辰戌丑未逢冲反发
                # 出处：《渊海子平·碧渊赋》
                ku_zhis = {"辰", "戌", "丑", "未"}
                if z1 in ku_zhis and z2 in ku_zhis:
                    special_note = (
                        "辰戌丑未遇刑冲，无人不发"
                        "（出处：《渊海子平·碧渊赋》）"
                    )
                else:
                    special_note = ""

                # 影响范围判断
                # 出处：《渊海子平·幽微赋》
                if i == 0 and j == 1:
                    scope = "年月冲，难为祖业（出处：《渊海子平·幽微赋》）"
                elif i == 2 and j == 3:
                    scope = "日时冲，妻子招迟（出处：《渊海子平·幽微赋》）"
                else:
                    scope = f"{pos_names[i]}与{pos_names[j]}相冲"

                chong_rec = {
                    "冲":       f"{z1}{z2}相冲",
                    "位置":     f"{pos_names[i]}支冲{pos_names[j]}支",
                    "冲力":     chong_weight,
                    "冲力说明": chong_note,
                    "影响范围": scope,
                    "特殊规则": special_note,
                }

                # ── 检测是否有合能解冲 ───────────────────────────────────────
                # 规则：三合局能解冲（局全）
                # 出处：《渊海子平·论子》'柱内申辰来合局，即成江海发涛声'
                he_jie_found = False

                # 检查 z1 或 z2 是否加入了三合局
                for san_he_set, san_he_wx in SAN_HE_GROUPS:
                    if z1 in san_he_set or z2 in san_he_set:
                        remaining = san_he_set - {z1, z2}
                        if remaining <= zhi_set:
                            # 三合局完整，可以解冲
                            he_jie_found = True
                            chong_rec["合解冲"] = {
                                "能解": True,
                                "解法": f"{''.join(san_he_set)}三合{san_he_wx}局完整，合局解冲",
                                "出处": "《渊海子平·论子》：柱内申辰来合局，即成江海发涛声",
                            }
                            break

                # 检查六合
                if not he_jie_found:
                    for za, zb in LIU_HE_PAIRS:
                        for chong_z in (z1, z2):
                            he_partner = zb if chong_z == za else (za if chong_z == zb else None)
                            if he_partner and he_partner in zhi_set:
                                # 六合存在，但能否解冲需看距离
                                # 出处：《渊海子平·论未》'近无亥卯形难变，远带刑冲库亦开'
                                # 简化：六合与冲在同一柱（相邻）才有效
                                he_idx  = zhis.index(he_partner)
                                chong_idx = zhis.index(chong_z)
                                if abs(he_idx - chong_idx) <= 1:
                                    chong_rec["合解冲"] = {
                                        "能解": True,
                                        "解法": f"{chong_z}{he_partner}六合，相邻解冲",
                                        "出处": "《渊海子平·论未》：近无亥卯形难变",
                                        "注意": "六合解冲力量弱于三合局，仅部分缓解",
                                    }
                                    he_jie_found = True
                                else:
                                    chong_rec["合解冲"] = {
                                        "能解": False,
                                        "说明": f"{chong_z}{he_partner}六合存在，但距离较远，解冲力量不足",
                                        "出处": "《渊海子平·论未》：远带刑冲库亦开",
                                    }
                                break

                if not he_jie_found and "合解冲" not in chong_rec:
                    chong_rec["合解冲"] = {
                        "能解": False,
                        "说明": "局中无合可解此冲，冲力不减",
                    }

                chong_analysis.append(chong_rec)

    # ── 扫描六合是否被冲破 ───────────────────────────────────────────────────
    # 出处：《渊海子平·杂论口诀》'冲天无合，乃飘流之徒'（反推：有合被冲则合力减弱）
    for za, zb in LIU_HE_PAIRS:
        if za in zhi_set and zb in zhi_set:
            # 检查 za 或 zb 是否同时被冲
            za_chong = any(
                (za, z) in CHONG_PAIRS or (z, za) in CHONG_PAIRS
                for z in zhi_set if z != zb
            )
            zb_chong = any(
                (zb, z) in CHONG_PAIRS or (z, zb) in CHONG_PAIRS
                for z in zhi_set if z != za
            )
            if za_chong or zb_chong:
                chong_z = za if za_chong else zb
                he_jie_analysis.append({
                    "六合":   f"{za}{zb}",
                    "状态":   "合被冲破",
                    "说明":   f"{chong_z}被冲，六合{za}{zb}力量减弱",
                    "出处":   "《渊海子平·论阳刃》：岁运相冲并相合，勃然灾祸又临门",
                })

    # ── 汇总 ─────────────────────────────────────────────────────────────────
    if not chong_analysis and not he_jie_analysis:
        return {
            "合冲动态": "原局无相冲",
            "说明":     "四柱地支无相冲，此模块不适用",
        }

    return {
        "相冲分析":   chong_analysis,
        "合被冲情况": he_jie_analysis if he_jie_analysis else ["无六合被冲破的情况"],
        "规则说明": [
            "年月冲者，难为祖业；日时冲者，妻子招迟——《渊海子平·幽微赋》",
            "辰戌丑未遇刑冲，无人不发——《渊海子平·碧渊赋》",
            "柱内申辰来合局，即成江海发涛声——《渊海子平·论子》（三合解冲）",
            "近无亥卯形难变，远带刑冲库亦开——《渊海子平·论未》（距离影响合力）",
            "冲天无合，乃飘流之徒——《渊海子平·杂论口诀》",
        ],
    }


# ==============================================================================
# H. 十神清浊判断
# 出处：《子平真诠·十一、论用神纯杂》《滴天髓·二十三、清气》
#       《滴天髓·五、何知章》《三命通会·卷十·看命口诀》
#
# 清浊→人生维度对应（仅《滴天髓·五、何知章》有，其他书无此内容）：
#   财神清 + 身旺 → 妻美
#   财神浊 + 身旺 → 家富
#   官星清 + 身旺 → 必贵
#   官星浊 + 身旺 → 多子
# ==============================================================================

# 十神之间的生克关系（用于判断并透两神是否"两相得"）
# 出处：《子平真诠·十一、论用神纯杂》
# '互用而两相得者'为纯（清），'互用而两不相谋者'为杂（浊）
def _two_gods_compatible(god1: str, god2: str) -> bool:
    """
    判断两个并透十神是否'两相得'（相生或相克得当）。
    出处：《子平真诠·十一、论用神纯杂》
    相生 = 两相得；相克且克制得宜（如煞逢食制）= 亦两相得
    相克且不得当（如官逢伤、印逢财）= 两不相谋
    """
    # 相生组合（两相得）
    SHENG_PAIRS = {
        ("食神",   "正财"), ("食神",   "偏财"),
        ("伤官",   "正财"), ("伤官",   "偏财"),
        ("正财",   "正官"), ("正财",   "七杀"),
        ("偏财",   "正官"), ("偏财",   "七杀"),
        ("正官",   "正印"), ("正官",   "偏印"),
        ("七杀",   "正印"), ("七杀",   "偏印"),
        ("正印",   "比肩"), ("正印",   "劫财"),
        ("偏印",   "比肩"), ("偏印",   "劫财"),
    }
    # 相克得当（煞逢食制 = 两相得）
    KE_DANG_PAIRS = {
        ("七杀",  "食神"),
        ("七杀",  "伤官"),
    }
    pair = (god1, god2)
    pair_r = (god2, god1)
    return (pair in SHENG_PAIRS or pair_r in SHENG_PAIRS or
            pair in KE_DANG_PAIRS or pair_r in KE_DANG_PAIRS)


# 各格局对应的忌神
# 出处：《子平真诠》各格论
JI_SHEN_MAP = {
    "正官格": ["伤官"],
    "七杀格": ["正财", "偏财"],
    "正印格": ["正财", "偏财"],
    "偏印格": ["正财", "偏财", "食神"],
    "食神格": ["偏印"],
    "伤官格": ["正官"],
    "正财格": ["比肩", "劫财", "七杀"],
    "偏财格": ["比肩", "劫财", "七杀"],
}


def assess_qing_zhuo(chart: BaziChart,
                     primary_pattern: str,
                     strength_result: dict) -> dict:
    """
    十神清浊判断。

    清的条件（出处：《子平真诠·十一》《滴天髓·二十三》）：
      1. 透干唯一（一位最清，多则浊）
      2. 并透两神两相得（相生或克制得当）
      3. 忌神未透干（无混杂）

    浊的条件：
      1. 同一十神多透（三命通会：七杀三位先清后浊）
      2. 并透两神两不相谋（相克不当）
      3. 忌神透干混杂

    清浊→人生维度（出处：《滴天髓·五、何知章》）：
      财神清 + 身旺 → 妻美
      财神浊 + 身旺 → 家富
      官星清 + 身旺 → 必贵
      官星浊 + 身旺 → 多子
    """
    ri     = chart.ri_gan
    non_ri = _non_ri_gans(chart)
    gods   = [(get_ten_god(ri, g), g) for g in non_ri]

    # 日主强弱
    strength = strength_result.get("综合倾向", "")
    shen_wang = "偏强" in strength or "中和偏强" in strength

    # ── Step1：统计各十神透干次数 ────────────────────────────────────────────
    god_count: dict = {}
    god_gans:  dict = {}
    for god, g in gods:
        if god not in ("日主", "未知"):
            god_count[god] = god_count.get(god, 0) + 1
            god_gans.setdefault(god, []).append(g)

    # ── Step2：忌神是否透干 ───────────────────────────────────────────────────
    ji_list = []
    for key, ji in JI_SHEN_MAP.items():
        if key in primary_pattern:
            ji_list = ji
            break
    ji_tou = [god for god, _ in gods if god in ji_list]

    # ── Step3：并透两神是否两相得 ────────────────────────────────────────────
    tou_gods = list(god_count.keys())
    compatible_pairs   = []
    incompatible_pairs = []
    for i in range(len(tou_gods)):
        for j in range(i + 1, len(tou_gods)):
            g1, g2 = tou_gods[i], tou_gods[j]
            if _two_gods_compatible(g1, g2):
                compatible_pairs.append((g1, g2))
            else:
                incompatible_pairs.append((g1, g2))

    # ── Step4：对财星和官星单独做清浊判断 ────────────────────────────────────
    # 出处：《滴天髓·五、何知章》
    cai_gods  = [g for g, _ in gods if g in ("正财", "偏财")]
    guan_gods = [g for g, _ in gods if g in ("正官", "七杀")]

    def _judge_qingzhuo(ten_god_name: str, count: int,
                        has_ji: bool, has_incompatible: bool) -> str:
        """综合三个维度判断单个十神的清浊"""
        zhuo_signals = sum([
            count > 1,          # 多透
            has_ji,             # 忌神混杂
            has_incompatible,   # 并透不相谋
        ])
        if zhuo_signals == 0:
            return "清"
        elif zhuo_signals == 1:
            return "偏清"
        elif zhuo_signals == 2:
            return "偏浊"
        else:
            return "浊"

    results = {}

    # 财星清浊
    if cai_gods:
        cai_count = sum(god_count.get(g, 0) for g in ("正财", "偏财"))
        cai_has_ji = any(g in ji_list for g in ("正财", "偏财")) or \
                     any(g in ji_tou for g in ("比肩", "劫财", "七杀"))
        cai_incompatible = any(
            g in ("正财", "偏财") or h in ("正财", "偏财")
            for g, h in incompatible_pairs
        )
        cai_qz = _judge_qingzhuo("财星", cai_count, cai_has_ji, cai_incompatible)

        # 清浊→人生维度（出处：《滴天髓·五、何知章》）
        if shen_wang:
            if cai_qz in ("清", "偏清"):
                cai_implication = "财神清而身旺，妻美"
            else:
                cai_implication = "财神浊而身旺，家富"
        else:
            cai_implication = "身弱，财星清浊对妻财的影响需结合日主承载能力判断"

        results["财星"] = {
            "清浊":   cai_qz,
            "透干":   cai_gods,
            "人生影响": cai_implication,
            "出处":   "《滴天髓·五、何知章》：财神清而身旺者妻美，财神浊而身旺者家富",
        }

    # 官星清浊
    if guan_gods:
        guan_count = sum(god_count.get(g, 0) for g in ("正官", "七杀"))
        guan_has_ji = any(
            g in ji_tou for g in ("伤官",)
        )
        guan_incompatible = any(
            g in ("正官", "七杀") or h in ("正官", "七杀")
            for g, h in incompatible_pairs
        )
        # 官杀混杂本身也是浊（出处：《三命通会·卷十》正官多则成败）
        guan_hun_za = "正官" in god_count and "七杀" in god_count
        if guan_hun_za:
            guan_has_ji = True

        guan_qz = _judge_qingzhuo("官星", guan_count, guan_has_ji, guan_incompatible)

        if shen_wang:
            if guan_qz in ("清", "偏清"):
                guan_implication = "官星清而身旺，必贵"
            else:
                guan_implication = "官星浊而身旺，多子"
        else:
            guan_implication = "身弱，官星清浊影响需结合日主承载能力判断"

        results["官星"] = {
            "清浊":   guan_qz,
            "透干":   guan_gods,
            "人生影响": guan_implication,
            "出处":   "《滴天髓·五、何知章》：官星清而身旺者必贵，官星浊而身旺者必多子",
        }

    # ── 格局整体清浊 ──────────────────────────────────────────────────────────
    # 出处：《子平真诠·十一》《滴天髓·二十三》
    if not ji_tou and not incompatible_pairs:
        ge_ju_qz = "清"
        ge_ju_desc = "忌神未透，并透诸神两相得，格局清纯"
        ge_ju_src  = "《子平真诠·十一》：互用而两相得者是也"
    elif ji_tou and incompatible_pairs:
        ge_ju_qz = "浊"
        ge_ju_desc = f"忌神{ji_tou}已透，并透诸神存在两不相谋，格局混浊"
        ge_ju_src  = "《子平真诠·十一》：互用而两不相谋者是也"
    elif ji_tou:
        ge_ju_qz = "偏浊"
        ge_ju_desc = f"忌神{ji_tou}已透，格局偏浊"
        ge_ju_src  = "《滴天髓·二十三》：以食神杂之不能伤我之官，反与官星不和，俱为浊"
    else:
        ge_ju_qz = "偏清"
        ge_ju_desc = "忌神未透，但并透诸神存在两不相谋，格局偏清"
        ge_ju_src  = "《子平真诠·十一》：论用神纯杂"

    return {
        "格局整体清浊": {
            "结论":   ge_ju_qz,
            "说明":   ge_ju_desc,
            "出处":   ge_ju_src,
        },
        "忌神透干情况": {
            "忌神列表": ji_list,
            "已透干":   ji_tou if ji_tou else ["无"],
            "出处":     "《子平真诠·十一》《滴天髓·二十三》",
        },
        "并透相生相克": {
            "两相得": [f"{a}与{b}" for a, b in compatible_pairs] or ["无"],
            "两不相谋": [f"{a}与{b}" for a, b in incompatible_pairs] or ["无"],
            "出处":   "《子平真诠·十一、论用神纯杂》",
        },
        "各十神清浊详情": results,
        "重要说明": (
            "'有安顿，循序得所'（《滴天髓·二十三》）属定性描述，"
            "无法量化，此条留待人工或AI判断。"
            "本模块仅处理可量化的清浊条件。"
        ),
    }


# ==============================================================================
# I. 六亲对应与体系验证
#
# 两个体系存在分歧，脚本同时输出两套结论，通过现实验证确定采用哪个体系。
#
# 体系A：《渊海子平·六亲总篇》
#   正印=母，偏财=父，正财=妻，偏财=妾/父
#   七杀=儿子，正官=女儿，食神=孙子，伤官=孙女/祖母
#   比肩=兄弟姐妹
#
# 体系B：《滴天髓·六亲论》
#   财星（正偏）=父/妻，印星（正偏）=母
#   官星（正官七杀）=子女（男命），不细分男女
#   '子平之法，以财为父，以印为母，以断其吉凶，十有九验'
#
# 分歧点：男命子女
#   体系A：七杀=儿子，正官=女儿（细分）
#   体系B：官星统论子女，不分男女
# ==============================================================================

# 体系A：《渊海子平·六亲总篇》
LIUQIN_SYSTEM_A = {
    "正印":  {"六亲": "母亲",   "说明": "正印为正母"},
    "偏印":  {"六亲": "祖父/偏母", "说明": "偏印为偏母及祖父"},
    "偏财":  {"六亲": "父亲/偏妻", "说明": "偏财为父，亦为偏妻"},
    "正财":  {"六亲": "妻子",   "说明": "正财为妻"},
    "比肩":  {"六亲": "兄弟姐妹", "说明": "比肩为兄弟姐妹"},
    "劫财":  {"六亲": "兄弟姐妹", "说明": "劫财为兄弟姐妹"},
    "七杀":  {"六亲": "儿子",   "说明": "七杀为男（儿子）"},
    "正官":  {"六亲": "女儿",   "说明": "正官为女（女儿）"},
    "食神":  {"六亲": "孙子",   "说明": "食神为男孙"},
    "伤官":  {"六亲": "孙女/祖母", "说明": "伤官为女孙及祖母"},
}

# 体系B：《滴天髓·六亲论》
LIUQIN_SYSTEM_B = {
    "正印":  {"六亲": "母亲", "说明": "以印为母"},
    "偏印":  {"六亲": "母亲（偏）", "说明": "以印为母"},
    "正财":  {"六亲": "父亲/妻子", "说明": "以财为父，以财看妻"},
    "偏财":  {"六亲": "父亲/妻子", "说明": "以财为父，以财看妻"},
    "正官":  {"六亲": "子女", "说明": "以官星看子（男命）"},
    "七杀":  {"六亲": "子女", "说明": "以官星看子（男命）"},
    "比肩":  {"六亲": "兄弟姐妹", "说明": "比肩同类"},
    "劫财":  {"六亲": "兄弟姐妹", "说明": "劫财同类"},
}


def build_liuqin_map(chart: BaziChart) -> dict:
    """
    同时输出两个体系的六亲对应，供验证使用。
    不预设哪个体系正确，两套都输出。
    """
    ri     = chart.ri_gan
    non_ri = _non_ri_gans(chart)
    cang   = _all_cang_gans(chart)

    # 透干十神
    tou_gods = {}
    for g in non_ri:
        god = get_ten_god(ri, g)
        if god not in ("日主", "未知"):
            tou_gods.setdefault(god, []).append(g)

    # 地支藏干十神
    cang_gods = {}
    for cg in cang:
        god = get_ten_god(ri, cg)
        if god not in ("日主", "未知"):
            cang_gods.setdefault(god, []).append(cg)

    def _build_system(system: dict, label: str) -> dict:
        result = {}
        for god, info in system.items():
            tou  = tou_gods.get(god, [])
            cang = cang_gods.get(god, [])
            if tou or cang:
                result[info["六亲"]] = {
                    "对应十神": god,
                    "天干透出": tou if tou else ["未透"],
                    "地支藏干": cang if cang else ["未藏"],
                    "说明":     info["说明"],
                }
        return result

    system_a = _build_system(LIUQIN_SYSTEM_A, "A")
    system_b = _build_system(LIUQIN_SYSTEM_B, "B")

    return {
        "体系A（渊海子平）": {
            "六亲分布": system_a,
            "出处": "《渊海子平·六亲总篇》",
        },
        "体系B（滴天髓）": {
            "六亲分布": system_b,
            "出处": "《滴天髓·六亲论》：子平之法，以财为父，以印为母，十有九验",
        },
        "主要分歧": "男命子女：体系A细分七杀=儿子/正官=女儿；体系B以官星统论不分男女",
        "验证说明": "请通过verify_liuqin()函数输入实际六亲情况，系统自动统计两体系命中率",
    }


def verify_liuqin(
    chart: BaziChart,
    actual: dict,
    history: list = None,
) -> dict:
    """
    六亲体系验证函数。

    actual 参数格式：
    {
        "有儿子": True/False,
        "有女儿": True/False,
        "父亲在世": True/False,
        "母亲在世": True/False,
        "已婚": True/False,
        "兄弟姐妹数": 0/1/2...
    }

    history：历史验证记录列表，用于累计统计命中率
    传入格式：[{"命盘": "xxx", "体系A命中": 3, "体系B命中": 4, "总项": 5}, ...]
    """
    ri     = chart.ri_gan
    non_ri = _non_ri_gans(chart)
    cang   = _all_cang_gans(chart)

    def _has_god(god: str) -> bool:
        """该十神是否存在（透干或藏干）"""
        for g in non_ri:
            if get_ten_god(ri, g) == god:
                return True
        for cg in cang:
            if get_ten_god(ri, cg) == god:
                return True
        return False

    hit_a = 0
    hit_b = 0
    total = 0
    details = []

    # ── 验证子女 ──────────────────────────────────────────────────────────────
    if "有儿子" in actual:
        total += 1
        has_sha = _has_god("七杀")
        has_guan = _has_god("正官")
        has_guan_sha = has_sha or has_guan

        # 体系A：七杀=儿子
        pred_a = has_sha
        # 体系B：官星（含七杀）=子女
        pred_b = has_guan_sha

        match_a = (pred_a == actual["有儿子"])
        match_b = (pred_b == actual["有儿子"])
        if match_a: hit_a += 1
        if match_b: hit_b += 1

        details.append({
            "验证项":  "有儿子",
            "实际":    actual["有儿子"],
            "体系A预测": f"{'有' if pred_a else '无'}（七杀{'存在' if has_sha else '不存在'}）",
            "体系B预测": f"{'有' if pred_b else '无'}（官星{'存在' if has_guan_sha else '不存在'}）",
            "体系A命中": match_a,
            "体系B命中": match_b,
        })

    if "有女儿" in actual:
        total += 1
        has_guan = _has_god("正官")
        has_guan_sha = _has_god("正官") or _has_god("七杀")

        pred_a = has_guan
        pred_b = has_guan_sha

        match_a = (pred_a == actual["有女儿"])
        match_b = (pred_b == actual["有女儿"])
        if match_a: hit_a += 1
        if match_b: hit_b += 1

        details.append({
            "验证项":  "有女儿",
            "实际":    actual["有女儿"],
            "体系A预测": f"{'有' if pred_a else '无'}（正官{'存在' if has_guan else '不存在'}）",
            "体系B预测": f"{'有' if pred_b else '无'}（官星{'存在' if has_guan_sha else '不存在'}）",
            "体系A命中": match_a,
            "体系B命中": match_b,
        })

    # ── 验证父母 ──────────────────────────────────────────────────────────────
    if "父亲在世" in actual:
        total += 1
        # 两体系一致：偏财=父
        has_pian_cai = _has_god("偏财")
        pred = has_pian_cai
        match = (pred == actual["父亲在世"])
        if match: hit_a += 1
        if match: hit_b += 1
        details.append({
            "验证项":  "父亲在世",
            "实际":    actual["父亲在世"],
            "体系A预测": f"{'有' if pred else '无'}",
            "体系B预测": f"{'有' if pred else '无'}（两体系一致）",
            "体系A命中": match,
            "体系B命中": match,
        })

    if "母亲在世" in actual:
        total += 1
        # 两体系一致：正印=母
        has_yin = _has_god("正印")
        pred = has_yin
        match = (pred == actual["母亲在世"])
        if match: hit_a += 1
        if match: hit_b += 1
        details.append({
            "验证项":  "母亲在世",
            "实际":    actual["母亲在世"],
            "体系A预测": f"{'有' if pred else '无'}",
            "体系B预测": f"{'有' if pred else '无'}（两体系一致）",
            "体系A命中": match,
            "体系B命中": match,
        })

    # ── 验证婚姻 ──────────────────────────────────────────────────────────────
    if "已婚" in actual:
        total += 1
        # 两体系一致：正财=妻
        has_zheng_cai = _has_god("正财")
        pred = has_zheng_cai
        match = (pred == actual["已婚"])
        if match: hit_a += 1
        if match: hit_b += 1
        details.append({
            "验证项":  "已婚（有正财）",
            "实际":    actual["已婚"],
            "体系A预测": f"{'有' if pred else '无'}",
            "体系B预测": f"{'有' if pred else '无'}（两体系一致）",
            "体系A命中": match,
            "体系B命中": match,
        })

    # ── 累计历史命中率 ────────────────────────────────────────────────────────
    if history:
        total_hist_a = hit_a + sum(h.get("体系A命中数", 0) for h in history)
        total_hist_b = hit_b + sum(h.get("体系B命中数", 0) for h in history)
        total_hist   = total + sum(h.get("总验证项", 0) for h in history)
        acc_a = round(total_hist_a / total_hist, 2) if total_hist else 0
        acc_b = round(total_hist_b / total_hist, 2) if total_hist else 0
    else:
        acc_a = round(hit_a / total, 2) if total else 0
        acc_b = round(hit_b / total, 2) if total else 0

    # ── 当前命中率结论 ────────────────────────────────────────────────────────
    if total == 0:
        conclusion = "未提供验证数据"
        recommended = "待定"
    elif acc_a > acc_b:
        conclusion = f"体系A命中率（{acc_a}）高于体系B（{acc_b}）"
        recommended = "体系A（渊海子平）"
    elif acc_b > acc_a:
        conclusion = f"体系B命中率（{acc_b}）高于体系A（{acc_a}）"
        recommended = "体系B（滴天髓）"
    else:
        conclusion = f"两体系命中率相同（{acc_a}），暂无法区分"
        recommended = "待更多样本验证"

    return {
        "本次验证": {
            "验证详情":   details,
            "体系A命中":  f"{hit_a}/{total}",
            "体系B命中":  f"{hit_b}/{total}",
        },
        "累计命中率": {
            "体系A": acc_a,
            "体系B": acc_b,
            "样本数": total if not history else total + sum(h.get("总验证项", 0) for h in history),
        },
        "当前结论":   conclusion,
        "推荐体系":   recommended,
        "说明": "建议累计5个以上命盘验证后再确定体系，单一命盘结果不足以定论",
    }


# ==============================================================================
# J. 六亲质量评估
#
# 判断逻辑来自两条核心规则：
#
# 规则一：喜神与六亲十神是否一致
#   出处：《滴天髓·六亲论》
#   '喜神即是财神，其妻美而且富贵'
#   '喜神即是官星，其子贤俊'
#   '喜神与财神不相妒忌亦好，否则克妻'
#
# 规则二：六亲十神的旺衰得地
#   出处：《三命通会·卷七·论六亲》
#   '父母星坐长生旺库禄马贵人之地则主父母富贵福寿'
#   '坐空刑克煞死亡衰败则主父母贫薄破伤刑夭'
#
# 规则三：日支宫位判断妻缘
#   出处：《子平真诠·二十四、论妻子》
#   '妻宫坐财，吉也；妻坐官，吉也'
#   '坐下财官，妻当贤贵'
# ==============================================================================

# 月令旺相休囚死（复用）
_YLS = {
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

# 六亲十神对应表（两体系合并，各自标注）
# 用于质量评估时找到对应十神
LIUQIN_GODS = {
    "妻":   {"A": ["正财"],          "B": ["正财", "偏财"]},
    "父":   {"A": ["偏财"],          "B": ["偏财", "正财"]},
    "母":   {"A": ["正印"],          "B": ["正印", "偏印"]},
    "子":   {"A": ["七杀"],          "B": ["正官", "七杀"]},
    "女":   {"A": ["正官"],          "B": ["正官", "七杀"]},
    "兄弟": {"A": ["比肩", "劫财"],  "B": ["比肩", "劫财"]},
}


def _get_liuqin_god_strength(chart: BaziChart, gods: list) -> dict:
    """
    计算六亲对应十神的力量（旺衰得地）。
    出处：《三命通会·卷七》'须看四柱之中父母兄弟妻子星居何地，论旺相休囚'
    """
    ri    = chart.ri_gan
    non_ri = _non_ri_gans(chart)
    cang  = _all_cang_gans(chart)
    yue_zhi = chart.yue_zhi

    tou_gans = [g for g in non_ri if get_ten_god(ri, g) in gods]
    cang_gans = [cg for cg in cang if get_ten_god(ri, cg) in gods]

    if not tou_gans and not cang_gans:
        return {"存在": False, "透干": [], "藏干": [], "月令强度": 0}

    # 取透干的月令强度（透干为主）
    strength_vals = []
    for g in tou_gans:
        wx = GAN_WU_XING.get(g, "")
        s = _YLS.get(wx, {}).get(yue_zhi, 0)
        strength_vals.append(s)

    avg_strength = sum(strength_vals) / len(strength_vals) if strength_vals else 0

    return {
        "存在":    True,
        "透干":    tou_gans,
        "藏干":    cang_gans,
        "月令强度": avg_strength,
        "得令":    avg_strength >= 3 if strength_vals else False,
    }


def _is_xi_shen(chart: BaziChart, god: str,
                pattern_name: str, pattern_status: str) -> bool:
    """
    判断某十神是否为喜神（格局用神方向）。
    出处：《滴天髓·六亲论》'喜神即是财神，其妻美而且富贵'

    简化判断：格局用神方向上的十神 = 喜神
    """
    # 格局用神方向
    xi_shen_map = {
        "正官格": ["正财", "偏财", "正印", "偏印"],
        "七杀格": ["食神", "伤官", "正印", "偏印"],
        "正印格": ["正官", "七杀", "比肩", "劫财"],
        "偏印格": ["正官", "七杀", "比肩", "劫财"],
        "食神格": ["正财", "偏财", "食神"],
        "伤官格": ["正财", "偏财", "正印", "偏印"],
        "正财格": ["正官", "食神", "伤官"],
        "偏财格": ["正官", "食神", "伤官"],
    }
    for key, xi_list in xi_shen_map.items():
        if key in pattern_name:
            return god in xi_list
    return False


def assess_liuqin_quality(chart: BaziChart,
                           pattern_name: str,
                           pattern_status: str,
                           system: str = "A") -> dict:
    """
    六亲质量评估。

    参数：
        system: "A"=渊海子平体系，"B"=滴天髓体系

    判断维度：
    1. 六亲十神是否为喜神（出处：《滴天髓·六亲论》）
    2. 六亲十神的月令旺衰（出处：《三命通会·卷七》）
    3. 日支宫位（妻缘专用）（出处：《子平真诠·二十四》）
    """
    ri = chart.ri_gan
    ri_zhi = chart.ri_zhi

    results = {}

    for liuqin, god_map in LIUQIN_GODS.items():
        gods = god_map.get(system, god_map["A"])

        strength = _get_liuqin_god_strength(chart, gods)
        if not strength["存在"]:
            results[liuqin] = {
                "状态":   "十神不存在",
                "说明":   f"命局中无{'/'.join(gods)}，该六亲十神缺位",
                "质量倾向": "无法判断",
            }
            continue

        # 维度一：是否喜神
        is_xi = any(_is_xi_shen(chart, g, pattern_name, pattern_status)
                    for g in gods)

        # 维度二：月令旺衰
        de_ling = strength["得令"]
        yue_strength = strength["月令强度"]

        # 维度三：日支宫位（仅妻）
        ri_zhi_note = ""
        if liuqin == "妻":
            ri_zhi_god = get_ten_god(ri, ZHI_CANG_GAN.get(ri_zhi, [""])[0])
            if ri_zhi_god in ("正财", "偏财"):
                ri_zhi_note = "日支坐财，妻宫得用，吉"
            elif ri_zhi_god in ("正官", "七杀"):
                ri_zhi_note = "日支坐官，妻宫吉"
            elif ri_zhi_god == "伤官":
                ri_zhi_note = "日支坐伤官，需看格局配合"
            else:
                ri_zhi_note = f"日支坐{ri_zhi_god}"

        # 综合质量判断
        good_signals = sum([is_xi, de_ling])
        bad_signals  = sum([not is_xi, yue_strength == 0])

        if good_signals >= 2:
            quality = "好"
            quality_desc = (
                ("喜神即是六亲星，" if is_xi else "") +
                ("六亲星得令有力" if de_ling else "")
            ).strip("，")
        elif good_signals == 1 and bad_signals <= 1:
            quality = "中"
            quality_desc = "条件部分满足，有好有不足"
        else:
            quality = "差"
            quality_desc = (
                ("六亲星非喜神，" if not is_xi else "") +
                ("六亲星失令无力" if yue_strength == 0 else "")
            ).strip("，")

        entry = {
            "对应十神":   gods,
            "透干":       strength["透干"],
            "月令强度":   yue_strength,
            "是否喜神":   is_xi,
            "质量倾向":   quality,
            "说明":       quality_desc,
        }

        # 加入原典对应结论
        if liuqin == "妻":
            if quality == "好" and is_xi:
                entry["原典对应"] = "喜神即是财神，其妻美而且富贵（《滴天髓·六亲论》）"
            elif quality == "差":
                entry["原典对应"] = "喜神与财神相妒忌，否则克妻，亦或不美（《滴天髓·六亲论》）"
            if ri_zhi_note:
                entry["日支妻宫"] = ri_zhi_note + "（《子平真诠·二十四》）"

        elif liuqin == "子":
            if quality == "好" and is_xi:
                entry["原典对应"] = "喜神即是官星，其子贤俊（《滴天髓·六亲论》）"
            elif quality == "差":
                entry["原典对应"] = "喜神与官星相妒，则无子或不肖（《滴天髓·六亲论》）"

        elif liuqin in ("父", "母"):
            if quality == "好":
                entry["原典对应"] = "父母星坐生旺之地，主父母富贵福寿（《三命通会·卷七》）"
            else:
                entry["原典对应"] = "父母星坐衰败之地，主父母贫薄刑夭（《三命通会·卷七》）"

        results[liuqin] = entry

    return {
        "使用体系":   f"体系{'A（渊海子平）' if system == 'A' else 'B（滴天髓）'}",
        "六亲质量":   results,
        "判断维度说明": [
            "维度一：六亲十神是否为格局喜神（出处：《滴天髓·六亲论》）",
            "维度二：六亲十神月令旺衰（出处：《三命通会·卷七·论六亲》）",
            "维度三：日支妻宫（仅妻，出处：《子平真诠·二十四、论妻子》）",
        ],
        "重要说明": (
            "质量倾向为结构性判断，反映命局条件，"
            "非时间性预测。具体何时显现需结合大运流年。"
        ),
    }
