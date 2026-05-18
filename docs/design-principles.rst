Design principles
=================

Invariants future contributors should keep:

1. **Annotation-driven, never code-driven for per-app metadata.** A
   new field on the app card becomes a new ``kex/*`` annotation that
   the parser handles, not a switch statement keyed on app name. Code
   never knows about specific apps.
2. **All data sources cached, all gracefully degradable.** Every
   external dependency (k8s API, ArgoCD API, future git access) is
   wrapped behind a function that returns either real data or a typed
   "unavailable" sentinel that the UI renders explicitly.
3. **SPA + backend separation.** The frontend talks only to ``/api/*``
   JSON. Backend can be replaced or split without UI changes.
4. **Argo as the integration point, not git directly.** kex's
   connection to git is mediated by ArgoCD, which already holds
   credentials. Never introduce a second credential channel.
5. **RBAC is strictly read-only.** Action features (record/stop,
   restart, sync) would require an explicit ClusterRole expansion +
   separate threat-model review.
6. **Server-rendered first paint is not required.** SPA load with a
   "loading…" state is fine.
7. **Annotation namespace is ``kex/`` with free-form suffix** where
   applicable (e.g. ``kex/links.<key>``). New top-level keys are
   documented in :doc:`annotations` before they're parsed.
8. **No per-app special cases in the chart.** Every app's row/detail
   is rendered by the same template path. Branching by app name is a
   smell.

If kex grows beyond "single FastAPI service + Svelte SPA," the right
move is to re-evaluate whether adopting the full ruskin framework is
now worth it — not to manually re-implement parts of it.
