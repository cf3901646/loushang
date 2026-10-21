# Tool exit to Worked: focused latency evidence

Status: measured; the current 500ms p95 goal is unmet. The original focused
tool-completion investigation targeted 250ms. Broader experiments are recorded
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

On a later approximately 29,400-record isolated continuation with the
evidence-free replay fixes, a 315.15ms main-thread generation-two collection
fell inside the post-tool prepared-request validation phase (329.5ms). Worked
arrived after 1,350.52ms; maximum loop delay was 329.1ms and keyboard echo
latency reached 562.4ms. Native reopening reconstructed its two snapshots,
terminal usage and output without changing the original authority or invoking
historical tools. A renewed owned-tree copy-on-write micro check did not
contradict the five-pair rejection above: on the same isolated history, median
logical projection was 26.08ms detached versus 26.36ms owned, and prepared
projection was 26.77ms versus 24.56ms. Its Product candidate was reverted after
98 focused tests passed; no copy-on-write Product change remains. The repeat
is diagnostic only and does not justify another latency acceptance claim.

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

Two further private feasibility checks excluded isolated substitutes for that
shared prefix. A request-preparation wrapper executed the offline adapter's
synchronous `prepare_request` in an asyncio worker thread, while retaining the
same capacity and durable-before-send barriers. One later sequential native
PTY turn took 1,358.6ms from tool exit to Worked, with a 323.6ms main-thread
generation-two collection and 503.2ms maximum keyboard echo latency. Native
reopening verified its two snapshots, terminal usage and one output without
altering the original authority. This is not a matched comparison, and the
single turn does not justify a thread-affinity change to all adapters.

On the isolated 1,533-item logical and prepared message arrays, seven warm
read-only samples compared exact prefix proof mechanisms. Type-sensitive
recursive equality took 21.60ms and 21.34ms median; native canonical JSON
encoding and comparison took 28.75ms and 30.05ms; the validated canonical
encoder took 53.87ms and 53.86ms. Replacing only the v2 writer's existing
equality proof with canonicalization would add work. A useful prefix cache must
reuse normalization, adapter payload and Model Input plans as one proven unit.

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

For resume, the latest compaction checkpoint is the context boundary: restore
its summary, the retained records from `first_kept_record_id` up to that
checkpoint, and records after it. Replaying only records after the checkpoint
would omit intentionally retained context. The current replay folder still
reduces state over the whole selected path, because model selection, metadata,
annotations and similar state may originate before compaction. Any resume
optimization needs a separate, validated state checkpoint before it can skip
that reduction. The append-only live path should keep using its incremental
projection; it does not need to replay the transcript on each tool result.

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

## Prepared-request prefix candidate

The Session now offers the last successfully committed prepared request to the
next AI request through its existing committer. AI reuses sealed message items
and their canonical encoding only after a type-sensitive, ordered comparison
of the entire old prefix and all other payload fields and visible headers.
Different nested values, signed floating zero, field order or a shortened
message sequence take the ordinary full-construction path. The new suffix is
validated and frozen before transport; metrics, binary-field locations, hash
and canonical bytes are recomputed for the resulting exact request. The
candidate is retained only after the durable Model Input commit succeeds.

On two isolated snapshots with 1,535 then 1,537 prepared messages, nine
alternating read-only samples measured full construction at 154.35ms median
and prefix construction at 64.07ms median. Canonical payload, hash, metrics,
binary-field locations and copied transport payload matched exactly. A separate
root-hash-only micro sample saved about 23ms across logical and prepared lists;
it was not implemented as a separate cache.

One native-PTY diagnostic pair on same-source long-history copies measured
3,102.55ms baseline and 2,671.32ms candidate from actual tool exit to Worked.
The copied fixtures lacked their writer-head and Model Input index sidecars,
causing cold materialization of about 1.06s and 0.95s in the post-tool commits.
Maximum input echo was worse in the candidate (1,737.58ms versus 1,086.81ms).
Both copies reopened with two exact snapshots and terminal usage, one correct
tool-output fingerprint, unchanged read-only authority and no historical tool
execution. This single noisy pair does not establish a p95 improvement or the
250ms target. The complete AI gate passed 875 offline tests with 90.64%
coverage; the focused Session/Model Input selection passed 104 tests.

Review of the adjacent v2 sequence cache found that its type-sensitive prefix
comparator still treated `-0.0` and `0.0` as equal although their canonical
JSON differs. A regression failed first; the comparator now distinguishes the
two signs so a changed prefix is replanned. The prefix and append tests pass.
This is a correctness guard for later writer reuse, not a latency claim.

Extend the exact prefix proof into the transcript writer and remove other
repeated full-context work while preserving the durable-before-send order.

## Background planning and verified value references

The writer's v2 plan previously compared and reused every historical JSON
message in the TUI event loop, yielding periodically. A regression first
showed that the event loop could not process input while the first items were
being collected. Planning now runs in a background thread over request-local
copies of the cached sequence plans; the writer checks the transcript
revision and leaf again before any write. Cancellation, branch replacement and
concurrent append regressions pass in both warm and cold cache states. The
focused Model Input and Session model-call selection passed 104 tests.

The first four native-PTY matched pairs used the same 29,465-record seed and
ran sequentially, alternating old and new order. A fifth baseline completed,
but the candidate was stopped when the goal was paused; this is not a five-pair
p95 result. The old/new tool-exit-to-Worked times in the four complete pairs
were 2,016/2,096ms, 2,162/2,051ms, 1,850/1,980ms and 2,044/2,058ms.
Threaded planning shortened its own phase from roughly 347–490ms to
152–167ms, but did not establish an end-to-end improvement. Maximum keyboard
echo in those pairs remained about 697–926ms. All nine completed authorities
were reopened read-only and verified: 18 snapshots with terminal usage, nine
tool-output fingerprints and truncation results, unchanged authority and no
historical tool execution. The background-planning change is an intermediate
input-loop responsiveness fix, not acceptance of the Worked target.

A second regression first found 55 value-index lookups after appending one
message to a 50-message request. The writer now retains verified value
references with an ancestry-bound sequence plan. It canonicalizes each
candidate prefix item before reusing a reference, so nested changes,
boolean/integer changes and signed floating zero cannot inherit an old node.
The changed suffix still uses the normal materialization and integrity path.
This reduced the regression's old-value lookups below ten; 138 Model Input,
v2 and Session tests plus 32 file-index/image/thaw tests passed. One bounded
native-PTY candidate reopened with two exact snapshots, terminal usage and
one output; its value-materialization phase was 67ms versus 102ms in the
separate baseline turn. The pair had unrelated phase variance and does not
prove a Worked improvement.

The built-in binary projection copied both full JSON trees even for text-only
requests. The committer now uses the logical canonical encoding it already
needs for the hash to check for declared images, logical image objects and
reserved literal marker keys. Only a plain request with the exact built-in
codec skips projection; custom codecs, images and markers retain the existing
path. A first-failing regression and 99 Model Input/image tests passed. A
bounded native-PTY turn confirmed the binary-externalization phase was absent
and reopened with two snapshots and exact tool output. Its Worked latency was
2,663ms because a 538ms generation-two collection moved into prepared-request
validation. This is a stage reduction, not an end-to-end tail result.

The current long-session critical path remains about two seconds: tool result
append, next call preparation, prepared request construction, multiple v2
graph writes and snapshot append, then usage/outcome/assistant writes and
terminal projection. Meeting 500ms requires shortening that serial chain and
controlling full-history allocations and GC pauses; the current changes alone
do not meet the goal.

## One ordered v2 graph and snapshot append

The writer now builds its missing value, sequence and root bundles in an
isolated index, with final record IDs and ancestry known before persistence.
Batch-capable Stores receive those bundles and the prepared snapshot in one
ordered append; other Stores retain the existing ordered fallback. The shared
index and verified prefix plans advance only after the
durable batch receipt. A staging failure leaves neither graph facts nor
speculative references behind; an acknowledged write with an uncertain
receipt retries the exact operation IDs. Cancellation after the Store accepted
the batch leaves a complete, independently rebuildable snapshot.

The focused Model Input, v2 file index and Session selection passed 141 tests
with one existing skip before adding the unknown-receipt regression. The
long-session native PTY diagnostic used a 29,465-record source, separate
copy-on-write authorities and 20 bounded keyboard samples per run. It measured
4,977ms before and 3,384ms after from tool exit to Worked; the post-tool v2
commit fell from 1,841ms to 1,326ms, with the values and sequence phases
falling from 84/190ms to 20/17ms. The two runs had material phase and GC
variance: the prior run's maximum echo was 2,729ms versus 785ms in the
candidate, while prepared planning remained 635/610ms. This one diagnostic
pair is not a p95 estimate, nor evidence that the 500ms goal is met. The
remaining full-history canonical prefix proof and request/terminal chain
still dominate the path.

## Sealed prepared prefix reuse

The AI `PreparedModelRequest` already seals its payload and, when an append is
verified, carries the exact same frozen message objects into the next request.
The transcript writer now retains those frozen source identities alongside
its ancestry-bound value plans after a durable commit. For an owned request
whose stored payload needs no binary replacement, identity proves the reused
prefix without a second per-item JSON encoding. Any fresh object, unsealed
request or changed item still takes the canonical comparison path. A
first-failing 50-message regression observed 52 redundant canonical prefix
checks; it passes below ten after this change and also proves a later changed
prefix rebuilds to the new content. The 149-test focused Model Input, Session
and thaw selection passed with one existing skip.

An isolated 1,545-message in-memory append measured the second writer plan
at 10.63ms before and 1.54ms after, with 1,547 versus two canonical prefix
checks; the complete second commit measured 18.16ms versus 8.61ms. This
short-message micro sample establishes the eliminated duplicate work, not
the long-session Worked latency. Logical Model Input is frozen separately on
each turn and still needs its own provenance-backed incremental proof.

One sequential long-session native PTY diagnostic against the previous batch
commit used the same 29,465-record source and bounded 20-key input. Tool exit
to Worked was 3,384ms before and 2,850ms after; the post-tool v2 commit was
1,326ms versus 975ms, and its plan phase was 610ms versus 300ms. Maximum
keyboard echo was 785ms versus 691ms. The candidate authority reopened
read-only with two exact snapshots and terminal usage, one exact tool-output
fingerprint, no history tool execution and unchanged file bytes. This one
pair demonstrates the intended plan reduction but cannot establish p95 or
accept the 500ms goal. Session preparation, logical input projection, adapter
construction, residual v2 work and terminal writes still remain serial.

## Logical prefix sealing and deferred plain-text blob setup

Session now retains its previous frozen logical Model Input. At the next
projection it checks each raw prefix item against the frozen value, including
nested shape, strict JSON types and signed zero. Only the exact prefix shares
immutable objects. The writer then recognizes those verified identities and
avoids a second JSON encoding. Branches still rebuild or extend their own
ancestry-bound node index before any reference is reused. An isolated
1,545-message complex-JSON append measured second writer planning at 21.73ms
before and 2.33ms after, with 1,547 versus two redundant canonical prefix
checks; context construction remained about 24ms in both samples. The focused
selection passed 151 tests with one existing skip before the blob setup change.

One native PTY long-session diagnostic against the previous sealed-prepared
commit measured post-tool writer planning at 300ms before and 89ms after, and
v2 commit at 975ms versus 826ms. Tool exit to Worked stayed about 2,850ms in
both runs; maximum keyboard echo was 691ms versus 737ms. Both sessions were
independently reopened with exact snapshots, usage and tool output, without
changing the authority. This is a writer improvement, not a verified Worked
improvement.

For plain persistent requests, Product now gives the committer a deferred
blob-codec factory. The committer determines from the already needed logical
canonical data and sealed prepared binary fields whether an image or reserved
marker needs projection, opening the blob authority only then. A real image
still opens the codec and round-trips exactly. This removes an unnecessary
active-path blob-reference scan from the text-only preparation chain; its
full-path latency impact remains to be measured.

The first same-source 20-key long-session check removed both per-call blob
codec constructions: the post-tool `create_model_input_committer` phase fell
from 221ms to 136ms. Tool exit to Worked nevertheless rose from 2,849ms to
3,361ms; the post-tool v2 root phase varied from 86ms to 286ms and snapshot
append from 159ms to 219ms. Maximum echo was 737ms versus 908ms. The
candidate independently reopened with exact two snapshots, usage and output,
and unchanged authority. This diagnostic establishes the skipped scan, not
an end-to-end improvement; GC and Store variability remain material.

The v2 mapping-root hash now stores a digest state at the end of the committed
messages sequence. When the next plan proves an unchanged prefix and all
preceding fields match, the writer hashes only the suffix and the remaining
fields. Otherwise it hashes the full mapping. A 1,545-message direct sample
measured 1.34ms versus 0.02ms; the focused v2 hash regressions proved exact
hashes for append, changed item and changed preceding field. In one sequential
29,465-record PTY diagnostic, the post-tool root phase was 14ms, compared
with 86ms in the earlier no-cache run and 286ms in the immediately prior
noisy run. Tool exit to Worked measured 2,457ms; maximum echo was 672ms.
The copy reopened read-only with two exact snapshots and terminal usage, one
exact tool-output fingerprint, unchanged authority and no historical tool
execution. This single result does not establish p95 or the 500ms goal.

## Terminal observation batching and lineage checks

AI's terminal provider callback now sends the observed terminal attempt usage
and outcome through one Session operation. The transcript commits them in
that order as one Store batch when the backend supports batches. Legacy
recorders keep their existing two-call contract. The batch retains the same
durable receipt, cancellation settlement and uncertain-receipt retry rules.
Focused regressions cover one ordered batch, exact-once retry, cancellation,
legacy recorders and Session integration. The transcript also keeps a global
set of committed outcome invocation ids, built once on open and advanced only
after a successful local commit. The owning Model Input committer proves the
current snapshot chain using its receipts and the expected revision and leaf;
the terminal batch therefore avoids rescanning the entire active path. A
regression first failed on that scan and now passes. A separate branch/reopen
test proves a prior outcome still blocks a duplicate invocation.

Two sequential 29,465-record PTY diagnostics on the same source gave
tool-exit-to-Worked times of 2,532ms with batching alone and 2,426ms after
removing the redundant terminal lineage scan, versus 2,457ms in the preceding
root-cache run. Maximum keyboard echo was 775ms and 746ms, versus 672ms.
The latter run measured a 124ms terminal batch, 246ms tool-result append and
175ms final assistant-message handling; its post-tool Model Input commit was
761ms. Both candidates independently reopened with exact snapshots, terminal
usage and tool output, without changing the source authority or executing
historical tools. These noisy single samples demonstrate bounded terminal
work but neither a reliable latency reduction nor acceptance of the 500ms
goal. The post-tool preparation and Model Input commit remain the larger
serial costs.

Acceptance still requires five matched before/after PTY rounds across the
required tool cases and history scales. A faster Worked display before the
final model call and terminal outcome would change the state contract and
cannot satisfy this objective.

## Post-tool input and long-history frame work

The post-tool keyboard probe places twenty keys at 40ms intervals starting
when the controlled tool service returns, so it measures input while the
continuation persists and publishes Worked. On one 29,465-record continuation
after terminal batching and lineage changes, tool exit to Worked was 3,682ms,
maximum echo 1,179ms and maximum event-loop delay 723ms. After moving exact
sealed prepared-request validation, logical thaw and canonical encoding to a
worker, a comparable single turn measured 3,259ms, 856ms and 633ms. Both
copies reopened with exact snapshots, terminal usage and tool output. These
samples show responsive input is still at risk and do not estimate p95.

A profiled post-tool turn found that 28 screen refreshes repeatedly traversed
thousands of stable historical render segments. Profiling inflated total work,
so its timings are diagnostic only. The render loop now reuses the unchanged
cacheable segment prefix, cumulative line offsets and a per-frame Kitty image
index. The first changed or uncacheable segment and all later segments remain
subject to normal validation and finalization. A 6,000-segment, changing-editor
micro sample fell from 11.26ms median per frame before these changes to
2.37ms after both. A failed-finalization test, uncacheable-boundary test and
145 TUI/transcript tests passed. The first full PTY sample after both changes
showed 2,909ms to Worked and 580ms maximum echo; its authority reopened
exactly. This one sample does not establish a Worked improvement or the goal.

The transcript unit of work also now prepares detached conversation graph
appends in a worker while retaining its commit lock and existing durable
publication barrier. A deliberately held graph-append test first demonstrated
an event-loop stall, then passed after the change; the selected 75 transcript,
model-input and Session tests passed. In one later long-session PTY sample,
tool exit to Worked was 2,965ms, maximum echo 180ms and maximum loop delay
898ms. The original authority remained unchanged; native reopening verified
the two snapshots with terminal usage and the exact tool output without
running historical tools. The lower echo maximum is promising but is a noisy
single observation, not a responsiveness p95. Worked remains around 3s.

The measured post-tool sequence still waits for the tool-result append
(about 580ms in that turn), Session/model-input preparation and commit
(roughly 1.8s together), terminal observations (96ms), final assistant append
(135ms), and the final flush. Moving graph copies off-loop does not remove
these ordered durability and model-call boundaries. The 500ms end-to-end
acceptance remains open.

## Incremental Store head reuse

An instrumented follow-up separated one tool-result append: the native
FileStore operation took 254ms, including 53ms to decode and validate the
advisory Store head, 41ms to append the authoritative JSONL fact and 76ms to
rewrite the head. The asynchronous append awaited 434ms in all, and the
message route took 526ms. The 2,567ms Worked result is one noisy diagnostic
turn; its copy reopened with exact snapshots, usage and output.

The same FileStore writer now retains its validated head after an accepted
append and checks the journal and sidecar file identities under the existing
exclusive lock before reuse. A changed sidecar falls back to authoritative
replay; another writer's journal update forces a fresh head read. The cache is
bounded to sixteen keys. Three regressions cover a cache hit, sidecar mutation
and a second writer; the selected Store, settlement, Model Input index and
writer lifecycle suites passed with 70 tests and 17 platform skips before the
third regression was added. Ruff and focused mypy passed.

On the same long-session seed, the next single PTY turn skipped head decoding
at the tool-result append. Its native Store operation took 207ms and the
message route 439ms; Worked appeared after 2,478ms versus 2,567ms in the
preceding instrumented run. The head rewrite still took 112ms in this run.
Native reopening again verified both snapshots, terminal usage and output,
with unchanged source authority and no historical tool execution. This
demonstrates the intended skipped read, but the difference is not a matched
p95 estimate and the 500ms target remains unmet.

## Canonical logical-message prefix

The built-in Model Input commit now caches per-message canonical JSON only
after the full logical input has passed its existing validation. A later
context reuses those strings only for the exact frozen message objects that
the context-freeze pass already proved against the previous raw values.
Changed messages, additional components, tools and request options are
encoded from the current context. Custom codec commits keep their previous
full-hash path. A regression first failed for the absent reuse path, then
proved exact canonical bytes for an appended message and a nested mutation;
the focused Model Input, canonical, v2 and Session suites passed with 152 tests
and one existing skip. Ruff and focused mypy passed.

A direct comparison on a rebuilt 1,549-message logical input measured full
canonical encoding at 104.52ms median versus 22.42ms with the proven prefix,
with byte-identical output in seven repetitions. A single full PTY turn on
the same long-session seed still took 3,193ms from tool exit to Worked,
versus 2,478ms in the preceding head-cache turn; the prepared-request phase
also varied from about 250ms to 578ms. The new authority independently
reopened with exact snapshots, usage and tool output and no historical tool
execution. This direct encoding improvement has not produced a measured
end-to-end improvement or met the 500ms goal.

## Follow-up prepared-request allocation, 2026-10-22

The offline PTY probe was split around its own provider payload construction
and transport assertion. On a continuation of the same roughly 29,500-record
history, tool exit to Worked took 3,018ms in one run. The post-tool prepared
request took 291ms: serializing 1,553 messages took 70ms and sealing the
prepared payload took 221ms. The Model Input commit took 610ms, including
91ms prepared-request validation, 54ms logical-input thaw, 100ms incremental
materialization and 124ms snapshot append. The standard transport payload
copy took 90ms; the probe's extra snapshot lookup took only 3ms. The maximum
observed input echo was 185ms, while the maximum loop delay reached 1,264ms.
These are one-run measurements, not p95 values or additive critical-path
totals; phase wall times include scheduling and machine contention.

A separate nine-repetition comparison on 1,549 rebuilt logical messages
found a 61ms median for both recursive exact comparison and a single native
JSON encoding comparison. Replacing the existing mutation proof with JSON
encoding would therefore have no demonstrated material speed benefit and
would need additional strict-type proof. No Product change was made for it.

The run's native reopen verified its two snapshots and terminal usage, the
exact output and unchanged source authority, with zero historical tool
executions. The adapter's full serialization and prepared-request sealing,
ordered Model Input commit, tool-result append and final assistant append
remain on the post-tool critical path. The 500ms acceptance remains open.

## Advisory Store head background publication, 2026-10-22

The persistent transcript Store now returns from an authoritative journal
append without waiting for that append's advisory Store head sidecar rewrite.
A background worker checks the journal identity under its exclusive lock
before publishing the head and refreshes the same writer's bounded head cache.
Another writer's newer journal prevents a stale head publication. Disposal
joins submitted sidecar writes before releasing the rooted IO owner; a missing
or stale sidecar still forces journal replay on a later writer. The Model Input
snapshot and terminal batches retain their existing durable wait points.

A regression first failed because the background mode was absent. The added
tests then showed that a deliberately held sidecar write does not delay the
journal append receipt, a later append reuses the refreshed cache, a stale
background update does not replace another writer's head, and lifecycle
disposal waits for the background worker. The selected Store, transcript
lifecycle and Model Input tests passed: 149 passed, 18 platform skips. Ruff,
focused mypy and `git diff --check` passed.

Two subsequent long-session offline PTY diagnostics on the same growing copy
reported 2,748ms and 2,929ms to Worked. The latter overlapped a short test
run and cannot serve as an uncontended comparison. Its native tool-result
Store append took 126ms without a synchronous sidecar rewrite; the earlier
instrumented turn took 277ms with a synchronous write. The first background
turn still reread a sidecar after an unrelated background update; refreshing
the writer cache fixed that extra read in the second turn. Both runs reopened
with exact Model Input snapshots, terminal usage and tool output, unchanged
source authority and zero historical tool executions. The end-to-end 500ms
target remains unproven and unmet.
