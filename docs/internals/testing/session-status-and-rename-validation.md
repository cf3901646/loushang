# Session Status And Rename Validation

## Scope

Authority: implementation and validation evidence. Owner: HarnessTUI presentation
and Harness transcript discovery. Date: 2026-10-15.

The status line displays remaining context as `64% left`. Context calculation,
rounding, measurement source and accuracy tokens are unchanged. Unknown usage
remains `ctx ?`; stale and structurally changed usage retain their suffixes.
Detailed usage views retain accuracy information.

The status line prefers a session name and otherwise displays the first eight
characters of its ID. Resume rows also show compact IDs; shared prefixes extend
until distinguishable among loaded rows. Full IDs remain in status/statistics
details, the Coding resume preview and selection targets. Presentation never
rewrites stored IDs, names, resume arguments or full identity references.

## Reproduced Rename Failure

A real persistent session has an original name near the beginning, a rename
between large messages, and an accurate index summary. Another transcript changes
and makes the directory index stale. Opening Resume discards every indexed row
and reads only transcript heads and tails. The rename is outside those segments,
so the original name returns despite the correct durable transcript and summary.
An ensuing bounded index refresh can preserve that partial result across restart.

The regression fails with `Original name` instead of `Renamed session` before the
fix. It exercises persistent SessionManager writes, the directory runtime, Coding
continuity and an actual ContinuitySurface, then repeats queries and constructs
a new runtime to model reopening after exit. It also clears the name and checks
the existing first-message fallback.

## Repair And Review

Discovery now passes validated index entries into bounded projection. An entry
is reused only when its provider, namespace, logical identity, direct-child path
and authority fingerprint match the current candidate. A second stat rejects a
changed candidate. Changed files still use bounded previews; a directory-wide
stale flag cannot downgrade unchanged summaries. Background bounded refresh uses
the same rule, retaining names across restart.

Candidate limits, transcript byte budgets, current-session exclusion and cursor
semantics remain in place. Missing or unusable caches retain existing partial
preview behavior; this change does not turn Resume into an unbounded replay.
No transcript schema, migration, authority ownership or PR gate changes.

Implementer review covers UI identity/selection separation, cache invalidation and
bounded work. Tests check changed and cleared names are never taken from a stale
entry, and unchanged entries avoid transcript body reads. The consulted local
architecture method was clean `master` at
`0f9bd3ff51afabeaaf76cc38dff1ceb279b7d37e`; no method files are vendored.

## Validation

Focused rename, cache invalidation, collision and layout regressions pass on
Linux with Python 3.11. Native macOS and Windows execution is not available in
this workspace. These changes use shared presentation and transcript logic;
this evidence does not claim native validation on those platforms.

Broader offline checks and static validation are recorded at delivery.
