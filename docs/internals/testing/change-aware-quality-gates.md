# Change-aware quality gates

The repository uses one Actions entrypoint, [quality.yml](../../../.github/workflows/quality.yml).
It selects checks once, calls the affected reusable workflows, and verifies
their results through `quality-gate`. Local development uses the same
[selection rules](../../../scripts/ci/check-scopes.json).

## Selection policy

| Change | Required scope |
| --- | --- |
| Ordinary Markdown/RST documentation | Existing documentation invariants and changed Markdown links; no product dependency installation |
| Ordinary package source or classified unit test on a PR | That package's complete offline regression directory and explicitly owned extras, plus documentation and source dependency facts |
| Session, conversation, transcript, or hosted application code on a PR | Package units plus a focused create → turn → resume → turn → close E2E smoke |
| Public AI contracts, shared Foundation, plugin SDK, and platform or native code | Existing affected package and consumer gates |
| Terminal lifecycle/platform code | TUI units, playback, native PTY/ConPTY, and tmux; a PR runs one Windows ConPTY startup/exit case unless it changes native backend ownership |
| Hosting provider source | Hosting checks and its AppHost/AppService startup and settlement consumers |
| Hosted native/wheel evidence helpers, supervisors, and PTY/ConPTY fixture drivers | AppService quality plus G16/G17 native and installed matrices; native evidence changes retain full Windows coverage on the PR |
| PR-only edits to the CI routing table, selector, gate verifier, or their existing contract tests | CI routing regressions, pinned Actions syntax check, one Agent module regression, and the three-platform E2E smoke |
| Shared dependencies, gate infrastructure, or unknown non-document paths | All configured checks |

The fast PR route is limited to known package source and exact test files in
the [routing inventory](../../../scripts/ci/unit-tests.json). New or unclassified
test files continue through the existing selector until reviewed. Each fast
module job runs every test in its package directory with offline selectors;
the routing inventory identifies eligible paths, not a smaller test subset.
Coding excludes its separately owned UI suite, and existing AI, Agent, Coding,
and Harness example tests retain their package owner. Coding, Harness,
HarnessTUI, and TUI module jobs use deterministic shards. A change touching
two packages runs both complete module regressions. Package source that selects
a platform, Worker, installation, LSP, or other high-risk gate also keeps the
existing route. The E2E smoke reopens a real hosted session and sends a second
message. PRs that edit the four listed routing files exercise CI static checks,
the Agent module job, and E2E. Other gate machinery retains full validation.

The existing routing rules are additive outside this fast PR route. Makefile source/test inventories retain explicitly shared
support paths, such as the Coding product worker canary owned by Harness
checks. An unchanged package can still be affected by changed dependencies or
shared test infrastructure. Package dependency direction does not mean every
consumer change must rerun all of its providers' suites.

The narrow routing-file exception applies only to pull requests. Main pushes
and scheduled/manual validation keep their existing scopes. Other CI files,
workflow definitions, test runners, build dependencies, and new unclassified
test files still select the complete gate.

Windows jobs have a second selection within their affected scope. An ordinary
PR selected for Windows Shell runs three native cases: shell execution, an
ordinary Session, and a hosted Worker query with clean exit evidence.
AppService runs one authenticated local request and one native console entry
case; TUI runs one ConPTY startup and
exit case. Windows Worker recovery and GC changes retain the full Worker jobs;
private data, ACL, and native package or platform changes retain their affected
full Windows jobs. Gate infrastructure and unknown paths retain the complete
Windows matrix. Main pushes and scheduled/manual validation use the full
Windows suites. The Windows summary verifies each selected full or smoke job,
including expected skips, against the same change plan.

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

The required `main` status is `quality-gate`. Ordinary documentation-only PRs
run the lightweight documentation invariants and changed-link check inside the
existing `changes` job. They select no reusable workflows, so their only
runner jobs are `changes` and `quality-gate`. The generated source dependency
document still selects the architecture source-facts workflow; mixed changes
retain every affected product check. A failure in documentation validation
fails `changes`, which in turn fails `quality-gate`.

The entrypoint always runs: skipping the whole workflow with a path filter can
leave a required check pending. The gate validates job-level skips and selected
results.
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
high-risk changes, main pushes, and full validation. When changing the routing
inventory, confirm that the path is eligible for complete offline package
regression and that live or native tests remain behind their dedicated gates.
