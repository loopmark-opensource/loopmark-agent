"""Tests for the static docs site."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        "site.js",
        "search-index.json",
        "social-preview.png",
        "logo.png",
        "favicon.png",
        "apple-touch-icon.png",
    ):
        assert (SITE_DIR / name).exists(), f"missing site/{name}"


def test_homepage_has_json_ld_and_og_tags() -> None:
    html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
    assert 'application/ld+json' in html
    assert '"@type": "SoftwareApplication"' in html
    assert 'property="og:title"' in html
    assert 'property="og:image"' in html
    assert 'property="og:image:width"' in html
    assert "social-preview.png" in html


def test_social_preview_is_valid_png() -> None:
    data = (SITE_DIR / "social-preview.png").read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n"), "site/social-preview.png must be real PNG (not JPEG renamed)"


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


def test_internal_links_and_anchors_resolve() -> None:
    errors, _external = _load_script("check_links").check_internal(SITE_DIR)
    assert errors == []


def test_search_index_covers_every_page() -> None:
    entries = json.loads((SITE_DIR / "search-index.json").read_text(encoding="utf-8"))
    pages = {p.name for p in SITE_DIR.glob("*.html")}
    assert {e["url"] for e in entries} == pages
    assert all(e["title"] and e["text"] for e in entries)


def test_pages_have_search_and_theme_toggle() -> None:
    for page in SITE_DIR.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        assert 'id="site-search"' in html, page.name
        assert 'id="theme-toggle"' in html, page.name
        assert "site.js?v=" in html, page.name


def test_styles_define_dark_theme() -> None:
    css = (SITE_DIR / "styles.css").read_text(encoding="utf-8")
    assert '[data-theme="dark"]' in css
    assert "prefers-color-scheme: dark" in css


def test_api_reference_generated_from_docstrings() -> None:
    build = _load_script("build_docs_site")
    reference = build.api_reference()
    assert 'id="ref-run_agent"' in reference
    assert 'id="ref-agentresult"' in reference
    assert "User input text." in reference
    assert f"v{build.package_version()}" in reference


def test_built_site_is_up_to_date() -> None:
    """site/ must be regenerated (python scripts/build_docs_site.py) after editing the build script."""
    build = _load_script("build_docs_site")
    title, path, body, desc = build.PAGES["api.html"]
    expected = build.page(title, path, body.replace("{api_reference}", build.api_reference()), desc)
    assert (SITE_DIR / "api.html").read_text(encoding="utf-8") == expected


def test_pages_use_colored_logo_and_favicon() -> None:
    for name in ("logo.png", "favicon.png", "apple-touch-icon.png"):
        assert (SITE_DIR / name).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), name
    for page in SITE_DIR.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        assert 'rel="icon" type="image/png" href="favicon.png"' in html, page.name
        assert '<img src="logo.png"' in html, page.name
