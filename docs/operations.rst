Operations
==========

Deployment
----------

kex is deployed via ArgoCD from the ``chart/`` directory of this repo.
The image is built and pushed by GitHub Actions to ``ghcr.io/jonatanolofsson/kex``
on every tag.

ArgoCD authentication
---------------------

kex authenticates to ArgoCD's HTTP API using its own Kubernetes
ServiceAccount JWT, verified by ``argocd-server`` via ``TokenReview``.
There is **no long-lived static token** to rotate.

Cluster-side setup (one-time):

.. code-block:: yaml

   # argocd-cm
   data:
     accounts.kex: apiKey, login
     accounts.kex.enabled: "true"

   # argocd-rbac-cm
   data:
     policy.csv: |
       p, kex, applications, get, */*, allow
       p, kex, applications, list, */*, allow
       p, kex, repositories, get, *, allow
       g, system:serviceaccount:kex:kex, kex

If SA-JWT verification turns out to need apiserver flags that aren't
configured, fall back to a long-lived project-role token sealed via
``kubeseal-webgui``.

Troubleshooting
---------------

ArgoCD reachable check from inside the pod:

.. code-block:: bash

   kubectl exec -n kex deploy/kex -- \
     curl -sf -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
     https://argocd-server.argocd.svc/api/v1/applications | jq '.items | length'
