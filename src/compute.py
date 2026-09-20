# -*- coding: utf-8 -*-
"""
世界大学综合排名计算 (QW Academic Assessment Bureau composite method)
方法论:
1. 统一口径: 四榜并列名次 -> 均位法(occupied-slot average)
2. 榜内百分位分: score_k = 100 * (N - pos_avg) / (N - 1)   (第1名=100, 末位=0)
3. 未进该榜Top100: 该维度记0分 (结构性短板计入, 不做权重稀释)
4. 公信力加权: THE 0.30 / US News 0.25 / ARWU 0.25 / QS 0.20
5. 综合分 = Σ w_k * score_k; 并列时按 四榜覆盖数 > THE均位 > US News均位 > 字母序 断位
"""
import json, re, sys, unicodedata
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

from matchlib import norm_key, load, tie_positions

def load_full(short):
    rows = load(f"raw_{short}.tsv")
    for suffix in ("101_300", "301_500"):
        f2 = f"raw_{short}_{suffix}.tsv"
        if (DATA / f2).exists():
            rows += load(f2)
    return rows

UNIV = {}   # key -> record
per_list_report = {}

for sysname in ["qs", "the", "usnews", "arwu"]:
    rows = load_full(sysname)
    positions, n = tie_positions(rows)
    per_list_report[sysname] = n
    for idx, r in enumerate(rows):
        key = norm_key(r["en"])
        pct = 100.0 * (n - positions[idx]) / (n - 1)
        rec = UNIV.setdefault(key, {"en": r["en"], "zh": r["zh"], "country": r["country"], "ranks": {}})
        # 显示名: 英文名优先无括号的规范名; 中文名优先THE, 否则更长者
        if "(" in rec["en"] and "(" not in r["en"]:
            rec["en"] = r["en"]
        if sysname == "the" or len(r["zh"]) > len(rec["zh"]):
            rec["zh"] = r["zh"] if (sysname == "the" or len(r["zh"]) >= len(rec["zh"])) else rec["zh"]
        rec["ranks"][sysname] = {"display": r["rank"], "pos": positions[idx], "pct": round(pct, 2), "raw_score": r["score"]}

# 检查匹配质量: 中文名冲突检测
zh_group = {}
for k, v in UNIV.items():
    zh_group.setdefault(v["zh"], []).append((k, v["en"]))
print("=== 同名(中文)多key告警 ===")
for zh, lst in zh_group.items():
    if len(lst) > 1:
        print("  ", zh, lst)
print("总院校数(四榜并集):", len(UNIV), "| 各榜行数:", per_list_report)

# 综合分
ABSENT_PENALTY_NOTE = "未进该榜Top100记0分"
for k, v in UNIV.items():
    comp = 0.0
    pcts = []
    for sname, w in WEIGHTS.items():
        p = v["ranks"].get(sname, {}).get("pct", 0.0)
        pcts.append(p)
        comp += w * p
    v["composite"] = round(comp, 2)
    v["appear"] = sum(1 for s in WEIGHTS if s in v["ranks"])
    m = sum(pcts) / 4.0
    v["spread"] = round((sum((p - m) ** 2 for p in pcts) / 4.0) ** 0.5, 1)  # 四榜百分位标准差, 越低越一致

def sortkey(item):
    k, v = item
    return (-v["composite"], -v["appear"],
            v["ranks"].get("the", {}).get("pos", 999),
            v["ranks"].get("usnews", {}).get("pos", 999),
            v["en"])

ordered = sorted(UNIV.items(), key=sortkey)
# 共识门槛: 综合榜须至少进入2个榜单Top300; 单榜院校进入"专科型参考名单"
GATE = 2
TOPN = 500
eligible = [(k, v) for k, v in ordered if v["appear"] >= GATE]
single = [(k, v) for k, v in ordered if v["appear"] < GATE]
top100 = eligible[:TOPN]
print("\n=== 单榜院校(不占综合席位, 共%d所, 显示前20) ===" % len(single))
for k, v in single[:20]:
    s = v["ranks"]
    which = [x for x in ["qs","the","usnews","arwu"] if x in s][0]
    print(f"  {v['composite']:.2f}  {v['en']} ({which}:{s[which]['display']})")
print("\n=== 门槛后第%d-%d (未入选) ===" % (TOPN+1, TOPN+8))
for k, v in eligible[TOPN:TOPN+8]:
    print(f"  {v['composite']:.2f}  {v['en']}  appear={v['appear']}")
cut = ordered[99]
just_outside = ordered[100:110]
print("\n=== 第100名(分数线) ===")
print("  100:", cut[1]["en"], cut[1]["composite"])
print("\n=== 第101-110 (未入选) ===")
for k, v in just_outside:
    print(f"  {v['composite']:.2f}  {v['en']}  appear={v['appear']}")

print("\n=== 综合Top100中单榜入围(结构警示) ===")
for k, v in top100:
    if v["appear"] <= 1:
        print("  ", v["en"], v["composite"])
print("\n=== 入围3+榜单但跌出综合Top100 (应为空或极少) ===")
rest = ordered[100:]
for k, v in rest:
    if v["appear"] >= 3:
        print("  ", v["en"], v["composite"], v["appear"])

out = {"weights": WEIGHTS, "editions": EDITIONS, "n_union": len(UNIV),
       "gate": GATE, "list_sizes": per_list_report,
       "n_single": len(single), "n_eligible": len(eligible), "topn": TOPN}

# 规范化显示名 (en, zh)
CURATED_RAW = {
    "University College London (UCL)": "伦敦大学学院",
    "Massachusetts Institute of Technology (MIT)": "麻省理工学院",
    "California Institute of Technology (Caltech)": "加州理工学院",
    "Heidelberg University": "海德堡大学",
    "Nanyang Technological University (NTU)": "南洋理工大学",
    "LMU Munich": "慕尼黑大学",
    "Technical University of Munich (TUM)": "慕尼黑工业大学",
    "University of Washington (Seattle)": "华盛顿大学（西雅图）",
    "Washington University in St. Louis": "圣路易斯华盛顿大学",
    "UNSW Sydney": "新南威尔士大学",
    "EPFL (École polytechnique fédérale de Lausanne)": "洛桑联邦理工学院",
    "PSL University": "巴黎文理研究大学",
    "Université Paris-Saclay": "巴黎-萨克雷大学",
    "Karolinska Institutet": "卡罗林斯卡学院",
    "KU Leuven": "荷语鲁汶大学",
    "University of Illinois Urbana-Champaign (UIUC)": "伊利诺伊大学厄巴纳-香槟分校",
    "Purdue University (West Lafayette)": "普渡大学西拉法叶分校",
    "University of Minnesota (Twin Cities)": "明尼苏达大学双城分校",
    "Penn State University (PennState)": "宾夕法尼亚州立大学",
    "Adelaide University": "阿德莱德大学",
    "National Taiwan University": "国立台湾大学",
    "Université Paris Cité": "巴黎西岱大学",
    "University of California, San Francisco (UCSF)": "加州大学旧金山分校",
    "Huazhong University of Science and Technology": "华中科技大学",
    "Sun Yat-sen University": "中山大学",
    "University of Maryland (College Park)": "马里兰大学帕克分校",
    "University of Michigan (Ann Arbor)": "密歇根大学安娜堡分校",
    "London School of Economics and Political Science (LSE)": "伦敦政治经济学院",
    "University of Tsinghua placeholder": "x",
}
CURATED = {}
for en, zh in CURATED_RAW.items():
    if "placeholder" in en:
        continue
    if " (" in en:
        en_disp = en.split(" (")[0]
    else:
        en_disp = en
    CURATED[norm_key(en)] = (en, zh)
for k, v in UNIV.items():
    if k in CURATED:
        v["en"], v["zh"] = CURATED[k]
# 括号会被norm_key剥离, 需显式指定簇键
CURATED_MANUAL = {
    "ann arbor michigan university": ("University of Michigan (Ann Arbor)", "密歇根大学安娜堡分校"),
    "college maryland park university": ("University of Maryland (College Park)", "马里兰大学帕克分校"),
    "chinese university hong kong": None,  # 占位不生效
}
for k, v in UNIV.items():
    if k in CURATED_MANUAL and CURATED_MANUAL[k]:
        v["en"], v["zh"] = CURATED_MANUAL[k]

for i, (k, v) in enumerate(top100):
    print(f"{i+1}\t{v['composite']}\t{v['zh']}\t{v['en']}\t{v['country']}\tappear={v['appear']}\t"
          + "\t".join(f"{s}:{v['ranks'].get(s,{}).get('display','-')}" for s in ["qs","the","usnews","arwu"]))

# 存中间结果 + 输出看板用最终结构
FINAL = []
for i, (k, v) in enumerate(eligible[:TOPN]):
    FINAL.append({"r": i + 1, "en": v["en"], "zh": v["zh"], "country": v["country"],
                  "comp": v["composite"], "appear": v["appear"], "spread": v["spread"],
                  "ranks": {s: ({"d": v["ranks"][s]["display"], "pct": v["ranks"][s]["pct"],
                                 "sc": v["ranks"][s]["raw_score"]} if s in v["ranks"] else None)
                            for s in ["qs", "the", "usnews", "arwu"]}})
SPECIAL = [{"en": v["en"], "zh": v["zh"], "country": v["country"], "comp": v["composite"],
            "list": ([x for x in ["qs", "the", "usnews", "arwu"] if x in v["ranks"]][0]),
            "d": v["ranks"][[x for x in ["qs", "the", "usnews", "arwu"] if x in v["ranks"]][0]]["display"]}
           for k, v in single[:15]]
with open(BASE / "stage1.json", "w", encoding="utf-8") as f:
    json.dump({"meta": out, "final": FINAL, "special": SPECIAL,
               "data": [{"key": k, **v} for k, v in ordered]}, f, ensure_ascii=False, indent=1)
print("\nstage1.json written; total candidates:", len(ordered))
