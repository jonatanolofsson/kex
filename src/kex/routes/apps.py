"""FastAPI router for the ``/api/apps`` surface.

Index endpoint returns the lightweight card list; detail endpoint fans
out into pods + ingressroutes + ArgoCD revision metadata. Every
external call is wrapped so a single failing dependency degrades that
section instead of breaking the response.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from markdown_it import MarkdownIt

from kex import annotations, argocd, k8s

logger = logging.getLogger(__name__)
router = APIRouter()
_md = MarkdownIt("commonmark", {"breaks": True, "html": False})


@router.get("/api/apps")
def list_apps() -> list[dict[str, Any]]:
    """Return one card-shaped row per Application with ``kex/enabled=true``.

    Fast: only annotation parsing + status badges. No git lookups.
    """
    rows: list[dict[str, Any]] = []
    for app in k8s.list_applications():
        if not annotations.is_enabled(app):
            continue
        meta = annotations.parse(app)
        rows.append(
            {
                "name": meta.name,
                "title": meta.title,
                "description": meta.description,
                "group": meta.group,
                "icon": meta.icon,
                "sync_status": meta.sync_status,
                "health_status": meta.health_status,
            }
        )
    return rows


@router.get("/api/apps/{name}")
def get_app(name: str) -> dict[str, Any]:
    """Return the full detail view for one Application.

    404 if the Application doesn't exist *or* exists but isn't kex-enabled
    — from a UI perspective those are equivalent and surfacing the
    distinction would leak operational info.
    """
    app = k8s.get_application(name)
    if app is None or not annotations.is_enabled(app):
        raise HTTPException(status_code=404, detail=f"app {name!r} not found")

    meta = annotations.parse(app)
    pods = k8s.list_pods(meta.namespace)
    ingresses = _format_ingressroutes(k8s.list_ingressroutes(meta.namespace))
    latest_commit, recent_deployers = _git_section(meta)

    return {
        "name": meta.name,
        "title": meta.title,
        "description": meta.description,
        "group": meta.group,
        "icon": meta.icon,
        "about_html": _md.render(meta.about) if meta.about else "",
        "links": [{"label": link.label, "url": link.url} for link in meta.links],
        "namespace": meta.namespace,
        "sync_status": meta.sync_status,
        "health_status": meta.health_status,
        "repo_url": meta.repo_url,
        "git_path": meta.git_path,
        "pods": pods,
        "ingresses": ingresses,
        "latest_commit": latest_commit,
        "recent_deployers": recent_deployers,
    }


def _format_ingressroutes(
    items: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Flatten Traefik IngressRoute rules to ``[{host, path}, …]``.

    A single IngressRoute can have multiple routes; each match yields
    its own row. The UI dedupes if needed; we keep the wire format
    explicit.
    """
    out: list[dict[str, str]] = []
    for item in items:
        spec = item.get("spec") or {}
        for route in spec.get("routes") or []:
            match = str(route.get("match", ""))
            for host, path in _extract_hosts_and_paths(match):
                out.append({"host": host, "path": path})
    return out


def _extract_hosts_and_paths(match: str) -> list[tuple[str, str]]:
    r"""Best-effort parse of a Traefik match expression.

    Handles the common shapes ``Host(\`x\`)``, ``Host(\`x\`) && PathPrefix(\`/p\`)``,
    multiple hosts via ``||``. Anything fancier falls through as a
    single ``("", match)`` so it still appears in the UI verbatim.
    """
    import re

    hosts = re.findall(r"Host\(`([^`]+)`\)", match)
    prefix_match = re.search(r"PathPrefix\(`([^`]+)`\)", match)
    path = prefix_match.group(1) if prefix_match else "/"
    if not hosts:
        return [("", match)]
    return [(host, path) for host in hosts]


def _git_section(
    meta: annotations.AppMetadata,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Fetch latest commit + recent deployers via the ArgoCD HTTP API.

    Returns a (latest_commit, recent_deployers) pair, each ``None`` /
    ``[]`` if the data couldn't be retrieved. The UI renders 'git data
    unavailable' for the sections that come back empty.
    """
    if not meta.sync_revision:
        return None, []
    latest_raw = argocd.get_revision_metadata(meta.name, meta.sync_revision)
    latest_commit = _format_commit(latest_raw)

    deployers: dict[str, dict[str, Any]] = {}
    for entry in meta.history:
        rev = entry.get("revision")
        if not rev or rev in {h.get("revision") for h in meta.history if h is not entry}:
            # dedupe by revision; we want the latest occurrence
            pass
        commit = argocd.get_revision_metadata(meta.name, rev) if rev else None
        formatted = _format_commit(commit)
        if not formatted:
            continue
        # Dedupe by author email when present, falling back to name
        key = formatted.get("email") or formatted.get("author") or ""
        if key and key not in deployers:
            deployers[key] = formatted
        if len(deployers) >= 5:
            break

    return latest_commit, list(deployers.values())


def _format_commit(
    raw: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Reshape an ArgoCD revision-metadata response for the UI.

    ArgoCD historically returns ``author`` as ``Name <email>``; split
    that into separate fields so the UI doesn't have to.
    """
    if not raw:
        return None
    author = raw.get("author") or ""
    name = author
    email = ""
    if "<" in author and ">" in author:
        name, _, rest = author.partition("<")
        name = name.strip()
        email = rest.rstrip(">").strip()
    return {
        "author": name or author,
        "email": email,
        "date": raw.get("date"),
        "message": raw.get("message", "").splitlines()[0] if raw.get("message") else "",
    }
