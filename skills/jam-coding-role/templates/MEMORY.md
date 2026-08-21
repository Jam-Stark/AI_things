# Project Memory Router

Memory is optional. Keep this file short. Create a subsystem only after repeated retrieval cost justifies it.

## Routes

| Need | Read |
|---|---|
| project-wide durable decisions and commands | this file |
| subsystem-specific facts | add an exact path only when the subsystem exists |
| active task execution | task, plan, or run ledger; not canonical memory |

## Current durable facts

Add only verified facts that are broadly reused:

- None yet.

## Update rules

- Record a fact or decision only when it is verified and likely to be reused.
- Include scope, evidence/provenance, consequence, status, `read when`, and timestamp.
- Distinguish intent, implementation, runtime observation, experiment conclusion, and inference.
- Do not paste raw logs, chat transcripts, heartbeats, temporary agent state, or speculative ideas.
- When current truth changes, update the routed summary and preserve only the provenance needed to understand the transition.
- Split into `memory/<subsystem>/MEMORY.md` only when this router stops being fast to use.
