# v1.6.0 · 2026-10-09

- execution lead 双入口与阶段授权；lead 可亲自组队，阶段内普通修复与已批迭代继续执行。
- 角色能力单源生成；Outside view 独立上下文、只读建议。
- Owner 交付原则完整落在 ROLE，精简重复入口与角色组织规则。
- 修正“修改奖励就上报”为“超出已批准范围才上报”；清理 managed block 外冲突的 Main 独占组织权。
- 阶段事件与实际传输分离，保留真实身份、共同额度、Astra 及未结束运行。
- 实际证据与能力限制见 VERIFICATION；不把静态更新宣称为全功能运行通过。
- 通用发布：默认使用 generic profile，清除私人路径/远程目标/站立上传授权；保留可选领域角色和安装项目自己的事实。
- 通用 fresh init、预检、refresh 幂等性及无关设置保留通过；公开材料分离既有本机运行观察与跨宿主保证。

# 历史版本（不代表 v1.6.0 当前行为）

## Jam Coding Role v1.5.1 — Adaptive Coordination

## v1.5.1 — 2026-10-02

GPT-6.1 Sol 五档静态角色；root Main 与 child 身份区分；生成策略贯穿角色、旧 hook、新 wrapper 与预检；普通团队控制验证实际归属；init/refresh/migration 共用生成路径。Main 配置、项目事实与既有配额/长跑状态保留。此项取代先前版本的当前说明；下文为历史。


历史 v1.5.0：默认 Sol/medium、子任务上限 5、迁移保留 Main context/compact。v1.3.0 内容仅为历史，不代表当前 hooks 行为；当前 SessionStart/PostCompact 不自动归档未处理事件。


> Release lineage: `AI_things/main` previously carried v1.0.0. v1.1.0 and v1.2.0 were reviewed delivery candidates but were not the published repository version. v1.3.0 is the consolidated repository release that incorporates the approved runtime, language, stage-decision, artifact, P2P, team-state, memory and lean-routing changes.

## 2026-08-23 repository update

- Corrected `PreToolUse` output to use dedicated event-specific allow/deny behavior; unsupported `continue` is no longer emitted.
- Changed every repo-local hook command to resolve from `$(git rev-parse --show-toplevel)`.
- Made hook JSON parsing and Git-root discovery fail visibly; strict PreToolUse enforcement now fails closed.
- Reduced PostToolUse persistence to coordination metadata only.
- Made SessionStart pending-event delivery one-shot with delivered/archive state.
- Added a 95 MiB cloud ZIP ceiling, semantic standard-ZIP splitting, `BUNDLE_INDEX.md`, split-volume rejection, and oversized-checkpoint handling.
- Added `UPDATE_LOG.md` as the detailed implementation and verification record.

## Summary

v1.3.0 keeps the portable behavior kernel and advanced coordination capabilities from v1.2.0, but changes the default from persistent workflow infrastructure to a lean, route-triggered model.

## Added

- FAST / STANDARD / HIGH_RISK routing with explicit activation rules.
- Independent control-facility trigger matrix for ledger、lease、freeze、verdict、curator、long-run and artifact handoff.
- Lazy team-state activation with `adaptive` and `strict` modes.
- `team_state.py status/activate/deactivate/hook-check-spawn` commands.
- Explicit `--confirm-stage-handoff` requirement for artifact packing/upload.
- Opt-in migration Git flags: `--checkpoint-commit` and `--migration-commit`, plus `--confirm-user-authorized-commit` for actual Git writes.

## Changed

- Root `AGENTS.md` is now a route table. Only core documents are read by default; optional documents are conditional.
- Ordinary Codex spawns no longer require a disk-backed task contract.
- Codex hooks are no-op while coordination is inactive and do not create runtime state.
- Team ledger is no longer a prerequisite for FAST or ordinary STANDARD tasks.
- Candidate freeze is limited to formal review/QA, ambiguous dirty/shared candidates or cross-session review.
- Leases are limited to actual concurrent writers or exclusive resources; read-only agents are not leased.
- Memory curator is candidate-triggered rather than a closure stage.
- Artifact handoff is explicit rather than automatic at task completion.
- OMO Team Mode defaults to disabled.
- OpenCode and Claude preload only the core routing files.
- A single authorized long run may use a receipt/tmux without activating the full team ledger.

## Preserved

- Codex MultiAgentV2 P2P communication.
- Main-only authority for scope、acceptance、resources、Git and final integration.
- Standalone Claude Code single-agent routing.
- OMO official ordinary delegation and Team Mode semantics.
- Active memory restructuring capability.
- Pro_Space create-only artifact target.
- Chinese native-language expression rules.
- Claim-matched scientific evidence and hardware safety boundaries.

## Git behavior

The migration tool defaults to no commits. A checkpoint commit and migration commit are created only when the caller supplies explicit flags under current Owner authorization. The tool never pushes.

## v1.5.0 — 2026-09-23

Main/App model ownership; preserved explicit Main context budgets; five-child ceiling; GPT-6 Sol/medium default and Luna/Sol roles; one Astra/medium child identity per team; model-gated notes/compact; bounded Main-to-Main outbox; opt-in Linux owned-tool cleanup. No Jev integration. New Codex bootstrap installs v150-assets; refresh does not silently overwrite old project configs. Existing targets use the reviewed migration kit. Native hooks/transport/model switching require local effective-runtime acceptance. Legacy long-run, artifact, memory and coordination scripts are preserved, not rewritten.
