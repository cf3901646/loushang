# Issue 803: long-session responsiveness investigation

## Status

- Authority: informative — measurement and implementation review
- Implementation status: partial; end-to-end response acceptance is pending
- Tracking: [#803](https://github.com/zhnt/loushang/issues/803)
- Baseline: `0adc4199466f67b63abc8ac6a01a72cfdc3c27e0`

## Architecture review scope

The implementation agent reviewed this change using the existing local
archmethod revision `0f9bd3ff51afabeaaf76cc38dff1ceb279b7d37e` and the workspace
high-risk change workflow. No upstream method was fetched.

- Strict historical identity/parent authority stays with the validated graph;
  only immutable suffix links take the extension path. Existing mutation APIs
  and compatible-mode repair retain their reconstruction behavior.
- The transcript UnitOfWork retains durable receipt validation, cancellation
  ownership, commit serialization and candidate publication order.
- Render segments and the lazy screen-text view retain immutable frame data;
  they do not become owners of session history or introduce history trimming.
- Terminal deadlines retain completed-input priority and waiter cleanup. No
  storage protocol, provider, approval or session-lifecycle contract is changed.

The performance objective remains open; this scope review is not acceptance of
unmet latency criteria or a statement of user approval.

## Workload and source isolation

A read-only local session was copied outside the repository into a private
workspace. The original session was not opened for writing or replayed as
commands. Reports carry only aggregate sizes and timings, with no transcript
content or session identifiers.

Sample A contains 191,719,829 bytes and 24,459 records. Its active path projects
to 4,909 display records: 468 prompts, 1,351 assistant messages, 3,082 tool
records and eight compactions. The normal resumed active window retains 17
records under the existing 320 logical-line budget; the full-window experiment
retains all 4,909. These are distinct scenarios.

The baseline platform is macOS, Python 3.11.15, using the lane's existing virtual
environment. Transcript decoding is excluded from append timing. An in-memory
Conversation store isolates repository preparation from filesystem latency;
this is not a Product tool execution or native terminal measurement.

## Finding: repeated repository reconstruction

Every single-record transcript commit rebuilt the complete validated BranchGraph,
including one child list per historical record. The replacement prepares a
separate graph from shallow copies of the lookup maps and a fresh child list
for each changed parent. Existing strict records have immutable identity/parent
links; they cannot point into the new suffix. Single and batch appends validate
new identities and parent links, including forward references within a batch,
and detect cycles among the new nodes before constructing the candidate.
Invalid IDs, duplicates, self-parent and missing-parent checks remain before
backend publication. Compatible graphs still fully normalize historical repairs,
including forward references supplied by the appended record.

The source repository, selected leaf and child lists remain detached. The
UnitOfWork still publishes its candidate only after a valid backend receipt;
its cancellation owner and commit lock are unchanged. Both single and batch
commits now use detached graph extension; compatible-mode graphs retain full
normalization. Regression coverage checks error parity, forward-parent batches,
empty batches, selected-branch preservation and immutable snapshot children.

Five alternating process pairs loaded the same isolated file with the same
interpreter and dependencies. Each process measured five bursts of three
append operations with a 5ms asynchronous heartbeat. Source snapshots were
fixed before measurement. The table reports per-process burst medians and
worst heartbeat intervals, in milliseconds.

| Pair | Baseline append median | Candidate append median | Baseline worst interval | Candidate worst interval |
| --- | ---: | ---: | ---: | ---: |
| 1 | 257.06 | 18.98 | 428.01 | 10.99 |
| 2 | 252.77 | 17.41 | 424.21 | 10.96 |
| 3 | 258.20 | 16.91 | 440.41 | 10.61 |
| 4 | 264.38 | 16.56 | 450.70 | 10.27 |
| 5 | 384.13 | 20.35 | 499.25 | 11.31 |

Across 25 bursts per version, median append time was 264.38ms versus 17.02ms;
the worst observed heartbeat interval was 499.25ms versus 11.31ms. This proves
an improvement in this isolated commit workload. It does not establish the
input-echo or Working-to-Worked acceptance criteria.

## Finding: rebuilding unchanged RenderLine objects

A full-window tool update reconstructed about 64,800 RenderLine objects even
when almost all record text was reused. The region now retains rendered lines
alongside its existing record-block cache and reuses unchanged line objects.
The cache shares the original block invalidation context (record identity,
expansion, window, width and style); focus labels remain regenerated controls.
The assistant/Worked suffix path also fills the per-record line cache.

A regression first failed on lost line identity, then passed after the change.
It compares all resulting text with a fresh region, checks detail controls and
exercises a tool replacement after the completion suffix path. Related screen
and transcript selections passed 98 tests. In a single exploratory full-window
profile, tool-end rendering fell from 624.28ms to 44.85ms. These profiled timings
include instrumentation overhead and are not the five-round UI acceptance
benchmark; cold initial rendering still took 17.27 seconds.

## Finding: replacing the complete committed render segment

Reusing line objects alone left the complete history in one new segment after
any tool change. The native RenderLoop therefore finalized every historical row
again. The region now retains one immutable segment per record, including its
leading separator and optional detail control. It preserves segment identity
when the record, expansion, layout context and control label are unchanged.
The final assistant/Worked suffix fills the same cache as ordinary updates.

The regression preserves all logical rows and compares text/control coordinates
against fresh full layout across widths, viewport heights, anchors and drafts.
Tool changes in a 2,000-record history now materialize at most five rows while
reusing more than 2,000 segments. A real screen-runner regression holds tool
execution and cancellation cleanup separately: draft editing and the Running /
Stopping timer remain observable before completion, one Worked is emitted,
original history objects remain present and no tasks survive shutdown. Both
normal and interrupted variants fail on the baseline because thousands of old
rows are finalized, and pass with record segments.

## Finding: flattening screen text for every input frame

ScreenConversationApp also copied every logical line into a string tuple on
every render for selection and hit testing. It now keeps an immutable frame's
line sequence behind a lazy text view. Individual lookups and requested slices
preserve original logical coordinates; selection snapshots still explicitly
capture their selected frame. A regression previously read 4,008 texts for a
single draft edit; it now limits frame text reads to 40 while checking both the
first historical row and the new draft remain accessible.

## Finding: grapheme scanning for plain commands

The full-history cold-frame profile spent substantial time segmenting printable
ASCII commands with the Unicode grapheme scanner. `wrap_cells` now slices
printable ASCII directly, preserving spaces, explicit empty lines and terminal
control removal. Tabs, controls and Unicode retain the existing cluster layout.
The structural regression first fails when ASCII invokes the cluster scanner;
Unicode, emoji and combining-character behavior is covered by the existing
cell-width suite. Cold full-history response remains an open acceptance item.

## Finding: render activity postponed terminal input deadlines

`read_input_chunk_or_render_tick` reused the original relative idle duration
inside its render-wakeup loop. Continuous output could restart Esc recognition
before every expiry; immediate animation and scheduled frames could postpone
terminal runtime deadlines in the same way. Each input wait now establishes
absolute monotonic deadlines and recomputes their remaining duration after
render activity. An expired deadline still performs the terminal-read and
render-waiter cleanup handoff before returning, so input completing during that
handoff keeps priority over the timeout.

Six deterministic regressions cover pending-input and terminal-runtime deadlines
under render events, immediate frames and scheduled frames. All six failed
before the fix. Existing zero-deadline input/EOF cleanup regressions remain green.
A private single-case real streaming subprocess check then acknowledged Esc in
33ms, preserved the draft and left no tasks. Multi-case full-history acceptance
is still pending; a shorter post-Esc keyboard gap in an exploratory probe also
exposed raw terminal Alt-prefix ambiguity under latency, so it is not counted
as a successful cancellation. The matched probe isolates Esc with a quiet
interval while retaining the requested 100ms acknowledgement threshold.

## Exploratory actual-screen measurements

The private offline probe uses the real screen runner, local ExecService child
processes, Bash result conversion, and the complete 24,459-record in-memory
transcript. It projects the read-only session and preserves its 4,909 display
records in the full-window scenario. Keyboard arrivals use absolute loop
scheduling deadlines and are observed in the physical viewport, including keys
after tool completion. This remains a harness integration measurement: it does
not run a live model, a complete Product agent turn, or a file-backed transcript.

One quiet-command exploration before record segments observed 1,129ms maximum
input echo and 504ms tool-return-to-Worked. After record segments it observed
123ms and 139ms respectively; input p95 was still about 112ms. A subsequent
exploration including lazy screen rows and ASCII wrapping observed 74ms maximum
input echo and 123ms Worked, with a separate quiet-command cancellation observing
50ms Esc acknowledgement. These single exploratory rounds do not prove the
five-round acceptance thresholds.

An earlier probe scanned the entire logical history in its output observer and
reported multi-second stalls caused by measurement overhead. That measurement
is explicitly invalid and excluded. A component-only viewport experiment also
did not represent the native renderer, which requests a complete logical frame
for terminal scrollback correctness. That optimization was removed; full
history and native scrollback semantics are preserved.

## Five-round candidate screen matrix

The frozen candidate was exercised in one continuing native screen loop, with
five rounds of each scenario in normal and interrupted forms (50 turns total).
It retained the complete display history rather than applying the resumed
window budget. Arrival deadlines and terminal conditions were the same across
rounds. p95/p99 use the nearest-rank definition. Esc has a quiet keyboard
interval to distinguish a standalone Esc from an intentional terminal Alt
prefix; the acknowledgement target remains 100ms.

| Scenario | Input p95 ms | Input p99 ms | Worked p95 ms | Esc p95 ms (cancelled) |
| --- | ---: | ---: | ---: | ---: |
| Quiet command | 67.59 | 88.11 | 125.65 | 61.59 |
| Continuous stdout/stderr | 69.25 | 100.89 | 89.21 | 93.85 |
| Three consecutive tools | 83.49 | 95.51 | 117.31 | 62.32 |
| 1.08MB ASCII result | 79.77 | 91.16 | 117.30 | 63.84 |
| 2.16MB UTF-8 result | **134.65** | 158.88 | 169.26 | 61.13 |

Input and Worked columns describe normal completion. Interrupted turns were
also measured; their highest input p95 was 94.04ms. Every draft was preserved,
all scheduled key echoes appeared, exactly one Worked appeared per turn, every
requested cancellation was observed, and shutdown left zero asynchronous tasks.
The maximum measured timer-frame gap was 180.06ms. Large results retained the
existing 51,200-byte preview and `bytes` truncation metadata; stdout fingerprints
and full captured byte counts were retained privately for baseline comparison.

**The Unicode-result input p95 does not meet the 100ms target.** The initial
unbounded logical frame also still took 15.18 seconds. Persistent/Product-turn acceptance and the complete five-round baseline
comparison remain pending.
A prototype UTF-8 fingerprint collector incorrectly used strict encoding on
byte-preserving surrogate escapes at preview boundaries; that prototype result
was discarded. The matched collector uses the same surrogate-escape encoding
contract as ExecService and explicitly requires successful tool receipts.

## Partial baseline screen comparison

The same frozen baseline was run separately with the same local commands,
read-only history, viewport and keyboard deadlines. It completed 25 measured
turns, including two complete rounds of all scenarios, over 431.61 seconds.
The agent stopped that negative-control run to run correctness gates; it did
not complete the required five baseline rounds. The private report retains all
completed measurements and the interrupted process status rather than treating
it as a passing benchmark.

Across its first two complete rounds, normal tool-return-to-Worked ranged from
1,391.83ms to 2,291.01ms. The corresponding candidate's five-round normal p95
values are shown above, but these are **not a complete five-pair comparison**.
Some baseline key echoes were still unobserved at the probe's post-completion
observation limit, and no requested cancellation in its 25 completed turns was
acknowledged as a cancellation. Missing observations are censored failures, not
zero-latency samples; a baseline Esc p95 cannot be reported from that run.

## Verification so far

- Conversation/UnitOfWork regressions after batch extension: 118 passed, 24 skipped.
- Region/screen/cell-width focused tests after ASCII wrapping: 137 passed.
- Screen, Coding screen and cell-width tests after lazy text rows: 130 passed.
- Terminal-input, screen, Coding screen and cell-width regressions after absolute
  deadlines: 167 passed.
- Region, terminal-input and real screen-runner regressions after block-cache
  identity reuse: 135 passed.
- Existing TUI unit route before the final segment changes: 1,312 passed.
- Existing render-contract route before the final segment changes: 311 passed.
- Changed-source Ruff and mypy checks passed (seven source files); architecture
  dependency validation passed, and HarnessTUI's 164-source mypy route passed.
- Full Harness units: 5,111 passed, 724 skipped, three deselected, 25 failed.
  All 25 failures report `rooted IO requires Linux` on this macOS host and
  reproduce on the frozen clean baseline in the exact failed-node selection.
- Original session size/mtime are unchanged, its isolated copy remains mode
  0400, and measured candidate source hashes match the working source.
- Final TUI units: 1,319 passed, 235 deselected. Final render contracts:
  311 passed, 7,615 deselected.
- Final HarnessTUI/Coding UI route: 1,656 passed, 153 deselected, two failed.
  Both are the known macOS PTY EXTPROC restoration cases in
  `test_loading_terminal_adapter`, with the same `2**29` local-mode flag delta.
- Terminal platform: 126 passed. Native terminal contracts: 13 passed.
  Selected host-runtime coverage: five passed, 25 skipped, 10,726 deselected.
- Offline Product E2E: two passed, covering real tool persistence/resume/close
  and terminal cancellation followed by a new message and exit. These are
  short-session correctness checks, not long-session latency acceptance.
- Documentation governance: nine passed. No CI gate, route or platform was added.

The earlier `make check-changed` run stopped in Coding on 128 failures and 39
errors. Of those node IDs, 166 match the known clean baseline. One additional
grep subprocess timing check observed 508ms against a 500ms bound; the exact
case then passed once on the clean baseline and once on the candidate. No
Product timeout was changed. Those results predate the final UI changes and
are not a final green gate.

## Remaining acceptance work

- Complete five matched actual-screen rounds for quiet commands, sustained
  output, consecutive tools, large ASCII and Unicode results, with normal
  completion and cancellation. Verify output/truncation metadata and drafts.
- Measure file-backed persistence and actual Product completion/context
  projection separately; the in-memory probe cannot establish those bounds.
- Investigate cold full-window rendering and resize. Its uninstrumented first
  frame still took about 17 seconds before ASCII wrapping. The bounded resume
  window and warm-cache improvement do not prove long-running resize is safe.
- Verify multiple history scales and rerun affected offline/native routes
  against the final source, reporting known environment baseline failures.
- Apply input p95/p99, Escape, timer and Worked thresholds only to valid matched
  measurements. The goal remains active and completion is unproven.
