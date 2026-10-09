<!-- managed-by: jam-coding-role; file: MODEL_ROUTING.md -->
# Model routing v1.6.0

Main 的模型与 effort 由 App/Owner 选择；项目不设置 Main model/effort，也不通过 profile 覆盖。保留现有 context/compact 设置，不把配置值当成实际生效证明。

| 角色 | 模型 / 默认 effort | 职责 |
|---|---|---|
| execution_lead | gpt-6.1-sol / high | 已批阶段执行、组队、依赖协调、整合交付；可选 xhigh/max |
| outside_view | gpt-6.1-sol / xhigh | 新上下文、只读检查问题定义；不做强制审批 |
| default / worker | gpt-6.1-sol / medium | 有界任务 / 普通实现 |
| context_researcher | gpt-6.1-sol / medium | 跨文件证据和依赖整合，只读 |
| scope_planner | gpt-6.1-sol / high | 计划拆解与验收设计 |
| semantic_worker | gpt-6.1-sol / high | 复杂实现和调试 |
| code_reviewer | gpt-6.1-sol / high | 对真实 concern 做独立审阅 |
| explorer / runtime_qa | gpt-6-luna / high | 窄检索 / 既定命令执行与证据整理 |
| memory_curator | gpt-6-luna / medium | 机械整理，不创造事实 |
| deep_researcher | gpt-6-astra / medium | team 全生命周期唯一身份，最难科研问题，只读 |

Sol 原有角色保留 low/medium/high/xhigh/max 变体，新 lead 为 high/xhigh/max，outside 为 xhigh。使用生成器注册的准确名称；默认名对应默认 effort，其他为 `role__effort`。不临时覆盖 model/effort，也不改活跃角色配置换模型。

执行能力只在 `role-policy.json` 定义，由生成器输出角色 TOML 与 checker。execution_lead、worker 和 semantic_worker 可在有效阶段授权内派生；其余为叶节点。职责、真实宿主身份、grant 分别记录。规范见 `.ai/EXECUTION_TEAM.md`，模型名不赋予组织权。

默认逻辑席位 5，计 lead 与所有支持成员，不计 Planner；真实 root lead 也占 1。阶段可明确配置预算，同时服从宿主并发限制。Astra 已分配身份不因关闭、刷新或压缩而重置。

委托使用短 brief、准确路径、范围和完成证据，采用 `fork_turns="none"`。Outside view 先形成问题定义，再读现有推荐。Luna 配置预算 65536/49152，Sol/Astra 196608/163840，scope=total；宿主历史预算缺陷没有由本版修复。
