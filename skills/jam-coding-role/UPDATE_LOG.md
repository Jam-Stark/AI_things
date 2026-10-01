# Jam Coding Role v1.5.0 — Repository Update Log

当前本地版本为 v1.5.0：默认 Sol/medium、子任务上限 5、迁移保留 Main context/compact。v1.3.0 内容仅为历史，不代表当前 hooks 行为；当前 SessionStart/PostCompact 不自动归档未处理事件。


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
