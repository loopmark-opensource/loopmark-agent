"""Security-focused tests for secrets handling and safe defaults."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIRS = ("agents", "tools", "models", "prompts")
SOURCE_FILES = ("config.py", "main.py", "scheduler.py")

# Patterns that indicate accidentally committed credentials.
SECRET_PATTERNS = (
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"ls__[a-zA-Z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
)


def _iter_source_files() -> list[Path]:
    paths: list[Path] = []
    for name in SOURCE_FILES:
        path = REPO_ROOT / name
        if path.is_file():
            paths.append(path)
    for directory in SOURCE_DIRS:
        root = REPO_ROOT / directory
        if root.is_dir():
            paths.extend(root.rglob("*.py"))
    return paths


def test_env_file_is_gitignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text()
    assert ".env" in gitignore


def test_no_hardcoded_secrets_in_source() -> None:
    violations: list[str] = []
    for path in _iter_source_files():
        content = path.read_text()
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                violations.append(f"{path.relative_to(REPO_ROOT)} matches {pattern.pattern}")
    assert not violations, "Potential secrets found:\n" + "\n".join(violations)


def test_env_example_uses_placeholders() -> None:
    env_example = (REPO_ROOT / ".env.example").read_text()
    assert "sk-..." in env_example
    assert "ls__..." in env_example
    for pattern in SECRET_PATTERNS:
        assert not pattern.search(env_example), f".env.example contains a real secret pattern: {pattern.pattern}"


def test_config_does_not_log_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "super-secret-test-key")
    from importlib import reload

    import config

    reload(config)
    config_repr = repr(config.config)
    assert "super-secret-test-key" not in config_repr


def test_data_dir_default_is_project_relative() -> None:
    """Config should persist data under the project tree, not system paths."""
    config_text = (REPO_ROOT / "config.py").read_text()
    assert "os.path.dirname(__file__)" in config_text
    assert "data" in config_text
