# Resume Compatibility And Background Activation Design

## Status

- Authority: descriptive — candidate design and delivery plan.
- Design status: proposed; design acceptance is separate from review completion.
- Implementation status: partial — read-only Header, bounded selected-path and
  unverified tail previews, exact-byte digest for bounded historical snapshots,
  historical Binding projection, fixed-ID UserMessage commit primitives with
  image externalization inside the existing Transcript owner, composition
  comparison, an internal fixed-ID activation-attempt record and Transcript
  commit path, a staged first-input path in Coding's SessionManager, and a
  data-only internal `SessionActivationPlanV1` envelope exist. Selected-path
  history projection classifies an unbound attempt as pending and keeps its
  pure Plan unavailable while still allowing read-only viewing. The ordinary
  persistent Session write path also stops at an unresolved attempt; a normal
  commit advances its checked transcript revision without rescanning history.
  ResourceLoader
  can calculate Catalog input facts and bounded native context content digests
  without choosing authority; Plan records only their redacted input fingerprint and
  rejects reuse when refreshed owner inputs differ. Skill and other mutable
  Resource content is not closed by this receipt, which cannot replace current
  owner selection. The staged first-input path is not yet armed by live Resume
  activation. Writable admission, owner selection
  completion, background scheduling, Hosted readiness, and release evidence
  are not implemented.
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

本轮落盘是候选设计与实施顺序，不接受新公共 API、持久化格式或跨 scope 依赖。
正式实施前，按 [governance profile](../architecture/governance-profile.md) 记录
受影响 owner 与 common-parent 的决定：恢复兼容契约、continuation 事务格式、
Hosted readiness/admission 的精确协议及旧版本回滚行为。

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
