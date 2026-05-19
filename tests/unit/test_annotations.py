"""Unit tests for :mod:`kex.annotations`.

Parser is pure — no I/O, no mocking needed. Cases cover the
display-field defaults, the free-form ``kex/links.*`` suffix grammar,
status/git extraction, and edge cases (empty annotations, missing
spec, malformed history).
"""

from __future__ import annotations

import pytest

from kex.annotations import Link, is_enabled, parse


def _app(annotations=None, spec=None, status=None, name="example"):
    return {
        "metadata": {"name": name, "annotations": annotations or {}},
        "spec": spec or {},
        "status": status or {},
    }


class TestIsEnabled:
    def test_true_value(self) -> None:
        assert is_enabled(_app({"kex/enabled": "true"})) is True

    def test_true_case_insensitive(self) -> None:
        assert is_enabled(_app({"kex/enabled": "TRUE"})) is True

    def test_false_value(self) -> None:
        assert is_enabled(_app({"kex/enabled": "false"})) is False

    def test_missing(self) -> None:
        assert is_enabled(_app({})) is False

    def test_no_annotations_block(self) -> None:
        assert is_enabled({"metadata": {"name": "x"}}) is False

    def test_no_metadata_block(self) -> None:
        assert is_enabled({}) is False


class TestParseDefaults:
    def test_minimal_application(self) -> None:
        meta = parse(_app({}, name="my-app"))
        assert meta.name == "my-app"
        assert meta.title == "my-app"  # defaults to name
        assert meta.description == ""
        assert meta.group == "Other"
        assert meta.icon is None
        assert meta.about == ""
        assert meta.links == []
        assert meta.namespace == ""
        assert meta.repo_url is None
        assert meta.git_path is None
        assert meta.sync_status is None
        assert meta.health_status is None
        assert meta.sync_revision is None
        assert meta.history == []


class TestParseAnnotations:
    def test_title_description_group_icon(self) -> None:
        meta = parse(
            _app(
                {
                    "kex/title": "My App",
                    "kex/description": "Short blurb",
                    "kex/group": "ML Platform",
                    "kex/icon": "rocket",
                }
            )
        )
        assert meta.title == "My App"
        assert meta.description == "Short blurb"
        assert meta.group == "ML Platform"
        assert meta.icon == "rocket"

    def test_about_markdown_passthrough(self) -> None:
        about = "**bold** and a list:\n- a\n- b\n"
        meta = parse(_app({"kex/about": about}))
        assert meta.about == about  # parser keeps markdown raw

    def test_unrelated_annotations_ignored(self) -> None:
        meta = parse(
            _app(
                {
                    "kubectl.kubernetes.io/last-applied-configuration": "{...}",
                    "argocd.argoproj.io/manifest-generate-paths": ".",
                }
            )
        )
        assert meta.title == "example"


class TestLinks:
    def test_links_sorted_by_label(self) -> None:
        meta = parse(
            _app(
                {
                    "kex/links.grafana": "https://grafana/x",
                    "kex/links.argo": "https://argo/x",
                    "kex/links.docs": "https://docs/x",
                }
            )
        )
        assert meta.links == [
            Link("argo", "https://argo/x"),
            Link("docs", "https://docs/x"),
            Link("grafana", "https://grafana/x"),
        ]

    def test_empty_link_value_dropped(self) -> None:
        meta = parse(
            _app(
                {
                    "kex/links.docs": "https://docs/x",
                    "kex/links.empty": "",
                }
            )
        )
        assert meta.links == [Link("docs", "https://docs/x")]

    def test_no_links(self) -> None:
        assert parse(_app({})).links == []


class TestSpecExtraction:
    def test_namespace_from_destination(self) -> None:
        meta = parse(_app({}, spec={"destination": {"namespace": "platform"}}))
        assert meta.namespace == "platform"

    def test_repo_url_from_source(self) -> None:
        meta = parse(_app({}, spec={"source": {"repoURL": "git@host/group/repo"}}))
        assert meta.repo_url == "git@host/group/repo"

    def test_git_path_defaults_to_source_path(self) -> None:
        meta = parse(_app({}, spec={"source": {"path": "apps/recorder/"}}))
        assert meta.git_path == "apps/recorder/"

    def test_git_path_annotation_overrides_source_path(self) -> None:
        meta = parse(
            _app(
                {"kex/git.path": "apps/sub/"},
                spec={"source": {"path": "apps/whole/"}},
            )
        )
        assert meta.git_path == "apps/sub/"


class TestStatus:
    def test_sync_health_revision(self) -> None:
        meta = parse(
            _app(
                {},
                status={
                    "sync": {"status": "Synced", "revision": "abc123"},
                    "health": {"status": "Healthy"},
                },
            )
        )
        assert meta.sync_status == "Synced"
        assert meta.health_status == "Healthy"
        assert meta.sync_revision == "abc123"

    def test_history_truncated_to_last_five(self) -> None:
        history = [{"revision": f"r{i}"} for i in range(8)]
        meta = parse(_app({}, status={"history": history}))
        assert len(meta.history) == 5
        # Keeps the *last* five, not the first
        assert meta.history[-1]["revision"] == "r7"

    def test_history_not_a_list(self) -> None:
        meta = parse(_app({}, status={"history": "garbage"}))
        assert meta.history == []


@pytest.mark.parametrize(
    "broken",
    [
        {"metadata": None},
        {"metadata": {"annotations": None}},
        {"spec": None, "status": None, "metadata": {"name": "x"}},
    ],
)
def test_parse_handles_missing_blocks(broken: dict) -> None:
    """``None`` for any top-level block should not raise."""
    meta = parse(broken)
    assert isinstance(meta.name, str)
    assert meta.links == []


class TestGroupWeight:
    """``kex/groupweight`` — between-group ordering."""

    def test_missing_defaults_to_zero(self) -> None:
        assert parse(_app({})).group_weight == 0.0

    def test_positive_integer(self) -> None:
        assert parse(_app({"kex/groupweight": "10"})).group_weight == 10.0

    def test_negative_float(self) -> None:
        assert parse(_app({"kex/groupweight": "-2.5"})).group_weight == -2.5

    def test_malformed_falls_back_to_zero(self) -> None:
        assert parse(_app({"kex/groupweight": "high-priority"})).group_weight == 0.0

    def test_empty_string_defaults_to_zero(self) -> None:
        assert parse(_app({"kex/groupweight": ""})).group_weight == 0.0

    def test_does_not_read_old_kex_weight(self) -> None:
        """The pre-rename key (``kex/weight``) must not bleed into group_weight."""
        meta = parse(_app({"kex/weight": "-30"}))
        assert meta.group_weight == 0.0
        assert meta.weight == -30.0


class TestWeight:
    """``kex/weight`` — within-group ordering."""

    def test_missing_defaults_to_zero(self) -> None:
        assert parse(_app({})).weight == 0.0

    def test_positive_integer(self) -> None:
        assert parse(_app({"kex/weight": "10"})).weight == 10.0

    def test_negative_float(self) -> None:
        assert parse(_app({"kex/weight": "-2.5"})).weight == -2.5

    def test_malformed_falls_back_to_zero(self) -> None:
        assert parse(_app({"kex/weight": "first-please"})).weight == 0.0

    def test_empty_string_defaults_to_zero(self) -> None:
        assert parse(_app({"kex/weight": ""})).weight == 0.0

    def test_independent_of_groupweight(self) -> None:
        """Setting one annotation must not affect the other."""
        meta = parse(_app({"kex/weight": "-10", "kex/groupweight": "-30"}))
        assert meta.weight == -10.0
        assert meta.group_weight == -30.0
