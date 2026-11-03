# Releasing to PyPI

`loopmark-agent` publishes with [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) from `.github/workflows/publish-pypi.yml`. No API tokens are stored in the repo.

## One-time setup (repo admin)

### 1. Register the trusted publishers

The project does not exist on PyPI yet, so add a **pending** publisher on each index:

- PyPI: [pypi.org/manage/account/publishing](https://pypi.org/manage/account/publishing/)
- TestPyPI: [test.pypi.org/manage/account/publishing](https://test.pypi.org/manage/account/publishing/)

| Field | Value |
|---|---|
| PyPI project name | `loopmark-agent` |
| Owner | `loopmark-opensource` |
| Repository name | `loopmark-agent` |
| Workflow name | `publish-pypi.yml` |
| Environment name | `pypi` (on PyPI) / `testpypi` (on TestPyPI) |

### 2. Create the GitHub environments

In [Settings → Environments](https://github.com/loopmark-opensource/loopmark-agent/settings/environments), create `pypi` and `testpypi`. On `pypi`, add yourself as a **required reviewer** so every production upload needs a click to approve.

## Cutting a release

1. Bump `version` in `pyproject.toml` on `main` (CI's **Package build and install** job checks that the wheel builds and runs).
2. Optional dry run: **Actions → Publish to PyPI → Run workflow**, target `testpypi`, then:

   ```bash
   python -m venv /tmp/lm && /tmp/lm/bin/pip install \
     --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ loopmark-agent
   /tmp/lm/bin/loopmark-agent --help
   ```

3. Create a GitHub Release whose tag is `v` plus the version, for example `v1.0.0`. The workflow refuses to publish if the tag and `pyproject.toml` disagree.
4. Approve the `pypi` environment deployment when prompted.
5. Verify from a clean venv:

   ```bash
   python -m venv /tmp/lm && /tmp/lm/bin/pip install loopmark-agent
   /tmp/lm/bin/loopmark-agent --help
   ```

PyPI never lets a version be re-uploaded, even after deleting it. If a release is broken, bump the version and release again.
