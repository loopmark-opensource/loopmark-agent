#!/usr/bin/env python3
"""
Check links in the built docs site.

    python scripts/check_links.py              # internal links and #anchors (fast, offline)
    python scripts/check_links.py --external   # also request every external http(s) URL
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urlparse

SITE_DIR = Path(__file__).resolve().parent.parent / "site"
USER_AGENT = "loopmark-docs-link-check/1.0"


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value is None:
                continue
            if name == "id":
                self.ids.add(value)
            elif (name == "href" and tag in ("a", "link")) or (name == "src" and tag in ("script", "img")):
                self.links.append(value)


def _parse(path: Path) -> _LinkParser:
    parser = _LinkParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def check_internal(site_dir: Path = SITE_DIR) -> tuple[list[str], set[str]]:
    """Return (errors, external_urls) for every page in the site."""
    pages = {p.name: _parse(p) for p in sorted(site_dir.glob("*.html"))}
    errors: list[str] = []
    external: set[str] = set()

    for name, parsed in pages.items():
        for link in parsed.links:
            scheme = urlparse(link).scheme
            if scheme in ("http", "https"):
                external.add(link)
                continue
            if scheme in ("mailto", "tel"):
                continue
            target, anchor = urldefrag(link.split("?", 1)[0])
            target = target or name
            if not (site_dir / target).is_file():
                errors.append(f"{name}: broken link '{link}' (no site/{target})")
            elif anchor and target in pages and anchor not in pages[target].ids:
                errors.append(f"{name}: broken anchor '{link}' (no id '{anchor}' in {target})")
    return errors, external


def check_external(urls: set[str], timeout: float = 15.0) -> list[str]:
    errors: list[str] = []
    for url in sorted(urls):
        base = urldefrag(url)[0]
        request = urllib.request.Request(base, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:  # nosec B310 - http(s) only
                if resp.status >= 400:
                    errors.append(f"{url}: HTTP {resp.status}")
        except urllib.error.HTTPError as exc:
            # Many sites reject bots with 403/429; only treat "gone" responses as broken.
            if exc.code in (404, 410):
                errors.append(f"{url}: HTTP {exc.code}")
        except (urllib.error.URLError, TimeoutError) as exc:
            errors.append(f"{url}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--external", action="store_true", help="also check external http(s) links")
    args = parser.parse_args()

    errors, external = check_internal()
    if args.external:
        errors += check_external(external)

    for err in errors:
        print(f"ERROR {err}")
    checked = "internal + external" if args.external else "internal"
    print(f"Checked {checked} links: {len(errors)} problem(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
