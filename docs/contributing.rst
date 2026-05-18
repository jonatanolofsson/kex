Contributing
============

Setup
-----

.. code-block:: bash

   git clone https://github.com/jonatanolofsson/kex
   cd kex
   direnv allow            # activates the nix flake dev shell
   just setup              # sync python deps + ui deps
   just check              # lint + fmt-check + tests + ui tests + docs build

Workflow
--------

1. **Docs first** — if the change affects user-visible behaviour,
   update the relevant ``docs/*.rst`` page before writing code.
2. **Test next** — add the failing test that captures the desired
   behaviour. ``tests/unit/`` for pure logic, ``tests/integration/``
   for FastAPI routes, ``ui/tests/`` for Svelte logic,
   ``ui/e2e/`` (Playwright) for browser flows.
3. **Implement** — make the test pass.
4. **Check** — ``just check`` must be green before commit.
5. **Conventional commit** — ``feat:``, ``fix:``, ``docs:``, etc.
   One commit per logical unit.

Local dev loop
--------------

.. code-block:: bash

   # Terminal 1 — backend with auto-reload
   just dev

   # Terminal 2 — Svelte HMR (proxies /api to :8000)
   just ui-dev

Image
-----

CI builds and pushes ``ghcr.io/jonatanolofsson/kex:<tag>`` on git tag.
Local ``just build`` builds with Docker for iteration.
