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
- **STANDARD**: ordinary implementation/debugging. When the task has independent workstreams、specialist context or a material benefit from independent review, this project instruction explicitly requires Main to delegate or parallelize without waiting for the user to say “team”.
- **HIGH_RISK**: destructive/external/hardware/hard-to-reverse/unapproved expensive work. Detect this route automatically; safe read-only planning/research may be delegated before side-effect approval.

### Mandatory delegation gate

Before substantive work on every non-FAST request, Main must check whether any of these is true:

1. two or more read-heavy or research lanes can proceed independently;
2. a specialist has materially different context from Main;
3. an independent reviewer/QA lane would materially reduce risk;
4. parallel work would materially improve completion time or keep noisy exploration out of Main context.

If any trigger is true and the runtime permits sub-agents, Main **must immediately spawn the minimum useful agents before doing the delegated work itself**. Merely saying that delegation might help later, or waiting for the user to request a team, does not satisfy this rule. STANDARD normally uses 1–3 focused agents when triggered. HIGH_RISK may start safe read-only agents while side effects wait for Owner approval.

Main may use zero agents only when no trigger is true, the task is tightly coupled and cheaper to do directly, or a higher-level/runtime restriction blocks sub-agents. Record a concise `NO_DELEGATION_REASON` in the task plan when a non-FAST request stays single-agent. Re-run this gate if the scope expands or a new independent lane appears.

Main owns scope、acceptance、write/resource authority、Git、external writes and final integration. Git commit/push require current explicit authorization, except an Owner-requested cloud Pro handoff as defined in `.ai/ARTIFACT_HANDOFF.md`. Do not activate ledger、freeze、curator or artifact handoff merely because those tools exist.
