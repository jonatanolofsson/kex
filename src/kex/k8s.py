"""Thin wrapper around the ``kubernetes`` Python client.

Loads in-cluster config when ``KUBERNETES_SERVICE_HOST`` is present
(i.e. running as a pod), otherwise falls back to ``~/.kube/config``
for local dev.

All functions return plain Python dicts. The annotation parser
(:mod:`kex.annotations`) and the routes layer consume those without
needing to know about the kubernetes client's typed objects.

Graceful failure: cluster unreachable → callers receive an empty list
and a logged warning, not an exception. The UI renders an empty state.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)

ARGO_GROUP = "argoproj.io"
ARGO_VERSION = "v1alpha1"
ARGO_PLURAL = "applications"
ARGO_NAMESPACE = "argocd"

TRAEFIK_GROUP = "traefik.io"
TRAEFIK_VERSION = "v1alpha1"
TRAEFIK_PLURAL = "ingressroutes"

_loaded = False


def _ensure_config() -> None:
    """Lazy-load the kube config exactly once per process."""
    global _loaded
    if _loaded:
        return
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        config.load_incluster_config()
        logger.info("kex: loaded in-cluster kube config")
    else:
        try:
            config.load_kube_config()
            logger.info("kex: loaded kube config from ~/.kube/config")
        except Exception:
            logger.warning("kex: no kube config available; cluster calls will fail")
    _loaded = True


def list_applications() -> list[dict[str, Any]]:
    """Return every ArgoCD ``Application`` in the ``argocd`` namespace.

    Failure to reach the API server is logged and returns ``[]``; the
    UI's empty state then renders with a friendly message.
    """
    try:
        _ensure_config()
        api = client.CustomObjectsApi()
        result = api.list_namespaced_custom_object(
            group=ARGO_GROUP,
            version=ARGO_VERSION,
            namespace=ARGO_NAMESPACE,
            plural=ARGO_PLURAL,
        )
        return list(result.get("items", []))
    except (ApiException, Exception):
        logger.warning("kex: failed to list ArgoCD Applications", exc_info=True)
        return []


def get_application(name: str) -> dict[str, Any] | None:
    """Fetch a single Application by name; ``None`` if not found / unreachable."""
    try:
        _ensure_config()
        api = client.CustomObjectsApi()
        return api.get_namespaced_custom_object(
            group=ARGO_GROUP,
            version=ARGO_VERSION,
            namespace=ARGO_NAMESPACE,
            plural=ARGO_PLURAL,
            name=name,
        )
    except ApiException as exc:
        if exc.status == 404:
            return None
        logger.warning("kex: failed to get Application %s", name, exc_info=True)
        return None
    except Exception:
        logger.warning("kex: failed to get Application %s", name, exc_info=True)
        return None


def list_pods(namespace: str) -> list[dict[str, Any]]:
    """List pods in ``namespace`` as plain dicts; ``[]`` on failure."""
    if not namespace:
        return []
    try:
        _ensure_config()
        api = client.CoreV1Api()
        result = api.list_namespaced_pod(namespace=namespace)
        return [_pod_to_dict(pod) for pod in result.items]
    except Exception:
        logger.warning("kex: failed to list pods in %s", namespace, exc_info=True)
        return []


def list_ingressroutes(namespace: str) -> list[dict[str, Any]]:
    """List Traefik ``IngressRoute`` CRs in ``namespace``; ``[]`` on failure."""
    if not namespace:
        return []
    try:
        _ensure_config()
        api = client.CustomObjectsApi()
        result = api.list_namespaced_custom_object(
            group=TRAEFIK_GROUP,
            version=TRAEFIK_VERSION,
            namespace=namespace,
            plural=TRAEFIK_PLURAL,
        )
        return list(result.get("items", []))
    except Exception:
        logger.warning("kex: failed to list ingressroutes in %s", namespace, exc_info=True)
        return []


def _pod_to_dict(pod: Any) -> dict[str, Any]:
    """Flatten a V1Pod to the few fields the detail-page table needs.

    Going via plain dicts keeps the rest of the codebase free from
    kubernetes-client typed objects, which simplifies testing.
    """
    status = pod.status
    spec = pod.spec
    ready = 0
    total = 0
    restarts = 0
    if status and status.container_statuses:
        for cs in status.container_statuses:
            total += 1
            if cs.ready:
                ready += 1
            restarts += cs.restart_count or 0
    return {
        "name": pod.metadata.name,
        "phase": status.phase if status else "Unknown",
        "ready": f"{ready}/{total}" if total else "0/0",
        "restarts": restarts,
        "creation_timestamp": (
            pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
        ),
        "node": spec.node_name if spec else None,
    }
