#!/usr/bin/env python3
"""Render the self-contained HTML report for the policy-transfer benchmark.

Reads analysis/results/policy_comparison.json and
analysis/results/policy_transfer_benchmark.json, writes a single-file
report (inline CSS/JS, no external assets) to
analysis/results/policy_transfer_report.html.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"

TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Policy-Level Transfer — 决策层 vs 表征层基准报告</title>
<style>
:root{--ink:#1a2027;--mut:#5c6875;--line:#e3e8ee;--good:#1a7f5a;--bad:#c0392b;--warn:#b9770e;--accent:#2f6b8a;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,"SF Pro","Helvetica Neue",Arial,"PingFang SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}
.wrap{max-width:960px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:1.45rem;margin:8px 0 2px}
h2{font-size:1.08rem;margin:30px 0 10px;color:var(--accent);border-bottom:2px solid var(--accent);padding-bottom:4px}
.sub{color:var(--mut);font-size:.86rem}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.8rem;font-variant-numeric:tabular-nums}
th,td{padding:5px 7px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{color:var(--mut);font-weight:600;font-size:.72rem;text-transform:uppercase;letter-spacing:.03em}
.pos{color:var(--good);font-weight:600}.neg{color:var(--bad);font-weight:600}
.d-apply{color:var(--good);font-weight:700}.d-rank{color:var(--warn);font-weight:600}.d-abst{color:var(--mut)}
.hero{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.metric{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px}
.metric .v{font-size:1.5rem;font-weight:700}
.metric .l{font-size:.72rem;color:var(--mut)}
.bar{height:8px;border-radius:4px;background:var(--line);overflow:hidden;margin-top:6px}
.bar>i{display:block;height:100%;border-radius:4px}
canvas{width:100%;height:auto}
.note{font-size:.78rem;color:var(--mut)}
code{background:#eef1f4;padding:1px 5px;border-radius:4px;font-size:.78rem}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:640px){.grid2{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
<h1>跨领域知识迁移：决策层 vs 表征层</h1>
<div class="sub">policy-transfer-benchmark-v1 · seed 20260810 · 15 条有向边 × {standard, contrastive} + ExtraTrees 行 · <code>analysis/results/policy_comparison.json</code></div>

<div class="card">
<b>研究假设（arXiv:2508.21038 启发）：</b>单向量表征存在理论上限，跨领域迁移应表述为 <i>context-conditioned policy transfer</i>——检索提供候选，策略决定 what/when/how。本报告是该假设的首次决策层实证：在 30 个 (边, 方法) 决策上比较 4 种策略。
</div>

<div class="hero">
<div class="metric"><div class="l">Frozen 规则 apply 精度</div><div class="v pos">100%</div><div class="bar"><i style="width:100%;background:var(--good)"></i></div></div>
<div class="metric"><div class="l">LLM 策略 apply 精度</div><div class="v pos">100%</div><div class="bar"><i style="width:100%;background:var(--good)"></i></div></div>
<div class="metric"><div class="l">Learned GBM apply 精度</div><div class="v" style="color:var(--warn)">70.6%</div><div class="bar"><i style="width:70.6%;background:var(--warn)"></i></div></div>
<div class="metric"><div class="l">朴素全迁移 apply 精度</div><div class="v neg">73.3%</div><div class="bar"><i style="width:73.3%;background:var(--bad)"></i></div></div>
</div>

<h2>① 策略总览（30 个决策）</h2>
<div class="card"><table id="polTable"></table>
<div class="note">mean ρ = 决策后实现 Spearman 均值（apply 记实际 ρ，abstain/rank_only 记 0）。harm = apply 后 ρ&lt;0 的伤害边。miss = 被 abstain 但 ρ&gt;0.3 的错失边。Δ vs naive 为配对 bootstrap（20,000 次）。</div></div>

<div class="grid2">
<div class="card"><b>实现 ρ 均值</b><canvas id="cMean" width="440" height="240"></canvas></div>
<div class="card"><b>伤害边数（越低越好）</b><canvas id="cHarm" width="440" height="240"></canvas></div>
</div>

<h2>② 15 条边的表征层结果 + 三个策略的决策</h2>
<div class="card"><table id="edgeTable"></table>
<div class="note">cov = 成分覆盖率；std/contr/ET = 表征层迁移 Spearman。决策列：frozen / learned / llm（standard 行）。LLM 决策由 Claude 仅基于 outcome-free 状态字段盲评给出，锚定于 <code>llm_policy_decisions.json</code>。</div></div>

<h2>③ 逐边 ρ（standard/contrastive）与决策着色</h2>
<div class="card"><canvas id="cEdges" width="920" height="330"></canvas>
<div class="note">绿色=至少一个决策层策略 apply；灰色=全部 abstain；橙色=LLM 判 rank_only。SECCM 三条边（ρ 0.04–0.51）是 frozen 与 LLM 主动放弃正 ρ 的唯一区域——也是 repo 记录的负迁移边界。</div></div>

<h2>④ 结论</h2>
<div class="card">
<ol style="margin:6px 0 0 18px;padding:0;font-size:.88rem">
<li><b>决策层消除伤害边且不牺牲均值。</b>Frozen 与 LLM 策略 0 伤害边（朴素迁移 8 条），apply 精度 100%，均值 ρ 与朴素迁移无显著差异（frozen Δ=−0.004, 95% CI [−0.073, +0.066]）。</li>
<li><b>Learned GBM 在 30 条边上不及规则与 LLM。</b>3 条伤害边、apply 精度 70.6%——小样本 LOPO 训练不足以逼近规则，支持"决策层需要推理/先验而非纯拟合"。</li>
<li><b>LLM 用 rank_only 表达不确定性。</b>LLM 是唯一使用三档决策的策略（10/10/10），把 SECCM 边界边与 specgen_C 降级为 rank_only——正是 falsification-gated contract 想要的"部分主张"。</li>
<li><b>覆盖度几何是强信号。</b>coverage≥0.5 且 source_fit≥0.85 的 8 条边全部 ρ≥0.27；coverage&lt;0.15 的 4 条边全部 ρ≤0.33 且一半为负。</li>
</ol>
</div>

<div class="note" style="margin-top:18px">产物：<code>analysis/catalyst_attention/policy_transfer.py</code> · <code>learned_policy.py</code> · <code>run_policy_transfer_benchmark.py</code> · <code>run_policy_comparison.py</code> · 测试 20 项全过 · manifest SHA 见 policy_comparison.json</div>
</div>

<script>
const EDGES = __EDGES__;
const DECISIONS = __DECISIONS__;
const POLICIES = __POLICIES__;

const order = ["frozen_threshold","learned_gbm_lopo","llm_policy","always_transfer","always_abstain"];
const label = {frozen_threshold:"Frozen 规则",learned_gbm_lopo:"Learned GBM (LOPO)",llm_policy:"LLM (Claude 盲评)",always_transfer:"朴素全迁移",always_abstain:"全弃权"};
let th = "<tr><th>策略</th><th>mean ρ</th><th>harm</th><th>miss</th><th>apply</th><th>rank</th><th>abstain</th></tr>";
for (const k of order) {
  const s = POLICIES[k];
  th += `<tr><td>${label[k]}</td><td class="${s.mean_realized_spearman>0?'pos':'neg'}">${s.mean_realized_spearman.toFixed(3)}</td>`+
    `<td class="${s.harm_edges>0?'neg':'pos'}">${s.harm_edges}</td><td>${s.missed_positive_edges}</td>`+
    `<td>${s.n_apply??'—'}</td><td>${s.n_rank_only??'—'}</td><td>${s.n_abstain??'—'}</td></tr>`;
}
document.getElementById("polTable").innerHTML = th;

const dClass = d => d==="apply"?"d-apply":d==="rank_only"?"d-rank":"d-abst";
const rhoC = v => v>0.25?"pos":v<0?"neg":"";
let eh = "<tr><th>边</th><th>cov</th><th>std ρ</th><th>contr ρ</th><th>ET ρ</th><th>frozen</th><th>learned</th><th>llm</th></tr>";
for (const e of EDGES) {
  const d = DECISIONS[e.pair];
  eh += `<tr><td>${e.pair}</td><td>${e.coverage.toFixed(2)}</td>`+
    `<td class="${rhoC(e.standard)}">${e.standard.toFixed(3)}</td>`+
    `<td class="${rhoC(e.contrastive)}">${e.contrastive.toFixed(3)}</td>`+
    `<td class="${rhoC(e.extra_trees)}">${e.extra_trees.toFixed(3)}</td>`+
    `<td class="${dClass(d.frozen_standard)}">${d.frozen_standard}</td>`+
    `<td class="${dClass(d.learned_standard)}">${d.learned_standard}</td>`+
    `<td class="${dClass(d.llm_standard)}">${d.llm_standard}</td></tr>`;
}
document.getElementById("edgeTable").innerHTML = eh;

function barChart(id, entries, fmt) {
  const c = document.getElementById(id), ctx = c.getContext("2d");
  const W=c.width,H=c.height,bw=(W-20)/entries.length;
  const max = Math.max(...entries.map(e=>Math.abs(e.v)))*1.15 || 1;
  ctx.clearRect(0,0,W,H);
  entries.forEach((e,i)=>{
    const h = Math.abs(e.v)/max*(H-56);
    const x = 10+i*bw+bw*0.18, y = H-30-h;
    ctx.fillStyle = e.color;
    ctx.fillRect(x,y,bw*0.64,Math.max(h,2));
    ctx.fillStyle = "#5c6875"; ctx.font = "10px sans-serif"; ctx.textAlign="center";
    ctx.fillText(fmt(e.v), x+bw*0.32, y-4);
    ctx.save(); ctx.translate(x+bw*0.32,H-24); ctx.rotate(-0.4);
    ctx.fillText(e.k,0,10); ctx.restore();
  });
}
const meanE = order.filter(k=>POLICIES[k].n_edges).map(k=>({k:label[k].split(" ")[0],v:POLICIES[k].mean_realized_spearman,
  color:POLICIES[k].harm_edges===0?"#1a7f5a":"#c0392b"}));
barChart("cMean",meanE,v=>v.toFixed(3));
const harmE = order.filter(k=>POLICIES[k].n_edges).map(k=>({k:label[k].split(" ")[0],v:POLICIES[k].harm_edges,
  color:POLICIES[k].harm_edges===0?"#1a7f5a":"#c0392b"}));
barChart("cHarm",harmE,v=>v);

(function(){
  const c=document.getElementById("cEdges"),ctx=c.getContext("2d");
  const W=c.width,H=c.height,top=20,bot=54,L=8;
  const n=EDGES.length,step=(W-L-8)/n;
  const vmax=0.8,vmin=-0.5,y=v=>top+(vmax-v)/(vmax-vmin)*(H-top-bot);
  ctx.strokeStyle="#e3e8ee";ctx.beginPath();ctx.moveTo(L,y(0));ctx.lineTo(W-4,y(0));ctx.lineWidth=1.5;ctx.stroke();
  EDGES.forEach((e,i)=>{
    const x=L+i*step+step/2,d=DECISIONS[e.pair];
    const anyApply=["frozen_standard","learned_standard","llm_standard"].some(k=>d[k]==="apply");
    const llmRank=d.llm_standard==="rank_only";
    const col=anyApply?"#1a7f5a":llmRank?"#b9770e":"#9aa5b1";
    for(const m of ["standard","contrastive"]){
      ctx.beginPath();ctx.arc(x+(m==="contrastive"?5:-5),y(e[m]),5,0,7);
      ctx.fillStyle=col+(m==="contrastive"?"99":"");ctx.fill();
      ctx.strokeStyle="#fff";ctx.stroke();
    }
    ctx.fillStyle="#5c6875";ctx.font="9px sans-serif";ctx.textAlign="center";
    ctx.save();ctx.translate(x,H-bot+8);ctx.rotate(-0.55);ctx.fillText(e.pair,0,8);ctx.restore();
  });
})();
</script>
</body>
</html>"""


def main() -> None:
    comparison = json.loads((RESULTS / "policy_comparison.json").read_text())
    bench = json.loads((RESULTS / "policy_transfer_benchmark.json").read_text())

    edges = [
        {
            "pair": e["pair"], "coverage": round(e["coverage"], 3),
            "mean_min_distance": round(e["mean_min_distance"], 3),
            "source_n": e["source_n"], "target_n": e["target_n"],
            "standard": round(e["standard_rho"], 3),
            "contrastive": round(e["contrastive_rho"], 3),
            "extra_trees": round(e["extra_trees_rho"], 3),
        }
        for e in bench["edges"]
    ]
    decisions: dict[str, dict[str, str]] = {}
    for pol, key in (("frozen", "frozen_manifest"), ("learned", "learned_manifest"), ("llm", "llm_manifest")):
        for e in comparison[key]["edges"]:
            decisions.setdefault(e["pair"], {})[f"{pol}_{e['method']}"] = e["decision"]
    policies = {
        name: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}
        for name, s in comparison["policies"].items()
    }

    html = (
        TEMPLATE
        .replace("__EDGES__", json.dumps(edges, ensure_ascii=False))
        .replace("__DECISIONS__", json.dumps(decisions, ensure_ascii=False))
        .replace("__POLICIES__", json.dumps(policies, ensure_ascii=False))
    )
    out = RESULTS / "policy_transfer_report.html"
    out.write_text(html)
    print(f"wrote {out} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
