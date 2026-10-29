import pandas as pd, numpy as np, json
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
h=pd.read_parquet("data/handoffs.parquet"); h["t"]=pd.to_datetime(h.t,utc=True); h["resp_t"]=pd.to_datetime(h.resp_t,utc=True)
h=h.sort_values("t").reset_index(drop=True)
H72=pd.Timedelta(hours=72)
out={}
# hop depth: a handoff whose sender was earlier a handoff target in the same issue is hop k+1
first_in=h.groupby(["issue","b"]).t.min()
depth={}
dep=[]
for r in h.itertuples():
    d=depth.get((r.issue,r.a),0)+1
    dep.append(d)
    if (r.issue,r.b) not in depth: depth[(r.issue,r.b)]=d
h["hop"]=dep
out["hop_distribution"]=h.hop.clip(upper=4).value_counts().sort_index().to_dict()
# action of each target within 72h: DROP / ACK only / ACK+FORWARD (forwarded to a new person)
fw=h[["issue","a","t"]].rename(columns={"a":"b","t":"ft"})
m=h[["issue","b","t","resp72"]].merge(fw,on=["issue","b"],how="left")
m["fwd72"]=(m.ft>m.t)&(m.ft-m.t<=H72)
g=m.groupby(["issue","b","t"]).agg(resp=("resp72","first"),fwd=("fwd72","any")).reset_index()
act=np.where(~g.resp,"DROP",np.where(g.fwd,"ACK+FORWARD","ACK"))
out["target_actions"]=pd.Series(act).value_counts(normalize=True).round(3).to_dict()
out["n_handoffs"]=len(g)
# chains end mostly by drop?
# per-recipient uptake vs number of new people named in the same comment
h["grp"]=h.issue+"|"+h.a+"|"+h.t.astype(str)
h["k"]=h.groupby("grp").b.transform("size")
out["uptake_by_k"]=h.groupby(h.k.clip(upper=4)).resp72.agg(["mean","size"]).round(3).reset_index().values.tolist()
# routing skill: sender's past effective-forward rate (causal, resolved before t)
h=h.sort_values("t").reset_index(drop=True)
done_sent={}; eff={}; pend=[]; import collections
q=collections.deque(); s_n=[]; s_e=[]
for i,r in enumerate(h.itertuples()):
    while q and h.t.iat[q[0]]+H72<=r.t:
        j=q.popleft(); a=h.a.iat[j]; done_sent[a]=done_sent.get(a,0)+1; eff[a]=eff.get(a,0)+int(h.resp72.iat[j])
    s_n.append(done_sent.get(r.a,0)); s_e.append(eff.get(r.a,0)); q.append(i)
h["a_sent"]=s_n; h["a_eff"]=s_e
L=np.log1p
for c in ["b_repo","b_tot","b_hto","b_hresp","a_sent","a_eff"]: h["f_"+c]=L(h[c])
T=lambda s: pd.Timestamp(s,tz="UTC")
tr=h[(h.t>=T("2024-03-08"))&(h.t<T("2024-03-22"))]; te=h[(h.t>=T("2024-03-22"))&(h.t<T("2024-03-29"))]
FA=["f_b_repo","f_b_tot","f_b_hto","f_b_hresp"]; FB=FA+["f_a_sent","f_a_eff"]
res={}
for n,f in (("target_records",FA),("plus_sender_routing_record",FB)):
    mdl=LogisticRegression(max_iter=1000).fit(tr[f],tr.resp72); p=mdl.predict_proba(te[f])[:,1]
    res[n]={"auc":round(roc_auc_score(te.resp72,p),3),"coef":dict(zip(f,np.round(mdl.coef_[0],3)))}
out["sender_skill"]=res
s3=h[h.a_sent>=3].copy(); s3["rate"]=(s3.a_eff+1)/(s3.a_sent+2)
out["uptake_by_sender_rate"]=s3.groupby(pd.cut(s3.rate,[0,.1,.2,.4,1.01]),observed=True).resp72.agg(["mean","size"]).round(3).reset_index().astype(str).values.tolist()
print(json.dumps(out,indent=1,default=str)); json.dump(out,open("data/routing_tests.json","w"),indent=1,default=str)
