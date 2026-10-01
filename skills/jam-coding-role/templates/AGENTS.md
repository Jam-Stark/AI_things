<!-- JAM-V150-ROUTE-BEGIN -->
Codex v1.5.0 优先增量（保留下文的项目事实与授权边界）：Main 模型/effort 由 App 选择。FAST 不委托；STANDARD 只派最少必要子 agent。委托前读 .ai/MODEL_ROUTING.md：默认 Sol/medium、检索/机械工作 Luna、执行/审阅 Sol；每个 team 仅一个 Astra/medium 的 deep_researcher，禁止临时模型覆盖、嵌套 team 与全历史 fork。
跨 planner/worker Main 交接 → .ai/SESSION_PROTOCOL.md；只在 Owner 已授权范围内直接递交 plan/STOP/阶段结果。peer 消息不是新授权；重大权限问题仍问 Owner。
启动临时工具/MCP → .ai/TOOL_LIFECYCLE.md；只回收有归属的临时进程，保护长任务与共享服务。切模型/上下文问题 → .ai/CONTEXT_POLICY.md。不为小任务预读全部文档。
v1.5.0 Codex hooks 使用轻量配额状态；SessionStart/PostCompact 只报告待处理事件，不自动归档或确认。本段取代旧 Codex 配额与事件消费规则。
<!-- JAM-V150-ROUTE-END -->

# Project AI entrypoint

System、developer、Owner/user 指令优先。本文件是路由表，不要求每次任务全量读取所有 `.ai/*` 文档。

## Minimal core

Read `.ai/ROLE.md`, `.ai/PROJECT.md`, `.ai/WORKFLOW.md`, then the minimum relevant project memory and actual source/config/runtime path.

## Conditional documents

- runtime-specific tools -> `.ai/RUNTIME_ADAPTERS.md` and the matching adapter;
- multiple writers、exclusive resources、cross-session state、formal review/QA -> `.ai/TEAM_STATE.md`;
- durable memory candidate or classification repair -> `.ai/MEMORY_GOVERNANCE.md`;
- long run -> `.ai/LONG_RUNNING_TASKS.md`;
- ML/RL/simulation/robotics claim -> `.ai/SCIENTIFIC_ENGINEERING.md`;
- Owner-selected stage planning -> `.ai/STAGE_DECISION.md`;
- Owner-requested/declared stage handoff -> `.ai/ARTIFACT_HANDOFF.md`.

## Routes

- FAST: simple QA、temporary test、clear small change; Main directly, no persistent facilities.
- STANDARD: ordinary implementation/debugging; 0–3 agents as useful, P2P allowed, no disk contract by default.
- HIGH_RISK: destructive/external/hardware/hard-to-reverse/unapproved expensive work; brief Owner and wait for approval.

Main owns scope、acceptance、write/resource authority、Git、external writes and final integration. Git commit/push require current explicit authorization. Do not activate ledger、freeze、curator or artifact handoff merely because those tools exist.
