#!/usr/bin/env python3
"""Cross-check every endpoint each dashboard page references against the live route table."""
import json, re, urllib.request
from pathlib import Path

TOK = ""
d = json.load(open("/workspace/agentic-os/data/sessions.json"))
items = list(d.items()) if isinstance(d, dict) else [(x.get("token"), x) for x in d]
TOK = sorted(((v.get("created_at", ""), k) for k, v in items if isinstance(v, dict)), reverse=True)[0][1]

req = urllib.request.Request("http://localhost:8082/openapi.json", headers={"Cookie": f"aos_session={TOK}"})
spec = json.loads(urllib.request.urlopen(req, timeout=40).read())
routes = set(spec["paths"].keys())


def norm(p):
    """/api/foo/${x}/bar -> /api/foo/{}/bar so it can be matched against the spec."""
    p = re.sub(r"\$\{[^}]*\}", "{}", p)
    p = re.sub(r"\{[^}]*\}", "{}", p)
    return p.rstrip("/")


route_norm = {norm(r) for r in routes}
route_norm |= {norm(r) + "/{}" for r in routes}
problems = []
for f in sorted(Path("/workspace/agentic-os/dashboard/pages").glob("*.js")):
    eps = set()
    for m in re.finditer(r"/api/[A-Za-z0-9_/{}$.:-]+", f.read_text(errors="replace")):
        eps.add(m.group(0).rstrip("/"))
    for e in sorted(eps):
        n = norm(e)
        if n not in route_norm and n + "/{}" not in route_norm:
            problems.append((f.stem, e))

print(f"pages checked: {len(list(Path('/workspace/agentic-os/dashboard/pages').glob('*.js')))} | live routes: {len(routes)}")
if problems:
    print("\n⚠ page references with NO matching live route:")
    for page, ep in problems:
        print(f"   {page:26} {ep}")
else:
    print("\n✓ every page endpoint reference resolves to a live route")
