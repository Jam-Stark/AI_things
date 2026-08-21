---
name: jam-coding-role
description: Bootstrap, audit, or evolve a lean project AI coding role and workflow. Use for new repositories, Codex/OMO integration, multi-agent routing, file-based memory, scientific/robotics evidence discipline, or simplifying duplicated agent instructions.
---

# Jam Coding Role

Use this skill when the user asks to create, migrate, audit, or improve project-level AI behavior and workflow.

The pack is intentionally layered:

- `references/ROLE.md`: stable universal coding behavior;
- `references/WORKFLOW.md`: adaptive execution, multi-agent, memory, evidence, and adapter rules;
- `references/SCIENTIFIC_ENGINEERING.md`: optional ML/RL/simulation/robotics extension;
- `references/PROJECT_GROWTH.md`: trigger-based workflow growth;
- `templates/`: thin project entrypoint, project overlay, memory router, and runtime adapters;
- `scripts/bootstrap.py`: safe init/refresh/audit helper;
- `examples/DoorDog-A2_Piper-migration.md`: concrete migration from a mature Codex/OMO robotics project.

## Operating procedure

1. **Inspect before installing**
   - Read current root instructions, runtime adapters/configs, memory routes, and actual code entrypoints.
   - Identify duplicated rules, stale paths, contradictory settings, and project-specific facts mixed into universal policy.

2. **Choose the lowest maturity level**
   - Start from `references/PROJECT_GROWTH.md`.
   - Do not install team, memory, scientific, or release ceremony without a concrete trigger.

3. **Create one canonical hierarchy**
   - universal behavior -> `.ai/ROLE.md`;
   - project truth and overrides -> `.ai/PROJECT.md`;
   - workflow, team, memory, and evidence -> `.ai/WORKFLOW.md`;
   - optional research rules -> `.ai/SCIENTIFIC_ENGINEERING.md`;
   - root `AGENTS.md` and runtime files remain thin routers/adapters.

4. **Preserve project value**
   - Keep proven project-specific memory, commands, safety rules, role configs, and artifact contracts.
   - Remove only duplication, stale references, conflicting authority, and ceremony that no longer changes decisions.

5. **Define acceptance before migration**
   - every supported runtime reaches the same canonical policy;
   - no adapter refers to deleted files or obsolete gates;
   - model, effort, concurrency, and tool settings have one config source;
   - project-specific invariants are retained;
   - existing files are not overwritten silently.

6. **Verify at the matching level**
   - inspect paths and references;
   - parse relevant config;
   - run the smallest runtime discovery or smoke needed by the migration;
   - do not claim agent spawning or workflow behavior from static files alone.

## Bootstrap commands

From this skill directory:

```bash
python scripts/bootstrap.py init /path/to/project \
  --profile scientific \
  --runtime codex \
  --runtime omo
```

Add `--runtime claude` when the project also needs a thin `CLAUDE.md` adapter.

Audit a project:

```bash
python scripts/bootstrap.py audit /path/to/project \
  --profile scientific \
  --runtime codex \
  --runtime omo
```

Refresh only managed upstream core files:

```bash
python scripts/bootstrap.py refresh /path/to/project \
  --profile scientific
```

`init` never overwrites existing files. `refresh` only replaces files marked as managed by this pack; it does not overwrite `AGENTS.md`, `.ai/PROJECT.md`, `MEMORY.md`, or runtime adapters.

## Attribution

The concise core is inspired by the four ideas in [`multica-ai/andrej-karpathy-skills`](https://github.com/multica-ai/andrej-karpathy-skills): surface assumptions, prefer the simplest sufficient solution, make surgical changes, and work toward explicit verifiable goals. This pack is an independent project-oriented adaptation that adds runtime adapters, adaptive multi-agent coordination, file-based memory, evidence levels, and scientific/robotics discipline.
