"""Integration tests for the ``/api/apps*`` routes.

We don't talk to a real cluster — :mod:`kex.k8s` is monkey-patched
with hand-built dicts in the shape ``CustomObjectsApi.list/get``
returns, and :mod:`kex.argocd` is intercepted at the httpx layer via
``respx``.

The cases cover: visibility filtering, the empty state, the detail
fan-out (pods + ingresses + git), and the graceful-degradation path
when ArgoCD is unreachable.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from kex import argocd
from kex import k8s as k8s_module
from kex.main import app


@pytest.fixture(autouse=True)
def reset_argocd_cache() -> None:
    """Each test gets a fresh in-process cache."""
    argocd._metadata_cache.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _app_doc(
    name: str,
    *,
    enabled: bool = True,
    title: str | None = None,
    description: str = "",
    group: str = "Other",
    namespace: str = "platform",
    revision: str | None = None,
    sync: str = "Synced",
    health: str = "Healthy",
    links: dict[str, str] | None = None,
    about: str = "",
    history: list[dict[str, str]] | None = None,
    weight: str | None = None,
    groupweight: str | None = None,
) -> dict[str, Any]:
    annotations: dict[str, str] = {}
    if enabled:
        annotations["kex/enabled"] = "true"
    if title:
        annotations["kex/title"] = title
    if description:
        annotations["kex/description"] = description
    annotations["kex/group"] = group
    if about:
        annotations["kex/about"] = about
    if weight is not None:
        annotations["kex/weight"] = weight
    if groupweight is not None:
        annotations["kex/groupweight"] = groupweight
    for key, value in (links or {}).items():
        annotations[f"kex/links.{key}"] = value

    status: dict[str, Any] = {
        "sync": {"status": sync},
        "health": {"status": health},
    }
    if revision:
        status["sync"]["revision"] = revision
    if history:
        status["history"] = history

    return {
        "metadata": {"name": name, "annotations": annotations},
        "spec": {"destination": {"namespace": namespace}, "source": {"path": "."}},
        "status": status,
    }


@pytest.fixture
def fake_cluster(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Patch the k8s module to return canned data.

    Returns a mutable state dict so individual tests can adjust the
    application list / pods / ingressroutes.
    """
    state: dict[str, Any] = {
        "applications": [],
        "pods": {},
        "ingressroutes": {},
    }

    def fake_list_applications() -> list[dict[str, Any]]:
        return list(state["applications"])

    def fake_get_application(name: str) -> dict[str, Any] | None:
        for app_doc in state["applications"]:
            if (app_doc.get("metadata") or {}).get("name") == name:
                return app_doc
        return None

    def fake_list_pods(namespace: str) -> list[dict[str, Any]]:
        return list(state["pods"].get(namespace, []))

    def fake_list_ingressroutes(namespace: str) -> list[dict[str, Any]]:
        return list(state["ingressroutes"].get(namespace, []))

    monkeypatch.setattr(k8s_module, "list_applications", fake_list_applications)
    monkeypatch.setattr(k8s_module, "get_application", fake_get_application)
    monkeypatch.setattr(k8s_module, "list_pods", fake_list_pods)
    monkeypatch.setattr(k8s_module, "list_ingressroutes", fake_list_ingressroutes)
    return state


@pytest.fixture
def fake_token(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Provide an in-memory SA token via the env var override."""
    token_file = tmp_path / "token"
    token_file.write_text("fake-jwt")
    monkeypatch.setattr(argocd, "TOKEN_PATH", token_file)


class TestListApps:
    def test_empty_state(self, client: TestClient, fake_cluster: dict[str, Any]) -> None:
        resp = client.get("/api/apps")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_only_enabled_apps_listed(
        self, client: TestClient, fake_cluster: dict[str, Any]
    ) -> None:
        fake_cluster["applications"] = [
            _app_doc("visible", title="Visible", group="A"),
            _app_doc("hidden", enabled=False),
        ]
        rows = client.get("/api/apps").json()
        assert [row["name"] for row in rows] == ["visible"]

    def test_card_shape(self, client: TestClient, fake_cluster: dict[str, Any]) -> None:
        fake_cluster["applications"] = [
            _app_doc(
                "one",
                title="One",
                description="Short blurb",
                group="ML Platform",
            )
        ]
        row = client.get("/api/apps").json()[0]
        assert row["title"] == "One"
        assert row["description"] == "Short blurb"
        assert row["group"] == "ML Platform"
        assert row["sync_status"] == "Synced"
        assert row["health_status"] == "Healthy"


class TestDetail:
    def test_404_when_app_missing(self, client: TestClient, fake_cluster: dict[str, Any]) -> None:
        resp = client.get("/api/apps/missing")
        assert resp.status_code == 404

    def test_404_when_app_disabled(self, client: TestClient, fake_cluster: dict[str, Any]) -> None:
        fake_cluster["applications"] = [_app_doc("hidden", enabled=False)]
        resp = client.get("/api/apps/hidden")
        assert resp.status_code == 404

    def test_about_rendered_as_html(self, client: TestClient, fake_cluster: dict[str, Any]) -> None:
        fake_cluster["applications"] = [_app_doc("a", about="**bold**")]
        body = client.get("/api/apps/a").json()
        assert "<strong>bold</strong>" in body["about_html"]

    def test_links_sorted(self, client: TestClient, fake_cluster: dict[str, Any]) -> None:
        fake_cluster["applications"] = [
            _app_doc(
                "a",
                links={"grafana": "g", "argo": "a", "docs": "d"},
            )
        ]
        body = client.get("/api/apps/a").json()
        assert [link["label"] for link in body["links"]] == [
            "argo",
            "docs",
            "grafana",
        ]

    def test_pods_included_from_destination_namespace(
        self, client: TestClient, fake_cluster: dict[str, Any]
    ) -> None:
        fake_cluster["applications"] = [_app_doc("a", namespace="platform")]
        fake_cluster["pods"]["platform"] = [
            {
                "name": "pod-1",
                "phase": "Running",
                "ready": "1/1",
                "restarts": 0,
                "creation_timestamp": None,
                "node": "n1",
            },
        ]
        body = client.get("/api/apps/a").json()
        assert body["pods"][0]["name"] == "pod-1"

    def test_ingressroutes_flattened(
        self, client: TestClient, fake_cluster: dict[str, Any]
    ) -> None:
        fake_cluster["applications"] = [_app_doc("a", namespace="ns")]
        fake_cluster["ingressroutes"]["ns"] = [
            {
                "spec": {
                    "routes": [
                        {"match": "Host(`a.example`) && PathPrefix(`/p/`)"},
                        {"match": "Host(`b.example`)"},
                    ]
                }
            }
        ]
        body = client.get("/api/apps/a").json()
        assert {(ing["host"], ing["path"]) for ing in body["ingresses"]} == {
            ("a.example", "/p/"),
            ("b.example", "/"),
        }

    def test_path_only_ingressroutes_dropped(
        self, client: TestClient, fake_cluster: dict[str, Any]
    ) -> None:
        """An IngressRoute without a Host() — e.g. an internal PathPrefix
        catch-all like the kubernetes-dashboard's
        `/clusters/main/fetchAllowedNamespaces` route — must not surface as
        a user-navigable URL on the detail page (was issue 1 of v1.1)."""
        fake_cluster["applications"] = [_app_doc("a", namespace="ns")]
        fake_cluster["ingressroutes"]["ns"] = [
            {
                "spec": {
                    "routes": [
                        {"match": "Host(`a.example`)"},
                        {"match": "PathPrefix(`/internal/`)"},
                    ]
                }
            }
        ]
        body = client.get("/api/apps/a").json()
        # Only the Host()-shaped route surfaces.
        assert body["ingresses"] == [{"host": "a.example", "path": "/"}]


class TestQuickLinksOnCard:
    """The list response promotes `kex/links.app` and `kex/links.docs` to
    a per-card `quick_links` array so the SPA can render them without
    pulling the full detail-page response. Other `kex/links.*` stay in
    the detail-page sidebar only."""

    def test_no_links_no_quick_links(
        self, client: TestClient, fake_cluster: dict[str, Any]
    ) -> None:
        fake_cluster["applications"] = [_app_doc("a")]
        row = client.get("/api/apps").json()[0]
        assert row["quick_links"] == []

    def test_only_app_slot_promoted(self, client: TestClient, fake_cluster: dict[str, Any]) -> None:
        fake_cluster["applications"] = [
            _app_doc("a", links={"app": "https://app/", "grafana": "https://g/"}),
        ]
        row = client.get("/api/apps").json()[0]
        assert [q["label"] for q in row["quick_links"]] == ["app"]
        assert row["quick_links"][0]["url"] == "https://app/"

    def test_app_and_docs_in_order(self, client: TestClient, fake_cluster: dict[str, Any]) -> None:
        fake_cluster["applications"] = [
            _app_doc(
                "a",
                links={
                    "docs": "https://docs/",
                    "app": "https://app/",
                    "grafana": "https://g/",
                },
            ),
        ]
        row = client.get("/api/apps").json()[0]
        # app always before docs, regardless of annotation declaration order
        assert [q["label"] for q in row["quick_links"]] == ["app", "docs"]
        assert all("icon" in q and q["icon"] for q in row["quick_links"])


class TestSortingInResponse:
    def test_list_response_carries_both_axes(
        self, client: TestClient, fake_cluster: dict[str, Any]
    ) -> None:
        fake_cluster["applications"] = [
            _app_doc("defaulted"),
            _app_doc("in-group-first", weight="-10"),
            _app_doc("group-anchor", groupweight="-30"),
            _app_doc("both", weight="-5", groupweight="-15"),
        ]
        rows = {row["name"]: row for row in client.get("/api/apps").json()}

        assert rows["defaulted"]["weight"] == 0.0
        assert rows["defaulted"]["group_weight"] == 0.0

        assert rows["in-group-first"]["weight"] == -10.0
        assert rows["in-group-first"]["group_weight"] == 0.0

        assert rows["group-anchor"]["weight"] == 0.0
        assert rows["group-anchor"]["group_weight"] == -30.0

        assert rows["both"]["weight"] == -5.0
        assert rows["both"]["group_weight"] == -15.0

    def test_detail_response_carries_both_axes(
        self, client: TestClient, fake_cluster: dict[str, Any]
    ) -> None:
        fake_cluster["applications"] = [_app_doc("a", weight="-10", groupweight="-30")]
        body = client.get("/api/apps/a").json()
        assert body["weight"] == -10.0
        assert body["group_weight"] == -30.0


class TestGitFanout:
    def test_latest_commit_via_argocd(
        self,
        client: TestClient,
        fake_cluster: dict[str, Any],
        fake_token: None,
    ) -> None:
        fake_cluster["applications"] = [_app_doc("a", revision="abc123")]
        with respx.mock(assert_all_called=False) as mock:
            mock.get(
                f"{argocd.ARGOCD_SERVER}/api/v1/applications/a/revisions/abc123/metadata"
            ).mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "author": "Jonatan Olofsson <jonatan@boliden.com>",
                        "date": "2026-05-18T05:31:00Z",
                        "message": "feat: do a thing",
                    },
                )
            )
            body = client.get("/api/apps/a").json()
        assert body["latest_commit"]["author"] == "Jonatan Olofsson"
        assert body["latest_commit"]["email"] == "jonatan@boliden.com"
        assert body["latest_commit"]["message"] == "feat: do a thing"

    def test_argocd_unreachable_degrades_gracefully(
        self,
        client: TestClient,
        fake_cluster: dict[str, Any],
        fake_token: None,
    ) -> None:
        fake_cluster["applications"] = [_app_doc("a", revision="abc123")]
        with respx.mock(assert_all_called=False) as mock:
            mock.get(
                f"{argocd.ARGOCD_SERVER}/api/v1/applications/a/revisions/abc123/metadata"
            ).mock(side_effect=httpx.ConnectError("unreachable"))
            body = client.get("/api/apps/a").json()
        # Page still renders; git column carries no commit.
        assert body["latest_commit"] is None
        assert body["recent_deployers"] == []
        # Non-git sections still populated
        assert body["title"] == "a"

    def test_no_revision_skips_git_lookup(
        self, client: TestClient, fake_cluster: dict[str, Any]
    ) -> None:
        fake_cluster["applications"] = [_app_doc("a", revision=None)]
        body = client.get("/api/apps/a").json()
        assert body["latest_commit"] is None
        assert body["recent_deployers"] == []
