# -*- coding: utf-8 -*-
"""
为综合榜展示的 Top500 (stage1.final) 抓取官方校徽 -> logo_map.json {stage1_key: wikimedia_thumbURL}
三级:
  pass1 批量 pageimages(original) —— 快, 覆盖约一半
  pass2 逐校解析 infobox  wikitext 的 |logo/|image 字段 -> imageinfo thumburl —— 救回名校
  pass3 残余缺失: list=search 定位规范条目 -> 再走 infobox
热链 upload.wikimedia.org, 缺失留空。curl 短超时+重试, pass2/3 并发。
"""
import json, re, subprocess, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
BASE = Path(__file__).parent

def gj(url, tries=2):
    for _ in range(tries):
        r = subprocess.run(["curl", "-sS", "-m", "10", "-A", "Mozilla/5.0 (logo)", url],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            try:
                return json.loads(r.stdout)
            except Exception:
                pass
    return None

def strip_paren(s): return re.sub(r"\s*\(.*?\)\s*", " ", s).strip()

def candidates(en):
    b = strip_paren(en); c = [b]
    c.append(b[4:] if b.lower().startswith("the ") else "The " + b)
    if b.lower().startswith("university of "):
        c.append(b[len("university of "):] + " University")
    elif b.lower().endswith(" university"):
        c.append("University of " + b[:-len(" university")])
    return list(dict.fromkeys(x for x in c if x))

# ---- pass1: 批量 pageimages original ----
def batch_pageimages(titles):
    orig, redir = {}, {}
    for i in range(0, len(titles), 50):
        u = ("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages"
             "&piprop=original&redirects=1&titles=" + urllib.parse.quote("|".join(titles[i:i+50])))
        d = gj(u)
        if not d: continue
        q = d.get("query", {})
        for p in q.get("pages", {}).values():
            s = (p.get("original") or {}).get("source")
            if s and p.get("title"): orig[p["title"].lower()] = s
        for rd in q.get("redirects", []) + q.get("normalized", []):
            redir[rd["from"].lower()] = rd["to"].lower()
    return orig, redir

LOGO_RE = re.compile(r"\|\s*(?:logo|image|shield|coat_of_arms|crest)\s*=\s*([^\n|]+)", re.I)
def url_of_file(f):
    f = f.strip().removeprefix("File:").removeprefix("Image:")
    if not re.search(r"\.(png|jpe?g|svg|gif)$", f, re.I): return None
    d = gj("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url&iiurlwidth=64&titles=" + urllib.parse.quote("File:" + f))
    try: return list(d["query"]["pages"].values())[0]["imageinfo"][0].get("thumburl")
    except Exception: return None

def infobox_logo(title):
    d = gj("https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=wikitext&section=0&redirects=1&page=" + urllib.parse.quote(title))
    try: wt = d["parse"]["wikitext"]["*"]
    except Exception: return None
    for m in LOGO_RE.finditer(wt):
        f = m.group(1).strip()
        f = re.sub(r"^\[\[\s*", "", f)          # 去 [[File: 前缀
        f = f.split("|")[0].split("]]")[0]        # 去 |150px]] 尺寸/标题
        f = re.sub(r"\{\{.*$", "", f).strip()     # 去 {{!}}class=... 后缀
        if f and "{{" not in f:
            u = url_of_file(f)
            if u: return u
    return None

def search_title(name):
    d = gj("https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srlimit=1&srsearch=" + urllib.parse.quote(name))
    try: return d["query"]["search"][0]["title"]
    except Exception: return None

def resolve_infobox(en):
    for c in candidates(en):
        u = infobox_logo(c)
        if u: return u
    t = search_title(en)
    if t:
        u = infobox_logo(t)
        if u: return u
    return None

def main():
    d = json.load(open(BASE / "stage1.json", encoding="utf-8"))
    key2 = {r["en"]: r["key"] for r in d["data"]}
    targets = []  # (key, en, zh) 仅展示的 final 500
    for r in d["final"]:
        k = key2.get(r["en"])
        if k: targets.append((k, r["en"], r["zh"]))
    # 累加: 载入已有结果, 只补未命中的
    try:
        logo_map = json.load(open(BASE / "logo_map.json", encoding="utf-8"))
    except Exception:
        logo_map = {}
    logo_map = {k: v for k, v in logo_map.items() if k in {t[0] for t in targets}}  # 只保留 final 键
    todo = [t for t in targets if t[0] not in logo_map]
    print(f"目标(展示 Top500): {len(targets)} 校 | 已有 {len(logo_map)} | 本轮待补 {len(todo)}")
    cand_of = {k: candidates(en) for k, en, zh in todo}
    allc = sorted({c for cs in cand_of.values() for c in cs})
    if allc:
        print(f"pass1 批量 pageimages ({len(allc)} 候选)…")
        orig, redir = batch_pageimages(allc)
        still1 = []
        for k, en, zh in todo:
            hit = None
            for c in cand_of[k]:
                canon = redir.get(c.lower(), c.lower())
                hit = orig.get(canon) or orig.get(c.lower())
                if hit: break
            if hit: logo_map[k] = hit
            else: still1.append((k, en, zh))
        print(f"pass1 命中 {len(todo)-len(still1)}, 缺失 {len(still1)} -> pass2/3 infobox 回退…")
        with ThreadPoolExecutor(max_workers=3) as ex:
            fut = {ex.submit(resolve_infobox, en): (k, en, zh) for k, en, zh in still1}
            still = []
            for f in as_completed(fut):
                k, en, zh = fut[f]
                try: u = f.result()
                except Exception: u = None
                if u: logo_map[k] = u
                else: still.append((k, zh, en))
    else:
        still = []
    json.dump(logo_map, open(BASE / "logo_map.json", "w", encoding="utf-8"), ensure_ascii=False)
    n = len(targets)
    print(f"\n最终命中 {len(logo_map)}/{n} ({len(logo_map)*100//n}%), 仍缺 {len(still)}")
    for k, zh, en in still[:50]:
        print("   缺:", zh, "|", en)

if __name__ == "__main__":
    main()
