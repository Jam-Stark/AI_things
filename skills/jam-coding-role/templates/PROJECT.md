# Project overlay

Complete this file from current source and configuration rather than plans or memory.

## Identity

- Repository:
- Primary branch/worktree:
- Domain:
- Source-truth order:

## Real paths

```text
entrypoints:
configs:
runtime/evaluation:
artifacts:
memory routes:
```

## Environment and command registry

Maintain one canonical list of environments and commands. Use a verified entry before train/eval/render/deploy; do not guess an equivalent command from memory.

### Environments

| ID | Runtime/conda environment | Activation command | Purpose | Last verified |
|---|---|---|---|---|
| primary | `[FILL]` | `[FILL, e.g. conda activate ...]` | normal development/runtime | NOT_VERIFIED |

### Commands

| ID | Purpose | CWD | Environment ID | Exact command | Expected output/artifact | Last verified | Evidence |
|---|---|---|---|---|---|---|---|
| train.default | training | `[FILL]` | primary | `[FILL]` | `[FILL]` | NOT_VERIFIED | NOT_RUN |
| eval.default | evaluation | `[FILL]` | primary | `[FILL]` | `[FILL]` | NOT_VERIFIED | NOT_RUN |
| smoke.default | narrow runtime smoke | `[FILL]` | primary | `[FILL]` | `[FILL]` | NOT_VERIFIED | NOT_RUN |

Rules:

- After a command succeeds in the intended environment, update the same row with the exact command、date and evidence; do not append near-duplicates.
- When source/config/runtime changes make a command stale, mark it `STALE` before replacing it.
- Project-specific launchers, tmux wrappers and required environment variables belong in this registry or a linked canonical script.

## Protected paths

List project-owned files that generic refresh/migration must never overwrite, especially runtime model/config and durable memory.

## Validation map

Map claims to actual parse/test/runtime/experiment/hardware evidence.

## Resource and safety boundaries

Record exclusive resources, external-write rules, long-run system and hardware safety requirements.

## Cloud Pro handoff

- Git remote used by cloud reviewer:
- Branch or review branch:
- Whether Owner request authorizes in-scope commit+push: yes/no
- Drive release root/path:
- Local AI decisions reserved from cloud gate-setting:
