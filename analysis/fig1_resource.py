import json, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
cat=json.load(open("../catalog/catalog.json",encoding="utf-8"))["entries"]
fig,ax=plt.subplots(1,3,figsize=(15,4.2))
dt=Counter(e["data_type"] for e in cat)
ax[0].pie([dt.get("experimental",0),dt.get("mixed",0)],labels=[f"experimental\n({dt.get('experimental',0)})",f"mixed\n({dt.get('mixed',0)})"],
          colors=["#2e7d32","#ff8f00"],autopct="%1.0f%%",startangle=90,wedgeprops=dict(width=.45))
ax[0].set_title(f"a) Catalog: {len(cat)} experimental databases\n(computational-only excluded by policy)")
dom=Counter(e["subdomain"] for e in cat)
top=dict(sorted(dom.items(),key=lambda x:-x[1])[:12][::-1])
ax[1].barh(list(top.keys()),list(top.values()),color="#1565c0")
ax[1].set_title("b) Coverage by sub-domain (top 12)"); ax[1].tick_params(labelsize=7); ax[1].set_xlabel("databases")
# data lake bar
lake={"TE":26025,"pKa":24017,"OpenPoly":20748,"AqSolDB":9982,"ISODB":8000,"Cat(OCx24)":7812,"Alloy(MPEA)":7725,"FreeSolv":642,"SolidElec":599,"Switch":405}
ax[2].bar(range(len(lake)),list(lake.values()),color="#7e57c2")
ax[2].set_xticks(range(len(lake))); ax[2].set_xticklabels(list(lake.keys()),rotation=45,ha="right",fontsize=7)
ax[2].set_yscale("log"); ax[2].set_ylabel("measurements (log)")
ax[2].set_title("c) Unified data lake: 105,955 measurements\n10 datasets · 319 properties · 1 schema")
plt.tight_layout(); plt.savefig("fig1_resource.png",dpi=200); print("saved fig1_resource.png")
