# Contributing to Loopmark Agent

Thanks for helping improve the open-source marketing agent. This guide covers local setup, tests, pull requests, and what belongs in OSS vs the planned paid layer.

## Development setup

Requirements: Python 3.10+.

```bash
git clone https://github.com/loopmark-opensource/loopmark-agent.git
cd loopmark-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env        # add your OPENAI_API_KEY for live chat
```

Run the CLI:

```bash
loopmark-agent chat
# or
python main.py chat
```

## Tests

CI uses a placeholder key so unit tests never call OpenAI:

```bash
OPENAI_API_KEY=test-key-for-ci pytest
```

With coverage:

```bash
OPENAI_API_KEY=test-key-for-ci pytest --cov=. --cov-report=term-missing
```

Security scans (also run in CI):

```bash
bandit -c bandit.yaml -r .
pip-audit
```

Rebuild the docs site after editing `scripts/build_docs_site.py`:

```bash
python scripts/build_docs_site.py
```

## Pull request expectations

1. Fork and branch from `dev` (`git checkout -b fix/short-description`).
2. Keep changes focused — one concern per PR when practical.
3. Match existing style (type hints, small tools, no unrelated refactors).
4. Add or update tests for behavior changes.
5. Do not commit `.env`, credentials, or `data/` (may contain PII).
6. Open the PR against `dev` with a short summary and test plan.

## OSS vs paid boundary

**In scope for this repo (OSS):** CLI agents, tools, local storage, audience research (website + CRM import), publishing helpers that use the user's own API keys, docs, and tests.

**Out of scope here (roadmap / paid layer):** hosted web UI, credential vault, OAuth social connect, managed scheduler workers, orgs/RBAC, Stripe billing. Track those under the epic [#1](https://github.com/loopmark-opensource/loopmark-agent/issues/1) and related roadmap issues — comment there rather than implementing them in OSS PRs unless maintainers ask.

## Reporting bugs and features

Use the GitHub issue templates:

- **Bug report** — what broke, steps to reproduce, environment
- **Feature request** — problem, proposed approach, OSS vs paid

Please search existing issues first.

## Discoverability

Ideas for SEO, GitHub topics, and external listings live in [docs/DISCOVERABILITY.md](docs/DISCOVERABILITY.md).
