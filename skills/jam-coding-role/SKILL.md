---
name: jam-coding-role
description: Bootstrap, migrate, audit, or evolve a lean project AI coding role. Use for project-level Codex/OpenCode/OMO/Claude routing, optional multi-agent coordination, file-based memory, long-running scientific work, or artifact handoff.
---

# Jam Coding Role v1.3.0

This skill provides a portable behavior kernel with **lean defaults and on-demand control facilities**.

## Core design

- FAST / STANDARD / HIGH_RISK route selection;
- no mandatory team, ledger, disk contract, reviewer wave, memory curator, or artifact step for ordinary work;
- Codex MultiAgentV2 P2P remains available without persistent coordination state;
- ledger, lease, candidate freeze and verdict dependency activate only for real multi-writer/resource/cross-session/formal-review needs;
- memory governance is proactive but candidate-triggered;
- long-run and artifact workflows are explicit optional profiles;
- standalone Claude Code remains single-agent;
- OpenCode/OMO preserves its own official ordinary delegation and Team Mode semantics.

## Files

- `references/ROLE.md`: stable coding behavior and Chinese expression standard;
- `references/WORKFLOW.md`: FAST / STANDARD / HIGH_RISK and facility triggers;
- `references/RUNTIME_ADAPTERS.md`: Codex, OpenCode/OMO and standalone Claude routing;
- `references/TEAM_STATE.md`: optional coordination ledger;
- `references/MEMORY_GOVERNANCE.md`: active, candidate-triggered memory maintenance;
- `references/LONG_RUNNING_TASKS.md`: tmux receipts and pending events;
- `references/SCIENTIFIC_ENGINEERING.md`: optional ML/RL/simulation/robotics evidence discipline;
- `references/STAGE_DECISION.md`: optional Owner-directed local/cloud planning synthesis;
- `references/ARTIFACT_HANDOFF.md`: explicit stage artifact packaging, 95 MiB semantic ZIP splitting and Drive handoff;
- `references/PROJECT_GROWTH.md`: grow only after observed workflow failure;
- `scripts/bootstrap.py`: safe init/refresh/audit;
- optional helpers under `scripts/`.

## Codex hook contract

When coordination hooks are installed:

- `PreToolUse` no-op success exits `0` without stdout; deny uses only the event-specific permission decision and never returns `continue`;
- `PostToolUse` and `SessionStart` may use their supported common output fields;
- repository-local commands resolve scripts from `$(git rev-parse --show-toplevel)`;
- malformed strict-policy input fails closed;
- PostToolUse persistence is metadata-only, and pending SessionStart events are delivered once then archived.

The implementation details and verification evidence are recorded in `UPDATE_LOG.md`.

## Bootstrap

Minimal project:

```bash
python scripts/bootstrap.py init /path/to/project
```

Scientific project with runtime adapters but without persistent coordination:

```bash
python scripts/bootstrap.py init /path/to/project \
  --profile scientific \
  --runtime codex \
  --runtime omo \
  --runtime claude
```

Add facilities only when needed:

```bash
  --memory
  --codex-coordination-state \
  --long-run-supervisor \
  --stage-workflow \
  --artifact-sync \
  --omo-team-mode
```

`init` never overwrites existing files. `refresh` updates only managed core files. Project entrypoints, runtime configuration, memory, credentials and local overlays remain project-owned.

## Migration principle

A migration script must not stage or commit by default. Git writes require current explicit Owner authorization and must be surfaced as opt-in flags. External upload is also explicit; never hide it in a session-end hook.
