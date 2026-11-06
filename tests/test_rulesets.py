"""Branch rulesets must enforce issue assignment on every branch contributors target."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RULESETS = Path(__file__).resolve().parent.parent / ".github" / "rulesets"
GITHUB_ACTIONS_APP_ID = 15368


def _load(name: str) -> dict:
    return json.loads((RULESETS / f"{name}.json").read_text(encoding="utf-8"))


def _required_checks(ruleset: dict) -> set[str]:
    (rule,) = [r for r in ruleset["rules"] if r["type"] == "required_status_checks"]
    return {c["context"] for c in rule["parameters"]["required_status_checks"]}


@pytest.mark.parametrize("branch", ["main", "dev"])
def test_branch_requires_pr_ci_and_issue_assignment(branch):
    ruleset = _load(branch)
    assert ruleset["enforcement"] == "active"
    assert ruleset["conditions"]["ref_name"]["include"] == [f"refs/heads/{branch}"]
    assert any(r["type"] == "pull_request" for r in ruleset["rules"])
    assert {"Required checks", "Issue assignment"} <= _required_checks(ruleset)


def test_dev_lets_sync_workflow_fast_forward():
    actors = _load("dev")["bypass_actors"]
    assert {"actor_id": GITHUB_ACTIONS_APP_ID, "actor_type": "Integration", "bypass_mode": "always"} in actors


def test_main_has_no_integration_bypass():
    assert all(a["actor_type"] != "Integration" for a in _load("main").get("bypass_actors", []))
