import json, matplotlib; matplotlib.use("Agg"); matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt
d = json.load(open("results/engagement_sweep.json"))
lab = {"none": "No credit", "delivery": "Delivery credit", "effective": "Effective-forward credit"}
col = {"none": "#7a7a7a", "delivery": "#c0504d", "effective": "#1f5fa8"}
mk = {"Kleinberg lattice": "s", "Watts-Strogatz": "o", "Barabasi-Albert": "^"}
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for i, kk in enumerate(["5", "inf"]):
    a = ax[i]
    for g in mk:
        for r in lab:
            v = d[g][r][kk]
            x = [v[e]["R_branch"][0] for e in v]; y = [v[e]["resolution"][0] for e in v]
            a.scatter(x, y, c=col[r], marker=mk[g], s=16, alpha=.85, label=lab[r] if g == "Watts-Strogatz" else None)
    a.axvline(1, ls=":", color="k", lw=.8)
    a.set_xlabel("branching ratio $R$")
    a.set_title("attention fatigue $\\kappa=5$" if kk == "5" else "no fatigue", fontsize=9)
ax[0].set_ylabel("share resolved"); ax[0].legend(fontsize=7, frameon=False)
plt.tight_layout(); plt.savefig("fig_branch.pdf"); plt.savefig("fig_branch.png", dpi=150)
