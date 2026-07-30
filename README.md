# Loopmark Agent — Open-Source AI Marketing Assistant

> **LangGraph marketing agent** for social media content, email campaigns, audience research, lead funnel management, and auto-posting to Twitter, LinkedIn, and Buffer. Free MIT-licensed Python CLI — bring your own OpenAI key.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-agent-blue)](https://github.com/langchain-ai/langgraph)

**Also known as:** marketing agent · AI content generator · social media automation · email marketing AI · lead funnel assistant · audience research tool

**Repository:** [github.com/loopmark-opensource/loopmark-agent](https://github.com/loopmark-opensource/loopmark-agent)

Open-source LangGraph marketing assistant — free to use, modify, and distribute under the [MIT License](LICENSE).

A LangGraph-powered AI marketing assistant with three specialised sub-agents. You talk to it in plain English — a router automatically sends your request to the right agent.

**Search keywords:** `langgraph marketing agent`, `open source social media AI`, `AI email campaign generator`, `marketing automation python`, `audience persona generator`, `lead funnel AI`, `twitter linkedin auto poster`

| Agent | What it does |
|---|---|
| **Complaints** | Log, classify, draft responses, escalate, and resolve customer complaints |
| **Posting** | Create social content, email campaigns, content calendars, and **automatically publish** to social platforms |
| **Funnel** | Manage leads, score prospects, move them through funnel stages, and plan nurture sequences |

---

## Features

### Complaints
- Log complaints with category and severity
- List open/resolved complaints
- Draft empathetic responses
- Track complaint stats by category and severity

### Social media & content
- Generate posts for Twitter/X, LinkedIn, Instagram, Facebook, and blog
- Platform-specific guidelines (character limits, best times, tips)
- Hashtag suggestions
- Content calendar planning
- Save drafts and scheduled posts

### Email marketing
- Draft full email campaigns (subject, preheader, body, CTA)
- A/B subject line variants
- Drip / nurture sequence planning
- Plain-text conversion
- Email best-practice checklists

### Automatic posting
- **Post immediately** to Twitter/X and LinkedIn
- **Schedule via Buffer** (Twitter, LinkedIn, Instagram, Facebook from one API)
- Background scheduler publishes queued posts when their date arrives
- Post status tracking: draft → scheduled → published / failed

### Funnel management
- Add and update leads through 8 funnel stages
- Lead scoring (0–100)
- Funnel metrics and source reporting
- Stage-specific nurture sequences

### Audience research
- Save a **business / brand profile** (product, audience, tone, website) once and reuse it
- **Analyze a website URL** to extract positioning signals and draft audience personas
- **Import CRM segments** from CSV or JSON exports (segment, industry, job title, tags)
- Summarize imported CRM data into segment patterns for persona ideas
- Save and list **audience personas** for posts, emails, and funnel planning

> **Note:** This agent does not connect to Meta Ads, LinkedIn Campaign Manager, Google Ads, or social follower analytics APIs. Audience finding here = saved profile + website analysis + CRM import + AI personas.

---

## Architecture

```
User input
    │
    ▼
Route Intent (GPT-4o)
    │
    ├── complaint ──► Complaints Agent
    ├── posting   ──► Posting Agent (content + email + publisher tools)
    └── funnel    ──► Funnel Agent
```

All agents are **ReAct** agents built with LangGraph. Data is persisted as JSON in `data/`.

---

## Requirements

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys) (required)
- Optional: Twitter, LinkedIn, or Buffer credentials for live posting

---

## Installation

```bash
# 1. Enter the project
cd marketing-agent

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
```

Edit `.env` and set your OpenAI key:

```env
OPENAI_API_KEY=sk-your-actual-key-here
```

---

## Configuration

### Required

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |

### Optional — LLM

| Variable | Default | Description |
|---|---|---|
| `OPENAI_MODEL` | `gpt-4o` | Model to use. Set to `gpt-4o-mini` for lower cost |
| `OPENAI_TEMPERATURE` | `0.7` | Default temperature |

### Optional — LangSmith tracing

| Variable | Default | Description |
|---|---|---|
| `LANGCHAIN_TRACING_V2` | `false` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | — | LangSmith API key |
| `LANGCHAIN_PROJECT` | `marketing-agent` | LangSmith project name |

### Optional — Social posting

| Variable | Platform | Description |
|---|---|---|
| `TWITTER_API_KEY` | Twitter/X | App API key |
| `TWITTER_API_SECRET` | Twitter/X | App API secret |
| `TWITTER_ACCESS_TOKEN` | Twitter/X | User access token |
| `TWITTER_ACCESS_SECRET` | Twitter/X | User access secret |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn | OAuth 2.0 token |
| `LINKEDIN_PERSON_ID` | LinkedIn | Your member URN (e.g. `urn:li:person:XXXXXXX`) |
| `BUFFER_ACCESS_TOKEN` | Buffer | Posts to Twitter, LinkedIn, Instagram, Facebook |

> **Tip:** Buffer is the easiest way to cover multiple platforms with one API key. Get a token at [buffer.com/developers](https://buffer.com/developers/api).

---

## Usage

### Interactive chat

Start a conversation with the agent:

```bash
python3 main.py
```

Show which sub-agent handled each request:

```bash
python3 main.py --verbose
```

Use a different model:

```bash
python3 main.py --model gpt-4o-mini
```

View a quick summary of stored data:

```bash
python3 main.py stats
```

Type `exit`, `quit`, or `bye` to leave the chat.

---

### Automatic posting scheduler

The scheduler checks your post queue and publishes anything due today.

```bash
# Run continuously, checking every 30 minutes
python3 scheduler.py

# Check every 60 minutes
python3 scheduler.py --interval 60

# Run once and exit (good for cron)
python3 scheduler.py --once

# Preview what would be posted without publishing
python3 scheduler.py --dry-run
```

**Cron example** (post every hour):

```cron
0 * * * * cd /path/to/marketing-agent && .venv/bin/python3 scheduler.py --once
```

---

## Example prompts

### Complaints

```
A customer named Alice emailed saying her package arrived damaged.
She's very upset. Log this as a critical shipping complaint and draft a response.
```

```
Show me all open high-severity complaints and give me stats by category.
```

```
Resolve complaint CMP-1234567890 with the response we drafted earlier.
```

### Social media

```
Write a LinkedIn post announcing our summer sale. Professional tone, include a CTA and hashtags.
```

```
Generate a 2-week content calendar for topics: product launch, tips, case study
across Twitter and LinkedIn.
```

```
Post this to Twitter now: "Big news — our summer sale starts today! Save 30% on everything. 🎉"
```

```
Schedule this LinkedIn post for tomorrow at 9 AM via Buffer.
```

```
What are the best posting guidelines for Instagram?
```

### Email marketing

```
Draft a promotional email for our Black Friday sale with 3 A/B subject line options.
```

```
Build a 5-email welcome drip sequence for new sign-ups. Goal: convert to paid plan.
```

```
What are the best practices for email deliverability?
```

```
Draft a re-engagement email for subscribers who haven't opened in 90 days.
```

### Funnel

```
Add a new lead: John Smith, john@acme.com, company Acme Corp,
came from a Google Ad, currently at the interest stage.
```

```
Show me funnel metrics and top acquisition sources.
```

```
What's the nurture sequence for leads in the consideration stage?
```

```
Score lead LEAD-1234567890 at 75 — they booked a demo call.
```

---

## How automatic posting works

```
1. You ask the agent to write and schedule a post
2. Agent saves it to data/posts.json with status "scheduled"
3. Scheduler (or manual publish) picks up posts when scheduled_date arrives
4. Post goes live via Twitter, LinkedIn, or Buffer
5. Status updates to "published" or "failed"
```

### Posting options

| Method | When to use | Credentials needed |
|---|---|---|
| `post_to_twitter` | Immediate tweet | Twitter API keys |
| `post_to_linkedin` | Immediate LinkedIn post | LinkedIn token + person ID |
| `schedule_via_buffer` | Schedule to any platform | Buffer access token |
| `publish_scheduled_posts` | Publish all due posts from queue | Depends on platform |

### Setting up Buffer (recommended)

1. Create a Buffer account and connect your social profiles
2. Get an access token from [buffer.com/developers](https://buffer.com/developers/api)
3. Add to `.env`: `BUFFER_ACCESS_TOKEN=...`
4. In chat, ask: *"Show my Buffer profiles"* to get profile IDs
5. Schedule posts: *"Schedule this to my LinkedIn Buffer profile for tomorrow at 9 AM"*

---

## Project structure

```
marketing-agent/
├── main.py                    # Interactive CLI
├── scheduler.py               # Auto-posting background daemon
├── config.py                  # Environment configuration
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── graph.py               # LangGraph orchestrator + intent router
│   └── sub_agents.py          # Complaints, Posting, Funnel ReAct agents
│
├── tools/
│   ├── complaint_tools.py     # Complaint logging and management
│   ├── social_tools.py        # Content creation and calendars
│   ├── email_tools.py         # Email campaigns and drip sequences
│   ├── publisher_tools.py     # Live posting to Twitter, LinkedIn, Buffer
│   └── funnel_tools.py        # Lead and funnel management
│
├── prompts/
│   └── templates.py           # System prompts for all agents
│
├── models/
│   └── schemas.py             # Pydantic data models
│
└── data/                      # Auto-created JSON persistence
    ├── complaints.json
    ├── leads.json
    ├── posts.json
    └── emails.json
```

---

## Data storage

All data is stored locally as JSON files in `data/`:

| File | Contents |
|---|---|
| `complaints.json` | Logged complaints and responses |
| `posts.json` | Social posts (draft, scheduled, published) |
| `emails.json` | Email campaigns |
| `leads.json` | Funnel leads and scores |

These files are created automatically on first use. They are gitignored by default.

---

## Web UI specification

> **Full handoff doc for the team:** see **[app.md](app.md)** — Node.js backend + Next.js frontend + Python agent-service architecture, API contract, flows, and build order.

There is **no web UI today** — the app is CLI-only (`python3 main.py`). This section is a handoff spec for backend and frontend teams building a web interface on top of the existing Python agent.

### Target architecture

```
Frontend (React / Next.js)
    │
    ▼  REST or WebSocket
Backend API (FastAPI — to be built)
    │
    ├── LangGraph agent (agents/graph.py)
    ├── Tools (tools/*.py)
    └── JSON storage (data/*.json)
            │
            ▼
    OpenAI · Twitter · LinkedIn · Buffer
```

**Backend team:** wrap the existing agent and tools in a FastAPI (or similar) HTTP layer.  
**Frontend team:** build pages that call those APIs. Reuse Pydantic models in `models/schemas.py` for request/response shapes.

### Frontend pages (navigation)

| Page | Purpose |
|---|---|
| **Dashboard** | Overview stats + quick actions |
| **Chat** | Main AI interface (replaces CLI) |
| **Posts** | Generate, edit, save, publish, schedule social content |
| **Calendar** | Week/month view of scheduled posts |
| **Email** | Draft campaigns, A/B subjects, drip sequences |
| **Complaints** | Log, triage, draft responses, resolve |
| **Funnel** | Lead list + pipeline board (8 stages) |
| **Settings** | Product profile, integrations, AI model |

Suggested nav structure:

```
Dashboard · Chat · Content (Posts, Calendar) · Email · Complaints · Funnel · Settings
```

### MVP screens (what each must include)

#### 1. Chat (required)

Replaces `python3 main.py`.

| UI element | Purpose |
|---|---|
| Message thread | User + agent messages |
| Text input + Send | Submit prompts |
| Agent badge | Show routed agent: Complaints / Posting / Funnel |
| Loading / error states | While agent runs or on failure |
| New conversation | Clear session history |

#### 2. Product / brand profile (strongly recommended)

Without this, users must describe their product in every prompt. Store once and inject into agent prompts.

| Field | Example |
|---|---|
| Product name | Loopmark |
| Tagline | AI marketing for small teams |
| Description | 2–3 sentences about the product |
| Target audience | Small business owners |
| Brand tone | Professional, friendly |
| Website URL | `https://...` |
| Default CTA | Start free trial |

#### 3. Content / social posts (required)

| Screen | Features |
|---|---|
| Post generator | Form: platform, topic, tone, audience → AI draft |
| Post editor | Edit text, hashtags, character count (280 for Twitter) |
| Actions | Save draft · Post now · Schedule |
| Post library | Filter by platform/status; preview content |
| Content calendar | Scheduled posts by date |

Post lifecycle: `draft` → `scheduled` → `published` / `failed`

Supported platforms: Twitter, LinkedIn, Instagram, Facebook, Blog

#### 4. Email marketing (required)

| Screen | Features |
|---|---|
| Email composer | Campaign name, subject, goal, audience, CTA |
| AI generate | Preheader, body, CTA block |
| A/B subjects | 2–3 subject line variants |
| Drip sequences | Multi-email nurture plan |
| Campaign library | Saved emails with status |
| Copy actions | Copy HTML / plain text |

> **Note:** The agent drafts emails only — it does not send via SMTP. The UI should label this clearly unless SendGrid/Mailchimp is added later.

#### 5. Complaints (required)

| Screen | Features |
|---|---|
| Complaint list | Filter by open/resolved, severity, category |
| Log complaint | Name, email, message, category, severity |
| Complaint detail | View message + AI-drafted response |
| Resolve | Mark resolved with response text |
| Stats | Counts by category and severity |

Categories: `product`, `shipping`, `billing`, `customer_service`, `other`  
Severity: `low`, `medium`, `high`, `critical`

#### 6. Funnel / leads (required)

| Screen | Features |
|---|---|
| Lead list | Name, email, company, stage, score |
| Add / edit lead | Source, stage, notes |
| Pipeline board | Kanban across 8 stages |
| Metrics | Totals, by stage, top sources |
| Nurture sequences | Recommended actions per stage |

Funnel stages: `awareness` → `interest` → `consideration` → `intent` → `evaluation` → `purchase` → `retention` → `advocacy`

Lead score bands: 0–30 cold · 31–60 warm · 61–80 hot · 81–100 sales-ready

#### 7. Settings (required)

| Section | Contents |
|---|---|
| AI | Model (`gpt-4o`, `gpt-4o-mini`), temperature |
| Product profile | Brand fields (see above) |
| Integrations | Twitter, LinkedIn, Buffer credentials |
| Connection status | Green/red badge per platform |
| Scheduler | Auto-post interval; manual run-once trigger |

Never expose full API keys to the frontend — store credentials server-side only.

### Backend API (to be built)

The following endpoints do not exist yet. Map them to existing tools in `tools/` and the agent in `agents/graph.py`.

#### Chat

```
POST /api/chat                         Send message, get reply + intent
GET  /api/chat/sessions                List conversations (optional v1)
GET  /api/chat/sessions/:id            Get conversation history (optional v1)
```

Example request/response:

```json
// POST /api/chat
{ "message": "Write a LinkedIn post about our launch", "session_id": "optional-uuid" }

// Response
{ "reply": "Here's your LinkedIn post...", "intent": "posting", "agent": "Posting Agent" }
```

#### Posts & publishing

```
GET    /api/posts?platform=&status=
POST   /api/posts
POST   /api/posts/generate
POST   /api/posts/:id/publish          Twitter / LinkedIn (post now)
POST   /api/posts/:id/schedule         Buffer
DELETE /api/posts/:id
GET    /api/posts/calendar?from=&to=
GET    /api/platforms/guidelines/:platform
GET    /api/hashtags?topic=&platform=
GET    /api/publishing/status
GET    /api/buffer/profiles
```

#### Email

```
GET    /api/emails?status=
POST   /api/emails/generate
POST   /api/emails
POST   /api/emails/ab-subjects
POST   /api/emails/drip-sequence
GET    /api/emails/:id
PUT    /api/emails/:id
DELETE /api/emails/:id
POST   /api/emails/:id/plain-text
```

#### Complaints

```
GET    /api/complaints?status=&severity=
POST   /api/complaints
GET    /api/complaints/:id
POST   /api/complaints/:id/draft-response
POST   /api/complaints/:id/resolve
GET    /api/complaints/stats
```

#### Funnel

```
GET    /api/leads?stage=&min_score=
POST   /api/leads
GET    /api/leads/:id
PATCH  /api/leads/:id/stage
PATCH  /api/leads/:id/score
GET    /api/funnel/metrics
GET    /api/funnel/nurture/:stage
```

#### Settings & dashboard

```
GET  /api/dashboard/stats
GET  /api/settings
PUT  /api/settings
GET  /api/settings/product
PUT  /api/settings/product
GET  /api/integrations/status
POST /api/integrations/test/:platform
POST /api/scheduler/run-once
GET  /api/scheduler/status
```

### What exists vs what needs building

| Exists today | Needs building |
|---|---|
| LangGraph agent (`agents/graph.py`) | REST / WebSocket API |
| JSON persistence (`data/*.json`) | CRUD endpoints |
| CLI (`main.py`) | `POST /api/chat` wrapper |
| Scheduler (`scheduler.py`) | Background job + API trigger |
| Publisher tools (Twitter, LinkedIn, Buffer) | Service layer calling same tools |
| Pydantic schemas (`models/schemas.py`) | API request/response models |

### Integrations the UI must surface

| Platform | UI action | Env vars |
|---|---|---|
| OpenAI | Generate all content | `OPENAI_API_KEY` |
| Twitter/X | Post now | `TWITTER_API_*` (4 keys) |
| LinkedIn | Post now | `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_ID` |
| Buffer | Schedule multi-platform | `BUFFER_ACCESS_TOKEN` |
| Email | Draft only (MVP) | — |

Disable **Post now** / **Schedule** buttons when the relevant integration is not connected. Show connection status in Settings.

### MVP vs v2

**MVP (ship first)**

1. Chat UI
2. Product profile in settings
3. Post generator + library + publish/schedule
4. Email draft + library
5. Complaints list + log + resolve
6. Leads list + add + stage/score
7. Integration settings + connection status

**v2**

- User auth / multi-tenant
- Real email sending (SendGrid / Mailchimp)
- Streaming chat responses (WebSocket / SSE)
- Image generation for social posts
- Platform analytics
- Mobile PWA

### Suggested frontend stack

| Area | Suggestion |
|---|---|
| Framework | Next.js or React + Vite |
| Chat | Message list + Markdown rendering |
| Forms | React Hook Form + Zod |
| Calendar | FullCalendar or similar |
| Funnel board | Drag-and-drop Kanban (e.g. dnd-kit) |
| Data fetching | TanStack Query |

---

## Troubleshooting

**"Set OPENAI_API_KEY in your .env file"**
- Copy `.env.example` to `.env` and add your real API key

**Twitter posting fails**
- Twitter write access requires a paid API tier
- Consider using Buffer instead for Twitter posting

**LinkedIn posting fails**
- Verify your access token has `w_member_social` scope
- Confirm `LINKEDIN_PERSON_ID` is correct (call `GET /v2/me`)

**Buffer posting fails**
- Run `get_buffer_profiles` to confirm profile IDs
- Check that the target profile is connected in your Buffer account

**Posts not publishing automatically**
- Ensure the scheduler is running: `python3 scheduler.py`
- Check post status: ask *"Show posting status"* in chat
- Verify `scheduled_date` is today or earlier

---

## Extending the agent

- **Add a tool**: create a function in the relevant `tools/` file, decorate with `@tool`, add to the `*_TOOLS` list
- **Add a sub-agent**: create it in `agents/sub_agents.py`, add a node in `agents/graph.py`, update the router prompt
- **Swap LLM**: set `OPENAI_MODEL` in `.env` or pass `--model` on the CLI
- **Add a new platform**: add a posting function in `tools/publisher_tools.py` and wire it into `publish_scheduled_posts`

---

## Open source vs hosted (Loopmark)

Part of the [open-core architecture](#open-source) — see issue [#1](https://github.com/loopmark-opensource/loopmark-agent/issues/1).

### Open source today (this repo)

Free under MIT. Run locally or self-host with your own keys:

| Included | Details |
|---|---|
| LangGraph agents | Complaints, Posting, Funnel sub-agents |
| CLI | `python3 main.py` interactive chat |
| Tools | Content, email drafts, funnel, audience research, publishing |
| Storage | Local JSON via `storage/` (complaints, leads, posts, personas) |
| Credentials | BYOK — your `.env` keys via `credentials/` |
| Scheduler | `python scheduler.py` — local cron/daemon auto-posting |
| Audience research | Website URL analysis, CRM import, saved personas (no ad-platform APIs) |

**Not paywalled:** core agents, content generation, local JSON persistence, and publishing with **your** API keys.

### Planned hosted / paid layer (not shipped)

Roadmap items tracked as GitHub issues — **not available in this OSS repo**:

| Planned | Issue |
|---|---|
| Hosted web UI + chat API | [#7](https://github.com/loopmark-opensource/loopmark-agent/issues/7) |
| Credential vault + OAuth social connect | [#6](https://github.com/loopmark-opensource/loopmark-agent/issues/6) |
| Managed scheduler worker (retries, alerts) | [#11](https://github.com/loopmark-opensource/loopmark-agent/issues/11) |
| Orgs, RBAC, post approval workflows | [#10](https://github.com/loopmark-opensource/loopmark-agent/issues/10) |
| Stripe billing + usage metering | [#8](https://github.com/loopmark-opensource/loopmark-agent/issues/8) |

### Contributing

| Want to… | Do this |
|---|---|
| Fix bugs, add OSS tools, improve agents | Open a PR on this repo |
| Request hosted features (UI, vault, billing) | Open or comment on the roadmap issues above |
| Run locally | Follow [Installation](#installation) — no account required |

---

## Open source

This project is open source and released under the **MIT License**. You are free to:

- Use it commercially or personally
- Modify and adapt the code
- Distribute copies
- Contribute improvements back

See [LICENSE](LICENSE) for the full text.

### Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Make your changes and test locally
4. Open a pull request with a clear description

Please keep changes focused and match the existing code style.

See [docs/DISCOVERABILITY.md](docs/DISCOVERABILITY.md) for SEO, GitHub topics, and how to help the project get found online.

### Security

Do not commit secrets. Keep API keys in `.env` only — this file is gitignored. If you accidentally expose a key, rotate it immediately with your provider.

---

## Testing

Run the test suite locally:

```bash
pip install -r requirements.txt -r requirements-dev.txt
OPENAI_API_KEY=test-key-for-ci pytest
```

With coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

CI runs automatically on push and pull requests via GitHub Actions (Python 3.10, 3.11, 3.12).
