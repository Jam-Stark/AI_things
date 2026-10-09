<!-- JAM-V160-ROUTE-BEGIN -->
## 工作方式 · v1.6.0

开始工作时读 `.ai/ROLE.md`，明确目标、职责、完成条件和已授权边界。FAST 小任务直接完成；STANDARD 有独立产出或专门上下文需求时委托最少必要成员。项目事实从 `.ai/PROJECT.md` 和实际源码查证，其余资料按需读取。

完整阶段交给 execution lead。它可以是独立 root，也可以是 Planner 派生的 child；真实身份不变，阶段内职责一致。lead 自主组队、分配已授资源、修复、验证、整合并交付。只在明确 gate、需要新决定的实质问题和最终阶段结果时返回 Planner；普通通知未获回复不阻塞已批准工作。

组队读 `.ai/EXECUTION_TEAM.md` 和 `.codex/TEAM.md`；独立审视问题读 `.ai/OUTSIDE_VIEW.md`。保持单写入方，不扩展已授范围，不用 fallback 掩盖错误，不凑 reviewer 或逐项确认。Main 模型与 effort 由 App/Owner 选择。
<!-- JAM-V160-ROUTE-END -->

# Project AI entrypoint

System/developer/Owner 指令优先。项目事实从 `.ai/PROJECT.md`、最小 memory 和实际 source/config/runtime 查证。

按需路由：多 writer/排他资源/正式审阅 → `.ai/TEAM_STATE.md`；长跑 → `.ai/LONG_RUNNING_TASKS.md`；科研/硬件 → `.ai/SCIENTIFIC_ENGINEERING.md`；可复用新事实 → `.ai/MEMORY_GOVERNANCE.md`；阶段规划 → `.ai/STAGE_DECISION.md`；明确交付 → `.ai/ARTIFACT_HANDOFF.md`。不触发就不启用。

Owner/Planner 保有目标与阶段验收，execution lead 持有已授权范围内的组织和整合职责。Git/外部写入按当前明确授权分别处理；不因存在工具而启用 ledger、freeze 或 curator。
