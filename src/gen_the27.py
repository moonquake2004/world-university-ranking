# -*- coding: utf-8 -*-
"""从 THE 2027 __NEXT_DATA__ 生成 raw_the.tsv / raw_the_101_300.tsv / raw_the_301_500.tsv
格式: rank \t en \t zh \t country \t score ; 并列去'=', 分档全角破折号->'-', 国家中文化
"""
import re, json, glob
from pathlib import Path
BASE = Path(__file__).parent
import matchlib as M
nk = M.norm_key

data = json.load(open(BASE / "the27_data.json", encoding="utf-8"))  # 已按 rank_order 数值排序, 前500

# 现有各 raw 文件 en -> (zh, country_zh)
en2zh, en2cty = {}, {}
for f in glob.glob(str(BASE / "raw_*.tsv")):
    if "the" in f and "cs" not in f:
        pass  # 也读, 但下面统一
    for ln in open(f, encoding="utf-8"):
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 4 and p[1] and p[2] and re.search(r"[\u4e00-\u9fff]", p[2]):
            k = nk(p[1])
            if k not in en2zh: en2zh[k] = p[2]
            if k not in en2cty and re.search(r"[\u4e00-\u9fff]", p[3]): en2cty[k] = p[3]

CTY = {"China":"中国内地","United States":"美国","United Kingdom":"英国","Germany":"德国","France":"法国",
 "Japan":"日本","India":"印度","Canada":"加拿大","Australia":"澳大利亚","Italy":"意大利","Spain":"西班牙",
 "Netherlands":"荷兰","Switzerland":"瑞士","South Korea":"韩国","Brazil":"巴西","Singapore":"新加坡",
 "Sweden":"瑞典","Poland":"波兰","Israel":"以色列","Denmark":"丹麦","Norway":"挪威","Finland":"芬兰",
 "Austria":"奥地利","Belgium":"比利时","Russia":"俄罗斯","Iran":"伊朗","Turkey":"土耳其","Mexico":"墨西哥",
 "Saudi Arabia":"沙特阿拉伯","Portugal":"葡萄牙","Czech Republic":"捷克","Czechia":"捷克","Argentina":"阿根廷",
 "Chile":"智利","South Africa":"南非","Egypt":"埃及","Pakistan":"巴基斯坦","Malaysia":"马来西亚",
 "Thailand":"泰国","Ireland":"爱尔兰","Chinese Taipei":"中国台湾","Taiwan":"中国台湾","Hong Kong":"中国香港",
 "Macau":"中国澳门","Ukraine":"乌克兰","Romania":"罗马尼亚","Greece":"希腊","Hungary":"匈牙利",
 "New Zealand":"新西兰","Bangladesh":"孟加拉国","Indonesia":"印度尼西亚","Vietnam":"越南","Colombia":"哥伦比亚",
 "Peru":"秘鲁","Morocco":"摩洛哥","Tunisia":"突尼斯","Nigeria":"尼日利亚","Kenya":"肯尼亚","Ghana":"加纳",
 "United Arab Emirates":"阿联酋","Qatar":"卡塔尔","Kuwait":"科威特","Lebanon":"黎巴嫩","Jordan":"约旦",
 "Philippines":"菲律宾","Sri Lanka":"斯里兰卡","Nepal":"尼泊尔","Kazakhstan":"哈萨克斯坦","Estonia":"爱沙尼亚",
 "Slovakia":"斯洛伐克","Slovenia":"斯洛文尼亚","Croatia":"克罗地亚","Serbia":"塞尔维亚","Bulgaria":"保加利亚",
 "Lithuania":"立陶宛","Latvia":"拉脱维亚","Cyprus":"塞浦路斯","Malta":"马耳他","Luxembourg":"卢森堡",
 "Iceland":"冰岛","Ecuador":"厄瓜多尔","Venezuela":"委内瑞拉","Uruguay":"乌拉圭","Costa Rica":"哥斯达黎加",
 "Panama":"巴拿马","Guatemala":"危地马拉","Cuba":"古巴","Dominican Republic":"多米尼加","Puerto Rico":"波多黎各",
 "Belarus":"白俄罗斯","Georgia":"格鲁吉亚","Armenia":"亚美尼亚","Azerbaijan":"阿塞拜疆","Algeria":"阿尔及利亚",
 "Libya":"利比亚","Iraq":"伊拉克","Oman":"阿曼","Bahrain":"巴林","Brunei":"文莱","Macau SAR":"中国澳门"}

def clean_rank(rk):
    rk = str(rk).strip().lstrip("=").replace("–", "-").replace("—", "-")
    return rk
def clean_score(sc):
    return str(sc).replace("–", "-").replace("—", "-")

# 尾部新校中文补译 (norm_key -> zh)
ZH_SUPP = {
    nk("EURECOM"): "欧洲数学与计算机科学研究所",
    nk("Ahlia University"): "阿赫利亚大学",
    nk("Constructor University"): "孔斯特鲁克托大学",
    nk("Ca’ Foscari University of Venice"): "威尼斯福斯卡里大学",
    nk("Ca' Foscari University of Venice"): "威尼斯福斯卡里大学",
    nk("Campus Bio-Medico University of Rome"): "罗马生物医学大学",
    nk("Gulf University for Science and Technology"): "海湾科技大学",
    nk("TU Dortmund University"): "多特蒙德工业大学",
    nk("Wroclaw Medical University"): "弗罗茨瓦夫医科大学",
}

rows = []
for r in data:
    en = r["name"]; k = nk(en)
    zh = en2zh.get(k) or ZH_SUPP.get(k, en)
    loc = r.get("location") or ""
    cty = en2cty.get(k) or CTY.get(loc, loc)
    rows.append((clean_rank(r["rank"]), en, zh, cty, clean_score(r.get("scores_overall", ""))))

def dump(fn, sub):
    with open(BASE / fn, "w", encoding="utf-8") as f:
        for x in sub:
            f.write("\t".join(x) + "\n")
dump("raw_the.tsv", rows[:100])
dump("raw_the_101_300.tsv", rows[100:300])
dump("raw_the_301_500.tsv", rows[300:500])
print("THE2027 写出:", len(rows), "行 (1-100/101-300/301-500)")
print("zh 仍为英文(未匹配)数:", sum(1 for x in rows if not re.search(r'[\u4e00-\u9fff]', x[2])))
print("country 仍为英文数:", sum(1 for x in rows if not re.search(r'[\u4e00-\u9fff]', x[3])))
print("前5:", rows[:5])
print("rank100-101:", rows[99:101])
print("rank300-301:", rows[299:301])
print("末2:", rows[-2:])
