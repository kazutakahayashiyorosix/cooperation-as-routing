# Cooperation as Routing — simulation code

Agent-based comparison of three credit rules for intermediaries who forward help requests
(no credit, delivery credit, effective-forward credit) on Kleinberg-lattice, Watts–Strogatz
and Barabási–Albert networks with attention fatigue.

Paper: K. Hayashi, *Cooperation as Routing: A Network-Layer Formalization of How Help Propagates Through Social Networks* (manuscript under review).

```
pip install networkx numpy matplotlib
python3 routing_sim.py   # main experiment -> results/sim_results.json
python3 sens.py          # sensitivity (c, kappa) -> results/sensitivity.json
python3 make_fig.py      # figure
```

![results](fig_sim.png)

License: see LICENSE
