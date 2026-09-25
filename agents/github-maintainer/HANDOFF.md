# GitHub publication handoff

## Target
Publish the prepared repository as a public open-source repository named `PoseFix` under the connected GitHub account.

## Current local state
- branch: `main`
- repository structure hardened for public collaboration
- tests: 7 passing in the current environment using `PYTHONPATH=.`
- Python bytecode compilation: passing
- lightweight secret-pattern scan: clean
- local `ruff` execution: not available in the current offline environment; CI is configured to install and run Ruff on GitHub

## Publication sequence
1. Create an empty public repository named `PoseFix` without generated README/license files.
2. Push the current `main` history.
3. Confirm GitHub Actions CI passes.
4. Enable Discussions if desired.
5. Enable private vulnerability reporting if available.
6. Protect `main` with pull-request + required CI checks when repository permissions allow.
7. Do not tag `v0.3.0` until the first live-provider validation is complete unless explicitly approved as a pre-release snapshot.

## Release gate
Follow `agents/github-maintainer/checklist.md` and Project Steward status.
