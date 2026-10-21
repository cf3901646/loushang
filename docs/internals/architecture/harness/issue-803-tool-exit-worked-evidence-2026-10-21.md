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

## Next work

Investigate an incremental, provenance-checked prepared-request and transcript
path that can reuse the unchanged historical prefix while preserving the exact
payload, hashes and durable-before-send order. Measure any prototype with five
matched before/after PTY rounds across the required tool cases and history
scales. A faster Worked display before the final model call and terminal
outcome would change the state contract and cannot satisfy this objective.
