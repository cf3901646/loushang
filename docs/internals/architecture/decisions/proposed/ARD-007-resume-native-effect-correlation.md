# ARD-007: Correlate Resume Effects In Their Original Journals

## Status

- ID: ARD-007
- Scope: Loushang
- Authority: normative — candidate cross-scope contract
- Design status: proposed
- Implementation status: not-started
- Owner: Loushang architecture, Coding, Harness Approval and native Worker owners
- Tracking: [Issue #696](https://github.com/zhnt/loushang/issues/696)
- Source review: `e072a764`, 2026-10-12

This proposal refines the external-effect prerequisite in
[ARD-005](../accepted/ARD-005-resume-continuation-commit.md). It does not replace
its accepted message commit or writer capability contract. No acceptance or
implemented settlement protocol is claimed here.

## Question And Current Evidence

How does a resumed input find every original activation effect after a crash,
without treating a new candidate's successful activation as settlement of an
older attempt?

The [R2.1 plan](../../../plans/2026-10-12-resume-compatibility-and-activation-design.md)
requires crash recovery, one durable input and current admission. Current
source establishes these boundaries:

- Coding commits `coding.activation-attempt/v1` before preparing a Session.
  Its `effectClasses` are class names, not native operation identities.
- `harness/approval/plugin_execution.py` owns Definition execution decisions,
  consumed uses and transitions. A started use can become
  `FAILED_AFTER_START`; that state does not prove absence of external effects.
- `harness/approval/plugin_activation.py` owns component activation decisions
  and uses. A different host boot recovers started uses to `FAILED`, and
  unstarted uses to `CANCELLED_BEFORE_START`.
- `coding/_capability_plugin_composition.py` constructs those existing
  journals and original Hosts. Persistent approval state is selected through
  Product composition; ephemeral state is cleaned by its retained custodian.
- `harness/worker/product_activation.py` and the existing Product C5 state
  own Worker attempts and exact containment/cleanup settlement. Their native
  attempt identities cannot be replaced by a Transcript input identity.
- Coding's original Session checks live published components. That check
  does not correlate a prior Resume intent with native effects. The production
  coordinator still requires an externally supplied settlement callback.

Therefore current guards are necessary but insufficient for default Resume.
The missing association is a data contract between existing owners, rather
than permission to create another effect ledger.

## Options

| Option | Recovery properties | Cost and limitation |
| --- | --- | --- |
| Infer settlement from a new graph's receipt or COMMITTED state | Finds only the new live activation | Cannot resolve older started uses or arbitrary external effects; rejected. |
| Copy native states into a Coding Saga journal | Gives Coding a convenient index | Creates another effect authority and a cross-journal acknowledgement gap; rejected. |
| Attach bounded parent operation context to each original native use | Recovery reads original owner facts and preserves authority | Requires native journal version gates, complete effect enumeration and owner-specific reconciliation; recommended. |

A deterministic ID factory alone is insufficient: a sequence number does not
prove complete enumeration, and regenerating IDs after different preparation
orders cannot establish which effects started. IDs may aid lookup, but their
original owner must persist the exact causal association.

## Recommended Contract

### Parent context and native registration

Coding supplies inert parent context from the committed attempt: Product and
Session identity, `attemptId`, request identity and a digest of the exact
committed intent. Owners validate scope before accepting it. Context contains
no path, Credential, policy grant, permission confirmation or live object.
It is never a substitute for the native owner subject and admission.

The original Definition, component or Worker owner attaches that context to
its native use/attempt in the same durable owner transaction that consumes or
reserves the operation. Registration is acknowledged before import, evaluation,
process creation or other native start. Keep the native decision/use ID,
subject digest, instance revision and boot/domain identity. Repeated parent
context does not authorize a second use and does not deduplicate arbitrary
operations by itself.

Each owner must enumerate its registered operations completely for that parent,
including failed, cancelled and replaced candidates. The coordinator records
which original owners must participate before their effects can start; an
omitted owner, missing registration acknowledgement, incomplete scan, lost
journal or unsupported schema yields unknown. Absence in a partial view is
never verified not started. Registration failures preserve the Transcript
intent and native evidence for explicit reconciliation.

### Reconciliation and disposition

Original owners return outcomes for exact native operations, checked against
the parent context and their current authority:

| Outcome | Required original-owner evidence | Resume consequence |
| --- | --- | --- |
| Verified not started | The durable native state proves no start boundary was crossed, including native reservation/containment edges | The coordinator may request fresh admission; the observation itself grants no retry. |
| Completed | The domain owner proves completion of its declared effect contract | May satisfy that effect obligation, with current candidate and caller checks still required. |
| Disposed | The domain owner proves the exact cleanup/compensation or records an authorized explicit disposition | May satisfy only the obligations covered by that disposition. |
| Unknown | Started failure, missing or conflicting facts, unsupported version, incomplete cleanup or an unregistered effect | Keep input pending or enter recovery-required; no automatic re-execution. |

`EVALUATED` and `COMMITTED` establish their native execution/publication
boundaries. They do not settle unrelated filesystem, network, process or
publication effects produced by arbitrary Plugin code. A domain that can
produce such effects must declare its effect owner and provide original-owner
reconciliation. Unsupported domains remain unavailable for writable Resume
until that obligation is resolved. Human confirmation is current admission;
it does not retrospectively prove completion or absence.

An explicit disposition must identify the exact native operations, uncovered
obligations, current authorized actor and policy revision. Its original domain
owner persists it; Coding and UI cannot manufacture it from a checkbox or a
receipt. This proposal does not introduce a generic force-retry flag.

### Coordination and lifetime

The existing Coding continuation coordinates the original owners after the
Transcript intent commit and before first-input commit. It validates current
admission before each owner operation and again after callbacks. It revalidates
current content, Product epoch and live component publication before input
commit, Runtime publication and model transport.

The original Session/graph still owns live components; the Product application
selection owns its epoch; the original Worker coordinator owns containment.
No second Root, live-session registry, authority issuer or cleanup owner is
introduced. Failed preparations retain their existing custodians until native
settlement succeeds. Durable effect evidence must outlive disposable import
or private-data state while reconciliation remains unresolved.

History and background planning never consume decisions, register native uses,
repair journals, settle effects or issue grants. They may show redacted
unavailability, but formal reconciliation belongs to admitted activation.
Embedded and Hosted use this same coordinator; Hosted additionally retains
its existing subject/controller generation and single Product binding.

## Version And Release Boundary

Use versioned native owner events for the additional causal context and
settlement/disposition data. Keep legacy decoding explicit. A legacy use
without a complete parent association cannot supply verified absence or full
settlement for a Resume intent.

Before the first such event is written, each affected original journal writer
must enforce its new minimum writer capability. Old binaries must refuse
mutation of those journals before repair or append. Changing native journal
schemas does not imply that `coding.resume-continuation/v1` covers this owner
capability. Name the concrete native capabilities and first shipping builds
in the implementation/release evidence; they are not established by this
proposal. Do not claim safe writer rollback from reader/export compatibility.

## Review And Acceptance Gates

The implementation-session source review identified a specific unresolved
association between Transcript intent and original native operations. This is
an author review, not independent review or acceptance. The proposal belongs
to the common parent of Coding and Harness. The project governance profile
requires owner acceptance of this exact contract; it creates no blanket
customer-confirmation requirement.

Before acceptance, resolve these material findings:

1. Specify complete participating-owner enumeration, including effects started
   during Definition evaluation before a component graph exists.
2. Specify atomic native registration and exact outcome semantics separately
   for Definition, in-process component and native Worker owners.
3. Identify original disposition authority and supported domain reconcilers;
   a generic callback returning None is insufficient production evidence.
4. Specify native event versions, old-writer refusal before repair, retention
   and first-shipping capability identities.

Required implementation evidence includes crash/ack loss at intent,
registration, start, completion, input commit and publication; recovery under
another boot; partial native journal tails; multiple native uses under one
attempt; changed caller/policy/content; journal loss; unknown external effects;
failed compensation; native Worker containment settlement; and old/new installed
reader and writer artifacts. Tests must use actual owner journals and retain
unknown results. A green callback fixture is not acceptance evidence.

The [accepted governance profile](../../governance-profile.md#target-acceptance-in-loushang)
and [decision catalog](../README.md) govern promotion. Until acceptance and
implementation evidence, default writable Resume and the full Issue remain
incomplete. Independent quality gates and existing accepted work may continue.
