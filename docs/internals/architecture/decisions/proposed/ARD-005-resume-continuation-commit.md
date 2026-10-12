# ARD-005: Commit Resume Binding With The First User Message

## Status

- ID: `ARD-005`
- Scope: Loushang cross-scope Coding and Harness transcript/session owners
- Parent: Loushang architecture
- Authority: normative when accepted; this proposal is not yet an accepted Target
- Design status: proposed
- Implementation status: partial — the original AgentEventRouter can merge
  optional Product message metadata with resource evidence before one append.
  The existing TranscriptCommitter can commit a prebuilt durable UserMessage
  with a fixed record ID, reject conflicting identity or branch, and reconcile
  a lost acknowledgement after an authoritative MemoryStore reload; a JSONL
  partial tail leaves absence unproven. Coding has a bounded internal
  RuntimeBinding v1 metadata codec and pure single-record builder. Selected
  ancestry projection preserves an epoch through compaction, excludes bindings
  copied from a source Session fork, and treats unknown later schema as
  unavailable. Coding also has an internal bounded activation-attempt v1 record
  builder and selected-path validator. The Transcript owner can commit a
  fixed-ID extension fact and reconcile it after an authoritative reload; a
  Coding test helper uses that path for the candidate intent. Selected-path
  projection now marks an unbound intent pending or an unknown version
  unavailable while keeping history viewable. Ordinary Coding bootstrap,
  Product factory selection, model preparation, and message writes reject an
  unresolved current-Session intent before preparing further runtime effects.
  Current activation admission,
  complete recovery, and runtime wiring are not implemented
- Owner: Loushang architecture, Coding continuity, and Harness transcript
- Tracking: [Issue #696](https://github.com/zhnt/loushang/issues/696)

## Decision Question And Drivers

How can a resumed Session record the environment used for its first new user
input without allowing a crash, lost acknowledgement, retry, or old reader to
create an unbound or duplicate input?

The [R2.1 design](../../../plans/2026-10-12-resume-compatibility-and-activation-design.md)
requires the first writable current path to preserve `agent.message` and
`UserMessage`, co-commit RuntimeBinding and resource evidence metadata, and
reconcile an unknown result using durable facts. RES-NFR-03 requires at most
one durable visible record for the same input. RES-FR-04 additionally requires
Embedded and Hosted to share that logical fact. This decision concerns the
durable record and version boundary; it does not grant execution authority.

Current `harness/session/agent_event_router.py` prepares request evidence and
appends the message on `message_end`. `harness/transcript/unit_of_work.py`
uses the record ID as the Store operation ID and can report unknown commit
outcomes. Its batch fallback commits records one by one. These facts establish
useful owners but do not prove atomic visibility of a new multi-record
transaction or durable retry across every backend.

## Options And Comparison

| Option | Fit against drivers | Costs and risks |
| --- | --- | --- |
| Append a Binding record before or after the normal message | Separates schemas | A crash can expose only one fact, and the normal message path can append a second input. |
| Add a new message envelope or rely on batch append | Could package more fields | Old readers may lose message semantics; per-record fallback does not supply group atomicity. |
| Keep the existing message kind and co-commit bounded metadata | Preserves the ordinary message path and one-record visibility | Requires stable identity, metadata merge, partial-tail and old-version tests, plus a separate effect settlement protocol. |

## Proposed Decision And Exact Scope

Select the third option for the first user-message-triggered writable current
Resume. The existing message commit owner constructs one `agent.message`
record carrying the original `UserMessage`, its existing resource evidence,
and a versioned, bounded Coding-owned RuntimeBinding metadata key. Metadata
keys are merged before commit; conflicts fail closed. The same fixed canonical
record ID is used by the Store operation and subsequent response path. No
preliminary Binding append and no second normal message append are permitted.

RuntimeBinding records an activation attempt ID, stable logical input ID,
target ancestry, origin evidence, planned and actual environment fingerprints,
payload digest, and redacted differences. It contains no Credential, Grant,
live Plan, Worker lease, or whole resource graph. It is an historical fact,
not proof that a Runtime was published or that present authorization persists.
Unknown metadata schema is inert and cannot enter model text. Hosted and HTML
projections use an explicit safe allowlist.

The logical input ID is bound to actor, Product, Session, branch, original
leaf, and frozen payload plus metadata digest. Admission after an uncertain
commit first resolves the fixed record and operation ID from the authority
store, including selected ancestry outside current model context. `not
retained`, an obsolete service instance, or an incomplete scan remains
`unknown`, never verified absent. A committed input is never appended again.
Changing the payload after admission requires a confirmed pre-commit cancel
and a new logical ID.

The record's atomic scope is one fully validated physical message. A partial
JSONL tail, fsync/ack uncertainty, and file replacement still need explicit
recovery evidence. Blob staging occurs before the message references an image;
unknown commit protects the Blob from orphan collection until resolved.
Compaction, branch, fork, export, and request-evidence projection retain the
binding as a selected-path historical fact. A cross-Session fork retains its
origin evidence, but establishes neither target activation nor target input
deduplication.

Activation attempt, plugin/Worker effect settlement, message commit, Runtime
publication, and model transport are distinct boundaries. `use FAILED` does
not prove an external effect never occurred. Publish failure after commit
shows “message saved, response not started.” A model attempt with uncertain
external outcome is marked unknown and is not automatically replayed. The
first writable slice does not cover automatic Continue, compaction, or other
effectful commands without a UserMessage.

### Candidate v1 attempt contract for owner review

The proposed `coding.activation-attempt/v1` intent uses one `extension.data`
record. Its fixed record ID equals `attemptId`; its parent is the selected
`originalLeafId`. The exact, bounded data object contains `version: 1`,
`attemptId`, `requestId`, `sessionId`, `originalLeafId`, `ancestryDigest`,
`planFingerprint`, `epochFingerprint`, `subjectDigest`, and sorted redacted
`effectClasses`. The proposed byte ceiling is 4096 bytes. An unknown version
is inert for historical reading and unavailable for writable continuation.

`requestId` is the stable logical input ID. Before the first input is staged,
the continuation owner checks the intent against the selected ancestry and
current Session. The Binding on the single user record must then match the
intent's attempt, request, Plan, epoch, subject, original leaf, and ancestry.
Its actual record parent is the intent record ID. The record contains no
approval grant, mutable lease, resource secret, or assertion that effects
settled. The Transcript owner has a fixed-ID extension commit and same-record
reload reconciliation path. Coding still lacks the admitted activation owner
that would call it and correlate it with effect settlement.

The selected-path read projection reports an unbound current-Session intent as
pending. A matching first UserMessage clears that pending input fact only when
its Binding and parent record agree with the intent. Unknown attempt versions
or malformed known facts keep historical viewing available but make the pure
Plan unavailable. Clearing the pending input fact does not settle plugin,
Worker, Tool, or model effects.

The candidate writer capability name is `coding.resume-continuation/v1`.
Its first shipping build is still undecided. The capability is a release
gate, not a claim that a historical reader or writer implements this path.
The owning scopes must accept this exact schema, unknown-version behavior,
record identity, commit owner, recovery states, and writer boundary before
the proposed route is enabled.

## Version And Rollback Boundary

The first release must identify a concrete minimum writer build or protocol
capability that understands RuntimeBinding and its continuation gate. Existing
`pyproject.toml` uses `0.1.0`, so that package version alone is insufficient
to name the boundary. The exact build/capability identifier remains a release
decision, not an assumed value in this proposal.

A 2026-10-12 local probe used `main` at `e0878dfa` as the old reader/writer
and an `agent.message` carrying a small unknown `coding.runtimeBindingV1`
metadata object. The old reader decoded the `UserMessage` and an export
preserved the unknown metadata. A copy opened by the old writer accepted a
new `UserMessage` without that metadata. This establishes why old-writer
rollback cannot be treated as safe. It does **not** verify the final Binding
schema, released N/N+1 artifacts, compaction, Blob references, or crash
recovery; those remain release gates.

A second local probe on 2026-10-12 used `main` at `29ff1c45` to read and export
a UserMessage with the current internal RuntimeBinding v1 shape and Resource
evidence metadata. The old reader displayed the message and retained both
metadata keys in the export; the new decoder validated that exported binding.
This is local source-version evidence only, not an N/N+1 released-artifact gate.

N and N+1 reader/export tests must demonstrate that a known `agent.message`
still displays or exports appropriately with the new metadata. An old writer
may ignore it; therefore this proposal does not claim safe downgrade writing.
The product must document unsupported rollback write recovery unless a tested
old-binary-readable fence is separately accepted. A reader/export claim is
not a writer claim.

## Consequences, Validation, And Acceptance

Coding owns the Binding schema and continuation decision. The existing
Harness transcript message owner owns record creation, commit outcome, Blob
reference safety, selected ancestry, and export. Effect owners retain their
own durable effect/settlement journals. AppService consumes only a narrow
stable-ID lookup and admission result; it does not become a transcript writer.

Required evidence includes deterministic failure injection at intent,
effect, Blob, commit, publish, and model-start boundaries; JSONL partial-tail
and fsync/ack loss; fixed-ID restart reconciliation; two Writers; selected
ancestry and compaction; fork origin; old reader/export; and explicit old
writer behavior. The [R2.1 review](../../../plans/2026-10-12-resume-compatibility-and-activation-review.md)
identifies message/Blob/restart proof as open investigation. No implementation
or version compatibility is claimed yet.

Coding, Harness transcript, and their common-parent owner must record the
accepted schema, commit owner, recovery states, and minimum writer capability
before this record becomes accepted. The reviewed design is evidence for a
decision, not the acceptance record itself.
