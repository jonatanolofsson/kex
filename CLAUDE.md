# kex

Annotation-driven cluster landing page + per-app detail view for ArgoCD-managed clusters.

## Quick reference

```bash
direnv allow            # activate the nix flake dev shell
just                    # list recipes
just check              # lint + fmt-check + pytest + vitest + docs build
just dev                # FastAPI on :8000 with auto-reload
just ui-dev             # Vite/Svelte on :5173 (proxies /api to :8000)
just build              # local docker build (CI pushes to ghcr.io on tag)
```

All commands need the nix dev shell. If direnv hasn't loaded, prefix with `direnv exec . ...`.

## Layout

| Path | Contents |
|---|---|
| `src/kex/` | FastAPI backend |
| `ui/` | Svelte 5 + Vite SPA |
| `chart/` | Helm chart (deployed via ArgoCD) |
| `docs/` | Sphinx docs |

## Design invariants (don't break these)

1. **Annotation-driven, never code-driven.** New field → new `kex/*` annotation, never a switch on app name.
2. **All external data sources cached + gracefully degradable.** ArgoCD down → page renders without git column, not 500.
3. **SPA + backend separation.** Frontend only talks to `/api/*` JSON.
4. **Argo as the integration point, not git directly.** Never introduce a second credential channel.
5. **RBAC is strictly read-only.** Write actions need a separate threat-model review.

See `docs/design-principles.rst` for the full list.

## Workflow

`docs → test → implement → check` before commit. Conventional commits (`feat:`, `fix:`, `docs:`, …).
