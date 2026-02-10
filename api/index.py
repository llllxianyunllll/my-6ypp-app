# api/index.py
from http.server import BaseHTTPRequestHandler
import json
import datetime
from urllib.parse import urlparse, parse_qs
import sxtwl  # 必须在 requirements.txt 中添加 sxtwl

# ==========================================
# 1. 基础字典与配置 (来自 auxiliary_tools.py & hexagram_data.py)
# ==========================================
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

PALACE_PROPERTIES = {
    "乾": {"element": "金", "code": "111"},
    "兑": {"element": "金", "code": "110"},
    "离": {"element": "火", "code": "101"},
    "震": {"element": "木", "code": "100"},
    "巽": {"element": "木", "code": "011"},
    "坎": {"element": "水", "code": "010"},
    "艮": {"element": "土", "code": "001"},
    "坤": {"element": "土", "code": "000"}
}

# ==========================================
# 六十四卦全量字典
# ==========================================
# Key规则: 下卦二进制 + 上卦二进制 (从初爻到上爻, 0=阴, 1=阳)
DATA_64 = {
    # ---------------- 乾宫 (金) ----------------
    "111111": {"name": "乾为天", "gong": "乾", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "011111": {"name": "天风姤", "gong": "乾", "shi": 1, "ying": 4, "nature": "", "label": "一世"},
    "001111": {"name": "天山遁", "gong": "乾", "shi": 2, "ying": 5, "nature": "", "label": "二世"},
    "000111": {"name": "天地否", "gong": "乾", "shi": 3, "ying": 6, "nature": "六合", "label": "三世"},
    "000011": {"name": "风地观", "gong": "乾", "shi": 4, "ying": 1, "nature": "", "label": "四世"},
    "000001": {"name": "山地剥", "gong": "乾", "shi": 5, "ying": 2, "nature": "", "label": "五世"},
    "000101": {"name": "火地晋", "gong": "乾", "shi": 4, "ying": 1, "nature": "游魂", "label": "游魂"},
    "111101": {"name": "火天大有", "gong": "乾", "shi": 3, "ying": 6, "nature": "归魂", "label": "归魂"},

    # ---------------- 兑宫 (金) ----------------
    "110110": {"name": "兑为泽", "gong": "兑", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "010110": {"name": "泽水困", "gong": "兑", "shi": 1, "ying": 4, "nature": "六合", "label": "一世"},
    "000110": {"name": "泽地萃", "gong": "兑", "shi": 2, "ying": 5, "nature": "", "label": "二世"},
    "001110": {"name": "泽山咸", "gong": "兑", "shi": 3, "ying": 6, "nature": "", "label": "三世"},
    "001010": {"name": "水山蹇", "gong": "兑", "shi": 4, "ying": 1, "nature": "", "label": "四世"},
    "001000": {"name": "地山谦", "gong": "兑", "shi": 5, "ying": 2, "nature": "", "label": "五世"},
    "001100": {"name": "雷山小过", "gong": "兑", "shi": 4, "ying": 1, "nature": "游魂", "label": "游魂"},
    "110100": {"name": "雷泽归妹", "gong": "兑", "shi": 3, "ying": 6, "nature": "归魂", "label": "归魂"},

    # ---------------- 离宫 (火) ----------------
    "101101": {"name": "离为火", "gong": "离", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "001101": {"name": "火山旅", "gong": "离", "shi": 1, "ying": 4, "nature": "六合", "label": "一世"},
    "011101": {"name": "火风鼎", "gong": "离", "shi": 2, "ying": 5, "nature": "", "label": "二世"},
    "010101": {"name": "火水未济", "gong": "离", "shi": 3, "ying": 6, "nature": "", "label": "三世"},
    "010001": {"name": "山水蒙", "gong": "离", "shi": 4, "ying": 1, "nature": "", "label": "四世"},
    "010011": {"name": "风水涣", "gong": "离", "shi": 5, "ying": 2, "nature": "", "label": "五世"},
    "010111": {"name": "天水讼", "gong": "离", "shi": 4, "ying": 1, "nature": "游魂", "label": "游魂"},
    "101111": {"name": "天火同人", "gong": "离", "shi": 3, "ying": 6, "nature": "归魂", "label": "归魂"},

    # ---------------- 震宫 (木) ----------------
    "100100": {"name": "震为雷", "gong": "震", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "000100": {"name": "雷地豫", "gong": "震", "shi": 1, "ying": 4, "nature": "六合", "label": "一世"},
    "010100": {"name": "雷水解", "gong": "震", "shi": 2, "ying": 5, "nature": "", "label": "二世"},
    "011100": {"name": "雷风恒", "gong": "震", "shi": 3, "ying": 6, "nature": "", "label": "三世"},
    "011000": {"name": "地风升", "gong": "震", "shi": 4, "ying": 1, "nature": "", "label": "四世"},
    "011010": {"name": "水风井", "gong": "震", "shi": 5, "ying": 2, "nature": "", "label": "五世"},
    "011110": {"name": "泽风大过", "gong": "震", "shi": 4, "ying": 1, "nature": "游魂", "label": "游魂"},
    "100110": {"name": "泽雷随", "gong": "震", "shi": 3, "ying": 6, "nature": "归魂", "label": "归魂"},

    # ---------------- 巽宫 (木) ----------------
    "011011": {"name": "巽为风", "gong": "巽", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "111011": {"name": "风天小畜", "gong": "巽", "shi": 1, "ying": 4, "nature": "", "label": "一世"},
    "101011": {"name": "风火家人", "gong": "巽", "shi": 2, "ying": 5, "nature": "", "label": "二世"},
    "100011": {"name": "风雷益", "gong": "巽", "shi": 3, "ying": 6, "nature": "", "label": "三世"},
    "100111": {"name": "天雷无妄", "gong": "巽", "shi": 4, "ying": 1, "nature": "六冲", "label": "四世"},  # 注意无妄是六冲
    "100101": {"name": "火雷噬嗑", "gong": "巽", "shi": 5, "ying": 2, "nature": "", "label": "五世"},
    "100001": {"name": "山雷颐", "gong": "巽", "shi": 4, "ying": 1, "nature": "游魂", "label": "游魂"},
    "011001": {"name": "山风蛊", "gong": "巽", "shi": 3, "ying": 6, "nature": "归魂", "label": "归魂"},

    # ---------------- 坎宫 (水) ----------------
    "010010": {"name": "坎为水", "gong": "坎", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "110010": {"name": "水泽节", "gong": "坎", "shi": 1, "ying": 4, "nature": "六合", "label": "一世"},
    "100010": {"name": "水雷屯", "gong": "坎", "shi": 2, "ying": 5, "nature": "", "label": "二世"},
    "101010": {"name": "水火既济", "gong": "坎", "shi": 3, "ying": 6, "nature": "", "label": "三世"},
    "101110": {"name": "泽火革", "gong": "坎", "shi": 4, "ying": 1, "nature": "", "label": "四世"},
    "101100": {"name": "雷火丰", "gong": "坎", "shi": 5, "ying": 2, "nature": "", "label": "五世"},
    "101000": {"name": "地火明夷", "gong": "坎", "shi": 4, "ying": 1, "nature": "游魂", "label": "游魂"},
    "010000": {"name": "地水师", "gong": "坎", "shi": 3, "ying": 6, "nature": "归魂", "label": "归魂"},

    # ---------------- 艮宫 (土) ----------------
    "001001": {"name": "艮为山", "gong": "艮", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "101001": {"name": "山火贲", "gong": "艮", "shi": 1, "ying": 4, "nature": "六合", "label": "一世"},
    "111001": {"name": "山天大畜", "gong": "艮", "shi": 2, "ying": 5, "nature": "", "label": "二世"},
    "110001": {"name": "山泽损", "gong": "艮", "shi": 3, "ying": 6, "nature": "", "label": "三世"},
    "110101": {"name": "火泽睽", "gong": "艮", "shi": 4, "ying": 1, "nature": "", "label": "四世"},
    "110111": {"name": "天泽履", "gong": "艮", "shi": 5, "ying": 2, "nature": "", "label": "五世"},
    "110011": {"name": "风泽中孚", "gong": "艮", "shi": 4, "ying": 1, "nature": "游魂", "label": "游魂"},
    "001011": {"name": "风山渐", "gong": "艮", "shi": 3, "ying": 6, "nature": "归魂", "label": "归魂"},

    # ---------------- 坤宫 (土) ----------------
    "000000": {"name": "坤为地", "gong": "坤", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "100000": {"name": "地雷复", "gong": "坤", "shi": 1, "ying": 4, "nature": "六合", "label": "一世"},
    "110000": {"name": "地泽临", "gong": "坤", "shi": 2, "ying": 5, "nature": "", "label": "二世"},
    "111000": {"name": "地天泰", "gong": "坤", "shi": 3, "ying": 6, "nature": "六合", "label": "三世"},
    "111100": {"name": "雷天大壮", "gong": "坤", "shi": 4, "ying": 1, "nature": "六冲", "label": "四世"},
    "111110": {"name": "泽天夬", "gong": "坤", "shi": 5, "ying": 2, "nature": "", "label": "五世"},
    "111010": {"name": "水天需", "gong": "坤", "shi": 4, "ying": 1, "nature": "游魂", "label": "游魂"},
    "000010": {"name": "水地比", "gong": "坤", "shi": 3, "ying": 6, "nature": "归魂", "label": "归魂"},
}

# 为了代码能跑，我补充几个关键卦象避免报错，你部署时请务必把你的 DATA_64 完整版填回来
DATA_64.update({
    "000000": {"name": "坤为地", "gong": "坤", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "101101": {"name": "离为火", "gong": "离", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "010010": {"name": "坎为水", "gong": "坎", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "100100": {"name": "震为雷", "gong": "震", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "001001": {"name": "艮为山", "gong": "艮", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "011011": {"name": "巽为风", "gong": "巽", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
    "110110": {"name": "兑为泽", "gong": "兑", "shi": 6, "ying": 3, "nature": "六冲", "label": "本宫"},
})

YAO_MAP = {
    6: {"name": "老阴", "val": 0, "change": 1, "is_moving": True, "symbol": "== x =="},
    7: {"name": "少阳", "val": 1, "change": 1, "is_moving": False, "symbol": "======="},
    8: {"name": "少阴", "val": 0, "change": 0, "is_moving": False, "symbol": "==   =="},
    9: {"name": "老阳", "val": 1, "change": 0, "is_moving": True, "symbol": "===o==="},
}

FIVE_ELEMENTS_RELATION = {
    "金": {"金": "兄弟", "水": "子孙", "木": "妻财", "火": "官鬼", "土": "父母"},
    "木": {"木": "兄弟", "火": "子孙", "土": "妻财", "金": "官鬼", "水": "父母"},
    "水": {"水": "兄弟", "木": "子孙", "火": "妻财", "土": "官鬼", "金": "父母"},
    "火": {"火": "兄弟", "土": "子孙", "金": "妻财", "水": "官鬼", "木": "父母"},
    "土": {"土": "兄弟", "金": "子孙", "水": "妻财", "木": "官鬼", "火": "父母"},
}

ZHI_ELEMENTS = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

BINARY_TO_TRIGRAM = {
    "111": "乾", "110": "兑", "101": "离", "100": "震",
    "011": "巽", "010": "坎", "001": "艮", "000": "坤"
}

NAJIA_RULES = {
    "乾": {"inner": [("甲", "子"), ("甲", "寅"), ("甲", "辰")], "outer": [("壬", "午"), ("壬", "申"), ("壬", "戌")]},
    "坎": {"inner": [("戊", "寅"), ("戊", "辰"), ("戊", "午")], "outer": [("戊", "申"), ("戊", "戌"), ("戊", "子")]},
    "艮": {"inner": [("丙", "辰"), ("丙", "午"), ("丙", "申")], "outer": [("丙", "戌"), ("丙", "子"), ("丙", "寅")]},
    "震": {"inner": [("庚", "子"), ("庚", "寅"), ("庚", "辰")], "outer": [("庚", "午"), ("庚", "申"), ("庚", "戌")]},
    "巽": {"inner": [("辛", "丑"), ("辛", "亥"), ("辛", "酉")], "outer": [("辛", "未"), ("辛", "巳"), ("辛", "卯")]},
    "离": {"inner": [("己", "卯"), ("己", "丑"), ("己", "亥")], "outer": [("己", "酉"), ("己", "未"), ("己", "巳")]},
    "坤": {"inner": [("乙", "未"), ("乙", "巳"), ("乙", "卯")], "outer": [("癸", "丑"), ("癸", "亥"), ("癸", "酉")]},
    "兑": {"inner": [("丁", "巳"), ("丁", "卯"), ("丁", "丑")], "outer": [("丁", "亥"), ("丁", "酉"), ("丁", "未")]}
}


# ==========================================
# 2. 核心类定义 (合并自各文件)
# ==========================================

class LiuShouSolver:
    BEASTS = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"]

    @staticmethod
    def get_six_beasts(day_gan):
        if day_gan in ["甲", "乙"]:
            start_idx = 0
        elif day_gan in ["丙", "丁"]:
            start_idx = 1
        elif day_gan == "戊":
            start_idx = 2
        elif day_gan == "己":
            start_idx = 3
        elif day_gan in ["庚", "辛"]:
            start_idx = 4
        elif day_gan in ["壬", "癸"]:
            start_idx = 5
        else:
            return ["未知"] * 6
        result = []
        for i in range(6):
            idx = (start_idx + i) % 6
            result.append(LiuShouSolver.BEASTS[idx])
        return result


class XunKongSolver:
    @staticmethod
    def get_xun_kong(gan_str, zhi_str):
        if gan_str not in GAN or zhi_str not in ZHI: return ""
        gan_idx = GAN.index(gan_str)
        zhi_idx = ZHI.index(zhi_str)
        diff = (zhi_idx - gan_idx) % 12
        empty1_idx = (diff - 2) % 12
        empty2_idx = (diff - 1) % 12
        return f"{ZHI[empty1_idx]}{ZHI[empty2_idx]}"


class TimeEngine:
    # 简化版的 TimeEngine，去掉了大量 print，只返回四柱字典
    def get_four_pillars_dict(self, year, month, day, hour, minute):
        # 1. 计算 JD
        if month <= 2:
            year -= 1
            month += 12
        a = year // 100
        b = 2 - a + a // 4
        jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
        fraction = (hour + minute / 60.0) / 24.0
        current_jd = jd + fraction

        # 恢复年份用于后续计算 (如果上面减了1)
        calc_year = year + 1 if month > 12 else year
        calc_month = month - 12 if month > 12 else month

        # 2. 立春判断 (简化逻辑，实际应调用 sxtwl)
        # 这里为了演示直接使用 sxtwl
        solar_day = sxtwl.fromSolar(calc_year, calc_month, day)
        gz = solar_day.getHourGZ(hour)
        y_gz = solar_day.getYearGZ()
        m_gz = solar_day.getMonthGZ()
        d_gz = solar_day.getDayGZ()

        # sxtwl 的干支索引 0-9, 0-11
        year_pillar = GAN[y_gz.tg] + ZHI[y_gz.dz]
        month_pillar = GAN[m_gz.tg] + ZHI[m_gz.dz]
        day_pillar = GAN[d_gz.tg] + ZHI[d_gz.dz]
        hour_pillar = GAN[gz.tg] + ZHI[gz.dz]

        return {
            "year": year_pillar,
            "month": month_pillar,
            "day": day_pillar,
            "hour": hour_pillar,
            "day_gan": GAN[d_gz.tg],
            "day_zhi": ZHI[d_gz.dz]
        }


def get_hexagram_info(binary_list):
    key = "".join(str(b) for b in binary_list)
    # 如果找不到，尝试去 DATA_64 里找
    if key in DATA_64:
        info = DATA_64[key].copy()
        gong_name = info["gong"]
        if gong_name in PALACE_PROPERTIES:
            info["gong_element"] = PALACE_PROPERTIES[gong_name]["element"]
        return info
    return {"name": f"未知卦({key})", "gong": "未知", "gong_element": "未知", "shi": 0, "ying": 0}


class NajiaEngine:
    def perform_najia(self, hexagram_code, gong_element):
        inner_code = hexagram_code[0:3]
        outer_code = hexagram_code[3:6]
        inner_key = "".join(str(b) for b in inner_code)
        outer_key = "".join(str(b) for b in outer_code)
        inner_name = BINARY_TO_TRIGRAM.get(inner_key, "未知")
        outer_name = BINARY_TO_TRIGRAM.get(outer_key, "未知")

        if inner_name == "未知" or outer_name == "未知": return []

        inner_ganzhi = NAJIA_RULES[inner_name]["inner"]
        outer_ganzhi = NAJIA_RULES[outer_name]["outer"]
        full_ganzhi = inner_ganzhi + outer_ganzhi

        result_lines = []
        for i, (gan, zhi) in enumerate(full_ganzhi):
            yao_element = ZHI_ELEMENTS[zhi]
            relation = FIVE_ELEMENTS_RELATION.get(gong_element, {}).get(yao_element, "未知")
            result_lines.append({
                "position": i + 1, "gan": gan, "zhi": zhi, "element": yao_element, "relation": relation
            })
        return result_lines

    def find_fushen(self, current_lines, gong_element, ben_gong_lines):
        present_relations = set(line['relation'] for line in current_lines)
        ALL_RELATIONS = ["父母", "兄弟", "官鬼", "妻财", "子孙"]
        missing_relations = [r for r in ALL_RELATIONS if r not in present_relations]

        fushen_map = {}
        if not missing_relations: return fushen_map

        for missing in missing_relations:
            for i, bg_line in enumerate(ben_gong_lines):
                if bg_line['relation'] == missing:
                    fushen_map[i] = f"{bg_line['relation']}{bg_line['gan']}{bg_line['zhi']}{bg_line['element']}"
        return fushen_map


# ==========================================
# 3. Vercel Handler (入口)
# ==========================================

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. 允许跨域
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            # 2. 解析参数
            query = urlparse(self.path).query
            params = parse_qs(query)

            # 默认参数（如果没传）
            year = int(params.get('year', [2026])[0])
            month = int(params.get('month', [2])[0])
            day = int(params.get('day', [10])[0])
            hour = int(params.get('hour', [12])[0])

            # 获取六爻输入 (例如 ?q=8,8,8,8,8,9)
            # 或者是 q1=8&q2=8...
            # 这里简化，假设通过 ?yao=8,8,8,8,8,9 传入
            yao_str = params.get('yao', ["8,8,8,8,8,8"])[0]
            user_input = [int(x) for x in yao_str.split(',')]

            # 3. 执行逻辑 (Controller)

            # A. 时间计算
            time_engine = TimeEngine()
            bazi = time_engine.get_four_pillars_dict(year, month, day, hour, 0)

            # B. 神煞
            xun_kong = XunKongSolver.get_xun_kong(bazi['day_gan'], bazi['day_zhi'])
            six_beasts = LiuShouSolver.get_six_beasts(bazi['day_gan'])

            # C. 排卦
            hexagram_data = []
            base_code = []
            future_code = []

            for i, val in enumerate(user_input):
                info = YAO_MAP[val]
                base_code.append(info["val"])
                future_code.append(info["change"])
                hexagram_data.append({
                    "val": val,
                    "symbol": info["symbol"],
                    "is_moving": info["is_moving"]
                })

            # D. 识别卦名
            ben_gua_info = get_hexagram_info(base_code)
            zhi_gua_info = get_hexagram_info(future_code)

            # E. 纳甲
            najia = NajiaEngine()
            ben_gua_lines = najia.perform_najia(base_code, ben_gua_info.get('gong_element', '未知'))

            # F. 变卦纳甲
            zhi_gua_lines = []
            if base_code != future_code:
                zhi_gua_lines = najia.perform_najia(future_code, ben_gua_info.get('gong_element', '未知'))
            else:
                zhi_gua_lines = ben_gua_lines  # 没变卦就复制一份

            # G. 伏神
            fushen_map = {}
            gong_name = ben_gua_info.get('gong', '')
            if gong_name in PALACE_PROPERTIES:
                gong_code = [int(x) for x in list(PALACE_PROPERTIES[gong_name]['code'] * 2)]
                ben_gong_lines = najia.perform_najia(gong_code, ben_gua_info.get('gong_element'))
                fushen_map = najia.find_fushen(ben_gua_lines, ben_gua_info.get('gong_element'), ben_gong_lines)

            # 4. 组装结果
            response_data = {
                "status": "success",
                "bazi": bazi,
                "shensha": {
                    "xun_kong": xun_kong,
                    "six_beasts": six_beasts
                },
                "ben_gua": {
                    "name": ben_gua_info['name'],
                    "gong": ben_gua_info['gong'],
                    "element": ben_gua_info.get('gong_element'),
                    "shi": ben_gua_info['shi'],
                    "ying": ben_gua_info['ying'],
                    "nature": ben_gua_info['nature']
                },
                "zhi_gua": {
                    "name": zhi_gua_info['name'] if base_code != future_code else ""
                },
                "lines": []
            }

            # 组合每一爻的详细信息
            for i in range(6):
                # i=0是初爻
                line_data = {
                    "position": i + 1,
                    "beast": six_beasts[i],
                    "fushen": fushen_map.get(i, ""),
                    "ben_gua": {
                        "gan": ben_gua_lines[i]['gan'],
                        "zhi": ben_gua_lines[i]['zhi'],
                        "element": ben_gua_lines[i]['element'],
                        "relation": ben_gua_lines[i]['relation'],
                        "symbol": hexagram_data[i]['symbol'],
                        "is_moving": hexagram_data[i]['is_moving']
                    },
                    "zhi_gua": {}
                }

                if hexagram_data[i]['is_moving']:
                    line_data["zhi_gua"] = {
                        "gan": zhi_gua_lines[i]['gan'],
                        "zhi": zhi_gua_lines[i]['zhi'],
                        "element": zhi_gua_lines[i]['element'],
                        "relation": zhi_gua_lines[i]['relation']
                    }

                response_data["lines"].append(line_data)

            # 5. 发送 JSON
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            error_data = {"status": "error", "message": str(e)}
            self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))