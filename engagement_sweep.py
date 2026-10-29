"""Where does the credit rule matter? Sweep base engagement e0 from the GitHub-calibrated
value (0.25) to 1, keeping the calibrated dilution delta and m = GitHub value.
kappa = 5 (attention fatigue) and no fatigue. 20 seeds x 3 graphs x 3 rules.
Output: results/engagement_sweep.json"""
import json, sys, numpy as np
from multiprocessing import Pool
from routing_sim import run_epoch, P, RULES, graphs
C = json.load(open("results/calibrated.json"))["fit"]
E0 = [0.25, 0.4, 0.55, 0.7, 0.85, 1.0]; KAPPA = [5.0, 1e9]
def job(args):
    s, e0, kap = args
    p = dict(P); p.update(e0=e0, delta=C["delta"], kappa=kap)
    out = []
    for gname, G in graphs(s).items():
        for rule in RULES:
            r = run_epoch(G, rule, C["m_github"], np.random.default_rng(70000 + 100 * s + RULES.index(rule)), p)
            out.append((gname, rule, e0, kap, r["resolution"], r["deliveries_per_resolution"]))
    return out
if __name__ == "__main__":
    tasks = [(s, e, k) for s in range(20) for e in E0 for k in KAPPA]
    with Pool(2) as pool: rows = [x for chunk in pool.map(job, tasks) for x in chunk]
    def ci(v):
        v = np.array(v, float); v = v[np.isfinite(v)]
        return [float(v.mean()), float(1.96 * v.std(ddof=1) / np.sqrt(len(v)))] if len(v) > 1 else [float("nan")] * 2
    res = {}
    for g in {r[0] for r in rows}:
        for rule in RULES:
            for k in KAPPA:
                kk = "inf" if k > 1e8 else "5"
                res.setdefault(g, {}).setdefault(rule, {})[kk] = {str(e): {"resolution": ci([r[4] for r in rows if r[:4] == (g, rule, e, k)]),
                    "deliveries_per_resolution": ci([r[5] for r in rows if r[:4] == (g, rule, e, k)])} for e in E0}
    json.dump(res, open("results/engagement_sweep.json", "w"), indent=1)
    for g in res:
        for rule in RULES:
            for kk in ["5", "inf"]:
                print(g, rule, kk, [round(res[g][rule][kk][str(e)]["resolution"][0], 3) for e in E0])
