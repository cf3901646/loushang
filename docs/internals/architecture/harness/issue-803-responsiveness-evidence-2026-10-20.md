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

## Real Product turn investigation (2026-10-21)

A second private probe restores the writable isolated session copy through
`SessionManager.open`, uses the real `AgentSession`, file persistence, context
meter and cooperative screen listener, and runs a synthetic model transport.
Only a new probe tool call is allowed; it executes a known local Python child.
The synthetic transport explicitly skips new durable Model Input commits; this
probe covers recovery/preparation and durable message/tool records, and does not
establish the cost of the provider commit-before-send barrier.
No historical tool call or external model request is executed. Runtime settings,
platform data and scratch files are redirected outside the repository.

This distinguishes the actual Product turn from the earlier memory-store screen
matrix. Single-round exploratory measurements on the normal resumed window were:

| Candidate stage | Input p95 | Tool completion to Worked | Maximum loop delay |
| --- | ---: | ---: | ---: |
| First local commit (`816f162d`) | 470.20ms | 608.69ms | 772.28ms |
| Cooperative evidence recovery | 527.33ms | 673.08ms | 515.59ms |
| Recovery plus context replay cache | 339.22ms | 437.06ms | 395.16ms |

These are diagnostic runs on a continuing isolated copy, not five matched
before/after rounds or acceptance evidence. Profiling timings are excluded from
latency acceptance. A path-cache run overlapped a static typecheck and is also
excluded from performance comparisons. No target has been relaxed.

### Durable evidence recovery occupied the model-call boundary

The first actual-turn profile found 2,976 indexed Model Input bundle reads during
evidence recovery. Recovery ran synchronously while preparing a model call.
The new async preparation drives the same checked recovery steps and yields
between records/snapshots after an eight-millisecond work budget. Staged caches
publish only after complete recovery; cancellation, closure and corruption do
not publish partial results. The final synchronous boundary still checks the
current path, message bindings and Session ownership before binding a committer.
A single opaque snapshot rebuild can still exceed the budget; this is not a
universal eight-millisecond bound on arbitrary histories.

### Context bindings repeatedly folded unchanged history

Model-call preparation also requested context bindings repeatedly, causing full
history folds. The UnitOfWork now retains one verified default-profile projection
and folds eligible suffix records. The cache key includes repository identity,
selected leaf and profile generation. Explicit record selections, custom
semantics, non-prefix branch changes and compaction checkpoints retain full
validation. Histories with mutable nested annotation/metadata state also retain
fresh replay. Background reads capture their selected leaf; a concurrent branch
selection cannot label an old path as the new one. Publication remains after
the durable receipt, including the existing cancellation settlement behavior.

### Repeated path walks and initial activation validation

The graph now retains one immutable path, reuses it for repeat reads, and walks
only new suffix links when a strict extension descends from that path. Compatible
repairs create a fresh graph and path. Record objects, branch membership and
old graph snapshots retain their existing meaning; the cache is bounded to one
path per graph.

A lightweight actual-turn trace also identified an initial 428.70ms synchronous
Coding activation-history check. Its async driver now shares the exact selected
path validator with the synchronous API. Cancellation publishes no guard;
commits/branch changes during a yield restart validation, and pending runtime
publication still rejects admission. The Coding preparation entry awaits this
check before ordinary execution. Later synchronous admission fences remain in
place and reuse only a completed matching revision/leaf check.

Blob reference collection also skips non-blob-bearing payload classes before
extracting references and avoids constructing repeated union-type checks. It
still scans relevant mutable message content/details on every call, preserves
stable deduplication order, accepts supported subclasses, and rejects foreign
Session references. No reference cache hides mutations or ownership checks.

### UTF-8 truncation could turn successful output into a tool error

The actual Product probe exposed a correctness failure hidden by the earlier
screen-only matrix: clipping a valid multibyte character could introduce lone
surrogates, which the transcript JSON boundary rejects. The byte-suffix helper
used `surrogateescape` inside a retry loop, so invalid leading bytes never raised
the exception intended to advance to a character boundary. The old boundary
example happened to cut exactly between characters.

The helper now uses a strict fast decode and, when necessary, finds the bounded
suffix in the original string. Valid UTF-8 stays valid; genuinely escaped source
bytes retain their previous byte meaning. Raw artifacts and original byte/line
counts remain unchanged. Four newly covered split-character cases and the real
ExecService-to-Bash preview check failed before the change and passed after it.
The focused truncation, execution and Bash suite passed 45 tests; the integration
case checks incremental and final JSON projection and exact full artifact bytes.

The first large-output probe failed because its private output directory was
missing. After fixing that setup, strict assertions exposed the Product JSON
failure above. Neither failed probe is latency acceptance evidence.

A later four-case diagnostic on frozen phase-two source (before the UTF-8 fix)
reported the following valid quiet/cancel observations. Input was sampled during
preparation and tool/completion windows, rather than continuously across all work:

| Scenario | Input p95 | Esc visible | Tool/cancel to Worked |
| --- | ---: | ---: | ---: |
| Quiet, normal completion | 107.70ms | — | 318.31ms |
| Cancel during preparation | 748.54ms | 187.09ms | No tool had started |
| Cancel during tool execution | 519.39ms | 35.79ms | 980.21ms |

These single rounds still fail the response targets and show long pauses remain.
The source was frozen separately from the earlier candidate, no static/test run
was concurrent, and no transcript/tool correctness failure was accepted as a
successful normal turn. Full matched rounds and continuous-input observation
remain outstanding.

After the UTF-8 fix, the strict large-Unicode Product probe completed with one
successful output, preserved the input draft and left no asyncio tasks after
disposal. Diagnostic input p95/p99 were 87.15/111.67ms and Worked was 312.23ms.
The latter still exceeds the 250ms target. This probe retained the earlier
windowed key schedule, so the input percentiles cannot establish uninterrupted
responsiveness throughout the turn.

GC observation recorded a 221.14ms generation-two collection on a background
thread at turn offset 1.49s; maximum event-loop delay was 247.06ms. The key
windows did not cover that entire pause. The exact allocation owner still needs
thread profiling; moving a computation to a thread alone does not prove that it
cannot pause input. The next private probe schedules absolute key deadlines
continuously through completion and records timer-frame gaps as well. No GC
threshold, timeout or acceptance target was changed. Original session size/mtime
and the read-only copy's 0400 mode were checked again, and current Product source
hashes match the separately frozen UTF-8 candidate.

Focused validation after these changes: 325 passed, 24 skipped. Changed-source
Ruff passed and mypy passed for nine source files. Deterministic
regressions observe work before completion, cancellation without publication,
branch changes while suspended, compatible repairs, and receipt-confirmed
publication. Full response acceptance remains pending.

The required phase-two `make check-changed` run passed documentation and source
dependency validation, then stopped in Coding: 3,357 passed, 283 skipped,
55 deselected, 128 failed and 39 errors (977.25s). The 167 failing node IDs exactly
match the prior diagnostic list: known platform failures plus the recurring grep
500ms timing check, which observed 604.17ms in this run. This is not a green gate
or proof that all failures are environmental. In the isolated exact-case rerun,
the frozen baseline failed at 521.01ms and the current candidate passed. Both
launchers verified their imported source before pytest configuration, and neither
Product timeouts nor the 500ms assertion were changed.

The complete affected Harness offline route passed 5,133 tests, skipped 724 and
deselected three, with the same 25 previously reproduced Linux-rooted-I/O failures
on macOS (392.14s); no new failing node appeared. The earlier TUI-library routes
remain evidence for unchanged source. Repeated consumer UI validation passed
1,656 tests, with 153 deselected and the same two macOS PTY mode-restoration
failures (282.43s). Its Ruff and 164-source mypy checks passed. Hosting offline
regression passed 257 tests, with 193 skipped and four deselected; the two real
Product persistence/cancellation E2E smoke cases passed as well.

## Phase three: prepared transport and repeated activation checks

The private offline probe now uses the normal prepared-provider adapter path.
It verifies the committed snapshot receipt and prepared-payload hash before
each transport call. One new controlled tool call produces two new durable
Model Inputs. Continuous absolute key deadlines cover preparation, execution
and completion. Historical tools are never invoked, and network connections
are blocked. The earlier synthetic transport explicitly omitted these commits;
its timings cannot establish the cost of the real Model Input barrier.

The isolated-file setup also needed correction. Native writer-head metadata is
bound to filesystem identity. Copying a journal invalidates its head, even when
the deferred-read index remains valid. A cold copy's first write therefore
strictly reconciles the entire prefix. The original sample has a valid head.
Warm-write fixtures now use the backend's idempotent append of the already
existing final record, outside the measurement process, to establish a native
head. Both authority bytes and journal mtime are checked unchanged. Cold
recovery remains a separate required scenario; its approximately 35-second
tool-start observation is not representative of an ordinary valid-head append.

With a valid head, the previous committed source still showed an approximately
1,013ms maximum input delay and 1,206ms Worked delay. Its first Model Input
commit took 1,123ms, including 553ms building the historical node index; the
second commit took 353ms. These are exploratory single rounds.

Stage tracing found another synchronous replay after Model Input metadata
advanced the transcript revision: the next Coding message ran the complete
activation projector again, taking approximately 352ms immediately before
Worked. The new Coding guard can reuse its completed classification only when
the entire checked prefix is activation-neutral, native immutable record
identities remain an exact prefix, and the new suffix has valid unique parent
links and no activation intent or reserved runtime-binding key. A later
sensitive fact still gets full ancestry hashing. Bound histories retain the
existing local input-proof check. This deliberately leaves their repeated full
validation as remaining work.

Ordinary-message guard advancement now inspects the committed record and its
selected prefix, including all `coding.runtimeBinding*` keys. It previously
checked only the v1 key in the caller's mutable metadata. Four regressions
first demonstrated that v2/future keys, caller mutation and a concurrent branch
change could bypass the next fence; all pass after the correction. Pending
publication still blocks before any cache lookup.

Cold/branched Model Input indexes now build cooperatively between the same
node checks. Cancellation, malformed history, a changed revision/leaf or a
changed compatibility token prevents publication of the new cache. A previous
branch cache remains intact. Synchronous consumers retain the same generator
and validation. Warm suffix indexing and the durable commit-before-send
barrier are unchanged. Ten regression cases exercise both cold and existing
branch caches, including observation while preparation is incomplete.

The latest isolated prepared round, with 24,459 initial records and 8,967
deferred bundles, recorded the following. This is not a matched five-round
acceptance result:

| Measurement | Observed |
| --- | ---: |
| Continuous input samples | 315 |
| Input p95 / p99 / maximum | 345.62 / 461.40 / 544.88ms |
| Maximum event-loop delay | 412.60ms |
| Maximum timer-frame gap | 576.60ms |
| Maximum warm render frame | 12.48ms |
| Final activation guard | 19.38ms |
| Tool exit to Worked | 1,267.21ms |

Two main-thread generation-two collections still took 280.98ms and 361.16ms.
The second Model Input commit still took 499.25ms. Input and Worked targets
remain unmet. A separate reopened process rebuilt both new Model Inputs through
the Product API, verified their hashes, the new prompt/tool identity and both
terminal usage facts, and checked authority bytes/mtime unchanged. Draft
preservation, one Worked divider and no remaining asyncio tasks also passed.

A separate continued-session cancellation round used the same private copy
after that normal turn. Escape displayed Stopping in 33.59ms and cancelled the
controlled running tool, preserving the draft and leaving no asyncio tasks.
Cancellation-to-Worked still took 652.40ms, with input p95/p99 of
277.38/341.57ms. This is one continued-session round, not a matched cancellation
acceptance result. A completion-only profiler is now available for diagnosis;
its instrumented latency is excluded from acceptance comparisons.

The prepared consecutive-tool probe now invokes three distinct controlled new
tools through the real sequential Agent executor. The short-session smoke
passed with a 6.95ms maximum input delay and 77.09ms Worked delay. In a separate
continued long-session round all three tools succeeded, the draft remained
exact and disposal left no asyncio tasks; maximum input delay was 385.08ms and
Worked took 908.94ms. This corrects the earlier probe's single-tool coverage;
matched long-session consecutive-tool acceptance is still outstanding.

Two allocation experiments were withdrawn: selective per-node bundle decoding
caused repeated parsing and showed no valid response improvement; replacing
per-node callback wrappers with bundle references also failed to establish an
end-to-end improvement. Neither change is retained. No GC policy, timeout or
response threshold was changed.

Current focused offline validation passed 220 tests covering Model Input,
deferred file indexes, request evidence, activation and bindings. Changed-source
Ruff and three-source mypy passed. The required `make check-changed` run passed
documentation and architecture validation, then stopped in Coding: 3,374 passed,
283 skipped, 55 deselected, 127 failed and 39 errors (867.71s). The 166 failing
node IDs are all in the previously established baseline; the additional grep
timing failure from the earlier run did not recur. This is not a green gate.

The complete Harness offline route passed 5,143 tests, skipped 724 and deselected
three, with exactly the same 25 Linux-rooted-I/O failures on macOS (325.78s).
Harness Ruff passed. Its full 775-source mypy route stopped on six errors for
`_pid_namespace_digest` in the unchanged sandbox legacy-runtime module. An
isolated full 775-source run against the frozen prior source reproduced those
same six errors at identical locations. No unrelated runtime code or type gate
was changed to suppress them. Matched normal/cancelled acceptance rounds remain
pending.

Hosting offline regression passed 257 tests, with 193 skipped and four
deselected. The two real Product persistence/resume/close and terminal
cancellation/new-message/exit E2E smoke cases passed (4.35s). Documentation
validation passed nine tests. Product source hashes still match the separately
frozen phase-three candidate; the proposed continuation-purpose and bound-proof
cache changes are separate private experiments, outside this checked snapshot.

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
- Complete matched file-backed Product measurements through the prepared offline
  transport, including separate valid-head and cold-recovery workloads. The
  completed exploratory prepared round does not replace matched acceptance.
- Investigate cold full-window rendering and resize. Its uninstrumented first
  frame still took 15.18 seconds with the first committed candidate. The bounded resume
  window and warm-cache improvement do not prove long-running resize is safe.
- Verify multiple history scales and rerun affected offline/native routes
  against the final source, reporting known environment baseline failures.
- Apply input p95/p99, Escape, timer and Worked thresholds only to valid matched
  measurements. The goal remains active and completion is unproven.
