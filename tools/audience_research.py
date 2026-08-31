"""Audience research: website analysis and CRM segment persona generation."""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
_OFFERING_BAD_START = re.compile(
    r"^(that|which|who|whom|whose|to|for|and|or|the|a|an|help|helps|helping|our|your|with|in|on|at|"
    r"serving|deliver(?:s|ing)?|we|tools|tech)\b",
    re.I,
)


class _PageMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.keywords = ""
        self.h1: list[str] = []
        self.h2: list[str] = []
        self.paragraphs: list[str] = []
        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False
        self._in_p = False
        self._buf = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
            self._buf = ""
        elif tag == "h2":
            self._in_h2 = True
            self._buf = ""
        elif tag == "p":
            self._in_p = True
            self._buf = ""
        elif tag == "meta":
            attr = dict(attrs)
            name = (attr.get("name") or attr.get("property") or "").lower()
            content = attr.get("content") or ""
            if name in ("description", "og:description") and content:
                self.description = content or self.description
            elif name == "keywords" and content:
                self.keywords = content

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
            text = self._buf.strip()
            if text and len(self.h1) < 5:
                self.h1.append(text)
        elif tag == "h2":
            self._in_h2 = False
            text = self._buf.strip()
            if text and len(self.h2) < 12:
                self.h2.append(text)
        elif tag == "p":
            self._in_p = False
            text = self._buf.strip()
            if text and len(text) > 40 and len(self.paragraphs) < 8:
                self.paragraphs.append(text[:400])

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title += text
        elif self._in_h1 or self._in_h2 or self._in_p:
            self._buf += (" " if self._buf else "") + text


def _strip_html(raw: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"https://{url}"
    return url


def _is_readable_text(text: str) -> bool:
    text = text.strip()
    if len(text) < 12:
        return False
    if re.search(r"[\{\};]|\.[a-zA-Z0-9_-]+\{", text):
        return False
    words = re.findall(r"[a-zA-Z]{3,}", text)
    if len(words) < 3:
        return False
    alpha = sum(ch.isalpha() or ch.isspace() for ch in text)
    return alpha / max(len(text), 1) >= 0.55


def _empty_site_result(url: str, error: str = "") -> dict[str, Any]:
    return {
        "url": url,
        "error": error,
        "title": "",
        "description": "",
        "keywords": "",
        "headings": "",
        "subheadings": "",
        "paragraphs": [],
        "structured_data": "",
        "social_links": {},
        "social_presence": [],
        "problem_phrases": [],
        "snippet": "",
    }


def _extract_json_ld_text(raw: str) -> str:
    chunks: list[str] = []
    for match in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        raw,
        re.I | re.S,
    ):
        try:
            data = json.loads(match.group(1))
            chunks.append(json.dumps(data)[:800])
        except json.JSONDecodeError:
            continue
    return " ".join(chunks)[:1500]


def _extract_social_links(raw_html: str) -> dict[str, str]:
    links: dict[str, str] = {}
    patterns = {
        "linkedin": r'https?://(?:[\w.-]+\.)?linkedin\.com/(?:company|in|school)/[A-Za-z0-9_%./-]+',
        "twitter": r'https?://(?:[\w.-]+\.)?(?:twitter|x)\.com/[A-Za-z0-9_./-]+',
        "facebook": r'https?://(?:[\w.-]+\.)?facebook\.com/[A-Za-z0-9_.-]+',
        "instagram": r'https?://(?:www\.)?instagram\.com/[A-Za-z0-9_.]+(?:\?[^"\'\s<>]*)?',
        "youtube": r'https?://(?:[\w.-]+\.)?youtube\.com/(?:@|channel/|c/)[A-Za-z0-9_./-]+',
        "tiktok": r'https?://(?:[\w.-]+\.)?tiktok\.com/@[A-Za-z0-9_.-]+',
    }
    href_patterns = {
        "linkedin": r'href=["\']?(https?://(?:[\w.-]+\.)?linkedin\.com/[^"\'#\s>]+)',
        "twitter": r'href=["\']?(https?://(?:[\w.-]+\.)?(?:twitter|x)\.com/[^"\'#\s>]+)',
        "facebook": r'href=["\']?(https?://(?:[\w.-]+\.)?facebook\.com/[^"\'#\s>]+)',
        "instagram": r'href=["\']?(https?://(?:[\w.-]+\.)?instagram\.com/[^"\'#\s>]+)',
        "youtube": r'href=["\']?(https?://(?:[\w.-]+\.)?youtube\.com/[^"\'#\s>]+)',
        "tiktok": r'href=["\']?(https?://(?:[\w.-]+\.)?tiktok\.com/[^"\'#\s>]+)',
    }
    for platform, pattern in patterns.items():
        candidates = [html.unescape(m.group(0).rstrip("'\"")) for m in re.finditer(pattern, raw_html, re.I)]
        for href_pattern in (href_patterns.get(platform),):
            if href_pattern:
                candidates.extend(
                    html.unescape(m.group(1).rstrip("'\""))
                    for m in re.finditer(href_pattern, raw_html, re.I)
                )
        best = _pick_best_social_url(platform, candidates)
        if best:
            links[platform] = best
    links.update(_social_links_from_structured_data(raw_html))
    return links


def _pick_best_social_url(platform: str, candidates: list[str]) -> str:
    scored: list[tuple[int, str]] = []
    for url in candidates:
        lower = url.lower()
        if any(x in lower for x in ("/share", "sharer", "/intent/", "sharearticle", "login")):
            continue
        if platform == "instagram" and any(x in lower for x in ("/p/", "/reel/", "/tv/")):
            continue
        score = 1
        if platform == "linkedin" and "/company/" in lower:
            score = 10
        elif platform == "linkedin" and "/in/" in lower:
            score = 7
        elif platform == "instagram":
            score = 8
        elif platform == "youtube" and ("/@" in lower or "/channel/" in lower):
            score = 9
        scored.append((score, url.split("?")[0].rstrip("/")))
    if not scored:
        return ""
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def _social_links_from_structured_data(raw_html: str) -> dict[str, str]:
    links: dict[str, str] = {}
    platform_hosts = {
        "linkedin.com": "linkedin",
        "twitter.com": "twitter",
        "x.com": "twitter",
        "facebook.com": "facebook",
        "instagram.com": "instagram",
        "youtube.com": "youtube",
        "tiktok.com": "tiktok",
    }
    for match in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        raw_html,
        re.I | re.S,
    ):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                same_as = node.get("sameAs")
                if isinstance(same_as, str):
                    same_as = [same_as]
                if isinstance(same_as, list):
                    for item in same_as:
                        if not isinstance(item, str):
                            continue
                        host = urlparse(item).netloc.lower().removeprefix("www.")
                        for needle, platform in platform_hosts.items():
                            if needle in host and platform not in links:
                                links[platform] = item.split("?")[0].rstrip("/")
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return links


def _extract_open_graph_meta(raw_html: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for match in re.finditer(
        r'<meta[^>]+(?:property|name)=["\']([^"\']+)["\'][^>]+content=["\']([^"\']*)["\']',
        raw_html,
        re.I,
    ):
        key = match.group(1).lower()
        value = html.unescape(match.group(2).strip())
        if value and key in ("og:title", "og:description", "description", "twitter:title", "twitter:description"):
            meta[key] = value
    for match in re.finditer(
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']([^"\']+)["\']',
        raw_html,
        re.I,
    ):
        key = match.group(2).lower()
        value = html.unescape(match.group(1).strip())
        if value and key in ("og:title", "og:description", "description", "twitter:title", "twitter:description"):
            meta.setdefault(key, value)
    title_match = re.search(r"<title[^>]*>([^<]+)</title>", raw_html, re.I | re.S)
    if title_match:
        meta.setdefault("title", html.unescape(re.sub(r"\s+", " ", title_match.group(1)).strip()))
    return meta


def _fetch_page_raw(url: str, timeout: int = 8) -> tuple[str, str]:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=_FETCH_HEADERS) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text[:80_000], ""
    except httpx.HTTPError as exc:
        return "", str(exc)


def _crawl_social_profile(platform: str, url: str) -> dict[str, Any]:
    raw, error = _fetch_page_raw(url)
    if error:
        return {
            "platform": platform,
            "url": url,
            "status": "error",
            "error": error,
            "title": "",
            "bio": "",
        }
    lower = raw.lower()
    if any(
        marker in lower
        for marker in (
            "sign in to continue",
            "log in to instagram",
            "join linkedin",
            "authwall",
            "login_required",
        )
    ):
        return {
            "platform": platform,
            "url": url,
            "status": "blocked",
            "error": "Login wall — public preview not available",
            "title": "",
            "bio": "",
        }

    meta = _extract_open_graph_meta(raw)
    title = meta.get("og:title") or meta.get("twitter:title") or meta.get("title", "")
    bio = meta.get("og:description") or meta.get("twitter:description") or meta.get("description", "")
    if not bio:
        snippet = _strip_html(raw)[:400]
        if _is_readable_text(snippet):
            bio = snippet[:220]

    return {
        "platform": platform,
        "url": url,
        "status": "ok" if (title or bio) else "limited",
        "error": "" if (title or bio) else "No public metadata found",
        "title": title[:200],
        "bio": bio[:400],
    }


def _crawl_social_presence(social_links: dict[str, str]) -> list[dict[str, Any]]:
    priority = ("linkedin", "instagram", "twitter", "facebook", "youtube", "tiktok")
    results: list[dict[str, Any]] = []
    for platform in priority:
        url = social_links.get(platform)
        if not url:
            continue
        results.append(_crawl_social_profile(platform, url))
    return results


def _enrich_site_with_social_crawl(site: dict[str, Any]) -> dict[str, Any]:
    links = dict(site.get("social_links") or {})
    if not links:
        site["social_presence"] = []
        return site

    presence = _crawl_social_presence(links)
    site["social_presence"] = presence

    social_text_parts: list[str] = []
    for profile in presence:
        if profile.get("title"):
            social_text_parts.append(profile["title"])
        if profile.get("bio"):
            social_text_parts.append(profile["bio"])

    if social_text_parts:
        social_text = " ".join(social_text_parts)
        existing = list(site.get("problem_phrases") or [])
        for phrase in _extract_problem_language(social_text):
            if phrase not in existing:
                existing.append(phrase)
        site["problem_phrases"] = existing

    return site


def _clean_pain_phrase(text: str, max_len: int = 120) -> str:
    text = re.sub(r"\s+", " ", text.strip(" .,-"))
    if len(text) < 8:
        return ""
    if re.match(r"^(?:and|or|the|a|an|to|for|with)\b", text, re.I):
        return ""
    if not _is_readable_text(text):
        return ""
    return text[:max_len].rsplit(" ", 1)[0] if len(text) > max_len else text


def _invert_help_or_solve_phrase(text: str) -> list[str]:
    pains: list[str] = []
    for match in re.finditer(
        r"(?:help(?:s|ing)?|enable(?:s|ing)?|empower(?:s|ing)?) ([^.!?;\n]{12,120})",
        text,
        re.I,
    ):
        benefit = re.sub(
            r"^(?:startups?|companies|businesses|teams|organizations|organisations|enterprises)"
            r"(?: and (?:startups?|enterprises|businesses|companies|organizations|organisations))? ",
            "",
            match.group(1).strip(),
            flags=re.I,
        )
        benefit = _clean_pain_phrase(benefit)
        if benefit:
            pains.append(f"Struggles to {benefit.lower()} without expert support")
    for match in re.finditer(r"(?:solve|address|fix|overcome)s? ([^.!?;\n]{10,90})", text, re.I):
        issue = _clean_pain_phrase(match.group(1))
        if issue:
            pains.append(f"Needs to overcome {issue.lower()}")
    return pains


def _extract_problem_language(text: str) -> list[str]:
    pains: list[str] = []
    patterns = [
        r"(?:struggle|struggling) with ([^.!?;\n]{8,100})",
        r"(?:tired of|frustrated (?:by|with)|fed up with) ([^.!?;\n]{8,100})",
        r"(?:without|lack of|short on) (?!sacrificing)([^.!?;\n]{8,80})",
        r"(?:challenge|challenges|problem|problems|pain point|pain points)(?: with|:)? ([^.!?;\n]{8,100})",
        r"(?:eliminate|reduce|avoid|prevent|stop) ([^.!?;\n]{8,80})",
        r"(?:can'?t|cannot|unable to) ([^.!?;\n]{8,80})",
        r"\b(?:slow|costly|expensive|manual|legacy|siloed|fragmented|complex|overwhelmed)[^.!?;\n]{0,60}",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I):
            snippet = _clean_pain_phrase(match.group(1) if match.lastindex else match.group(0))
            if snippet and snippet.lower() not in {p.lower() for p in pains}:
                pains.append(snippet[0].upper() + snippet[1:])
    pains.extend(_invert_help_or_solve_phrase(text))
    return pains[:6]


def _pain_from_headings(site: dict[str, Any]) -> list[str]:
    pains: list[str] = []
    chunks: list[str] = []
    for field in ("headings", "subheadings"):
        chunks.extend(part.strip() for part in (site.get(field) or "").split(" · ") if part.strip())
    for heading in chunks:
        lower = heading.lower()
        if any(w in lower for w in ("why", "problem", "challenge", "struggle", "without", "tired", "stop", "reduce")):
            pains.append(heading)
        elif heading.endswith("?"):
            pains.append(f"Seeking answers to: {heading}")
    return pains[:3]


def _pain_from_presence_and_offerings(context: str, offerings: list[str]) -> list[str]:
    pains: list[str] = []
    lower = context.lower()
    signals = [
        (r"cloud migr|migrate to (?:the )?cloud", "Legacy infrastructure slows cloud migration and increases downtime risk"),
        (r"cyber\s*security|security posture|compliance", "Security gaps and compliance pressure create operational risk"),
        (r"digital transformation|moderniz", "Outdated processes block scalable digital transformation"),
        (r"custom (?:application|software)|software development|app development", "Off-the-shelf tools do not match business workflows"),
        (r"devops|ci/cd|deployment", "Slow releases and fragile deployments drain engineering teams"),
        (r"data analytics|business intelligence|data intelligence", "Siloed data prevents actionable insights"),
        (r"ui/?ux|design", "Poor user experience hurts conversion and customer trust"),
        (r"talent|staff aug|contractor|hiring", "Hard to find and retain skilled specialists quickly"),
        (r"automation|automate", "Manual repetitive work limits growth capacity"),
        (r"qa testing|quality assurance", "Quality issues ship to customers before they are caught"),
        (r"ai-driven|artificial intelligence|machine learning", "Teams lack in-house AI expertise to move fast"),
        (r"lead generation|pipeline|growth", "Inconsistent pipeline makes revenue unpredictable"),
    ]
    for pattern, pain in signals:
        if re.search(pattern, lower) and pain not in pains:
            pains.append(pain)
    for offering in offerings[:4]:
        if offering.lower() in lower:
            pains.append(f"Needs reliable partners for {offering}")
    return pains[:4]


def _pain_points_from_online_presence(
    context: str,
    offerings: list[str],
    site: dict[str, Any] | None = None,
) -> list[str]:
    site = site or {}
    pains: list[str] = []
    for phrase in _extract_key_phrases_from_site(site, 12):
        pains.extend(_extract_problem_language(phrase))
    for phrase in site.get("problem_phrases") or []:
        if phrase not in pains:
            pains.append(phrase)

    for profile in site.get("social_presence") or []:
        bio = (profile.get("bio") or "").strip()
        if bio and _is_readable_text(bio):
            pains.extend(_extract_problem_language(bio))

    pains.extend(_pain_from_headings(site))
    pains.extend(_pain_from_presence_and_offerings(context, offerings))

    deduped: list[str] = []
    for pain in pains:
        cleaned = _clean_pain_phrase(pain)
        if cleaned and cleaned.lower() not in {p.lower() for p in deduped}:
            deduped.append(cleaned)
    if not deduped and offerings:
        deduped = [f"Needs trusted expertise in {offerings[0]}"]
        if len(offerings) > 1:
            deduped.append(f"Wants support across {offerings[1]} and related services")
    return deduped[:5]


def fetch_site_summary(url: str, timeout: int = 10) -> dict[str, Any]:
    fetch_url = _normalize_url(url)
    parsed = urlparse(fetch_url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return _empty_site_result(fetch_url, f"Unsupported URL scheme: {parsed.scheme}")

    social_links: dict[str, str] = {}
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=_FETCH_HEADERS) as client:
            response = client.get(fetch_url)
            response.raise_for_status()
            full_text = response.text
            raw = full_text[:120_000]
            social_links = _extract_social_links(full_text)
    except httpx.HTTPError as exc:
        return _empty_site_result(fetch_url, str(exc))

    if not social_links:
        try:
            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"},
            ) as client:
                retry = client.get(fetch_url)
                retry.raise_for_status()
                full_text = retry.text
                retry_raw = full_text[:120_000]
                social_links = _extract_social_links(full_text)
                if social_links:
                    raw = retry_raw
        except httpx.HTTPError:
            pass

    parser = _PageMetaParser()
    parser.feed(raw)

    title = parser.title.strip()
    description = parser.description.strip()
    snippet = _strip_html(raw)[:600]
    if not description:
        description = snippet[:220]

    presence_text = " ".join(
        part
        for part in (
            title,
            description,
            " ".join(parser.h1),
            " ".join(parser.h2),
            " ".join(parser.paragraphs),
            _extract_json_ld_text(raw),
        )
        if part
    )

    return {
        "url": fetch_url,
        "title": title,
        "description": description,
        "keywords": parser.keywords.strip(),
        "headings": " · ".join(parser.h1),
        "subheadings": " · ".join(parser.h2),
        "paragraphs": parser.paragraphs[:5],
        "structured_data": _extract_json_ld_text(raw),
        "social_links": social_links,
        "social_presence": [],
        "problem_phrases": _extract_problem_language(presence_text),
        "snippet": snippet,
    }


def _infer_industry(text: str, url: str = "") -> str:
    lower = text.lower()
    host = urlparse(_normalize_url(url)).netloc.lower().removeprefix("www.") if url else ""
    if host.split(".")[0] in ("google", "bing", "yahoo", "duckduckgo"):
        return "consumer internet"
    if any(w in lower for w in ("saas", "software", "platform", "api", "cloud", "devops")):
        return "B2B software / IT services"
    if any(w in lower for w in ("ecommerce", "e-commerce", "online store", "add to cart", "shop now")):
        return "e-commerce / retail"
    if any(w in lower for w in ("agency", "consulting", "professional services")):
        return "professional services"
    if any(w in lower for w in ("health", "wellness", "fitness", "clinic")):
        return "health & wellness"
    if any(w in lower for w in ("course", "learn", "education", "training")):
        return "education"
    return "small business"


def _extract_offerings(context: str, site: dict[str, Any] | None = None) -> list[str]:
    found: list[str] = []
    known = [
        "cloud DevOps",
        "cybersecurity",
        "software engineering",
        "UI/UX design",
        "data analytics",
        "QA testing",
        "project management",
        "custom software",
        "digital transformation",
        "staff augmentation",
        "AI automation",
        "cloud migration",
    ]
    lower = context.lower()
    for item in known:
        if item.lower() in lower and item.lower() not in {f.lower() for f in found}:
            found.append(item)

    patterns = [
        r"(?:services?|solutions?|offer(?:s|ings)?|specialize(?:s|d)? in)\s*[:\-–]?\s*([A-Za-z0-9][\w\s/,&-]{6,80})",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, context, re.I):
            chunk = match.group(1)
            for part in re.split(r"[,|/]| and ", chunk):
                item = re.sub(r"\s+", " ", part).strip(" .:-")
                if (
                    3 < len(item) < 60
                    and not _OFFERING_BAD_START.match(item)
                    and not re.search(r"\b(we|our|deliver|build|maintain)\b", item, re.I)
                    and _is_readable_text(item)
                    and item.lower() not in {f.lower() for f in found}
                ):
                    found.append(item)
    for heading in (site or {}).get("subheadings", "").split(" · "):
        h = heading.strip()
        if 4 < len(h) < 50 and h.lower() not in {f.lower() for f in found}:
            if any(
                w in h.lower()
                for w in ("service", "solution", "cloud", "devops", "design", "data", "security", "ai")
            ) and not re.search(r"\b(we|our|deliver|build|maintain)\b", h, re.I):
                found.append(h)
    return found[:8]


def _extract_key_phrases_from_site(site: dict[str, Any], limit: int = 8) -> list[str]:
    phrases: list[str] = []
    for field in ("description", "headings", "subheadings"):
        value = (site.get(field) or "").strip()
        if value and _is_readable_text(value):
            phrases.append(value[:180])
    for para in site.get("paragraphs") or []:
        if _is_readable_text(para):
            phrases.append(para[:180])
    deduped: list[str] = []
    for phrase in phrases:
        if phrase.lower() not in {p.lower() for p in deduped}:
            deduped.append(phrase)
    return deduped[:limit]


def _company_does_summary(site: dict[str, Any], brand: str, offerings: list[str]) -> str:
    desc = (site.get("description") or "").strip()
    if desc and _is_readable_text(desc):
        return desc[:280]
    if offerings:
        return f"{brand} provides {', '.join(offerings[:4])}."
    headings = site.get("headings") or ""
    if headings:
        return f"{brand}: {headings[:200]}"
    return f"{brand} — based on website analysis of {site.get('url', 'the site')}"


def _target_audience_from_site(
    context: str,
    site: dict[str, Any],
    brand: str,
    industry: str,
    offerings: list[str],
) -> str:
    roles = _buyer_roles(context, offerings)
    services = ", ".join(offerings[:3]) if offerings else industry
    return f"{roles} at {industry} organizations interested in {services} from {brand}"[:400]


def _buyer_roles(context: str, offerings: list[str]) -> str:
    lower = context.lower()
    roles: list[str] = []
    mapping = [
        (r"cto|cio|it director|technology", "CTOs / IT directors"),
        (r"founder|startup|ceo", "founders and CEOs"),
        (r"product|engineering|devops", "engineering and product leaders"),
        (r"marketing|growth", "marketing and growth leads"),
        (r"security|compliance|ciso", "security and compliance leaders"),
    ]
    for pattern, label in mapping:
        if re.search(pattern, lower) and label not in roles:
            roles.append(label)
    if not roles:
        if any("cloud" in o.lower() or "devops" in o.lower() for o in offerings):
            roles = ["CTOs / IT directors", "engineering leaders"]
        else:
            roles = ["decision-makers and operators"]
    return " and ".join(roles[:2])


def _demographics_from_context(context: str, industry: str, offerings: list[str]) -> str:
    roles = _buyer_roles(context, offerings)
    return f"{roles} in {industry}, typically 28–55, active on LinkedIn and email"


def _goals_list_from_site(context: str, offerings: list[str], site: dict[str, Any] | None = None) -> list[str]:
    goals: list[str] = []
    lower = context.lower()
    if "grow" in lower or "scale" in lower:
        goals.append("Scale operations without sacrificing quality")
    if "cloud" in lower or "migrat" in lower:
        goals.append("Modernize infrastructure and reduce downtime")
    if "security" in lower:
        goals.append("Strengthen security and compliance posture")
    if "ai" in lower or "automat" in lower:
        goals.append("Use AI and automation to move faster")
    if offerings:
        goals.append(f"Find a trusted partner for {offerings[0]}")
    if not goals:
        goals = [
            "Grow revenue with the right specialists",
            "Reach qualified prospects consistently",
            "Build trust with audience-fit content",
        ]
    return goals[:3]


def _goals_summary_from_site(text: str, brand: str, offerings: list[str], site: dict[str, Any] | None = None) -> str:
    goals = _goals_list_from_site(text, offerings, site)
    return f"For {brand}: " + "; ".join(goals)


def _engagement_from_offerings(offerings: list[str], platforms: list[str], context: str) -> str:
    topics = ", ".join(offerings[:4]) if offerings else "your services"
    return f"Content about {topics} on {', '.join(platforms)}"


def _build_research_findings(
    site: dict[str, Any],
    offerings: list[str],
    key_phrases: list[str],
    analysis_source: str,
    pain_points: list[str] | None = None,
) -> dict[str, Any]:
    social = site.get("social_links") or {}
    social_presence = site.get("social_presence") or []
    return {
        "url": site.get("url", ""),
        "page_title": site.get("title", ""),
        "meta_description": site.get("description", ""),
        "headings": site.get("headings", ""),
        "subheadings": site.get("subheadings", ""),
        "services_found": offerings,
        "key_phrases_from_site": key_phrases,
        "pain_points_from_online_presence": pain_points or [],
        "social_profiles_found": list(social.values()),
        "social_presence": social_presence,
        "paragraphs_analyzed": list(site.get("paragraphs") or [])[:3],
        "analysis_method": analysis_source,
    }


def _site_research_context(site: dict[str, Any]) -> str:
    parts = [
        site.get("title", ""),
        site.get("description", ""),
        site.get("keywords", ""),
        site.get("headings", ""),
        site.get("subheadings", ""),
        " ".join(site.get("paragraphs") or []),
        site.get("structured_data", ""),
        " ".join((site.get("social_links") or {}).values()),
        " ".join(
            part
            for profile in (site.get("social_presence") or [])
            for part in (profile.get("title", ""), profile.get("bio", ""))
            if part
        ),
    ]
    return " ".join(p.strip() for p in parts if p and p.strip())


def _resolve_openai_api_key(openai_api_key: str | None = None) -> str:
    if openai_api_key and openai_api_key.strip():
        return openai_api_key.strip()
    try:
        from config import config

        return config.OPENAI_API_KEY or ""
    except Exception:
        return ""


def _analyze_with_llm(
    site_context: str,
    brand: str,
    url: str,
    openai_api_key: str | None = None,
) -> dict[str, Any] | None:
    api_key = _resolve_openai_api_key(openai_api_key)
    if not api_key:
        return None
    try:
        from config import config
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=getattr(config, "OPENAI_MODEL", "gpt-4o"),
            temperature=0.35,
            api_key=api_key,
        )
        prompt = f"""You are a B2B audience researcher. Analyze ONLY the website content below.
Return valid JSON (no markdown) with this shape:
{{
  "suggested_target_audience": "string",
  "what_they_do": "string",
  "suggested_business_goals": "string",
  "suggested_audience_engagement": "string",
  "personas": [
    {{
      "name": "string",
      "description": "string",
      "demographics": "string",
      "pain_points": ["string", "string", "string"],
      "goals": ["string", "string", "string"],
      "platforms": ["linkedin", "email"]
    }}
  ]
}}

Rules:
- Derive every field from the website copy. Do not use generic filler.
- pain_points MUST be inferred from the company's online presence: website copy, headings, services promoted, and social profiles (LinkedIn, Instagram, etc.) when available.
- suggested_target_audience MUST describe WHO is interested AND what services/products from the site they care about.
- Provide exactly 2 personas.
- Reference specific services, industries, or value props found on the site.

Website URL: {url}
Brand: {brand}
Website content:
{site_context[:4500]}
"""
        response = llm.invoke(prompt)
        content = str(response.content).strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.M).strip()
        data = json.loads(content)
        if not isinstance(data.get("personas"), list) or len(data["personas"]) < 1:
            return None
        return data
    except Exception:
        return None


def _analyze_site_content(
    site: dict[str, Any],
    brand: str,
    url: str,
    industry: str,
    platforms: list[str],
    openai_api_key: str | None = None,
) -> dict[str, Any]:
    context = _site_research_context(site)
    offerings = _extract_offerings(context, site)
    key_phrases = _extract_key_phrases_from_site(site)
    pain_points = _pain_points_from_online_presence(context, offerings, site)

    llm_result = _analyze_with_llm(context, brand, url, openai_api_key)
    if llm_result:
        for persona in llm_result.get("personas", []):
            persona.setdefault("source", "website")
            persona.setdefault("source_ref", url)
            if not persona.get("pain_points"):
                persona["pain_points"] = pain_points[:3]
        if not llm_result.get("what_they_do"):
            llm_result["what_they_do"] = _company_does_summary(site, brand, offerings)
        llm_result["research_findings"] = _build_research_findings(
            site, offerings, key_phrases, "llm", pain_points
        )
        llm_result["analysis_source"] = "llm"
        llm_result["site_summary"] = (site.get("description") or site.get("snippet") or "")[:300]
        return llm_result

    goals = _goals_list_from_site(context, offerings, site)
    demographics = _demographics_from_context(context, industry, offerings)

    if offerings:
        primary_name = f"{offerings[0].title()} buyer"
        secondary_name = (
            f"{brand} — {offerings[1].title()} stakeholder"
            if len(offerings) > 1
            else f"{brand} — evaluation stage"
        )
        primary_desc = (
            key_phrases[0]
            if key_phrases
            else f"Prospects evaluating {brand} for {', '.join(offerings[:3])}."
        )
    else:
        primary_name = f"{brand} core audience"
        secondary_name = f"{brand} — research stage"
        primary_desc = (
            key_phrases[0]
            if key_phrases
            else (site.get("description") or f"Audience inferred from {url}")[:180]
        )

    target = _target_audience_from_site(context, site, brand, industry, offerings)
    what_they_do = _company_does_summary(site, brand, offerings)
    findings = _build_research_findings(site, offerings, key_phrases, "website_content", pain_points)

    return {
        "suggested_target_audience": target[:400],
        "what_they_do": what_they_do[:400],
        "suggested_business_goals": _goals_summary_from_site(context, brand, offerings, site),
        "suggested_audience_engagement": _engagement_from_offerings(offerings, platforms, context),
        "research_findings": findings,
        "site_summary": (site.get("description") or site.get("snippet") or "")[:300],
        "personas": [
            {
                "name": primary_name,
                "description": primary_desc,
                "demographics": demographics,
                "pain_points": pain_points[:3] or [f"Challenges referenced on {url}"],
                "goals": goals[:3],
                "platforms": platforms,
                "source": "website",
                "source_ref": url,
            },
            {
                "name": secondary_name,
                "description": key_phrases[1]
                if len(key_phrases) > 1
                else f"Secondary stakeholders researching {brand}.",
                "demographics": demographics,
                "pain_points": pain_points[1:4] or pain_points[:1],
                "goals": goals[1:3] or goals[:1],
                "platforms": platforms,
                "source": "website",
                "source_ref": url,
            },
        ],
        "analysis_source": "website_content",
    }


def personas_from_website(
    site: dict[str, Any],
    product_name: str | None = None,
    existing_audience: str | None = None,
    openai_api_key: str | None = None,
) -> dict[str, Any]:
    title = site.get("title") or product_name or "Your business"
    description = site.get("description") or site.get("snippet") or ""
    url = site.get("url") or ""
    industry = _infer_industry(f"{title} {description}", url)
    brand = product_name or title.split("|")[0].split("-")[0].strip() or "this business"
    platforms = ["linkedin", "email", "twitter"]

    if site.get("error") and not description:
        return {
            "personas": [
                {
                    "name": existing_audience.split(",")[0].strip()
                    if existing_audience
                    else f"Ideal {industry} buyer",
                    "description": f"Could not fully fetch site ({site['error']}). Personas inferred from profile.",
                    "demographics": f"{industry} decision-makers, 28–55",
                    "pain_points": [
                        "Needs clear ROI before adopting new tools",
                        "Limited time for marketing and growth tasks",
                    ],
                    "goals": ["Grow revenue", "Reach qualified prospects"],
                    "platforms": platforms,
                    "source": "website",
                    "source_ref": url,
                }
            ],
            "suggested_target_audience": existing_audience or f"{industry} owners and growth-focused teams",
            "what_they_do": "",
            "suggested_business_goals": "Increase qualified leads and improve audience engagement",
            "suggested_audience_engagement": "Educational posts and customer stories",
            "site_summary": f"Could not fully fetch site ({site['error']}).",
            "research_findings": _build_research_findings(site, [], [], "fallback", []),
            "analysis_source": "fallback",
        }

    result = _analyze_site_content(site, brand, url, industry, platforms, openai_api_key)
    if existing_audience and not result.get("suggested_target_audience"):
        result["suggested_target_audience"] = existing_audience
    return result


def personas_from_segment(
    segment: str,
    leads: list[dict[str, str]],
    product_name: str | None = None,
) -> dict[str, Any]:
    companies = [l.get("company", "").strip() for l in leads if l.get("company")]
    stages: dict[str, int] = {}
    for l in leads:
        st = l.get("stage", "awareness")
        stages[st] = stages.get(st, 0) + 1

    top_stage = max(stages, key=stages.get) if stages else "awareness"
    company_sample = ", ".join(sorted(set(companies))[:5]) or "mixed industries"
    brand = product_name or "your business"

    personas = [
        {
            "name": f"{segment} — core segment",
            "description": f"Imported CRM segment with {len(leads)} contacts from {company_sample}.",
            "demographics": f"B2B/B2C contacts in funnel stage '{top_stage}', sourced from CRM import",
            "pain_points": [
                "Needs messaging matched to their funnel stage",
                "Expects relevant follow-up, not generic blasts",
            ],
            "goals": [
                "Move from awareness to purchase",
                "Stay engaged with valuable content",
            ],
            "platforms": ["email", "linkedin"],
            "source": "crm_segment",
            "source_ref": segment,
        },
        {
            "name": f"{segment} — high-intent subset",
            "description": "Contacts further along the pipeline within this segment.",
            "demographics": f"Leads in consideration/intent stages within {segment}",
            "pain_points": ["Needs proof and social validation", "Comparing options before buying"],
            "goals": ["Get a demo or trial", "Understand ROI clearly"],
            "platforms": ["email", "linkedin"],
            "source": "crm_segment",
            "source_ref": segment,
        },
    ]

    return {
        "personas": personas,
        "suggested_target_audience": f"Contacts in CRM segment '{segment}' ({len(leads)} leads)",
        "what_they_do": f"CRM contacts engaging with {brand}",
        "suggested_business_goals": f"Nurture {segment} toward {top_stage} and convert high-intent leads",
        "suggested_audience_engagement": f"Segment-specific emails and LinkedIn posts referencing {company_sample}",
        "segment_summary": f"{len(leads)} leads · top stage: {top_stage} · companies: {company_sample}",
    }


def research_audience(
    website_url: str | None = None,
    segment: str | None = None,
    segment_leads: list[dict[str, str]] | None = None,
    product_name: str | None = None,
    description: str | None = None,
    existing_audience: str | None = None,
    openai_api_key: str | None = None,
) -> dict[str, Any]:
    if segment and segment_leads:
        result = personas_from_segment(segment, segment_leads, product_name)
        if website_url:
            site = fetch_site_summary(website_url)
            if not site.get("error"):
                result["site_summary"] = site.get("description") or site.get("snippet", "")[:300]
        return result

    url = website_url or ""
    if not url:
        raise ValueError("website_url or segment with leads is required")

    site = fetch_site_summary(url)
    if description and not site.get("description"):
        site["description"] = description
    site = _enrich_site_with_social_crawl(site)

    return personas_from_website(site, product_name, existing_audience, openai_api_key)
