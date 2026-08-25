# Jam Coding Role Changelog

## 1.3.1 — Minimal routing and cloud-review handoff update

- Declared root `AGENTS.md` as the repository's project-level workflow authority, below system/developer/Owner instructions but above runtime defaults and ordinary adapters.
- Made FAST/STANDARD/HIGH_RISK classification automatic. STANDARD/HIGH_RISK may delegate without waiting for the user to say “team” when independent workstreams、specialist context or independent review justify it; explicit higher-level sub-agent bans still force single-agent fallback.
- Added a canonical environment and command registry to `.ai/PROJECT.md`, including initial train/eval/smoke placeholders and maintenance rules.
- Made cloud Pro handoff a Git-published handoff: commit in-scope changes、push、verify remote commit、pack/upload artifacts、then generate the review prompt.
- Added `PRO_REVIEW_PROMPT.md` and `pro_review_handoff.py` with repository URL、branch、commit、Drive release、ZIP list、review type and Owner request.
- Explicitly stated that 95 MiB limits the final compressed size of each generated ZIP, not raw input size.
- Added `UPDATE_GUIDE_1.3.1.md` for existing project installations.

### v1.3.1 Pro full-delivery addendum — version unchanged

- Split the cloud Pro response into a concise five-item Owner view and one detailed `pro_delivery__full_review.zip` for the local Worker AI.
- The detailed ZIP contains `FULL_REVIEW.md` and `LOCAL_WORKER_PARSE_PROMPT.md`; concise item 5 gives the same copy-ready Worker prompt and exact Drive address.
- Worker inputs and Pro outputs now share one immutable task folder. Worker files use `worker_delivery__`; the Pro answer uses `pro_delivery__`.
- Updated the stage packer to create prefixed Worker ZIPs and sidecars, while the prompt helper lists only Worker input ZIPs and reserves `pro_delivery__full_review.zip` for the Pro result.
- Historical task folders remain valid and do not need renaming.

---

# Jam Coding Role v1.3.0 — Adaptive Coordination

> Release lineage: `AI_things/main` previously carried v1.0.0. v1.1.0 and v1.2.0 were reviewed delivery candidates but were not the published repository version. v1.3.0 is the consolidated repository release that incorporates the approved runtime, language, stage-decision, artifact, P2P, team-state, memory and lean-routing changes.

## 2026-08-23 repository update

- Corrected `PreToolUse` output to use dedicated event-specific allow/deny behavior; unsupported `continue` is no longer emitted.
- Changed every repo-local hook command to resolve from `$(git rev-parse --show-toplevel)`.
- Made hook JSON parsing and Git-root discovery fail visibly; strict PreToolUse enforcement now fails closed.
- Reduced PostToolUse persistence to coordination metadata only.
- Made SessionStart pending-event delivery one-shot with delivered/archive state.
- Added a 95 MiB cloud ZIP ceiling, semantic standard-ZIP splitting, `BUNDLE_INDEX.md`, split-volume rejection, and oversized-checkpoint handling.
- Added `UPDATE_LOG.md` as the detailed implementation and verification record.

## Summary

v1.3.0 keeps the portable behavior kernel and advanced coordination capabilities from v1.2.0, but changes the default from persistent workflow infrastructure to a lean, route-triggered model.

## Added

- FAST / STANDARD / HIGH_RISK routing with explicit activation rules.
- Independent control-facility trigger matrix for ledger、lease、freeze、verdict、curator、long-run and artifact handoff.
- Lazy team-state activation with `adaptive` and `strict` modes.
- `team_state.py status/activate/deactivate/hook-check-spawn` commands.
- Explicit `--confirm-stage-handoff` requirement for artifact packing/upload.
- Opt-in migration Git flags: `--checkpoint-commit` and `--migration-commit`, plus `--confirm-user-authorized-commit` for actual Git writes.

## Changed

- Root `AGENTS.md` is now a route table. Only core documents are read by default; optional documents are conditional.
- Ordinary Codex spawns no longer require a disk-backed task contract.
- Codex hooks are no-op while coordination is inactive and do not create runtime state.
- Team ledger is no longer a prerequisite for FAST or ordinary STANDARD tasks.
- Candidate freeze is limited to formal review/QA, ambiguous dirty/shared candidates or cross-session review.
- Leases are limited to actual concurrent writers or exclusive resources; read-only agents are not leased.
- Memory curator is candidate-triggered rather than a closure stage.
- Artifact handoff is explicit rather than automatic at task completion.
- OMO Team Mode defaults to disabled.
- OpenCode and Claude preload only the core routing files.
- A single authorized long run may use a receipt/tmux without activating the full team ledger.

## Preserved

- Codex MultiAgentV2 P2P communication.
- Main-only authority for scope、acceptance、resources、Git and final integration.
- Standalone Claude Code single-agent routing.
- OMO official ordinary delegation and Team Mode semantics.
- Active memory restructuring capability.
- Pro_Space create-only artifact target.
- Chinese native-language expression rules.
- Claim-matched scientific evidence and hardware safety boundaries.

## Git behavior

The migration tool defaults to no commits. A checkpoint commit and migration commit are created only when the caller supplies explicit flags under current Owner authorization. The tool never pushes.
