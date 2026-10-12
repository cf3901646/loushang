# Change-aware quality gates

The repository uses one Actions entrypoint, [quality.yml](../../../.github/workflows/quality.yml).
It selects checks once, calls the affected reusable workflows, and verifies
their results through `quality-gate`. Local development uses the same
[selection rules](../../../scripts/ci/check-scopes.json).

## Selection policy

| Change | Required scope |
| --- | --- |
| Ordinary Markdown/RST documentation | Existing documentation invariants and changed Markdown links; no product dependency installation |
| Ordinary package source or classified unit test on a PR | That package's [unit inventory](../../../scripts/ci/unit-tests.json), plus documentation and source dependency facts |
| Session, conversation, transcript, or hosted application code on a PR | Package units plus a focused create → turn → resume → turn → close E2E smoke |
| Public AI contracts, shared Foundation, plugin SDK, and platform or native code | Existing affected package and consumer gates |
| Terminal lifecycle/platform code | TUI units, playback, platform units, native PTY/ConPTY, and tmux |
| Hosting provider source | Hosting checks and its AppHost/AppService startup and settlement consumers |
| Hosted native/wheel evidence helpers, supervisors, and PTY/ConPTY fixture drivers | AppService quality plus G16/G17 native and installed matrices |
| PR-only edits to the CI routing table, selector, gate verifier, or their existing contract tests | CI routing regressions and pinned Actions syntax check, plus documentation invariants |
| Shared dependencies, gate infrastructure, or unknown non-document paths | All configured checks |

The fast PR route is limited to known package source and exact test files in
the unit inventory. New or unclassified test files continue through the
existing selector until they are reviewed and added to the inventory. Package
source that selects a platform, Worker, installation, LSP, or other high-risk
gate also keeps the existing route. The unit inventory is intentionally a
focused suite of isolated tests, not a claim that every test under a package
directory is a unit test. Each package gets a separate CI matrix job; a change
touching two packages runs both unit inventories. The E2E smoke reopens a real
hosted session and sends a second message.

The existing routing rules are additive outside this fast PR route. Makefile source/test inventories retain explicitly shared
support paths, such as the Coding product worker canary owned by Harness
checks. An unchanged package can still be affected by changed dependencies or
shared test infrastructure. Package dependency direction does not mean every
consumer change must rerun all of its providers' suites.

The narrow routing-file exception applies only to pull requests. Main pushes
and scheduled/manual validation keep their existing scopes. Other CI files,
workflow definitions, test runners, build dependencies, and new unclassified
test files still select the complete gate.

The host-runtime workflow also limits collection to affected package test
directories. A Coding-only plan collects Coding host-runtime tests, not Harness
tests. Full validation preserves the original repository-wide host-runtime
collection.

Coding backend collection excludes the Coding UI test inventory already owned
by the separate adapter job. This avoids rerunning that UI suite indirectly
through a backend or host-runtime check.

Machine-consumed evidence manifests and Markdown test fixtures are not ordinary
documentation. The generated package dependency document also triggers source
fact verification. The source graph is checked once; the lightweight document
check reuses existing pure document assertions without pytest collection or
product imports. Changed Markdown links are checked for existing repository
targets; remote URL reachability and heading anchors are not checked.

PR selection uses the merge base with the PR head. Main pushes use the complete
before/after range. Renames include both old and new paths; local selection
includes staged, unstaged, and untracked files. An invalid comparison or malformed
plan fails instead of silently selecting nothing.

## Local commands

```bash
# Explain the plan without installing dependencies or running tests.
python3 scripts/ci/check_changed.py --plan-only

# Preview or run the same fast package route used by PRs.
.venv/bin/python scripts/ci/check_changed.py --pr-fast --plan-only
.venv/bin/python scripts/ci/check_changed.py --pr-fast

# Run the local portion with the existing virtual environment.
.venv/bin/python scripts/ci/check_changed.py

# Compare against another integration branch.
.venv/bin/python scripts/ci/check_changed.py --base main

# Request all configured scopes explicitly.
.venv/bin/python scripts/ci/check_changed.py --full

# Existing Make entrypoints.
make plan-checks
make check-changed
make check-docs-light
make check-agent
```

On Windows, use `python` and `.venv\Scripts\python.exe` as appropriate. Selection
and direct Python scopes are portable; the legacy Make-based scopes still need
Make. Local execution reports platform, installation, and real-LSP scopes that
must run in Actions; a local success is not a substitute for that evidence.
Existing offline and host-runtime selectors are preserved. Do not repeat a
passed suite without relevant changes or an unresolved failure.

## Actions and branch protection

PRs use the fast package route for ordinary changes. Main pushes keep the
existing affected-check selection. The daily run at 20:17 UTC and
Actions → **Change-aware Quality** → **Run workflow** select all configured
checks. Main pushes still validate the merged state, but no longer launch every
suite unconditionally. Real LSP and native evidence commands retain their
existing explicit workflows and platform setup.

Every called workflow checks its complete job inventory against the plan:
selected jobs must succeed and unselected jobs must be skipped. The top-level
gate also requires the selector to succeed. A selected job that fails, is
cancelled, goes missing, or is unexpectedly skipped cannot produce a green gate.

The first migration stage retains these existing required context names:

- `Architecture documentation`
- `ai-quality`
- `harness-quality`
- `harnesstui-quality`
- `tui-cross-platform-contracts`

They all depend on `quality-gate`, so branch protection can remain unchanged
while the new workflow is verified. These five compatibility jobs are cheap,
but do still allocate runners. After successful remote validation:

1. Add `quality-gate` to the required checks for `main`.
2. Confirm it is reported by GitHub Actions and protects the expected branch.
3. Remove the old contexts from both the ruleset and classic branch protection.
4. Remove the five compatibility jobs in a subsequent PR.

Do not remove the old requirements before the replacement is reporting. A
whole workflow skipped by a path filter can leave required checks pending;
this design keeps an unconditional entrypoint and validates job-level skips.
See GitHub's [workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
and [reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows).

## Maintaining the rules

Run `python3 -m unittest discover -s tests/ci -v` after changing selection or
aggregation. These tests cover documentation, package consumers, native
terminals, evidence manifests, Git ranges, renames, and rejection of false green
results. Actions also checks workflow syntax with pinned actionlint 1.7.12 when
CI infrastructure changes. Platform evidence manifests and their verifiers
remain in the corresponding reusable workflows.

Broad Harness/AppHost/Hosting suite commands remain available for selected
high-risk changes, main pushes, and full validation. When changing the unit
inventory, include tests that have no live provider or native runtime
dependency, and confirm the exact scope locally before merging.
