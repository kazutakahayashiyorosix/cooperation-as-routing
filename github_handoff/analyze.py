import pandas as pd, numpy as np, json, collections
df=pd.read_parquet("data/events.parquet").sort_values("time",kind="stable").reset_index(drop=True)
def isbot(u): return u.endswith("[bot]") or u.endswith("-bot") or u.endswith("bot") and len(u)>3 and u[-4] in "-_"
H=np.timedelta64(72,"h")
part=collections.defaultdict(set); opened={}; closed={}
pending=collections.defaultdict(list)
repo_c=collections.Counter(); tot_c=collections.Counter()
h_to=collections.Counter(); h_resp=collections.Counter()
handoffs=[]; q=collections.deque()
T=df.time.values.astype("datetime64[ns]"); TY=df.type.values; AC=df.action.values; RP=df.repo.values
K=df.key.values; U=df.actor.values; AU=df.author.values; M=df.mentions.values
for i in range(len(df)):
    t=T[i]
    while q and handoffs[q[0]]["t"]+H<=t:
        h=handoffs[q.popleft()]; h_to[h["b"]]+=1
        if h["resp_t"] is not None and h["resp_t"]-h["t"]<=H: h_resp[h["b"]]+=1
    k=K[i]; u=U[i]
    if TY[i]=="Issues":
        if AC[i]=="opened": opened[k]=t; part[k].add(u)
        elif AC[i]=="closed" and k not in closed: closed[k]=t
        continue
    if isbot(u): continue
    if AU[i]: part[k].add(AU[i])
    for j in pending.pop((k,u),[]):
        if handoffs[j]["resp_t"] is None: handoffs[j]["resp_t"]=t
    if M[i]:
        for b in M[i].split(";"):
            b=b.strip()
            if not b or b==u or isbot(b) or b in part[k]: continue
            handoffs.append(dict(issue=k,repo=RP[i],a=u,b=b,t=t,resp_t=None,
                b_repo=repo_c[(b,RP[i])],b_tot=tot_c[b],b_hto=h_to[b],b_hresp=h_resp[b],
                a_tot=tot_c[u],in_window=k in opened))
            j=len(handoffs)-1; pending[(k,b)].append(j); q.append(j); part[k].add(b)
    part[k].add(u); repo_c[(u,RP[i])]+=1; tot_c[u]+=1
h=pd.DataFrame(handoffs)
h["resp72"]=h.resp_t.notna() & ((h.resp_t-h.t)<=H)
h.to_parquet("data/handoffs.parquet")
iss=pd.DataFrame({"key":list(opened)}); iss["open_t"]=iss.key.map(opened); iss["close_t"]=iss.key.map(closed)
iss.to_parquet("data/issues.parquet")
print("handoffs",len(h),"resp72",round(h.resp72.mean(),3),"unique targets",h.b.nunique())
