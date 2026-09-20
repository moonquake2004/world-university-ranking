# -*- coding: utf-8 -*-
"""共享: 院校名规范化匹配 + TSV加载 + 并列均位"""
import json, re, sys, unicodedata
from pathlib import Path

from pathlib import Path
BASE = Path(__file__).parent
DATA = BASE / "data"

WEIGHTS = {"the": 0.30, "usnews": 0.25, "arwu": 0.25, "qs": 0.20}
EDITIONS = {
    "qs":     {"name": "QS World University Rankings 2027",        "pub": "2026-06"},
    "the":    {"name": "THE World University Rankings 2026",       "pub": "2025-10"},
    "usnews": {"name": "U.S. News Best Global Universities 2026-27","pub": "2026-06"},
    "arwu":   {"name": "软科 ARWU 2026",                            "pub": "2026-08"},
}

STOP = {"the", "of", "at", "in", "and", "de", "la"}
TOKMAP = {"universite": "university", "universiteit": "university",
          "universitat": "university", "universidade": "university",
          "university": "university", "universidad": "university"}

# 归一化key -> 规范id (仅列归一化后仍无法自然合并的)
OVERRIDES = {
    "ucl": "university college london",
    "epfl": "epfl",
    "ecole polytechnique federale lausanne": "epfl",
    "federal institute technology lausanne swiss": "epfl",
    "psl paris research university": "psl university",
    "psl university": "psl university",
    "university psl": "psl university",
    "nanyang technological university singapore": "nanyang technological university",
    "university washington seattle": "university washington",
    "lmu munich": "lmu munich",
    "munich university": "lmu munich",
    "ludwig maximilians university munchen": "lmu munich",
    "heidelberg university": "heidelberg university",
    "ruprecht karls university heidelberg": "heidelberg university",
    "university heidelberg": "heidelberg university",
    "freie university berlin": "freie universitat berlin",
    "free university berlin": "freie universitat berlin",
    "pennsylvania state university university park": "pennsylvania state university",
    "pennsylvania state university park": "pennsylvania state university",
    "university illinois urbana champaign": "university illinois urbana champaign",
    "purdue university west lafayette": "purdue university",
    "purdue university lafayette west": "purdue university",
    "university minnesota twin cities": "university minnesota",
    "university minnesota cities twin": "university minnesota",
    "university ohio columbus state": "ohio state university",
    "university texas southwestern medical center": "university texas southwestern medical center",
    "adelaide university": "university adelaide",
    "new south wales university sydney": "university new south wales",
    "university south wales new": "university new south wales",
    "unsw sydney": "university new south wales",
    "university melbourne": "university melbourne",
    "sun yat sen university": "sun yat sen university",
    "karolinska institute": "karolinska institutet",
    "karolinska institutet": "karolinska institutet",
    "institute polytechnique paris": "institut polytechnique paris",
    "university science technology china": "university science technology china",
    "university science technology beijing china": "university science technology china",
    "china academy sciences university": "university chinese academy sciences",
    "university chinese academy sciences": "university chinese academy sciences",
    "paris sciences lettres psl research university paris": "psl university",
    # ---- 101-300 扩展后新增的跨榜别名合并 ----
    "universiti malaya": "malaya university",
    "kfupm": "fahd king minerals petroleum university",
    "advanced institute korea science technology": "kaist",
    "milan polytechnic university": "di milano politecnico",
    "center research university wageningen": "research university wageningen",
    "berlin technical university": "berlin technische university",
    "dresden tu": "dresden technische university",
    "dresden technical university": "dresden technische university",
    "dresden technology university": "dresden technische university",
    "autonomous barcelona university": "autonoma barcelona university",
    "erlangen nuremberg university": "alexander erlangen friedrich nurnberg university",
    "autonomous madrid university": "autonoma madrid university",
    "tuebingen university": "tubingen university",
    "darmstadt technical university": "darmstadt technische university",
    "porto university": "do porto university",
    "goettingen university": "gottingen university",
    "charles prague university": "charles university",
    "campus pittsburgh university": "pittsburgh university",
    "nijmegen radboud university": "radboud university",
    "university wuerzburg": "university wurzburg",
    "university muenster": "university munster",
    "duesseldorf heine heinrich university": "dusseldorf heine heinrich university",
    "tech virginia": "institute polytechnic state university virginia",
    "center dallas medical southwestern texas university": "center medical southwestern texas university",
    "penn state": "pennsylvania state university",
    "amherst massachusetts university": "massachusetts university",
    "icahn medicine mount sinai school": "icahn medicine school",
    # ---- 定向扫描后补充 ----
    "moscow state university": "lomonosov moscow state university",
    "ntnu norwegian science technology university": "norwegian science technology university",
    "brook suny stony university": "brook stony university",
    "uclouvain": "catholique louvain university",
    "bangalore indian institute science": "indian institute science",
}

def _sortkey_tokens(s):
    return " ".join(sorted(s.split()))

OVERRIDES = {_sortkey_tokens(k): _sortkey_tokens(v) for k, v in OVERRIDES.items()}

# ---- 学科榜新增缩写/变体别名 (CSRankings 常用缩写) ----
_extra = {
    "hkust": "hong kong science technology university",
    "ustc": "china science technology university",
    "tu munich": "munich technical university",
    "uestc": "china electronic science technology university",
    "hust": "huazhong science technology university",
    "tu darmstadt": "darmstadt technische university",
    "tu wien": "vienna technology university",
    "bupt": "beijing posts telecommunications university",
    "tu delft": "delft technology university",
    "mbzuai": "artificial bin intelligence mohamed university zayed",
    "academy chinese sciences": "academy chinese sciences university",
    "technion": "israel institute technology technion",
    "et lettres paris psl research sciences university": "psl university",
    "university maryland": "college maryland park university",
    "ludwig maximilian munich university": "lmu munich",
    "catholic chile pontifical university": "catolica chile pontificia university",
    "oslomet oslo metropolitan university": "oslo metropolitan university",
    "alabama tuscaloosa university": "university alabama",
    "norman oklahoma university": "oklahoma university",
    "carolina columbia south university": "carolina south university",
    "kebangsaan malaysia universiti": "malaysia national university",
    "malaysia teknologi universiti": "malaysia technology university",
    "polytechnic turin university": "di politecnico torino",
    "campinas estadual university": "campinas university",
    "campinas state university": "campinas university",
    "ii rome tor university vergata": "rome tor university vergata",
    "catholic heart sacred university": "cattolica cuore del sacro universita",
    "buffalo suny university": "buffalo university",
    "china medical southern university": "medical southern university",
    "brunswick jersey new rutgers state university": "brunswick new rutgers university",
    "polytechnic university valencia": "politecnica university valencia",
    "a china f northwest university": "a f northwest university",
    "china southwest university": "southwest university",
    "university washington": "university washington",
}
OVERRIDES.update({_sortkey_tokens(k): _sortkey_tokens(v) for k, v in _extra.items()})

def norm_key(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = s.replace("\u2019","").replace("'","")   # 去撇号: Hawai'i/St George's
    s = re.sub(r"\(.*?\)", " ", s)          # 去括号缩写
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    toks = [TOKMAP.get(t, t) for t in s.split()]
    toks = [t for t in toks if t not in STOP]
    key = " ".join(sorted(set(toks)))
    return OVERRIDES.get(key, key)

def load(fname):
    rows = []
    for line in (DATA / fname).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        p = line.split("\t")
        try:
            rank = int(p[0])
        except ValueError:
            rank = p[0].strip()  # 区间名次字符串, 如 "201-250"
        try:
            sc = float(p[4]) if len(p) > 4 and p[4] else None
        except ValueError:
            sc = None  # 区间分数串(如"54.3-56.3")不作数值处理
        rows.append({"rank": rank, "en": p[1], "zh": p[2],
                     "country": p[3], "score": sc})
    return rows

def load_full(short):
    f1 = f"raw_{short}.tsv"
    f2 = f"raw_{short}_101_300.tsv"
    rows = load(f1)
    if (DATA / f2).exists():
        rows += load(f2)
    return rows

def tie_positions(rows):
    """按连续相同display rank分组, pos_avg = 所占用行位置(1-based)的均值"""
    n = len(rows)
    out, i = [], 0
    while i < n:
        j = i
        while j + 1 < n and rows[j + 1]["rank"] == rows[i]["rank"]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            out.append(avg)
        i = j + 1
    return out, n



def norm_country(c):
    c = c.strip()
    fix = {"中国": "中国内地", "中国香港特别行政区": "中国香港", "中国澳门特别行政区": "中国澳门",
           "沙特": "沙特阿拉伯"}
    return fix.get(c, c)
