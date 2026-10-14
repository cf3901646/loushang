# Change-aware quality gates

The repository uses one Actions entrypoint, [quality.yml](../../../.github/workflows/quality.yml).
It selects checks once, calls the affected reusable workflows, and verifies
their results through `quality-gate`. Local development uses the same
[selection rules](../../../scripts/ci/check-scopes.json).

## Temporary long-running gate pause

The following entire reusable workflows are paused by user request while their
necessary scenarios and execution costs are reviewed:

| Workflow | Observed long task |
| --- | --- |
| Windows Shell Compatibility | Session recovery/direct 30–34 minutes; normal GC 27 minutes |
| Hosting Quality | Sustained Worker query 24 minutes |
| AppService Quality | Windows AppService 20 minutes |
| Host Runtime Quality | Runtime group 15 minutes |
| Registered Worker Reboot Drill | QEMU recovery 13 minutes |
| Harness Quality | Linux native/contract composite 11 minutes |

This applies to PRs, main pushes, scheduled and manual full validation. The
root `quality-gate` expects these workflows to skip and continues enforcing all
other selected workflows. Complete affected Harness, Hosting, AppService and
AppServer offline module regressions run through the module workflow instead;
Harness retains its four deterministic shards. Three-platform core persistence
and selected terminal cancellation smoke remain enabled. Windows tests in
other selected workflows remain enabled.

Original native test cases and inventories are retained. `PAUSED_WORKFLOWS` and
`PAUSED_MODULES` in `scripts/ci/select_checks.py` record the pause and offline
coverage replacement. Remove a workflow from both mappings when restoring its
reviewed gate. Runs already in progress keep their original selection plans.

Restore scenarios individually: ordinary module regression; one or two portable
core smoke flows; affected-platform native smoke; path-selected crash/GC/recovery;
and separately scheduled sustained/reboot campaigns. Record each scenario's
unique assertion, owner paths, runtime and duplicate coverage before restoring
it. Long campaigns must not silently return to ordinary PR gates.

## Selection policy

| Change | Required scope |
| --- | --- |
| Ordinary Markdown/RST documentation | Existing documentation invariants and changed Markdown links; no product dependency installation |
| Ordinary package source or classified unit test on a PR or main push | That package's complete offline regression directory and explicitly owned extras, plus documentation and source dependency facts |
| Session, conversation, transcript, or hosted application code on a PR or main push | Package units plus a focused create → turn → resume → turn → close E2E smoke |
| Public AI contracts, shared Foundation, plugin SDK, and platform or native code | Existing affected package and consumer gates |
| Terminal lifecycle/platform code | TUI units, playback, native PTY/ConPTY, and tmux; a PR runs one Windows ConPTY startup/exit case unless it changes native backend ownership |
| Hosting provider source | Hosting checks and its AppHost/AppService startup and settlement consumers |
| Hosted native/wheel evidence helpers, supervisors, and PTY/ConPTY fixture drivers | AppService quality plus G16/G17 native and installed matrices; native evidence changes retain full Windows coverage on the PR |
| Edits to the CI routing table, unit inventory, selector, gate verifier, or their existing contract tests | CI routing regressions, pinned Actions syntax check, one Agent module regression, and the three-platform E2E smoke |
| Edits to the module regression reusable workflow | CI routing and Actions syntax checks, every eligible package's complete offline regression, and the three-platform E2E smoke |
| Edits to a known product reusable workflow | CI routing and syntax checks, the complete owned workflow, and three-platform E2E; unrelated native suites are not selected |
| Edits to the E2E reusable workflow or its explicitly owned smoke test file | CI routing and syntax checks and both smoke cases on three platforms |
| Main merge push with matching successful PR evidence | Lightweight documentation and any applicable CI static checks, plus verification of the successful same-tree, same-plan PR run |
| Shared dependencies, main gate infrastructure, or unknown non-document paths | All configured checks |

The fast PR/main-push route is limited to known package source and exact test files in
the [routing inventory](../../../scripts/ci/unit-tests.json). New or unclassified
test files continue through the existing selector until reviewed. Each fast
module job runs every test in its package directory with offline selectors;
the routing inventory identifies eligible paths, not a smaller test subset.
Coding excludes its separately owned UI suite, and existing AI, Agent, Coding,
and Harness example tests retain their package owner. Coding, Harness,
HarnessTUI, and TUI module jobs use deterministic shards. A change touching
two packages runs both complete module regressions. Package source that selects
a platform, Worker, installation, LSP, or other high-risk gate also keeps the
existing route. The core E2E smoke creates a real hosted Coding session, executes the product's
read tool on a private UTF-8 fixture, closes its owners, reconstructs the catalog
and factory from the saved transcript, verifies restored messages and tool
results, and sends another message. It runs once on Linux, macOS and Windows
for code PRs. The composition canary with test session ports remains in the
Coding offline regression rather than being advertised as persistence evidence.

Agent, session, tool, approval and terminal control changes additionally select
one terminal cancellation smoke in the same platform job. This drives the real
screen input/render loop and AgentSession with scripted terminal IO: start a
controlled tool, press Escape, observe actual cancellation and task settlement,
then submit and render another reply before exiting. Native PTY/ConPTY checks
remain in their platform gates; this portable smoke does not replace them.
The model transport is synthetic and neither flow calls a live provider.
Reports require exactly one or two passing, non-skipped cases according to the
selection plan; selected smoke cases are excluded from concurrent module shards. Changes to the explicitly listed routing files exercise CI static checks,
the Agent module job, and E2E. Changes to the module regression workflow run
the complete eligible unit inventory instead of unrelated native suites. Known reusable workflows validate their own complete scope. The main orchestrator
and unclassified gate machinery retain full validation. Agent module regressions
are not scheduled a second time when the package quality gate already owns them.

The existing routing rules are additive outside this fast PR route. Makefile source/test inventories retain explicitly shared
support paths, such as the Coding product worker canary owned by Harness
checks. An unchanged package can still be affected by changed dependencies or
shared test infrastructure. Package dependency direction does not mean every
consumer change must rerun all of its providers' suites.

The narrow routing-file exception applies to pull requests and ordinary main
pushes. Scheduled/manual validation stays full. The main workflow, other unclassified CI files, test runners, build dependencies,
and new unclassified test files
still select the complete gate.

Windows jobs have a second selection within their affected scope. An ordinary
PR or main push selected for Windows Shell runs native shell execution and an
ordinary Session. Worker-native changes add one hosted Worker query with clean
exit evidence. Crash, recovery, GC, fence, and C5 scenarios run in scheduled or
manual full validation; changing several Worker risk paths together does not
expand an ordinary PR to the full native matrix.
The Linux Hosting Worker gate likewise runs one hosted Session on an ordinary
PR; its four direct, hosted, disable-fence, and update-fence cases remain in
scheduled/manual validation and on native boundary or test changes.
AppService runs one authenticated local request and one native console entry
case; TUI runs one ConPTY startup and
exit case. Changes to the native Worker test suite itself and Windows Job/process
ownership retain the full Worker matrix. Private data, ACL, and other native
platform code retain their affected full Windows jobs. Other gate infrastructure and unknown paths retain the complete
Windows matrix. Scheduled/manual validation uses the full Windows suites.
The Windows summary verifies each selected full or smoke job,
including expected skips, against the same change plan.

The host-runtime workflow runs at most two explicit Linux smoke cases on an
ordinary PR: Worker candidate admission for Coding, native launcher containment
for Hosting, or transcript process exit for Harness and other scopes. Its pytest
XML report must contain passing cases with no skips. Changes to the native
host-runtime tests, Windows Worker platform boundaries, or gate infrastructure
retain the affected full collection. Scheduled/manual validation preserves the
original repository-wide host-runtime collection.

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

PRs and main pushes use the fast package route for ordinary changes. The daily run at 20:17 UTC and
Actions → **Change-aware Quality** → **Run workflow** select all configured
checks. Main pushes still validate the merged state, but no longer launch every
suite unconditionally. Real LSP and native evidence commands retain their
existing explicit workflows and platform setup.

Multi-job reusable workflows check their complete job inventory against the
plan: selected jobs must succeed and unselected jobs must be skipped. The
single-owner architecture, module regression, and E2E workflows rely on the
top-level gate to check their workflow result without starting another runner.
Each module shard and E2E platform also verifies a nonempty passing JUnit
report. The top-level gate requires the selector to succeed. A selected job that fails, is
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
high-risk changes, unclassified paths, and scheduled/manual full validation. When changing the routing
inventory, confirm that the path is eligible for complete offline package
regression and that live or native tests remain behind their dedicated gates.

## Reusing successful PR validation after merge

A successful PR gate with E2E smoke selected uploads `pr-quality-evidence` for seven days. The evidence
records the actual checked-out Git tree, complete compact execution plan, PR number,
run ID and run attempt. An ordinary main push can reuse it only for a single merge
commit whose first parent is the push's previous main revision and whose second
parent is the head of the associated merged PR from this repository.

The lookup requires a completed successful run of this same workflow, for that exact PR head with artifact evidence recording the PR number, and an unexpired evidence artifact from the
same run attempt. Its tested tree and all execution-plan fields except changed
filenames must exactly match the main checkout and selected plan. The top-level
gate verifies that change selection succeeded and every reused workflow skipped;
it records the source run in the job summary. Documentation invariants and
applicable CI routing/syntax checks still execute on main.

Missing artifacts, old runs without evidence, API errors, failed/cancelled runs,
changed plans or trees, fork PRs, direct/squash/rebase/multiple-merge pushes, and
forced pushes fall back to normal selected testing. Scheduled/manual runs and
PRs always execute their selected tests. No test-result reuse occurs across
different code contents. This removes post-merge repetition without changing
which tests the PR must pass.
