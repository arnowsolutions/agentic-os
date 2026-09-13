"""
Agentic OS — Skill Manifest (AI-generalist layer, Stage 5a).

Generates data/skill-manifest.json: a machine-readable contract of every
dashboard page → its endpoints, derived from real source (NAV_CONFIG +
pages/*.js + route decorators). Never hand-maintained: regenerated on
demand via POST /api/skill-manifest/regenerate or the CLI wrapper in
scripts/gen_skill_manifest.py.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from modules.config import get_settings

MANIFEST_VERSION = 1

_NAV_ENTRY_RE = re.compile(
    r"\{\s*page:\s*'([a-z0-9-]+)'.*?label:\s*'([^']*)'.*?(?:title:\s*'([^']*)')?.*?(?:breadcrumb:\s*'([^']*)')?\}",
)
_API_CALL_RE = re.compile(r"""['"`](/api/[A-Za-z0-9_\-./{}$]+)['"`]""")
_ROUTE_DECORATOR_RE = re.compile(
    r"@(app|router)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']",
)
_ROUTER_PREFIX_RE = re.compile(r"APIRouter\(\s*prefix\s*=\s*[\"']([^\"']+)[\"']")


def _norm_template(path: str) -> str:
    """/api/foo/${id}/bar → /api/foo/{id}/bar ; drop query strings for stability."""
    path = re.sub(r"\$\{[^}]*\}", "{param}", path)
    path = path.split("?")[0]
    return path


def _parse_nav(pages_dir_name: str = "pages") -> dict:
    utils = get_settings().BASE_DIR / "dashboard" / "utils.js"
    text = utils.read_text()
    nav = {}
    for m in _NAV_ENTRY_RE.finditer(text):
        page, label, title, breadcrumb = m.groups()
        nav[page] = {
            "title": title or label,
            "breadcrumb": (breadcrumb or "").strip(),
            "module": f"dashboard/{pages_dir_name}/{page}.js",
        }
    return nav


def _page_endpoints() -> dict:
    """Map page → API paths it calls, by scanning its dashboard/pages/*.js source."""
    pages_dir = get_settings().BASE_DIR / "dashboard" / "pages"
    out = {}
    if not pages_dir.exists():
        return out
    for f in sorted(pages_dir.glob("*.js")):
        paths = set()
        for m in _API_CALL_RE.finditer(f.read_text()):
            p = _norm_template(m.group(1))
            if len(p) > len("/api/"):
                paths.add(p)
        out[f.stem] = sorted(paths)
    return out


def _all_routes() -> list:
    """Every FastAPI route in server.py + modules/*.py, with resolved prefixes."""
    base = get_settings().BASE_DIR
    routes = []
    sources = [base / "server.py"] + sorted((base / "modules").glob("*.py"))
    for src in sources:
        if not src.exists():
            continue
        text = src.read_text()
        prefix = ""
        pm = _ROUTER_PREFIX_RE.search(text)
        if pm:
            prefix = pm.group(1)
        for m in _ROUTE_DECORATOR_RE.finditer(text):
            obj, method, path = m.groups()
            full = (prefix if obj == "router" else "") + path
            if not full.startswith("/api/") and not full.startswith("/metrics"):
                continue
            routes.append({"method": method.upper(), "path": _norm_template(full), "source": src.name})
    seen = set()
    uniq = []
    for r in sorted(routes, key=lambda r: (r["path"], r["method"])):
        k = (r["method"], r["path"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return uniq


def generate(force: bool = False) -> dict:
    """Build the manifest; regenerate only when sources changed unless force."""
    manifest_path = get_settings().BASE_DIR / "data" / "skill-manifest.json"
    if manifest_path.exists() and not force:
        existing = json.loads(manifest_path.read_text())
        if _is_fresh(existing, manifest_path):
            return existing

    nav = _parse_nav()
    endpoints = _page_endpoints()
    pages = {}
    for page, meta in nav.items():
        pages[page] = {
            "title": meta["title"],
            "description": meta["breadcrumb"],
            "route": f"#/{page}",
            "module": meta["module"] if (get_settings().BASE_DIR / "dashboard" / "pages" / f"{page}.js").exists() else None,
            "endpoints": endpoints.get(page, []),
        }

    manifest = {
        "version": MANIFEST_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "modules/skill_manifest.py (do not hand-edit)",
        "usage": "Machine contract for agents: each page's route + endpoints. "
                 "GET /api/skill-manifest to read, POST /api/skill-manifest/regenerate to rebuild. "
                 "Page-aware chat injects entries from here.",
        "pages": pages,
        "api_routes": _all_routes(),
        "source_mtimes": _source_mtimes(),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def _source_mtimes() -> dict:
    base = get_settings().BASE_DIR
    out = {}
    targets = [base / "dashboard" / "utils.js", base / "server.py"]
    targets += sorted((base / "dashboard" / "pages").glob("*.js"))
    targets += sorted((base / "modules").glob("*.py"))
    for t in targets:
        if t.exists():
            out[str(t.relative_to(base))] = int(t.stat().st_mtime)
    return out


def _is_fresh(manifest: dict, manifest_path: Path) -> bool:
    current = _source_mtimes()
    stored = manifest.get("source_mtimes") or {}
    return current == stored


def load() -> dict:
    """Read cached manifest (generate once if missing)."""
    manifest_path = get_settings().BASE_DIR / "data" / "skill-manifest.json"
    if not manifest_path.exists():
        return generate(force=True)
    try:
        return json.loads(manifest_path.read_text())
    except Exception:
        return generate(force=True)


def page_context(page: str) -> dict:
    """Manifest slice for one page — what the chat context injection sends."""
    m = load()
    entry = m.get("pages", {}).get(page)
    if not entry:
        return {}
    return {"page": page, **entry}
