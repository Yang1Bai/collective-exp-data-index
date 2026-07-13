"""Generate catalog_map.html - an interactive similarity map of the catalog.

Every database entry is embedded from its text (name + description + tags +
subdomain) via TF-IDF; classical MDS (kernel PCA on the cosine-similarity
Gram matrix, pure stdlib) projects entries to 2D. Points are colored by
thematic group with confidence ellipses, hover tooltips, click-through to
each database, and group toggles.

Regenerate after every catalog change (build_exports.py calls this):
    python scripts/build_map.py
"""
from __future__ import annotations

import json
import math
import random
import re

import common

OUT_HTML = common.ROOT + "/catalog_map.html"

GROUPS = {
    "General & infrastructure": ["general-properties", "data-infrastructure",
                                 "benchmark-ml"],
    "Structures & spectra": ["crystallography", "mofs-porous", "magnetic",
                             "spectra-exp", "spectroscopy"],
    "Catalysis": ["catalysis", "electrocatalysis-exp"],
    "Energy devices": ["batteries", "photovoltaics", "thermoelectrics",
                       "superconductors"],
    "HTE & self-driving labs": ["high-throughput-exp", "hte-synthesis",
                                "lab-automation", "sdl-benchmarks"],
    "Molecules & reactions": ["reactions", "molecular-properties", "bioactivity",
                              "quantum-chem", "solubility", "pka", "solvation",
                              "electrochemistry", "optical-properties",
                              "kinetics", "thermochemistry", "ionic-liquids",
                              "physical-properties"],
    "Polymers & organics": ["polymers", "organic-electronics", "glasses"],
    "Alloys & structural": ["alloys-mechanical", "additive-manufacturing",
                            "thermophysical", "2d-materials"],
}
COLORS = ["#00b8d4", "#ff8f00", "#e91e8c", "#6a1b9a",
          "#1565c0", "#2e7d32", "#c62828", "#7e57c2"]

STOP = set("a an and are as at based by data database dataset datasets for from "
           "in including is it its of on or over than that the this to via with "
           "which were was be been has have their more most each per used using "
           "these those such into across also".split())


def group_of(subdomain: str) -> str:
    for g, subs in GROUPS.items():
        if subdomain in subs:
            return g
    return "General & infrastructure"


def tokenize(entry: dict) -> list[str]:
    text = " ".join([entry.get("name", ""), entry.get("description", ""),
                     " ".join(entry.get("tags", []) * 3),
                     (entry.get("subdomain", "") + " ") * 4,
                     entry.get("domain", "")])
    toks = [t for t in re.split(r"[^a-z0-9]+", text.lower())
            if len(t) > 2 and t not in STOP and not t.isdigit()]
    return toks


def tfidf_vectors(entries: list) -> list[dict]:
    docs = [tokenize(e) for e in entries]
    n = len(docs)
    df: dict[str, int] = {}
    for d in docs:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    vecs = []
    for d in docs:
        tf: dict[str, float] = {}
        for t in d:
            tf[t] = tf.get(t, 0) + 1
        v = {t: (1 + math.log(c)) * math.log(n / df[t])
             for t, c in tf.items() if df[t] > 1}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({t: x / norm for t, x in v.items()})
    return vecs


def mds_2d(vecs: list[dict]) -> list[tuple[float, float]]:
    n = len(vecs)
    # cosine Gram matrix
    G = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            s = 0.0
            a, b = vecs[i], vecs[j]
            if len(b) < len(a):
                a, b = b, a
            for t, x in a.items():
                y = b.get(t)
                if y:
                    s += x * y
            G[i][j] = G[j][i] = s
    # double-centering: B = J G J
    row = [sum(r) / n for r in G]
    tot = sum(row) / n
    B = [[G[i][j] - row[i] - row[j] + tot for j in range(n)] for i in range(n)]

    def power_iter(mat, seed):
        rnd = random.Random(seed)
        v = [rnd.uniform(-1, 1) for _ in range(n)]
        lam = 0.0
        for _ in range(200):
            w = [sum(mat[i][k] * v[k] for k in range(n)) for i in range(n)]
            lam = math.sqrt(sum(x * x for x in w)) or 1e-12
            v = [x / lam for x in w]
        return lam, v

    l1, v1 = power_iter(B, 1)
    B2 = [[B[i][j] - l1 * v1[i] * v1[j] for j in range(n)] for i in range(n)]
    l2, v2 = power_iter(B2, 2)
    return [(v1[i] * math.sqrt(max(l1, 0)), v2[i] * math.sqrt(max(l2, 0)))
            for i in range(n)]


def ellipse(points: list[tuple[float, float]]) -> dict | None:
    if len(points) < 3:
        return None
    n = len(points)
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    sxx = sum((p[0] - mx) ** 2 for p in points) / n
    syy = sum((p[1] - my) ** 2 for p in points) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in points) / n
    tr, det = sxx + syy, sxx * syy - sxy * sxy
    disc = math.sqrt(max(tr * tr / 4 - det, 0))
    l1, l2 = tr / 2 + disc, tr / 2 - disc
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    return {"cx": mx, "cy": my, "rx": 1.9 * math.sqrt(max(l1, 1e-9)),
            "ry": 1.9 * math.sqrt(max(l2, 1e-9)), "angle": ang}


def main() -> int:
    catalog = common.load_catalog()
    entries = common.entries_of(catalog)
    vecs = tfidf_vectors(entries)
    coords = mds_2d(vecs)

    rnd = random.Random(42)
    pts = []
    for e, (x, y) in zip(entries, coords):
        g = group_of(e["subdomain"])
        pts.append({
            "x": x + rnd.uniform(-0.004, 0.004), "y": y + rnd.uniform(-0.004, 0.004),
            "name": e["name"], "group": g, "domain": e["domain"],
            "sub": e["subdomain"], "dt": e["data_type"],
            "url": e.get("homepage_url"),
            "desc": (e.get("description") or "")[:220],
        })
    groups = []
    for gi, g in enumerate(GROUPS):
        gp = [(p["x"], p["y"]) for p in pts if p["group"] == g]
        groups.append({"name": g, "color": COLORS[gi], "n": len(gp),
                       "ellipse": ellipse(gp)})

    payload = json.dumps({"points": pts, "groups": groups,
                          "meta": {"count": len(pts),
                                   "updated": catalog.get("updated", "")}},
                         ensure_ascii=False)

    html = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Collective Experimental Data Index - similarity map</title>
<style>
 body{font-family:Segoe UI,system-ui,sans-serif;margin:0;background:#fafafa;color:#222}
 #wrap{display:flex;height:100vh}
 #cv{flex:1}
 #side{width:250px;padding:14px;border-left:1px solid #e0e0e0;background:#fff;overflow-y:auto}
 h1{font-size:15px;margin:0 0 4px} .sub{color:#888;font-size:12px;margin-bottom:12px}
 .leg{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:4px 6px;
      border-radius:6px;cursor:pointer;user-select:none}
 .leg:hover{background:#f0f0f0} .leg.off{opacity:.3}
 .dot{width:11px;height:11px;border-radius:50%;flex:none}
 #tip{position:fixed;display:none;max-width:300px;background:#222;color:#fff;
      padding:8px 10px;border-radius:8px;font-size:12px;pointer-events:none;z-index:9}
 #tip b{color:#ffd54f} #tip .m{color:#aaa}
 input{width:100%;box-sizing:border-box;padding:6px 8px;margin:8px 0;border:1px solid #ddd;
       border-radius:6px;font-size:12.5px}
</style></head><body>
<div id="wrap"><canvas id="cv"></canvas>
<div id="side">
 <h1>Cross-database similarity map</h1>
 <div class="sub" id="meta"></div>
 <input id="q" placeholder="search databases...">
 <div id="legend"></div>
 <div class="sub" style="margin-top:10px">TF-IDF text similarity &middot; classical MDS<br>
 hover = details &middot; click = open database<br>
 regenerated by <code>scripts/build_map.py</code></div>
</div></div>
<div id="tip"></div>
<script>
const DATA = __PAYLOAD__;
const cv=document.getElementById('cv'),ctx=cv.getContext('2d'),tip=document.getElementById('tip');
const off=new Set(); let query='';
document.getElementById('meta').textContent=DATA.meta.count+' databases · updated '+DATA.meta.updated;
const leg=document.getElementById('legend');
DATA.groups.forEach(g=>{const d=document.createElement('div');d.className='leg';
 d.innerHTML='<span class="dot" style="background:'+g.color+'"></span>'+g.name+' ('+g.n+')';
 d.onclick=()=>{off.has(g.name)?off.delete(g.name):off.add(g.name);
  d.classList.toggle('off');draw();};leg.appendChild(d);});
const color={};DATA.groups.forEach(g=>color[g.name]=g.color);
let W,H,sx,sy;
function fit(){W=cv.clientWidth;H=cv.clientHeight;cv.width=W*devicePixelRatio;cv.height=H*devicePixelRatio;
 ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
 const xs=DATA.points.map(p=>p.x),ys=DATA.points.map(p=>p.y);
 const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
 const pad=60;sx=x=>pad+(x-x0)/(x1-x0||1)*(W-2*pad);sy=y=>pad+(y-y0)/(y1-y0||1)*(H-2*pad);}
function draw(){ctx.clearRect(0,0,W,H);
 ctx.font='13px Segoe UI';ctx.fillStyle='#555';
 ctx.fillText('Unified cross-database similarity map — Collective Experimental Data Index',18,26);
 DATA.groups.forEach(g=>{if(!g.ellipse||off.has(g.name))return;const e=g.ellipse;
  ctx.save();ctx.translate(sx(e.cx),sy(e.cy));ctx.rotate(-e.angle);
  ctx.beginPath();
  ctx.ellipse(0,0,Math.abs(sx(e.cx+e.rx)-sx(e.cx)),Math.abs(sy(e.cy+e.ry)-sy(e.cy)),0,0,7);
  ctx.fillStyle=g.color+'1f';ctx.fill();ctx.restore();});
 DATA.points.forEach(p=>{if(off.has(p.group))return;
  const hit=query&&(p.name.toLowerCase().includes(query)||p.sub.includes(query));
  ctx.beginPath();ctx.arc(sx(p.x),sy(p.y),hit?7:4.2,0,7);
  ctx.fillStyle=color[p.group]+(query&&!hit?'33':'e6');ctx.fill();
  if(p.dt==='experimental'){ctx.lineWidth=1.4;ctx.strokeStyle='#333';ctx.stroke();}});}
function nearest(mx,my){let best=null,bd=144;DATA.points.forEach(p=>{if(off.has(p.group))return;
 const dx=sx(p.x)-mx,dy=sy(p.y)-my,d=dx*dx+dy*dy;if(d<bd){bd=d;best=p;}});return best;}
cv.onmousemove=ev=>{const p=nearest(ev.clientX,ev.clientY);
 if(!p){tip.style.display='none';cv.style.cursor='default';return;}
 cv.style.cursor='pointer';tip.style.display='block';
 tip.style.left=Math.min(ev.clientX+14,innerWidth-320)+'px';tip.style.top=(ev.clientY+14)+'px';
 tip.innerHTML='<b>'+p.name+'</b><br><span class="m">'+p.domain+' · '+p.sub+' · '+p.dt+
  '</span><br>'+p.desc;};
cv.onclick=ev=>{const p=nearest(ev.clientX,ev.clientY);if(p&&p.url)window.open(p.url,'_blank');};
document.getElementById('q').oninput=ev=>{query=ev.target.value.toLowerCase();draw();};
addEventListener('resize',()=>{fit();draw();});fit();draw();
</script></body></html>"""
    html = html.replace("__PAYLOAD__", payload)
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"Wrote catalog_map.html ({len(pts)} points, {len(groups)} groups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
