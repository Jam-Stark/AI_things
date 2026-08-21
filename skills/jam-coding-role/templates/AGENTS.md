# Project AI entrypoint

This file is the repository-level authority router for coding agents.

## Read order

1. `.ai/ROLE.md` — stable coding behavior;
2. `.ai/PROJECT.md` — project truth, invariants, commands, and overrides;
3. `.ai/WORKFLOW.md` — non-trivial work, delegation, memory, and evidence;
4. `.ai/SCIENTIFIC_ENGINEERING.md` — only when the project or task is experimental, ML/RL, simulation, robotics, benchmark, or hardware related;
5. `MEMORY.md` — only when prior decisions, failures, progress, or run evidence matter.

Runtime-specific files such as `.codex/*`, `.omo/*`, `CLAUDE.md`, and `.github/instructions/*` are adapters. They may map tools and roles but must not redefine or weaken the files above.

## Authorization

- Read, explain, diagnose, review, research, and plan requests are read-only unless the user also asks for changes.
- Build, fix, refactor, or update requests authorize exact in-scope local edits and matching non-destructive verification.
- Ask before destructive operations, external writes, material scope expansion, expensive or long runs not already authorized, or hardware actions.
- Protect existing dirty work. Do not reset, stash, discard, overwrite, commit, push, or merge without the applicable authorization.

## Completion

Do not claim success without evidence matching the claim. Report changed paths, actual evidence, and anything not run or still uncertain.
