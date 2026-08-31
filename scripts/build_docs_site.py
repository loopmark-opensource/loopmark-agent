#!/usr/bin/env python3
"""Build static HTML docs for GitHub Pages."""

from __future__ import annotations

from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent / "site"
SITE_NAME = "Loopmark Agent"
SITE_URL = "https://loopmark-opensource.github.io/loopmark-agent"
REPO_URL = "https://github.com/loopmark-opensource/loopmark-agent"
DESCRIPTION = (
    "Open-source LangGraph AI marketing agent for social content, email campaigns, "
    "audience research, lead funnel management, and auto-posting."
)
OG_IMAGE = f"{SITE_URL}/social-preview.png"

JSON_LD = f"""{{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Loopmark Agent",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Cross-platform",
  "description": "{DESCRIPTION}",
  "softwareVersion": "1.0.0",
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
    </nav>
  </div>
</header>
""".format(repo=REPO_URL)

FOOTER = f"""
<footer>
  <p>MIT licensed · <a href="{REPO_URL}">View source on GitHub</a></p>
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
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{full_title}">
<meta name="twitter:description" content="{page_desc}">
<meta name="twitter:image" content="{OG_IMAGE}">
<link rel="stylesheet" href="styles.css">
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
  <h1>Open-source LangGraph marketing agent</h1>
  <p class="lead">Social content, email campaigns, audience research, lead funnel management, and auto-posting — from a Python CLI you self-host with your own API keys.</p>
  <div class="cta-row">
    <a class="button" href="install.html">Get started</a>
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
  <li>MIT licensed — run locally with JSON storage and BYOK credentials</li>
  <li>LangGraph router sends each request to the right specialist agent</li>
  <li>Programmatic API via <code>run_agent()</code> for backends and automations</li>
</ul>
""".format(repo=REPO_URL),
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
""",
        "Feature overview for Loopmark Agent — complaints, posting, funnel, and audience research.",
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
  <li>Twitter/X, LinkedIn, Buffer — set credentials in <code>.env</code></li>
  <li>Local scheduler — <code>python scheduler.py</code> for due posts</li>
</ul>
""",
        "Install Loopmark Agent via pip or from source with Python 3.10+.",
    ),
    "audience-research.html": (
        "Audience research",
        "/audience-research.html",
        """
<h1>Audience research</h1>
<p class="lead">Build personas from your website, CRM exports, and saved business profile — no ad-platform APIs required.</p>
<h2>Workflow</h2>
<ol>
  <li>Save your product, tone, and target audience with the business profile tools</li>
  <li>Analyze your website URL to extract headings, copy, and positioning</li>
  <li>Import CRM segments (CSV or JSON) with industry, job title, and tags</li>
  <li>Generate draft personas with pain points, goals, and platform preferences</li>
</ol>
<h2>What is not included</h2>
<p>Loopmark Agent does not connect to Meta Ads, LinkedIn Campaign Manager, Google Ads, or follower analytics APIs in the OSS edition. Audience research here means website + CRM + AI personas.</p>
""",
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
<h2>AgentResult</h2>
<ul>
  <li><code>reply</code> — assistant text for this turn</li>
  <li><code>intent</code> — routed agent name</li>
  <li><code>messages</code> — full LangChain message history for multi-turn chat</li>
</ul>
<h2>CLI equivalent</h2>
<pre><code>loopmark-agent chat
loopmark-agent stats</code></pre>
<p>The CLI wraps the same graph via <code>main.py</code>. Hosted REST endpoints are tracked separately for the paid layer.</p>
""",
        "Programmatic run_agent API for Loopmark Agent integrations.",
    ),
}


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
    for filename, (title, path, body, desc) in PAGES.items():
        (SITE_DIR / filename).write_text(page(title, path, body, desc), encoding="utf-8")
    write_sitemap()
    write_robots()
    print(f"Built {len(PAGES)} pages in {SITE_DIR}")


if __name__ == "__main__":
    main()
