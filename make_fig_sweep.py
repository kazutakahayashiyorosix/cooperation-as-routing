import json, matplotlib; matplotlib.use("Agg"); matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt
d = json.load(open("results/engagement_sweep.json"))
G = ["Kleinberg lattice", "Watts-Strogatz", "Barabasi-Albert"]; R = ["none", "delivery", "effective"]
lab = {"none": "No credit", "delivery": "Delivery credit", "effective": "Effective-forward credit"}
col = {"none": "#7a7a7a", "delivery": "#c0504d", "effective": "#1f5fa8"}
fig, ax = plt.subplots(2, 3, figsize=(10, 5.6), sharex=True)
for j, g in enumerate(G):
    for i, kk in enumerate(["5", "inf"]):
        a = ax[i, j]
        for r in R:
            e = sorted(d[g][r][kk], key=float)
            x = [float(v) for v in e]; y = [d[g][r][kk][v]["resolution"][0] for v in e]; ci = [d[g][r][kk][v]["resolution"][1] for v in e]
            a.errorbar(x, y, yerr=ci, color=col[r], marker="o", ms=3, capsize=2, label=lab[r])
        a.axvline(0.25, ls=":", color="k", lw=0.8)
        a.set_title(f"{g}, " + ("fatigue $\\kappa=5$" if kk == "5" else "no fatigue"), fontsize=9)
        if j == 0: a.set_ylabel("share resolved")
        if i == 1: a.set_xlabel("base engagement $e_0$")
ax[0, 0].legend(fontsize=7, frameon=False)
plt.tight_layout(); plt.savefig("fig_sweep.pdf"); plt.savefig("fig_sweep.png", dpi=150)
