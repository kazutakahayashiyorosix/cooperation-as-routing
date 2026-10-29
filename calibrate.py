"""Calibrate the routing simulation to GitHub issue handoffs (github_handoff/ results) and rerun.
e0, delta: fitted to per-recipient uptake when a comment names k = 1, 2, 3 new people.
m: share of engaged recipients who forward further (ACK+FORWARD / (ACK + ACK+FORWARD)).
Outputs results/calibrated.json."""
import json, os, time, numpy as np, networkx as nx
from scipy.optimize import least_squares
from routing_sim import run_epoch, P, RULES, graphs
G = json.load(open("github_handoff/routing_tests.json"))
k = np.array([1, 2, 3]); y = np.array([float(r[1]) for r in G["uptake_by_k"][:3]])
fit = least_squares(lambda th: th[0] / (1 + (k - 1) / th[1]) - y, x0=[0.25, 2.0], bounds=([0, 0.1], [1, 50]))
e0, delta = [float(v) for v in fit.x]
a = G["target_actions"]; m_gh = a["ACK+FORWARD"] / (a["ACK"] + a["ACK+FORWARD"])
out = {"fit": {"e0": e0, "delta": delta, "uptake_obs": y.tolist(),
               "uptake_fit": (e0 / (1 + (k - 1) / delta)).tolist(), "m_github": m_gh}}
base = dict(P); base.update(e0=e0, delta=delta, kappa=1e9)
ms = [round(m_gh, 3), 0.2, 0.4]; seeds = range(20)
res = {}
t0 = time.time()
for s in seeds:
    for gname, Gr in graphs(s).items():
        for rule in RULES:
            for m in ms:
                rng = np.random.default_rng(5000 + 1000 * s + int(m * 1000) + RULES.index(rule))
                r = run_epoch(Gr, rule, m, rng, base)
                res.setdefault(gname, {}).setdefault(rule, {}).setdefault(str(m), []).append(r)
out["runtime_s_main"] = time.time() - t0
def ci(v):
    v = np.array(v, float); v = v[~np.isnan(v)]
    return [float(v.mean()), float(1.96 * v.std(ddof=1) / np.sqrt(len(v)))]
out["summary"] = {g: {r: {m: {k2: ci([x[k2] for x in rows]) for k2 in rows[0]} for m, rows in d2.items()} for r, d2 in d1.items()} for g, d1 in res.items()}
# sensitivity of the calibrated comparison to e0, delta, kappa (Watts-Strogatz, m = GitHub value)
sens = {}
for e in [e0 * 0.5, e0, min(1, e0 * 2)]:
    for dl in [delta / 2, delta, delta * 2]:
        for kap in [5.0, 1e9]:
            p = dict(base); p.update(e0=e, delta=dl, kappa=kap)
            row = {}
            for rule in RULES:
                v = [run_epoch(nx.watts_strogatz_graph(900, 8, 0.1, seed=s), rule, m_gh, np.random.default_rng(900 + s), p) for s in range(8)]
                row[rule] = [float(np.mean([x["resolution"] for x in v])), float(np.mean([x["deliveries_per_resolution"] for x in v]))]
            sens[f"e0={e:.3f},delta={dl:.2f},kappa={'inf' if kap > 1e8 else kap}"] = row
out["sensitivity"] = sens
# scaling: Watts-Strogatz n = 900, 3600 (runtime and result)
scal = {}
for n in [900, 3600]:
    t1 = time.time(); v = {}
    for rule in RULES:
        rows = [run_epoch(nx.watts_strogatz_graph(n, 8, 0.1, seed=s), rule, m_gh, np.random.default_rng(300 + s), base) for s in range(5)]
        v[rule] = ci([x["resolution"] for x in rows])
    v["runtime_s"] = time.time() - t1; scal[str(n)] = v
out["scaling"] = scal
os.makedirs("results", exist_ok=True)
json.dump(out, open("results/calibrated.json", "w"), indent=1)
print(json.dumps(out["fit"], indent=1)); print("runtime", out["runtime_s_main"])
for g in out["summary"]:
    for r in RULES:
        print(g, r, {m: (round(v["resolution"][0], 3), round(v["resolution"][1], 3), round(v["deliveries_per_resolution"][0], 1), round(v["drop_share"][0], 3), round(v["hop2_per_hop1"][0], 3)) for m, v in out["summary"][g][r].items()})
print(json.dumps(scal, indent=1))
