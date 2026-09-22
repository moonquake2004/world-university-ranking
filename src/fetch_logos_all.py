# -*- coding: utf-8 -*-
"""
把 logo 扩到全部榜单(主榜 final + cs/ai/comm/grad 子榜)。
汇总各榜展示行的 norm_key(en), 复用现有 logo_map.json, 只补未覆盖的院校。
低并发(抗 Wikimedia 限流) + 每命中即落盘 + 按优先级(main>cs>ai>grad>comm 尾部) + 时长上限。
"""
import json, re, subprocess, urllib.parse, time, importlib.util
from pathlib import Path
BASE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("fl", BASE / "fetch_logos.py")
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)

def gj(url, tries=2):
    for _ in range(tries):
        try:
            r = subprocess.run(["curl", "-sS", "-m", "10", "-A", "Mozilla/5.0 (logo)", url],
                               capture_output=True, text=True, timeout=14)
        except Exception:
            continue
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            try: return json.loads(r.stdout)
            except Exception: pass
    return None
fl.gj = gj

import matchlib as M
nk = M.norm_key

def collect():
    stage = json.load(open(BASE / "stage1.json", encoding="utf-8"))
    subj = json.load(open(BASE / "subject.json", encoding="utf-8"))
    # (key, en) 去重, 按优先级: main, cs, ai, grad, comm
    order = []
    seen = set()
    def add(rows):
        for r in rows:
            k = nk(r["en"])
            if k and k not in seen:
                seen.add(k); order.append((k, r["en"]))
    add(stage["final"])
    for b in ("cs", "ai", "grad", "comm"):
        add(subj[b]["rows"])
    return order

def main():
    order = collect()
    lm = {}
    p = BASE / "logo_map.json"
    if p.exists():
        lm = json.load(open(p, encoding="utf-8"))
    todo = [(k, en) for k, en in order if k not in lm]
    print(f"全榜 distinct 院校 {len(order)}, 已覆盖 {len(order)-len(todo)}, 待补 {len(todo)}")
    t0 = time.time(); BUDGET = 420; added = 0
    for k, en in todo:
        if time.time() - t0 > BUDGET:
            print("时间到, 停止"); break
        u = None
        # 先试 pageimages original(单次), 再 infobox
        try:
            orig, redir = fl.batch_pageimages(fl.candidates(en))
            for c in fl.candidates(en):
                u = orig.get(redir.get(c.lower(), c.lower())) or orig.get(c.lower())
                if u: break
            if not u:
                u = fl.resolve_infobox(en)
        except Exception:
            u = None
        if u:
            lm[k] = u; added += 1
            json.dump(lm, open(p, "w", encoding="utf-8"), ensure_ascii=False)
            if added % 15 == 0:
                print(f"  +{added} 现{len(lm)} 用时{int(time.time()-t0)}s")
    json.dump(lm, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\n完成: 新增{added}, logo_map 总{len(lm)} 条")

if __name__ == "__main__":
    main()
