#!/usr/bin/env python3
"""Build static HTML docs for GitHub Pages."""

from __future__ import annotations

import ast
import hashlib
import html
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"
SITE_NAME = "Loopmark Agent"
SITE_URL = "https://loopmark-opensource.github.io/loopmark-agent"
REPO_URL = "https://github.com/loopmark-opensource/loopmark-agent"
LOOPMARK_WEB_URL = "https://main.d3b5sf354a54dh.amplifyapp.com/"
DESCRIPTION = (
    "Open-source LangGraph AI marketing agent for social content, email campaigns, "
    "audience research, lead funnel management, and auto-posting."
)
OG_IMAGE = f"{SITE_URL}/social-preview.png"
OG_IMAGE_WIDTH = 1280
OG_IMAGE_HEIGHT = 720
OG_IMAGE_ALT = "Loopmark Agent, open-source LangGraph marketing assistant"
THEME_COLOR = "#009E96"


def asset_href(name: str) -> str:
    """Cache-bust a site asset so browsers pick up changes after deploy."""
    path = SITE_DIR / name
    if path.is_file():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
        return f"{name}?v={digest}"
    return name


def package_version() -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', (REPO_ROOT / "pyproject.toml").read_text(), re.M)
    return match.group(1) if match else "0.0.0"


# Applied before first paint so a saved theme never flashes the wrong colors.
THEME_INIT = (
    'try{var t=localStorage.getItem("theme");'
    'if(t==="dark"||t==="light")document.documentElement.dataset.theme=t}catch(e){}'
)

JSON_LD = f"""{{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Loopmark Agent",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Cross-platform",
  "description": "{DESCRIPTION}",
  "softwareVersion": "{package_version()}",
  "license": "https://opensource.org/licenses/MIT",
  "url": "{SITE_URL}",
  "codeRepository": "{REPO_URL}",
  "offers": {{
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }}
}}"""

NAV = """
<header>
  <div class="nav">
    <a class="brand" href="index.html">Loopmark Agent</a>
    <nav class="nav-links" aria-label="Primary">
      <a href="features.html">Features</a>
      <a href="install.html">Install</a>
      <a href="audience-research.html">Audience</a>
      <a href="api.html">API</a>
      <a href="{repo}">GitHub</a>
      <a class="nav-cta" href="{web}">Loopmark website</a>
    </nav>
    <div class="nav-tools">
      <div class="search" role="search">
        <label class="visually-hidden" for="site-search">Search docs</label>
        <input id="site-search" type="search" placeholder="Search docs" autocomplete="off" aria-controls="search-results">
        <ul id="search-results" class="search-results" hidden></ul>
      </div>
      <button id="theme-toggle" class="theme-toggle" type="button" aria-label="Toggle dark theme">&#9790;</button>
    </div>
  </div>
</header>
""".format(repo=REPO_URL, web=LOOPMARK_WEB_URL)

FOOTER = f"""
<footer>
  <p>MIT licensed · <a href="{REPO_URL}">View source on GitHub</a> · <a href="{LOOPMARK_WEB_URL}">Loopmark product site</a></p>
</footer>
"""


def page(title: str, path: str, body: str, description: str | None = None) -> str:
    page_desc = description or DESCRIPTION
    canonical = f"{SITE_URL}{path}"
    full_title = f"{title} · {SITE_NAME}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{page_desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{page_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="{OG_IMAGE_WIDTH}">
<meta property="og:image:height" content="{OG_IMAGE_HEIGHT}">
<meta property="og:image:alt" content="{OG_IMAGE_ALT}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{full_title}">
<meta name="twitter:description" content="{page_desc}">
<meta name="twitter:image" content="{OG_IMAGE}">
<meta name="twitter:image:alt" content="{OG_IMAGE_ALT}">
<meta name="theme-color" content="{THEME_COLOR}">
<script>{THEME_INIT}</script>
<link rel="stylesheet" href="{asset_href("styles.css")}">
<script src="{asset_href("site.js")}" defer></script>
<script type="application/ld+json">{JSON_LD}</script>
</head>
<body>
{NAV}
<main>
{body}
</main>
{FOOTER}
</body>
</html>
"""


PAGES: dict[str, tuple[str, str, str, str | None]] = {
    "index.html": (
        "Home",
        "/",
        """
<section class="hero">
  <p class="site-banner">Looking for the full Loopmark experience? Visit the <a href="{web}">Loopmark website</a> for product overview, pricing, and FAQs.</p>
  <h1>Open-source LangGraph marketing agent</h1>
  <p class="lead">Social content, email campaigns, audience research, lead funnel management, and auto-posting, from a Python CLI you self-host with your own API keys.</p>
  <div class="cta-row">
    <a class="button" href="install.html">Get started</a>
    <a class="button secondary" href="{web}">Loopmark website</a>
    <a class="button secondary" href="{repo}">Star on GitHub</a>
  </div>
</section>
<div class="card-grid">
  <article class="card"><h3>Complaints agent</h3><p>Log, classify, draft responses, and resolve customer complaints.</p></article>
  <article class="card"><h3>Posting agent</h3><p>Generate social posts, emails, calendars, and publish to Twitter, LinkedIn, or Buffer.</p></article>
  <article class="card"><h3>Funnel agent</h3><p>Score leads, move prospects through stages, and plan nurture sequences.</p></article>
  <article class="card"><h3>Audience research</h3><p>Analyze websites, import CRM segments, and draft personas for campaigns.</p></article>
</div>
<h2>Why Loopmark Agent?</h2>
<ul>
  <li>MIT licensed; run locally with JSON storage and BYOK credentials</li>
  <li>LangGraph router sends each request to the right specialist agent</li>
  <li>Programmatic API via <code>run_agent()</code> for backends and automations</li>
</ul>
""".format(repo=REPO_URL, web=LOOPMARK_WEB_URL),
        DESCRIPTION,
    ),
    "features.html": (
        "Features",
        "/features.html",
        """
<h1>Features</h1>
<p class="lead">Three specialist agents plus audience research tools, all driven in plain English.</p>
<h2>Complaints</h2>
<ul><li>Log and classify complaints by severity</li><li>Draft empathetic responses</li><li>Track resolution stats</li></ul>
<h2>Posting &amp; content</h2>
<ul><li>Platform-specific social posts (Twitter/X, LinkedIn, Instagram, Facebook, blog)</li><li>Email campaigns with A/B subject lines and drip sequences</li><li>Content calendars and hashtag suggestions</li><li>Auto-publish via Twitter, LinkedIn, or Buffer scheduler</li></ul>
<h2>Funnel</h2>
<ul><li>Eight funnel stages with lead scoring</li><li>Source reporting and nurture playbooks</li></ul>
<h2>Audience research</h2>
<ul><li>Save a reusable business profile</li><li>Analyze a website URL for persona signals</li><li>Import CRM CSV/JSON segments</li><li>Persist audience personas for campaigns</li></ul>
<p><a href="audience-research.html">Audience workflow</a> · <a href="audience-research.html#data-collection--limits">Data collection, limits &amp; PII</a></p>
""",
        "Feature overview for Loopmark Agent: complaints, posting, funnel, and audience research.",
    ),
    "install.html": (
        "Install",
        "/install.html",
        """
<h1>Installation</h1>
<p class="lead">Python 3.10+ and an OpenAI API key. Optional social credentials for live posting.</p>
<h2>pip install</h2>
<pre><code>pip install loopmark-agent
export OPENAI_API_KEY=sk-your-key
loopmark-agent chat
loopmark-agent stats</code></pre>
<p>Data files are written to <code>./data</code> in your working directory. Override with <code>DATA_DIR</code>.</p>
<h2>From source</h2>
<pre><code>git clone https://github.com/loopmark-opensource/loopmark-agent.git
cd loopmark-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
loopmark-agent chat</code></pre>
<h2>Optional integrations</h2>
<ul>
  <li>Twitter/X, LinkedIn, Buffer: set credentials in <code>.env</code></li>
  <li>Local scheduler: <code>python scheduler.py</code> for due posts</li>
</ul>
""",
        "Install Loopmark Agent via pip or from source with Python 3.10+.",
    ),
    "audience-research.html": (
        "Audience research",
        "/audience-research.html",
        """
<h1>Audience research</h1>
<p class="lead">Build personas from your website, CRM exports, and saved business profile. No ad-platform APIs required.</p>
<h2>Workflow</h2>
<ol>
  <li>Save your product, tone, and target audience with the business profile tools</li>
  <li>Analyze your website URL to extract headings, copy, and positioning</li>
  <li>Import CRM segments (CSV or JSON) with industry, job title, and tags</li>
  <li>Generate draft personas with pain points, goals, and platform preferences</li>
</ol>
<h2>What is not included</h2>
<p>Loopmark Agent does not connect to Meta Ads, LinkedIn Campaign Manager, Google Ads, or follower analytics APIs in the OSS edition. Audience research here means website + CRM + AI personas.</p>
<h2 id="data-collection--limits">Data collection &amp; limits</h2>
<p>This is <strong>not</strong> large-scale web scraping. Audience research uses small, user-initiated fetches to help draft marketing personas.</p>
<h3>What the agent may fetch</h3>
<ul>
  <li><strong>Website URL (you provide)</strong>: one HTTP GET of public HTML per analysis. We parse title, meta tags, headings, and body copy. Response size is capped; requests time out after a few seconds.</li>
  <li><strong>Social profile links on that site</strong>: optional follow-up GET of public profile pages (LinkedIn, Instagram, X, etc.) to read Open Graph / title / description when available. Many platforms return login walls; we mark those as blocked and do not bypass authentication.</li>
  <li><strong>CRM files (you upload)</strong>: CSV or JSON you export from your own CRM. Nothing is pulled from third-party CRM APIs in the OSS edition.</li>
  <li><strong>Business profile (you enter)</strong>: product name, tone, audience description, website URL stored locally for reuse.</li>
</ul>
<h3>What we do not do</h3>
<ul>
  <li>No crawling sitemaps, search results, or competitor databases at scale</li>
  <li>No ad-platform or social analytics APIs (followers, ad spend, lookalikes)</li>
  <li>No circumventing rate limits, CAPTCHAs, or login walls</li>
  <li>No resale or sharing of fetched or imported data</li>
</ul>
<h3>Operational limits (self-hosted)</h3>
<p>Volume is intentionally low (on-demand, per user action). If you deploy for many users or geos, you are responsible for robots.txt, site terms, request politeness, and infrastructure (including proxies) where appropriate.</p>
<h2>PII &amp; privacy</h2>
<p>When you self-host Loopmark Agent, <strong>you</strong> are responsible for how personal data is collected, stored, and processed. The OSS agent stores data locally under <code>data/</code> (JSON files) unless you integrate your own backend.</p>
<h3>Where PII can appear</h3>
<table>
  <thead>
    <tr><th>Feature</th><th>Typical fields</th><th>Storage</th></tr>
  </thead>
  <tbody>
    <tr><td>CRM import</td><td>Name, email, company, job title, tags, segment</td><td><code>data/</code> (imported rows / personas)</td></tr>
    <tr><td>Funnel / leads</td><td>Name, email, company, notes, score</td><td><code>data/leads.json</code></td></tr>
    <tr><td>Complaints</td><td>Customer name, email, message</td><td><code>data/complaints.json</code></td></tr>
    <tr><td>Website analysis</td><td>Usually no individual PII; public marketing copy only</td><td>Transient / persona drafts</td></tr>
    <tr><td>Social public fetch</td><td>Public bio/title text only when pages are accessible</td><td>Enrichment on analysis result</td></tr>
  </tbody>
</table>
<h3>Third parties</h3>
<ul>
  <li><strong>OpenAI</strong>: persona and content tools may send website excerpts, CRM summaries, or messages you provide to the model API. Review <a href="https://openai.com/policies" rel="noopener noreferrer">OpenAI’s policies</a> and use enterprise / zero-retention options if your compliance program requires them.</li>
  <li><strong>Twitter, LinkedIn, Buffer</strong>: only when you configure publishing; not used for audience scraping.</li>
</ul>
<h3>Recommendations</h3>
<ul>
  <li>Do not commit <code>data/</code>, CRM exports, or <code>.env</code> to git.</li>
  <li>Import the minimum CRM columns needed (avoid full contact dumps when anonymized segments are enough).</li>
  <li>Honor GDPR, CCPA, and local rules for consent, retention, and deletion when processing customer or lead data.</li>
  <li>Redact or delete JSON files when offboarding users or closing a deployment.</li>
</ul>
<p>Questions from partners or reviewers? Point them to this page and the <a href="{repo}#data-collection-limits--pii">README section</a>.</p>
""".format(repo=REPO_URL),
        "Audience research with website analysis, CRM import, and AI personas.",
    ),
    "api.html": (
        "API",
        "/api.html",
        """
<h1>Programmatic API</h1>
<p class="lead">Use <code>core.run.run_agent()</code> from Python backends, scripts, or a future hosted API.</p>
<pre><code>from core.run import run_agent

result = run_agent("Draft a LinkedIn post about our product launch")
print(result.reply)
print(result.intent)  # posting | complaint | funnel</code></pre>
{api_reference}
<h2>CLI equivalent</h2>
<pre><code>loopmark-agent chat
loopmark-agent stats</code></pre>
<p>The CLI wraps the same graph via <code>main.py</code>. Hosted REST endpoints are tracked separately for the paid layer.</p>
""",
        "Programmatic run_agent API for Loopmark Agent integrations.",
    ),
}


def _docstring_html(doc: str) -> str:
    """Render a Google-style docstring: summary paragraphs plus Args/Returns lists."""
    blocks: list[str] = []
    section: str | None = None
    items: list[str] = []
    para: list[str] = []

    def flush_para() -> None:
        if para:
            blocks.append(f"<p>{html.escape(' '.join(para))}</p>")
            para.clear()

    def flush_items() -> None:
        if section and items:
            lis = "".join(f"<li>{i}</li>" for i in items)
            blocks.append(f"<h4>{section}</h4><ul>{lis}</ul>")
        items.clear()

    for raw in doc.strip().splitlines():
        line = raw.strip()
        if line in ("Args:", "Returns:", "Raises:"):
            flush_para()
            flush_items()
            section = line[:-1]
        elif not line:
            flush_para()
        elif section:
            name, sep, rest = line.partition(":")
            if sep and section == "Args" and " " not in name:
                items.append(f"<code>{html.escape(name)}</code>: {html.escape(rest.strip())}")
            elif items:
                items[-1] += " " + html.escape(line)
            else:
                items.append(html.escape(line))
        else:
            para.append(line)
    flush_para()
    flush_items()
    return "\n".join(blocks)


def api_reference(module_path: Path = REPO_ROOT / "core" / "run.py") -> str:
    """Generate reference HTML from a module's public classes and functions (no imports)."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    sections = [f'<h2 id="reference">Reference <span class="version">v{package_version()}</span></h2>']
    sections.append(
        f"<p>Generated from <code>{module_path.relative_to(REPO_ROOT).as_posix()}</code> docstrings.</p>"
    )
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            doc = ast.get_docstring(node) or ""
            anchor = f"ref-{node.name.lower()}"
            if isinstance(node, ast.FunctionDef):
                sig = f"{node.name}({ast.unparse(node.args)})"
                if node.returns is not None:
                    sig += f" -> {ast.unparse(node.returns)}"
            else:
                sig = f"class {node.name}"
            parts = [f'<h3 id="{anchor}"><code>{html.escape(sig)}</code></h3>', _docstring_html(doc)]
            if isinstance(node, ast.ClassDef):
                fields = [
                    f"<li><code>{html.escape(stmt.target.id)}: {html.escape(ast.unparse(stmt.annotation))}</code></li>"
                    for stmt in node.body
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
                ]
                if fields:
                    parts.append(f"<h4>Fields</h4><ul>{''.join(fields)}</ul>")
            sections.append("\n".join(p for p in parts if p))
    return "\n".join(sections)


def _page_text(body: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def write_search_index(pages: dict[str, tuple[str, str, str, str | None]]) -> None:
    entries = [
        {"title": title, "url": filename, "text": _page_text(body)}
        for filename, (title, _path, body, _desc) in pages.items()
    ]
    (SITE_DIR / "search-index.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def write_sitemap() -> None:
    urls = "\n".join(
        f"  <url><loc>{SITE_URL}{path}</loc></url>"
        for path in ("/", "/features.html", "/install.html", "/audience-research.html", "/api.html")
    )
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""
    (SITE_DIR / "sitemap.xml").write_text(content, encoding="utf-8")


def write_robots() -> None:
    content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    (SITE_DIR / "robots.txt").write_text(content, encoding="utf-8")


def main() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    pages = dict(PAGES)
    title, path, body, desc = pages["api.html"]
    pages["api.html"] = (title, path, body.replace("{api_reference}", api_reference()), desc)
    for filename, (title, path, body, desc) in pages.items():
        (SITE_DIR / filename).write_text(page(title, path, body, desc), encoding="utf-8")
    write_search_index(pages)
    write_sitemap()
    write_robots()
    print(f"Built {len(PAGES)} pages in {SITE_DIR}")


if __name__ == "__main__":
    main()
