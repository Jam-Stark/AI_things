---
name: jam-coding-role
description: Install or update a project AI workflow with autonomous execution teams, independent outside view, clear Owner delivery, and task-specific memory and scientific facilities.
---

# Jam Coding Role v1.6.0

Use actual project source, current authority and evidence. Preserve project facts, research edits and active work. Main model/effort belong to the App. Read `references/ROLE.md` for stable behavior and the Owner delivery principle; other documents are task routes, not a full-reading checklist.

Small work runs directly. Delegate when there is an independent output or specialist context. For a complete approved stage, use an execution lead: either an independent root or a Planner-spawned child. Both organize their team and complete authorized work without per-command approval. Keep actual runtime identity separate from delegated responsibility.

## Read as needed

- Team/grants/communication: `references/EXECUTION_TEAM.md`, generated `.codex/TEAM.md`.
- Reconsidering the problem: `references/OUTSIDE_VIEW.md`, fresh context, advisory only.
- Role and effort: `references/MODEL_ROUTING.md`; context behavior: `references/CONTEXT_POLICY.md`.
- Shared writes/resources: `references/TEAM_STATE.md`; durable jobs: `references/LONG_RUNNING_TASKS.md`.
- Scientific claims: `references/SCIENTIFIC_ENGINEERING.md`; stage planning: `references/STAGE_DECISION.md`.
- Reusable facts: `references/MEMORY_GOVERNANCE.md`; requested handoff: `references/ARTIFACT_HANDOFF.md`.
- Design references: `references/WORKFLOW_SOURCES.md`; installation and evidence limits: `README.md`, `VERIFICATION.md`.

## Install or update

```bash
python3 scripts/bootstrap.py init /path/to/project --runtime codex
python3 scripts/bootstrap.py refresh /path/to/project --runtime codex
python3 scripts/bootstrap.py refresh /path/to/project --runtime codex --apply
python3 scripts/migrate_v160.py --root /path/to/project
python3 scripts/migrate_v160.py --root /path/to/project --apply
```

Init, refresh and migration default to dry-run; use `--apply` to write. Fresh projects use the generic role profile; existing projects retain their installed profile. The optional `doordog` profile adds IsaacLab roles (`bootstrap.py --role-profile doordog`, or `migrate_v160.py --profile doordog`); dependency paths and project facts stay in the project. See `examples/migrate-existing-project.md`.

All three commands share the role generator and installation source. Preserve project overlays, memory, credentials, unrelated hooks and existing process/state records. Remove known obsolete organizational rules, including conflicting ones outside managed entry blocks; preserve domain constraints. Optional artifact destinations start unconfigured and require project authorization.

Role capabilities, effort variants and model mappings come from `scripts/role-policy.json`. Team seats are shared, not multiplied per parent. Keep the persistent Astra identity. Do not install a global session bus, add silent transport fallbacks or confuse queued, delivered and handled.

Use a new session to load the new registry and instructions. Register hooks through the supported host path and review trust through `/hooks`; never edit trust automatically. Static parsing, actual helper execution, native team operation and cross-root/Dot delivery are separate evidence. Installation does not automatically run training, a model matrix, Git publication or unrelated audits. OMO/standalone Claude retain their own runtime behavior.
