# kex — Kubernetes index for the EdgeLab cluster

default:
    @just --list

# === Environment ===

# Show environment info
[group("env")]
info:
    @echo "Python: $(python --version 2>/dev/null || echo 'not found')"
    @echo "uv:     $(uv --version 2>/dev/null || echo 'not found')"
    @echo "node:   $(node --version 2>/dev/null || echo 'not found')"
    @echo "just:   $(just --version 2>/dev/null || echo 'not found')"

# Fresh-clone bring-up: install deps, sync, smoke
[group("env")]
setup: sync ui-install
    @echo "kex setup complete. Run 'just check' to verify."

# Print project layout, recent commits, open issues
[group("env")]
onboard:
    @echo "=== kex layout ==="
    @ls -1
    @echo "\n=== recent commits ==="
    @git log --oneline -10 2>/dev/null || echo "(no commits yet)"
    @echo "\n=== open GitHub issues ==="
    @gh issue list --limit 10 2>/dev/null || echo "(gh not configured)"

# === Development ===

# Run FastAPI dev server with auto-reload
[group("dev")]
dev:
    uvicorn kex.main:app --reload --host 0.0.0.0 --port 8000

# Install UI dependencies
[group("ui")]
ui-install:
    cd ui && npm install

# Run UI dev server (Vite + Svelte, proxies /api to :8000)
[group("ui")]
ui-dev:
    cd ui && npm run dev

# Build UI for production
[group("ui")]
ui-build:
    cd ui && npm run build

# === Python ===

[group("python")]
lint:
    ruff check .

[group("python")]
lint-fix:
    ruff check --fix .

[group("python")]
fmt:
    ruff format .

[group("python")]
fmt-check:
    ruff format --check .

[group("python")]
sync:
    uv sync

# === Tests ===

[group("test")]
test *args:
    pytest tests/ {{ args }}

[group("test")]
test-unit:
    pytest tests/unit/ -v

[group("test")]
test-integration:
    pytest tests/integration/ -v

[group("test")]
test-ui:
    cd ui && npm test

[group("test")]
test-e2e:
    cd ui && npx playwright test

# Run all static checks (no cluster, no images) — fast feedback loop
[group("test")]
check: lint fmt-check test test-ui docs-build

# === Docs ===

[group("docs")]
docs-build:
    sphinx-build -b html -c . docs/ docs/_build/html

[group("docs")]
docs-serve:
    sphinx-autobuild -c . docs/ docs/_build/html

[group("docs")]
docs-clean:
    rm -rf docs/_build

# === Container ===

# Project version (used as default container tag)
version := `grep -m1 '^version' pyproject.toml | cut -d'"' -f2`

# Build container image locally with docker (CI uses GitHub Actions → ghcr.io)
[group("container")]
build tag=version:
    docker build -t ghcr.io/jonatanolofsson/kex:{{ tag }} -t ghcr.io/jonatanolofsson/kex:latest .

[group("container")]
push tag=version: build
    docker push ghcr.io/jonatanolofsson/kex:{{ tag }}
    docker push ghcr.io/jonatanolofsson/kex:latest

# === Helm chart ===

[group("chart")]
chart-lint:
    helm lint chart/

[group("chart")]
chart-template:
    helm template kex chart/ --namespace kex
