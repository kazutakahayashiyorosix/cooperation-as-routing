import pandas as pd, glob, gzip
cols=["type","time","repo","issue","actor","action","target","author","icreated","labels","mentions"]
rows=[]
for f in sorted(glob.glob("data/out2/*.tsv.gz")):
    with gzip.open(f,"rt",encoding="utf-8",errors="replace",newline="\n") as fh:
        for line in fh:
            p=line.rstrip("\n").replace("\r"," ").split("\t")
            if len(p)==11: rows.append(p)
df=pd.DataFrame(rows,columns=cols)
df["time"]=pd.to_datetime(df["time"],errors="coerce",utc=True)
df=df.dropna(subset=["time"])
df["key"]=df["repo"]+"#"+df["issue"]
df.to_parquet("data/events.parquet")
print(len(df)); print(df.groupby(["type","action"]).size())
print("bot rows:", round(df.actor.str.endswith("[bot]").mean(),3))
print("rows with mentions:", (df.mentions!="").sum())
