# Resume Compatibility And Background Activation Design

## Status

- Hosted history binding: explicit catalog `open_history_binding` and
  `open_history_candidate` entries now
  deliver bounded selected-branch history through the existing Hosted adapter
  without a Writer, Product factory or executable control. This does not yet
  replace the default AppHost resume path or activate on first input.
- Authority: descriptive — implementation design and delivery plan; accepted cross-scope contracts are normative in ARD-004/005/006.
- Design status: proposed — ARD-004/005/006 boundaries were accepted by the project owner on 2026-10-12; further implementation detail and release evidence remain distinct.
- Implementation status: partial — read-only Header, bounded selected-path and
  unverified tail previews, exact-byte digest for bounded historical snapshots,
  historical Binding projection, fixed-ID UserMessage commit primitives with
  image externalization inside the existing Transcript owner, composition
  comparison, an internal fixed-ID activation-attempt record and Transcript
  commit path, a staged first-input path in Coding's SessionManager, and a
  data-only internal `SessionActivationPlanV1` envelope exist. Selected-path
  history projection classifies an unbound attempt as pending and keeps its
  pure Plan unavailable while still allowing read-only viewing. The ordinary
  persistent bootstrap, Product factory selection, model preparation, and
  message write paths also stop at an unresolved attempt; a normal
  commit advances its checked transcript revision without rescanning history.
  The original Transcript committer also offers a read-only fixed-record
  lookup under the Product operation fence. It reloads the authority store,
  compares the frozen payload and full metadata, and reports committed,
  not_committed_verified, unknown, or conflict without appending or moving the
  leaf. Verified absence requires complete evidence and an unchanged target;
  an unavailable store, partial tail, or uncertain receipt remains unknown.
  This lookup uses a full authority reload and is not yet the Hosted logical-ID
  or model-outcome facade. The staged Coding first-input path now retains a
  detached copy of its prepared persisted record and exposes an internal
  request-ID checked observation through that original lookup owner. A lost
  append acknowledgement can be observed as committed without replay;
  incomplete tail or unavailable authority remains unknown. The observation
  does not clear the activation fence, authorize retry, or start a model call.
  Before record preparation there is no invented fixed-record observation.
  An internal logical-input lookup query now contains only the stable input ID
  and a digest of the exact prepared record. The original Transcript codec
  covers payload, full metadata, timestamp, record identity and branch parent.
  Coding resolves the matching current-Session Binding in selected ancestry
  (outside truncated model context) or its retained prepared input, then calls
  the original authority lookup. Duplicate selected IDs or digest mismatch are
  conflict; missing local evidence is unknown, never verified absence. A
  provisional 65536-record local scan ceiling also returns unknown. The real
  Hosted binding forwards this observation without replacing control identity,
  and rejects lookup once close begins. Callers still need current read
  authorization. SessionManager reload tests cover committed identity with no local
  submission ledger and partial-tail uncertainty. Deployment capability selection
  and model-attempt observation remain pending. An optional
  Product-neutral AppService observation port now accepts bounded input IDs and
  record digests and returns validated durability states. Coding's Hosted
  adapter converts this port to the native query without exposing Plans or
  Transcript records. The existing scoped AppService client validates current
  attachment, member and controller generation before Product lookup and again
  before delivery. Foreign scopes are rejected before the Product read; controller
  takeover discards an old scope's late result. Unsupported Product ports return
  operation unavailable, not absence. Invalid or mismatched results and private
  Product failures become Session unavailable. This read does not reserve an
  execution or change old Ack timing; current scope authority is the existing
  snapshot-read capability, not a new persistent permission grant. AppServer
  now carries the closed observation query/result over the existing framed
  execution channel under the explicitly selected
  `local-detachable-resume-execution/v1` profile. AppService and transport share
  the same bounded data values; AppServer imports no Coding or Transcript owner.
  Remote clients expose a separate borrowed lookup capability only after that
  exact profile is negotiated. Old profiles reject the new operation even when
  a peer manually encodes it; old frame goldens and operations remain unchanged.
  The query uses existing request IDs and bounded control communication slots,
  checks the current service instance, and grants no execution/retry authority.
  Local connection records now publish this explicitly enabled capability in
  their authenticated capability list, with closed profiles preserving the six
  existing execution/discovery/managed/close combinations. Local clients borrow
  the same negotiated lookup client only while connected. Authenticated loopback
  tests cover enabled and default-disabled publication; framed queries cover all
  six optional profiles without creating executions. Installed deployments have
  not enabled this capability; client reconnection/editor integration,
  actor-policy read revocation and the
  full Hosted Resume readiness/admission flow remain pending.
  The application-owned SessionManager also has an internal isolated Resume
  Writer preparation route. It rechecks bounded source evidence and owner input
  references, rebuilds the canonical Plan, retains historical Header validation
  without current-profile equality, and delegates exclusive acquisition to the
  original Transcript factory. Before delivery it closes execution readiness,
  compares all loaded records, selects the verified leaf through the original
  Transcript's local branch operation, and compares the complete selected path.
  Store restore's default last-record leaf cannot replace the Plan selection.
  A branch change after preparation rejects intent commit without changing
  existing bytes; the initial intent's parent remains the verified selected leaf.
  Changed history disposes the original undelivered preparation. JSONL tests
  prove same-ID legacy preparation with unchanged Header bytes, a changed
  capability profile, competing Writer rejection, an acquisition-time source
  change, and intent plus one co-committed UserMessage/Binding. The prepared
  Plan pins the initial intent's Session, leaf and ancestry and is consumed
  before commit. Matching these data facts grants no execution permission.
  This internal route is not yet called by Embedded/Hosted Product bootstrap;
  live policy/owner admission, effects and production Runtime publication remain pending.
  The internal SessionManager initial-intent route now validates current
  Session, selected leaf and ancestry, freezes the canonical intent, and closes
  the local Runtime publication gate before its first await into the original
  fixed-ID Transcript commit owner. Success, write failure, lost acknowledgement
  and caller cancellation cannot reopen that gate. This route still requires
  the activation coordinator's live admission; it is not a retry/recovery port
  and is not yet wired into ordinary Product bootstrap. Staging also closes
  the same distinct local Runtime publication gate. That gate
  remains closed after successful input/Binding commit, including when the
  historical attempt projection becomes settled and a historical guard result
  is cached. Ordinary message writes, startup readiness and Coding model-runtime
  preparation cannot treat input durability as Runtime publication. The current
  Coding shell pre-execution hook, extension exec entry and explicit compaction
  entry check the same guard before invoking their downstream owners. Coding's
  execution-availability observation also remains false while local publication
  is pending, so the existing Hosted execution entry rejects dispatch. These
  checks do not implement Hosted readiness or continuation admission. The current
  production activation coordinator is not implemented. The internal publication
  boundary below is not a durable publication receipt or crash-recovery authority.
  Coding AgentSession now builds detached current composition observations in
  a separate internal receipt builder. Ordinary startup calls that builder and
  retains its existing historical Header/startup equality checks. The builder
  reads current Plugin revisions, Product policy revision, Catalog selection,
  Worker receipt and owner generation references without reading or appending
  transcript history or enabling execution. A sentinel verifies this with the
  local Resume gate closed, including caller mutation of a returned receipt.
  This is a data seam for the upcoming activation coordinator, not live owner
  admission, effect settlement or Runtime publication.
  Harness AgentProductSession now exposes an internal candidate graph preparation
  path with an explicit synchronous current-admission check. Ordinary graph
  preparation delegates to it using the existing execution-readiness check.
  The candidate path retains original component/owner authority gates, graph
  binding and rollback; it rechecks admission after lock acquisition, around
  graph binding, before Worker preparation and before consumer delivery. It
  rejects a failed execution preparation and checks admission even for a cached
  graph. Tests keep Product execution unavailable while preparing a candidate,
  revoke admission during lock/bind waits and verify original owner disposal.
  This shared owner seam does not implement Coding's live admission decision,
  input/effect settlement or the final Runtime publication gate; the Coding
  activation coordinator and its production call sites remain pending.
  Coding now has an internal candidate preparation entry tied to a locally
  verified, definitely committed intent and the original exclusive Writer.
  It passes the checked immutable attempt to a synchronous current-admission
  callback, rechecks original current Product selections, and calls the same
  Harness graph owner. Each admission borrows a short synchronous Writer scope;
  no Writer operation spans graph awaits, because graph rollback may retire
  that same Writer. A preparation failure after owner claims fences retry on
  that Session. Preparation returns current composition observations without
  appending startup history, activating the Worker turn Tool or reopening the
  execution gate. Unknown acknowledgements and historical intent alone do not
  establish local preparation admission. This is not yet the production Resume
  coordinator: production bootstrap wiring, native effect correlation, current
  grants and production Runtime publication remain pending.
  An internal asynchronous Coding bootstrap now constructs a current candidate
  from that same owned resumed Writer after definite intent commit. The Writer
  retains its verified Plan locally; bootstrap matches the canonical current
  composition to the Plan and gives its immutable attempt to current admission
  before Product selection, before construction and before delivery. The
  explicit internal context selects the current composition without sealing or
  changing the original Header. Public ordinary bootstrap retains its pending
  activation rejection and historical composition pinning. A candidate denied
  after construction is disposed through the original Session owner before the
  error returns. This route neither settles native effects nor publishes
  execution readiness, and Embedded/Hosted production callers are still pending.
  The internal Coding publication boundary now retains a definitely committed
  first-input record and its full digest separately from intent and candidate
  preparation. Publication requires that same selected input and canonical
  intent, an original Transcript lookup reporting the exact committed record,
  and the locally prepared consumer, graph generation and composition receipt.
  The coordinator must supply both current admission and current epoch/effect
  settlement checks; neither historical Binding nor local preparation substitutes
  for them. Admission runs before the lookup await and both checks run before
  final synchronous publication. Only then does the boundary activate the
  original Worker turn Tool lease and reopen the local gate. Failure during
  final publication retires execution preparation. A published local Resume
  uses these current checks for subsequent model-runtime preparation, shell,
  extension exec and explicit compaction admission, retaining the first Binding
  on its selected ancestry and avoiding old startup equality and startup writes.
  The boundary dispatches no model request and supplies no
  automatic replay or crash-recovery grant. Live policy/epoch settlement owners,
  Worker Resume fault coverage and production continuation callers remain pending.
  A published local Coding candidate can now consume its committed first input
  through an internal once-only dispatch entry. The original Host claims the
  run before Coding installs the selected transcript context; queued inputs,
  a changed leaf, retry activity or revoked admission reject dispatch. The
  original Agent continuation runs that already committed UserMessage with
  purpose `main`, producing no second user append. The standard AI prepared
  transport and original durable Model Input snapshot owner remain installed.
  Coding's current-Session predicate rechecks publication admission at the
  original transport commit barrier, including after snapshot commit.
  A run-local Harness recovery predicate suppresses automatic retry/compaction
  for this explicit committed-input run, and the Agent's temporary CallOptions
  permits one AI transport attempt. Both return to their previous values on
  exit; persistent settings are not changed. A claimed run is not replayed;
  error, abort or cancellation fences this Session's execution preparation.
  This local claim is not a durable model-outcome registry. Production
  continuation coordinators, restart/outcome lookup, full native permission
  settlement and Embedded/Hosted submit wiring remain pending.
  ResourceLoader
  can calculate Catalog input facts and bounded native context content digests
  without choosing authority; Plan records only their redacted input fingerprint and
  rejects reuse when refreshed owner inputs differ. The synchronous
  `plan_coding_resume` entry reuses displayed history and calls this original
  Resource owner; unavailable history skips resource scanning. The internal
  `plan_coding_resume_async` entry builds the same envelope through bounded
  Resource-owned work and additionally records caller-observed subject and
  policy input digests. These digests identify dependencies, not permissions;
  refreshed domain inputs invalidate a stale Plan. Catalog Session views
  delegate computation to their shared source owner and retain bounded local
  waiting Tasks. Closing a view fences new waits and cancels its references;
  asynchronous close joins their release without waiting for native work.
  Closing one view leaves peer computations available. The shared Resource
  owner still joins native completion before releasing its own source leases.
  The original AgentProductSession disposal path now joins local reference
  release before retiring capability owners, without closing peer views or
  the shared source loader. A real Coding Session disposal regression covers
  two concurrent Session references. Production Resume startup and shared-owner
  close wiring remain pending.
  Skill and other mutable
  Resource content is not closed by this receipt, which cannot replace current
  owner selection. The staged first-input path is not yet armed by live Resume
  activation. Writable admission, owner selection
  completion, Product background wiring, Hosted readiness, and release evidence
  are not implemented.
- Planning cancellation: the shared Plan entry and original ResourceLoader
  preview accept a cooperative work probe. Checkpoints cover phase boundaries,
  context candidates, package/revision directory enumeration and Skill recursion,
  and 64 KiB context-file, package-text, and revision-digest reads. Package text
  capture uses the original mount/revision owner, preserves ordinary newline
  semantics, and limits raw bytes to 8 MiB total across mounts. Budget exhaustion
  discards the speculative receipt with `resource.preview_byte_budget_exceeded`;
  ordinary on-demand preparation still uses its existing owner path.
  Descriptor and portable
  revision verification preserve cancellation rather than reporting changed
  content; temporary descriptors close and the original handle remains owned.
  Directory cancellation occurs before collecting
  and sorting all candidates. Cancellation discards the
  result without selecting authority and permits re-planning. Work-unit/time
  budgets are explicit caller inputs to an internal Resource-owned background
  entry. This entry shares one computation for identical input state, workspace,
  subject and policy across matching ResourceLoaders on one event loop; separate
  domains do not share. Captured Resource input state and work budgets must also
  match; distinct live revision handles are conservatively separate.
  The process limits admitted jobs to eight, background jobs to six so two
  admission slots remain for foreground preparation, and native workers to two, with
  at most 64 references per job. These provisional bounds are not release
  performance evidence. Cancellation releases one waiter reference; only the
  last reference cancels computation. Original revision owners supply temporary
  read pins without an eager scan, then verify them during native computation.
  Pin cleanup runs before a successful native completion receipt. `aclose` joins native
  completion even when its caller is cancelled; synchronous close reports
  pending settlement while work remains. A publication gate prevents source
  reads when native submission loses its receipt and fences further background
  submission; the ordinary on-demand path remains available. Only a redacted
  fingerprint leaves the Resource owner. Catalog Session views now own their
  local waiting references. Foreground requests promote queued shared work,
  and cancelled work is promoted for cleanup. Product Resume invocation,
  completed-value caches, broader Workspace deduplication across distinct
  revision handles, and production close wiring remain unimplemented.
- Revision: R2.1, 2026-10-12; R2 independently rechecked, with the requested
  legacy Ack timing and fork-origin clarifications applied.
- Owning scope: Coding Session continuity; collaborating scopes: Harness,
  AppHost, AppService, AppServer, HarnessTUI.
- Source baseline: `5c148849`; source links describe this baseline, not implemented changes.
- Method: existing local `archmethod/method/`, revision
  `5b31521605ce12e20134de74fa3877b5717127e4`, read without upstream checks.
- Review: three independent GPT-6 Astra perspectives; results are recorded in
  [the review record](2026-10-12-resume-compatibility-and-activation-review.md).

普通 Resume 应恢复历史会话，并允许后续操作使用当前安装、资源和执行策略。
升级包、修改 AGENTS、更新插件或调整权限不应使历史会话无法打开。
历史首先可读展示；显示期间并行准备当前环境的纯数据计划。用户继续操作时，
取得写入所有权、验证计划并激活运行环境，随后持久化输入和环境绑定。

该候选采用 Fast Open、Background Plan、Owned Activation、Continuation Commit
四阶段。只新增一个核心纯数据计划类型，复用现有规划、准备、绑定和释放机制。
Embedded CLI/TUI 与 LMUX/AppService 使用同一恢复语义和 Product 执行入口。

## Problem And Current Evidence

目前存在三组普通恢复门禁：

| 当前机制 | 证据 | 恢复影响 |
| --- | --- | --- |
| Header 和 startup receipt 使用当前 composition 定义反验历史指纹 | [composition_provenance.py](../../../src/loushang/coding/composition_provenance.py) | 同名 composition 更新后，历史证据也可能无法解码 |
| 启动凭证要求资源、插件、策略和 Worker 等字段相等 | [agent_session.py](../../../src/loushang/coding/session/agent_session.py) | AGENTS、Skill、插件变化可阻断普通 Resume |
| Runtime 与 Capability Profile 要求与当前快照相等 | [session_manager.py](../../../src/loushang/coding/session_manager.py)、[runtime_profile.py](../../../src/loushang/harness/transcript/runtime_profile.py) | 只放宽资源哈希仍不能解决跨安装恢复 |

缺少 `codingCompositionSetV1` 的会话可能仍是可解析的 Conversation JSONL v1；
缺少产品 provenance 不等于核心格式不可迁移。现有拒绝行为由
[test_plugin_p3_composition_choice.py](../../../tests/coding/test_plugin_p3_composition_choice.py)
和 [test_cli.py](../../../tests/coding/test_cli.py) 固化，修复需调整行为契约及测试。

当前若干 `prepare` 已取得资源所有权或产生效果，不能直接作为后台计划入口：

| 当前抽象 | 已有责任 | 拟复用位置 |
| --- | --- | --- |
| Prepared Transcript restore | 获取 Writer、加载 transcript、持有生命周期资源 | 用户正式继续时；[writer_lifecycle.py](../../../src/loushang/harness/transcript/writer_lifecycle.py) |
| Prepared Product route | Product admission、candidate claim、validate、资源关闭 | Hosted 正式激活；[router.py](../../../src/loushang/apphost/router.py) |
| Capability prepare/bind | activation decision、component factory 和绑定 | 所有权阶段；[component_host.py](../../../src/loushang/harness/capabilities/component_host.py) |
| Extension prepare generation | 可执行模块顶层、register、factory | 正式插件激活；[loader.py](../../../src/loushang/harness/extensions/loader.py)、[runner.py](../../../src/loushang/harness/extensions/runner.py) |
| Worker prepare | 可物化 payload、写 launch intent、启动进程 | 正式 Worker 激活；[agent_product.py](../../../src/loushang/harness/session/agent_product.py) |

现有 batch substrate 有 CAS、稳定 operation ID 和 unknown-outcome 重试能力，
但不是所有 backend 都具备崩溃后完整组可见性；逐条 fallback 和 JSONL 部分追加
不能作为新逻辑事务的原子保证。见
[unit_of_work.py](../../../src/loushang/harness/transcript/unit_of_work.py)、
[jsonl.py](../../../src/loushang/harness/journal/jsonl.py)。

[Resume Request Evidence Recovery](2026-09-28-resume-request-evidence-recovery.md)
已规定正常恢复从所选路径的消息锚点恢复证据。该约定继续有效：历史已加载 Skill
的文本与摘要保持历史事实；新轮次环境资源采用当前内容，两者不能相互覆盖。

## Outcomes And Quality Scenarios

下表是本候选的可追踪验收条款。用户明确提出恢复兼容、显示期间准备、性能优化、
LMUX 支持以及避免 prepare 重复；故障与一致性条款是相应的工程约束。
业务重要性为设计排序建议，数值延迟预算需基线测量后确认。

| ID | 场景与结果 | 验收与责任 |
| --- | --- | --- |
| RES-FR-01 | 包升级、AGENTS/Skill/插件/工具/策略变化后恢复旧会话 | 历史可打开；后续使用当前安全环境；Coding |
| RES-FR-02 | 历史显示期间准备当前环境，用户立即输入 | 输入立即成为明确未发送的 pending；准备不阻塞历史首屏；Coding/HarnessTUI |
| RES-FR-03 | Legacy 会话缺 composition provenance | 身份可证明且核心格式兼容时同 ID 延续，Header 不变，来源永久标记 legacy_unknown；Coding |
| RES-FR-04 | Embedded 与 LMUX 使用相同会话 | 相同兼容分类、输入状态、reason code 与执行门禁；Hosted adapter |
| RES-NFR-01 | 用户只查看后退出 | Session authority 与 activation/Worker journals 零写入；无第三方 import、无进程启动；Harness |
| RES-NFR-02 | 准备期间配置/路径/插件/策略变化或两个进程争写 | 候选失效或只读冲突；输入不静默改接另一个 leaf；Harness/Coding |
| RES-NFR-03 | 激活、提交、发布之间取消或崩溃 | 同一输入最多一个持久可见记录；未知结果不自动重放；无未记账的 Worker 或 activation use；Harness |
| RES-NFR-04 | 大 Session、大 Workspace、多 LMUX Session | 有界预览、去重扫描、受限后台调度；明确冷/热缓存及阶段耗时；Harness |
| RES-NFR-05 | 更换 UI、部署方式或扩展实现 | 一个计划入口与现有 owner 选择逻辑；AppService 不获得插件/Graph 内部依赖；跨 scope owners |

性能、安全与一致性场景优先级高；跨版本回滚与 LMUX 多客户端场景技术难度高。
本次评审检查设计，运行时指标与故障注入仍是实施验收任务。

## Resume Compatibility Contract

普通 Resume 分别判断核心数据可读性、会话用户意图和当前执行能力。
历史 receipt 是审计数据；当前 Product policy、权限、Sandbox 和工具网关决定新操作。

| 变化或状态 | 默认行为 |
| --- | --- |
| AGENTS、Prompt、Skill、插件增删升级、工具面变化 | 打开历史；按当前环境规划；记录分类差异或降级能力 |
| 同名 composition 的实现变化 | 保留 setId 意图，解析当前定义；旧 plan fingerprint 仅作证据 |
| 显式禁用工具、explicit_only、模型/thinking/cwd 意图 | 保留意图；无法满足时提示 unavailable 或请求显式重新绑定 |
| 权限/策略收紧 | 新操作立即遵循当前限制 |
| 未经明确配置确认的权限扩大 | 历史可读；执行前显示具体扩大项并确认 |
| 缺 composition provenance，但 Product 身份与 transcript 可确认 | legacy_unknown，同 ID 继续；不补写 Header |
| 缺 Product 身份、来源冲突或无法判定的格式 | 类型化兼容处理；不能默认猜测 Product；按可读性提供查看/导出 |
| 核心格式损坏、不支持的核心 schema、解密失败 | 限制可写恢复；只在有读取授权且数据可读时提供只读/原始导出 |
| 缺历史插件，未知 extension record | 保留历史；未知扩展 inert；不得加载旧插件解释或执行 |
| 未结非幂等 Tool/Worker/activation effect | 查看可用；隔离新效果，显式核对与处置 |

历史记录解码只验证其自身结构与引用，不调用当前 registry 判定历史指纹是否正确。
Runtime/Capability Profile 采用核心兼容分类和当前新轮次 profile，删除普通恢复
的全等门禁。历史 Profile 不提供当前 authority。

Composition set 被移除或 cwd 缺失时，需要显式替代选择。外部来源 import、
真正格式转换或 Product 身份补认继续通过已有受控迁移边界，不能直接修改来源。

同 ID 承诺按入口的身份条件限定：

| 身份证据 | Embedded | Hosted/LMUX |
| --- | --- | --- |
| 已有 canonical Hosted identity，仅缺 composition provenance | 按该身份验证 | 目录可发现，legacy_unknown，同 ID 继续 |
| Product 已证明，但无 Hosted continuity/create identity | 同 ID 恢复 | 首版不自动 adoption；提供可读候选与 explicit identity migration reason，执行需受控迁移 |
| Product 未知或身份冲突 | 不猜 Product；受控确认/只读或拒绝 | 不默认 Coding；保持 ProductIdentityRequired/conflict |

仅传入 product_id 不是身份来源证明。现有 hosted catalog 排除缺 Hosted metadata
的文件；新增只读候选发现投影与受控迁移是显式入口改动，不放宽 canonical 校验。
“跨入口同语义”指满足入口身份约束后的恢复与执行，不意味着全部旧文件自动跨部署。

可选 exact 模式只在历史依赖证据可重建时提供。它不自动安装历史插件，
不绕过当前权限上限；legacy_unknown 不声称可 exact replay。用户必须显式
选择切换为 current 模式，禁止静默回退。具体入口与能力范围在发布切片中确认。

## Ownership And Deployment

| 责任 | Owner | 协作者与边界 |
| --- | --- | --- |
| 普通恢复、legacy 分类、composition 用户意图 | Coding continuity/session | 调用 Harness 公共机制；不改变 AI SDK |
| 通用只读 projection、Writer fencing、journal/Blob、取消与关闭 | Harness 现有 owners | 按需补充公开契约，不建第二个 store 或 lease manager |
| 插件选择、Resource/Tool/Policy 投影、Graph prepare/bind | 现有 Harness owner + Coding composition | 后台与正式阶段使用同一选择逻辑 |
| Product admission、身份路由、scoped factory | AppHost | 提供 Product route；不发现 Product 内部插件 |
| canonical process-local Product live binding | AppHost 现有 live registry | 去重 factory、profile generation、attachment 引用与最终关闭 |
| 服务端 Session 路由投影、attachment/controller、execution admission、客户端事件 | AppService | 消费 Product 窄接口；不 import Harness planner/binder 或 Coding internals |
| framing、连接、RPC 传输 | AppServer | 不获得 transcript 或 runtime 激活所有权 |
| pending 编辑、显示和用户输入 | CLI/TUI/LMUX client | 状态来自 Product 投影；执行由服务端 Product binding 决定 |

Embedded 在前台进程内创建 Coding continuity owner；Hosted 在 LMUX AppHost
进程内创建相同 Product owner，并经 Coding hosted adapter 暴露窄 Session port。
可共享纯值定义和静态缓存，mutable runtime、Writer、审批与 Worker lease 按 Session
隔离。既有边界见
[AppService Boundary](../architecture/drafts/appservice-embedded-tui-hosted-boundary-plan.md)
与 [Coding Hosted Adapter](../../../src/loushang/coding/appservice_adapter.py)。

```text
Embedded CLI/TUI ───────────────────────┐
                                      ↓
LMUX client → AppServer → AppService → Coding Session binding
                                      ↓
                         同一恢复计划与激活入口
                                      ↓
                         Harness 原有 owners
```

图中为候选调用关系，不代表新增 import 依赖。AppService 只观察准备状态、
脱敏诊断和 typed admission，不持有 SessionActivationPlan 或 Epoch Vector。

LMUX 已存在的活跃 Session 采用 attach/reconnect，不重复从磁盘 Resume。
只有未在 live registry 的 persisted 会话，或服务重启恢复时才走新恢复流程。
AppService 聚合成员可在历史可读、订阅与 cursor barrier 建立后显示为 preparing；
准备状态纳入 snapshot/event，禁止把 preparing 伪装成可执行。

Hosted scoped factory 的候选改动为：创建一个轻量 Product continuity runtime，
其 identity/read-only snapshot/status subscription/close 已可用，内部 execution runtime
尚未激活。AppHost 仍只发布一次 canonical live binding，两个客户端 attach 等待
同一个 factory task；后续激活在该 continuity runtime 内完成，不替换 binding key、
profile generation 或 attachment 身份。AppService 只取得其服务投影。
现有 Coding adapter 构造即依赖 live control；需在原 Product binding 内提供延迟
execution control 或 readiness facade，不能另设第二个 live registry。

只读 facade 构造和 snapshot 禁止调用 Writer/Extension/Worker prepare。关闭与
generation retirement 沿原 AppHost ownership chain 收敛，dispose 内部 Plan、
activation effects 与 Writer。此 factory/port 变更需 AppHost 与 Coding owner 接受，
两客户端同时 attach/准备中 detach/关闭 debt 测试通过后才能开放 Hosted 快速恢复。

## One Plan And Existing Prepare Owners

新增 `SessionActivationPlanV1`，初期作为 Coding 内部不可变数据值；只有被多个
Product 验证为相同公共需要时，才将最小契约提升到 Harness。它不是新的公共
Capability planner，也不是新的插件 registry。

Plan 引用现有 owner 产生的不可变 selection/projection 结果，保存：plan ID、
schema version、session/branch/workspace identity、用户意图、输入依赖指纹、
epoch vector、兼容分类、差异及能力降级。数据可以丢弃、重建；不保存
Credential、Grant、模块、工具实例、live graph 或可写句柄。

每个选择只存在一个 canonical owner。现有 prepare 若混合纯计算与资源获取，
先在该 owner 内提取纯计划步骤；后台调用此步骤，正式 prepare 消费其结果并验证。
旧调用入口可委托相同逻辑。不得在 Resume 层另写插件、工具或 Provider 选择算法。

| 术语 | 契约 |
| --- | --- |
| inspect/snapshot | 只读数据与有界历史 projection |
| plan | 纯计算，不取得实时执行权或资源 lease |
| prepare/acquire/stage | 已获得资源所有权，必须 close/settle |
| commit | 将事实持久化，处理未知提交结果 |
| publish | 使运行态或逻辑事件对消费者可见 |

`PreparedProductRouteV1`、Prepared Transcript restore、Capability prepare/bind
保留各自作用域的所有权和关闭责任。协调器通过已有 acquisition/close 基础串接，
不再引入一组平行 PreparedResume/PreparedRuntime/PreparedActivation 公共对象。

Plan 新增纯值结构不意味着新增第二套事实源。正式阶段的选择与 Plan 不一致时
返回 stale/replan；禁止自行静默换 Provider。测试对比冷规划、热缓存规划与现有
owner 选择结果，并约束各 UI 与 Hosted adapter 使用同一入口。

## Fast Open And Background Plan

只读打开使用 read-only store；不修复 partial JSONL tail、不 enrollment、
不写 shutdown/activation。Header、索引和最近页先显示；验证不足的页面标为
preview，不能直接作为当前 active branch 的执行依据。

权威绑定的轻量 recent-page cache 保存 revision、leaf、父链、offset、journal
identity 和兼容版本。索引失效时先提供有界 preview，再完成所选路径验证。
执行前必须完成所需核心路径验证；正常恢复不全量重建所有历史 Model Input。

确定 Session/branch/workspace 后即可启动后台 Plan，first-paint/输入任务优先。
仅静态读取 Manifest、包摘要、资源和声明式 Schema；禁止 import 第三方或工作区
Python，禁止 factory/register/get_tools、进程、网络、Worker payload/lease 和
durable activation decision consume。动态旧扩展标为 non_speculable，正式激活
才求值；只读后退出不会执行其代码。

后台任务由 Product Session owner 持有。Embedded 页面关闭会取消其未交付任务；
LMUX 客户端 detach 不等于服务端 Session close。服务端根据已有 Session 引用与
资源预算决定保留或取消 Plan；任何取消均可重新计算，无权威状态遗失。

共享调度器提供按阶段限流、singleflight、Workspace 扫描去重、容量与取消预算；
asyncio Task 本身不构成低优先级保证。用户继续时提升对应任务优先级，不能使
一个 Session 的大扫描阻塞其他 Session 的首屏或中断操作。

共享纯值任务由承接该计算的原 Harness owner 持有；Coding continuity owner 管理
Session 的等待引用和优先级。singleflight key 与缓存使用相同主体/Workspace/policy
隔离域。取消一个等待者只释放其引用；最后一个引用释放才取消工作。
IO 与 CPU 解析分别使用有界执行槽和线程/进程载体，循环按文件/字节工作单元
检查取消，不能把无界同步扫描直接放到 event loop 或默认线程池。
超过预算退回按需规划并保留 pending；具体并发/字节/取消预算在基线后确定。

## Final Validation And Live Authority

Plan 的 Epoch Vector 覆盖 Store/file identity、revision/branch/leaf、workspace
根与 cwd、composition intent、package/instance revision、tool owner generation、
resource snapshot/source generation、policy/actor/permission/approval/sandbox、
Worker 协议和 model/provider selection。

用户继续时获取唯一 Writer，复核 transcript identity 与预期 leaf，再由原有
owner 获得当前资源 generation guard。不能 pin 的可变源采用不可变字节 snapshot
和双读稳定性：构建前 A、构建后 B 与计划完全一致才交付。stat 信息用于快速
失效检测；内容闭包通过摘要、不可变包 revision 与 owner generation 证明。

双读只检测观察点变化，不证明实际执行内容。正式 stage 必须消费 Plan 所证明的
不可变 snapshot，或由原 owner pin 到实际消费、commit、publish 的 generation。
动态 import 的入口、相对 import 与延迟依赖属于内容闭包；路径摘要不能替代该
证明。支持 pin 的包加载链需明确公开 owner 契约。旧式扩展无法证明闭包时，
首版默认 unavailable；若将其纳入可信进程代码，须先由原 plugin trust/admission
owner 明确批准精确 scope 并记录证据，不能靠恢复时后置确认补授权已执行代码。
动态贡献可在原 owner 批准的静态能力上限内 refinement；超出范围即关闭门禁并
失败/重新准入，Plan 标记未确定部分，不以全环境 equality 触发无限重规划。

任一依赖变化，相关确认随 Plan 失效；按依赖图增量重建。变更重试设置预算，
持续变化时保持 pending 并提示，不无限追逐或静默采用旧环境。Writer 获取失败
保持只读冲突；拿到 Writer 后 leaf 变化也不能自动将输入换到新分支。

ACTIVE owner 持有 Writer 到 Session 关闭或替换。Hosted 多客户端共享该 owner，
controller generation 与 Writer fencing 分别管理客户端控制和磁盘写入。
权限扩大确认绑定当前主体、目标 Session/leaf、候选 fingerprint 和精确扩大项；
发送消息本身不表示同意。已通过可信配置流程明确选择当前权限的操作避免重复
确认，历史 receipt 仍不能授权。Legacy 未知基线加 full_access 按未知扩大处理。

权限差异基线是当前主体仍有效的、由原 Approval/Plugin activation owner 确认的
subject 与 scope；历史限制可用于比较但不能授予权限。复用已有 subject digest、
package/dependency digest、policy revision、revocation epoch 和 effective authorities。
配置值本身不算确认凭证；未知/部分未知/不可比较 authority 在所需执行能力超出
可证明 scope 时请求确认。可信配置流程免重复提示必须匹配原 owner 的有效确认
事实、主体、范围和撤销状态。没有匹配事实时不因配置写着 full_access 而豁免。
等待确认时不持有 Writer；恢复执行前重新取得 Writer 并验证绑定完全相同。

每次 Model Input 使用当前暴露策略；每次 Tool Start 使用当前 Policy、Approval、
Sandbox ceiling 与 hard revocation；每次 Worker 接管使用当前 fencing。Plan 与
Binding 解释某次选择，不提供未来持续授权。

## Activation And Durable Continuation

正式 activation 采用可恢复 Saga。磁盘、插件代码和进程没有共同事务，
所以记录严格区分 attempt、绑定输入和 runtime 发布。

```text
History / Plan ready + local pending input
  → confirm if needed
  → acquire Writer and revalidate
  → commit activation attempt intent
  → stage current Runtime with execution gates closed
  → final validation and immutable Blob staging
  → 单条 agent.message 提交 UserMessage 与 RuntimeBinding metadata
  → publish Runtime and open execution gates
  → model request
```

`coding.activation-attempt/v1` 记录 attempt ID、plan fingerprint、目标 leaf、
当前 epoch、效果分类和关联 request ID，只说明正式激活尝试开始。后台规划不会
写该记录。插件 import/Worker 启动由各既有 owner 执行，复用它们的 durable
launch/use 记录与清理；协调器只关联证据，不创建第二个 Worker journal。

所有工具执行、历史任务接管、自动 Continue 和模型传输门禁在成功提交与发布前
关闭。插件 activation 本身属于已获当前 admission 的正式效果；动态插件的真实
贡献若偏离静态候选则重新校验，需要扩大 authority 时重新确认或退回失败。

R2 优先保留 `AGENT_MESSAGE_KIND` 与 `UserMessage` payload，将有界 RuntimeBinding
放在该记录独立版本化的 Coding-owned metadata key。它与原 resource-evidence
metadata 在记录构造前合并、冲突拒绝、同一次提交，不先写消息后补 binding。
首个输入指本次 activation epoch 的首个 continuation 输入。复用
[AgentEventRouter](../../../src/loushang/harness/session/agent_event_router.py)
及原 message-commit owner 的证据准备与 commit 协调，后续响应流程接收 canonical
record ID，禁止先专门 append 后又由正常事件重复 append。

完整且校验通过的同一物理记录使输入与 Binding 一起可见；这不承诺物理 write
不会残缺。partial-tail、fsync/ack unknown 与 Store head 的收敛继续验证。
Binding 仅记录 attempt/input ID、目标 ancestry、originEvidence、计划/实际环境
指纹、payload digest 和脱敏差异，设置 schema 与字节预算，不保存整个 Plan。
它不代表 current authority、Runtime 已发布、用户已授权新操作或模型已经收到。

从所选 ancestry 发现 epoch binding，不能仅从当前 model context 发现；compaction
可去掉消息上下文而保留历史事实。分支到 binding 之前不继承该 epoch。
跨 Session fork 复制的 Binding 保留来源 Session/输入事实，不代表目标已经激活，
也不作为目标 Session 的输入去重证明；目标新 epoch 和幂等身份重新按目标授权建立。
未知 metadata schema inert，不进入模型正文；独立 binding annotation/patch 不允许
覆盖已提交事实。原始导出可含脱敏审计字段，Hosted/HTML 投影使用明确白名单。

稳定 logical input ID 关联固定 record ID、Session/branch、目标原 leaf、payload 与
完整 metadata digest。预构建消息及相关 resource evidence 通过原消息提交 owner
提交；unknown 时核验同一 record/operation，不能再次普通 append 生成新 ID。
attempt 若推进 transcript leaf，区分原输入目标 leaf 与本 owner 新增记录后的
expected parent；验证无外部写入后，消息父链包含 attempt，CAS 使用实际提交 parent。

Binding 首版内联，不新增 Blob；用户图片沿原 message externalization owner 先
durable staging，再提交引用。提交结果 unknown 时禁止 orphan GC 回收相关 Blob。
取消/失败后只有证明未提交才能清理，branch/export/compaction 验证沿原消息引用。

N/N+1 旧 reader 的消息显示预期保持，但旧 writer 会忽略新 metadata。不能假定
新门禁保护旧 binary；首版只承诺经测试版本的读/导出，不承诺降级后的安全可写
恢复，发布须明确最低 writer 版本与 unsupported rollback，并实测原 gate 的行为。
若产品要求旧版安全写恢复，需另做可被旧 binary 理解的兼容机制后才能接受。

新 envelope 不再是首选。首版 writable current 仅开放用户消息触发；无用户消息
的自动 Continue、compact、其他 effectful continuation 先保持受限或原已验证路径，
不伪造空 UserMessage。纯元数据 rename 只需 Writer/当前授权，无需 Runtime。
确需多独立记录共同可见时再评估 Store transaction visibility；不能用逐条 batch
fallback 冒充事务，也不能将消息载体的保证泛化到所有 command。

Runtime 发布失败且消息与 Binding 已成功提交时，显示“消息已保存，响应未启动”。
重新建立环境后只重试响应。模型请求已可能发出但无结果时，标记 outcome_unknown；
不宣称外部请求 exactly-once，也不自动重放。用户显式重试才产生新的 model attempt。

崩溃恢复根据已有 attempt、commit 与 owner journals 判断：无效果时可废弃计划；
已启动效果而无可靠终态时先 settlement/quarantine；完成输入不重复追加。
清理失败记录 debt 并限制新效果。历史 Tool/Worker 调用不自动重放。

Admission/use 终态与 effect settlement 分别判定。原 plugin activation use 的
STARTING/STARTED 在新 host boot 被恢复为 FAILED，不证明外部效果未发生。
协调器保留该 unknown 含义，由原 effect owner 提供独立结算证据；只有可信完成、
未启动证明或显式处置解除隔离。attempt intent 不能替代 Worker/extension 的效果证据。
模型响应重试使用原 durable Model Input invocation/outcome projection：没有 attempt
时可以准备响应；已有 prepared snapshot 而无可靠 outcome 保守 unknown，即使可能
尚未发送；显式重试创建新 model attempt，输入 record 不变。

## Input State And Hosted Admission

| 状态 | 输入事实与用户操作 |
| --- | --- |
| draft | 尚未提交，输入框可编辑 |
| pending_prepare | 本地 pending，未写入，未交给模型；可编辑/取消 |
| awaiting_confirmation | 输入仍 pending；确认独立绑定候选，文本不能充当确认 |
| activating | 正式 activation 已开始；取消需结算已有效果 |
| committing | 等待确定提交结果；取消先等待提交收敛 |
| committed | 输入 durable；取消保留消息并可阻止尚未发出的模型请求 |
| running / response_failed / outcome_unknown | 展示响应状态；重试不重复输入记录 |

首版一个 Session 只允许一个激活触发 pending。prepare 失败保留文本；commit
前取消可恢复草稿；退出时未保存输入需明确提示。传输断开与用户取消是不同事实。

Baseline `start_turn` 返回 AckV1，Product `start_turn(text)` 返回 None；新 execution
registry 使用 ACCEPTED/RUNNING/... 与 service-instance scoped submission ledger。
Started/Consumed/Queued/Rejected 属于边界设计中的候选约定，尚不能称为现有
activation queue。R2 复用 execution/submission owner，增加准备状态的 Product
投影及必要能力协商，不先建平行 Turn/Activation queue。

| Baseline 接口或身份 | R2 候选映射 |
| --- | --- |
| 连接 transport request ID | 仅相关一次 RPC，不作 durable input identity |
| client submission ID | 客户端预生成稳定 logical input ID；服务端绑定主体、Product/Session/branch/原 leaf 与 payload digest |
| ACCEPTED execution + execution ID | 表示服务端 admission 已接受；准备是其 Product 子状态，不代表输入已保存或模型运行 |
| service instance ID | 检测重启；旧执行 ID 可失效，logical input ID 跨连接/重启保留 |
| agent.message record ID + Store operation ID | 固定 canonical record ID；承载消息与 Binding 的 durable reconciliation |
| Ack-only old client | 保留原 operation completion/错误返回时序；激活与输入提交是必要条件，不提前将 Ack 改为 committed acknowledgment；无法交互确认时明确拒绝或要求新客户端 |

首版服务端非持久 pending 不承诺跨重启队列恢复。客户端保留 logical ID/文本到
明确 committed；重连先按当前读取授权与 stable input ID 查询 durable record 和
model attempt。只有完成 authority store 核验，证明未提交且目标 ancestry 未变化，
才允许同 ID 重新 admission。not retained、旧 instance 或扫描未完成是 unknown，
不能当作未提交。跨重启查询必须覆盖已提交但不在当前模型上下文的目标 ancestry，
并返回 committed、not_committed_verified、unknown 或 conflict，不依赖内存 ledger。
补齐该 Product durable lookup 及 service event 契约后才能启用 Hosted retry。

客户端尚未发出时可以编辑；server admission 接受后冻结该 ID 的 payload。
改文本需先获得取消且确定未提交，再用新 logical ID；同 ID 不同 digest 拒绝。
controller takeover fence 旧 controller 的 mutation，accepted 请求绑定既有主体与
目标 Session，由新合法 controller 显式查询/取消/继续；重新 admission 要重新授权。
断线不取消 accepted execution。新增状态使用现有 execution owner 的终态规则；
旧 Turn interrupt 仅作用于其原目标，不取消未交付本地 pending。

`/resume` 切换候选失败保留原活动 Session 与文本归属；不能自动新建会话。
Fast View 绑定 candidate identity，交互必须明确当前目标，正式切换通过现有 lifecycle
owner 结算。CLI/TUI/Hosted 共用稳定事件与 reason code，而非异常英文字符串。

显示目标与执行目标分别保存：预览 B 时输入明确属于 B 的 editor/pending 容器；
A 保持原执行 owner。B commit 前返回 A 可取消本地 pending，已启动 effects 则
异步 settlement，不丢文本或释放未结资源；B commit 后返回 A 只改变显示，
B 的已保存消息不回退，响应失败由 B 的状态展示。通知与 action 按 mux/member/
session/presentation generation fencing，沿现有 A→B→A editor 隔离语义。
所有状态有文字标签与目标 Session，确认/保存/失败可被辅助技术感知，进度不夺焦点。

用户主状态为“可继续”“需确认”“只读”，准备中和未发送状态额外明确显示。
快照应包含 history verification、activation readiness 与 pending/committed 信息，
重连通过 cursor/snapshot 收敛，不能把 app snapshot revision 当作 runtime generation。

## Cache And Incremental Preparation

纯值缓存保存 package/static manifest、Schema 解析、resource 解析、catalog merge
和 Worker artifact 校验。缓存键包含对应内容摘要、parser/protocol/ABI/platform
版本、输入依赖向量；含工作区数据的缓存还绑定安全主体、workspace 根身份、
安装/Product 与相关 policy generation。跨 Session 只共享真正不可变且无秘密的值。

整个 ActivationPlan 不作为跨 Session authority 缓存；Session 部分绑定 revision/leaf。
不缓存 Writer、Credential、Approval、Grant、模块、LoadedExtension、ToolRegistry、
Worker receipt/lease 或活跃 graph。缓存采用 private permissions、容量/LRU 和
schema 版本；失败不长期负缓存。cache root 是非权威、可删除的独立目录。

依赖图复用原有 owners 的输入/输出 fingerprints：AGENTS 变化重建 Resource/Prompt；
权限变化重建 Authority/Tool projection；package 变化重建对应 Plugin/Tool/Resource；
transcript append 验证 tail 并更新 selected context；Worker 变化不重读历史。

正式获取 Writer 后，若文件 identity/revision/内容 proof 完全相同，可采用后台
detached transcript snapshot；仅 append 时验证 tail，替换/缩短/分支变化回退。
该优化需先补公开 owner 契约，避免“后台全读一次、激活再次全读”的重复成本。

Session 列表只读便宜摘要与 resumeHint；对当前选择或可见且预算允许的 LMUX 成员
规划，不为每行扫描 Workspace/加载插件。索引缺失不能显示误导性的 No sessions yet。

## Alternatives And Tradeoffs

| 选项 | 收益 | 成本与推荐 |
| --- | --- | --- |
| 保留环境全等门禁 | 实现改动小 | 无法满足正常升级与资源编辑后恢复；不选 |
| 首条消息后才开始全部准备 | 最少推测工作 | 首次交互等待长；仅作为资源预算不足时回退 |
| 显示期间启动完整 Runtime | 可能最早 ready | 只读浏览会 import/启动 Worker；不满足零权威副作用约束 |
| 显示期间纯计划，继续时复用现有所有权 prepare | 重叠静态成本，保持统一 owner | 正式阶段仍有动态插件/Worker 成本；推荐 |
| Legacy 默认复制到新 ID | 可独立新 Header | 分裂 ID、复制 Blob/历史成本高；仅真转换/外部 import 时使用 |
| Legacy 同 ID 追加 continuation epoch | 用户心智与性能简单 | reader 需区分未知起点与新绑定；推荐 |

纯计划不能保证首条消息零等待；动态扩展和 Worker 的启动保留在正式阶段。
优化效果取决于可静态规划工作的占比、缓存命中和 transcript snapshot 复用。
共享 Worker warm pool、全局强一致环境锁和持续 full-history audit 不纳入首版。

## Delivery Sequence And Acceptance Evidence

1. 修复恢复契约：历史 provenance 解码与当前解析拆开；普通 Resume 放宽三层
   全等门禁；身份与核心兼容验证保留；加入 legacy_same_id、upgrade golden fixtures。
2. 拆 owner 内的 pure plan 与有所有权 prepare，统一 Coding 执行入口；先完成
   readonly/取消/关闭测试，再启用后台 scheduler。源码实现按 code/harness lane 分工。
3. 验证 agent.message metadata binding 的单记录提交及全部 projection；通过断电/残尾、
   operation-ID、branch/Blob/request-evidence 测试后才启用新写入格式。
4. 完成 writer/epoch/权限确认、activation effects settlement、pending 输入与重试。
   垂直切片可先使用同步规划；后台任务后接同一 Plan，不能绕过提交门禁。
5. 接入 Hosted Facade 的只读/准备状态和 typed admission；保留既有 AppHost
   admission、AppService controller/attachment/idempotency owners，不建立第二套队列。
6. 加 recent-page cache、detached snapshot reuse、pure-value cache 和增量调度；
   建立冷/热、大小历史、多 Session 性能基线。
7. exact 验证作为可选后续切片；发布前记录真实支持范围，current 默认不受其拖累。

上述为开发依赖顺序，不是七次独立上线承诺。发布切片为：

| 发布切片 | 可开放行为 | 必须同时具备 |
| --- | --- | --- |
| Read-only compatibility | 宽容历史解码、可读候选/导出 | read-only store、identity 验证、零效果；保留旧可写门禁 |
| Embedded writable current | 用户消息触发、same-ID legacy 范围 | 三层兼容改造、当前 admission/确认、消息binding/evidence单提交、effects结算、未知提交/模型恢复 |
| Hosted writable current | canonical身份范围内 LMUX 用户输入 | 上述安全切片 + canonical facade、协商、stable ID durable lookup、controller fencing/取消/重启 |
| Background/performance | 显示期间Plan、缓存、snapshot reuse | 复用同一同步Plan与commit入口，调度/取消/隔离与性能工作量验收 |

后台纯 Plan 可以在任一已有安全运行切片内先启用；任何可写 current 入口都不能
仅删除门禁就上线。未开放路径返回明确 reason，不静默创建 Session 或使用旧权限。

必须覆盖 RES-FR/NFR 的契约测试：

- 跨安装 N/N+1、AGENTS/Skill/插件/策略变化、same ID legacy、多绑定 epoch。
- 恶意 extension 顶层 sentinel：只读/Plan 无 import，无进程，无 journal 写入。
- 所选分支 recent-page、stale cache、tail append、workspace/symlink 替换。
- 两进程 Writer 竞争、多个客户端 controller 切换、plan 改变确认失效。
- intent/插件/Worker/Blob/commit/publish/model-start 各窗口取消与崩溃。
- 未结非幂等操作隔离；旧 grant 不复用；当前策略执行前收紧仍有效。
- 已提交输入不重复；模型 outcome_unknown 不自动重放；退出不 silently 新建会话。
- LMUX attach、detach、重连、服务重启与 queue ID 归属；单 Session 失败不阻塞其他成员。
- current/exact 与旧版本 export/profile 保留未知记录的兼容边界。

指标分别记录 first frame、输入接受、Plan ready、input durable、model transport，
以及读取/解码字节、full rebuild 次数、Writer wait、fsync、CPU/RSS/FD、缓存命中、
Plan 废弃与取消耗时。冷/热缓存、1/2/8 Session、1万/10万记录及大量资源都报告。
共享 CI 优先确定性工作量断言，固定毫秒阈值先由指定机器基线确认；此前讨论的
500ms 首屏与 100ms 热计划提交额外延迟仅是优化愿望，不作为已实现或已接受保证。

## Review And Decision Boundaries

项目 owner 已于 2026-10-12 在 #696 实施会话中明确“接受，继续”。按
[governance profile](../architecture/governance-profile.md) 记录的跨 scope 接受
决定为 [ARD-004](../architecture/decisions/accepted/ARD-004-resume-history-and-current-authority.md)、
[ARD-005](../architecture/decisions/accepted/ARD-005-resume-continuation-commit.md) 和
[ARD-006](../architecture/decisions/accepted/ARD-006-hosted-resume-readiness-and-admission.md)。
恢复边界、v1 continuation 契约及 Hosted 单一 binding 语义可进入实施；实际开放
可写路径仍须满足本文的授权、故障、版本与性能发布条件。

独立评审检查架构性能、安全一致性、兼容产品三视角。评审意见须引用 R1/后续
具体 revision，区分 demonstrated source facts、设计歧义和需 spike 的假设。
修文关闭的是设计歧义；运行时保证需实现与测试。跨视角矛盾在综合记录中处理，
语义修改需受影响评审者复核，不能将旧评审结论泛化到新 revision。

## Local Implementation Baseline (2026-10-12)

The offline command `env PYTHONPATH=src .venv/bin/python
scripts/dev/verify_resume_scale.py --sessions 2 --logical-size-mib 1 --json`
passed on both `main` at `574f24bc` and the #696 task branch at `0198ef86`.
The script creates two sparse catalog candidates and one valid 40.008 MiB
transcript, then resumes it in a fresh process with a deterministic model.

| Observed phase | `main` | #696 branch |
| --- | ---: | ---: |
| Cold bounded catalog listing | 7.402 s | 8.181 s |
| Fresh-process Resume through completed turn | 11.512 s | 11.833 s |
| Resume to first model request | 3.958 s | 4.206 s |

These two local runs establish a pre-background baseline, not a speedup claim
or a stable latency budget. The script does not yet measure first frame, input
acceptance, Plan readiness, durable input, CPU/RSS/FD, or 1/2/8 concurrent
Sessions and 10k/100k record scenarios required for R2.1 acceptance.

## Internal Recovery Guard Evidence (2026-10-12)

The internal ordinary-route guards were committed as `db90f355` and
`2221b8c7`. The Resume Binding, Plan, comparison, and history-preview tests
passed 46 cases after those changes. Three normal bootstrap/model-preparation
cases also passed on the final guard code.

Commit `6da762e1` adds three real JSONL reopen cases: an unbound v1 intent,
an unknown v2 intent, and a malformed v1 intent. After closing and loading a
new SessionManager, each case retains its Session ID and selected leaf,
rejects ordinary continuation with the corresponding typed recovery reason,
and remains viewable through the read-only snapshot. The final file bytes
equal the bytes before reopening. All three cases passed.

Ruff passed for the touched code and tests. Mypy with
`--follow-imports=silent` passed for `resume_activation_attempt.py`,
`session_manager.py`, `bootstrap.py`, and `session/agent_session.py`.
These checks establish the internal historical guard; they do not establish
live activation admission, effect settlement, Hosted continuation, released
N/N+1 compatibility, or the complete R2.1 quality and performance gates.

## Latest Main Integration Evidence

The task branch incorporated fetched `origin/main` at `197a9008` through
merge `f915f5f0`, including the Windows history-source inventory and conditional
Windows PR smoke selection. The merge had no conflicts. After integration,
212 non-live tests passed across `tests/ci`, Resume Writer/Binding/Plan, framed
execution connections, authenticated local execution, local records, and
connection profiles. Documentation validation passed nine checks. This proves
the listed local integration checks, not Windows runtime execution or completed
Resume admission/publication, release, and performance acceptance.

## Internal Coding Candidate Preparation Evidence (2026-10-12)

208 non-live tests passed across Resume runtime preparation, Binding, Writer,
ordinary Coding AgentSession and the Harness AgentProduct contract. The seven
new preparation cases use the original owned Writer and graph: definite intent,
unknown acknowledgement, historical-only intent, admission denial, wrong attempt,
changed selected branch and revocation after real graph binding. The last case
also rejects retry after failed preparation. All preserve transcript bytes
during preparation and keep execution unavailable. An initial fault run exposed
a Writer-drain deadlock when an operation scope spanned graph rollback; short
synchronous admission scopes fixed that lifecycle conflict, and the final
seven-case run completed normally.

Seven focused composition tests also passed for detached current observations,
concurrent ordinary preparation, foreign startup rejection and fenced Product
startup records. Ruff, mypy for the two changed Product modules and all nine
documentation checks passed. The graph-preparation fixture constructs its AgentSession
before committing intent; those tests do not prove bootstrap from a legacy resumed
Writer, native Worker effect settlement, Hosted readiness or Runtime publication.

## Internal Resume Bootstrap Evidence (2026-10-12)

The owned Writer baseline passed four tests before this slice. A new legacy
reopen test first failed because the internal Resume bootstrap was absent.
After implementation, 159 non-live tests passed across Resume bootstrap, runtime
preparation, Writer, Binding and the ordinary Coding bootstrap suite. The seven
new bootstrap cases cover legacy history, a previously prepared standard
composition resumed with the current minimal composition, initial denial,
wrong current composition, revocation after construction, a non-None admission
result and an uncertain intent acknowledgement. Successful cases construct and
prepare the real candidate graph without changing history after intent commit;
execution remains unavailable. Delivery revocation disposes the original
candidate Writer, while wrong composition and uncertain intent are rejected
before the caller's admission callback.

Ruff and mypy for the changed Product modules passed, documentation checks
passed, and the cumulative change-aware gate plan was inspected. Full branch
quality gates and Actions platform checks remain pending. These internal tests
do not prove live subject/policy grants, native effect correlation, production
Embedded/Hosted continuation, Runtime publication, performance acceptance or
released N/N+1 behavior.

## Internal Runtime Publication Evidence (2026-10-12)

The pre-change Binding and candidate-preparation baseline passed 51 tests.
After adding publication, 184 non-live tests passed across publication,
bootstrap, graph preparation, Binding and ordinary AgentSession. After extending
published Resume admission to shell, extension exec and explicit compaction,
the final related Binding/AgentSession/publication run passed 170 tests.
The existing inert guard fixture now uses the actual AgentSession type so its
instance admission checks are exercised without downstream execution services.

The final eleven publication cases passed. They cover definite publication,
unknown input acknowledgement, selected branch change, subject revocation,
unsettled epoch effects, changed current receipt, missing local graph,
unknown durable lookup, revocation during lookup, real on-disk input mutation
and cancellation while awaiting lookup. Successful publication permits current
runtime preparation and a descendant input without writing historical startup
records; later revocation rejects model preparation, shell, extension exec and
explicit compaction. Selecting ancestry without the bound input also rejects
preparation. Failure cases preserve the closed gate, perform no publication
history write and dispatch no model request. Publication cancellation retains
the already committed input and leaves execution closed.

Ruff, mypy for the two Product modules and documentation checks passed. The
admission and epoch-settlement callbacks in these tests exercise the internal
boundary contract; they do not establish real current grants or native effect
journal correlation. Production activation and submit owners must still supply
those checks and consume the single committed input without appending it again.
Hosted readiness, model outcome recovery, full quality gates, performance and
released-artifact acceptance remain pending.

## Internal Committed-Input Dispatch Evidence (2026-10-12)

The pre-change Harness router/runtime baseline passed fourteen tests. The
updated router/runtime run passed fifteen, including a retryable error whose
observation is retained while retry/compaction are suppressed, and whose normal
recovery behavior returns when the predicate permits it again.

The final integrated run passed ninety non-live tests across Resume publication,
Coding's Model Input contract, Binding and Harness router/runtime. Seven new
dispatch cases cover completion, provider connection failure, an existing queue,
initial subject revocation, revocation after real snapshot commit, caller
cancellation during transport and Host abort. The fixtures use a registered
offline prepared API adapter through the standard AI stream, not a bypassed
custom stream. Every invoked request creates one original Model Input snapshot
with purpose `main`, while the original history plus resumed input remain exactly
two UserMessages. Repeated dispatch is rejected without another request.
Revocation at the commit barrier retains the snapshot and invokes no transport.
Provider failure, abort and cancellation invoke at most one transport and retire
execution preparation. CallOptions and the run-local recovery predicate return
to their prior values. No network provider is contacted.

Ruff, mypy for the three changed source modules and documentation checks passed.
This proves internal consumption and the original transport boundary. It does
not prove production current grants or native effect settlement, Hosted submit
deduplication/outcome lookup, restart recovery or Embedded/TUI integration.
These production callers and the full release/performance gates remain pending.

### Hosted detached history binding

`CodingHostedSessionCatalogV1.open_history_binding` reads the original bounded
selected-path snapshot and rechecks the discovered canonical identity, source
revision and accepting owner before delivery. It bypasses writable candidate
claiming entirely. It does not run services selection, Product preparation,
Writer acquisition or historical startup replay. Ordinary writable open and
idempotent create retain their existing checks.

The returned `CodingHostedHistoryBindingV1` holds only a detached bounded text
projection. The existing Hosted adapter and application binding validator admit
an explicit absent execution control; no artificial SessionControlPort is
created. Snapshot and subscriptions are available, prompt/steer/follow-up report
Session unavailable, interrupt reports false, and interactions cannot approve
historical requests. The display neither grants current actor authority nor
provides input-outcome lookup. Existing scoped AppService read authorization
remains required by callers. Closing the binding is idempotent and has no runtime
or Writer to dispose.

Regression coverage exercises changed composition/capability metadata through
the actual Hosted adapter, preserves the selected left branch when a right
branch is also present, and rejects delivery after source revision change or an
owned catalog fence. Successful display leaves original transcript bytes intact.
The pre-change adapter/real-session baseline passed fifteen tests with one
existing skip. Scoped mypy for all four changed source modules and Ruff passed;
unscoped mypy also reports pre-existing errors in imported modules and is not
the changed-module gate.

The final integrated run passed fifty-eight non-live tests with one existing
skip across Hosted catalog, adapter, application, execution and real-session
coverage. The owned-fence case uses the real managed catalog; the legacy
unowned catalog's historical no-op fence is not used as shutdown evidence.
All nine documentation checks passed.

This is an explicit history entry, not yet the default LMUX/AppHost open route.
The original real-session factory still constructs an executable runtime eagerly.
Connecting deferred AppHost claim/profile ownership, native current policy and
effect settlement, first-input activation, and Embedded/TUI remains required.
The full bounded snapshot read is not a measured large-session fast-open path;
tail paging and background-plan performance acceptance remain pending. Goal and
Issue #696 remain incomplete.

### Hosted history claim and profile ownership

The catalog's explicit `open_history_candidate` entry now wraps the detached
display in the original candidate/claim lifecycle. Its exact
`CodingHostedHistoryCandidateBindingV1` type carries no SessionManager or Writer.
The original Product candidate validator continues to require matching canonical
reference, envelope and Hosted compatibility identity. Claim verification and
factory transfer recheck the original source revision and managed catalog fence.

`CodingRealHostedSessionFactoryV1` recognizes this exact display candidate before
services or Package Product selection. Transfer is synchronous and consumes the
display once. Failed identity, source or owner checks retain candidate cleanup;
closing an untransferred candidate closes its display. After transfer, candidate
and claimed-handle cleanup leave the delivered Product display alive. The
original foreground Product runtime and Hosted profile factory accept the
absent execution control, with their existing identity and close ownership.
Neither the candidate nor the display is a current actor grant or an activation
proof.

Nine focused offline cases passed for delivery through the original Product
runtime/profile path, source changes before and after claim, catalog fences
before and after claim, a closed factory, wrong binding key, unclaimed close,
claimed close, repeated delivery rejection and post-transfer candidate cleanup.
Test services and Product-selection functions fail on invocation; successful
historical display invokes neither and preserves transcript bytes. The managed
fence cases use the original owned catalog on Linux. The pre-change history
baseline passed four cases.

The integrated non-live catalog, owned-catalog, real-session, application and
execution run passed sixty-eight cases with one existing skip. Scoped mypy for
catalog, real-session factory, application and launcher modules passed, as did
Ruff and all nine documentation checks.

The default catalog `open_candidate` and writable/idempotent-create paths remain
unchanged. This explicit path supplies the native claim/profile seam needed for
deferred Resume composition; selecting it in default LMUX/AppHost, retaining
first-input identity, admitting current authority and effects, and publishing
the activated runtime still remain required. These tests do not establish a
full scoped multi-client or default launcher Resume flow.

### Resource preview foreground priority and cleanup

The original Resource preview task scope now dispatches through a priority queue
on its existing two native workers. Foreground requests run before queued
background work. A foreground reference to the same workspace, owner state,
subject, policy and budget promotes the existing job; it does not repeat its
scan or produce new selection evidence. ResourceLoader Session views and
`plan_coding_resume_async` forward this scheduling input without including it
in Plan identity or current authority.

The process remains bounded to eight admitted jobs. At most six may be
background jobs, preserving two admission slots for foreground preparation.
Promotion releases a background reservation while retaining the total-job
reservation until actual native completion. Already running work is never
interrupted or restarted. Caller work-unit and wall-time budgets are unchanged.

Cancelled jobs and fenced owner work are promoted for cleanup so sustained
foreground requests cannot indefinitely delay temporary read-pin disposal.
Cleanup still runs in the original native callback, and `aclose` waits for its
actual completion. Priority does not replace the existing cancellation flag,
submission publication gate, reference limits or source validation.

Queue submission can throw after native dispatch admission. The scheduler
removes only that submission's still-pending operation; an unknown queued
dispatch callback may service an already admitted peer. The original scope
publication gate prevents the failed submission from reading source content,
disposes its pins and fences new work. Existing accepted peers keep their
completion callbacks and total reservations.

The pre-change preview/Plan baseline passed twenty-five non-live cases. New
regressions fill both native workers, queue background work, and verify a
foreground Session view runs first or promotes one shared scan. They also fill
six background slots, admit two foreground jobs, reject a ninth job, preserve
an admitted peer across a lost native submission receipt, and close a cancelled
background owner while a foreground peer remains blocked. Foreground and
background Plan envelopes have the same identity for unchanged input data.

The final integrated preview-task, Coding Plan and ResourceLoader run passed
sixty-four non-live cases. Scoped mypy for all four source modules, Ruff and all
nine documentation checks passed. These are scheduling and regression results,
not release startup latency measurements.

This proves Resource-owned scheduling and lifecycle behavior, not production
Resume invocation, current subject or policy grants, cross-loader Workspace
deduplication, completed Plan caching or first-message performance acceptance.
Embedded/TUI, default Hosted activation and release evidence remain pending.

### Read-only initial Model Outcome observation

`observe_coding_resume_model_outcome` correlates one exact, selected-path Resume
UserMessage with the original Model Input snapshot and native
`project_model_call_invocations` terminal projection. Input lookup identity is
the complete persisted record digest, including Binding, parent and timestamp.
The initial snapshot must anchor to that UserMessage leaf, use Coding's same
conversation and main purpose, and identify one unambiguous invocation. Native
outcome snapshot references must match exactly. Repeated input identities or
multiple anchored snapshots are conflicts, rather than latest-success selection.

The result contains only logical input/record IDs, invocation ID, one snapshot
ID and `observed_completed`, `observed_failed`, `observed_cancelled`, `unknown`
or `conflict`. These are historical observations of the initial model call,
not whole-turn completion, current admission or retry permission. Missing
snapshots, prepared-only invocations, unknown outcome schemas, mismatched
references, copied foreign-conversation snapshots, compaction and other users
remain unknown. Neither an AssistantMessage nor an input commit proves model
completion. The original required Model Input codec remains unchanged: an
unsupported required version is rejected by that reader, not implicitly adopted.

The Hosted catalog's explicit `preview_resume_model_outcome` uses its original
bounded snapshot and source/closing fences. It reads fresh data for a current
discovery reference; a stale reference is rejected. It does not use a cached
display or acquire a Writer/Runtime. Calling services still own current read
authorization; no new remote profile or submit capability is negotiated here.

The pre-change logical-input/publication baseline passed twenty-three cases.
Five original offline API-adapter dispatch cases passed outcome correlation for
completion, provider failure, caller cancellation, Host abort and revocation at
the snapshot commit barrier. The last case persists a snapshot without invoking
transport and remains unknown. Actual snapshots anchor to the fixed resumed
UserMessage record. Existing repeat-dispatch rejection and one-UserMessage
invariants continue to hold.

The integrated fresh-reader projection, logical-input lookup and Hosted catalog
run passed thirty-five non-live cases. Sixteen projection cases include restart
reads, selected branches, duplicate input/snapshot identities, digest and outcome
reference conflicts, other conversations/users/purposes and unknown payload
observations. The unknown required-snapshot projection case uses a detached
in-memory mutation because the original file codec refuses to encode that
unsupported version; it is not future-version reader compatibility evidence.
File bytes remain unchanged. Scoped mypy for both source modules and Ruff passed.

This supplies observation needed by recovery but does not authorize automatic
retry or complete crash recovery. Default production activation, scoped Hosted
outcome delivery, first-input deduplication, current policy/effect settlement,
Embedded/TUI and release/performance evidence remain required. Goal and Issue
#696 remain incomplete.

#### Initial outcome ordering and later replay

The initial-outcome observer also checks anchored snapshots across the whole
selected descendant path. A replay of the same input after a later UserMessage
is a conflict, even when the earlier invocation completed. A sole anchored
snapshot after that later UserMessage remains unknown. A matching terminal
Outcome that precedes its prepared snapshot is unknown. The native generic
Model Call projector remains unchanged; these are Coding's narrower Resume
association rules.

Both wrong-order and later-replay regressions first reproduced false completed
observations. The updated fresh-reader observation and logical-input lookup run
passed twenty-three non-live cases, including both new cases. Scoped mypy and
Ruff passed. This strengthens historical evidence and still grants no retry or
current execution authority. Default activation and the full R2.1 delivery
remain incomplete.

The original offline completed-dispatch case also passed with these narrower
association rules, and all nine documentation checks passed.

#### Embedded history preview native-read settlement

The real Coding Continuity preview now uses the existing native I/O settlement
helper for Header, selected history, large-file tail fallback, and asset-health
reads. Cancellation retains the submitted read through actual completion. When
the preview is called through the original stable Continuity reference, root
shutdown consequently joins the native read before disposing the binding. A
second cancellation does not release that ownership or resubmit the read;
references arriving after root closing fail before reaching the reader.

Two blocked-native-read regressions, for Header and selected-history reads,
first reproduced premature reference retirement. Both pass after the change,
including repeated cancellation, concurrent root shutdown, stale-reference
rejection, one reader invocation, unchanged transcript bytes, and no prepared
Writer. The complete Continuity test file passed thirty-six non-live cases.
Scoped source mypy and Ruff passed. Existing byte limits and tail display
semantics remain in force. Cancellation and provider timeout can finish only
after submitted native I/O settles; this is ownership evidence, not a native
I/O latency guarantee or a performance measurement.

This change reaches the production Embedded history-preview path. It does not
connect the Resource Catalog scheduler to transcript reads, switch the default
restore operation to a read-only session, or supply first-input activation.
Full R2.1 delivery, Goal, and Issue #696 remain incomplete.

#### Reopened Binding does not restore current admission

The ordinary Coding activation guard now checks the selected current-Session
Binding after validating historical attempt settlement. A bound input can be
durably committed while the process that held its current admission has ended.
Reopening that file therefore returns `runtime.current_admission_required`
before ordinary Product runtime selection or another message append. A readable
Binding and a historical Model Outcome cannot recreate current authority.

The locally published candidate retains the original exact-input and original
Writer proof. Its guard requires that proof to match the selected Binding;
switching to another Binding cannot borrow an earlier publication. The existing
publication-pending fence still runs first. Source-Session Binding copied into a
fork remains historical origin under the original projector's identity rules.
Existing revision caching remains unchanged for ordinary messages without new
Binding metadata.

The reopening regression first reproduced an ordinary guard accepting a bound
input without local current proof. It exercises the real fixed input commit,
file close and reopen, read-only history observation, a Product-selection
sentinel, and an attempted subsequent write, with unchanged canonical bytes.
This closes an admission bypass in the existing production guard; it does not
provide the missing activation coordinator or default read-only restore route.
Full R2.1 delivery and Issue #696 remain incomplete.

Validation passed sixty-three non-live Binding and runtime-publication cases,
including original offline prepared-model dispatch and cancellation/error
boundaries, plus scoped source mypy, Ruff, and all nine documentation checks.

#### Embedded runtime owns detached history reads

`AgentSessionRuntime.preview_resume_history` is a read-only data entry using the
original discovered-source resolver and bounded Coding snapshot reader. It
accepts an exact path or discovered identity and an explicit selected leaf,
preserves historical cwd without repair, and returns a preview rather than an
Agent Session. It never calls the configured Product session factory, loads a
Writer, imports a compatibility file, or replaces the current lifecycle Session.
The original terminal history projector can consume its selected records with
no live Tool resolver. The real Embedded Coding Continuity provider routes its
bounded selected-history snapshot through this owner entry, retaining its
existing summary/source revision checks. Other continuity runtime adapters
keep the prior cancellation-atomic reader path.

The runtime retains at most two submitted reads. Cancelling an observation
waiter releases that waiter promptly but leaves its native read with the root;
it does not free admission capacity early. Root disposal fences new reads,
performs the original lifecycle disposal, and joins actual read completion
before closing the transcript factory. A cancelled root close retains this
join. Results arriving after the fence are rejected, as are files whose source
revision changed between the bounded read and delivery. Read errors left by
cancelled waiters are observed by the completion callback.

This establishes the Embedded owner entry needed for fast history opening. The
default CLI resolver and Continuity activation still restore an Agent Session
eagerly, and no TUI current-session replacement, initial activation coordinator,
or background Plan scheduling is supplied by this entry. Those production
connections and the full R2.1 release evidence remain required. Goal and Issue
#696 remain incomplete.

The new owner and production Continuity integration run passed forty-six
non-live cases. The new fixtures combine retired composition, changed
capability profile, and deleted historical cwd. They cover both path and
discovered identity, original owned and unowned runtime configurations,
selected terminal projection, unchanged directory contents, stale source
delivery, cancelled waiter retention, capacity accounting, cancelled root
close, and rejection after closing. The final stale-delivery case passed after
aligning its exception with the existing preview's read-error handling. Scoped
mypy for both changed source modules and Ruff passed.

The earlier owned-runtime and Agent-runtime regression run also completed:
one hundred fourteen non-live cases passed. It included the initial detached
history owner tests and the existing runtime lifecycle coverage.

#### Initial input uses native Request Evidence commit coordination

Coding's `_commit_resume_first_user_input` now joins the prepared current
candidate, exact staged payload, original Writer, and current admission before
calling `AgentEventRouter.commit_prepared_user_message`. The router uses its
original metadata preparation and append path, including Request Evidence and
Product metadata collision checks. The staged Manager supplies the fixed
record ID and inline Binding to that same physical UserMessage record. The
Request Evidence owner records the definite commit using the returned canonical
record ID. No Agent event, model run, recovery, or Runtime publication occurs
through this persistence entry.

The initial Coding entry is claimed once before the append await. A lost ACK,
cancellation, or failure after claiming leaves execution fenced and requires
lookup/recovery; calling the entry again cannot prepare metadata or append
another input. Exact staged-input checks run before metadata callbacks. The
candidate, Writer proof and current admission are rechecked after commit. A
revocation during the append can therefore leave a committed input without
making the candidate executable.

The original UnitOfWork retains its existing exact-record/operation-ID
idempotent verification on Store uncertainty. That native behavior is distinct
from submitting another input or replaying a model call. Fault evidence checks
identical full records, expected revision and operation ID across native
attempts, one canonical persisted user record, authoritative input lookup, and
rejection of a second Coding submission. The native Store and UOW algorithms
remain unchanged.

The Resource evidence fixture is prepared and bound by the original Request
Evidence runtime using its existing typed loaded-Skill fixture. It proves
metadata co-commit and canonical record association, not production Skill
preflight, current Resource generation pinning or authority admission. The
existing offline model cases use this new input entry before original
publication and prepared-model dispatch.

Default Embedded/Hosted first-input coordination, live policy and native epoch
settlement owners, logical input event publication, release compatibility, and
performance evidence remain required. Goal and Issue #696 remain incomplete.

Validation: the publication/dispatch and native Event Router run passed
thirty-two cases with one new fault-test assertion failing. Source inspection
confirmed the original UOW's fixed-ID verification; the assertion was corrected
to check exact request identity and one physical record. All five new
input-commit/evidence cases then passed, including the previously failing
unknown-ACK case. The existing eighteen publication/dispatch cases also passed
with the new input entry. Scoped mypy for all three source modules, Ruff and
all nine documentation checks passed.

#### Initial input uses native prompt and Skill preparation

Coding's `_prepare_resume_first_user_input` now delegates to the original
PromptController's preparation entry, which reuses Resource prompt preflight,
Request Evidence preparation and native UserMessage construction. This entry
does not queue input, invoke a command, commit history or dispatch a model.
Recognized builtin and extension commands are rejected through the existing
command matchers before Resource preparation. Extension command execution
remains disabled in the original preflight call.

Preparation requires the same locally verified intent, exclusive Writer and
current candidate as input commit. Current admission is checked before and
after the Resource await. The preparation is claimed once; cancellation or
failed post-await admission discards its native evidence owner and fences
execution preparation. The prepared native message's full input digest is
retained locally. Input commit rejects a different payload even if that
different payload was subsequently staged in the Manager.

A real workspace `skills/review/SKILL.md` fixture now exercises the current
Catalog and Resource owner instead of constructing a loaded-Skill result.
Its expanded native message and observed source-byte digest are committed
through the original Request Evidence owner alongside the inline Binding.
The committed canonical record is independently found by logical input lookup.
Boundary cases cover revoked admission after reading, cancellation during
preflight, repeated preparation, command isolation and substituted staged input.
Admission callbacks remain test validators; these cases do not establish
production actor-policy admission, approval or epoch settlement.

Validation: eighteen non-live publication/preflight and native PromptController
cases passed. Scoped mypy for both changed source modules, Ruff and all nine
documentation checks passed.

#### Permission expansion borrows native Approval confirmation

The original InteractiveApprovalResolver now issues and validates bounded,
ephemeral exact-action confirmation facts. A current matching native grant or
retained Policy rule may satisfy a request; otherwise an accepted interactive
response is required. Headless fallback's plain allow does not issue a fact.
Once-only approval remains bound to that one action and is not generalized
into Tool authority. Native grant/rule revocation is rechecked at each borrow.
Copied facts, another owner, changed requests, released facts and reopened
closed Sessions cannot validate the original confirmation. Cancellation and
denial remove reservations without retaining confirmation. The owner admits
at most sixty-four outstanding confirmation actions.

Coding's permission confirmation request binds the immutable activation
attempt's target Session/leaf, ancestry, Plan, candidate epoch and subject,
together with bounded owner-observed expansion codes. The optional native
session-grant proposal includes a fingerprint of all these fields. Coding's
borrower re-creates that exact request and validates it through the issuing
Approval owner. No new approval store or durable confirmation journal is
introduced. This is a permission-expansion prerequisite, not a computation of
current subject/Policy authority or native epoch/effect settlement.

The real native Skill/Resume fixture now obtains interactive confirmation
before acquiring its Resume Writer. It checks unchanged history bytes during
confirmation, then uses the original owner's current validation through
bootstrap, graph preparation, Skill preflight, input/evidence commit and
publication. Revocation after Skill reading prevents input commit and removes
pending evidence. Revocation after publication rejects native model preparation,
compaction, shell and extension execution entries. Epoch settlement in these
fixtures remains a test validator; the default Embedded/Hosted continuation
coordinator and actual current actor/Policy owner wiring remain pending.

Validation: one hundred twelve non-live cases passed across native Approval,
multi-agent approval lifecycle, Hosted approval presentation, Coding request
binding and both real Resume integration cases. This includes once/session
confirmation, safe grant reuse, coalesced-request distinction, capacity,
changed actor/candidate/scope/leaf/subject and owner closure. Scoped mypy for
the three changed source modules and Ruff passed.

Both final cancellation/close delivery cases also passed with explicit rejection
of action-ID reuse before the original waiter settles. Invalidated reservations
remain bounded until that waiter releases them, so its cleanup cannot erase a
new confirmation. All nine documentation checks passed.

#### Initial continuation has one Coding coordinator

`prepare_coding_resume_continuation` now sequences the original owned Writer,
fixed intent, current bootstrap, candidate graph, native prompt/Skill
preparation, inline Binding and Request Evidence commit, and local Runtime
publication. It returns the original AgentSession and canonical input record
for the Product's existing slot/binding owner to adopt. It does not replace a
Product slot, invoke normal prompt, dispatch a model or retry any stage.
Current admission is required before Writer acquisition and is rechecked after
acquisition and throughout the existing owner entries. Current epoch/effect
settlement is required after graph preparation, after input preparation and by
the original publication owner. Its callback cannot return a truthy receipt or
an unawaited coroutine as admission.

Before intent or Runtime effects, the admitted Writer rejects an existing
physical record identity and a known logical input ID on the selected Session
ancestry. A regression first demonstrated that a new Plan and new physical
record ID could otherwise duplicate an already saved logical input. The new
fence requires recovery lookup instead; the second attempt leaves bytes
unchanged and prepares no graph. This does not implement the Hosted client
registry or absence proof for an input from another branch or service restart.

After definite commit, the coordinator delivers the original full-record
digest as a native input lookup query. The same identity is available from the
original staged record on an unknown commit outcome, and from the original
committed record after a post-commit failure. This data is not permission,
Runtime readiness or model-outcome evidence. A receiver failure does not cause
redelivery, input replay or publication. A fresh bounded native history read
and original model-outcome observer recognize the exact persisted input while
conservatively leaving its model outcome unknown.

Failure disposes the undelivered original Session/Manager, retaining committed
history and cancellation semantics. If that cleanup fails, the coordinator
fences the original Transcript factory and raises a cleanup-debt exception
that retains the original owner and both failures. Its retry entry calls that
same owner's disposal; it does not create another Writer or reopen the factory.
The Product root must retain this debt and close/restart its affected owner.
Pending draft display, adoption, event delivery and retry disposition remain
with the upcoming Embedded/Hosted callers.

The coordinator fixtures use a real native interactive permission confirmation,
owned persistent Writer, current standard composition and actual Skill bytes.
They cover pre-Writer denial, graph/read revocation, cancellation, unsettled
effects, fixed-ID native UOW verification on unknown ACK, post-commit publication
revocation, identity receiver failure and cleanup debt. Current epoch settlement
is still a test validator. Default Embedded/Hosted callers, actual live actor
and Policy/epoch owners, background scheduling/cache/performance, release
compatibility and final delivery remain required; Goal and Issue #696 remain
incomplete.

Validation: twenty non-live coordinator and native permission-binding cases
passed. Initial entry absence, unretained cleanup failure and duplicate logical
input cases were demonstrated before their fixes. The duplicate fixture's
initial Writer assertion was corrected to recognize the already closed prior
Writer before confirming the new candidate. Scoped mypy, Ruff and all nine
documentation checks passed.

#### Bootstrap cleanup debt retains the complete candidate

The Resume bootstrap's final-admission failure now shares the same Coding
cleanup-debt contract as the continuation coordinator. If the original
constructed AgentSession cannot be disposed, the debt retains that exact
Session, the admission error and cleanup error, and fences its original
Transcript factory. Retrying disposal through this owner preserves graph,
Product and Writer ordering. This is a complete constructed-candidate case;
partial constructor failures still use their original preparation custodians.

The continuation coordinator passes an existing bootstrap debt through without
disposing its Manager separately. A real standard-composition fixture revokes
native interactive confirmation immediately after original construction,
injects one native disposal failure and verifies that the Manager has not been
disposed before the retained Session's cleanup retry. No graph preparation or
UserMessage commit occurs in that case. The existing later-publication cleanup
failure uses the same contract. Product-root debt retention and default
Embedded/Hosted adoption remain required.

Validation: the new bootstrap failure was reproduced before the fix. Nineteen
non-live bootstrap/coordinator regressions passed, followed by both nested
bootstrap and later-publication cleanup-debt cases. Scoped mypy for all three
source modules and Ruff passed.

#### Native application Root retains preparation and delivery

`AgentSessionRuntime.prepare_resume_continuation` now uses the original Root's
owned Transcript factory and Product application selection. Product borrowing
occurs after the current admission and definite intent commit. Resume Bootstrap
rechecks admission after borrowing and retains the original unbound factory or
complete Session cleanup route on failure. Session disposal releases its native
Product runtime lease without closing the application's epoch owner. Ordinary
Session construction shares the same borrowing helper and retains its existing
unsettled-Resume rejection.

The Root prepares an original `PreparedSessionLifecycleOperation` through its
existing lifecycle runtime. The returned `CodingRuntimePreparedResume` exposes
Root-owned `consume` and `abort` operations alongside the canonical committed
input lookup identity. It does not submit a normal prompt or dispatch a model.
Its candidate is bound to the original runtime host before delivery to the
caller, so the native model transport's current-Session predicate rejects it
before the original lifecycle installs that exact Session in the Root slot.
Current admission also checks the previous slot until the native operation's
delivery marker, and the exact candidate slot after that marker. A changed slot
invalidates preparation or delivery.

Preparation and delivery tasks remain Root-owned through cancellation. Root
close first fences admission, cancels and joins those tasks, then aborts native
undelivered operations and retries retained complete-candidate cleanup debts.
Failure to settle a candidate prevents closing its dependent Transcript and
Product factories; the same original operation or debt remains available to a
later Root close. Native lifecycle disposal uses its original post-shutdown
entry, while coordinator cleanup retains the original Session disposal entry.
The native lifecycle still owns current Session replacement and retirement.
If retirement of an already delivered Session fails, Root close also stops
before dependent factory close. The original lifecycle retains that retirement
for the next close attempt; Product epoch guards remain defense in depth.

Regression fixtures use real owned Writers, native lifecycle operations and
interactive permission facts. They cover exact Session delivery, pre-delivery
model ownership, committed input identity, abort, changed current slot,
cancellation during preparation and delivery, confirmation revocation before
delivery, failed Host binding, failed native abort, delivered retirement failure
and retained cleanup debt.
Effect-settlement callbacks in these fixtures validate orchestration only.

This is an explicit Root entry. Default CLI/TUI and Hosted callers have not yet
been switched to it; actual current actor/policy comparison and external effect
settlement remain mandatory production work. Caller-supplied construction
options, Worker support and released-version provenance still need their full
delivery acceptance evidence. Issue #696 and the full Goal remain incomplete.

Validation: missing Root preparation was demonstrated before implementation;
the delivered-retirement fault demonstrated a dependent Product close attempt
before the ordering fix. Forty-three non-live Root, continuation, bootstrap,
history and Product revision regressions passed. After the retirement fix,
all eleven Root scenarios and four existing owned-runtime cleanup cases passed
(15 tests). Scoped mypy, Ruff and nine documentation checks passed.

#### Root first input executes through the original Model Input transport

`CodingRuntimePreparedResume.run_first_input` delegates to the original
Session's committed-input entry only after its native lifecycle operation was
consumed and the Root still holds that exact Session. A closed Root, an
undelivered operation or a replaced current slot is rejected before the native
dispatch claim. This leaves an undelivered candidate's committed input and
dispatch claim unchanged. The UI can complete native delivery and rebind its
presentation before calling this separate entry.

The existing native Session owns the Host claim, Model Input snapshot and
transport barrier, once-only dispatch, and cancellation. The Root entry does
not submit a normal prompt, append another UserMessage, create a second model
loop, or provide automatic replay after failure or uncertainty. Current native
permission confirmation and mandatory effect-settlement checks remain active
at the original transport boundary.

Real owned-Root fixtures register an original AI API adapter and invoke prepared
transport. They verify the committed input and lookup digest, exact legacy
Header preservation, one main input snapshot, the original model outcome, and
no duplicate user append or transport invocation. Revocation before dispatch
prevents snapshots and transport; revocation after snapshot commit prevents
transport while retaining that snapshot. Provider uncertainty and cancellation
prevent another invocation of this input. An `observed_failed` native model
outcome records local invocation failure; it is not proof of absent remote
effects or a replay grant.

Standard-composition fixtures modify Skill or AGENTS bytes after pure history
preview. The actual provider request uses the current bytes. Skill Request
Evidence carries the current content digest on the same fixed UserMessage,
while the original Header and Session identity remain unchanged. These tests
exercise the explicit Root entry; default CLI/TUI and Hosted startup, actual
current actor/policy comparison, external effect recovery and background
performance remain incomplete.

Validation: the missing Root first-input entry was reproduced before the fix,
after correcting the fixture's native API registry cleanup call. All nine
non-live prepared-transport scenarios passed, including current Skill/AGENTS
bytes and exact original Header checks. Scoped mypy, Ruff and nine
documentation checks passed.

#### Explicit history screen binds the original Resume lifecycle

`build_coding_resume_history_screen` presents the selected native history through
the existing screen application and transcript projector without creating an
Agent, acquiring a Writer, or preparing model input. Quit does not activate the
Session. The first continuation input calls the supplied current-admission
preparer, consumes the original Root lifecycle operation, installs the persisted
history, subscribes to the exact delivered Session, and invokes the original
committed-input transport. It does not echo or append that input again.

The original Root now offers a transient history-view intent scope. Before
Writer preparation it checks the displayed canonical target, Session identity,
selected ancestry and source digests against the preparer's plan. Its current
view callback also fences a closed or cancelled display through native delivery.
This scope adds an intent restriction; it grants no actor, permission, epoch or
effect authority. Original current-owner checks and Writer freshness checks
remain mandatory. After native delivery the original current-Session and actor
checks govern subsequent inputs.

A regression initially demonstrated that checking the target only after
preparation allowed a faulty preparer to commit input to another history file.
The Root restriction rejects that mismatch before either file changes or a
Product owner is acquired. A preparer that swallows cancellation before entering
the Root is likewise rejected after the history screen closes. Subscription
failure disposes the delivered Session through the original Root; cancellation
and pre-delivery failure abort the original prepared operation. Retained cleanup
debt remains with its native owner.

The screen retains canonical input lookup data for uncertain commits and refuses
another preparation or normal prompt after a failed first continuation. This is
not a recovery or replay grant. Fixtures exercise original native Writers,
interactive confirmation, Root lifecycle and model transport. Their effect
callbacks validate orchestration only.

This entry is explicit and requires the caller's original approval surface and
current-admission preparer. Default CLI/TUI startup and Hosted/LMUX routing,
production actor/policy comparison, external effect settlement and recovery,
background invocation/cache/performance, and released-version acceptance remain
unfinished. Issue #696 and the full Goal remain incomplete.

Validation: the combined run passed 78 history, Root, transport, import and
transcript regressions; its two failures identified the new module exceeding
the existing UI manifest and adapter budget. The product interaction entry was
moved to `coding.interaction`, preserving both gates. All eight history-screen
scenarios and both previously failing gates then passed (10 tests). Scoped
mypy, Ruff and nine documentation checks passed. The cancelled-view fixture was
also corrected after its erroneous branch had left a test waiting without
issuing cancellation; no Product timeout or sleep was added.

#### Resource owners share matching in-flight Workspace scans

The existing Resource preview task scope now finds matching running computation
across loader scopes on the same event loop. The key retains Workspace, subject,
policy, exact captured Resource input state and work budgets. It shares no
Future across event loops and caches no completed value. Distinct package read
handle identities remain separate rather than assuming equal authority from
equal paths or digests.

Each original scope retains its own references and native completion route.
Closing one scope fences that scope and joins actual computation/pin settlement;
an open peer's reference prevents cancellation of the shared job. Cancelling
one waiter releases only its reference. Foreground peers promote the same
native job. The process-wide admission bounds remain eight jobs, six background
jobs and two native workers; all shared scopes together have at most 64 waiting
references per job. Registry entries disappear on actual native completion;
they are neither a second lifecycle owner nor an authority cache.

Regression-first tests reproduced duplicate computation by distinct loaders.
The fixtures also corrected a scan counter that had counted their independent
synchronous verification read. Five cross-loader cases now cover shared work,
creator close, single-waiter cancellation, policy isolation and subject
isolation. All 34 Resource scheduler and Coding Plan regressions passed. Scoped
mypy, Ruff and documentation checks validate this increment. Production
background invocation, completed-value freshness/cache design, broader package
deduplication and cold/hot performance acceptance remain unfinished.

#### Runtime selection rechecks the original Product Workspace/epoch witness

`AgentSession._require_current_coding_runtime_selection` now rechecks its
original factory-issued Workspace witness before inspecting Plugin selections.
The witness calls the original factory's Workspace identity check and retained
native Product epoch owner's current-root/cutover checks. It runs for minimal
composition too, where there may be no selected Plugin manifest to trigger a
Product check. No detached composition receipt or historical Binding replaces
this live owner check.

Fault injection first demonstrated that replacing the actual Workspace inode,
with Transcript storage outside that Workspace, still allowed first-input
transport. Replacing the actual native epoch control root also allowed
transport. Both now fail before a dispatch claim or Model Input snapshot. The
fixture restores the original directory before native cleanup, preserving the
same original owners and testing their real filesystem checks.

A further case replaces the epoch control root immediately after the native
Model Input snapshot commit. The original transport barrier rejects the new
root before provider invocation, retains the committed snapshot and blocks a
second first-input dispatch. It grants no replay after restoration. Nineteen
Root first-input/history-screen cases and this additional transport-barrier
case passed. Scoped mypy, Ruff and documentation checks passed.

This closes a live Product identity gate; it does not compute current actor or
permission differences, prove Plugin/Worker external effect settlement, or
derive the activation attempt's production epoch fingerprint. Those owner
producers, default CLI/TUI and Hosted routing, recovery and the remaining
background/release/performance acceptance are still required by Issue #696.

#### Resume permission confirmation binds the observed execution scope

The original Harness Authorization module now compares native execution scopes
without issuing authority. It identifies readable/writable expansion, weaker
network restriction and removed denied subtrees, including partial removal of a
denied subtree. Entirely denied current roots and baseline denials outside the
current scope do not falsely count as expansion. An absent baseline is unknown.
Inputs are bounded to 64 roots per field. These are abstract scope comparisons;
historical restrictions and a non-widening result grant no current permission.

The existing Coding Resume request can bind this native scope and its observed
baseline. It adds the owner-computed expansion codes without dropping other
unknown-authority codes, and includes reviewable current scope data plus bounded
scope fingerprints. Scope serialization is capped at 16 KiB; the combined code
budget remains sixteen. The original Approval owner still issues and rechecks
the exact fact. A scope-bound borrower must receive the current native scope at
every revalidation; omission, changed scope, rebound wrapper fields or native
revocation rejects the borrow. No approval store or journal was added.

The original Process launcher now exposes its frozen execution-profile ceiling
as data. Root first-input fixtures compare the confirmed native Workspace scope
with this actual original gateway ceiling and recompute the current Workspace
scope at every admission boundary. The initial assertion against Sandbox
ExecService was corrected: when Sandbox is disabled that service's profile can
be absent, even though the original process authorization gateway retains its
ceiling. This evidence does not establish OS containment or external effects.

The missing Authorization comparison and scope-binding request were reproduced
before implementation. Native Approval fixtures cover changed readable,
writable, network and denied scope, omitted current scope and revocation. Root
transport fixtures use the real native gateway, Writer, fact and transport.
Default CLI/TUI and Hosted actor/Policy producers, trusted configuration proof
reuse, formal effect settlement, recovery, production background invocation and
release/performance acceptance remain incomplete. The full Goal remains active.

Validation: the combined Authorization/confirmation/Root run passed 41 cases,
including all twelve actual first-input transport scenarios. After adding nested
denial and bounded-root/byte cases, all 33 Authorization and confirmation tests
passed. Scoped mypy passed four source files; Ruff, diff whitespace and all nine
documentation checks passed. Effect-settlement callbacks in the Root fixtures
still validate orchestration only.


#### Resume confirmation observes native current Policy inputs

The original native PolicyEngine now exposes a bounded fingerprint of its
ordered rule configuration. It limits each rule field to 256 entries and the
encoded document to 16 KiB. The original PermissionProfilePolicyEvaluator
combines this observation with the current requested/effective profile and
native ceiling. These hashes describe configuration dependencies; they grant
no actor admission or Tool authority and identify neither executable code nor
external effects.

The native Workspace selection already read live permission profiles and
ceilings, but retained managed rules from selection time. A regression first
showed that a newly configured blocked Bash rule changed a fresh selection
while the existing native evaluator kept its old fingerprint and behavior.
The default selection now reads managed rules from the same settings owner
for observation and evaluation. The selected evaluator honors the new deny.
Injected custom policy factories keep their existing contract and require
an owner-specific observation entry rather than inferred native identity.

Coding Resume may bind this native Policy observation in the original Approval
request. Revalidation requires explicit current native Policy inputs and
rebuilds the exact request for the issuing resolver. Changing the profile,
changing managed rules, omitting current Policy, or changing configuration
while the native confirmation awaits rejects the old fact. A hash alone does
not replace the existing actor, execution-scope, Product or settlement gates.

Root first-input fixtures pass the actual selected native evaluator to the
original candidate factory and observe fresh Policy through the same native
settings entry at each admission boundary. A real settings profile change
before first-input dispatch prevents a snapshot and provider call. Adding a
managed deny immediately after the native snapshot commit prevents provider
transport, preserves that snapshot and rejects a second dispatch. Existing
Workspace/control-root, skill/AGENTS, revocation, cancellation and transport
outcome cases remain covered with the original owners.

Validation: 117 Root first-input, PolicyEngine and Workspace-profile cases
passed, including fourteen Root transport scenarios. Ten existing Workspace
tool/selection cases passed. Native Policy and confirmation tests also cover
waiting-period changes and missing current inputs. Full production actor and
epoch/effect producers, default Embedded/Hosted routing, recovery, background
invocation/cache/performance and released provenance acceptance remain
incomplete; the full Issue #696 Goal remains active. The Root fixture's effect
callback still verifies orchestration only.


#### History-screen failure recovery reads the original saved input

The explicit native Resume history screen now uses its retained exact input
lookup query to re-read the discovered target through the original Root history
entry after first-input failure. It verifies the original Header and selected
ancestry prefix before projecting the native Model Input/Outcome observation.
Confirmed saved-input presence refreshes the displayed persisted history, so a
failed event subscription or revoked confirmation no longer leaves a committed
first input invisible. No replacement Agent, Writer, lookup journal, model
request or approval fact is created.

The display distinguishes an unknown model result from a recorded terminal
outcome. A recorded failed call is historical evidence, not proof that a
provider performed no external work. Missing input remains unknown; it does
not prove non-commit. Identity conflict, unreadable/stale source or changed
history cannot authorize retry. Subsequent prompt submissions remain fenced
and do not append another input or dispatch again.

A native first-input failure that leaves execution unavailable now releases
its active Slot through the original Root after observation. Exceptions also
release the native prepared operation or active Slot if the recovery read is
cancelled again. The native Root retains its cancelled history reads until
settlement. A new fault injection pauses after the actual native read and
cancels the observation, then verifies the original Slot is gone.

The existing eight screen scenarios passed as baseline. The regression first
failed because revoked confirmation had no recovery observation. Added cases
cover an actual provider transport failure and cancellation during recovery.
This closes failure presentation and read-only observation in the explicit
screen entry. Default Embedded/Hosted routing, production actor/epoch/effect
inputs, restart reconciliation and admitted retry, background performance and
released-version acceptance are still required; Issue #696 remains active.

Validation: the combined screen/Model Outcome run covered 28 cases, with 25
passing and three failures caused by the test using `ErrorRecord.text` rather
than its native `summary` field. After correcting that assertion, all three
failed scenarios passed in the focused rerun. Ruff, scoped mypy, diff whitespace
and all nine documentation checks passed. The branch-wide `make plan-checks`
was inspected; its broader subsystem and platform gates remain delivery work,
not evidence supplied by these focused runs.


#### Native Hosted controller subject observation and exact confirmation

The original AppClientScope now observes the current Resume subject using its
own attachment/controller/member checks and the original canonical Session
owner. Its synchronous revalidation includes the Session's accepting state.
The fingerprint carries the selected execution application's native application
and service-instance identities, attachment generation, member, canonical
Product/continuity/Session and scope. Encoded data is bounded to 4 KiB; an absent
native execution instance is explicitly unavailable. No execution port is
selected, no execution binding/reservation is created and no Product callback
runs during observation.

Coding's permission request may borrow this exact native scoped owner and
control. The native owner requires the activation attempt's Session to match
the actual controlled Session before issuing a request. The owner selection
is itself bound into the exact request, so stripping those wrapper references
changes the original Approval request and cannot reuse its retained fact.
Revalidation consults the same live native controller before the original
Approval fact. Closing a scope, controller takeover while confirmation awaits,
wrong target, or a closed canonical Session rejects the borrow. Embedded
confirmation does not import Hosted owners merely to take its unbound path.

The original scope tests passed 23 baseline cases. Missing subject observation
and revalidation entries first failed two regressions. Native owner fixtures
then cover foreign scopes, takeover, closed scopes, Session close before mapping
removal, unavailable execution identity and zero execution binding. Cross-owner
fixtures use the original AppService scope and Approval resolver, covering
current confirmation, wrong Session, takeover before/after confirmation and
removing owner references. These tests observe actual native controller state;
their injected Hosted Product ports do not establish full Coding activation or
external-effect settlement.

This supplies a production Hosted subject producer and its exact confirmation
borrower. Wiring the default Hosted submit path and Embedded actor producer,
production epoch/content/effect settlement, restart reconciliation, background
invocation/performance, released compatibility and delivery gates remains
required. The full Goal and Issue #696 remain active.


G11 architecture validation also exposed an impermissible new direct
AppService consumer and branch-wide reviewability budget excess. The concrete
subject borrower now lives at the existing optional Coding Hosted execution
bridge. Default lookup remains on the ordinary Hosted binding path and does
not import or select optional execution. The original AppService Session owner
keeps accepting checks before and after lookup; its closed Product-result
validation uses the existing optional port module. Coding's existing catalog
and binding modules host their own pure identity/lookup/binding validation,
while the public adapter methods and original owners remain in place. No
budget limit was raised, authority owner split, new file hidden or wire shape
changed. These placements restore the existing G11 bridge and budget gates.

Validation: 62 controller/execution/confirmation cases passed before boundary
placement checks. Those checks identified the bridge and budget failures above.
After the adjustments, 113 confirmation, AppService controller/execution,
Coding adapter/catalog/execution and G11 cases passed. The final ordinary
lookup helper placement was separately revalidated by 67 confirmation,
adapter, scope and G11 cases. Scoped mypy passed all eight affected source
files; Ruff, whitespace and documentation validation passed. These focused
results do not discharge the branch-wide delivery and platform gates.

#### Native accepted execution task carries the current Hosted subject

The selected scoped submit route now borrows the original AppClientScope and
control at admission. The existing registry creates its accepted task in that
context and continues to own submission deduplication, execution and settlement.
The stable submission ID follows that same task; the registry-backed legacy
turn route carries no invented ID. The caller resets its borrow in `finally`.
Every Product getter revalidates the original live controller. A replacement
controller can inspect the original execution ledger without restarting work;
the old task cannot use its stale borrow for Resume confirmation.

A regression crosses actual native scope admission, execution registry and
guard task into the original Coding Approval resolver. Its activation attempt
uses the captured stable submission ID as request identity. Native takeover
then rejects the exact retained confirmation. The injected Product and attempt
leaf/epoch data remain fixtures: this does not establish default writable
history activation, production epoch/effect settlement or restart safety.

G16 scope reviewability required moving optional functions into the existing
Resume port module and binding them to the same original scope instance.
Controller/session tables and lifecycle checks remain with their original
owners. Local record profile selection is now a pure projection in the
existing closed profile algebra; record authentication and wire fields are
unchanged. No architecture budget was raised or test bypassed.

The combined controller/execution/confirmation, local-record and G11/G16 run
passed 113 cases and failed the local-record line budget while import placement
was still being adjusted. The final placement is checked separately below.
Scoped mypy passed eight source files. The broader Coding Wave A gate also
exposed a remaining G14 slice excess (1,854 lines against 1,516); it remains
delivery work. Default Embedded/Hosted routing, production activation inputs,
background invocation/performance, released compatibility and full delivery
gates remain required. Goal and Issue #696 remain active.

Final local-record/G16 revalidation passed all 41 cases after correcting the
profile module import (the intermediate facade import failed collection).
Ruff and the nine static documentation checks passed. The optional Coding
subject functions now share the existing execution-work bridge and retain
their public imports from `hosted_execution`; both existing files count in
the execution slice (248 and 133 lines, total 381 within 400, each within 250).
This placement adds no execution owner or default composition import.
After that final placement, all 70 scoped execution, Coding confirmation,
native Coding execution and G11 cases passed. Scoped mypy also passed the
three relocated/import-adjusted sources. G14 remains the identified failing
Wave A gate; the execution slice itself stays within its existing limits.

#### R2.1 Hosted slice accounting and broader AppService validation

The previous G14 aggregate limit was measured against its pre-Resume scope.
Reviewing the actual diff against control `main` at `2cb18a0b` identified
catalog +191 and Session binding +147 lines, with the Hosted CLI unchanged.
These are the detached history claim/factory path, bounded display, fenced
history/outcome and input observation, and narrow canonical/data validation.
Their placement retains the original catalog, factory and Session owners.
Moving these functions solely to evade a slice budget would obscure that
ownership. The existing G14 architecture document now records this exact
338-line increment. Wave A keeps its file partition and adds individual
catalog/Session/CLI ceilings alongside the 1,854-line aggregate ceiling.
Other budgets and dependency gates retain their existing limits.

The current Wave A test first failed on the measured 1,854/1,516 mismatch.
After the accounting change, combined Wave A, G11/G16 and native Hosted
catalog/Session/adapter regressions passed 57 cases, with one platform skip.
Ruff and nine static documentation checks passed. This closes the identified
G14 accounting gap, rather than claiming completion of the remaining default
Resume, effect-settlement, background/performance or release requirements.

The complete AppService quality target passed every Ruff invocation and mypy
over 94 source files. Offline uv initially lacked build-system cache, so the
gate uses the existing virtual environment with `UV_OFFLINE=1 UV_NO_SYNC=1`.
Its first test collection selected that environment's control-lane editable
source and failed 17 collections. Re-running the test phase with explicit
`PYTHONPATH=src` selects this task branch. The command retains `-m 'not live'`
and `--skip-host-runtime`; that full test phase is still running at this
checkpoint. It must reach a terminal result before being reported as passed.
