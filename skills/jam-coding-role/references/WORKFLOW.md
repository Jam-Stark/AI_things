<!-- managed-by: jam-coding-role; file: WORKFLOW.md -->
# Adaptive workflow v1.3.1

## 1. Light kernel, automatic routing

The default is prompt-level coordination. Persistent ledger, disk contracts, leases, candidate freeze, memory curation, long-run supervisor and artifact handoff exist as capabilities, not mandatory stages.

Main must choose FAST、STANDARD or HIGH_RISK automatically. A generic runtime preference against proactive sub-agents is satisfied by this explicit project instruction: when STANDARD/HIGH_RISK criteria below justify delegation, Main may and should use the minimum useful agents without waiting for the user to request a team. A higher-level system/developer prohibition still wins and requires single-agent fallback.

## 2. FAST

Use for simple QA, read-only lookup, prose, typo, clear config adjustment, temporary implementation/test, or one bounded local change.

```text
minimal context -> inspect/change -> one matching proof -> report
```

Default: Main works directly. No team, ledger, freeze, curator or artifact bundle.

## 3. STANDARD

Use for ordinary cross-file implementation, debugging and design.

```text
route context -> trace real path -> concise acceptance
-> smallest end-to-end implementation -> claim-matched evidence -> integrate
```

Use 0–3 agents only when they add independent value. Delegation is automatic when there are independent workstreams, specialist context or a material need for independent review; otherwise Main stays direct. P2P may carry technical findings directly; a disk-backed contract is not required for ordinary ephemeral tasks.

## 4. HIGH_RISK

This is an automatically detected authorization/risk overlay for destructive operations, external writes, hardware actions, material cross-subsystem redesign, hard-to-reverse data changes, or an unapproved expensive run.

Main first states scope, cost/resources, stop condition and rollback, then waits for Owner approval before side effects. Read-only planning or research may be delegated before approval. Complexity alone does not make work HIGH_RISK.

## 5. Facility trigger matrix

| Facility | Enable only when |
|---|---|
| Team ledger | multiple writers, exclusive resources, cross-session task state, formal review/QA, or Owner request |
| Disk task contract | Main explicitly registers a task for persistent tracking |
| Lease | actual write-path or exclusive GPU/process/display/port/hardware/output ownership |
| Candidate freeze | formal code/semantic review, formal runtime QA, or release qualification |
| Memory curator | a validated durable memory candidate exists |
| Long-run supervisor | durable tmux receipt, checkpoint/eval continuation or pending event is useful |
| Artifact handoff | Owner request or explicit stage deliverable |

Read-only agents do not receive leases. Simple QA and temporary tests do not create a ledger or freeze.

## 6. P2P and authority

- `PEER_FINDING`: exact source/API/runtime evidence or targeted defect;
- `PEER_REQUEST`: bounded diagnosis or read-only request within existing authority;
- `AUTHORITY_REQUEST`: scope, acceptance, revision, write/resource ownership, Git, external write or hard stop, sent to Main.

Main remains the sole control plane. Do not mirror every peer message into Main; summarize only material state changes.

## 7. Commands and environments

Before training、evaluation、rendering or deployment, use the canonical environment and exact command registry in `.ai/PROJECT.md`. Do not reconstruct commands from memory when a verified entry exists. When a command is absent or stale, trace the real entrypoint/config, run the narrowest proof, then update the registry with the verified command and date.

## 8. Evidence and closure

Evidence matches the claim: inspected, static, test, runtime, experiment, hardware. Do not repeat the same proof for reassurance.

Only close facilities that were actually activated. Ordinary work ends when the requested outcome is complete, relevant evidence is recorded, one final path/diff check is done, and no writer or exclusive resource remains active.
