<!-- managed-by: jam-coding-role; file: WORKFLOW.md -->
# Adaptive workflow v1.6.0

FAST：有明确边界的小任务直接完成。STANDARD：有独立实现、证据或专门上下文需求时，委托最少必要成员并继续自己的工作。HIGH_RISK 是已有授权的覆盖层；未授权的昂贵长跑、硬件、破坏性或外部动作需要决定，不因任务复杂强制启动整套流程。

Owner/Planner 定义目标、阶段边界和验收；execution lead 完成批准阶段。用现有 plan 交接，不要求 Owner 重写合同或逐命令批准。lead 在范围内处理成员依赖、普通故障与已批后续运行，依 `.ai/EXECUTION_TEAM.md` 绑定真实身份与阶段授权。

两种启动方式同责同权：Owner 新开 root lead，或 Planner spawn child lead。技术事实走直接 P2P；实际创建者负责成员控制，阶段整合由 lead 负责。Planner 收到 gate、需要新决定的实质问题及最终结果。写入与排他资源不冲突，阶段外的新目标或新资源仍由原决策者批准。

按任务需要读取：`.ai/TEAM_STATE.md`（多 writer、资源/依赖、正式审阅），`.ai/LONG_RUNNING_TASKS.md`（持久长跑），`.ai/SCIENTIFIC_ENGINEERING.md`（科研结论），`.ai/OUTSIDE_VIEW.md`（问题重构），`.ai/MEMORY_GOVERNANCE.md`（可复用新事实），`.ai/ARTIFACT_HANDOFF.md`（明确交付）。不为小任务启动这些设施。
