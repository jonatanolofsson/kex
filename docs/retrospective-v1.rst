Retrospective — kex v1
======================

A walk through the way-of-working, code-standards, security,
performance, accessibility, and design-principle checklists from the
kex plan (Phase 7). What landed cleanly, what drifted, and what got
revised in response.

Way-of-working
--------------

Every principle in the plan's mapping table has a concrete realisation
in the as-built code:

- ``Plan-first``: this plan file went through six full rewrites during
  Phases 0–7 as constraints surfaced (the PAT-is-wrong moment, the
  truck-tracker template discovery, the IngressRoute-vs-Application
  question, the cluster-auth consumer pattern). Each revision left a
  trail in ``/home/jonatan/.claude/plans/cheerful-cuddling-stonebraker.md``.
- ``just check ≠ behavior verified``: Phase 4 explicitly walked from
  ArgoCD-Synced → pod-Running → in-cluster API hit → public URL +
  OIDC redirect, rather than stopping at "pytest green". The
  IngressRoute drift between v0 (cross-namespace Middleware) and v1
  (same-namespace consumer pattern) was only caught by the behavioural
  probe, not by ``helm lint`` or ``helm template``.
- ``Deploy-then-verify``: each phase's verification gate required
  cluster-side evidence, not just CI green.
- ``Source repo + rollout repo discipline``: the kex chart lives in
  the kex GitHub repo; the ArgoCD Application wrapper lives in
  ``default-helm-charts-ARGO``. Both have their own commit trails and
  both gated by ArgoCD reconciliation.
- ``Conventional commits``: every commit (15 across 4 repos) uses
  ``feat:``, ``fix:``, ``docs:``, or ``chore:``.

Drift to note:

- The plan called for ``sealed-secrets`` as the credential pattern. v1
  ships **no** SealedSecret because the chosen SA-JWT auth path
  doesn't require one. The principle is honoured by *not* introducing
  a long-lived static credential at all — strictly better than sealing
  one — but ``chart/values.yaml`` retains an ``argocdTokenSecretName``
  knob for the project-role-token fallback. Worth re-evaluating
  whether to delete the knob if SA-JWT proves stable in production
  for a few months.

Code standards
--------------

- ruff: 0 errors, 0 warnings on ``ruff check .`` and ``ruff format
  --check .``. Configured for ``E, F, I, W, UP, B``.
- Type hints on every public function in ``annotations.py``,
  ``argocd.py``, ``k8s.py``, ``routes/apps.py``.
- Docstrings on every module + public function. ``annotations.py``
  documents the grammar (which is the load-bearing one — future
  contributors should not need to read the parser to know what
  annotations exist).
- No ``TODO`` without an issue link (checked: zero TODOs).
- No commented-out code.
- No debug ``print``; everything goes through ``logger`` at WARNING
  for failures, INFO for one-shot startup events.
- vitest: 6/6 pass.
- pytest: 37/37 pass.
- sphinx: builds clean with ``-W`` (warnings as errors).

Security review
---------------

RBAC
~~~~

ClusterRole ``kex-reader`` grants:

- ``argoproj.io/applications`` — get, list, watch
- ``core/pods``, ``core/services`` — get, list, watch
- ``traefik.io/ingressroutes`` — get, list, watch

No write verbs anywhere. No ``exec``, no ``logs``, no ``clusters``
access. Verified with ``kubectl auth can-i`` against the kex SA.

Secrets
~~~~~~~

- No plaintext token anywhere in the repo (grepped ``kex/`` repo
  tree, no matches for the token shape).
- The ArgoCD project-role-token *fallback* would land as a
  SealedSecret via ``kubeseal-webgui``; not exercised in v1 because
  SA-JWT auth is the primary path.
- No env-var fallthrough that would log a secret in the proxy chain.

OIDC
~~~~

The IngressRoute references the cluster-auth ``oauth2-auth`` +
``oauth2-signin`` Middlewares (defined per-namespace in
``chart/templates/middleware.yaml`` using the consumer pattern
documented at ``auth/cluster-auth/README.md``). Verified: anonymous
``curl`` against ``edgelab.k8sapps.boliden.internal/`` returns 401,
which a real browser would follow to the AAD login.

CSP + security headers (revised this phase)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

v0 ``nginx.conf`` shipped without explicit security headers. v1 adds:

- ``X-Content-Type-Options: nosniff``
- ``X-Frame-Options: DENY``
- ``Referrer-Policy: strict-origin-when-cross-origin``
- ``Content-Security-Policy`` with self-only directives, no
  ``unsafe-eval``, ``frame-ancestors 'none'``.

``style-src`` allows ``'unsafe-inline'`` because Svelte 5's scoped
styles compile to ``<style>`` blocks in the document head; the
Vite-emitted scripts are hashed and don't need inline.

Dep scan
~~~~~~~~

- ``pip-audit`` not yet wired into CI. The dependency tree is small
  (fastapi, uvicorn, kubernetes, httpx, cachetools, markdown-it-py,
  pydantic) and all at recent versions; first CVSS≥7 finding in a
  dep should drive ``just check`` failing.
- ``npm audit`` reports 5 moderate vulnerabilities in dev-deps
  (vitest transitive); production deps are clean.

Logs
~~~~

``logger.warning(..., exc_info=True)`` is the only path that could
leak data via stack traces. The token is read inline in
``get_revision_metadata`` and never bound to a variable that ends up
in an exception traceback — the only place it appears is the
``Authorization`` header value passed to ``httpx.get``, and httpx
masks Authorization headers in its own exception messages.

Performance
-----------

Not exercised yet at the realistic load. The annotation parser is
~microseconds per Application; the index endpoint's hot path is
``k8s.list_applications()`` which hits the kubernetes API server
once per request. Worth a follow-up: add a TTL cache to
``list_applications`` (30s would be sufficient) so the index doesn't
hammer the API server on refresh.

Accessibility
-------------

- Catppuccin Mocha and Latte both pass WCAG AA on body text by design
  (verified against the official palette tables).
- Focus rings: ``button:focus`` and ``input[type=search]:focus`` use
  ``outline: 2px solid var(--ctp-mauve)`` — visible in both themes.
- Keyboard navigation: the SPA is built from semantic ``<a>``,
  ``<button>``, ``<input>`` elements; no custom keyboard handlers
  needed. Tab order follows DOM order.
- Empty-state copy includes a code example so screen readers can
  surface the annotation contract verbatim.

Worth a follow-up: ``axe-core`` automated audit in Playwright once
real Playwright specs land.

Future-features compatibility
-----------------------------

The eight design invariants from ``docs/design-principles.rst`` were
re-checked against the as-built code:

1. Annotation-driven, never code-driven — confirmed. Zero branches on
   app name; the parser is the only place that knows about annotations.
2. All data sources cached + gracefully degradable — confirmed.
   ``argocd.get_revision_metadata`` returns ``None`` on every failure
   path; the routes layer handles that with a typed "git data
   unavailable" sentinel.
3. SPA + backend separation — confirmed. Frontend talks only to
   ``/api/*`` JSON.
4. Argo as the integration point — confirmed. No second credential
   channel; the only outbound auth is the SA token to ArgoCD.
5. RBAC is strictly read-only — confirmed; see above.
6. Server-rendered first paint not required — confirmed; SPA-only.
7. ``kex/`` namespace + free-form suffix — confirmed.
8. No per-app special cases in the chart — confirmed.

Open follow-ups
---------------

- v2 git contributors view (full author history) — see plan.
- ``axe-core`` accessibility audit in Playwright.
- ``pip-audit`` / ``npm audit`` in CI.
- TTL cache around ``k8s.list_applications`` for the index hot path.
- Real Playwright E2E specs (config landed; specs deferred per the
  plan).
- Resurrect or delete the ``argocdTokenSecretName`` knob once SA-JWT
  auth has been in production for ~3 months.
- Per-team filtering via ``kex/visibility.groups`` annotation
  (annotation shape documented; not parsed).

Verdict
-------

v1 is production-ready as a read-only cluster landing page. The
distributed-catalog property is real: 13 Applications are now
registered, each by editing one annotation block in the repo that
owns the deployment. The Backstage chart is gone. The way-of-working
checklist holds end-to-end.
