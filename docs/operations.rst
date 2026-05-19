Operations
==========

Deployment
----------

kex is deployed via ArgoCD from the ``chart/`` directory of this repo.
The image is built and pushed by GitHub Actions to ``ghcr.io/jonatanolofsson/kex``
on every tag.

ArgoCD authentication
---------------------

kex authenticates to ArgoCD's HTTP API with a long-lived account
token, issued once a year by an operator and committed to the
platform repo as a SealedSecret. The SA-JWT path was evaluated but
needs argocd-cm tuning beyond what's currently in place; the
account-token path mirrors the existing backstage-readonly pattern
and is the supported model today.

Cluster-side setup (one-time, already in place on EdgeLab):

.. code-block:: yaml

   # argocd-cm  (ops/argocd-config/templates/argocd-cm-config-overrides.yaml)
   data:
     accounts.kex: apiKey
     accounts.kex.enabled: "true"

   # argocd-rbac-cm  (auth/rbac/templates/argocd-rbac.yaml)
   data:
     policy.csv: |
       p, role:kex-readonly, applications, get, */*, allow
       p, role:kex-readonly, applications, list, */*, allow
       p, role:kex-readonly, projects, get, *, allow
       p, role:kex-readonly, repositories, get, *, allow
       g, kex, role:kex-readonly

Rotating the token (yearly, or sooner if compromised)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run from a dev shell that has both ``argocd`` and ``kubeseal``
available (the kex repo's nix flake provides both):

.. code-block:: bash

   # 1. Log in with your OIDC session (browser opens).
   argocd login argocd-styles.k8sapps.boliden.internal --grpc-web --sso

   # 2. Generate a fresh token for the kex account.
   TOKEN=$(argocd account generate-token \
       --account kex --expires-in 12months)

   # 3. Encrypt the token strict-scoped to the kex namespace + the
   #    secret name the deployment reads ARGOCD_AUTH_TOKEN from.
   SEALED=$(echo -n "$TOKEN" | kubeseal --raw \
       --namespace kex --name kex-argocd-token \
       --controller-namespace sealed-secrets \
       --scope strict)

   # 4. Paste $SEALED into default-helm-charts-ARGO's
   #    values-edgelab.yaml under kex.argocdToken.sealedValue,
   #    commit, push. ArgoCD reconciles within ~3 min and the new
   #    Secret materialises in the kex namespace.

The previous token can be revoked from ArgoCD after the new one is
verified active::

   argocd account delete-token --account kex <old-token-id>

Troubleshooting
---------------

ArgoCD reachable check from inside the pod:

.. code-block:: bash

   kubectl exec -n kex deploy/kex -- \
     curl -sf -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
     https://argocd-server.argocd.svc/api/v1/applications | jq '.items | length'
