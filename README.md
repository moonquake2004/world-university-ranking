# 世界大学综合排名 Top 300 + CS/AI 学科榜 · 数据看板

> Global University Composite Ranking (Top 300) with CS & AI subject sub-rankings — a self-contained dark-theme dashboard.

**在线看板 Live:** https://moonquake2004.github.io/world-university-ranking/

单文件 HTML（数据内联 + ECharts），直接打开即用，无后端依赖。

## 子榜构成

| 视图 | 数据源 | 输出 |
|---|---|---|
| 综合总榜 | QS 2027 · THE 2026 · U.S. News 2026-27 · 软科 ARWU 2026（各 Top 300） | 综合 Top 300 + 146 所单榜参考 |
| 学科榜 · CS | CSRankings 2026 · THE Subject CS 2026 · U.S. News CS 26-27 · 软科 GRAS CS 2026 · QS CS 2026 | CS 综合 Top 100 |
| 学科榜 · AI | CSRankings-AI · U.S. News-AI · 软科 GRAS-AI 2026 | AI 综合 91 校 + CS↔AI 对照 |
| 学科榜 · 传播学 | QS Communication & Media Studies 2026 · 软科 GRAS Communication 2026（THE 无独立传播学榜、U.S. News 世界学科榜不覆盖） | 双源综合 104 席（分数线并列全保留） |

## 方法论（非简单平均）

1. **统一口径**：并列名次按所占位次均值折算（均位法）；THE/软科 100 名后的官方区间名次按区间中值折算，不虚构精确名次。
2. **榜内百分位归一**：`score = 100 × (N − 均位) / (N − 1)`，弃用不可比的原始分；未进池记 0 分（结构性短板如实计入）。
3. **公信力加权**：
   - 综合榜：THE 30% ｜ U.S. News 25% ｜ ARWU 25% ｜ QS 20%
   - CS 榜：CSRankings 25% ｜ THE 20% ｜ U.S. News 20% ｜ ARWU 20% ｜ QS 15%
   - AI 榜：CSRankings-AI 40% ｜ U.S. News-AI 35% ｜ 软科-AI 25%
   - 传播学：QS 50% ｜ 软科 50%（仅两源可用、声誉与计量范式互补故等权；不设 ≥2 门槛，单源院校标注 1/2）
4. **跨榜共识门槛**：至少命中 2 个来源方可占综合席位；单源专科/研究机构另列参考名单。
5. **稳健性披露**：每校公布各源百分位标准差 σ；断位规则 = 覆盖数 → THE → U.S. News → 字母序。

## 数据版本

- QS World University Rankings 2027（2026-06 发布）
- THE World University Rankings 2026（2025-10 发布）
- U.S. News Best Global Universities 2026-27（2026-06 发布）
- 软科 ARWU 2026（2026-08 发布）
- 学科榜：CSRankings 2026（DBLP 2016-2026 窗口）· QS/THE/US News/软科 GRAS 2026 学科排名

名次与原始分均取自各榜官方公开发布；院校名经跨源规范化匹配（见 `src/matchlib.py`）。

## 仓库结构

```
index.html          # 看板成品（数据内联，可直接部署 GitHub Pages）
src/
  compute.py        # 综合榜计算（读 data/ 下 8 个综合榜 TSV → stage1.json）
  subject_compute.py# CS/AI 学科榜计算（读 data/ 下 8 个学科 TSV → subject.json）
  matchlib.py       # 院校名规范化匹配 / 并列均位 / 百分位（共用库）
  build_dashboard.py# 组装 index.html（内联两份 JSON）
  data/raw_*.tsv    # 四大综合榜 Top1-100 / 101-300 + 学科榜原始快照
```

## 复现

```bash
cd src
python3 compute.py && python3 subject_compute.py && python3 build_dashboard.py
# 输出 ../index.html
```

## 免责声明

本项目为独立研究性综合评估，权重与方法论设定不代表任何官方立场；排名仅供比较参考，不构成升学、资助或雇佣决策依据。各榜单名称与数据版权归原发布机构所有。

License: MIT
