# -*- coding: utf-8 -*-
"""
第二轮 favicon 补全: 对仍缺图标的院校, 从 中/英文维基 infobox「网站」字段取域名, 严格校验后才上 favicon。
校验(避免 ce.cn 这类"域名存在但归属错误"):
  1) 归一到注册域(hhu.edu.cn 而非 hhuxxq.hhu.edu.cn); 黑名单媒体/门户/社交域名直接拒。
  2) 命中机构域名特征 -> 信任: *.edu.cn/*.ac.cn(中国院校), *.edu / *.edu.* / *.ac.* (国际)。
  3) 普通 TLD(欧洲等 uni-x.de/polito.it) -> 仅当能抓取首页且 <title> 与校名 token 重合才接受(本机可达的非.cn站)。
  4) 中国 .cn 站本机不可达, 只走规则2的 .edu.cn/.ac.cn, 不做首页校验(避免误判)。
favicon: 域名过校验后, 优先 DDG ip3(200) 否则直连 https://{domain}/favicon.ico(用户浏览器可达)。
"""
import json, re, subprocess, urllib.parse, time
from pathlib import Path
BASE = Path(__file__).parent
import matchlib as M
nk = M.norm_key

def gj(url, tries=2):
    for _ in range(tries):
        try:
            r = subprocess.run(["curl", "-sS", "-m", "12", "-A", "Mozilla/5.0 (fav2)", url], capture_output=True, text=True, timeout=15)
        except Exception:
            continue
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            try: return json.loads(r.stdout)
            except Exception: pass
    return None

def http_get(url, t=8):
    try:
        r = subprocess.run(["curl", "-sS", "-m", str(t), "-L", "-A", "Mozilla/5.0", url], capture_output=True, text=True, timeout=t + 3)
        return r.stdout
    except Exception:
        return ""

BAD = re.compile(r'(wikipedia|wikimedia|weibo|linkedin|facebook|twitter|x\.com|researchgate|youtube|baidu|baike|instagram|ce\.cn|people\.com|gov\.cn|github|bit\.ly|doodle|mywiki)', re.I)
# 机构域名特征
INST = re.compile(r'(\.edu\.cn$|\.ac\.cn$|\.edu$|\.edu\.[a-z]{2}$|\.ac\.[a-z]{2}$)', re.I)
MULTI = {"cn","uk","au","jp","kr","il","tw","hk","nz","br","in","tr","za","sg","my","pe","ar","mx","co"}
SLD = MULTI | {"edu","ac","co","com","net","org","go","gov","or","ne","re","ed"}

def registrable(host):
    host = re.sub(r'^https?://', '', host.strip()); host = re.sub(r'^www\.', '', host)
    host = host.split('/')[0].strip().rstrip('.').lower()
    parts = host.split(".")
    if len(parts) >= 3 and (parts[-2] in SLD or (parts[-1] in MULTI and parts[-2] in SLD)):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host

STOP = set("university universite universitat universidade the of and institute institut college school 大学 学院 大 省 市".split())
def name_tokens(en, zh):
    toks = set(re.findall(r"[a-z]{3,}", en.lower())) - STOP
    toks |= set(re.findall(r"[\u4e00-\u9fff]{2,}", zh or ""))
    return {t for t in toks if t}

def title_match(dom, toks):
    html = http_get("https://" + dom + "/", t=7)
    if not html: return False
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if not m: return False
    t = m.group(1).lower()
    th = set(re.findall(r"[a-z]{3,}", t)) | set(re.findall(r"[\u4e00-\u9fff]{2,}", t))
    hit = len(toks & th)
    return hit >= 1 and (hit >= 2 or any(len(x) >= 5 for x in (toks & th)))

def website_from(title, lang):
    d = gj(f"https://{lang}.wikipedia.org/w/api.php?action=parse&format=json&prop=wikitext&section=0&redirects=1&page=" + urllib.parse.quote(title))
    try: wt = d["parse"]["wikitext"]["*"]
    except Exception: return None
    m = re.search(r'\|\s*(?:website|homepage|url|网站|网址|官方网站|school_site)\s*=\s*([^\n|]+)', wt, re.I)
    if not m: return None
    s = m.group(1)
    mu = re.search(r'\{\{(?:URL|Plain link)\|\s*([^}|]+)', s, re.I) or re.search(r'https?://([^/\s}|]+)', s)
    return (mu.group(1) if mu else None)

def resolve_domain(en, zh):
    cands = ([(zh, "zh")] if zh else []) + [(en, "en")]
    for title, lang in cands:
        if not title: continue
        w = website_from(title, lang)
        if not w: continue
        dom = registrable(w)
        if not dom or BAD.search(dom): continue
        if INST.search(dom): return dom, "inst"
        # 普通TLD: 非.cn 才做首页标题校验
        if not dom.endswith(".cn"):
            if title_match(dom, name_tokens(en, zh)): return dom, "title"
    return None, None

def favicon_for(dom):
    ddg = "https://icons.duckduckgo.com/ip3/" + dom + ".ico"
    body = http_get(ddg, t=8)
    # DDG 有图标会返回真图(非404页); 用二次 HTTP code 判定
    code = subprocess.run(["curl", "-sS", "-m", "8", "-o", "/dev/null", "-w", "%{http_code}", ddg], capture_output=True, text=True, timeout=11).stdout
    if code == "200": return ddg
    return "https://" + dom + "/favicon.ico"

def main():
    stage = json.load(open(BASE / "stage1.json", encoding="utf-8"))
    subj = json.load(open(BASE / "subject.json", encoding="utf-8"))
    lm = json.load(open(BASE / "logo_map.json", encoding="utf-8"))
    fm = json.load(open(BASE / "favicon_map.json", encoding="utf-8")) if (BASE / "favicon_map.json").exists() else {}
    rows = stage["final"] + sum((subj[b]["rows"] for b in ["cs", "ai", "grad", "comm"]), [])
    seen = set(); todo = []
    for r in rows:
        k = nk(r["en"])
        if k in seen or k in lm or k in fm: continue
        seen.add(k); todo.append((k, r["en"], r.get("zh", "")))
    print(f"仍缺待校验补 favicon: {len(todo)}")
    t0 = time.time(); BUDGET = 900; added = 0; rejected = 0; noinst = 0
    for k, en, zh in todo:
        if time.time() - t0 > BUDGET:
            print("时间到,停止"); break
        dom, how = resolve_domain(en, zh)
        if not dom:
            noinst += 1; continue
        url = favicon_for(dom)
        fm[k] = url; added += 1
        json.dump(fm, open(BASE / "favicon_map.json", "w", encoding="utf-8"), ensure_ascii=False)
        if added % 12 == 0: print(f"  +{added}(拒{noinst}) 现{len(fm)} {int(time.time()-t0)}s 例:{zh or en}->{dom}/{how}")
    json.dump(fm, open(BASE / "favicon_map.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\n完成: 校验通过并新增{added}, 无合规域名{noinst}, favicon_map 总{len(fm)}")

if __name__ == "__main__":
    main()
