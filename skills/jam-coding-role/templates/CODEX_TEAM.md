# Codex MultiAgentV2 routing

## Proactive delegation gate

- FAST: Main direct.
- STANDARD: before deep work, Main checks for independent lanes、specialist context、material independent review/QA value、or material speed/context benefit. If any trigger is true, Main must spawn the minimum useful 1–3 focused agents immediately. Do not wait for the user to say “team”, and do not postpone spawn until Main has already done the work intended for the child.
- HIGH_RISK: Owner approval remains required before destructive/external/hardware/expensive side effects. Safe read-only scout、planner、source-verification or reviewer lanes follow the same proactive gate and may start before approval.
- A non-FAST single-agent route requires a concrete `NO_DELEGATION_REASON`: no independent value、tightly coupled cheaper direct work、or higher-level/runtime restriction.

Current local Codex releases can delegate when applicable project or skill instructions request it; this adapter is that explicit request. Main still waits for child results, integrates them, and closes completed threads.

## P2P

Use `PEER_FINDING` and `PEER_REQUEST` for technical information inside existing authority. Send `AUTHORITY_REQUEST` to Main for scope、acceptance、revision、write/resource、Git、external write or hard stop.

## Optional state

Activate `.ai/TEAM_STATE.md` only for multiple writers、exclusive resources、cross-session state、formal review/QA or Owner request. In adaptive mode unregistered ephemeral work remains allowed. In strict mode configured writer/reviewer/runtime roles require valid contracts.

Lease only actual write paths and exclusive resources. Freeze only formal review/QA candidates. Memory curator and artifact handoff are trigger-driven, not closure stages.
