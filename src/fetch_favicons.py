# -*- coding: utf-8 -*-
"""
为仍缺官方校徽的院校补 favicon 回退 -> favicon_map.json {norm_key(en): url}
域名来源: 维基条目 -> Wikidata P856(官方网址); 无则解析 infobox |website/{{URL|...}}
favicon: 优先 DuckDuckGo ip3(本机可验证200); 否则直连 https://{domain}/favicon.ico
        (本机访问不了的 .cn 站, 用户浏览器在国内可达, 破损由前端 onerror 隐藏)
串行低并发 + 每命中即落盘 + 时长上限。
"""
import json, re, subprocess, urllib.parse, time
from pathlib import Path
BASE = Path(__file__).parent
import matchlib as M
nk = M.norm_key

def gj(url, tries=2):
    for _ in range(tries):
        try:
            r = subprocess.run(["curl", "-sS", "-m", "12", "-A", "Mozilla/5.0 (fav)", url],
                               capture_output=True, text=True, timeout=15)
        except Exception:
            continue
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            try: return json.loads(r.stdout)
            except Exception: pass
    return None

def http_ok(url):
    try:
        r = subprocess.run(["curl", "-sS", "-m", "10", "-o", "/dev/null", "-w", "%{http_code} %{content_type}",
                            "-L", url], capture_output=True, text=True, timeout=13)
        code, ct = (r.stdout.split() + ["", ""])[:2]
        return code == "200" and ("image" in ct or "icon" in ct or "octet" in ct)
    except Exception:
        return False

def canon_title(en):
    d = gj("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops&ppprop=wikibase_item&redirects=1&titles=" + urllib.parse.quote(en))
    try:
        p = list(d["query"]["pages"].values())[0]
        return p.get("title"), p.get("pageprops", {}).get("wikibase_item")
    except Exception:
        return None, None

def p856(qid):
    if not qid: return None
    d = gj("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims&ids=" + qid)
    try:
        cl = d["entities"][qid]["claims"].get("P856", [])
        best = None
        for c in cl:
            v = c["mainsnak"]["datavalue"]["value"]; 
            if c.get("rank") == "preferred": return v
            if best is None: best = v
        return best
    except Exception:
        return None

WS = re.compile(r"\|\s*website\s*=\s*([^\n|]+)", re.I)
def website_from_wikitext(title):
    d = gj("https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=wikitext&section=0&redirects=1&page=" + urllib.parse.quote(title))
    try: wt = d["parse"]["wikitext"]["*"]
    except Exception: return None
    m = WS.search(wt)
    if not m: return None
    s = m.group(1)
    mu = re.search(r"\{\{URL\|\s*([^}|]+)", s, re.I) or re.search(r"https?://([^/\s}|]+)", s)
    return (mu.group(1) if mu else None)

def norm_dom(u):
    u = re.sub(r"^\s*\[?\[?", "", u.strip())
    u = re.sub(r"^https?://", "", u); u = re.sub(r"^www\.", "", u)
    u = u.split("/")[0].split("|")[0].strip().rstrip(".")
    return u if "." in u and " " not in u else None

def favicon_for(en):
    title, qid = canon_title(en)
    dom = None
    url = p856(qid)
    if url: dom = norm_dom(url)
    if not dom and title:
        w = website_from_wikitext(title)
        if w: dom = norm_dom(w)
    if not dom: return None
    ddg = "https://icons.duckduckgo.com/ip3/" + dom + ".ico"
    if http_ok(ddg):
        return ddg
    return "https://" + dom + "/favicon.ico"   # 本机可能不可达, 但用户浏览器可达; 破损 onerror 隐藏

def main():
    stage = json.load(open(BASE / "stage1.json", encoding="utf-8"))
    subj = json.load(open(BASE / "subject.json", encoding="utf-8"))
    lm = json.load(open(BASE / "logo_map.json", encoding="utf-8")) if (BASE / "logo_map.json").exists() else {}
    fm = json.load(open(BASE / "favicon_map.json", encoding="utf-8")) if (BASE / "favicon_map.json").exists() else {}
    rows = stage["final"] + sum((subj[b]["rows"] for b in ["cs", "ai", "grad", "comm"]), [])
    seen = set(); todo = []
    for r in rows:
        k = nk(r["en"])
        if k in seen or k in lm or k in fm: continue
        seen.add(k); todo.append((k, r["en"]))
    print(f"缺校徽待补 favicon: {len(todo)}")
    t0 = time.time(); BUDGET = 900; added = 0; fail = 0
    for k, en in todo:
        if time.time() - t0 > BUDGET:
            print("时间到,停止"); break
        try: u = favicon_for(en)
        except Exception: u = None
        if u:
            fm[k] = u; added += 1
            json.dump(fm, open(BASE / "favicon_map.json", "w", encoding="utf-8"), ensure_ascii=False)
            if added % 15 == 0: print(f"  +{added} 现{len(fm)} 用时{int(time.time()-t0)}s")
        else:
            fail += 1
    json.dump(fm, open(BASE / "favicon_map.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\n完成: favicon 新增{added}, 失败/无域名{fail}, favicon_map 总{len(fm)}")

if __name__ == "__main__":
    main()
