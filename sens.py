import json, numpy as np, networkx as nx
from routing_sim import run_epoch, P, RULES
out={}
for kappa in [5.0, 20.0, 1e9]:
  for c in [0.1,0.3,0.5]:
    p=dict(P); p["kappa"]=kappa; p["c"]=c
    for rule in RULES:
      rows=[]
      for s in range(5):
        G=nx.watts_strogatz_graph(900,8,0.1,seed=s)
        rows.append(run_epoch(G,rule,0.6,np.random.default_rng(77+s),p))
      k=f"kappa={'inf' if kappa>1e8 else kappa},c={c},{rule}"
      out[k]={m:float(np.mean([r[m] for r in rows])) for m in rows[0]}
      print(k, round(out[k]["resolution"],3), round(out[k]["deliveries_per_resolution"],1), flush=True)
json.dump(out,open("results/sensitivity.json","w"),indent=1)
