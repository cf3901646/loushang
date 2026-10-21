# Tool exit to Worked: focused latency evidence

Status: measured; the 250ms p95 target is unmet. This note narrows the new
tool-completion objective. The broader responsiveness experiments are recorded
in `issue-803-responsiveness-evidence-2026-10-20.md`.

## Measurement boundary

The start is the controlled tool service returning its result. The end is the
first flushed terminal frame containing the matching Worked divider. A real
POSIX PTY, native terminal reader, independent physical keyboard process,
prepared offline model transport and restored file-backed Session were used.
The authority was an isolated continuation with approximately 29,100 records;
the original session remained read-only. The measured source was `cb8fcaeb`.

The earlier five-pair silent-command comparison measured tool exit to Worked
p95 at 1,329.02ms before the input-waiter fix and 1,276.65ms after it. Five
normal turns each of streaming output, three tools, 1.08MB ASCII and 2.16MB
Unicode measured p95 between 1,357.84ms and 1,720.77ms on the current source.
Those four workloads have no matched earlier-version counterpart.

## One unprofiled long-session trace

This diagnostic turn took **1,159.16ms** from tool exit to visible Worked.
The following intervals are from timestamps emitted at actual boundaries;
the model input commit is additionally measured by its own phase timer.

| Tool-exit offset | Boundary or operation | Elapsed |
| ---: | --- | ---: |
| 0–113.55ms | Tool result conversion, publication and entry into the next model-call preparation | 113.55ms |
| 113.55–256.33ms | Session model-call preparation, including request evidence and codec setup | 142.78ms |
| 256.33–283.02ms | Scheduling and adapter admission | 26.69ms |
| 283.02–478.04ms | Provider adapter builds the prepared request from the long context | 195.02ms |
| about 478.52–953.86ms | Durable model input commit before transport | 475.34ms |
| 953.86–1,159.16ms | Offline response, terminal outcome and Worked projection/flush | 205.30ms |

Within the 475.34ms commit, prepared-request validation took 94.79ms, logical
input thaw 16.29ms, binary externalization 51.23ms, resolver construction
13.81ms, materialization 203.77ms and snapshot append 15.35ms. The completed
writer used its extended index cache and reused 2,912 sequence items. No
generation-two collection occurred between tool exit and Worked in this turn;
the measured delay is intrinsic to the current post-tool path, even without a
GC pause.

An optional main-thread profiler inflated this path to 3.17 seconds, so its
times are excluded from latency acceptance. Its call counts locate repeated
full-context work across provider request construction, JSON validation,
canonicalization, transcript materialization and final projection. The
unprofiled stage timestamps above are the latency evidence.

Both diagnostic turns retained their draft, emitted one Worked divider and
executed no historical tools. Native reopening reconstructed four model input
snapshots with terminal usage and checked both tool results; the authority was
unchanged by verification.

## Prefix reuse boundary

One later isolated turn counted object identities on both sides of Agent's
message conversion. After the controlled tool, all 1,467 earlier Agent messages
were the same objects seen before it. The prepared adapter then received 1,469
normalized messages, and none of the 1,467 earlier positions retained object
identity across the two model calls. The converter and normalization boundary
therefore discards an identity-only cache key before provider preparation.

This is a feasibility observation, not permission to trust object identity:
message parts can contain mutable containers, and conversion, provider options
or the selected transcript path can change. Reuse must carry explicit immutable
provenance from the selected transcript and recheck the final suffix before
publishing a prepared request. The diagnostic turn's two snapshots, terminal
usage and tool output were rebuilt on native reopening without historical tool
execution or authority changes. Its extra identity logging is excluded from
latency acceptance.

Native reconstruction of two further ordinary silent-command continuations
checked the exact serialized requests. In the shorter history, both logical
and prepared message lists grew from 231 to 233; in the longer history they
grew from 1,459 to 1,461. In each case the entire earlier message list was an
equal prefix and every non-message field was equal. Both authorities stayed
unchanged. This establishes that an append-only reuse path is applicable to
these turns; it does not establish a safe cache key for conversions, mutation,
branch changes, provider options or other tool cases.

## Post-commit work

A further instrumented turn located work after the prepared-request snapshot
was durably committed. Its adapter began offline invocation about 5ms after
the commit. The attempt-usage recorder then took 63.66ms, including a 50.04ms
durable append. The terminal-outcome recorder took 33.00ms, including a
32.85ms durable append. The final Session check took 10.32ms, followed by
prompt completion and the Worked flush. The interval from snapshot commit to
visible Worked was about 207ms in this diagnostic turn. It includes transport
payload projection and model event processing in addition to the named phases.
The extra tracing makes this a stage-location result, not a comparable p95.

The success path therefore has little room for post-commit work under a
250ms end-to-end target. Any prefix-staging design must preserve terminal
attempt usage and model outcome recovery semantics. The current implementation
awaits their append attempts before Worked. Whether Worked must await successful
terminal-observation durability is a separate design choice: ordinary recorder
failures are already traced and swallowed, and recovery classifies a missing
terminal outcome as unknown. Native reopening of
this turn verified both snapshots, terminal usage and its tool output without
executing historical tools or changing the authority.

## Owned prepared envelope

The AI-prepared request now retains the original recursively frozen payload,
headers, canonical JSON and digest as one owned envelope. The committer checks
that these exact fields still belong to that envelope, thaws the immutable
payload once, and uses the already computed canonical identity. A replaced
field follows the existing full-validation path; malformed or changed
payloads are still rejected before any Model Input write. A regression test
forbids a second canonicalization and JSON validation of an untouched envelope,
and four tests cover changes to its payload, headers, canonical string and
digest. Transport projection also rejects a replaced payload or visible header,
so it cannot send a different envelope after the committed snapshot. Transport
now copies the same frozen tree without another JSON validation scan or digest
recalculation. The focused AI/Model Input suites passed with 119 tests and one
skip; `make check-ai` passed with 871 offline tests.

In one 29,193-record native PTY diagnostic, the post-tool prepared-request
validation phase was 13.47ms, compared with 94.79ms in the earlier long-session
trace. These are separate turns, not a matched p95. The same new turn still
took 1,467.38ms from tool exit to Worked; other post-tool phases and scheduling
remain substantial. Native reopening verified its two snapshots, terminal
usage and tool output, with zero historical tool executions and no change to
the original authority. The broader Harness typecheck currently reports six
errors in unrelated sandbox PID-namespace typing; the changed transcript
module passes focused mypy.

One final-code 24,459-record native PTY turn completed and showed one Worked
after 1,046.33ms. Its prepared-request validation took 2.51ms. A 495.55ms
logical-input thaw in that turn is anomalous against earlier turns and needs
separate attribution; this single run cannot establish an end-to-end
improvement. Native reopening again verified both snapshots, terminal usage and
the tool result without executing history or changing the original authority.

## Tool-phase allocation experiment rejected

A later GC-instrumented turn located one 695.61ms main-thread generation-two
collection inside the post-tool binary-externalization phase. That phase took
708.23ms, while the same phase ordinarily took about 9–12ms in this shorter
history. The earlier 29,100-record trace had no post-tool generation-two
collection, so GC is an intermittent tail amplifier rather than the sole cause
of the slow path.

A private candidate made the built-in blob codec share unchanged subtrees of
the committer's exclusively owned logical/prepared JSON. The public default
continued making independent copies, and custom codecs kept the prior call
route. Image, literal-marker, Model Input and static checks passed. Five
alternating real-PTY pairs used the same read-only 24,459-record seed, offline
model transport, a controlled silent command, and a native reopen after every
turn:

| Measure | Baseline `d3190fcd` | Candidate |
| --- | ---: | ---: |
| Tool exit to Worked median | 1,027.36ms | 817.06ms |
| Tool exit to Worked p95 | 1,102.86ms | 1,635.31ms |
| Main-thread generation-two collections, five turns | 4 | 3 |

All ten reports, twenty snapshots with terminal usage and ten outputs rebuilt
successfully; no historical tool ran, drafts and durable-before-send held, and
the seed authority remained unchanged. The candidate's worst turn had a
920.67ms main-thread collection and took 1,781.38ms to Worked. Both variants
still took more than 500ms even in turns without a main-thread generation-two
collection. The candidate was reverted: sharing unchanged blob subtrees did
not control the tail or approach the 250ms objective. No Product GC policy or
threshold was changed.

## Exact prefix-mutation proof feasibility

A private read-only check timed exact comparison of restored historical Agent
messages against a copy. It used type-sensitive recursive equality, then a
restricted byte serialization that accepts only the built-in message, part and
usage dataclasses and ordinary containers. The latter never deserializes the
bytes, does not run custom reducers, rejects unknown object types, and detects
both an altered nested part and a boolean-to-integer change.

| Context | Recursive comparison median | Restricted bytes median | Serialize every message median |
| --- | ---: | ---: | ---: |
| 234 messages, 24,475 records | 14.18ms | 3.91ms | 4.43ms |
| 1,474 messages, 29,193 records | 68.30ms | 22.44ms | 24.69ms |

Seven warm samples formed each median. Both source authorities remained byte-
and mtime-stable, and no historical tool executed. This checks reconstructed
messages; it is not an Agent/Provider integration test or a matched PTY result.
Per-message restricted serialization was 25.77ms in the longer context,
approximately the same as serializing all messages again. An isolated logical-
message cache therefore cannot materially reduce the post-tool path. The
restricted proof is useful only if it authorizes reuse of the larger
normalization, prepared-request and Model Input prefix work.

## Normalization-only prefix reuse rejected

A temporary AI cache reused a normalized message prefix only after checking
the prior raw and normalized messages, unchanged model target and pairing mode,
a closed tool boundary, and disjoint historical/new tool-call IDs. It fell back
to full normalization after nested mutation, an incomplete tool pair, a model
change or a potentially late tool result. Six focused cache regressions and
the existing 59 context tests passed; Ruff and focused mypy passed. The
candidate was then removed without a Product commit.

Real PTY diagnostics on isolated session copies showed why this seam is too
small. On 24,459 records, the cache hit spent 21.46ms checking the prefix and
23.47ms total in normalization; tool exit to Worked was 554.44ms. On a
29,209-record copy with roughly 1,479 messages, the cache hit spent 111.95ms
checking the prefix and 117.19ms total in normalization; Worked arrived after
1,340.09ms. These are diagnostics rather than matched before/after p95s. The
longer run still spent 299.81ms in adapter preparation, 454.64ms in durable
Model Input commit, and roughly 200ms after commit. A cache limited to AI
normalization therefore cannot meet the 250ms end-to-end target and can add
main-thread work to shorter contexts.

A separate native PTY stage trace on the same long-history scale located
PreparedModelRequest construction inside adapter preparation: 194.59ms of a
220.18ms adapter phase. Its projected-payload copy took 44.73ms and metrics
scan took 60.82ms. The subsequent durable commit took 432.06ms, with
216.30ms in v2 materialization; its plan and roots phases took 68.29ms and
84.81ms. The normalizer-only prototype did not reuse any of these stages.
The next candidate must stage or incrementally prove the prepared payload and
Model Input prefix together, then verify the total PTY latency.

## Exact tool-exit-to-Worked allocation

The 1,340.09ms experimental turn above and a fresh 1,099.87ms turn on current
`3881eb56` code used separate isolated copies of the same 29,209-record
history, a real PTY, one silent tool process and offline model transport.
Both were diagnostic single turns, not matched p95 comparisons. The first
column includes the reverted normalization cache; the second does not.

| Interval from actual process exit | Experimental 1.34s turn | Current code 1.10s turn |
| --- | ---: | ---: |
| Result publication and admission until Session preparation starts | 124.71ms | 133.45ms |
| Session model-call preparation | 127.14ms | 146.57ms |
| AI normalization and resolution until adapter preparation starts | 125.65ms | 26.82ms |
| Adapter prepared-request construction | 299.81ms | 198.14ms |
| Adapter end through durable Model Input commit | 455.22ms | 401.03ms |
| Durable commit through first visible Worked frame | 207.57ms | 193.87ms |
| **Total** | **1,340.09ms** | **1,099.87ms** |

Result conversion itself took under 0.2ms in both traces. The first interval
also includes result publication, next-call context work and scheduling; those
substeps need finer instrumentation before assigning their individual costs.
For the current turn, PreparedModelRequest construction used 175.82ms of the
198.14ms adapter interval; its payload projection and metrics pass used
35.53ms and 57.76ms respectively. The 400.52ms commit included 49.59ms of
binary externalization and 206.27ms of v2 materialization, of which plan and
roots used 68.32ms and 81.34ms. The remaining phase-timer difference is not
yet attributed to a single operation. After commit, terminal usage and outcome
appends took 57.56ms and 48.85ms, the final Session check took 14.94ms, and
model return, intervening scheduling and visible rendering filled the rest.

The current-code turn recorded a 686.50ms maximum event-loop delay and
689.76ms maximum input echo latency. Thus the observed freeze is real main-
loop unavailability, not only slow Worked labeling. Native reopening verified
both Model Input snapshots and terminal usage, the one tool-output hash and
truncation state, an unchanged post-run copy during read-only verification,
and zero historical tool calls.

## Canonical prepared-envelope metrics

The prepared-request constructor now obtains message and tool-schema byte
counts from the same canonical encoding used for the full request, avoiding a
second JSON encoding of the historical message list. On the isolated
29,209-record continuation's rebuilt 1,481-item payload, seven alternating
read-only micro samples measured the former canonical-and-size step at 62.51ms
median and the single-encoding step at 38.31ms median. Their canonical bytes
and both size metrics were exactly equal; the source authority bytes and mtime
were unchanged. The focused AI suite passed 41 tests, and `make check-ai`
passed 874 offline tests with 90.63% coverage. These are local stage results,
not a matched real-PTY Worked p95 or evidence of the 250ms target.

## Streaming mapping-root hash

The v2 mapping-root hash now consumes canonical sequence items directly,
without joining the full historical list into an intermediate string. On the
same isolated long-session copy, seven read-only micro samples of the 1,485-item
prepared sequence measured 25.30ms median for the former join-and-hash path
and 10.67ms for streaming, with identical SHA-256 results. One instrumented
real-PTY continuation measured its post-tool root phase at 71.39ms before and
59.56ms after; overall Worked times were 1,281.22ms and 1,401.89ms. These
are different sequential turns, not matched pairs, and the total does not
establish an improvement. Native reopening verified four snapshots with
terminal usage and two outputs, with unchanged authority and zero historical
tool calls. The Model Input and Session model-call suites passed 132 tests.

## Next work

An event-path timing probe on the same long-session scale measured one
post-tool continuation with 111.86ms in the awaited Tool-result append,
approximately 91ms between the following turn start and Session preparation
before the synchronous Session preparer, and 238.29ms in Session
preparation. That preparation included 57.23ms of logical-input serialization,
32.35ms of request-evidence projection, and 143.88ms creating the committer;
the latter included 48.25ms constructing its blob codec. Instrumentation and
turn-to-turn variation make these diagnostic allocations, not comparable p95s.

Subsequent direct timing of the same path attributed a 94.56ms pre-preparer
interval to `prepare_model_input_async`, which cooperatively recovers Resource
evidence. Session-graph preparation was 0.10ms in that turn. The extension
context transformer and its deep copy were not invoked. A separate read-only
micro sample found context-to-model conversion below 2ms for roughly 1,500
messages, so neither transformation explains this interval. This was another
sequential turn, with 1,922.32ms from tool exit to Worked, and is not a matched
before/after comparison.

The asynchronous recovery previously replayed all context message bindings
whenever the appended suffix contained a Model Input snapshot, even when that
snapshot had no Resource evidence component. A regression test first failed on
this unnecessary replay. Recovery now obtains the bindings lazily only after
reading a nonempty Resource evidence component; the final request projection
still checks its exact message-to-record bindings. The evidence-free and
snapshot-evidence tests, Agent Product contract tests, and Coding Model Input
tests passed (70 total). A later sequential, instrumented native-PTY turn on
the same long-session copy measured recovery at 65.44ms versus 94.56ms in the
previous turn, and tool-exit-to-Worked at 1,838.89ms versus 1,922.32ms. These
turns are not matched pairs and establish only the stage attribution, not a
p95 gain. Native reopening verified two snapshots with terminal usage and the
tool output, with original authority unchanged and no historical tool calls.
Ruff and focused mypy passed. `make check-harness` stopped at six mypy errors
in the unchanged sandbox package legacy runtime, before running its test target.

The user requested no transcript replay in the ordinary live tool path. A
second regression test first failed because evidence-free request projection
still requested context bindings despite having no committed or recovered
Resource evidence. Projection now validates selected-path records and hydrates
new evidence first, then skips context binding when both evidence maps are
empty. Evidence-bearing requests retain their exact record-to-message checks.
The existing transcript Unit of Work already caches ordinary append-only
context projection; branch changes and resumed sessions use the checkpoint
aware replay path. One later sequential native-PTY turn on the same long copy
recorded no context-binding call in post-tool Resource evidence projection,
which took 16.18ms; Session preparation took 145.37ms and tool exit to Worked
was 1,682.45ms. This remains diagnostic only. The focused evidence, Agent
Product, and Coding Model Input suites passed 70 tests; native reopening
verified two snapshots with terminal usage and one output without modifying
the original authority or executing historical tools.

A private candidate indexed only record types that might carry blob references
while still rechecking their mutable contents on every sampling. This history
had 7,839 such messages among 29,321 selected records. The candidate reduced
one observed reference-collection interval from 43.66ms to 32.08ms, while
Worked was slower in the separate sequential turn. It was reverted: a 12ms
stage reduction does not justify the extra selected-path cache and mutation
surface while the full target remains far away. The focused Product/session
tests passed, and the original history remained read-only.

An incremental receipt lookup replaced the usage recorder's full active-path
scan. Four focused attempt-usage tests and the combined Model Input/session
model-call suite passed (97 passed, one skipped). One diagnostic native PTY
turn with the change measured 1,135.40ms from tool exit to Worked. The usage
recorder took 97.83ms, of which its durable append took 97.74ms. This isolated
turn is not a matched before/after p95 and does not establish an end-to-end
gain. Native reopening verified its two snapshots with terminal usage and one
tool result without changing the authority or executing historical tools.

Investigate an incremental, provenance-checked prepared-request and transcript
path that can reuse the unchanged historical prefix while preserving the exact
payload, hashes and durable-before-send order. Measure any prototype with five
matched before/after PTY rounds across the required tool cases and history
scales. A faster Worked display before the final model call and terminal
outcome would change the state contract and cannot satisfy this objective.
