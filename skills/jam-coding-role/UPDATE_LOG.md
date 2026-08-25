# Jam Coding Role v1.3.1 — Update Log

**Target branch:** `release/jam-coding-role-v1.3.0`  
**Update type:** minimal backward-compatible project-workflow delta

## 2026-08-26 Pro full-delivery addendum — version unchanged

Cloud Pro review now produces two synchronized deliverables:

1. a concise five-item conversation response for the Owner;
2. `pro_delivery__full_review.zip` for the local Worker AI.

The full ZIP contains `FULL_REVIEW.md` and `LOCAL_WORKER_PARSE_PROMPT.md`. Concise item 5 provides the same copy-ready Worker prompt and the exact Drive task-folder/ZIP address. If upload is unavailable, the Pro must report `NOT_UPLOADED` and must not invent a URL.

Worker inputs and the Pro result share one immutable task folder. New Worker ZIPs and sidecars use `worker_delivery__`; the Pro full answer uses `pro_delivery__`. The stage packer now emits the Worker-prefixed names, and the prompt helper lists only Worker ZIPs while remaining backward-compatible with historical unprefixed releases.

This addendum does not change `VERSION`, route authority, Git publish checks, Codex hooks/P2P, team state, memory, long-run, OMO, Claude, 95 MiB compressed-size enforcement, Pro_Space target or migration Git defaults.

## 1. Route authority

The new Codex request default observed in production says not to proactively create sub-agents unless the user or project explicitly requires delegation、parallel work or a team. v1.3.1 does not attempt to outrank system/developer instructions. Instead, root `AGENTS.md` now explicitly serves as the repository workflow instruction that:

- automatically classifies every request as FAST、STANDARD or HIGH_RISK;
- requires useful delegation in STANDARD/HIGH_RISK when independent workstreams、specialist context or independent review justify it;
- permits zero agents when delegation adds no value;
- falls back to single-agent execution when a higher-level instruction explicitly makes sub-agents off-limits.

This restores automatic routing without falsely claiming that a repository file can override system/developer policy.

## 2. Cloud Pro review handoff

A cloud Pro reviewer can only inspect the remote repository state. Therefore an Owner-requested cloud review requires this order:

```text
inspect diff -> commit in-scope Git changes -> push configured branch
-> verify remote commit == local HEAD -> pack/upload Worker artifacts
-> generate PRO_REVIEW_PROMPT.md -> Pro review
-> upload pro_delivery__full_review.zip into the same task folder
```

The generated prompt includes repository URL、branch、full commit SHA、Drive task folder and Worker ZIP names. It tells the cloud reviewer to think independently while respecting its lack of access to the local production environment, avoiding over-strict scientific gates and leaving local AI discretion over production feasibility. Review type is auto-filled when supplied; otherwise an explicit Owner placeholder remains.

## 3. Compressed ZIP wording

The 95 MiB boundary is the actual compressed file size of each generated `.zip`. It is not a limit on raw source/log/checkpoint input size. Existing semantic independent-ZIP splitting and oversized-checkpoint rules remain unchanged.

## 4. Project command registry

`.ai/PROJECT.md` initializes canonical runtime/conda environments and exact train、eval and smoke commands, including CWD、environment ID、expected artifact、last verified date and evidence. Agents use verified commands first, mark stale entries before replacement, and update the same row after successful verification instead of accumulating near-duplicate commands.

## 5. Minimal-diff check

v1.3.1 intentionally does not alter Codex hook/P2P semantics、team-state/lease/freeze triggers、memory governance、long-run behavior、OMO Team Mode、Claude single-agent routing、semantic ZIP splitting algorithm、Pro_Space target or migration Git defaults.

The addendum scope is limited to cloud-Pro prompt/output contract、same-folder delivery naming、prompt/stage helpers、artifact docs/config、tests and logs.

## 6. Verification

```text
published branch/commit prompt fields                    PASS
concise five-item Owner output contract                  PASS
full-review ZIP contract                                 PASS
copy-ready local Worker parse prompt                     PASS
Worker/Pro same-folder prefixes                          PASS
prompt helper excludes Pro ZIP from Worker input list    PASS
historical unprefixed Worker ZIP fallback                PASS
compressed ZIP >95 MiB rejection                        PASS
stage packer Worker-prefixed ZIP/sidecar generation      PASS
Python compilation                                       PASS
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
- Oversized bundles are split into independently readable standard ZIP files by meaning.
- Every multi-ZIP release includes a plain-text bundle index describing order, purpose, contents, compressed size, and exclusions.
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
