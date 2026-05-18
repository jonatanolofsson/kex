"""FastAPI entrypoint for kex.

The SPA hits ``/api/*``; nginx routes everything else to the built
Svelte bundle. This module is intentionally thin — domain logic lives
in :mod:`kex.annotations`, :mod:`kex.argocd`, and :mod:`kex.k8s`.
"""

from __future__ import annotations

from fastapi import FastAPI

from kex import __version__

app = FastAPI(
    title="kex",
    version=__version__,
    description="Kubernetes index — annotation-driven cluster landing page.",
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe. Returns 200 if the process is up."""
    return {"status": "ok", "version": __version__}


@app.get("/api/version")
def version() -> dict[str, str]:
    """Build version, surfaced in the SPA footer."""
    return {"version": __version__}
