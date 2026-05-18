Architecture
============

Stack
-----

- Frontend: Svelte 5 + Vite SPA (``ui/``).
- Backend: Python 3.13 + FastAPI + uv (``src/kex/``).
- Runtime: one container, nginx + uvicorn under supervisord.
- Build: 4-stage Dockerfile (ui-build → py-build → docs-build → runtime).
- Dev shell: nix flake.

Data sources
------------

- **ArgoCD ``Application`` CRs** — one row per Application; the iteration unit.
- **Kubernetes API** — live pods + IngressRoutes for the detail page.
- **ArgoCD HTTP API** — per-revision commit metadata (author/date/subject).
  Authenticated via the kex pod's own Kubernetes ServiceAccount JWT
  (verified by ``argocd-server`` via TokenReview). No PAT, no
  long-lived static token.

Design invariants
-----------------

See :doc:`design-principles`.
