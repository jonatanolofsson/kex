"""Pure parser for ``kex/*`` annotations on ArgoCD ``Application`` CRs.

Takes the dict form of an Application object (as returned by the
``kubernetes`` client's ``to_dict()`` or the ArgoCD HTTP API) and
returns typed display data the routes layer hands to the SPA.

No I/O, no caching, no markdown rendering — that all lives elsewhere.
This module is the one place where annotation grammar is decoded; if a
new annotation is added, this is the only file that learns about it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

KEX_PREFIX = "kex/"
LINKS_PREFIX = "kex/links."


@dataclass(frozen=True)
class Link:
    """A sidebar link rendered on the detail page.

    The label comes from the annotation key's suffix
    (``kex/links.<label>``); the URL is the annotation value.
    """

    label: str
    url: str


@dataclass(frozen=True)
class AppMetadata:
    """View model derived from one ArgoCD ``Application`` CR.

    Every field has a sensible default so partial / missing
    annotations never raise. The routes layer is responsible for any
    side effects (markdown rendering, k8s/argocd lookups, caching).
    """

    name: str
    title: str
    description: str
    group: str
    icon: str | None
    about: str
    links: list[Link]
    namespace: str
    repo_url: str | None
    git_path: str | None
    sync_status: str | None
    health_status: str | None
    sync_revision: str | None
    history: list[dict[str, Any]]


def is_enabled(app: dict[str, Any]) -> bool:
    """``True`` iff ``kex/enabled == "true"`` on the Application CR.

    The check is case-insensitive on the value; missing or any other
    value is treated as disabled.
    """
    annotations = (app.get("metadata") or {}).get("annotations") or {}
    return str(annotations.get("kex/enabled", "")).strip().lower() == "true"


def parse(app: dict[str, Any]) -> AppMetadata:
    """Convert an Application dict to an :class:`AppMetadata`.

    Caller should already have filtered by :func:`is_enabled` — this
    function happily renders disabled apps too, so it's safe to call
    on either filtered or unfiltered input depending on use case
    (e.g. detail-page lookup needs to parse even disabled apps to
    return a useful 404 message).
    """
    meta = app.get("metadata") or {}
    annotations = meta.get("annotations") or {}
    spec = app.get("spec") or {}
    source = spec.get("source") or {}
    status = app.get("status") or {}

    name = str(meta.get("name", ""))
    history_raw = status.get("history") or []
    history = list(history_raw[-5:]) if isinstance(history_raw, list) else []

    return AppMetadata(
        name=name,
        title=annotations.get("kex/title") or name,
        description=annotations.get("kex/description", ""),
        group=annotations.get("kex/group", "Other"),
        icon=annotations.get("kex/icon"),
        about=annotations.get("kex/about", ""),
        links=_parse_links(annotations),
        namespace=(spec.get("destination") or {}).get("namespace", ""),
        repo_url=source.get("repoURL"),
        git_path=annotations.get("kex/git.path") or source.get("path"),
        sync_status=(status.get("sync") or {}).get("status"),
        health_status=(status.get("health") or {}).get("status"),
        sync_revision=(status.get("sync") or {}).get("revision"),
        history=history,
    )


def _parse_links(annotations: dict[str, str]) -> list[Link]:
    """Extract ``kex/links.<label>`` annotations as sorted :class:`Link` list.

    Empty values are dropped (an unset annotation that round-tripped
    through helm is a footgun we don't want surfacing as a broken
    button on the UI). Order is alphabetic on the label so the
    sidebar layout is stable across reloads.
    """
    links = [
        Link(label=key[len(LINKS_PREFIX) :], url=value)
        for key, value in annotations.items()
        if key.startswith(LINKS_PREFIX) and value
    ]
    return sorted(links, key=lambda link: link.label)
