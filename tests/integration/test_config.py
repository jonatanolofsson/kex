"""Integration tests for ``GET /api/config``.

The route reads ``ui.json`` once at module import. To test multiple
shapes we patch the module-level ``CONFIG_FILE`` to a ``tmp_path`` file
and re-run ``_load_config_payload()`` before each request, re-assigning
the cached ``_payload``.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from kex import routes
from kex.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def config_override(monkeypatch, tmp_path):
    """Point the config module at a ``tmp_path`` file and return a setter.

    Usage::

        config_override({...})       # dict → json-encoded into the file
        config_override("{garbage")  # raw string → file content as-is
        config_override(None)         # don't create the file
    """
    config_file = tmp_path / "ui.json"
    monkeypatch.setattr(routes.config, "CONFIG_FILE", config_file)

    def _apply(payload):
        if payload is None:
            return
        if isinstance(payload, str):
            config_file.write_text(payload)
        else:
            config_file.write_text(json.dumps(payload))
        new_payload = routes.config._load_config_payload()
        monkeypatch.setattr(routes.config, "_payload", new_payload)

    return _apply


@pytest.fixture
def reset_payload(monkeypatch):
    """For the missing-file case, force the payload to the all-empty default."""

    def _apply():
        monkeypatch.setattr(routes.config, "_payload", routes.config._load_config_payload())

    return _apply


class TestConfigRoute:
    def test_missing_file_returns_empty_defaults(
        self, client: TestClient, config_override, reset_payload
    ) -> None:
        config_override(None)
        reset_payload()
        body = client.get("/api/config").json()
        assert body == {
            "cluster_name": "",
            "hero_tagline": "",
            "header_links": [],
            "welcome_html": "",
        }

    def test_valid_json_round_trips(self, client: TestClient, config_override) -> None:
        config_override(
            {
                "clusterName": "EdgeLab",
                "heroTagline": "Welcome operators.",
                "headerLinks": [
                    {"label": "Docs", "url": "https://example/docs", "icon": "book"},
                ],
                "welcomeMarkdown": "Hello **world**.",
            }
        )
        body = client.get("/api/config").json()
        assert body["cluster_name"] == "EdgeLab"
        assert body["hero_tagline"] == "Welcome operators."
        assert body["header_links"] == [
            {"label": "Docs", "url": "https://example/docs", "icon": "book"},
        ]
        assert "<strong>world</strong>" in body["welcome_html"]

    def test_malformed_json_degrades_to_empty(self, client: TestClient, config_override) -> None:
        config_override("{not valid json")
        body = client.get("/api/config").json()
        assert body["cluster_name"] == ""
        assert body["welcome_html"] == ""

    def test_root_must_be_object(self, client: TestClient, config_override) -> None:
        config_override("[1, 2, 3]")
        body = client.get("/api/config").json()
        assert body["cluster_name"] == ""

    def test_header_links_filter_out_incomplete_entries(
        self, client: TestClient, config_override
    ) -> None:
        config_override(
            {
                "headerLinks": [
                    {"label": "Docs", "url": "https://docs"},
                    {"label": "", "url": "https://no-label"},
                    {"label": "No URL", "url": ""},
                    "not-an-object",
                ],
            }
        )
        body = client.get("/api/config").json()
        assert body["header_links"] == [
            {"label": "Docs", "url": "https://docs", "icon": None},
        ]

    def test_header_links_not_a_list_yields_empty(
        self, client: TestClient, config_override
    ) -> None:
        config_override({"headerLinks": "not-a-list"})
        body = client.get("/api/config").json()
        assert body["header_links"] == []

    def test_welcome_markdown_escapes_html(self, client: TestClient, config_override) -> None:
        """``html: False`` policy on the shared MarkdownIt instance must
        escape inline HTML rather than passing it through (the SPA
        renders the result via ``{@html}``)."""
        config_override({"welcomeMarkdown": "<script>alert(1)</script>"})
        body = client.get("/api/config").json()
        assert "<script>" not in body["welcome_html"]
        assert "&lt;script&gt;" in body["welcome_html"]

    def test_empty_welcome_yields_empty_html(self, client: TestClient, config_override) -> None:
        config_override({"welcomeMarkdown": ""})
        body = client.get("/api/config").json()
        assert body["welcome_html"] == ""
