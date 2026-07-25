# Marketing Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Open-source LangGraph marketing assistant — free to use, modify, and distribute under the [MIT License](LICENSE).

A LangGraph-powered AI marketing assistant with three specialised sub-agents. You talk to it in plain English — a router automatically sends your request to the right agent.

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
