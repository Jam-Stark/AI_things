# Jam Coding Role v1.3.1 — Update Log

**Target branch:** `release/jam-coding-role-v1.3.0`  
**Update type:** minimal backward-compatible project-workflow delta

## 1. Route authority

The new Codex request default observed in production says not to proactively create sub-agents unless the user or project explicitly requires delegation、parallel work or a team. v1.3.1 does not attempt to outrank system/developer instructions. Instead, root `AGENTS.md` now explicitly serves as the repository workflow instruction that:

- automatically classifies every request as FAST、STANDARD or HIGH_RISK;
- requires useful delegation in STANDARD/HIGH_RISK when independent workstreams、specialist context or independent review justify it;
- permits zero agents when delegation adds no value;
- falls back to single-agent execution when a higher-level instruction explicitly makes sub-agents off-limits.

This restores automatic routing without falsely claiming that a repository file can override system/developer policy.

## 2. Cloud Pro review handoff

A cloud Pro reviewer can only inspect the remote repository state. Therefore an Owner-requested cloud review now requires this order:

```text
inspect diff -> commit in-scope Git changes -> push configured branch
-> verify remote commit == local HEAD -> pack/upload artifacts
-> generate PRO_REVIEW_PROMPT.md
```

The generated prompt includes repository URL、branch、full commit SHA、Drive release and ZIP names. It tells the cloud reviewer to think independently while respecting its lack of access to the local production environment, avoiding over-strict scientific gates and leaving local AI discretion over production feasibility. Review type is auto-filled when supplied; otherwise an explicit Owner placeholder remains.

## 3. Compressed ZIP wording

The 95 MiB boundary is the actual compressed file size of each generated `.zip`. It is not a limit on raw source/log/checkpoint input size. Existing semantic independent-ZIP splitting and oversized-checkpoint rules remain unchanged.

## 4. Project command registry

`.ai/PROJECT.md` now initializes canonical runtime/conda environments and exact train、eval and smoke commands, including CWD、environment ID、expected artifact、last verified date and evidence. Agents use verified commands first, mark stale entries before replacement, and update the same row after successful verification instead of accumulating near-duplicate commands.

## 5. Minimal-diff check

v1.3.1 intentionally does not alter Codex hook/P2P semantics、team-state/lease/freeze triggers、memory governance、long-run behavior、OMO Team Mode、Claude single-agent routing、semantic ZIP implementation、Pro_Space target or migration Git defaults.

Changed scope is limited to route authority、workflow wording、project command registry、cloud-review handoff documentation/config、one prompt helper/template、tests and version logs.

## 6. v1.3.1 verification

```text
pro_review_handoff unit tests                         PASS
published branch/commit prompt fields                 PASS
missing review type preserves Owner placeholder       PASS
unpushed local commit rejected                        PASS
compressed ZIP >95 MiB rejected                       PASS
AGENTS automatic route marker                         PASS
PROJECT command registry marker                       PASS
Python compilation                                    PASS
```

---

# Jam Coding Role v1.3.0 — Repository Update Log

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
