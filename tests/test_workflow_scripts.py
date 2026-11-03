"""Tests for the github-script bodies in the issue assignment workflows (run with Node)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404 - runs the local Node harness only
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
HARNESS = Path(__file__).with_name("workflow_harness.js")
NODE = shutil.which("node")

# Skip locally without Node, but never silently in CI (GitHub runners ship Node).
pytestmark = pytest.mark.skipif(
    NODE is None and not os.getenv("CI"), reason="node is required to run workflow scripts"
)

REPO = {"owner": "loopmark-opensource", "repo": "loopmark-agent"}


def _script(workflow: str) -> str:
    data = yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))
    (job,) = data["jobs"].values()
    (step,) = [s for s in job["steps"] if s.get("uses", "").startswith("actions/github-script")]
    return step["with"]["script"]


def _run(workflow: str, context: dict, fake: dict | None = None, env: dict | None = None) -> dict:
    payload = json.dumps({"script": _script(workflow), "context": context, "fake": fake or {}, "env": env or {}})
    out = subprocess.run(  # nosec B603 - fixed argv, no shell
        [NODE, str(HARNESS)], input=payload, capture_output=True, text=True, check=True, timeout=30
    )
    return json.loads(out.stdout)


# ─── /assign and /unassign ────────────────────────────────────────────────

def _assign(body: str, assignees: list[str] | None = None, association: str = "NONE", **fake) -> dict:
    context = {
        "repo": REPO,
        "payload": {
            "issue": {"number": 56, "assignees": [{"login": a} for a in assignees or []]},
            "comment": {"body": body, "user": {"login": "alice"}, "author_association": association},
        },
    }
    return _run("issue-assign.yml", context, fake, {"MAX_OPEN_ASSIGNMENTS": "2"})


def _ops(result: dict) -> list[str]:
    return [c["op"] for c in result["calls"]]


def test_assign_claims_unassigned_issue():
    result = _assign("/assign")
    assert result["calls"][0] == {"op": "addAssignees", "assignees": ["alice"]}
    assert "@alice assigned" in result["calls"][1]["body"]
    assert "Closes #56" in result["calls"][1]["body"]


def test_assign_refuses_when_taken():
    result = _assign("/assign", assignees=["bob"])
    assert _ops(result) == ["createComment"]
    assert "already assigned to @bob" in result["calls"][0]["body"]


def test_assign_enforces_open_assignment_limit():
    result = _assign("/assign", openCount=2)
    assert _ops(result) == ["createComment"]
    assert "limit 2" in result["calls"][0]["body"]


def test_assign_limit_does_not_apply_to_maintainers():
    result = _assign("/assign", association="OWNER", openCount=5)
    assert _ops(result) == ["addAssignees", "createComment"]


def test_assign_reports_when_github_refuses():
    result = _assign("/assign", assignable=False)
    assert "would not assign you automatically" in result["calls"][-1]["body"]


def test_assign_when_already_assignee():
    result = _assign("/assign", assignees=["alice"])
    assert "already assigned to this issue" in result["calls"][0]["body"]


def test_unassign_releases_issue():
    result = _assign("/unassign", assignees=["alice"])
    assert result["calls"][0] == {"op": "removeAssignees", "assignees": ["alice"]}


def test_unassign_when_not_assignee():
    result = _assign("/unassign", assignees=["bob"])
    assert _ops(result) == ["createComment"]
    assert "not assigned" in result["calls"][0]["body"]


def test_similar_command_is_ignored():
    assert _assign("/assignee")["calls"] == []


# ─── PR assignment check ─────────────────────────────────────────────────

ISSUES = {
    "56": {"assignees": [{"login": "alice"}]},
    "54": {"assignees": []},
    "53": {"assignees": [{"login": "bob"}]},
    "45": {"assignees": [], "pull_request": {}},
}


def _check(body: str, association: str = "NONE", user_type: str = "User", comments=None) -> dict:
    context = {
        "repo": REPO,
        "payload": {
            "pull_request": {
                "number": 59,
                "body": body,
                "user": {"login": "alice", "type": user_type},
                "author_association": association,
            }
        },
    }
    return _run("pr-assignment-check.yml", context, {"issues": ISSUES, "comments": comments or []})


@pytest.mark.parametrize("body", ["Closes #56", "Resolves: #56", "fixes #56 and docs", "FIXED #56"])
def test_check_passes_for_assigned_issue(body):
    result = _check(body)
    assert result["failed"] is None
    assert result["calls"] == []


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ("Small fix", "does not link an issue"),
        ("Related to #56", "does not link an issue"),
        ("Fixes #54", "#54 is not assigned to you yet"),
        ("Closes #53", "#53 is assigned to @bob"),
        ("Closes #999", "#999 was not found"),
        ("Closes #45", "#45 is a pull request"),
        ("Closes #56, closes #54", "#54 is not assigned to you yet"),
    ],
)
def test_check_fails_with_reason(body, reason):
    result = _check(body)
    assert reason in result["failed"]
    assert result["calls"][0]["op"] == "createComment"
    assert reason in result["calls"][0]["body"]


@pytest.mark.parametrize(("association", "user_type"), [("OWNER", "User"), ("COLLABORATOR", "User"), ("NONE", "Bot")])
def test_check_skips_maintainers_and_bots(association, user_type):
    result = _check("no issue link", association=association, user_type=user_type)
    assert result == {"calls": [], "failed": None}


def test_check_updates_existing_comment_instead_of_reposting():
    existing = [{"id": 7, "body": "<!-- pr-assignment-check -->\nold"}]
    failing = _check("Small fix", comments=existing)
    assert _ops(failing) == ["updateComment"]

    passing = _check("Closes #56", comments=existing)
    assert passing["calls"][0]["op"] == "updateComment"
    assert "check passed" in passing["calls"][0]["body"]
