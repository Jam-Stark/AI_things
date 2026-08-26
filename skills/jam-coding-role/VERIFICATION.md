# Jam Coding Role v1.3.2 — Verification

## v1.3.2 delta

```text
Mandatory delegation gate in AGENTS                     PASS
STANDARD/HIGH_RISK proactive spawn wording              PASS
Non-FAST NO_DELEGATION_REASON requirement               PASS
Codex TEAM runtime-specific proactive gate              PASS
Cloud Pro prompt uses Owner chat transfer               PASS
Prompt does not require Pro Drive upload                PASS
Local Worker prompt says not to search Drive            PASS
Project-configured Pro review destination               PASS
Path traversal in Pro document root rejected            PASS
Published branch/commit prompt fields                   PASS
Worker ZIP list and 95 MiB compressed limit             PASS
Python syntax compilation                               PASS
```

## Preserved behavior

```text
FAST remains Main-direct                                PASS BY STATIC REVIEW
Persistent team facilities remain trigger-driven        PASS BY STATIC REVIEW
Git publish verification remains required               PASS
Codex hook/P2P implementation unchanged                 PASS BY DIFF BOUNDARY
Team-state/lease/freeze implementation unchanged        PASS BY DIFF BOUNDARY
Memory/long-run/OMO/Claude unchanged                    PASS BY DIFF BOUNDARY
Worker semantic ZIP implementation unchanged            PASS BY DIFF BOUNDARY
Pro_Space Worker artifact target unchanged              PASS BY DIFF BOUNDARY
```

## Evidence boundary

These checks establish prompt/helper behavior and static routing rules. They do not prove that every future Main session will delegate optimally, nor do they establish real production upload, IsaacLab, GPU, training, evaluation or hardware behavior.
