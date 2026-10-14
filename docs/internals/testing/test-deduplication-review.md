# 测试去重实施记录

本记录是[测试与 PR 门禁重构方案](test-and-pr-gate-refactoring-plan.md)的实施证据，不能替代全量语义审查或远程性能验收。当前接受范围为下述已确认重复项与 AppHost Linux 同配置重复执行；其他项仍待审查。

## 1. 全仓候选扫描

2026-10-14 扫描当前任务工作树的 1475 个 `test_*.py` 文件、13755 个静态 `test_` 函数定义。比较忽略位置和函数自身名称的完整 AST，保留参数、装饰器和函数体，发现 10 组候选。参数化实际运行数量、全局配置、共享夹具和被包含但不完全相同的断言不在这项扫描的证明范围内。

| 候选 | 上下文核对 | 处置 |
| --- | --- | --- |
| AI `test_api_streaming.py` 的 register/get 两个 legacy signature 用例 | 同文件、同 provider、同 registry，实际都只调用 register 并检查相同异常 | 确认重复，待 AI 验证批次合并 |
| AI 同文件 optional legacy signature 两个用例 | 同一 `_LegacyProviderWithOptionalDebug`、相同调用与异常 | 确认重复，待 AI 验证批次合并 |
| 五个 vendor live 测试 wrapper | 各模块的 main、模型/协议和工具配置不同 | 保留；wrapper 相同不代表网络行为相同，不执行 live 验证 |
| 两个 Kimi OpenAI live wrapper | 分别调用 stream/complete 示例流程 | 保留；全局函数不同 |
| Coding 两个 UI 文件的 non-interactive 用例 | 使用各文件的 `_Session` 和 `_runtime_for`，尚未完成上下文等价证明 | 暂保留，后续核对后归唯一 owner |
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

仍需完成非相同 AST 的语义重复、全部目录角色与夹具影响、跨工作流唯一执行、历史 job 重组、必要原生场景和真实多次 PR/main 验收。5 个冗余用例的删除不代表全部单元测试去重完成。

## 5. 共享全仓源码扫描准备

AppHost A0、A0.2、A0.3/A0.4 与 Hosted Application G11 的导入扫描统一采用[共享导入事实](../../../tests/architecture/_source_imports.py)。同一进程、同文件内容只解析一次 AST，返回新的结果集合；源文本变更立即失配，缓存只保留不可变导入元组，不缓存可变 AST、Product 状态或会话资源。

保留各消费者原有解析模式：是否包含 from-import 的成员、是否显式拒绝越界相对导入。所有 32 个测试函数的完整 AST 与改动前相同，参数化收集的 32 个用例身份也与完整基线报告一致，32 项全部通过。

旧完整 AppHost 报告中这四个文件的 testcase 时间累计 148.515 秒；新聚焦执行墙钟 20.83 秒。前者为用例时间总和、后者包括聚焦执行准备，且运行时负载不同，因此只作为初步改善证据，不能宣称严格对照倍数或远程总耗时达标。四个消费者覆盖保持，其他消费者与完整远程流程仍待验证。

新增缓存合同验证覆盖绝对/相对/别名/条件导入、两种成员模式、相同输入单次解析、返回集合隔离、同大小同时间戳内容变更、非法相对导入与语法错误；CI 合同增至 121 项通过。
