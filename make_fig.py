import json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
d=json.load(open("results/sim_results.json")); S=d["summary"]; ms=d["m_values"]
gs=["Kleinberg lattice","Watts-Strogatz","Barabasi-Albert"]
sty={"none":("#888888","o","No credit"),"delivery":("#c0504d","s","Delivery credit"),"effective":("#1f5fa0","^","Effective-forward credit")}
fig,ax=plt.subplots(2,3,figsize=(10,5.6),sharex=True)
for j,g in enumerate(gs):
  for r,(col,mk,lab) in sty.items():
    y=[S[g][r][str(m)]["resolution"][0] for m in ms]; e=[S[g][r][str(m)]["resolution"][1] for m in ms]
    ax[0,j].errorbar(ms,y,yerr=e,color=col,marker=mk,label=lab,capsize=2)
    y=[S[g][r][str(m)]["deliveries_per_resolution"][0] for m in ms]
    ax[1,j].plot(ms,y,color=col,marker=mk)
  ax[0,j].set_title(g.replace("Barabasi","Barabási"),fontsize=10)
  ax[1,j].set_yscale("log"); ax[1,j].set_xlabel("intrinsic forwarding probability $m$")
  ax[0,j].set_ylim(0,0.4)
ax[0,0].set_ylabel("share of requests resolved"); ax[1,0].set_ylabel("deliveries per resolved request")
ax[0,0].legend(fontsize=8,frameon=False,loc="upper left")
plt.tight_layout(); plt.savefig("fig_sim.pdf"); plt.savefig("fig_sim.png",dpi=200)
