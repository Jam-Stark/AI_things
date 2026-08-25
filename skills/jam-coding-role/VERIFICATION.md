# Jam Coding Role v1.3.1 — Verification

## v1.3.1 delta

```text
Prompt generated from pushed branch/commit                 PASS
Repository URL、branch、full SHA and ZIP names present      PASS
Review type and Owner request auto-fill                     PASS
Missing review type leaves explicit Owner placeholder       PASS
Tracked dirty state rejected                                PASS
Local commit not present on remote-tracking branch rejected PASS
Compressed ZIP larger than 95 MiB rejected                  PASS
AGENTS automatic delegation project instruction present     PASS
PROJECT command registry present                            PASS
ARTIFACT_HANDOFF says compressed size, not raw size         PASS
Python syntax compilation                                   PASS
```

The v1.3.1 comparison did not modify v1.3.0 Codex hooks、team-state、memory、long-run、OMO、Claude or semantic ZIP implementation.

## Preserved v1.3.0 repository verification

```text
Python syntax compilation                               PASS
JSON / JSONC parse                                      PASS
TOML parse                                              PASS
Bundled unit tests                                      13 / 13 PASS
Minimal bootstrap creates no MEMORY.md or team state    PASS
Full optional bootstrap remains lazy-loaded             PASS
OpenCode optional docs are not globally preloaded       PASS
Standalone Claude Agent capability is denied            PASS
OMO Team Mode appears only with explicit flag           PASS
Coordination tooling defaults to inactive               PASS
Adaptive ephemeral Codex spawn remains allowed          PASS
Strict writer contract and exclusive lease checks       PASS
Candidate freeze requires formal review/QA purpose      PASS
Memory inbox is created only by a durable candidate      PASS
Long-run receipt works without activating team ledger   PASS
Artifact bundle requires explicit stage handoff          PASS
Checkpoint default exclusion and sensitive-name scan    PASS
PreToolUse no-op success emits no stdout                 PASS
PreToolUse deny omits unsupported `continue`             PASS
Malformed strict hook input fails closed                 PASS
Repo-local hooks resolve scripts from Git root            PASS
PostToolUse persistence is metadata-only                 PASS
SessionStart pending events deliver/archive once         PASS
95 MiB semantic standard-ZIP splitting                   PASS
Oversized checkpoint is not binary-sliced                PASS
```

## Evidence boundary

The checks establish package structure, helper behavior and synthetic local workflows. They do not establish:

```text
real production repository migration                    NOT RUN BY GENERIC PACK
real Codex MultiAgentV2 P2P session                     NOT RUN
real OMO Team Mode session                              NOT RUN
real tmux/GPU/IsaacLab training                         NOT RUN
Google Drive upload                                     NOT RUN
robot hardware action                                   NOT RUN
```

Project migrations must separately verify protected paths, local Git authorization, actual runtime evidence and any project-specific overlay.
