import json
pts = json.load(open('/tmp/data/points.json'))
URLS = {
 'ESTM thermoelectrics':'https://github.com/KRICT-DATA/SIMD',
 'AqSolDB solubility':'https://github.com/mcsorkun/AqSolDB',
 'Photoswitches':'https://github.com/Ryan-Rhys/The-Photoswitch-Dataset',
 'FreeSolv hydration':'https://github.com/MobleyLab/FreeSolv',
 'OCx24 electrocatalysts':'https://fair-chem.github.io/core/datasets/ocx24.html',
 'MPEA alloys (Borg)':'https://doi.org/10.1038/s41597-020-00768-9',
 'IUPAC pKa':'https://github.com/IUPAC/Dissociation-Constants',
}
COLORS = ['#e91e8c','#1565c0','#7e57c2','#2e7d32','#ff8f00','#00b8d4','#c62828']
ds_names = sorted(set(p['ds'] for p in pts))
groups=[{'name':n,'color':COLORS[i%len(COLORS)],'n':sum(1 for p in pts if p['ds']==n),'url':URLS.get(n,'')} for i,n in enumerate(ds_names)]
payload=json.dumps({'points':pts,'groups':groups,'meta':{'count':len(pts),'nds':len(groups)}},ensure_ascii=False)
html = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Unified cross-database similarity map (data-point level)</title>
<style>
 body{font-family:Segoe UI,system-ui,sans-serif;margin:0;background:#fff;color:#222}
 #wrap{display:flex;height:100vh}#cv{flex:1}
 #side{width:265px;padding:14px;border-left:1px solid #e5e5e5;overflow-y:auto}
 h1{font-size:15px;margin:0 0 4px}.sub{color:#888;font-size:12px;margin-bottom:10px}
 .leg{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:4px 6px;border-radius:6px;cursor:pointer}
 .leg:hover{background:#f2f2f2}.leg.off{opacity:.3}
 .dot{width:11px;height:11px;border-radius:50%;flex:none}
 .cnt{color:#999;margin-left:auto}
 #tip{position:fixed;display:none;max-width:320px;background:#222;color:#fff;padding:8px 10px;border-radius:8px;font-size:12px;pointer-events:none;z-index:9}
 #tip b{color:#ffd54f}
</style></head><body><div id="wrap"><canvas id="cv"></canvas><div id="side">
<h1>Unified cross-database similarity map</h1>
<div class="sub" id="meta"></div><div id="legend"></div>
<div class="sub" style="margin-top:10px">Each point = one experimental sample/measurement.<br>
Element-composition features (formula / SMILES) &rarr; PCA &rarr; t-SNE.<br>
Hover = details &middot; click legend = toggle &middot; click point = open source dataset.</div>
</div></div><div id="tip"></div>
<script>
const DATA=__P__;
const cv=document.getElementById('cv'),ctx=cv.getContext('2d'),tip=document.getElementById('tip');
const off=new Set();const color={},url={};
document.getElementById('meta').textContent=DATA.meta.count.toLocaleString()+' experimental data points · '+DATA.meta.nds+' databases';
const leg=document.getElementById('legend');
DATA.groups.forEach(g=>{color[g.name]=g.color;url[g.name]=g.url;
 const d=document.createElement('div');d.className='leg';
 d.innerHTML='<span class="dot" style="background:'+g.color+'"></span>'+g.name+'<span class="cnt">'+g.n.toLocaleString()+'</span>';
 d.onclick=()=>{off.has(g.name)?off.delete(g.name):off.add(g.name);d.classList.toggle('off');draw();};
 leg.appendChild(d);});
let W,H,sx,sy;
function fit(){W=cv.clientWidth;H=cv.clientHeight;cv.width=W*devicePixelRatio;cv.height=H*devicePixelRatio;
 ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
 const xs=DATA.points.map(p=>p.x),ys=DATA.points.map(p=>p.y);
 const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),pad=50;
 sx=x=>pad+(x-x0)/(x1-x0)*(W-2*pad);sy=y=>pad+(y-y0)/(y1-y0)*(H-2*pad);}
function draw(){ctx.clearRect(0,0,W,H);
 ctx.font='13px Segoe UI';ctx.fillStyle='#555';
 ctx.fillText('Unified cross-database similarity map — experimental data points',18,26);
 DATA.points.forEach(p=>{if(off.has(p.ds))return;
  ctx.beginPath();ctx.arc(sx(p.x),sy(p.y),2.1,0,7);
  ctx.fillStyle=color[p.ds]+'99';ctx.fill();});}
function nearest(mx,my){let b=null,bd=100;DATA.points.forEach(p=>{if(off.has(p.ds))return;
 const dx=sx(p.x)-mx,dy=sy(p.y)-my,d=dx*dx+dy*dy;if(d<bd){bd=d;b=p;}});return b;}
cv.onmousemove=ev=>{const p=nearest(ev.clientX,ev.clientY);
 if(!p){tip.style.display='none';cv.style.cursor='default';return;}
 cv.style.cursor='pointer';tip.style.display='block';
 tip.style.left=Math.min(ev.clientX+14,innerWidth-330)+'px';tip.style.top=(ev.clientY+14)+'px';
 tip.innerHTML='<b>'+p.label+'</b><br>'+p.ds+(p.prop?('<br>'+p.prop):'');};
cv.onclick=ev=>{const p=nearest(ev.clientX,ev.clientY);if(p&&url[p.ds])window.open(url[p.ds],'_blank');};
addEventListener('resize',()=>{fit();draw();});fit();draw();
</script></body></html>'''
html=html.replace('__P__',payload)
out='/sessions/vigilant-vibrant-cannon/mnt/Collective exp dataset/datapoint_map.html'
open(out,'w',encoding='utf-8').write(html)
print('wrote',out,len(html)//1024,'KB')
