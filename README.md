# kex

**Kubernetes index** — annotation-driven cluster landing page + per-app detail view.

Each ArgoCD `Application` CR carries `kex/*` annotations describing its tile (title, description, group, links). kex scans the cluster and renders one row per application — no central catalog to edit.

Built for Boliden's EdgeLab cluster but generic: any Kubernetes cluster running ArgoCD + Traefik IngressRoutes works.

## Quick start

```bash
git clone https://github.com/jonatanolofsson/kex
cd kex
direnv allow            # activates the nix flake dev shell
just setup              # sync python + ui deps
just check              # lint + tests + ui tests + docs build
```

Local dev loop (two terminals):

```bash
just dev                # FastAPI on :8000 with auto-reload
just ui-dev             # Vite/Svelte on :5173, proxies /api to :8000
```

## Stack

- Svelte 5 + Vite SPA (`ui/`)
- FastAPI + Python 3.13 + uv (`src/kex/`)
- nginx + uvicorn under supervisord, one image
- Catppuccin Mocha (dark default) / Latte (light)
- ArgoCD as the integration point — no PAT, no long-lived static token

See `docs/` for architecture, annotations contract, operations, and design principles.

## License

MIT.
