# Jam Coding Role Changelog

## 1.3.2 — Proactive delegation and Owner-transferred Pro package

- Added a mandatory delegation gate before substantive work on every non-FAST request.
- When independent lanes、specialist context、material independent review/QA value or material parallel/context benefit exists, Main must immediately spawn the minimum useful agents rather than waiting for the Owner to say “team” or completing delegated work itself first.
- A non-FAST single-agent route now requires a concrete `NO_DELEGATION_REASON`; FAST remains Main-direct and persistent coordination facilities remain trigger-driven.
- Changed Cloud Pro full-delivery transport: Google Drive contains Worker input artifacts only. The Pro attaches `pro_delivery__full_review.zip` in its conversation; Owner uploads it in the local Worker conversation.
- Added a project-configured Pro review document root and deterministic local destination for preserving/extracting the Owner-transferred ZIP.
- Updated the Pro prompt/helper、artifact handoff contract、project/config templates、tests and existing-project update guide.

## 1.3.1 — Minimal routing and cloud-review handoff update

- Declared root `AGENTS.md` as the repository's project-level workflow authority, below system/developer/Owner instructions but above runtime defaults and ordinary adapters.
- Made FAST/STANDARD/HIGH_RISK classification automatic. STANDARD/HIGH_RISK may delegate without waiting for the user to say “team” when independent workstreams、specialist context or independent review justify it; explicit higher-level sub-agent bans still force single-agent fallback.
- Added a canonical environment and command registry to `.ai/PROJECT.md`, including initial train/eval/smoke placeholders and maintenance rules.
- Made cloud Pro handoff a Git-published handoff: commit in-scope changes、push、verify remote commit、pack/upload artifacts、then generate the review prompt.
- Added `PRO_REVIEW_PROMPT.md` and `pro_review_handoff.py` with repository URL、branch、commit、Drive release、ZIP list、review type and Owner request.
- Explicitly stated that 95 MiB limits the final compressed size of each generated ZIP, not raw input size.
- Added `UPDATE_GUIDE_1.3.1.md` for existing project installations.

### v1.3.1 Pro full-delivery addendum — superseded transport

- Split the cloud Pro response into a concise five-item Owner view and one detailed `pro_delivery__full_review.zip` for the local Worker AI.
- The detailed ZIP contains `FULL_REVIEW.md` and `LOCAL_WORKER_PARSE_PROMPT.md`.
- The original addendum placed Worker inputs and Pro outputs in one Drive task folder. v1.3.2 supersedes only this transport detail: the Pro ZIP is now attached in the Pro conversation and transferred by Owner.

---

# Jam Coding Role v1.3.0 — Adaptive Coordination

> Release lineage: `AI_things/main` previously carried v1.0.0. v1.1.0 and v1.2.0 were reviewed delivery candidates but were not the published repository version. v1.3.0 is the consolidated repository release that incorporates the approved runtime、language、stage-decision、artifact、P2P、team-state、memory and lean-routing changes.

## 2026-08-23 repository update

- Corrected `PreToolUse` output to use dedicated event-specific allow/deny behavior; unsupported `continue` is no longer emitted.
- Changed every repo-local hook command to resolve from `$(git rev-parse --show-toplevel)`.
- Made hook JSON parsing and Git-root discovery fail visibly; strict PreToolUse enforcement now fails closed.
- Reduced PostToolUse persistence to coordination metadata only.
- Made SessionStart pending-event delivery one-shot with delivered/archive state.
- Added a 95 MiB cloud ZIP ceiling、semantic standard-ZIP splitting、bundle index、split-volume rejection and oversized-checkpoint handling.

## Summary

v1.3.0 keeps the portable behavior kernel and advanced coordination capabilities from v1.2.0, but changes the default from persistent workflow infrastructure to a lean, route-triggered model.

## Added

- FAST / STANDARD / HIGH_RISK routing with explicit activation rules.
- Independent control-facility trigger matrix for ledger、lease、freeze、verdict、curator、long-run and artifact handoff.
- Lazy team-state activation with `adaptive` and `strict` modes.
- Explicit `--confirm-stage-handoff` requirement for artifact packing/upload.
- Opt-in migration Git flags and current-authorization confirmation.

## Changed

- Root `AGENTS.md` is a route table; optional documents are conditional.
- Ordinary Codex spawns do not require a disk-backed task contract.
- Team ledger is not a prerequisite for FAST or ordinary STANDARD tasks.
- Candidate freeze、leases、memory curator and artifact handoff remain trigger-driven.
- OMO Team Mode defaults to disabled; standalone Claude remains single-agent.

## Preserved

- Codex MultiAgentV2 P2P communication.
- Main-only authority for scope、acceptance、resources、Git and final integration.
- Active memory restructuring capability.
- Pro_Space Worker artifact target.
- Chinese native-language expression rules.
- Claim-matched scientific evidence and hardware safety boundaries.

## Git behavior

Migration tools default to no commits. Commit flags require current Owner authorization. The generic migration tool never pushes.
