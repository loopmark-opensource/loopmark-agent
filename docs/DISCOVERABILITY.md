# Discoverability & SEO guide

How to make **Loopmark Agent** easier to find on Google, GitHub, and AI tool directories.

## GitHub repository settings

Set these on [github.com/loopmark-opensource/loopmark-agent/settings](https://github.com/loopmark-opensource/loopmark-agent/settings):

| Field | Recommended value |
|---|---|
| **Description** | Open-source LangGraph AI marketing agent — social content, email campaigns, audience research, lead funnel, auto-posting |
| **Website** | https://loopmark-opensource.github.io/loopmark-agent/ |
| **Topics** | See list below |

### Recommended topics

```
langgraph
langchain
marketing-automation
social-media
email-marketing
ai-agent
open-source
python
content-marketing
lead-generation
audience-research
twitter
linkedin
buffer
gpt-4
```

Apply via CLI:

```bash
gh repo edit loopmark-opensource/loopmark-agent \
  --description "Open-source LangGraph AI marketing agent — social content, email campaigns, audience research, lead funnel, auto-posting" \
  --add-topic langgraph --add-topic langchain --add-topic marketing-automation \
  --add-topic social-media --add-topic email-marketing --add-topic ai-agent \
  --add-topic open-source --add-topic python --add-topic content-marketing \
  --add-topic lead-generation --add-topic audience-research
```

## PyPI package

The project is packaged as **`loopmark-agent`**:

```bash
pip install loopmark-agent
loopmark-agent chat
```

Console script and dependencies are declared in `pyproject.toml`. Publishing uses GitHub Actions (`.github/workflows/publish-pypi.yml`) with [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) on GitHub Release — configure the `pypi` environment and PyPI trusted publisher for this repo once.

## README & metadata (done in repo)

- Keyword-rich title and subtitle in `README.md`
- `pyproject.toml` with PyPI-style `keywords` and classifiers
- Clear feature list: complaints, posting, funnel, audience research

## Search terms people use

Target these phrases in docs, issues, and release notes:

- AI marketing agent open source
- LangGraph social media bot
- Python marketing automation CLI
- AI write LinkedIn posts
- Email drip sequence generator AI
- Audience persona from website
- CRM segment marketing tool
- Auto post Twitter LinkedIn Python

## External listings (manual — track as issues)

| Channel | Action |
|---|---|
| **Awesome lists** | PR to awesome-langchain, awesome-ai-agents |
| **PyPI** | Package is buildable via `pyproject.toml`; publish with the `Publish to PyPI` workflow on release ([#26](https://github.com/loopmark-opensource/loopmark-agent/issues/26)) |
| **GitHub Pages** | Static docs at `/site` — see [site index](https://loopmark-opensource.github.io/loopmark-agent/) ([#27](https://github.com/loopmark-opensource/loopmark-agent/issues/27)) |
| **Product Hunt / Hacker News** | Launch when web UI ships |
| **Dev.to / Medium** | Tutorial: "Build a marketing agent with LangGraph" |

## Docs site (GitHub Pages)

Static docs live in `site/` and deploy via `.github/workflows/pages.yml`:

- **URL:** https://loopmark-opensource.github.io/loopmark-agent/
- **Pages:** features, install, audience research, programmatic API
- **SEO:** meta description, Open Graph tags, `sitemap.xml`, `robots.txt`
- **JSON-LD:** `SoftwareApplication` schema on every page ([#30](https://github.com/loopmark-opensource/loopmark-agent/issues/30))

Rebuild locally:

```bash
python scripts/build_docs_site.py
```

## Social link previews

`docs/social-preview.png` and `site/social-preview.png` (1280×640) are included in the repo ([#28](https://github.com/loopmark-opensource/loopmark-agent/issues/28)).

Upload the same image in GitHub **Settings → General → Social preview** so repository links show the branded card on Twitter/LinkedIn.

## Structured data

JSON-LD `SoftwareApplication` is embedded in the docs site homepage and sibling pages. Validate with [Google Rich Results Test](https://search.google.com/test/rich-results).

## Measuring discoverability

- GitHub **Insights → Traffic** — clone and view counts
- Google Search Console — after docs domain is live
- Star/watch counts and issue search hits for target keywords
