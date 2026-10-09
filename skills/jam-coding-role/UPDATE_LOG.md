# v1.6.0 · 2026-10-09

- execution lead 双入口与阶段授权；lead 可亲自组队，阶段内普通修复与已批迭代继续执行。
- 角色能力单源生成；Outside view 独立上下文、只读建议。
- Owner 交付原则完整落在 ROLE，精简重复入口与角色组织规则。
- 修正“修改奖励就上报”为“超出已批准范围才上报”；清理 managed block 外冲突的 Main 独占组织权。
- 阶段事件与实际传输分离，保留真实身份、共同额度、Astra 及未结束运行。
- 实际证据与能力限制见 VERIFICATION；不把静态更新宣称为全功能运行通过。
- 通用发布：默认使用 generic profile，清除私人路径/远程目标/站立上传授权；保留可选领域角色和安装项目自己的事实。
- 通用 fresh init、预检、refresh 幂等性及无关设置保留通过；公开材料分离既有本机运行观察与跨宿主保证。

# 历史记录（下列旧版检查不作为 v1.6.0 验收）

## Jam Coding Role v1.5.1 — Repository Update Log

## v1.5.1 — 2026-10-02

GPT-6.1 Sol 五档静态角色；root Main 与 child 身份区分；生成策略贯穿角色、旧 hook、新 wrapper 与预检；普通团队控制验证实际归属；init/refresh/migration 共用生成路径。Main 配置、项目事实与既有配额/长跑状态保留。此项取代先前版本的当前说明；下文为历史。


历史 v1.5.0：默认 Sol/medium、子任务上限 5、迁移保留 Main context/compact。v1.3.0 内容仅为历史，不代表当前 hooks 行为；当前 SessionStart/PostCompact 不自动归档未处理事件。


**Update date:** 2026-08-23  
**Target repository:** `Jam-Stark/AI_things`  
**Target path:** `skills/jam-coding-role/`  
**Release branch:** `release/jam-coding-role-v1.3.0`

## Purpose

This repository update publishes the approved v1.3.0 adaptive workflow and folds in production fixes discovered while deploying it into DoorDog. It does not introduce a new workflow version; it repairs the v1.3.0 implementation so the published generic pack matches the actual Codex hook protocol and the observed `Pro_Space` upload boundary.

## Codex hook protocol fixes

1. `PreToolUse` now has dedicated `pre_allow()` and `pre_deny()` paths.
   - no-op allow exits `0` with no stdout;
   - contextual allow emits only `hookSpecificOutput.additionalContext`;
   - deny emits only the supported `PreToolUse` permission decision;
   - `continue`, `stopReason`, and `suppressOutput` are never returned by `PreToolUse`.
2. `PostToolUse` and `SessionStart` retain the common success shape because those events support it.
3. Every repository-local hook command resolves the script from:

   ```bash
   $(git rev-parse --show-toplevel)
   ```

   so Codex can start from any repository subdirectory.
4. Hook payload parsing and Git-root resolution now fail visibly. Strict `PreToolUse` enforcement fails closed instead of silently allowing malformed input.
5. `PostToolUse` stores only coordination metadata. Prompts, message bodies, command output, and full tool responses are not copied into the JSONL ledger.
6. `SessionStart` delivers pending long-run events once, marks them delivered, archives them, and removes the pending copy so later sessions do not repeatedly inject the same event.

## Artifact handoff fixes

- The default cloud-facing ZIP ceiling is `95 MiB` (`99,614,720` bytes).
- Oversized bundles are split into independently readable standard ZIP files by meaning, for example:
  - `source_and_configs.zip`;
  - `logs_and_metrics.zip`;
  - `plots_and_evidence.zip`;
  - `checkpoints_part01.zip`.
- Every multi-ZIP release includes a plain-text `BUNDLE_INDEX.md` describing order, purpose, contents, compressed size, and exclusions.
- Stage bundle indexes do not use SHA-256.
- `.z01/.z02/.zip`, `.zip.001`, and similar reconstruction-dependent split volumes are prohibited.
- A single checkpoint over the limit is excluded unless an explicit authenticated rclone exception is approved. It is never binary-sliced into unusable cloud fragments.

## Preserved v1.3.0 behavior

- FAST / STANDARD / HIGH_RISK routing remains the default.
- Team ledger, disk contracts, leases, candidate freeze, memory curation, long-run supervision, and artifact handoff remain trigger-driven facilities.
- Codex MultiAgentV2 peer communication remains available without persistent team state.
- Standalone Claude Code remains single-agent.
- OMO keeps its own ordinary delegation and optional Team Mode semantics.
- Migration tools do not commit or push without current explicit Owner authorization.

## Verification of the exact repository files

```text
Bundled unit tests                                           13 / 13 PASS
PreToolUse no-op success has empty stdout                    PASS
PreToolUse deny omits unsupported common fields              PASS
Malformed PreToolUse input fails closed                      PASS
Git-root resolution failure fails closed                     PASS
All repo-local hook commands resolve from git root            PASS
PostToolUse metadata redaction                               PASS
SessionStart deliver-once/archive behavior                   PASS
Inactive/strict optional team-state behavior                 PASS
95 MiB semantic standard-ZIP splitting                       PASS
Oversized checkpoint is not binary-sliced                    PASS
Python compilation                                           PASS
JSON and TOML parsing                                        PASS
```

## Branch policy

`main` is the published source of truth. Among release/development branches, only the current `release/jam-coding-role-v1.3.0` branch should remain after merge. Historical version branches are not part of the versioning scheme; release history belongs in this file and `CHANGELOG.md`.

## v1.5.0 — 2026-09-23

Main/App model ownership; preserved explicit Main context budgets; five-child ceiling; GPT-6 Sol/medium default and Luna/Sol roles; one Astra/medium child identity per team; model-gated notes/compact; bounded Main-to-Main outbox; opt-in Linux owned-tool cleanup. No Jev integration. New Codex bootstrap installs v150-assets; refresh does not silently overwrite old project configs. Existing targets use the reviewed migration kit. Native hooks/transport/model switching require local effective-runtime acceptance. Legacy long-run, artifact, memory and coordination scripts are preserved, not rewritten.
