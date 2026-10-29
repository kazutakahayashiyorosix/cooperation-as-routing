"""Read one GH Archive hour (gzip JSON lines) on stdin; write issue events and issue comments as gzip TSV on stdout.
Columns: type, time, repo, issue, actor, action, target(assignee), issue_author, issue_created, labels(;), mentions(;)
mentions = @logins in the comment body (comments) or the issue body (opened); a mention of someone new is our handoff signal."""
import sys, gzip, json, re
MENT = re.compile(r"(?<![\w.`/])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))\b")
out = gzip.open(sys.stdout.buffer, "wt", encoding="utf-8")
for line in gzip.GzipFile(fileobj=sys.stdin.buffer):
    try:
        e = json.loads(line)
    except Exception:
        continue
    t = e.get("type")
    if t not in ("IssuesEvent", "IssueCommentEvent"):
        continue
    p = e.get("payload") or {}
    iss = p.get("issue") or {}
    if "pull_request" in iss:
        continue
    action = p.get("action", "")
    if t == "IssuesEvent" and action not in ("opened", "closed", "reopened", "assigned", "unassigned"):
        continue
    if t == "IssueCommentEvent" and action != "created":
        continue
    tgt = (p.get("assignee") or {}).get("login", "") if action in ("assigned", "unassigned") else ""
    labels = ";".join(l.get("name", "").replace("\t", " ").replace(";", ",") for l in (iss.get("labels") or []))
    body = (p.get("comment") or {}).get("body") if t == "IssueCommentEvent" else (iss.get("body") if action == "opened" else "")
    ments = []
    for m in MENT.findall(body or ""):
        if m not in ments and len(ments) < 10:
            ments.append(m)
    row = [t[:-5], e.get("created_at", ""), (e.get("repo") or {}).get("name", ""), str(iss.get("number", "")),
           (e.get("actor") or {}).get("login", ""), action, tgt, (iss.get("user") or {}).get("login", ""),
           iss.get("created_at", ""), labels, ";".join(ments)]
    out.write("\t".join(x.replace("\t", " ").replace("\n", " ") for x in row) + "\n")
out.close()
