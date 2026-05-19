"""Shared MarkdownIt instance.

All kex surfaces that render operator-authored markdown (the per-app
``kex/about`` block and the cluster-wide ``ui.welcomeMarkdown``) go
through this single configuration so the policy is one place:

- ``commonmark`` preset (no GFM extras kex doesn't already need)
- ``breaks: True`` — single newlines render as ``<br>``, matching how
  operators usually compose short paragraphs in YAML
- ``html: False`` — raw HTML in the source is escaped, not passed
  through. The configmap is operator-edited inside the cluster, but
  the rendered HTML is served to a browser; keep the XSS surface
  closed by policy rather than by trust.
"""

from __future__ import annotations

from markdown_it import MarkdownIt

md = MarkdownIt("commonmark", {"breaks": True, "html": False})
