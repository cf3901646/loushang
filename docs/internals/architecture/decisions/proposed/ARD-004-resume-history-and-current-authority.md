# ARD-004: Separate Resume History From Current Execution Authority

## Status

- ID: `ARD-004`
- Scope: Loushang cross-scope Coding, Harness, AppHost, AppService, and HarnessTUI
- Parent: Loushang architecture
- Authority: normative when accepted; this proposal is not yet an accepted Target
- Design status: proposed
- Implementation status: partial — historical composition Header and startup
  receipt decoders are separated from current registry resolution and
  discovered Managed/Hosted candidates have read-only Header and bounded
  transcript previews. Coding Continuity displays the historical Header
  classification in its preview; full UI history opening, large-history paging,
  and activation separation are not implemented
- Owner: Loushang architecture, with the affected scope owners
- Tracking: [Issue #696](https://github.com/zhnt/loushang/issues/696)

## Decision Question And Drivers

When a Coding Session is resumed after an installation, composition, resource,
plugin, tool, or policy change, which historical facts must still match the
current process before the Session can be viewed or continued?

The [R2.1 design](../../../plans/2026-10-12-resume-compatibility-and-activation-design.md)
defines RES-FR-01 through RES-FR-04 and RES-NFR-01 through RES-NFR-05. The
[independent review](../../../plans/2026-10-12-resume-compatibility-and-activation-review.md)
found the candidate ready for an owner decision within its stated scope, not
accepted or runtime-verified. The principal drivers are:

1. Old history remains readable after ordinary environment changes.
2. New operations obey current authorization and execution policy.
3. Read-only inspection cannot acquire a Writer, execute third-party code, start
   a Worker, or write Session authority, activation, or Worker journals.
4. Embedded and Hosted use the same compatibility classification after their
   respective Product identity conditions are met.
5. A history preview cannot silently become an executable branch.

Current code couples these questions. `coding/composition_provenance.py` resolves
the stored set against the current registry and compares its fingerprint.
`coding/session_manager.py` compares stored Runtime and Capability Profiles
with current snapshots for persistent restore. `coding/session/agent_session.py`
compares startup receipt fields with the current composition and refuses
historical input without startup evidence. `coding/managed_catalog.py` uses
current-profile validation to classify a candidate as available. Tests in
`tests/coding/test_plugin_p3_composition_choice.py`,
`tests/coding/test_runtime_profile.py`, and `tests/coding/test_cli.py` encode
these current refusals. This is source evidence, not an accepted future
behavior.

## Options And Comparison

| Option | Fit against drivers | Costs and evidence |
| --- | --- | --- |
| Keep current equality gates | Retains existing writable behavior | An ordinary upgrade or resource change can hide readable history; fails RES-FR-01 and RES-FR-03. |
| Ignore historical evidence and use current defaults | Opens more files | Can guess Product identity, lose explicit user intent, or treat a preview as executable; fails identity and authority constraints. |
| Separate historical decode, compatibility classification, and current execution admission | Opens readable history while keeping new operations under current authority | Requires typed states and a distinct activation/commit contract; [R2.1](../../../plans/2026-10-12-resume-compatibility-and-activation-design.md) describes that subsequent contract and its release gates. |

## Proposed Decision And Exact Scope

Select the third option for ordinary Resume, subject to the affected owners'
acceptance. Historical provenance, receipt, Runtime Profile, and Capability
Profile are immutable audit facts. Decode them using their own versioned shape
and internal references. Current registry entries or snapshot equality cannot
retroactively invalidate those facts. A missing `codingCompositionSetV1` is
classified as `legacy_unknown`; it is not proof of an invalid Conversation
JSONL v1 file or permission to infer a Product.

The read path separately classifies core data readability, Product identity,
historical composition intent, and current continuation capability. It keeps
core schema and decryption checks, read authorization, identity conflict checks,
and bounded parsing. Unknown extension records remain inert. Where Product
identity is proven and the core format is compatible, an Embedded legacy
Session can retain its ID and original Header. A Hosted Session with canonical
Hosted identity can do likewise. A Product-known file without Hosted canonical
identity is a readable migration candidate, not an automatic Hosted adoption.
An unknown or conflicting Product identity is not guessed from a caller's
`product_id` argument.

Read-only opening uses a read-only store and a bounded projection. It does not
repair a partial JSONL tail, enroll a Session, acquire a Writer, import
third-party or workspace Python, run factories or registration, start a Worker,
or write activation and authority journals. Insufficiently verified pages are
marked preview. Selected-path verification is required before execution.

Continuation is a separate admission under the current Product policy,
permissions, approval, sandbox, and tool gateway. Stored receipts and profiles
cannot grant present authority. Explicit historical intent such as composition
set, model, thinking, cwd, or disabled tools is preserved where satisfiable;
otherwise the Product reports a typed unavailable or rebind reason. A current
permission expansion requires a valid confirmation fact from the owning
approval mechanism. A plan, view, or read-only candidate never implies that
the runtime is activated or that input is committed.

This decision alone does not enable a writable current Resume. Writable
activation requires the separate continuation transaction and Hosted admission
decisions, plus their failure and version evidence. Optional exact historical
replay and implicit Embedded-to-Hosted adoption are outside this decision.

## Consequences And Release Boundary

Coding owns compatibility and historical intent. Harness owns read-only
projection and Writer fencing. AppHost retains Product identity and one live
binding. AppService observes a narrow Product status and admission port, not
the Coding plan or Harness internals. Clients display typed read, preparing,
pending, and unavailable states without treating a preview as ready.

A read-only compatibility release can precede writable implementation if it
keeps the old writable gate and proves zero authority effects. Deleting the
current equality checks without replacing execution admission is not a valid
implementation of this decision. Read-only compatibility adds no persisted
record format; writer and rollback version policy belongs to the continuation
transaction decision.

## Validation And Reconsideration

Required evidence includes upgrade and legacy golden fixtures, Product
identity conflicts, corrupted and unsupported core formats, unknown extension
records, read authorization, selected ancestry, and sentinels proving no
third-party import, process start, Writer acquisition, or authority journal
write during view and pure planning. Embedded and Hosted projections must use
the same reason taxonomy within their identity scope.

The existing focused baseline passed 37 tests on 2026-10-12, using
`tests/coding/test_plugin_p3_composition_choice.py`,
`tests/coding/test_ui_resume.py`, and
`tests/harnesstui/conversation/test_resume.py` on `e0878dfa`; it verifies
current behavior only. No R2.1 implementation or fault-injection proof is
claimed. Reconsider this choice if a supported historical schema cannot be
decoded without executing current extension code, or if Product identity
cannot be established independently of a mutable registry.

## Review And Acceptance Record

The R2.1 review covers this proposal's design direction but is not an owner
acceptance of this ARD. Before moving this record to `accepted/`, Coding,
Harness, AppHost, AppService, and the Loushang common-parent owner must record
their accepted scope and any remaining conditions. No acceptance is recorded
here yet.
