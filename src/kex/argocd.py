"""HTTP client for ArgoCD's REST API.

Auth: kex's own Kubernetes ServiceAccount JWT (projected by kubelet at
``/var/run/secrets/kubernetes.io/serviceaccount/token``), passed as a
bearer token. ArgoCD verifies it via TokenReview when its
``argocd-cm`` is configured with the matching account binding (see
``docs/operations.rst``).

Failures are degraded gracefully — every public function returns
``None`` or an empty value on error and logs at WARNING. The route
layer surfaces a "git data unavailable" message; the rest of the page
renders unaffected.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import httpx
from cachetools import TTLCache

logger = logging.getLogger(__name__)

ARGOCD_SERVER = os.environ.get("ARGOCD_SERVER", "https://argocd-server.argocd.svc.cluster.local")
TOKEN_PATH = Path(
    os.environ.get("KEX_TOKEN_PATH", "/var/run/secrets/kubernetes.io/serviceaccount/token")
)
CACHE_TTL_SECONDS = int(os.environ.get("KEX_ARGOCD_CACHE_TTL", "3600"))
CACHE_MAX_SIZE = int(os.environ.get("KEX_ARGOCD_CACHE_SIZE", "1024"))

# Verify TLS by default; can be turned off via env for local development
# against a self-signed argocd cluster.
VERIFY_TLS = os.environ.get("KEX_ARGOCD_VERIFY_TLS", "true").lower() != "false"

_metadata_cache: TTLCache[tuple[str, str], dict[str, Any]] = TTLCache(
    maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS
)


def _read_token() -> str | None:
    """Read the SA token from disk on demand.

    Kubelet rotates the token every ~1h; we re-read on every cache
    miss rather than caching the token, so rotation is transparent.
    """
    try:
        return TOKEN_PATH.read_text().strip()
    except OSError:
        return None


def get_revision_metadata(app_name: str, revision: str) -> dict[str, Any] | None:
    """Fetch commit metadata for a given Application revision.

    Returns the parsed JSON body (typically ``{author, date, message,
    tags, signatureInfo}``) or ``None`` if ArgoCD is unreachable or
    the revision can't be resolved.

    Cached in-process for :data:`CACHE_TTL_SECONDS`; the key includes
    both the app name and the revision so different SHAs don't collide.
    """
    if not app_name or not revision:
        return None
    key = (app_name, revision)
    cached = _metadata_cache.get(key)
    if cached is not None:
        return cached

    token = _read_token()
    if token is None:
        logger.warning("kex: no SA token available for ArgoCD auth")
        return None

    url = (
        f"{ARGOCD_SERVER.rstrip('/')}/api/v1/applications/{app_name}/revisions/{revision}/metadata"
    )
    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0,
            verify=VERIFY_TLS,
        )
        if response.status_code != 200:
            logger.warning(
                "kex: argocd revision-metadata HTTP %s for %s@%s",
                response.status_code,
                app_name,
                revision,
            )
            return None
        body = response.json()
        _metadata_cache[key] = body
        return body
    except (httpx.HTTPError, ValueError):
        logger.warning(
            "kex: failed to fetch revision metadata for %s@%s",
            app_name,
            revision,
            exc_info=True,
        )
        return None
