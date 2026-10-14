# 测试去重实施记录

本记录是[测试与 PR 门禁重构方案](test-and-pr-gate-refactoring-plan.md)的实施证据，不能替代全量语义审查或远程性能验收。当前接受范围为下述已确认重复项与 AppHost Linux 同配置重复执行；其他项仍待审查。

## 0. 全仓完全相同函数体复核（2026-10-14）

在远端 `main` 的 `ed01d756` 上，对全部 `tests/**/test_*.py` 进行静态 AST
复核：保留函数参数、decorator 和函数体，只忽略测试函数名称及源码位置，再按
规范化 AST 哈希分组。没有发现可直接删除的普通 unit/contract 完全重复函数。
仅有两类完全相同函数体，均因执行配置不同而保留：

- Windows 与 POSIX epoch cutover 的并发收敛测试各验证独立平台实现，不能以函数
  体相同视为重复平台覆盖。
- DashScope/Moonshot 的 live stream/tools/complete 包装测试调用各自文件绑定的
  provider fixture，函数体相同但外部模型、协议和凭据配置不同；它们继续留在
  显式 live 路径，不进入 PR 门禁。

该扫描只证明没有“忽略名称后完全相同”的剩余低风险删除项，不证明近似实现、
参数矩阵或不同写法覆盖相同行为。后续语义去重仍须逐候选比较断言、fixture、
marker、平台和最终 collected node ID。

## 1. 全仓候选扫描

2026-10-14 扫描当前任务工作树的 1475 个 `test_*.py` 文件、13755 个静态 `test_` 函数定义。比较忽略位置和函数自身名称的完整 AST，保留参数、装饰器和函数体，发现 10 组候选。参数化实际运行数量、全局配置、共享夹具和被包含但不完全相同的断言不在这项扫描的证明范围内。

完成映射删除后以相同算法复扫，剩余 3 组：POSIX/Windows epoch 收敛各一项、五个 vendor live wrapper、两个 Kimi OpenAI stream/complete wrapper，均为下表已审查且保留的平台或 provider 变体。当前树不再有未处置的完整 AST 重复簇；这不代表近似 AST 或语义包含关系已经全仓审完。

| 候选 | 上下文核对 | 处置 |
| --- | --- | --- |
| AI `test_api_streaming.py` 的 register/get 两个 legacy signature 用例 | 同文件、同 provider、同 registry，实际都只调用 register 并检查相同异常 | 合并到 register owner |
| AI 同文件 optional legacy signature 两个用例 | 同一 `_LegacyProviderWithOptionalDebug`、相同调用与异常 | 合并到 register owner |
| 五个 vendor live 测试 wrapper | 各模块的 main、模型/协议和工具配置不同 | 保留；wrapper 相同不代表网络行为相同，不执行 live 验证 |
| 两个 Kimi OpenAI live wrapper | 分别调用 stream/complete 示例流程 | 保留；全局函数不同 |
| Coding 两个 UI 文件的 non-interactive 用例 | 两个函数体相同，均 patch 同一 mode 入口；两套 helper 对被断言的 runtime/current session/prompt 行为相同 | 删除 Screen 复本，保留聚焦的 UI mode owner |
| Coding session codec 的 native/read-only v3 rejection | 同文件、同 tmp_path 隔离、同 `load_session_repository`，并未调用不同入口 | 合并为原 native 用例 |
| Harness events/host 的 subscribe/unsubscribe | 相同 canonical 导入、无局部夹具、同父级 conftest | 仅 events owner 保留 |
| Harness events/host 的 scheduled listener serialization | 同上，相同事件栅栏、调度顺序与 drain 断言 | 仅 events owner 保留 |
| Harness events/host 的 no-loop rejection | 同上，相同定制错误与拒绝断言 | 仅 events owner 保留 |
| POSIX/Windows epoch concurrent convergence | owner、平台跳过条件、布局/ACL 配置不同 | 保留对应平台覆盖 |

## 2. 已实施的旧用例到保留集合映射

以下旧 node ID 可在基线提交 `1f1fcaf1` 中核对。已删除项均不携带独有参数、失败分支、平台或生命周期差异。

| 旧用例 | 保留用例 | 等价或包含依据 |
| --- | --- | --- |
| `tests/resource/test_frontmatter.py::test_harness_frontmatter_entrypoint_is_canonical` | 同文件 `test_legacy_resource_frontmatter_path_preserves_harness_owner_identity` | 同一 parse 函数身份断言被包含，其他导出/错误类型身份仍保留 |
| `tests/coding/test_session_file_codec.py::test_read_only_repository_rejects_session_v3_without_rewriting_source` | 同文件 `test_native_repository_rejects_session_v3_without_rewriting` | 完整函数体等价，均检验 v3 拒绝、错误码与原文件字节不变 |
| `tests/harness/host/test_events.py::test_ordered_event_bus_subscribes_and_unsubscribes` | `tests/harness/events/test_bus.py::test_ordered_event_bus_subscribes_and_unsubscribes` | 相同 canonical 类型、订阅/退订和监听状态断言 |
| `tests/harness/host/test_events.py::test_ordered_event_bus_serializes_scheduled_async_listeners` | `tests/harness/events/test_bus.py::test_ordered_event_bus_serializes_scheduled_async_listeners` | 相同受控 async listener，串行与 drain 行为完整保留 |
| `tests/harness/host/test_events.py::test_ordered_event_bus_no_loop_rejects_async_listener_with_configured_error` | `tests/harness/events/test_bus.py::test_ordered_event_bus_no_loop_rejects_async_listener_with_configured_error` | 相同无事件循环拒绝及定制异常信息 |
| `tests/ai/test_api_streaming.py::test_get_api_adapter_stream_rejects_legacy_provider_signature` | 同文件 `test_register_api_adapter_rejects_legacy_provider_signature` | 两者构造同一 `_LegacyProvider` 和空 registry，均只调用 `register_api_adapter` 并断言相同 TypeError；旧名称未经过 get/call 路径 |
| `tests/ai/test_api_streaming.py::test_get_api_adapter_stream_rejects_legacy_optional_arg_signature` | 同文件 `test_register_api_adapter_rejects_optional_legacy_argument_signature` | 两者构造同一 optional-debug provider，调用与异常断言完全相同；无独有 get/call 行为 |
| `tests/coding/test_screen_coding_tui_mode.py::test_run_coding_tui_non_interactive_keeps_plain_prompt_loop` | `tests/coding/test_ui_mode.py::test_run_coding_tui_non_interactive_keeps_plain_prompt_loop` | 两个函数体完全相同，均 patch 同一 mode 入口并断言非交互分支、prompt 与参数集合；保留 fixture 更小且职责更聚焦的 UI mode owner |
| `tests/coding/test_file_mutation_queue.py::{test_mutation_queue_serializes_same_file_operations,test_mutation_queue_uses_canonical_same_file_identity}` | `tests/harness/workspace/test_mutation_queue.py::test_mutation_queue_serializes_canonical_same_path` | canonical Harness owner 同时覆盖相同路径串行与不同拼写归一化，包含基本同路径场景 |
| `tests/coding/test_file_mutation_queue.py::test_mutation_queue_allows_different_files_to_progress_independently` | `tests/harness/workspace/test_mutation_queue.py::test_mutation_queue_allows_different_paths_to_progress` | 都用受控 event 栅栏证明不同绝对路径不会共享锁；Harness 用例无脆弱的 0.1 秒完成超时 |
| `tests/coding/test_file_mutation_queue.py::test_mutation_queue_rejects_relative_paths` | `tests/harness/workspace/test_mutation_queue.py::test_mutation_queue_rejects_relative_paths` | 同一 canonical API、相同异常类型和消息 |
| `tests/coding/test_file_mutation_queue.py::test_mutation_queue_cleans_up_lock_entries_after_use` | `tests/harness/workspace/test_mutation_queue.py::test_mutation_queue_context_tracks_and_releases_active_path` | 独有的持锁期间可见与退出清理断言迁入 canonical owner |
| `tests/coding/test_file_mutation_queue.py::test_run_with_file_mutation_queue_serializes_callback_operations` | `tests/harness/workspace/test_mutation_queue.py::test_mutation_queue_runner_serializes_callbacks_and_returns_results` | 独有的 callback 串行、顺序及返回值断言迁入 canonical owner |
| `tests/coding/test_file_mutation_queue.py::{test_run_with_file_mutation_queue_accepts_sync_callback,test_mutation_queue_uses_its_direct_harness_owner}` | `tests/harness/workspace/test_mutation_queue.py::test_mutation_queue_runner_accepts_sync_results_and_cleans_up` | 统一保留同步 callback 返回与锁清理；从同一模块重复导入后比较对象身份没有额外消费者边界 |
| `tests/coding/test_file_mutation_queue.py::test_run_with_file_mutation_queue_cleans_up_after_callback_error` | `tests/harness/workspace/test_mutation_queue.py::test_mutation_queue_cleans_up_after_callback_failure` | 同一 canonical runner、异步异常传播与锁表清理 |
| `tests/ontology/test_action_schema.py::test_schema_v3_documents_are_not_loaded_as_v4` | `tests/ontology/test_schema.py::test_schema_v3_documents_are_not_loaded_as_v4` | `load_json` 在解析内容前按同一 format 字段拒绝 v3；换用包含 action 的合法 v4 草稿不会形成新的版本边界 |
| `tests/coding/test_frontmatter.py::{test_parse_frontmatter_normalizes_crlf_and_block_scalars,test_parse_frontmatter_supports_simple_lists_and_maps,test_parse_frontmatter_supports_nested_maps}` | `tests/harness/resources/test_frontmatter.py::{test_parse_frontmatter_normalizes_newlines_and_block_scalars,test_parse_frontmatter_supports_lists_and_nested_maps}` | Coding 文件直接导入 canonical Harness parser，没有 Coding adapter；Harness owner 覆盖 CRLF/block scalar、list 和 nested map 的相同解析边界 |
| `tests/coding/test_frontmatter.py::test_parse_frontmatter_keeps_original_body_without_complete_frontmatter` | `tests/harness/resources/test_frontmatter.py::{test_parse_frontmatter_returns_plain_content_unchanged,test_parse_frontmatter_preserves_unterminated_document}` | Harness owner 分别保留普通正文与未闭合 frontmatter 的原文保持，并额外校验完整结果值 |
| `tests/coding/test_frontmatter.py::test_parse_frontmatter_reports_invalid_yaml_location` | `tests/harness/resources/test_frontmatter.py::test_parse_frontmatter_reports_source_location` | 同一 canonical 异常、输入及 line/field 断言 |
| `tests/coding/test_prompt_assembly.py::test_prompt_template_args_do_not_recursively_substitute_argument_values` | `tests/harness/capabilities/test_prompt.py::test_template_expansion_does_not_reprocess_argument_values` | 完整调用、恶意占位符参数和输出断言相同；Coding 文件直接调用 canonical Harness helper，没有 Coding adapter |
| `tests/ai/test_provider_contract_matrix.py::test_builtin_registration_is_frozen_to_core_adapter_matrix` | `tests/ai/contracts/test_core_provider_contracts.py::test_builtin_registration_matches_core_contracts` | 两份矩阵包含同一三个 core adapter，均对 builtin registry 的排序 API 集合做相同断言；文档矩阵文件保留文档一致性职责 |
| `tests/ai/test_provider_contract_matrix.py::test_core_production_adapters_implement_api_adapter_contract` | `tests/ai/contracts/test_core_provider_contracts.py::test_core_adapters_implement_invoke_raw_contract` | canonical contract 对同一三个具体 adapter 保留全部旧断言，并额外验证 PreparedRequest adapter、prepare 与 invoke_prepared 签名 |
| `tests/coding/test_workspace_path_mutation_compatibility.py::test_workspace_mutation_queue_preserves_owner_identity` | `tests/harness/workspace/test_mutation_queue.py` 的 canonical runner/context 行为集合 | 两种导入写法都解析为同一个 Harness 模块，没有 legacy Coding facade；同模块对象自等不构成消费者合同 |
| `tests/coding/test_screen_coding_tui_mode.py::test_run_coding_tui_non_interactive_keeps_plain_prompt_loop` | `tests/coding/test_ui_mode.py::test_run_coding_tui_non_interactive_keeps_plain_prompt_loop` | 两个函数体完全相同，均 patch 同一 mode 入口并断言非交互分支、prompt 与参数集合；保留 fixture 更小且职责更聚焦的 UI mode owner |

Harness host 测试文件只包含这三个重复项，且也直接导入 canonical events 类型，没有独有 facade 合同，因此删除整个重复文件。canonical events 的失败传播且不阻塞后续事件用例继续保留。

## 3. AppHost Linux 一次执行与报告派生

主回归一次执行原集合，并补入原 G8 独有的 `test_product_normal_close_retires_exact_attempt_without_global_rollback`。G8/G9/G10 后续步骤从主 JUnit 派生报告，不再重复执行 pytest。

- join：完整 `tests.coding.test_apphost_product` 与上述 Worker close node。
- composition/rollback：完整 `tests.coding.test_apphost_composition`。
- canary：原四个文件中带 G10 标识的用例；其他架构约束也在主回归执行。
- 原 manifest 精确 case ID、最少数量、零跳过/失败/错误校验继续执行。
- installed canary 的真实安装验证仍单独执行，它与源码回归的运行配置不同。
- Windows 验证未因 Linux 派生报告被删除，跨平台去重需另行证明。

[报告派生器](../../../scripts/ci/derive_junit.py)拒绝来源失败/错误、重复身份、声明与实际数量不符、选择缺失、所选用例跳过以及覆盖来源文件。保留测试结果和 suite properties，不执行 Product、不共享可变状态。来源中合法平台 skip 可以不进入派生报告；所选必需用例必须真实通过。

## 4. 当前验证与剩余工作

- 合并执行的重点集合：62 项通过，27.74 秒；派生 join/composition/canary 报告分别为 19/16/13 项，原 manifest 均通过。
- 去重后的完整事件总线与 session codec 文件：15 项通过，1.58 秒。
- Resource 去重后：4 项通过，1.28 秒；Work 完整初审集合：45 项通过，3.71 秒。
- CI 合同：117 项通过，包含报告派生的缺失、跳过、失败、重复与数量矛盾负例；Ruff、Actions 语法和 diff 检查通过。
- 完整 AppHost 主集合离线验证：2646 项通过、11 项跳过，518.16 秒；跳过项均为明确的 Windows native 条件，不作为 Linux 通过的原生证据。三个报告从这份完整结果再次派生，原 manifest 全部通过。已验证同次执行没有导致该集合的夹具或顺序失败；本地附加 `not live and not requires_host_runtime`、`--skip-host-runtime`，因此仍不是所有执行配置的验收。
- 完整报告显示反复扫描全仓的静态依赖检查单项耗时 60.804/42.307/21.760 秒；两个终端进程死亡恢复用例分别为 38.180/31.081 秒。这些是后续共享扫描和能力拆分的实测依据，不以增加超时解决。
- 上述数字为本地执行，不证明 PR 排队和总耗时达标；真实 installed 与 Windows 运行仍待交付验证。

仍需完成其他非相同 AST 的语义重复、全部目录角色与夹具影响、其余跨工作流唯一执行、历史 job 重组、必要原生场景和真实多次 PR/main 验收。当前共删除 27 个旧 node ID，其中 mutation queue 的 2 个独有合同迁入 canonical Harness owner；数量变化本身不代表全部单元测试去重完成。

## 5. 共享全仓源码扫描准备

AppHost A0、A0.2、A0.3/A0.4 与 Hosted Application G11 的导入扫描统一采用[共享导入事实](../../../tests/architecture/_source_imports.py)。同一进程、同文件内容只解析一次 AST，返回新的结果集合；源文本变更立即失配，缓存只保留不可变导入元组，不缓存可变 AST、Product 状态或会话资源。

保留各消费者原有解析模式：是否包含 from-import 的成员、是否显式拒绝越界相对导入。所有 32 个测试函数的完整 AST 与改动前相同，参数化收集的 32 个用例身份也与完整基线报告一致，32 项全部通过。

旧完整 AppHost 报告中这四个文件的 testcase 时间累计 148.515 秒；新聚焦执行墙钟 20.83 秒。前者为用例时间总和、后者包括聚焦执行准备，且运行时负载不同，因此只作为初步改善证据，不能宣称严格对照倍数或远程总耗时达标。四个消费者覆盖保持，其他消费者与完整远程流程仍待验证。

新增缓存合同验证覆盖绝对/相对/别名/条件导入、两种成员模式、相同输入单次解析、返回集合隔离、同大小同时间戳内容变更、非法相对导入与语法错误；CI 合同增至 121 项通过。

完整 `tests/architecture/test_import_boundaries.py` 也有自己的相对导入错误格式和
成员展开语义，不能直接改用不同返回约定。该文件现在按 `文件名 + 实际源码内容`
缓存不可变的绝对导入 tuple；每次调用仍重新读取源码，内容变化立即形成新键，
返回给调用方的 list 也彼此隔离。全部现有边界测试身份和断言保持不变。同机完整
165 项对照从 537.86 秒降到 83.79 秒；旧远程 #746 报告中的同文件 testcase 时间
合计 134.02 秒，最终远程收益仍以本次 PR 运行确认。

Harness 模块报告中 `test_exec_capture.py` 的 14 个 reader failure 组合各等待测试
请求的 3 秒预算，累计 42.70 秒。它们保留全部 task publication point、before/
after fault 与 reader/non-reader 组合；仅把测试请求预算收紧为 1 秒。断言仍要求
原始 reader 异常、进程退出及 stdout/stderr transport 关闭，不把超时本身作为成功。

## 6. AI 示例唯一执行

旧 `check-ai` 先由 `scripts/ai/check_examples.py` 子进程执行所有离线 AI 示例，再由 `tests/examples` 重跑它们，最后 coverage 又运行 `test_ai_examples.py`；同时把 Agent/Coding/Harness examples 带入 AI gate。现在保留带文件清单、环境清理、输出和公开导入断言的 pytest owner，把 AI 与 Auth example tests 各放入 coverage 执行一次，移除重复脚本阶段及无关 examples 全目录。示例脚本本身和独立检查工具仍保留；变更只收敛 PR gate 的重复执行。

完整新配置实测 858 项通过、7 项 marker deselect，45.18 秒；总覆盖率 90.65%，三个细分 coverage target 均通过。Ruff、76 个 AI 源文件 mypy、catalog 和 import boundary 同时通过。该数据是本地执行时间，不包含远程 runner 安装和排队。

## 7. Coding 混合集合拆分

PR #742 的 8 个 Coding 分片报告共执行约 4,798 项。slowest 列表中的主要耗时来自真实终端/PTY、子进程服务、安装 wheel、包迁移/删除/GC CLI、Worker 修复和完整插件旅程；这些文件按实际边界登记为 integration、platform 或 e2e，而非按 `not live` 标记继续归入单元。

策略 v4 先登记 55 个有运行或静态进程边界证据、且适合整文件迁移的文件。未登记的 372 个文件仍在保守模块集合中，避免把尚未审查的测试默认为单元；targeted 文件变更精确执行自身，不再同时展开 8 个模块分片和通用 E2E。初次候选中的 9 个混合文件仍保留在模块回归，防止同文件的参数解析、选择算法、注册表或纯计划单元用例丢失。代表文件 `test_package_gc_cli.py` 两项通过，耗时 53.75/47.29 秒，证明它是应按能力触发的真实 CLI 集成场景。

第一轮仅移出 slowest 报告出现的 30 个文件时，原最慢 2/8 分片本地仍为 593 项通过、10 项跳过、9 分 18 秒。哈希重新分配及剩余跨进程文件使尾部没有改善，因此不据此减少分片数；第二轮扩展到所有已核对的显式进程边界后再做远程测量。此记录不宣称 Coding 全目录分类完成。

第二轮收紧为 55 个适合整文件迁移的文件后，同一 2/8 分片为 545 项通过、4 项跳过、1 项失败、7 分 29 秒。失败的 lmux selector 用例单独复跑 14.89 秒通过，属于需要继续治理的顺序/环境敏感信号；本次只把 1 分 49 秒的耗时下降作为方向性数据，绿色与全分片尾部以远程 PR 运行确认。

PR #743 的完整远程运行 `38554483283` 为 6 分 04 秒，8 个 Coding job 为 2 分 09 秒至 3 分 30 秒；此前 #742 最慢 Coding 用例阶段为 7 分 48 秒。Ubuntu/macOS/Windows 恢复会话冒烟为 23/41/40 秒，全部通过。合并后的 push 运行 `38555330728` 使用同树、同计划证据，在 58 秒内完成。该结果证明第一批拆分已达到 15 分钟目标，但不代表剩余 Coding 文件完成语义分类。

第三轮从 #743 的 8 份 slowest 报告继续复核。新增 13 个适合整文件迁移的真实执行、托管会话、持久化、LSP、终端和恢复文件，targeted 合计 68 个，359 个文件继续保守回归。候选 `test_hosted_session.py` 同时包含 Ubuntu 集成和 Windows 原生条件用例，Ubuntu 为 18 项通过、1 项跳过，已撤回整文件分类，等待 node 级分类。

部分分类把 Coding 目录展开为显式文件后，pytest 的 `--ignore` 不会再次排除同一显式参数，导致 39 个由 Harnesstui/Coding UI 独立拥有的文件重新进入 Coding 后端；#743 的两个 13 秒全仓 import 扫描即由此重复。runner 现在先从显式 Coding 集合移除这 39 个文件，同时保留 Harnesstui/Coding UI owner。新增 13 个 targeted 文件在合并验证集合中全部通过；修正后的本地 0/8 为 463 项通过、2 项平台条件跳过，原 #743 远端 0/8 为 538 项通过、3 项跳过。不同 runner 的墙钟不作倍数比较，下一次远程全选确认最终尾部。

PR #744 远程全选运行 `38557834260` 绿色完成于 4 分 58 秒。Coding 8 个 job 为 2 分 04 秒至 2 分 57 秒，0/8 从 #743 的 3 分 30 秒降为 2 分 56 秒；Ubuntu/macOS/Windows 恢复冒烟为 26/40/64 秒。该结果确认重复 owner 移除和第三轮分类没有丢失顶层必需检查。

完整验证覆盖补强：此前 catalog targeted 文件只在自身发生改动时执行，schedule/manual full 会从模块集合排除它们却不生成 targeted job。现在 full plan 枚举所有非 live targeted owner，并按平台、类别和稳定路径哈希合并为 19 个批次（当前 76 个平台执行），避免 76 次独立环境安装。普通 PR 仍只批处理实际改动的 targeted 文件。批处理使用 JSON 路径数组和 Python 参数列表，不经过 shell 路径拼接；JUnit 验证要求每个登记文件至少有一项通过，不能由同批其他文件掩盖全 skip。双文件实际执行 11 项通过，两个文件均通过文件级报告验证。

## 8. 跨工作流实际执行去重

PR #746 的运行 `38563194640` 提供了所有活动 pytest job 的 JUnit。审计按
`classname + name` 比较实际 testcase，并区分派生报告、平台变体、skip 和独立
pytest 进程；报告条目重复不直接计为重复执行。

- G8/G9/G10 Linux 三份报告来自同一份 AppHost 主报告，分别包含 19/16/13 项，
  不启动 pytest，因此不是 48 次额外执行。
- AppHost Linux 主报告为 2657 项，其中 11 项平台 skip；它与 Linux 模块、
  Harnesstui/Coding UI 报告共有 1174 个均通过的 testcase。
- 上述 1174 项在 AppHost 进程中的 testcase 时间合计 5.65 秒，在其他 owner
  中合计 4.76 秒。即使全部从 AppHost 删除，可直接归因的 pytest 时间上限也
  只有 5.65 秒；不能把 1174 的数量当作尾部收益。
- AppHost 其余 1483 个身份的 testcase 时间为 144.96 秒。主要成本是终端进程
  死亡恢复、双 mux 交互、真实 Coding 断线恢复、native/installed canary、
  托管进程清理和全仓架构扫描；它们不是模块 job 中已经执行的同配置复本。
- Ubuntu、macOS、Windows 的恢复会话冒烟属于不同平台配置；相同测试身份不按
  普通重复删除。Windows AppHost 的 G8/G9/G10/G13 也需先按平台独有断言审查，
  不能用 Linux 报告代替。

结论：删除 AppHost 与模块的廉价重合项只能减少收集与少量执行开销，不是当前
尾部的主要手段。下一轮应逐项判断 144.96 秒独有集合中哪些是普通 PR 必需冒烟、
哪些适合按变更触发或定时运行。任何因此新增或扩大 test route、平台、job 或失败
条件的方案均先进入审批包；未获明确批准前只记录建议，不修改门禁。

首批执行归属收敛移除 AppHost PR 主回归中的四个已有 targeted owner：
`test_hosted_local.py`、`test_mux_product_terminal.py`、`test_mux_subprocess.py` 和
`test_mux_terminal_process.py`。它们在 #746 AppHost 报告中合计 56.16 秒；直接修改
由 catalog 的 Ubuntu integration/platform job 执行，schedule/manual full 也会
执行，且本地 `make check-apphost` 继续包含完整集合。普通 AppHost PR 保留
`tests/apphost` 全包、架构合同、G8/G9 组合、G10 native/installed canary、Windows
G8/G9/G10/G13 及独立三平台核心冒烟。本批只删除旧 PR 清单归属，不新增 job、
test route、平台、触发或失败条件。

随后对 catalog 的 77 个 targeted 文件逐一生成 test-only 计划。旧选择器在选中精确
targeted job 后仍继续套用目录和 Makefile 清单，使 20 个整文件 owner 额外选择
AppHost，另一个 node 级混合文件额外选择 architecture。选择器现在以 catalog 作为
已审查 test-only 路径的完整 owner：整文件和专用夹具只执行既有 targeted job；
node 级混合文件同时执行原模块剩余节点与既有精确节点。源码、未知测试、共享夹具
和 CI 编排仍走原影响规则。该变化删除旧规则误触发，不新增 job、route、平台、
触发或失败条件。

同一提前收敛也移除了四个已分类 Worker test-only 文件附带的完整 Windows native
矩阵，其中 candidate wheel 过去还会选择持续查询。对应源码平台边界、三个未分类
Windows Worker 测试和 schedule/manual full 仍保留原完整矩阵；被修改的四个测试
继续在 catalog 声明的平台执行自身场景。

## 9. Protocols 测试支撑代码合并

`tests/protocols` 的 4 个测试文件包含 101 个静态测试函数，参数化后收集 109 个
实例。逐项按协议入口、输入分区和断言复核后，没有可删除的行为复本：相似的
max-token、reasoning、auth、tool-call 和资源关闭用例分别约束 Anthropic Messages、
OpenAI Chat Completions、OpenAI Responses 的不同 wire payload 或生命周期。所有
SDK 调用由 fake module、内存 adapter 或合成事件驱动，不访问真实网络。

三个真实协议文件此前各自复制同一套 context normalization、request mode 转换和
stream 启动代码，只替换 API 名称。该驱动已合并到 `_runtime.py`，协议文件通过
绑定 API 名称复用；测试 node、参数、fake SDK、输入与断言均未改变。改动净减少
75 行测试支撑代码，完整目录仍为 109 项通过、1.36 秒。所属 AI 完整离线回归
858 项通过、7 项 live deselect，31.28 秒；总覆盖率 90.65% 及三个细分阈值、
Ruff、mypy、catalog 和 import boundary 均通过。本批减少维护重复，不改变门禁、
route、平台、触发或失败条件。

## 10. Root、Examples 与 Integration 初审

Root 的 1 个实例只约束打包 console script。Examples 的 49 个静态函数收集为
61 个实例，按 Agent、AI/Auth、Coding 和 Harness 的公开示例分别验证公开导入、
受控 fake 模型或认证、脚本 help/import 与独有输出。忽略函数名的完整 AST 没有
重复测试；相似的 module loader 属于多个模块 owner，共享它需要先定义跨 owner
测试助手的影响路由，因此本批不以无归属 helper 替换局部代码。

Integration 的 10 个静态函数收集为 42 个实例：4 个显式 `live` LSP Server
兼容用例，5 个 Ontology 内存/SQLite 产品组合实例，以及 33 个 manifest 示例
子进程 smoke。LSP 用例分别验证 Pyright、TypeScript、gopls、rust-analyzer 的真实
协议和诊断生命周期；Ontology 用例覆盖 action/fact 投影与真实 SQLite 重启、身份
拒绝边界，不能跨平台或存储配置合并。

Root、Examples 与 Integration 的非 live 联合运行结果为 97 项通过、3 项失败、
4 项 live deselect，3 分 58.95 秒。`legacy-007/013/019` 三个示例在各自新建临时
目录首次创建 Session 时稳定得到 transcript writer `conflict/unavailable`；精确
复跑仍为 3 项失败、12.89 秒，不能作为绿色证据。manifest smoke 的 33 个参数逐个
启动子进程，最慢两个为 24.69 秒和 20.11 秒；当前正常 PR workflow 不执行该文件，
直接修改它却会因无 owner 保守选择全量门禁。为它新增 targeted owner 会增加测试
route，须单独审批；本批仅记录问题，不改变门禁、测试身份或失败条件。

## 11. CI 合同初审

`tests/ci` 当前有 6 个文件、139 个静态测试函数和 139 个收集实例：

- `test_change_gates.py` 的 95 项覆盖选择与暂停、顶层聚合、suite 清单、Git diff
  范围、工作流结构和轻量文档链接检查；
- `test_test_catalog.py` 的 16 项覆盖完整目录、targeted 文件/node、专用夹具、
  schema 拒绝和执行计划归属；
- 其余 28 项分别覆盖 JUnit 证据派生、模块报告完整性、PR 证据复用和导入事实缓存。

这些用例只使用临时 Git 仓库、合成 JUnit、fake GitHub API、静态工作流文本及
mock 执行器，不运行 Product 或访问网络。忽略函数名和源码位置的完整 AST 扫描
没有重复簇。选择器与 catalog 的相似路径样本分别证明“触发集合”和“清单归属”；
JUnit 派生与模块报告分别证明“子集证据真实”和“模块集合完整”；证据复用与顶层
聚合分别证明“可复用来源匹配”和“当前运行不会误绿”。这些失败面不能由另一组
断言替代。

完整目录 139 项通过，2.493 秒。当前成本很小，删除或跨文件合并不会显著缩短 PR，
却会降低失败定位或引入共享夹具状态，因此本批保留全部节点。审计没有增加 required
check、workflow、job、route、平台、触发或失败条件。

## 12. Dev 目录初始分组与误路由收敛

`tests/dev` 的 45 个文件包含 406 个静态测试函数，参数化后收集 1674 个实例。明确
绑定当前 worktree 源码的 Linux 离线运行结果为 1669 项通过、5 项平台条件跳过，
243.10 秒。这里混合了纯比较/收据合同、真实子进程监督、进程树回收、临时 Git 与
wheel、POSIX 行为及跨平台 observer，不能把目录整体归作快速单元。忽略函数名和
源码位置的完整 AST 扫描没有重复簇；参数矩阵和相似合同仍待继续语义审查。

路由逐文件检查发现，18 个 `test_lmux_*` 文件和
`test_screen_first_probe_readiness.py` 复用已有 G18 runner、comparison 或 Coding
probe，却没有进入 G18/AppService 路径规则。它们的 test-only PR 因此使用未知路径
全量回退，误选八类 workflow。现将 19 个路径加入已有 G18/AppService owner，静态
验证均收敛到相同的 `docs`、`appservice`、`host_runtime` check 与 `units`、`e2e`
workflow；这只删除无关选择，未增加任何门禁。

AppService 工作流仍按用户要求暂停，现有 owner 也不直接执行这 19 个测试文件。
若要在修改这些测试时新增精确 targeted 执行，将形成新的 PR 失败条件；按审批规则
须先提交成本、断言和回退方案，本批不实施。

同一目录的首个执行成本重复位于
`test_recovery_seed_rejects_changed_workload`：12 个故障参数都先创建完整真实 Session
seed，约 4.2--4.7 秒后才分别改写一个输入分区。现在模块级创建一次与原路径绑定的
合法 cwd seed，并保存只读文件快照；函数级 fixture 在每个参数前删除上一份活动树，
从快照恢复到同一原路径，再返回重新解码的 record 与重新构造的 scope。这样保留
绝对 cwd、scope fingerprint、session identity 和每例独立初态，也避免在不同路径
复制 seed 导致路径绑定失真。

12 个原 node ID 和 fault 参数全部通过。聚焦重复运行分别为 12.54 秒与 8.99 秒；
完整 `test_measure_g18_native.py` 为 250 项通过、4 项平台跳过，55.86 秒。相同机器
上的完整 Dev 回归从 194.89 秒降到 138.37 秒，1669 项通过、5 项平台跳过，减少
56.52 秒。该文件当前仍属于暂停的 AppService 路径；收益适用于本地、手动及未来经
审批恢复后的执行，不据此声称当前 PR 墙钟同步减少。

该优化 PR 的首轮远程计划还暴露一项执行重复：G18 test-only 改动除既有 owner 与
模块回归外，又被通用未审查路径规则附加三平台 Resume E2E，而 E2E 不执行这些 Dev
测试。G18 规则现复用既有 reviewed-test 语义，test-only 只保留原 owner、依赖和
模块回归；源码与未知路径继续保守选择。本次只移除无关 E2E，不增加 route、job、
平台或失败条件。

PR #763 同分支远程对照中，旧运行 `38588834269` 的两个模块单元为 18/19 秒，三平台
Resume E2E 为 29/41/63 秒，总墙钟同口径 84 秒。新运行 `38589276148` 保留模块单元
并明确跳过 E2E，总墙钟 61 秒；`changes` 在两轮间从 10 秒波动到 26 秒，所以实际
端到端净减少 23 秒，不能把三个 E2E job 的时间直接相加作为墙钟收益。

## 13. Architecture 目录部分初审

`tests/architecture` 当前有 62 个测试文件和 654 个收集实例。它不是单一快速单元
套件：文件分别进入 Harness、Hosting、AppHost 等历史清单，且包含全仓源码库存、
导入边界、文档状态、平台证据和运行时所有权合同。控制分支上的首次整目录性能探测
在 900 秒上限时仍约有 12% 未完成；该控制分支包含未推送提交，因此这次探测只作为
成本证据，不作为远端主线通过或失败结论。不能把整目录加入普通 PR 门禁。

首个确定热点位于 `test_hosted_product_runtime_v1_baseline.py`。其中
`test_current_inventory_matches_source_and_retained_absences` 为寻找 AppHost 反向依赖，
原先对 `src/loushang` 下每个 Python 文件执行 AST 解析。基于 `origin/main` 的隔离
基线为 16.48 秒。现在先检查源码是否包含断言所需的精确 `loushang.apphost` 前缀；
不含此前缀的文件不可能由原助手返回匹配项，候选文件仍走相同 AST 解析。导入事实
同时按文件名和实际源码内容缓存为不可变 tuple，对调用方继续返回独立 set。

同一节点优化后为 0.81 秒，约快 20 倍；该文件全部 11 项通过、总计 1.73 秒。
测试名称、断言、源码读取和候选文件 AST 语义均保持不变。

路由复核还发现，该测试已同时列入 `HOSTING_TEST_PATHS` 和
`APPHOST_TEST_PATHS`，却因不在已完整分类的目录中又附加三平台 Resume E2E。
选择器现在把现有 Makefile `*_TEST_PATHS` 当作 test-only 文件的既有 owner：保留
所有原 owner 和依赖，只停止追加不执行这些文件的通用 E2E。源码、未知测试、
非 Python 支持文件、专项 targeted 路由和完整验证保持原规则。该文件的计划由
`Hosting + AppHost + E2E` 收敛为 `Hosting + AppHost`；139 项现有 CI 契约全部
通过。此项只删除重复执行，没有增加 check、workflow、job、route、平台、触发或
失败条件。

远程首轮还暴露 AppHost workflow 内部耦合：同一个 `apphost` 开关同时启动普通
回归和 Windows native 证据，即使计划已明确关闭 E2E。Windows native job 现在只在
既有 `apphost` 与 `e2e` 风险位同时成立时运行；AppHost 源码、未知变更和完整验证仍
满足该条件，已审查 test-only 改动只保留普通回归。`apphost-quality.yml` 自身的修改
归入已有 CI 契约短路径，由路由/聚合合同与 actionlint 验证，不再为了验证 YAML
条件而执行产品和 Windows native 场景。这同样只收窄现有门禁。
