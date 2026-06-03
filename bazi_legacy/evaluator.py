# ==============================================================================
# evaluator.py —— 《子平真诠》八格成败救应引擎
# PatternManager 严格且唯一依据《子平真诠》八格表格，表格之外的条件一律不采用。
# ==============================================================================

import json
import datetime as _dt
from bazi_engine import BaziChart, TIAN_GAN, DI_ZHI

# ── 基础五行映射 ──────────────────────────────────────────────────────────────
GAN_WU_XING = {
    "甲":"木","乙":"木","丙":"火","丁":"火","戊":"土",
    "己":"土","庚":"金","辛":"金","壬":"水","癸":"水",
}
ZHI_CANG_GAN = {
    "子":["癸"],"丑":["己","癸","辛"],"寅":["甲","丙","戊"],"卯":["乙"],
    "辰":["戊","乙","癸"],"巳":["丙","庚","戊"],"午":["丁","己"],"未":["己","丁","乙"],
    "申":["庚","壬","戊"],"酉":["辛"],"戌":["戊","辛","丁"],"亥":["壬","甲"],
}

# 地支相冲对
XIANG_CHONG = {
    ("子","午"),("午","子"),("丑","未"),("未","丑"),
    ("寅","申"),("申","寅"),("卯","酉"),("酉","卯"),
    ("辰","戌"),("戌","辰"),("巳","亥"),("亥","巳"),
}

# 天干六合（用于判断"官被合去"/"煞被合去"/"财被合去"）
GAN_HE = {
    ("甲","己"),("己","甲"),("乙","庚"),("庚","乙"),
    ("丙","辛"),("辛","丙"),("丁","壬"),("壬","丁"),
    ("戊","癸"),("癸","戊"),
}

# 地支六合（用于"会合解冲"救应）
ZHI_LIU_HE = {
    ("子","丑"),("丑","子"),("寅","亥"),("亥","寅"),
    ("卯","戌"),("戌","卯"),("辰","酉"),("酉","辰"),
    ("巳","申"),("申","巳"),("午","未"),("未","午"),
}

# 地支三合局
ZHI_SAN_HE = [
    {"申","子","辰"},{"寅","午","戌"},{"巳","酉","丑"},{"亥","卯","未"},
]

# ==============================================================================
# 十神关系计算
# ==============================================================================

YANG_GAN = {"甲","丙","戊","庚","壬"}
SHENG = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
KE    = {"木":"土","土":"水","水":"火","火":"金","金":"木"}

def get_ten_god(ri_gan, target_gan):
    if ri_gan == target_gan: return "日主"
    ri_wx = GAN_WU_XING[ri_gan]; tg_wx = GAN_WU_XING[target_gan]
    same = (ri_gan in YANG_GAN) == (target_gan in YANG_GAN)
    if ri_wx == tg_wx:              return "比肩" if same else "劫财"
    if SHENG[tg_wx] == ri_wx:       return "偏印" if same else "正印"
    if SHENG[ri_wx] == tg_wx:       return "食神" if same else "伤官"
    if KE[tg_wx]    == ri_wx:       return "七杀" if same else "正官"
    if KE[ri_wx]    == tg_wx:       return "偏财" if same else "正财"
    return "未知"

# ==============================================================================
# 局面信息提取器
# ==============================================================================

class SituationReader:
    """
    从 BaziChart 一次性提取所有格局判断所需的布尔标志。
    所有标志严格来自原典表格中出现的概念，不引入表格外条件。
    """
    def __init__(self, chart):
        ri = chart.ri_gan
        self.yue_ben_qi  = ZHI_CANG_GAN[chart.yue_zhi][0]
        self.pattern_god = get_ten_god(ri, self.yue_ben_qi)

        all_gans = [chart.nian_gan, chart.yue_gan, chart.ri_gan, chart.shi_gan]
        non_ri   = [g for g in all_gans if g != ri]
        all_zhis = [chart.nian_zhi, chart.yue_zhi, chart.ri_zhi, chart.shi_zhi]
        gods     = [get_ten_god(ri, g) for g in non_ri]

        self.has_zheng_guan = "正官" in gods
        self.has_qi_sha     = "七杀" in gods
        self.has_zheng_yin  = "正印" in gods
        self.has_pian_yin   = "偏印" in gods
        self.has_yin        = self.has_zheng_yin or self.has_pian_yin
        self.has_shi_shen   = "食神" in gods
        self.has_shang_guan = "伤官" in gods
        self.has_zheng_cai  = "正财" in gods
        self.has_pian_cai   = "偏财" in gods
        self.has_cai        = self.has_zheng_cai or self.has_pian_cai
        self.has_bi_jian    = "比肩" in gods
        self.has_jie_cai    = "劫财" in gods
        self.has_bi_jie     = self.has_bi_jian or self.has_jie_cai

        # 地支相冲
        self.has_chong = any(
            (z1, z2) in XIANG_CHONG
            for i, z1 in enumerate(all_zhis)
            for j, z2 in enumerate(all_zhis) if i != j
        )

        # 天干六合：正官被合去
        guan_gans = [g for g in non_ri if get_ten_god(ri, g) == "正官"]
        self.guan_he_qu = any(
            (guan_g, other) in GAN_HE
            for guan_g in guan_gans
            for other in non_ri if other != guan_g
        )

        # 天干六合：七杀被合去
        sha_gans = [g for g in non_ri if get_ten_god(ri, g) == "七杀"]
        self.sha_he_qu = any(
            (sha_g, other) in GAN_HE
            for sha_g in sha_gans
            for other in non_ri if other != sha_g
        )

        # 天干六合：财被合去
        cai_gans = [g for g in non_ri if get_ten_god(ri, g) in ("正财","偏财")]
        self.cai_he_qu = any(
            (cai_g, other) in GAN_HE
            for cai_g in cai_gans
            for other in non_ri if other != cai_g
        )

        # 地支会合解冲
        self.has_zhi_he = any(
            (z1, z2) in ZHI_LIU_HE
            for i, z1 in enumerate(all_zhis)
            for j, z2 in enumerate(all_zhis) if i != j
        ) or any(set(all_zhis) >= combo for combo in ZHI_SAN_HE)

        # 日主得令（月令本气同五行或生日主）
        ri_wx = GAN_WU_XING[ri]
        ben_qi_wx = GAN_WU_XING[self.yue_ben_qi]
        self.de_ling = (ben_qi_wx == ri_wx) or (SHENG.get(ben_qi_wx) == ri_wx)


# ==============================================================================
# PatternManager — 严格依据《子平真诠》八格表格
# ==============================================================================

def _r(name, status, reason):
    return {"main_pattern": name, "status": status, "reason": reason}


class PatternManager:
    """
    判定顺序（状态机）：
      1. 救应条件 → status = "救应"
      2. 败格条件 → status = "败"
      3. 成格条件 → status = "成"
      4. 以上均不命中 → status = "成"（格局自然成立）
    """

    # ── 正官格 ────────────────────────────────────────────────────────────────
    def _zheng_guan(self, s):
        name = "正官格"
        # 救应①：官逢伤而透印以解之
        if s.has_shang_guan and s.has_yin:
            return _r(name, "救应", "官逢伤官，透印解围（官逢伤而透印以解之）")
        # 救应②：杂煞合煞以清之（合煞留官）
        if s.has_qi_sha and s.sha_he_qu:
            return _r(name, "救应", "官杀混杂，合煞留官以清之")
        # 救应③：刑冲而会合以解之
        if s.has_chong and s.has_zhi_he:
            return _r(name, "救应", "刑冲而地支会合解之")
        # 败①：官逢伤官克制
        if s.has_shang_guan:
            return _r(name, "败", "正官逢伤官克制（官逢伤克，官格败也）")
        # 败②：地支刑冲（无会合解救）
        if s.has_chong:
            return _r(name, "败", "官星地支遭刑冲破害")
        # 败③：透官而又逢合（正官被合去）
        if s.guan_he_qu:
            return _r(name, "败", "正官透干而被合去（透官逢合，带忌）")
        # 败④：正官逢财而又逢伤
        if s.has_cai and s.has_shang_guan:
            return _r(name, "败", "正官逢财而又逢伤官（带忌）")
        # 成①：官逢财印，无刑冲破害
        if (s.has_cai or s.has_yin) and not s.has_chong:
            return _r(name, "成", "官逢财印相生相护，无刑冲破害（官格成也）")
        # 成②：财生官旺
        if s.has_cai:
            return _r(name, "成", "财星透干生官，财生官旺")
        return _r(name, "成", "正官格当令，格局成立")

    # ── 七杀格 ────────────────────────────────────────────────────────────────
    def _qi_sha(self, s):
        name = "七杀格"
        # 救应①：煞旺食制，印来护煞（煞食印俱全 + 有财流通）
        # 原典：印来护煞 = 煞/食/印三者兼备，需财化解印食矛盾
        if s.has_shi_shen and s.has_yin and s.has_cai:
            return _r(name, "救应", "食制煞而印护食且有财流通，煞食印财兼备（印来护煞）")
        # 救应②：逢财存食（财透食神仍存）
        if s.has_cai and s.has_shi_shen:
            return _r(name, "救应", "七杀逢财，食神仍存以制煞（存财而食制）")
        # 救应③：存财而合煞
        if s.has_cai and s.sha_he_qu:
            return _r(name, "救应", "财透而七杀被合去，存财合煞")
        # 败①：七煞逢财无制
        if s.has_cai and not s.has_shi_shen and not s.sha_he_qu:
            return _r(name, "败", "七杀逢财生煞，无食神制伏（煞逢财无制）")
        # 败②：有制而印夺食（有食制煞，但印夺食使制失效，且无财）
        if s.has_shi_shen and s.has_yin and not s.has_cai:
            return _r(name, "败", "食神制煞而印绶夺食，制煞失效（印夺食无制）")
        # 成①：身强七煞，食神制伏
        if s.de_ling and s.has_shi_shen:
            return _r(name, "成", "身强七煞，食神制伏，格局成也")
        # 成②：食神制煞（煞重就食制）
        if s.has_shi_shen:
            return _r(name, "成", "食神制七杀，煞重就食制")
        # 成③：煞印相生（以印化煞）
        if s.has_yin:
            return _r(name, "成", "七杀逢印，煞印相生以化煞")
        return _r(name, "成", "七杀格当令，格局成立")

    # ── 正印格 / 偏印格（同格论之）──────────────────────────────────────────
    def _yin_ge(self, s, is_pian):
        name = "偏印格" if is_pian else "正印格"
        # 救应①：印逢财，劫财制财以解
        if s.has_cai and s.has_bi_jie:
            return _r(name, "救应", "印逢财破，劫财制财以解（印逢财劫财解之）")
        # 救应②：合财而存印
        if s.has_cai and s.cai_he_qu:
            return _r(name, "救应", "财星被合去，印绶得存（合财而存印）")
        # 败①：印轻逢财（财克印）
        if s.has_cai:
            return _r(name, "败", "印绶逢财克制，印轻无力（印逢财破）")
        # 成①【先于败②】：煞印相生
        # 原典"煞印相生"是成格核心；"身强印重透煞"败格须同时满足：身旺+无食+无财
        if s.has_qi_sha:
            if s.de_ling and not s.has_shi_shen and not s.has_cai:
                return _r(name, "败", "身强印重又透七杀，纯旺无泄无制，格局破损")
            return _r(name, "成", "七杀生印，煞印相生，格局成也")
        # 败③：偏印夺食（偏印格特有）
        if is_pian and s.has_shi_shen and s.de_ling:
            return _r(name, "败", "偏印过旺，夺食神之秀（倒印逢，偏印夺食）")
        # 成②：官印双全
        if s.has_zheng_guan:
            return _r(name, "成", "官印双全，官生印护，格局成也")
        # 成③：身印旺用食泄秀
        if s.has_shi_shen:
            return _r(name, "成", "身印俱旺，食神泄秀，格局成也")
        return _r(name, "成", "印格当令，格局成立")


    # ── 食神格 ────────────────────────────────────────────────────────────────
    def _shi_shen(self, s):
        name = "食神格"
        # 救应①：食神杂煞，弃食就煞以成格（同时存在食与煞，取食制煞）
        if s.has_qi_sha and s.has_shi_shen:
            return _r(name, "救应", "食神遇七杀，弃食就煞煞以成格（食制煞救应）")
        # 救应②：透财克枭护食（偏印夺食，财克偏印护住食神）
        if s.has_pian_yin and s.has_cai:
            return _r(name, "救应", "透财克枭（偏印），护住食神（透财克枭护食）")
        # 败①：食神逢煞，无制无化（无食制煞，也无印化煞）
        if s.has_qi_sha and not s.has_shi_shen and not s.has_yin:
            return _r(name, "败", "食神逢七杀，无力制煞亦无印化（食神逢煞）")
        # 败②：生财露煞（财生煞，食神不能制）
        if s.has_cai and s.has_qi_sha and not s.has_shi_shen:
            return _r(name, "败", "生财而露七杀，煞得财生无制（生财露煞）")
        # 败③：食神带煞，印又透财（三者相克）
        if s.has_qi_sha and s.has_yin and s.has_cai:
            return _r(name, "败", "食神带煞印又透财，格局大损")
        # 败④：偏印夺食（枭神夺食）
        if s.has_pian_yin:
            return _r(name, "败", "偏印（枭神）夺食，食神被克（枭神夺食）")
        # 成①：食神生财
        if s.has_cai:
            return _r(name, "成", "食神顺生财星，格局成也")
        # 成②：带煞无财，弃食就煞透印（煞印相生）
        if s.has_qi_sha and s.has_yin:
            return _r(name, "成", "弃食就煞而透印，煞印相生，格局成也")
        return _r(name, "成", "食神格当令，格局成立")

    # ── 伤官格 ────────────────────────────────────────────────────────────────
    def _shang_guan(self, s):
        name = "伤官格"
        # 救应①：伤官生财透煞，而煞合（煞被合去）
        if s.has_cai and s.has_qi_sha and s.sha_he_qu:
            return _r(name, "救应", "伤官生财透煞，而煞被合去（伤官生财透煞而煞合）")
        # 败①：非金水见官（伤官格见正官，非金水格局为忌）
        if s.has_zheng_guan:
            return _r(name, "败", "伤官见官，格局大忌（非金水见官）")
        # 败②：生财带煞，煞无合
        if s.has_cai and s.has_qi_sha and not s.sha_he_qu:
            return _r(name, "败", "伤官生财而带七杀，煞得财生（生财带煞）")
        # 败④：带煞无财又逢合（伤官带煞无财，煞被合，流通断绝）
        if s.has_qi_sha and not s.has_cai and s.sha_he_qu:
            return _r(name, "败", "伤官带煞无财，煞又被合（伤官带煞无财又逢合）")
        # 成①：伤官生财
        if s.has_cai:
            return _r(name, "成", "伤官顺生财星，格局成也")
        # 成②：伤官旺印俱全
        if s.has_yin:
            return _r(name, "成", "伤官旺印俱全，相辅相成，格局成也")
        # 成③：伤官旺身弱透煞（化煞为用）
        # 注：原典"偏而身弱透煞"败格 vs "伤官旺身弱透煞"成格，区别在于伤官是否当旺
        # 实现层以月令本气即伤官（格局成立前提）= 伤官当旺，故身弱透煞统归成格
        if not s.de_ling and s.has_qi_sha:
            return _r(name, "成", "伤官身弱透煞，化煞为用，格局成也")
        # 成④：伤官带煞无财（伤官制煞，无财生煞）
        if s.has_qi_sha and not s.has_cai:
            return _r(name, "成", "伤官带煞无财，伤官制煞，格局成也")

        return _r(name, "成", "伤官格当令，格局成立")

    # ── 正财格 / 偏财格（同格论之）──────────────────────────────────────────
    def _cai_ge(self, s, is_pian):
        name = "偏财格" if is_pian else "正财格"
        # 救应①：财逢劫，食神化劫护财
        if s.has_bi_jie and s.has_shi_shen:
            return _r(name, "救应", "财逢劫夺，食神化劫护财（透食化劫）")
        # 救应②：生官以制劫（官克比劫护财）
        if s.has_bi_jie and s.has_zheng_guan:
            return _r(name, "救应", "财逢劫夺，官星制劫护财（生官以制之）")
        # 救应③：逢煞食神制煞生财
        if s.has_qi_sha and s.has_shi_shen:
            return _r(name, "救应", "财透七杀，食神制煞生财（食神制煞生财）")
        # 救应④：存财合煞（煞被合去）
        if s.has_qi_sha and s.sha_he_qu:
            return _r(name, "救应", "财透七杀，七杀被合去（存财合煞）")
        # 败①：财轻比劫（无食生财、无官制劫）
        if s.has_bi_jie and not s.has_shi_shen and not s.has_zheng_guan:
            return _r(name, "败", "财轻比劫旺，劫财夺财（财轻比劫）")
        # 败②：财透七杀，无制无合
        if s.has_qi_sha and not s.has_shi_shen and not s.sha_he_qu:
            return _r(name, "败", "财透七杀，煞得财生无制（财党七杀）")
        # 败③：财旺生官，官又逢伤
        if s.has_zheng_guan and s.has_shang_guan:
            return _r(name, "败", "财旺生官，官又逢伤官克制（生官逢伤）")
        # 败④：财旺生官，官被合去
        if s.has_zheng_guan and s.guan_he_qu:
            return _r(name, "败", "财旺生官，官被合去（生官逢合）")
        # 成①：财旺生官
        if s.has_zheng_guan:
            return _r(name, "成", "财旺生官，官财相生，格局成也")
        # 成②：财逢食且身强
        if s.has_shi_shen and s.de_ling:
            return _r(name, "成", "食神生财且日主身强，格局成也")
        # 成③：财格透印，两不相碍（财印不相克）
        if s.has_yin and not s.has_cai:
            return _r(name, "成", "财格透印，两不相碍，格局成也")
        return _r(name, "成", "财格当令，格局成立")

    # ── 对外入口 ──────────────────────────────────────────────────────────────
    def analyze(self, chart):
        s  = SituationReader(chart)
        pg = s.pattern_god
        if   pg == "正官": return self._zheng_guan(s)
        elif pg == "七杀": return self._qi_sha(s)
        elif pg == "正印": return self._yin_ge(s, False)
        elif pg == "偏印": return self._yin_ge(s, True)
        elif pg == "食神": return self._shi_shen(s)
        elif pg == "伤官": return self._shang_guan(s)
        elif pg == "正财": return self._cai_ge(s, False)
        elif pg == "偏财": return self._cai_ge(s, True)
        elif pg in ("比肩","劫财"):
            return _r(pg+"格（建禄/月劫）", "成",
                      "建禄月劫，日主通根，不入八格成败，另论用神")
        else:
            return _r(pg+"格", "成", "格局当令成立")


# ==============================================================================
# DynamicEvaluator（接口层不变）
# ==============================================================================

class DynamicEvaluator:
    def __init__(self): self.pm = PatternManager()

    def evaluate(self, y, m, d, h, mi=0, lon=116.4, gender=None):
        chart = BaziChart(y, m, d, h, mi, lon, gender=gender)
        return {"chart": chart, "patterns": self.pm.analyze(chart)}

    @staticmethod
    def to_json(res):
        c = res["chart"]; p = res["patterns"]
        payload = {
            "four_pillars": {"nian":c.nian_zhu,"yue":c.yue_zhu,"ri":c.ri_zhu,"shi":c.shi_zhu},
            "pattern_analysis": p,
            "ri_zhu": c.ri_gan,
        }
        if c.gender: payload["gender"] = c.gender
        if c.dayun:  payload["da_yun"] = c.dayun
        return json.dumps(payload, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    e = DynamicEvaluator()
    print("《子平真诠》八格成败救应引擎")
    while True:
        raw = input("\n时间(年,月,日,时,分，q退出): ").strip()
        if raw.lower() == "q": break
        try:
            parts = [int(x.strip()) for x in raw.replace("，",",").split(",")]
            g = input("性别(男/女，回车跳过): ").strip() or None
            if g not in ("男","女"): g = None
            res = e.evaluate(*parts, gender=g)
            print(e.to_json(res))
        except Exception as err: print(f"错误: {err}")
