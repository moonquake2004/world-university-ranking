# -*- coding: utf-8 -*-
"""组装世界大学综合排名看板 HTML (单文件, 数据内联, ECharts CDN)"""
import json
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE.parent  # 仓库根目录, 输出 index.html
OUT.mkdir(parents=True, exist_ok=True)

d = json.load(open(BASE / "stage1.json", encoding="utf-8"))
# 扁平化: ranks 嵌套合并到行对象顶层 (qs/the/usnews/arwu)
final = []
for row in d["final"]:
    flat = {k: v for k, v in row.items() if k != "ranks"}
    for k, v in row["ranks"].items():
        flat[k] = v
    final.append(flat)
payload = {
    "meta": d["meta"],
    "final": final,
    "special": d["special"],
}
DATA_JS = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
SUBJECT_JS = json.dumps(json.load(open(BASE / "subject.json", encoding="utf-8")),
                        ensure_ascii=False, separators=(",", ":"))

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>世界大学综合排名前300 · 2026 | Global University Composite Ranking</title>
<style>
:root{
  --bg:#070b14; --panel:#0d1524; --panel2:#101b2f; --line:#1d2c47;
  --txt:#e9effb; --sub:#93a7c7; --faint:#5c7099;
  --gold:#ffd166; --qs:#20c997; --the:#ff6b81; --us:#5b8def; --arw:#f4a259;
  --accent:#7aa5ff;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:radial-gradient(1200px 600px at 70% -10%, #14264a 0%, transparent 60%),
     radial-gradient(900px 500px at 0% 0%, #10203d 0%, transparent 55%), var(--bg);
  color:var(--txt); font-family:"PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,"Noto Sans SC",sans-serif;
  min-height:100vh; padding:28px clamp(14px,3vw,44px) 60px;}
.wrap{max-width:1440px;margin:0 auto}
header{display:flex;flex-wrap:wrap;gap:18px;justify-content:space-between;align-items:flex-end;margin-bottom:8px}
h1{font-size:clamp(22px,3vw,34px);letter-spacing:1px}
h1 .en{display:block;font-size:13px;color:var(--sub);font-weight:400;letter-spacing:2px;margin-top:6px;text-transform:uppercase}
.editions{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end;max-width:640px}
.badge{border:1px solid var(--line);background:rgba(20,32,56,.6);border-radius:20px;padding:5px 12px;font-size:12px;color:var(--sub)}
.badge b{color:var(--txt);font-weight:600}
.sub-line{color:var(--faint);font-size:12.5px;margin:6px 0 22px;line-height:1.7}
.sub-line .tag{color:var(--gold);border:1px solid rgba(255,209,102,.35);border-radius:4px;padding:1px 7px;margin:0 4px;font-size:11.5px}
/* tabs */
.tabs{display:flex;gap:8px;margin:2px 0 18px;flex-wrap:wrap}
.tab{padding:9px 22px;border-radius:10px;border:1px solid var(--line);background:#0a1322;color:var(--sub);
  font-size:14px;cursor:pointer;transition:.15s}
.tab.on{background:linear-gradient(135deg,rgba(122,165,255,.22),rgba(143,107,255,.18));border-color:var(--accent);color:#dbe7ff;font-weight:700}
.tab small{display:block;font-size:10px;color:var(--faint);font-weight:400;letter-spacing:.5px}
.tab.on small{color:#9db8ee}
.wnote{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.wnote .w{font-size:11.5px;border-radius:6px;padding:3px 9px;border:1px solid}
/* KPI */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:20px}
.kpi{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:14px;padding:16px 18px;position:relative;overflow:hidden}
.kpi::after{content:"";position:absolute;left:0;top:0;width:100%;height:2px;background:linear-gradient(90deg,var(--accent),transparent)}
.kpi .v{font-size:clamp(22px,2.4vw,30px);font-weight:700;color:#fff;font-variant-numeric:tabular-nums}
.kpi .v small{font-size:13px;color:var(--sub);font-weight:400;margin-left:3px}
.kpi .t{font-size:13px;color:var(--txt);margin-top:5px}
.kpi .e{font-size:10.5px;color:var(--faint);margin-top:2px;letter-spacing:.4px}
/* layout */
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
@media(max-width:1080px){.grid{grid-template-columns:1fr}}
@media(max-width:1080px){.grid{grid-template-columns:1fr}}
.panel{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:14px;padding:16px 18px 10px}
.panel h3{font-size:15px;margin-bottom:2px}
.panel h3 small{color:var(--faint);font-size:11px;font-weight:400;margin-left:8px;letter-spacing:.5px}
.chart{width:100%;height:330px}
.chart.tall{height:380px}
/* table */
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:4px 0 12px}
.controls input,.controls select{background:#0a1322;border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:7px 12px;font-size:13px;outline:none;min-width:150px}
.controls input:focus{border-color:var(--accent)}
.fbtn{background:#0a1322;border:1px solid var(--line);color:var(--sub);border-radius:16px;padding:5px 13px;font-size:12px;cursor:pointer}
.fbtn.on{background:rgba(122,165,255,.16);border-color:var(--accent);color:#cfe0ff}
.spacer{flex:1}
.hint{font-size:11.5px;color:var(--faint)}
.tbl-scroll{overflow:auto;max-height:750px;border:1px solid var(--line);border-radius:12px}
table{width:100%;border-collapse:collapse;font-size:13px;min-width:980px}
thead th{position:sticky;top:0;background:#0e1930;z-index:3;color:var(--sub);font-weight:600;text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}
tbody td{padding:9px 12px;border-bottom:1px solid rgba(29,44,71,.55);vertical-align:middle;white-space:nowrap}
tbody tr{cursor:pointer;transition:background .15s}
tbody tr:hover{background:rgba(122,165,255,.07)}
tr.top1 td:first-child{color:var(--gold)}
.rk{font-weight:700;font-variant-numeric:tabular-nums;width:56px}
.medal{display:inline-flex;width:24px;height:24px;border-radius:50%;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#0a0f1c}
.m1{background:linear-gradient(135deg,#ffe08a,#f2b53c)}.m2{background:linear-gradient(135deg,#e6ecf5,#9fb0c6)}.m3{background:linear-gradient(135deg,#f0c08e,#c07840)}
.uni .zh{font-weight:600}
.uni .en{display:block;font-size:11px;color:var(--faint);max-width:330px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cty{color:var(--sub);font-size:12px}
.score{display:flex;align-items:center;gap:8px;min-width:130px}
.score .n{font-weight:700;font-variant-numeric:tabular-nums;width:44px}
.bar{height:5px;border-radius:3px;background:linear-gradient(90deg,#3b6cff,#8f6bff);flex:none}
.bar-bg{width:90px;background:#152238;border-radius:3px;height:5px;overflow:hidden}
.lchip{display:inline-flex;min-width:38px;height:22px;padding:0 5px;border-radius:6px;align-items:center;justify-content:center;font-size:11px;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap}
.lmiss{color:#3f5273;font-weight:400}
.app{display:inline-block;padding:2px 9px;border-radius:10px;font-size:11px}
.a4{background:rgba(32,201,151,.14);color:#43e0b0;border:1px solid rgba(32,201,151,.4)}
.a3{background:rgba(91,141,239,.14);color:#8fb0ff;border:1px solid rgba(91,141,239,.4)}
.a2{background:rgba(244,162,89,.13);color:#f4b878;border:1px solid rgba(244,162,89,.4)}
.spr{font-size:11px;color:var(--sub);font-variant-numeric:tabular-nums}
/* method */
.method{display:grid;grid-template-columns:1.25fr 1fr;gap:16px;margin-bottom:16px}
@media(max-width:1080px){.method{grid-template-columns:1fr}}
.steps{counter-reset:st}
.step{display:flex;gap:14px;padding:11px 0;border-bottom:1px dashed rgba(29,44,71,.7)}
.step:last-child{border-bottom:none}
.step .no{counter-increment:st;flex:none;width:30px;height:30px;border-radius:8px;background:rgba(122,165,255,.12);border:1px solid rgba(122,165,255,.35);color:#bcd0ff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px}
.step .no::before{content:counter(st)}
.step b{font-size:13.5px}
.step p{font-size:12.5px;color:var(--sub);line-height:1.7;margin-top:3px}
.step p .en{color:var(--faint)}
.wtab{width:100%;border-collapse:collapse;font-size:12.5px;min-width:0}
.wtab th{color:var(--sub);text-align:left;padding:8px;border-bottom:1px solid var(--line);font-weight:600;position:static;background:none}
.wtab td{padding:8px;border-bottom:1px solid rgba(29,44,71,.5);white-space:normal}
.dot{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:7px}
/* special + modal + footer */
.small-tbl{width:100%;border-collapse:collapse;font-size:12.5px;min-width:0}
.small-tbl th{color:var(--sub);text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);position:static;background:none}
.small-tbl td{padding:8px 10px;border-bottom:1px solid rgba(29,44,71,.5)}
#mask{position:fixed;inset:0;background:rgba(3,6,12,.72);display:none;z-index:50;backdrop-filter:blur(3px)}
#modal{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);width:min(760px,92vw);max-height:88vh;overflow:auto;background:linear-gradient(180deg,#12203a,#0c1526);border:1px solid var(--line);border-radius:16px;z-index:51;display:none;padding:22px 26px}
#modal.open,#mask.open{display:block}
#modal h2{font-size:19px}
#modal h2 small{display:block;color:var(--faint);font-size:12px;font-weight:400;margin-top:4px}
.mgrid{display:grid;grid-template-columns:340px 1fr;gap:18px;margin-top:14px}
@media(max-width:700px){.mgrid{grid-template-columns:1fr}}
.mstat{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
.mstat .box{flex:1;min-width:100px;background:rgba(10,18,34,.7);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.mstat .box .k{font-size:11px;color:var(--faint)}
.mstat .box .v{font-size:17px;font-weight:700;margin-top:3px}
.xbtn{position:absolute;top:14px;right:16px;width:30px;height:30px;border-radius:50%;border:1px solid var(--line);background:#0c1526;color:var(--sub);font-size:15px;cursor:pointer}
footer{margin-top:34px;color:var(--faint);font-size:11.5px;line-height:1.9;border-top:1px solid var(--line);padding-top:16px}
footer a{color:var(--sub);text-decoration:none}
.sec-title{font-size:16px;margin:26px 0 12px;display:flex;align-items:baseline;gap:10px}
.sec-title small{color:var(--faint);font-size:11px;letter-spacing:1px;font-weight:400;text-transform:uppercase}
#err{display:none;background:#2a1220;border:1px solid #7c2d46;color:#ff9db1;padding:14px;border-radius:10px;margin:14px 0;font-size:13px}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>世界大学综合排名前 300<span class="en">Global University Composite Ranking · Top 300</span></h1>
    </div>
    <div class="editions" id="editions"></div>
  </header>
  <div class="sub-line">
    独立学术评估机构 · 研究性综合排名<span class="tag">非官方聚合</span><span class="tag" style="color:#a78bff;border-color:#a78bff55">新增 CS / AI 学科子榜</span>
    方法论：四榜百分位归一 × 方法学公信力加权 × 跨榜共识门槛（覆盖各榜 Top 300，区间名次按中值折算）—— <b>不是名次的简单平均</b>
    <span class="en">Percentile normalisation · credibility-weighted · cross-ranking consensus gate</span>
    <div id="err">图表库加载失败（网络受限）。排名表格与筛选功能不受影响。</div>
  </div>

  <div class="tabs">
    <button class="tab on" data-v="main">综合总榜 TOP 300<small>Composite · overall</small></button>
    <button class="tab" data-v="cs">学科榜 · 计算机 CS<small>Subject ranking · Computer Science</small></button>
    <button class="tab" data-v="ai">学科榜 · 人工智能 AI<small>Subject ranking · Artificial Intelligence</small></button>
  </div>
  <div id="view-main">
  <div class="kpis" id="kpis"></div>

  <div class="grid">
    <div class="panel"><h3>上榜国家/地区分布 <small>Universities by Country / Region · Top 300</small></h3><div id="cCountry" class="chart"></div></div>
    <div class="panel"><h3>Top 10 在四大榜单中的名次轨迹 <small>Rank trajectory of composite Top 10 across the four rankings</small></h3><div id="cBump" class="chart"></div></div>
    <div class="panel"><h3>综合 300 强入榜结构 <small>Cross-ranking coverage structure</small></h3><div id="cCover" class="chart"></div></div>
    <div class="panel"><h3>四榜平均名次 vs 综合名次 <small>Mean sub-ranking position vs composite position</small></h3><div id="cScatter" class="chart"></div></div>
  </div>

  <div class="sec-title">综合排名总表 <small>Composite Master Table · 点击任意院校查看四榜画像</small></div>
  <div class="panel" style="padding-bottom:16px">
    <div class="controls">
      <input id="q" type="search" placeholder="搜索院校 Search 清华 / Tsinghua …">
      <select id="fc"><option value="">全部国家/地区 All regions</option></select>
      <div class="spacer"></div>
      <button class="fbtn on" data-ap="0">全部</button>
      <button class="fbtn" data-ap="4">四榜全入</button>
      <button class="fbtn" data-ap="3">三榜</button>
      <button class="fbtn" data-ap="2">双榜</button>
      <span class="hint" id="cnt"></span>
    </div>
    <div class="tbl-scroll">
      <table id="tbl">
        <thead><tr>
          <th>综合<br>排名</th><th>大学 University</th><th>国家/地区</th><th>综合分<br>Score</th>
          <th>QS 2027</th><th>THE 2026</th><th>USNews 26-27</th><th>ARWU 2026</th>
          <th>入榜数</th><th>四榜离散度<br>σ↓更稳</th>
        </tr></thead>
        <tbody id="tb"></tbody>
      </table>
    </div>
  </div>

  <div class="sec-title">评估方法论 <small>Methodology</small></div>
  <div class="method">
    <div class="panel"><div class="steps" id="steps"></div></div>
    <div class="panel">
      <h3>维度权重与依据 <small>Weights & rationale</small></h3>
      <table class="wtab"><thead><tr><th>榜单</th><th>权重</th><th>为何如此定价公信力</th></tr></thead><tbody id="wt"></tbody></table>
      <div id="cWeight" style="width:100%;height:210px"></div>
    </div>
  </div>

  <div class="sec-title">单榜入围参考名单 <small>Single-ranking reference list · 不占综合榜席位</small></div>
  <div class="panel" style="padding-bottom:14px">
    <p style="font-size:12.5px;color:var(--sub);margin-bottom:10px" id="spIntro">以下院校仅进入某一个榜单的 Top 300，多为专科/科研机构或单一范式受益者。综合榜要求跨榜共识（≥2 榜），故单列供参考，不占综合席位。
    <span style="color:var(--faint)">Institutes appearing in only one ranking (mostly specialised or single-paradigm beneficiaries) — listed separately.</span></p>
    <table class="small-tbl"><thead><tr><th>院校 Institution</th><th>国家</th><th>唯一入围榜单</th><th>该榜名次</th><th>综合分(参考)</th></tr></thead><tbody id="tb2"></tbody></table>
  </div>

  </div><!-- /view-main -->

  <div id="view-sub" style="display:none">
    <div class="sub-line" id="subIntro"></div>
    <div class="wnote" id="subWeights"></div>
    <div class="kpis" id="subKpis"></div>
    <div class="grid">
      <div class="panel"><h3 id="barTitle">Top 15 综合分 <small>Composite score</small></h3><div id="cSubBar" class="chart"></div></div>
      <div class="panel"><h3 id="cmpTitle">Top 10 各源名次 <small>Per-source positions of Top 10</small></h3><div id="cSubBump" class="chart"></div></div>
    </div>
    <div class="panel" style="margin-bottom:16px" id="cmpPanel">
      <h3>CS 榜 vs AI 榜 名次对照 <small>CS rank vs AI rank · 对角线上方=AI 相对更强</small></h3>
      <div id="cCross" style="width:100%;height:380px"></div>
    </div>
    <div class="sec-title" id="subTblTitle">学科综合榜总表 <small>点击搜索/筛选</small></div>
    <div class="panel" style="padding-bottom:16px">
      <div class="controls">
        <input id="sq" type="search" placeholder="搜索院校 Search …">
        <select id="sfc"><option value="">全部国家/地区 All regions</option></select>
        <div class="spacer"></div>
        <span class="hint" id="scnt"></span>
      </div>
      <div class="tbl-scroll">
        <table><thead><tr id="sHead"></tr></thead><tbody id="stb"></tbody></table>
      </div>
    </div>
  </div>

  <footer id="foot"></footer>
</div>

<div id="mask"></div>
<div id="modal"><button class="xbtn" onclick="closeM()">✕</button><div id="mbody"></div><div id="mchart" style="width:100%;height:300px"></div></div>

<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js" onerror="cdnErr()"></script>
<script>
function cdnErr(){window.__noech=true;}
</script>
<script>
const PAYLOAD = __DATA__;
const FINAL = PAYLOAD.final, SPECIAL = PAYLOAD.special, META = PAYLOAD.meta;
const LISTS = ["qs","the","usnews","arwu"];
const LC = {qs:"#20c997", the:"#ff6b81", us:"#5b8def", arw:"#f4a259"};
const LNAME = {qs:"QS", the:"THE", us:"US News", arw:"ARWU 软科"};
const LFULL = {qs:"QS World University Rankings 2027", the:"THE World University Rankings 2026", us:"U.S. News Best Global Universities 2026-27", arw:"软科世界大学学术排名 ARWU 2026"};
const LW = {qs:0.20, the:0.30, us:0.25, arw:0.25};
const KEYMAP = {qs:"qs", the:"the", us:"usnews", arw:"arwu"};
const $ = s => document.querySelector(s);

/* ---------- editions badges ---------- */
const SHORT = {qs:"QS 2027 · Top300", the:"THE 2026 · Top300", us:"U.S. News 2026-27 · Top300", arw:"软科 ARWU 2026 · Top300"};
$("#editions").innerHTML = [["qs","QS"],["the","THE"],["us","U.S. News"],["arw","软科 ARWU"]].map(([k,l])=>{
  const e = META.editions[KEYMAP[k]];
  return `<span class="badge"><b style="color:${LC[k]}">${SHORT[k]}</b> · ${e.pub} 发布</span>`;
}).join("");

/* ---------- KPIs ---------- */
const byCountry = {};
FINAL.forEach(r=>byCountry[r.country]=(byCountry[r.country]||0)+1);
const nA4 = FINAL.filter(r=>r.appear===4).length;
const nA3 = FINAL.filter(r=>r.appear===3).length;
const cnCount = (byCountry["中国内地"]||0)+(byCountry["中国香港"]||0)+(byCountry["中国台湾"]||0);
const spreadMin = FINAL.filter(r=>r.appear===4).sort((a,b)=>a.spread-b.spread)[0];
const spreadMax = FINAL.slice().sort((a,b)=>b.spread-a.spread)[0];
const kpis = [
  {v:META.n_union, u:"所", t:"四榜并集候选院校", e:"Candidate pool (union of 4 rankings)"},
  {v:Object.keys(byCountry).length, u:"个", t:"覆盖国家/地区", e:"Countries / regions covered"},
  {v:nA4, u:"所", t:"四榜全入院校", e:"In all four rankings · three-list: "+nA3},
  {v:byCountry["美国"], u:"所", t:"美国上榜 (居首)", e:"US leads · UK "+(byCountry["英国"]||0)},
  {v:cnCount, u:"所", t:"中国高校 合计", e:"Mainland "+(byCountry["中国内地"]||0)+" + HK "+(byCountry["中国香港"]||0)+" + TW "+(byCountry["中国台湾"]||0)},
  {v:spreadMin?(""+spreadMin.spread):"-", u:"", t:"四榜评价最一致院校 σ", e:(spreadMin?spreadMin.zh+" · 综合第"+spreadMin.r+"名":"")+"（σ为四榜百分位标准差）"}
];
$("#kpis").innerHTML = kpis.map(k=>`<div class="kpi"><div class="v">${k.v}<small>${k.u}</small></div><div class="t">${k.t}</div><div class="e">${k.e}</div></div>`).join("");

/* ---------- country chart ---------- */
function echOk(){ return !window.__noech && typeof echarts!=="undefined"; }
function noEch(){ $("#err").style.display="block"; }
window.addEventListener("load",()=>{ setTimeout(()=>{ if(!echOk()) noEch(); }, 1200); });

/* ---------- table ---------- */
const tb = $("#tb");
function chip(list, r){
  const v = r[KEYMAP[list]];
  if(!v) return `<span class="lmiss">—</span>`;
  const a = {qs:"rgba(32,201,151,.13)",the:"rgba(255,107,129,.13)",us:"rgba(91,141,239,.15)",arw:"rgba(244,162,89,.13)"}[list];
  return `<span class="lchip" style="background:${a};color:${LC[list]};border:1px solid ${LC[list]}55" title="${LFULL[list]} 名次 ${v.d} · 百分位 ${v.pct}${v.sc!=null?" · 原始分 "+v.sc:""}">${v.d}</span>`;
}
function appearPill(n){ const t={4:"四榜",3:"三榜",2:"双榜"}[n]; const c={4:"a4",3:"a3",2:"a2"}[n]; return `<span class="app ${c}">${t}</span>`; }
let FQ="", FC="", FAP=0;
function render(){
  const rows = FINAL.filter(r=>{
    if(FC && r.country!==FC) return false;
    if(FAP && r.appear!==FAP) return false;
    if(FQ){ const s=(r.zh+r.en+r.country).toLowerCase(); if(!s.includes(FQ)) return false; }
    return true;
  });
  $("#cnt").textContent = `显示 ${rows.length} / ${FINAL.length}`;
  tb.innerHTML = rows.map(r=>{
    const medal = r.r<=3 ? `<span class="medal m${r.r}">${r.r}</span>` : r.r;
    return `<tr data-r="${r.r}" class="${r.r<=3?'top1':''}">
      <td class="rk">${medal}</td>
      <td class="uni"><span class="zh">${r.zh}</span><span class="en">${r.en}</span></td>
      <td class="cty">${r.country}</td>
      <td><div class="score"><span class="n">${r.comp.toFixed(1)}</span><span class="bar-bg"><span class="bar" style="width:${Math.round(r.comp)}px"></span></span></div></td>
      <td>${chip("qs",r)}</td><td>${chip("the",r)}</td><td>${chip("us",r)}</td><td>${chip("arw",r)}</td>
      <td>${appearPill(r.appear)}</td>
      <td><span class="spr">σ ${r.spread}</span></td>
    </tr>`;
  }).join("");
  tb.querySelectorAll("tr").forEach(tr=>tr.addEventListener("click",()=>openM(+tr.dataset.r)));
}
$("#q").addEventListener("input",e=>{FQ=e.target.value.trim().toLowerCase();render();});
const cOpts = Object.keys(byCountry).sort((a,b)=>byCountry[b]-byCountry[a]);
$("#fc").innerHTML += cOpts.map(c=>`<option value="${c}">${c} (${byCountry[c]})</option>`).join("");
$("#fc").addEventListener("change",e=>{FC=e.target.value;render();});
document.querySelectorAll(".fbtn").forEach(b=>b.addEventListener("click",()=>{
  document.querySelectorAll(".fbtn").forEach(x=>x.classList.remove("on"));
  b.classList.add("on"); FAP=+b.dataset.ap; render();
}));
render();

/* ---------- special list ---------- */
$("#spIntro").innerHTML = $("#spIntro").innerHTML.replace("Top 300，","Top 300（共 "+META.n_single+" 所），");
$("#tb2").innerHTML = SPECIAL.map(s=>{
  const ln = {qs:"QS 2027",the:"THE 2026",usnews:"U.S. News 2026-27",arwu:"软科 ARWU 2026"}[s.list];
  return `<tr><td><b>${s.zh}</b> <span style="color:var(--faint);font-size:11.5px">${s.en}</span></td><td style="color:var(--sub)">${s.country}</td><td style="color:${LC[KEYMAP[s.list]]}">${ln}</td><td>No.${s.d}</td><td>${s.comp.toFixed(1)}</td></tr>`;
}).join("");

/* ---------- methodology ---------- */
const steps = [
 ["统一口径：并列均位法 + 区间名次中值","四榜并列规则不一（QS 并列跳号、THE 官方跳号、U.S. News 同率并列）。并列院校映射为所占名次区间的算术均值；THE 201-250/251-300 与软科 101-150/151-200/201-300 等官方区间名次，按区间中值折算，不虚构精确名次。","Ties via occupied-slot averaging; banded ranks via midpoints."],
 ["榜内百分位归一，不做原始分对齐","各榜分数量纲互不可比（QS 声誉问卷 / THE 五维指标 / U.S. News 13 项文献计量 / ARWU 诺奖+高被引）。取 score = 100×(N−均位)/(N−1)（N=300）：榜内第 1 名得 100 分、第 300 位趋近 0。未进某榜 Top300 记 0 分——结构性短板如实计入，不做权重稀释。","Percentile scores replace raw scores."],
 ["方法学公信力加权","THE 30%（五维度最均衡、引文采用分数化计数）；U.S. News 25% 与 ARWU 25%（客观但偏文献计量/理科）；QS 20%（声誉与国际化主导，主观问卷占比最高、年度间名次漂移最大）。","Credibility weighting; absence scored 0."],
 ["跨榜共识门槛","综合榜要求至少进入 2 个榜单 Top 300。仅凭单榜入围的专科/研究机构（如梅奥诊所医学院、比萨高等师范学校、魏茨曼科学研究所）不占综合席位，另列「单榜参考名单」，避免单一评价范式绑架综合结论。","Consensus gate: ≥2 of 4 rankings."],
 ["断位与稳健性披露","综合分并列时按 覆盖榜数 → THE 均位 → U.S. News 均位 → 字母序 断位；同时公布每校四榜百分位标准差 σ，供使用者自行评估名次背后的一致性/分歧度。","Tie-breakers & dispersion metric σ."]
];
$("#steps").innerHTML = steps.map((s,i)=>`<div class="step"><div class="no"></div><div><b>${i+1}. ${s[0]}</b><p>${s[1]} <span class="en">${s[2]}</span></p></div></div>`).join("");
$("#wt").innerHTML = [["the","THE 2026","五维度均衡：教学/研究/引用/国际化/产业，引用指标分数化处理，方法透明"],
  ["us","U.S. News 26-27","13 项文献计量指标（Scopus/WoS），全球+区域声誉仅占 25%，客观可复核，但无教学维度"],
  ["arw","ARWU 2026","诺奖校友/教师、高被引科学家、NSF 高分期刊论文等硬指标，抗刷分能力最强，但严重偏理科"],
  ["qs","QS 2027","学术声誉 40%+雇主声誉等，反映全球认可度与国际化，但问卷主导、易受品牌惯性影响"]
].map(([k,l,why])=>`<tr><td style="white-space:nowrap"><span class="dot" style="background:${LC[k]}"></span><b>${l}</b></td><td style="font-weight:700;color:${LC[k]}">${(LW[k]*100).toFixed(0)}%</td><td style="color:var(--sub);font-size:12px">${why}</td></tr>`).join("");

/* ---------- footer ---------- */
$("#foot").innerHTML = `数据来源：QS 2027（2026-06 发布）· THE 2026（2025-10 发布）· U.S. News Best Global Universities 2026-27（2026-06 发布）· 软科 ARWU 2026（2026-08 发布）。名次与原始分均取自各榜官方公开发布（U.S. News 官方总分未公开可得，仅采用其名次）。101-300 区间：THE 取自官方页面内嵌数据库（201 名后为官方区间）；QS 取自官方数据双源交叉；U.S. News 官方存在同率并列跳号，按官方显示顺序连续编号；软科 101 名后为官方区间名单。<br>
Data sources: topuniversities.com · timeshighereducation.com · usnews.com Best Global Universities · shanghairanking.com. 中文译名为通行译法。<br>
<b style="color:var(--sub)">免责声明</b>：本看板为独立研究性综合评估，方法论与权重由评估机构设定，不代表任何官方立场；排名仅供比较参考，不构成升学/资助决策依据。生成时间 Generated: __GENDATE__<br>
<b style="color:var(--sub)">学科榜数据源</b>：CSRankings 2026（DBLP 顶会发表口径，2016-2026 窗口）· QS/THE/U.S. News/软科 2026 学科排名（CS 五源、AI 三源交叉；AI 学科榜为软科 2025 年首发新学科）。学科榜方法论与综合榜一致，详见各子榜页首说明。`;

/* ---------- charts ---------- */
function drawCharts(){
  if(!echOk()) return;
  const AX = {axisLine:{lineStyle:{color:"#2a3c5e"}}, axisLabel:{color:"#93a7c7",fontSize:11}, splitLine:{lineStyle:{color:"rgba(29,44,71,.5)"}}};
  // country bar
  const cs = cOpts.slice(0,15).map(c=>[c,byCountry[c]]).reverse();
  echarts.init($("#cCountry")).setOption({
    grid:{left:80,right:40,top:8,bottom:22},
    xAxis:{type:"value",...AX}, yAxis:{type:"category",data:cs.map(x=>x[0]),...AX,axisLabel:{color:"#c6d4ec",fontSize:11.5}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    series:[{type:"bar",data:cs.map(x=>x[1]),barWidth:13,
      label:{show:true,position:"right",color:"#93a7c7",fontSize:11},
      itemStyle:{borderRadius:[0,7,7,0],color:p=>["中国内地","中国香港"].includes(cs[p.dataIndex][0])?"#ff6b6b":(cs[p.dataIndex][0]==="美国"?"#5b8def":"#35507f")}}]
  });
  // bump: top10 across 4 rankings ordered by weight
  const T10 = FINAL.filter(r=>r.r<=10);
  const order = [["qs","QS 27",.20],["arw","ARWU 26",.25],["us","US News",.25],["the","THE 26",.30]];
  const pal = ["#ffd166","#5b8def","#20c997","#ff6b81","#f4a259","#8f6bff","#4dd0e1","#e0e0e0","#c5e1a5","#f48fb1"];
  echarts.init($("#cBump")).setOption({
    grid:{left:44,right:150,top:8,bottom:26},
    legend:{show:false},
    tooltip:{trigger:"axis",formatter:ps=>ps[0].name+"<br>"+ps.map(p=>p.marker+p.seriesName+": 第"+p.value+"名").join("<br>")},
    xAxis:{type:"category",data:order.map(o=>o[1]),...AX,axisLabel:{color:"#c6d4ec",fontSize:12}},
    yAxis:{type:"value",inverse:true,min:1,max:30,interval:5,...AX},
    series:T10.map((r,i)=>({name:r.zh,type:"line",symbolSize:8,lineStyle:{width:2.4,color:pal[i]},itemStyle:{color:pal[i]},
      endLabel:{show:true,color:pal[i],fontSize:11,distance:6,formatter:p=>r.zh},
      labelLayout:{hideOverlap:true},
      emphasis:{focus:"series"},
      data:order.map(o=>r[KEYMAP[o[0]]]?r[KEYMAP[o[0]]].d:null)}))
  });
  // weight donut
  echarts.init($("#cWeight")).setOption({
    tooltip:{formatter:p=>`${p.name}: ${p.value}%`},
    series:[{type:"pie",radius:["52%","78%"],center:["50%","52%"],
      label:{color:"#c6d4ec",fontSize:11,formatter:"{b}\n{c}%"},
      data:[{name:"THE",value:30,itemStyle:{color:LC.the}},{name:"U.S. News",value:25,itemStyle:{color:LC.us}},
            {name:"ARWU",value:25,itemStyle:{color:LC.arw}},{name:"QS",value:20,itemStyle:{color:LC.qs}}],
      itemStyle:{borderColor:"#0d1524",borderWidth:2}}]
  });
  // coverage structure
  const n2=FINAL.filter(r=>r.appear===2).length, n3=FINAL.filter(r=>r.appear===3).length, n4=FINAL.filter(r=>r.appear===4).length;
  echarts.init($("#cCover")).setOption({
    grid:{left:88,right:50,top:14,bottom:26},
    xAxis:{type:"value",...AX}, yAxis:{type:"category",data:["双榜入围","三榜入围","四榜全入","单榜(仅参考)"],...AX,axisLabel:{color:"#c6d4ec",fontSize:12}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    series:[{type:"bar",barWidth:26,
      label:{show:true,position:"right",color:"#c6d4ec",fontSize:12},
      data:[{value:n2,itemStyle:{color:"#f4a259"}},{value:n3,itemStyle:{color:"#5b8def"}},{value:n4,itemStyle:{color:"#20c997"}},{value:META.n_single,itemStyle:{color:"#35507f"}}],
      itemStyle:{borderRadius:[0,8,8,0]}}]
  });
  // scatter: mean pos of sub-rankings vs composite rank
  echarts.init($("#cScatter")).setOption({
    grid:{left:56,right:24,top:14,bottom:44},
    tooltip:{formatter:p=>{const r=FINAL[p.dataIndex];return r.zh+"<br>综合第"+r.r+" · 四榜平均位次 "+Math.round(p.value[1])+" · 入榜"+r.appear+"个";}},
    xAxis:{type:"value",inverse:true,min:1,max:300,...AX},
    yAxis:{type:"value",inverse:true,min:1,max:300,...AX},
    series:[{type:"scatter",symbolSize:p=>p[2]===4?7:(p[2]===3?6:4.5),
      data:FINAL.map(r=>{const ps=LISTS.map(k=>r[k]?r[k].pct:null).filter(v=>v!==null);
        const mean=ps.reduce((a,b)=>a+b,0)/ps.length; const mp=Math.round((1-mean/100)*(LIST_N)+0.5);
        return {value:[r.r,mp,r.appear],itemStyle:{color:r.appear===4?"#20c997":(r.appear===3?"#5b8def":"#f4a259")}};}),
      markLine:{silent:true,symbol:"none",lineStyle:{color:"#3b527e",type:"dashed"},data:[[{coord:[1,1]},{coord:[300,300]}]],label:{show:false}}}],
  });
}
const LIST_N = 300;

/* ---------- modal ---------- */
let mChart=null;
function openM(rk){
  const r = FINAL.find(x=>x.r===rk); if(!r) return;
  const rows = [["the","THE 2026"],["us","U.S. News 26-27"],["arw","软科 ARWU 2026"],["qs","QS 2027"]].map(([k,l])=>{
    const v=r[KEYMAP[k]]; 
    return `<tr><td style="white-space:nowrap"><span class="dot" style="background:${LC[k]}"></span>${l}</td>
      <td>${v?("第 "+v.d+" 名"):'<span style="color:#3f5273">未入该榜百强</span>'}</td>
      <td>${v?v.pct:"—"}</td><td>${v&&v.sc!=null?v.sc:"—"}</td></tr>`;
  }).join("");
  $("#mbody").innerHTML = `<h2>${r.zh}<small>${r.en} · ${r.country}</small></h2>
    <div class="mstat">
      <div class="box"><div class="k">综合排名 Overall</div><div class="v" style="color:var(--gold)">No.${r.r}</div></div>
      <div class="box"><div class="k">综合分 Composite</div><div class="v">${r.comp.toFixed(2)}</div></div>
      <div class="box"><div class="k">入榜数 Coverage</div><div class="v">${r.appear} / 4</div></div>
      <div class="box"><div class="k">离散度 σ</div><div class="v" style="color:${r.spread<8?"#43e0b0":(r.spread<16?"#f4b878":"#ff6b81")}">${r.spread}</div></div>
    </div>
    <table class="small-tbl" style="margin-top:14px"><thead><tr><th>榜单</th><th>榜内名次</th><th>百分位分</th><th>官方原始分</th></tr></thead><tbody>${rows}</tbody></table>
    <p style="font-size:11.5px;color:var(--faint);margin-top:8px">σ 为四榜百分位分的标准差（缺榜按 0 计）：σ 越小，说明该院校在四种评价范式下结论越一致。</p>`;
  $("#mask").classList.add("open"); $("#modal").classList.add("open");
  if(echOk()){
    if(!mChart) mChart = echarts.init($("#mchart"));
    mChart.setOption({
      tooltip:{},
      radar:{indicator:["QS","THE","U.S. News","ARWU"].map(n=>({name:n,max:100})),
        axisName:{color:"#93a7c7",fontSize:11}, splitArea:{show:false},
        splitLine:{lineStyle:{color:"rgba(29,44,71,.8)"}}, axisLine:{lineStyle:{color:"#2a3c5e"}}},
      series:[{type:"radar",data:[{name:r.zh,value:LISTS.map(k=>r[k]?r[k].pct:0),
        areaStyle:{color:"rgba(122,165,255,.25)"},lineStyle:{color:"#7aa5ff"},itemStyle:{color:"#7aa5ff"}}]}]
    }, true);
    mChart.resize();
  }
}
function closeM(){ $("#mask").classList.remove("open"); $("#modal").classList.remove("open"); }
$("#mask").addEventListener("click",closeM);
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeM();});


/* ---------- subject views ---------- */
const SUBJECT = __SUBJECT__;
const SC = {csr:"#a78bfa",qs:"#20c997",the:"#ff6b81",usnews:"#5b8def",arwu:"#f4a259"};
const SUBED = {csr:"CSRankings 2026 · 顶会发表量",qs:"QS Subject CS 2026",the:"THE Subject CS 2026",usnews:"U.S. News Subject 26-27",arwu:"软科 GRAS 2026"};
let CUR="main", SQ="", SFC="", SUBCUR="cs";
function subSrcs(s){return Object.keys(SUBJECT[s].weights);}
function subData(s){return SUBJECT[s];}
function sChip(list,r){
  const v=r.ranks[list];
  if(!v) return `<span class="lmiss">—</span>`;
  return `<span class="lchip" style="background:${SC[list]}1a;color:${SC[list]};border:1px solid ${SC[list]}55" title="${SUBED[list]} 名次 ${v.d} · 百分位 ${v.pct}">${v.d}</span>`;
}
function sHead(){
  const srcs=subSrcs(SUBCUR);
  $("#sHead").innerHTML = `<th>综合<br>排名</th><th>大学 University</th><th>国家/地区</th><th>综合分<br>Score</th>`+
    srcs.map(s=>`<th>${({csr:"CSRank",qs:"QS",the:"THE",usnews:"USNews",arwu:"ARWU"})[s]}</th>`).join("")+
    `<th>来源数</th><th>σ</th>`;
}
function sRender(){
  const rows=subData(SUBCUR).rows, srcs=subSrcs(SUBCUR), n=srcs.length;
  const filt=rows.filter(r=>{
    if(SFC && r.country!==SFC) return false;
    if(SQ){const s=(r.zh+r.en).toLowerCase(); if(!s.includes(SQ)) return false;}
    return true;
  });
  $("#scnt").textContent=`显示 ${filt.length} / ${rows.length}`;
  $("#stb").innerHTML=filt.map(r=>{
    const medal=r.r<=3?`<span class="medal m${r.r}">${r.r}</span>`:r.r;
    return `<tr><td class="rk">${medal}</td>
      <td class="uni"><span class="zh">${r.zh}</span><span class="en">${r.en}</span></td>
      <td class="cty">${r.country}</td>
      <td><div class="score"><span class="n">${r.comp.toFixed(1)}</span><span class="bar-bg"><span class="bar" style="width:${Math.round(r.comp)}px"></span></span></div></td>
      ${srcs.map(s=>`<td>${sChip(s,r)}</td>`).join("")}
      <td><span class="app ${n===5?(r.appear===5?"a4":r.appear>=3?"a3":"a2"):(r.appear===3?"a4":"a2")}">${r.appear}/${n}</span></td>
      <td><span class="spr">σ ${r.spread}</span></td></tr>`;
  }).join("");
}
function sCharts(){
  if(!echOk()) return;
  const data=subData(SUBCUR), rows=data.rows, srcs=subSrcs(SUBCUR);
  const AX={axisLine:{lineStyle:{color:"#2a3c5e"}},axisLabel:{color:"#93a7c7",fontSize:11},splitLine:{lineStyle:{color:"rgba(29,44,71,.5)"}}};
  const t15=rows.slice(0,15).reverse();
  echarts.init($("#cSubBar")).setOption({
    grid:{left:120,right:46,top:8,bottom:22},
    xAxis:{type:"value",max:100,...AX},yAxis:{type:"category",data:t15.map(r=>r.zh),...AX,axisLabel:{color:"#c6d4ec",fontSize:11.5}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    series:[{type:"bar",data:t15.map(r=>r.comp),barWidth:14,
      label:{show:true,position:"right",color:"#93a7c7",fontSize:11,formatter:p=>p.value.toFixed(1)},
      itemStyle:{borderRadius:[0,7,7,0],color:p=>["中国内地","中国香港","中国台湾"].includes(t15[p.dataIndex].country)?"#ff6b6b":"#7aa5ff"}}]
  },true);
  const T10=rows.slice(0,10);
  const pal=["#ffd166","#5b8def","#20c997","#ff6b81","#f4a259","#8f6bff","#4dd0e1","#e0e0e0","#c5e1a5","#f48fb1"];
  echarts.init($("#cSubBump")).setOption({
    grid:{left:40,right:130,top:8,bottom:26},
    tooltip:{trigger:"axis",formatter:ps=>ps[0].name+"<br>"+ps.filter(p=>p.value!=null).map(p=>p.marker+p.seriesName+": 第"+p.value+"名").join("<br>")},
    xAxis:{type:"category",data:srcs.map(s=>({csr:"CSRank",qs:"QS",the:"THE",usnews:"USNews",arwu:"ARWU"})[s]),...AX,axisLabel:{color:"#c6d4ec",fontSize:12}},
    yAxis:{type:"value",inverse:true,min:1,max:50,interval:10,...AX},
    series:T10.map((r,i)=>({name:r.zh,type:"line",symbolSize:8,lineStyle:{width:2.4,color:pal[i]},itemStyle:{color:pal[i]},
      endLabel:{show:true,color:pal[i],fontSize:11,distance:6,formatter:()=>r.zh},labelLayout:{hideOverlap:true},
      emphasis:{focus:"series"},
      data:srcs.map(s=>r.ranks[s]?r.ranks[s].d:null)}))
  },true);
  // cross CS vs AI
  const csMap={},aiMap={};
  subData("cs").rows.forEach(r=>csMap[r.zh]=r.r);
  subData("ai").rows.forEach(r=>aiMap[r.zh]=r.r);
  const pts=Object.keys(csMap).filter(z=>aiMap[z]!==undefined).map(z=>({zh:z,x:csMap[z],y:aiMap[z],d:csMap[z]-aiMap[z]}));
  echarts.init($("#cCross")).setOption({
    grid:{left:56,right:30,top:16,bottom:44},
    tooltip:{formatter:p=>{const q=pts[p.dataIndex];return q.zh+"<br>CS 第"+q.x+" · AI 第"+q.y+(q.d>0?`<br>AI 相对强 ${q.d} 位`:`<br>CS 相对强 ${-q.d} 位`);}},
    xAxis:{type:"value",name:"CS 榜名次",nameLocation:"middle",nameGap:28,inverse:true,min:1,max:100,...AX,nameTextStyle:{color:"#93a7c7"}},
    yAxis:{type:"value",name:"AI 榜名次",inverse:true,min:1,max:100,...AX,nameTextStyle:{color:"#93a7c7"}},
    series:[{type:"scatter",symbolSize:9,
      data:pts.map(q=>({value:[q.x,q.y],itemStyle:{color:Math.abs(q.d)>=25?(q.d>0?"#43e0b0":"#ff6b81"):"#7aa5ff"}})),
      label:{show:true,position:"top",fontSize:10,color:"#93a7c7",formatter:p=>{const q=pts[p.dataIndex];return Math.abs(q.d)>=30?q.zh:"";}},labelLayout:{hideOverlap:true},
      markLine:{silent:true,symbol:"none",lineStyle:{color:"#3b527e",type:"dashed"},data:[[{coord:[1,1]},{coord:[100,100]}]],label:{show:false}}}]
  },true);
}
function showSub(sub){
  SUBCUR=sub; SQ="";SFC=""; $("#sq").value="";
  const srcs=subSrcs(sub), rows=subData(sub).rows;
  $("#subIntro").innerHTML = (sub==="cs"
    ? "计算机科学学科综合榜 · 五源交叉：CSRankings 顶会发表量 + QS/THE/U.S. News/软科 四大学科榜。与综合榜同一套方法（百分位归一 × 公信力加权 × ≥2 源共识门槛），各源统一取 Top 100 可比池；区间名次按中值折算。"
    : "人工智能学科综合榜 · 三源交叉：CSRankings-AI（顶会口径）+ U.S. News-AI（文献计量口径）+ 软科 GRAS-AI 2026（2025 年首发新学科）。QS/THE 无独立 AI 学科榜故为三源；门槛为 ≥2/3 源。");
  $("#subWeights").innerHTML = srcs.map(s=>`<span class="w" style="border-color:${SC[s]}66;color:${SC[s]};background:${SC[s]}14">${SUBED[s]} · ${(subData(sub).weights[s]*100).toFixed(0)}%</span>`).join("");
  const byC={}; rows.forEach(r=>byC[r.country]=(byC[r.country]||0)+1);
  const full=rows.filter(r=>r.appear===srcs.length).length;
  const china=(byC["中国内地"]||0)+(byC["中国香港"]||0)+(byC["中国台湾"]||0)+(byC["中国澳门"]||0);
  const stable=rows.filter(r=>r.appear>=srcs.length-1).sort((a,b)=>a.spread-b.spread)[0];
  $("#subKpis").innerHTML=[
    {v:rows.length,u:"校",t:"学科榜院校数",e:"Ranked"},
    {v:Object.keys(byC).length,u:"个",t:"国家/地区",e:"Countries"},
    {v:byC["美国"]||0,u:"所",t:"美国上榜",e:"US"},
    {v:china,u:"所",t:"中国高校合计",e:"China incl. HK/TW"},
    {v:full,u:"所",t:"全源交叉命中",e:"In all "+srcs.length+" sources"},
    {v:stable?stable.zh:"-",u:"",t:"评价最稳（σ "+(stable?stable.spread:"-")+"）",e:stable?"综合第 "+stable.r+" 名":""}
  ].map(k=>`<div class="kpi"><div class="v" ${k.u?'':"style=font-size:19px"}>${k.v}<small>${k.u}</small></div><div class="t">${k.t}</div><div class="e">${k.e}</div></div>`).join("");
  sHead(); sRender();
  const cOptsS=Object.keys(byC).sort((a,b)=>byC[b]-byC[a]);
  $("#sfc").innerHTML=`<option value="">全部国家/地区 All regions</option>`+cOptsS.map(c=>`<option value="${c}">${c} (${byC[c]})</option>`).join("");
  sCharts();
}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>{
  document.querySelectorAll(".tab").forEach(x=>x.classList.remove("on")); b.classList.add("on");
  CUR=b.dataset.v;
  $("#view-main").style.display = CUR==="main"?"":"none";
  $("#view-sub").style.display = CUR==="main"?"none":"";
  if(CUR!=="main") showSub(CUR);
}));
if(["#cs","#ai"].includes(location.hash)){ setTimeout(()=>{ document.querySelector('.tab[data-v="'+location.hash.slice(1)+'"]').click(); },50); }
$("#sq").addEventListener("input",e=>{SQ=e.target.value.trim().toLowerCase();sRender();});
$("#sfc").addEventListener("change",e=>{SFC=e.target.value;sRender();});

/* ---------- init charts ---------- */
window.addEventListener("load",()=>{ if(echOk()){drawCharts(); window.addEventListener("resize",()=>{document.querySelectorAll(".chart,#cWeight,#mchart,#cCross").forEach(el=>{const c=echarts.getInstanceByDom(el);if(c)c.resize();});});} });
</script>
</body>
</html>
"""

import datetime
gen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
html = HTML.replace("__DATA__", DATA_JS).replace("__SUBJECT__", SUBJECT_JS).replace("__GENDATE__", gen)
outfile = OUT / "index.html"
outfile.write_text(html, encoding="utf-8")
print("written:", outfile, outfile.stat().st_size, "bytes")
