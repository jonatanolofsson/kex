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

# TLS verification for the ArgoCD HTTPS client. Three modes:
#   * KEX_ARGOCD_CA_BUNDLE=/path/to/bundle.pem — verify against that bundle
#     (mounted by the chart from an external ConfigMap; keeps cluster-
#     specific CAs out of the kex image).
#   * KEX_ARGOCD_VERIFY_TLS=false — disable verification entirely (local
#     dev only).
#   * Neither set — verify against the default system trust store.
_CA_BUNDLE = os.environ.get("KEX_ARGOCD_CA_BUNDLE", "").strip()
_VERIFY_TLS_FLAG = os.environ.get("KEX_ARGOCD_VERIFY_TLS", "true").lower() != "false"
if _CA_BUNDLE:
    VERIFY_TLS: bool | str = _CA_BUNDLE
elif _VERIFY_TLS_FLAG:
    VERIFY_TLS = True
else:
    VERIFY_TLS = False

_metadata_cache: TTLCache[tuple[str, str], dict[str, Any]] = TTLCache(
    maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS
)


def _read_token() -> str | None:
    """Resolve the bearer token for the ArgoCD HTTP API.

    Two sources, in order:

    1. ``ARGOCD_AUTH_TOKEN`` env var — an ArgoCD ``account
       generate-token`` JWT mounted from a SealedSecret. This is the
       supported path against current EdgeLab; argocd doesn't accept
       raw k8s ServiceAccount JWTs out of the box.
    2. ``TOKEN_PATH`` (default ``/var/run/secrets/.../token``) — kex's
       own k8s SA token. Kept as a fallback for future deployments
       that wire argocd's ``TokenReview`` integration (no static token
       to seal). The caller degrades gracefully on the 401 that
       results when argocd hasn't been configured for SA tokens.
    """
    env_token = os.environ.get("ARGOCD_AUTH_TOKEN", "").strip()
    if env_token:
        return env_token
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
