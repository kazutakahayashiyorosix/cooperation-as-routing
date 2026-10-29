"""
routing_sim.py -- agent-based illustration for "Cooperation as Routing".

Compares three credit rules for intermediaries who cannot help:
  none      : no credit; forwarding only from intrinsic motivation m
  delivery  : one unit per recipient who receives the request
  effective : one unit per forward whose recipient subsequently acts
Each intermediary is myopic: it adds a recipient v iff expected credit for v
exceeds a per-recipient forwarding cost c. Recipients suffer attention
fatigue: the probability of engaging with a delivered request falls with the
number of requests already delivered to them in the epoch.

Usage: python3 routing_sim.py  -> results/sim_results.json, fig_sim.pdf/png
"""
import json, os, collections
import numpy as np
import networkx as nx

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
RULES = ["none", "delivery", "effective"]
P = dict(c=0.3, L=1.5, sigma=0.5, kappa=5.0, ttl=10, requests=300, cap_frac=0.5,
         e0=1.0, delta=None)  # e0: base engagement; delta: dilution when one sender names k recipients at once (None = off)


def graphs(seed):
    g1 = nx.navigable_small_world_graph(30, p=1, q=1, r=2, dim=2, seed=seed).to_undirected()
    g1 = nx.convert_node_labels_to_integers(g1)
    g2 = nx.watts_strogatz_graph(900, 8, 0.1, seed=seed)
    g3 = nx.barabasi_albert_graph(900, 4, seed=seed)
    return {"Kleinberg lattice": g1, "Watts-Strogatz": g2, "Barabasi-Albert": g3}


def run_epoch(G, rule, m, rng, p=P):
    n = G.number_of_nodes()
    nbrs = {u: list(G.neighbors(u)) for u in G}
    load = np.zeros(n)
    stats = collections.Counter()
    hops_resolved = []
    deliv_by_hop = collections.Counter(); engaged_by_hop = collections.Counter()
    for _ in range(p["requests"]):
        t = int(rng.integers(n))
        capable = {t} | {v for v in nbrs[t] if rng.random() < p["cap_frac"]}
        dist = nx.multi_source_dijkstra_path_length(G, capable)  # hops to nearest capable node
        origin = int(rng.integers(n))
        while origin in capable:
            origin = int(rng.integers(n))
        seen = {origin}
        frontier = [(origin, 0, 1)]
        resolved = False
        # the origin posts and routes like an intermediary that is always engaged
        first = True
        while frontier and not resolved:
            nxt = []
            for u, h, k in frontier:
                if not first:
                    load[u] += 1
                    deliv_by_hop[h] += 1
                    engage = p.get("e0", 1.0) / (1.0 + load[u] / p["kappa"])
                    if p.get("delta"):
                        engage /= (1.0 + (k - 1) / p["delta"])
                    if rng.random() >= engage:
                        stats["drop_unengaged"] += 1
                        continue
                    engaged_by_hop[h] += 1
                    if u in capable:
                        resolved = True
                        hops_resolved.append(h)
                        break
                if h >= p["ttl"]:
                    continue
                cand = [v for v in nbrs[u] if v not in seen]
                if not cand:
                    stats["dead_end"] += 1
                    continue
                est = np.array([np.exp(-dist.get(v, 99) / p["L"]) for v in cand])
                est = est * np.exp(rng.normal(0, p["sigma"], len(cand)))
                est = np.clip(est, 0, 1)
                send = set()
                if rng.random() < m or first:
                    send.add(cand[int(np.argmax(est))])
                if rule == "delivery" and 1.0 > p["c"]:
                    send |= set(cand)
                elif rule == "effective":
                    send |= {v for v, e in zip(cand, est) if e > p["c"]}
                if not send:
                    stats["drop_engaged"] += 1
                    continue
                for v in send:
                    seen.add(v)
                    nxt.append((v, h + 1, len(send)))
                stats["deliveries"] += len(send)
            first = False
            frontier = nxt
        stats["resolved"] += int(resolved)
    R = p["requests"]
    return {
        "resolution": stats["resolved"] / R,
        "deliveries_per_request": stats["deliveries"] / R,
        "deliveries_per_resolution": stats["deliveries"] / max(stats["resolved"], 1),
        "median_hops": float(np.median(hops_resolved)) if hops_resolved else float("nan"),
        "mean_load": float(load.mean()),
        "drop_share": 1 - sum(engaged_by_hop.values()) / max(sum(deliv_by_hop.values()), 1),
        "hop2_per_hop1": deliv_by_hop[2] / max(deliv_by_hop[1], 1),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    ms = [0.2, 0.4, 0.6, 0.8]
    seeds = range(10)
    res = {}
    for s in seeds:
        for gname, G in graphs(s).items():
            for rule in RULES:
                for m in ms:
                    rng = np.random.default_rng(1000 * s + int(m * 100) + RULES.index(rule))
                    r = run_epoch(G, rule, m, rng)
                    res.setdefault(gname, {}).setdefault(rule, {}).setdefault(str(m), []).append(r)
    summ = {}
    for g in res:
        for rule in res[g]:
            for m in res[g][rule]:
                rows = res[g][rule][m]
                summ.setdefault(g, {}).setdefault(rule, {})[m] = {
                    k: [float(np.nanmean([r[k] for r in rows])), float(np.nanstd([r[k] for r in rows]))]
                    for k in rows[0]}
    json.dump({"params": P, "m_values": ms, "n_seeds": len(seeds), "summary": summ},
              open(os.path.join(OUT, "sim_results.json"), "w"), indent=1)
    for g in summ:
        for rule in RULES:
            print(g, rule, {m: (round(v["resolution"][0], 3), round(v["deliveries_per_resolution"][0], 1),
                                v["median_hops"][0]) for m, v in summ[g][rule].items()})


if __name__ == "__main__":
    main()
