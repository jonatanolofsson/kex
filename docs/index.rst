kex — Kubernetes index for the EdgeLab cluster
================================================

kex is an annotation-driven cluster landing page + per-app detail view.
Each ArgoCD ``Application`` CR carries ``kex/*`` annotations describing
its tile (title, description, group, links, …); kex scans the cluster
and renders one row per application.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   architecture
   annotations
   operations
   design-principles
   contributing
   retrospective-v1
