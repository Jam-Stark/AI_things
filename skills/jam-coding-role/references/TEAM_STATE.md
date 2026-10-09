<!-- managed-by: jam-coding-role; file: TEAM_STATE.md -->
# Optional persistent coordination state

Team state is inactive by default. It is not a prerequisite for ordinary agent spawning.

## Activate when

- two or more writers;
- exclusive GPU/process/display/port/hardware/output resources;
- cross-session task continuity;
- formal review/QA with candidate/verdict dependency;
- Owner requests persistent coordination.

Do not activate for simple QA, a single writer, ordinary read-only research or temporary tests.

## Modes

```bash
python .ai/scripts/team_state.py activate --mode adaptive --reason "multiple writers"
python .ai/scripts/team_state.py activate --mode strict --reason "formal QA"
```

- `adaptive`: unregistered ephemeral spawns remain allowed; registered tasks are validated.
- `strict`: configured writer/reviewer/runtime groups require registered valid contracts.

## Contracts and leases

Only tracked tasks get disk contracts. Leases cover actual write paths or exclusive runtime resources; never read-only agents.

## Freeze and verdict

Freeze only formal review/QA candidates. Verdicts bind exact paths/contracts/topology; changes become `INVALID`, `RETAINED` or `REVIEW_REQUIRED` conservatively.

## Closure

No fixed ceremony. Release real leases and deactivate when tracked work is done. Ordinary work never initializes this state.


## 阶段组织权

阶段内的 ownership、依赖与资源安排由 execution lead 在有效 grant 内处理，root/child 身份不改变这项职责。现有正式协调记录仍按需使用；它不取代阶段授权，也不要求 Planner 为已批步骤逐一放行。
