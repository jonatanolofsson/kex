"""``GET /api/config`` — cluster-scoped UI configuration.

The kex image is generic (lives on public ghcr.io) and stays free of
per-cluster content. Cluster-specific prose — the cluster name shown
in the hero, the tagline, the header link row, the welcome card —
arrives at runtime via a ConfigMap mounted by the chart at
``KEX_CONFIG_DIR`` (default ``/etc/kex/config``).

Schema: ``ui.json`` in that directory, shaped like

.. code-block:: json

    {
      "clusterName": "EdgeLab",
      "heroTagline": "Boliden's cluster for ML and edge work.",
      "headerLinks": [{"label": "Docs", "url": "https://...", "icon": "book"}],
      "welcomeMarkdown": "Welcome.\\n\\nThe cluster runs ..."
    }

Read once at module import; restart-driven refresh (stakater/reloader
on the Deployment) handles edits to the ConfigMap. Missing file or
malformed JSON → all-empty response, logged at WARNING so it surfaces
in the pod log but doesn't crash the API.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from kex.markdown import md as _md

logger = logging.getLogger(__name__)
router = APIRouter()

CONFIG_DIR = Path(os.environ.get("KEX_CONFIG_DIR", "/etc/kex/config"))
CONFIG_FILE = CONFIG_DIR / "ui.json"


def _load_config_payload() -> dict[str, Any]:
    """Read ``ui.json`` once and shape it into the wire response.

    Defaults to all-empty values so the SPA renders cleanly even when
    nothing is configured. Errors degrade silently to the empty payload
    plus a WARNING log line.
    """
    empty = {
        "cluster_name": "",
        "hero_tagline": "",
        "header_links": [],
        "welcome_html": "",
    }
    if not CONFIG_FILE.is_file():
        logger.info("kex: no UI config at %s; serving empty defaults", CONFIG_FILE)
        return empty
    try:
        raw = json.loads(CONFIG_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        logger.warning(
            "kex: failed to read/parse %s; serving empty defaults", CONFIG_FILE, exc_info=True
        )
        return empty

    if not isinstance(raw, dict):
        logger.warning("kex: %s root is not an object; serving empty defaults", CONFIG_FILE)
        return empty

    header_links_raw = raw.get("headerLinks") or []
    if not isinstance(header_links_raw, list):
        header_links_raw = []
    header_links = [
        {
            "label": str(item.get("label", "")),
            "url": str(item.get("url", "")),
            "icon": str(item.get("icon", "")) or None,
        }
        for item in header_links_raw
        if isinstance(item, dict) and item.get("label") and item.get("url")
    ]

    welcome_md = raw.get("welcomeMarkdown") or ""
    welcome_html = _md.render(welcome_md) if welcome_md else ""

    return {
        "cluster_name": str(raw.get("clusterName") or ""),
        "hero_tagline": str(raw.get("heroTagline") or ""),
        "header_links": header_links,
        "welcome_html": welcome_html,
    }


# Cache at import time. Restart triggers re-read; stakater/reloader on
# the Deployment turns a ConfigMap edit into a rolling restart.
_payload = _load_config_payload()


@router.get("/api/config")
def get_config() -> dict[str, Any]:
    """Return the in-process UI config snapshot."""
    return _payload
