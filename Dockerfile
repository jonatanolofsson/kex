# Stage 1 — Build the SPA with Vite + Svelte
FROM node:lts-alpine AS ui-build
WORKDIR /app
COPY ui/package.json ui/package-lock.json* ./
RUN npm install
COPY ui/ ./
RUN npm run build

# Stage 2 — Build Python dependencies + install kex
FROM python:3.13-slim AS py-build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable || \
    uv sync --no-dev --no-editable

# Stage 3 — Build Sphinx docs
FROM python:3.13-slim AS docs-build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-editable --no-install-project || \
    uv sync --no-editable --no-install-project
COPY src/ src/
COPY conf.py ./
COPY docs/ docs/
RUN .venv/bin/sphinx-build -b html -c . docs/ docs/_build/html

# Stage 4 — Runtime (nginx + uvicorn via supervisord)
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends nginx supervisor \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=py-build /app/.venv /app/.venv
COPY --from=py-build /app/src /app/src
COPY --from=ui-build /app/dist/ /usr/share/nginx/html/
COPY --from=docs-build /app/docs/_build/html/ /usr/share/nginx/html/docs/
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisord.conf
RUN rm -f /etc/nginx/sites-enabled/default

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

EXPOSE 80
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
