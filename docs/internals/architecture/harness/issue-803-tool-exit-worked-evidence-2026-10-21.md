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
250ms end-to-end target. Any prefix-staging design must also preserve terminal
attempt usage and model outcome durability. Moving the Worked divider ahead of
those outcomes would violate the completion boundary. Native reopening of
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

## Next work

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
