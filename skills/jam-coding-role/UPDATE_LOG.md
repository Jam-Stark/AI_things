# Jam Coding Role v1.3.2 — Update Log

**Target branch:** `release/jam-coding-role-v1.3.0`  
**Update type:** minimal production fix

## 1. Proactive delegation

Production use showed that v1.3.1 still allowed Main to acknowledge multi-agent value without actually spawning agents. v1.3.2 adds a mandatory delegation gate before substantive work on every non-FAST request.

Main checks independent lanes、specialist context、material review/QA value and material speed/context benefit. When any trigger is true and the runtime permits sub-agents, Main must spawn the minimum useful agents before doing the delegated work itself. Waiting for the Owner to say “team”, or saying delegation could happen later, is not compliant. A non-FAST single-agent route records `NO_DELEGATION_REASON`.

This matches Codex's documented behavior: current local Codex can delegate when applicable `AGENTS.md` or skill instructions request it. FAST remains Main-direct; ledger、lease、freeze and other persistent facilities remain trigger-driven.

## 2. Cloud Pro delivery transport

The Google Drive connector available to Cloud Pro is treated as a source-reading mechanism, not a reliable ZIP upload channel. v1.3.2 separates transport:

```text
Worker artifacts -> Google Drive
Cloud Pro full ZIP -> attached in the Pro conversation
Owner -> uploads that ZIP in the local Worker conversation
Local Worker -> preserves/extracts it under the project Pro review document root
```

The Pro prompt no longer asks the Pro model to upload its answer ZIP to Drive or provide a Pro ZIP Drive URL. It attaches `pro_delivery__full_review.zip` in the current conversation or reports `NOT_ATTACHED`.

The local Worker prompt states that the ZIP is an Owner-provided conversation attachment, not a Drive artifact. The destination is derived from `[pro_review].local_review_root` in `.ai/artifact-sync.toml`, with a release/commit-specific subdirectory.

## 3. Minimal-diff boundary

Changed:

```text
VERSION
AGENTS / WORKFLOW / CODEX_TEAM delegation wording
PROJECT Pro review document root
ARTIFACT_HANDOFF transport contract
ARTIFACT_SYNC pro-review transport fields
PRO_REVIEW_PROMPT
pro_review_handoff helper
tests / README / CHANGELOG / verification / update guide
```

Not changed:

```text
Codex hook protocol
P2P message semantics
team-state activation、lease、freeze or verdict implementation
memory governance
long-run supervisor
OMO Team Mode
Claude single-agent route
Worker semantic ZIP packer and 95 MiB compressed-size rule
Pro_Space Worker artifact folder ID
migration Git defaults
```

## 4. v1.3.2 verification

```text
pro_review_handoff targeted tests                         8 / 8 PASS
published branch/commit and Worker ZIP source lock        PASS
Owner-chat transfer wording                               PASS
Drive search for Pro ZIP explicitly prohibited            PASS
project-configured local Pro review destination            PASS
invalid destination traversal rejected                    PASS
mandatory delegation markers                              PASS
NO_DELEGATION_REASON marker                               PASS
compressed Worker ZIP >95 MiB rejection                   PASS
Python syntax compilation                                 PASS
```

---

# Jam Coding Role v1.3.1 — Update Log

## 2026-08-26 Pro full-delivery addendum — superseded transport

v1.3.1 introduced a concise Owner response plus `pro_delivery__full_review.zip` for the local Worker AI. It originally asked the cloud Pro to place the ZIP in the same Drive task folder as Worker inputs. v1.3.2 preserves the two-tier output but supersedes only the transport: the Pro ZIP is now attached in the Pro conversation and transferred by Owner.

## Route authority

v1.3.1 declared root `AGENTS.md` as the repository workflow instruction that automatically classifies FAST、STANDARD or HIGH_RISK and permits useful delegation without waiting for the user to say “team”, while higher-level prohibitions still win.

## Git-published cloud handoff

The cloud reviewer still requires:

```text
inspect diff -> commit in-scope Git changes -> push configured branch
-> verify remote commit == local HEAD -> pack/upload Worker artifacts
-> generate PRO_REVIEW_PROMPT.md
```

The prompt includes repository URL、branch、full commit SHA、Drive Worker folder and ZIP names. Review type is auto-filled when supplied; otherwise an Owner placeholder remains.

## Compressed ZIP wording

The 95 MiB boundary is the actual compressed file size of each generated `.zip`, not raw source/log/checkpoint input size. Semantic independent-ZIP splitting and oversized-checkpoint rules remain unchanged.

## Project command registry

`.ai/PROJECT.md` initializes canonical runtime/conda environments and exact train、eval and smoke commands, including CWD、environment ID、expected artifact、last verified date and evidence.

---

# Jam Coding Role v1.3.0 — Repository Update Log

## Codex hook protocol fixes

- `PreToolUse` uses dedicated event-specific allow/deny behavior and never emits unsupported `continue`.
- repository-local hook commands resolve from `$(git rev-parse --show-toplevel)`.
- malformed strict input and Git-root failures fail visibly/closed.
- `PostToolUse` stores coordination metadata only.
- `SessionStart` delivers pending events once, archives them and removes pending copies.

## Artifact handoff fixes

- default cloud-facing ZIP ceiling: 95 MiB compressed;
- semantic independently readable ZIP splitting;
- plain-text bundle index;
- no `.z01/.z02/.zip.001` split volumes;
- oversized checkpoint excluded or handled by explicit rclone exception, never binary-sliced.

## Preserved v1.3.0 behavior

- FAST / STANDARD / HIGH_RISK routing;
- trigger-driven team ledger、contracts、leases、freeze、memory curator、long-run and artifact handoff;
- Codex MultiAgentV2 P2P;
- standalone Claude single-agent;
- OMO ordinary delegation and optional Team Mode;
- no migration commit/push without current Owner authorization.

## Branch policy

`main` is the published source of truth. Among release/development branches, only the current `release/jam-coding-role-v1.3.0` branch should remain after merge. Historical release history belongs in `CHANGELOG.md` and this file.
