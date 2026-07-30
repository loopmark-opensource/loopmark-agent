# Discoverability & SEO guide

How to make **Loopmark Agent** easier to find on Google, GitHub, and AI tool directories.

## GitHub repository settings

Set these on [github.com/loopmark-opensource/loopmark-agent/settings](https://github.com/loopmark-opensource/loopmark-agent/settings):

| Field | Recommended value |
|---|---|
| **Description** | Open-source LangGraph AI marketing agent — social content, email campaigns, audience research, lead funnel, auto-posting |
| **Website** | Link to docs site or README when available |
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
| **PyPI** | Publish package for `pip install` discoverability |
| **GitHub Pages** | Docs site with meta description + sitemap |
| **Product Hunt / Hacker News** | Launch when web UI ships |
| **Dev.to / Medium** | Tutorial: "Build a marketing agent with LangGraph" |

## Social link previews

Add `docs/social-preview.png` (1280×640) and reference in GitHub **Settings → Social preview** so shared links show a branded image.

## Structured data (future docs site)

When a docs site exists, add JSON-LD `SoftwareApplication` schema:

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Loopmark Agent",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Cross-platform",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
}
```

## Measuring discoverability

- GitHub **Insights → Traffic** — clone and view counts
- Google Search Console — after docs domain is live
- Star/watch counts and issue search hits for target keywords
