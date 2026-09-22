# -*- coding: utf-8 -*-
"""
「研究生科研实力」硬数据子榜计算 (零声誉, 纯文献计量三源交叉)
数据源:
  leiden  CWTS Leiden Open Edition 2025  · P(top 10%) 高被引论文量   (全学科 · 质量×规模)
  ni      Nature Index 2026              · Share 顶刊论文贡献量      (基础科学顶刊)
  hici    Clarivate Highly Cited 2025    · 高被引科学家人数          (顶尖学者人才存量)
方法: 每源按指标值降序 -> 并列均位 -> 榜内百分位 pct=100*(N-pos)/(N-1)
      综合分 = Σ(w_i·pct_i)/Σ(w_i) 仅对该校「在场源」归一化
      (Leiden 仅覆盖大学、不含 CAS/马普等科研院所, 故不能沿用主榜「缺失源计 0」,
       否则会把科研院所误罚; 改按可比子集打分, 门槛 >=2 源。)
显示名/国家优先复用综合榜 stage1.json, 缺失回落英文原名。
"""
import json, sys
from pathlib import Path
BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
import matchlib as M

# ---- 跨源匹配增强: 常见缩写词映射 + 定向别名 ----
M.TOKMAP.update({"univ": "university", "inst": "institute", "natl": "national",
                 "tech": "technology", "technol": "technology", "sci": "science",
                 "eng": "engineering", "fed": "federal", "cent": "central",
                 "acad": "academy", "nat": "national"})
_extra_grad = {
    "cent s university": "central south university",
    "central s university": "central south university",
    "huazhong university science technology": "huazhong science technology university",
    "beijing university science technology": "university science technology beijing china",
    "mit": "massachusetts institute technology",
    "eth": "institute technology federal zurich",
    "swiss federal institute technology zurich": "eth zurich",
    "epfl": "institute technology federal lausanne",
    "swiss federal institute technology lausanne": "epfl",
}
M.OVERRIDES.update({M._sortkey_tokens(k): M._sortkey_tokens(v) for k, v in _extra_grad.items()})

def nk(n): return M.norm_key(n)

def _p(fname):
    """兼容 workspace(文件在 BASE) 与 repo(文件在 BASE/data) 两种布局"""
    a = BASE / fname
    return a if a.exists() else (BASE / "data" / fname)

# ---- 各源加载: 返回 {key: {en, val, country?}} + 有序 val 列表用于百分位 ----
_DIR = {"N":"North","S":"South","E":"East","W":"West","NE":"Northeast","NW":"Northwest",
        "SE":"Southeast","SW":"Southwest"}
def _expand_dir(name):
    """Leiden 常用单字母方位缩写(Univ S Florida / Middle E Tech ...), 仅作用于 Leiden 名"""
    out=[]
    for tok in name.split():
        core=tok.strip("().,")
        if core.upper() in _DIR and len(core)<=2 and core.isalpha():
            tok=tok.replace(core, _DIR[core.upper()])
        out.append(tok)
    return " ".join(out)

def load_leiden():
    d = {}
    for ln in _p("raw_leiden.tsv").read_text(encoding="utf-8").splitlines():
        p = ln.split("\t")
        if len(p) < 5: continue
        d[nk(_expand_dir(p[1]))] = {"en": p[1], "val": float(p[4])}   # col4 = P(top10%)
    return d

def load_ni():
    d = {}
    for ln in _p("raw_ni.tsv").read_text(encoding="utf-8").splitlines():
        p = ln.split("\t")
        if len(p) < 4: continue
        try: v = float(p[3])
        except ValueError: continue
        d[nk(p[1])] = {"en": p[1], "val": v, "country_en": p[2]}   # col3 = Share
    return d

def load_hici():
    d = {}
    for ln in _p("grad_hici.tsv").read_text(encoding="utf-8").splitlines():
        p = ln.split("\t")
        if len(p) < 3: continue
        try: v = float(p[1])
        except ValueError: continue
        d[nk(p[0])] = {"en": p[0], "val": v, "country_zh": p[2]}
    return d

def percentile(src):
    """按指标值降序 -> 并列均位 -> pct。返回 {key: (pct, display_rank, val)}"""
    items = sorted(src.items(), key=lambda kv: -kv[1]["val"])
    n = len(items)
    out = {}
    i = 0
    disp = 0
    while i < n:
        j = i
        while j + 1 < n and items[j + 1][1]["val"] == items[i][1]["val"]:
            j += 1
        avgpos = (i + 1 + j + 1) / 2.0            # 并列均位
        for t in range(i, j + 1):
            disp = i + 1                            # 区间起始作为展示名次
            out[items[t][0]] = (round(100.0 * (n - avgpos) / (n - 1), 2), disp, items[t][1]["val"])
        i = j + 1
    return out

SRC = {"leiden": ("CWTS Leiden 2025 · 高被引论文量 P(top10%)", 0.35),
       "ni":     ("Nature Index 2026 · 顶刊贡献 Share",        0.35),
       "hici":   ("Clarivate 高被引科学家 2025 · 人数",         0.30)}

loaders = {"leiden": load_leiden(), "ni": load_ni(), "hici": load_hici()}
pcts = {s: percentile(loaders[s]) for s in loaders}

# ---- 综合榜显示信息复用 ----
GLOBAL = {}   # 按 stage1 存储键
GALIAS = {}   # 按「扩展 norm_key(en)」重建, 与 grad 侧键口径一致
try:
    stage = json.load(open(BASE / "stage1.json", encoding="utf-8"))
    for row in stage["data"]:
        GLOBAL[row["key"]] = {"en": row["en"], "zh": row["zh"], "country": row["country"]}
        ek = nk(row["en"])                          # 用当前(含缩写扩展)的 norm_key 重建别名
        GALIAS.setdefault(ek, {"en": row["en"], "zh": row["zh"], "country": row["country"]})
except Exception as e:
    print("stage1 not loaded:", e)

# 主榜未覆盖 / 带校区名 / 科研院所等, 精确中文兜底 (键为 grad 侧 nk)
ZH_NAME = {
    "michigan university": "密歇根大学",
    "federal institute swiss technology zurich": "苏黎世联邦理工学院",
    "beijing china science technology university": "北京科技大学",
    "berkeley laboratory lawrence national": "劳伦斯伯克利国家实验室",
    "nanjing technology university": "南京工业大学",
    "academy agricultural chinese sciences": "中国农业科学院",
    "clinic mayo": "梅奥诊所",
    "association leibniz": "德国莱布尼茨学会",
    "jersey new rutgers state university": "罗格斯大学",
    "university yeungnam": "岭南大学（韩国）",
    "cancer center kettering memorial sloan": "纪念斯隆凯特琳癌症中心",
    "qingdao science technology university": "青岛科技大学",
    "riken": "日本理化学研究所",
    "normal northeast university": "东北师范大学",
    "technology texas university": "得克萨斯理工大学",
    "toledo university": "托莱多大学",
    "padova university": "帕多瓦大学",
}


ZH_ORG = {  # 重要科研院所/机构的通行中文译名兜底
    "chinese academy sciences": "中国科学院",
    "chinese academy sciences university": "中国科学院大学",
    "academy chinese sciences university": "中国科学院大学",
    "max planck society": "马普学会", "max planck": "马普学会",
    "french national centre science research": "法国国家科学研究中心(CNRS)",
    "helmholtz association german research centre": "亥姆霍兹联合会",
    "national institute health": "美国国立卫生研究院(NIH)",
    "russian academy science": "俄罗斯科学院",
    "academy scientific research bangladesh": "孟加拉国科学研究委员会",
    "academy china sciences": "中国科学院",
}
COUNTRY_EN2ZH = {"China": "中国内地", "United States of America (USA)": "美国",
    "United States": "美国", "Germany": "德国", "United Kingdom": "英国", "France": "法国",
    "Japan": "日本", "India": "印度", "Canada": "加拿大", "Australia": "澳大利亚",
    "Netherlands (Kingdom of the)": "荷兰", "Switzerland": "瑞士", "Italy": "意大利",
    "Spain": "西班牙", "South Korea": "韩国", "Brazil": "巴西", "Singapore": "新加坡",
    "Sweden": "瑞典", "Poland": "波兰", "Israel": "以色列", "Denmark": "丹麦",
    "Norway": "挪威", "Finland": "芬兰", "Austria": "奥地利", "Belgium": "比利时",
    "Russian Federation": "俄罗斯", "Iran": "伊朗", "Turkey": "土耳其", "Mexico": "墨西哥",
    "Saudi Arabia": "沙特阿拉伯", "Portugal": "葡萄牙", "Czech Republic": "捷克",
    "Argentina": "阿根廷", "Chile": "智利", "South Africa": "南非", "Egypt": "埃及",
    "Pakistan": "巴基斯坦", "Malaysia": "马来西亚", "Thailand": "泰国", "Ireland": "爱尔兰"}

allkeys = set(pcts["leiden"]) | set(pcts["ni"]) | set(pcts["hici"])
UNIV = {}
for k in allkeys:
    present = {s: pcts[s][k] for s in pcts if k in pcts[s]}
    if len(present) < 2:
        continue
    # 显示名/国家
    en = None
    for s in ("ni", "hici", "leiden"):   # 优先全称源
        if k in loaders[s]:
            e = loaders[s][k]["en"]
            if "(" not in e and en is None:
                en = e
            if "(" in e:
                en = e; break
    en = en or loaders[next(iter(present))][k]["en"]
    g = GLOBAL.get(k) or GALIAS.get(k)
    zh = g["zh"] if g else (ZH_NAME.get(k) or ZH_ORG.get(k) or en)
    country = g["country"] if g else None
    if not country:
        if k in loaders["hici"]:
            country = loaders["hici"][k]["country_zh"]
        elif k in loaders["ni"]:
            country = COUNTRY_EN2ZH.get(loaders["ni"][k]["country_en"], loaders["ni"][k]["country_en"])
    comp = sum(SRC[s][1] * present[s][0] for s in present) / sum(SRC[s][1] for s in present)
    pv = [present[s][0] for s in present]
    m = sum(pv) / len(pv)
    spread = round((sum((x - m) ** 2 for x in pv) / len(pv)) ** 0.5, 1)
    UNIV[k] = {"en": en, "zh": zh, "country": M.norm_country(country) if country else "",
               "comp": round(comp, 2), "appear": len(present), "spread": spread,
               "ranks": {s: ({"d": present[s][1], "pct": present[s][0], "sc": present[s][2]}
                             if s in present else None) for s in SRC}}

# 同名中文多 key 告警
zhg = {}
for k, v in UNIV.items(): zhg.setdefault(v["zh"], []).append(v["en"])
conf = {z: e for z, e in zhg.items() if len(e) > 1}
ordered = sorted(UNIV.items(), key=lambda kv: (-kv[1]["comp"], -kv[1]["appear"], kv[1]["en"]))

TOPN = 300
rows = []
for i, (k, v) in enumerate(ordered[:TOPN]):
    rows.append({"r": i + 1, "key": k, "en": v["en"], "zh": v["zh"], "country": v["country"],
                 "comp": v["comp"], "appear": v["appear"], "spread": v["spread"], "ranks": v["ranks"]})

print(f"三源并集(>=2): {len(UNIV)} 校 | 展示 Top {len(rows)}")
print(f"ZH-CONFLICT: {len(conf)}")
for z, e in list(conf.items())[:15]: print("  ", z, e)
print("TOP20:")
for x in rows[:20]:
    print(f"  #{x['r']:>3} {x['zh'][:18]:<18} {x['country']:<6} comp={x['comp']:6.2f} appear={x['appear']} "
          f"L={x['ranks']['leiden'] and x['ranks']['leiden']['d']} N={x['ranks']['ni'] and x['ranks']['ni']['d']} H={x['ranks']['hici'] and x['ranks']['hici']['d']}")
tail = [x for x in rows[-3:]]
print("TAIL3:", [(x["r"], x["zh"], x["comp"], x["appear"]) for x in tail])
import re as _re
still = [x for x in rows if not _re.search(r'[\u4e00-\u9fff]', x["zh"])]
print(f"中文名仍缺失(Top{len(rows)}): {len(still)}", [(x['r'], x['zh']) for x in still])


out = {"weights": {s: SRC[s][1] for s in SRC},
       "labels": {s: SRC[s][0] for s in SRC},
       "gate": 2, "topn": TOPN, "pool": len(UNIV), "rows": rows}
# 合并进 subject.json
sj = BASE / "subject.json"
subj = json.load(open(sj, encoding="utf-8")) if sj.exists() else {}
subj["grad"] = out
json.dump(subj, open(sj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已写入 subject.json[grad]")
