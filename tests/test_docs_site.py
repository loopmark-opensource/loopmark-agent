"""Tests for the static docs site."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"


def test_docs_pages_exist() -> None:
    for name in (
        "index.html",
        "features.html",
        "install.html",
        "audience-research.html",
        "api.html",
        "sitemap.xml",
        "robots.txt",
        "styles.css",
        "social-preview.png",
    ):
        assert (SITE_DIR / name).exists(), f"missing site/{name}"


def test_homepage_has_json_ld_and_og_tags() -> None:
    html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
    assert 'application/ld+json' in html
    assert '"@type": "SoftwareApplication"' in html
    assert 'property="og:title"' in html
    assert 'property="og:image"' in html
    assert "social-preview.png" in html


def test_sitemap_lists_core_pages() -> None:
    sitemap = (SITE_DIR / "sitemap.xml").read_text(encoding="utf-8")
    for path in ("/install.html", "/api.html", "/features.html"):
        assert path in sitemap


def test_json_ld_is_valid_json() -> None:
    html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
    start = html.index('type="application/ld+json">') + len('type="application/ld+json">')
    end = html.index("</script>", start)
    data = json.loads(html[start:end])
    assert data["@type"] == "SoftwareApplication"
    assert data["offers"]["price"] == "0"
