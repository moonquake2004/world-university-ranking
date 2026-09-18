# -*- coding: utf-8 -*-
"""
CS / AI 学科综合榜计算
方法论与综合榜同源: 并列均位 -> 榜内百分位 -> 公信力加权 -> 共识门槛(>=2源)
统一取每个来源的前100行作为可比池(池深一致, 百分位才跨源可比)
权重:
  CS : CSRankings 25% | THE-CS 20% | U.S. News-CS 20% | ARWU-CS 20% | QS-CS 15%
  AI : CSRankings-AI 40% | U.S. News-AI 35% | ARWU-AI 25%
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from matchlib import norm_key, load, load_full, tie_positions, norm_country

BASE = Path(__file__).parent
TOPN = 100

SOURCES = {
    "cs": {
        "csr":    ("raw_csr_all.tsv",  0.25, "CSRankings 2026"),
        "the":    ("raw_the_cs.tsv",   0.20, "THE-CS 2026"),
        "usnews": ("raw_usnews_cs.tsv",0.20, "U.S. News-CS 26-27"),
        "arwu":   ("raw_arwu_cs.tsv",  0.20, "软科CS&E 2026"),
        "qs":     ("raw_qs_cs.tsv",    0.15, "QS-CS 2026"),
    },
    "ai": {
        "csr":    ("raw_csr_ai.tsv",   0.40, "CSRankings-AI 2026"),
        "usnews": ("raw_usnews_ai.tsv",0.35, "U.S. News-AI 26-27"),
        "arwu":   ("raw_arwu_ai.tsv",  0.25, "软科-AI 2026"),
    },
}

# 综合榜已有院校 -> 复用显示名与国家, 保证两榜一致
stage = json.load(open(BASE / "stage1.json", encoding="utf-8"))
GLOBAL = {}
for row in stage["data"]:
    GLOBAL[row["key"]] = {"en": row["en"], "zh": row["zh"], "country": row["country"]}

def build_subject(subject):
    UNIV = {}
    for sname, (fname, w, label) in SOURCES[subject].items():
        rows = load(fname)[:100]  # 统一池深100行
        positions, n = tie_positions(rows)
        assert n == len(rows)
        for idx, r in enumerate(rows):
            key = norm_key(r["en"])
            pct = 100.0 * (n - positions[idx]) / (n - 1)
            rec = UNIV.setdefault(key, {"en": r["en"], "zh": norm_country and r["zh"],
                                        "country": norm_country(r["country"]), "ranks": {}})
            if "(" in rec["en"] and "(" not in r["en"]:
                rec["en"] = r["en"]
            rec["ranks"][sname] = {"display": r["rank"], "pos": positions[idx],
                                   "pct": round(pct, 2), "raw_score": r["score"]}
    # 与综合榜对齐显示名
    for k, v in UNIV.items():
        if k in GLOBAL:
            g = GLOBAL[k]
            v["en"], v["zh"], v["country"] = g["en"], g["zh"], g["country"]
    # 综合分
    weights = {s: SOURCES[subject][s][1] for s in SOURCES[subject]}
    for k, v in UNIV.items():
        pcts = []
        comp = 0.0
        for sname, w in weights.items():
            p = v["ranks"].get(sname, {}).get("pct", 0.0)
            pcts.append(p)
            comp += w * p
        v["composite"] = round(comp, 2)
        v["appear"] = sum(1 for s in weights if s in v["ranks"])
        m = sum(pcts) / len(pcts)
        v["spread"] = round((sum((p - m) ** 2 for p in pcts) / len(pcts)) ** 0.5, 1)
    def sortkey(item):
        k, v = item
        first = list(weights)[0]
        return (-v["composite"], -v["appear"], v["ranks"].get(first, {}).get("pos", 999), v["en"])
    ordered = sorted(UNIV.items(), key=sortkey)
    eligible = [(k, v) for k, v in ordered if v["appear"] >= 2]
    single = [(k, v) for k, v in ordered if v["appear"] < 2]
    # 中文同名多key告警
    zhg = {}
    for k, v in UNIV.items():
        zhg.setdefault(v["zh"], []).append(v["en"])
    print(f"\n===== {subject.upper()} 池: {len(UNIV)} 校 | 多源: {len(eligible)} | 单源: {len(single)} =====")
    for zh, lst in zhg.items():
        if len(lst) > 1:
            print("  ZH-CONFLICT:", zh, lst)
    out = []
    for i, (k, v) in enumerate(eligible[:TOPN]):
        out.append({"r": i + 1, "en": v["en"], "zh": v["zh"], "country": v["country"],
                    "comp": v["composite"], "appear": v["appear"], "spread": v["spread"],
                    "ranks": {s: ({"d": v["ranks"][s]["display"], "pct": v["ranks"][s]["pct"],
                                   "sc": v["ranks"][s]["raw_score"]} if s in v["ranks"] else None)
                              for s in weights}})
    print("  TOP15:")
    for x in out[:15]:
        ds = {s: (x["ranks"][s]["d"] if x["ranks"][s] else "-") for s in weights}
        print("   ", x["r"], x["zh"], x["comp"], ds)
    print("  尾部3:", [(x["r"], x["zh"], x["comp"]) for x in out[-3:]])
    print("  未入选(单源Top10):", [(v["en"], v["composite"]) for k, v in single[:10]])
    print("  门槛后落选:", [(v["en"], v["composite"], v["appear"]) for k, v in eligible[TOPN:TOPN+5]])
    return {"weights": weights, "labels": {s: SOURCES[subject][s][2] for s in weights}, "rows": out}

result = {"cs": build_subject("cs"), "ai": build_subject("ai")}
with open(BASE / "subject.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("\nsubject.json written")
