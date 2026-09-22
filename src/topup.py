# -*- coding: utf-8 -*-
import json,re,subprocess,urllib.parse,time,importlib.util
spec=importlib.util.spec_from_file_location("fl","fetch_logos.py"); fl=importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
fl.gj.__defaults__=(2,)
def gj(url,tries=2):
    for _ in range(tries):
        try:
            r=subprocess.run(["curl","-sS","-m","12","-A","Mozilla/5.0 (logo)",url],capture_output=True,text=True,timeout=16)
        except Exception: continue
        if r.returncode==0 and r.stdout.strip().startswith("{"):
            try:return json.loads(r.stdout)
            except:pass
    return None
fl.gj=gj
d=json.load(open('stage1.json')); lm=json.load(open('logo_map.json'))
key2={r['en']:r['key'] for r in d['data']}
final=[(r['r'],r['en'],r['zh'],key2.get(r['en'])) for r in d['final']]
final.sort()
t0=time.time(); BUDGET=200; added=0
for rank,en,zh,k in final:
    if not k or k in lm: continue
    if time.time()-t0>BUDGET: print("时间到,停止"); break
    try: u=fl.resolve_infobox(en)
    except Exception: u=None
    if u:
        lm[k]=u; added+=1
        json.dump(lm,open('logo_map.json','w'),ensure_ascii=False)  # 每条落盘
        if added%10==0: print(f"  +{added} 现{len(lm)} (rank~{rank})")
print(f"完成: 新增{added}, 总{len(lm)}/500 = {len(lm)*100//500}%")
