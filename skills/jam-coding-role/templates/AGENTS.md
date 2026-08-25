# Project AI entrypoint

System、developer、Owner/user 指令优先。**在本仓库自身的规则中，本文件是项目级工作流权威入口**；runtime 默认、adapter 或子目录说明可以补充具体工具和局部事实，但不得静默关闭这里要求的自动路由。若更高层 system/developer 明确禁止 sub-agent，则遵守该限制并退化为单 agent。

本文件是路由表，不要求每次任务全量读取所有 `.ai/*` 文档。

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

## Automatic route selection

Main must classify every request as FAST、STANDARD or HIGH_RISK without waiting for the user to name a mode.

- **FAST**: simple QA、temporary test、clear small change; Main directly, no persistent facilities.
- **STANDARD**: ordinary implementation/debugging. When the task has independent workstreams、specialist context or a material benefit from independent review, this project instruction explicitly requires Main to delegate or parallelize without waiting for the user to say “team”. Use 0 agents when delegation adds no value.
- **HIGH_RISK**: destructive/external/hardware/hard-to-reverse/unapproved expensive work. Detect this route automatically; read-only planning/research may be delegated, while side effects wait for Owner approval.

Main owns scope、acceptance、write/resource authority、Git、external writes and final integration. Git commit/push require current explicit authorization, except an Owner-requested cloud Pro handoff as defined in `.ai/ARTIFACT_HANDOFF.md`. Do not activate ledger、freeze、curator or artifact handoff merely because those tools exist.
