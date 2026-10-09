<!-- managed-by: jam-coding-role; file: RUNTIME_ADAPTERS.md -->
# Runtime adapters

Universal behavior lives in `.ai/ROLE.md`; project facts live in `.ai/PROJECT.md`. Runtime adapters only map those rules onto actual tools.

## Codex MultiAgentV2

- The execution lead integrates the approved stage, as an independent root or a real child. Runtime identity and stage authority are separate.
- Named agents exchange technical facts directly with `send_message`; lifecycle controls such as `followup_task` require actual creator/management authority.
- P2P does not require team ledger.
- Disk contract, lease, freeze and verdict state are optional under `.ai/TEAM_STATE.md`.
- Owner/Planner sets stage boundaries and acceptance. The execution lead manages delegated writes/resources and integration; Git and external writes need explicit authority.
- Project models and concurrency remain in `.codex/config.toml` and `.codex/agents/*.toml`.

### Codex lifecycle hooks

- `PreToolUse` is event-specific: a no-op allow exits `0` without output; deny returns only `hookSpecificOutput.permissionDecision = "deny"`; never return `continue` from this event.
- `PostToolUse` and `SessionStart` may use their supported common output shape.
- Resolve repository-local hook scripts through `$(git rev-parse --show-toplevel)` because the session working directory may be a repository subdirectory.
- In strict coordination mode, malformed JSON, an invalid `cwd`, a missing validator, or failed Git-root resolution is an enforcement error, not an implicit allow.
- Persist real tool outcomes and retain pending long-run events until explicitly handled; SessionStart notification never archives unresolved events.
- After installing or changing hooks, use Codex `/hooks` to review and trust the exact definitions before treating them as active.

## OpenCode / OMO

- Simple work: normal prompt or `quick`.
- Complex autonomous work: ordinary goal-based delegation or `ulw`/`ultrawork` as appropriate.
- Precise planned work: Prometheus plan and Atlas execution only when useful.
- Team Mode is optional and off by default; enable for real shared tasks/member mailbox/multiple writers.
- Ineligible specialists remain official `task()`/`call_omo_agent()` calls rather than forced team members.

OpenCode preloads only the entrypoint, stable role and project facts. Other `.ai/*` documents are read by trigger.

## Standalone Claude Code

Standalone Claude is a single-agent local lane. It may use local source, memory, logs and runtime, but does not spawn Claude subagents or Agent Teams. This does not prevent OMO from routing a Claude-family model under OMO rules.
