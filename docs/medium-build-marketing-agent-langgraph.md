# Build a Marketing Agent with LangGraph (Open Source)

*Social posts, email campaigns, audience personas, and lead funnels, all from a Python CLI you self-host with your own API keys.*

---

Most “AI marketing” tools lock your brand voice, your customer data, and your posting keys behind a SaaS dashboard. **Loopmark Agent** takes the opposite approach: an open-source [LangGraph](https://github.com/langchain-ai/langgraph) assistant you run locally, under the MIT license, with your own OpenAI key.

In this post you’ll install it, research an audience from a website, draft social and email content, and peek at the lead funnel, all in plain English chat.

**Repo:** [github.com/loopmark-opensource/loopmark-agent](https://github.com/loopmark-opensource/loopmark-agent)  
**Docs:** [loopmark-opensource.github.io/loopmark-agent](https://loopmark-opensource.github.io/loopmark-agent/)

---

## What you get

You talk to one CLI. A router classifies your intent and sends it to the right **ReAct** sub-agent:

| Agent | Job |
|---|---|
| **Posting** | Social posts, content calendars, email campaigns, optional publish to Twitter/X, LinkedIn, or Buffer |
| **Funnel** | Leads, scoring, stage moves, nurture ideas |
| **Complaints** | Log, classify, draft replies, escalate |

There’s also **audience research**: save a business profile, analyze a public website URL for persona signals, import CRM CSV/JSON, and save personas for later campaigns.

No Meta Ads, LinkedIn Campaign Manager, or Google Ads APIs in the open-source edition. Audience work here means website + CRM + AI personas.

---

## Install

You need **Python 3.10+** and an [OpenAI API key](https://platform.openai.com/api-keys).

### From GitHub

```bash
git clone https://github.com/loopmark-opensource/loopmark-agent.git
cd loopmark-agent
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
```

Put your key in `.env`:

```env
OPENAI_API_KEY=sk-your-actual-key-here
```

Optional: set `OPENAI_MODEL=gpt-4o-mini` for lower cost while you explore.

### Or install straight from GitHub with pip

```bash
pip install git+https://github.com/loopmark-opensource/loopmark-agent.git
export OPENAI_API_KEY=sk-your-actual-key-here
```

A PyPI release (`pip install loopmark-agent`) is coming; until then, use one of the two paths above.

Start chatting:

```bash
loopmark-agent chat
```

Data lands in `./data` under your working directory (override with `DATA_DIR`). Don’t commit that folder, since it can hold PII from leads and CRM imports.

---

## Architecture in one glance

```
You type a request
        │
        ▼
  Route intent (GPT)
        │
   ┌────┼────────┐
   ▼    ▼        ▼
Posting  Funnel  Complaints
   │
   └─ tools: social, email, publisher, audience research…
```

Everything is LangGraph + tool calling. Persistence is plain JSON, so it’s easy to inspect and back up.

---

## Walkthrough: audience → content → funnel

### 1. Tell it about your business

In the chat:

> Save a business profile for **Acme Analytics**: we sell lightweight dashboards for SMB marketers. Tone is clear and friendly. Website https://example.com. Target audience is growth-focused small business owners.

The agent stores a reusable profile so later posts and emails stay on-brand.

### 2. Research audience from a website

> Analyze https://example.com for audience personas.

Under the hood this does a **user-initiated** public page fetch (title, meta, headings, copy), optionally tries public social links when they aren’t login-walled, and drafts personas. With an API key it can use an LLM pass; otherwise it falls back to heuristics from the page content.

You can also:

> Import this CRM CSV and summarize segments…

Paste CSV/JSON with columns like segment, company, industry, job title. The OSS agent does **not** sync live CRM APIs.

### 3. Create social content

> Write three LinkedIn posts about how Acme helps SMB marketers ship reports faster. Use our brand tone. Suggest hashtags.

Or plan a week:

> Build a content calendar for next week: LinkedIn, Twitter, and one blog outline.

### 4. Draft email (and cold outreach)

> Draft a cold email to SMB marketing leads: subject, preheader, body, CTA. Give me two subject-line variants.

You stay in control of sending: wire your own mail stack, or use the agent’s email drafting tools for copy and sequences.

### 5. Publish when you’re ready

With Twitter/X, LinkedIn, or Buffer credentials in `.env`:

> Post the LinkedIn draft now.  
> Schedule this Twitter post for tomorrow at 9am via Buffer.

Without credentials, drafts and schedules still live locally for review.

### 6. Manage the funnel

> Add lead Jordan Lee, jordan@shop.co, company ShopCo, stage awareness, score 55.  
> Show funnel metrics.  
> Suggest a nurture sequence for leads in consideration.

---

## Why LangGraph for marketing?

Marketing work is **multi-step and tool-heavy**: research → draft → revise → maybe publish → track leads. A single prompt chat forgets structure. LangGraph gives you:

- Clear **routing** between specialized agents  
- **Tools** with real side effects (save persona, publish post)  
- A path to extend the OSS core without rewriting the whole app  

Loopmark Agent is built as an **open-core** project: the CLI and local tools stay free; a hosted UI, vault, and billing sit on a separate roadmap.

---

## Try it and contribute

```bash
loopmark-agent chat
```

Useful links:

- **GitHub:** https://github.com/loopmark-opensource/loopmark-agent  
- **Docs:** https://loopmark-opensource.github.io/loopmark-agent/  
- **Contributing:** https://github.com/loopmark-opensource/loopmark-agent/blob/main/CONTRIBUTING.md  
- **Audience & PII notes:** https://loopmark-opensource.github.io/loopmark-agent/audience-research.html  

If this helped, star the repo and open an issue or PR, especially around audience research, publishing, or docs.

---

*Keywords: LangGraph marketing agent, open source social media AI, AI email campaign generator, Python marketing automation, audience persona from website, lead funnel AI*

---

### Medium publishing checklist

1. Create a new story on Medium → paste this markdown (or convert via Medium’s importer).  
2. Title: **Build a Marketing Agent with LangGraph (Open Source)**  
3. Add tags: `Artificial Intelligence`, `LangChain`, `Marketing`, `Open Source`, `Python`  
4. Featured image: use `docs/social-preview.png` from the repo (1280×720).  
5. After publish, add the URL under External listings in `docs/DISCOVERABILITY.md` and comment on issue #31.
