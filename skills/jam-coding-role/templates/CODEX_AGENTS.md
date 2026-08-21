# Codex adapter

Root `../AGENTS.md` is canonical. Read it and the routed `.ai/*` files before acting.

This directory contains Codex runtime configuration and capability mappings only:

- model, effort, sandbox, and concurrency: `.codex/config.toml`;
- custom agent definitions: `.codex/agents/*.toml`;
- optional capability map or team notes: `.codex/TEAM.md`.

Do not duplicate the universal coding role, project invariants, memory policy, verification policy, or model settings in prose here. A child agent receives the smallest relevant project context plus:

```text
OUTCOME
CONTEXT
BOUNDARY
ACCEPTANCE
EVIDENCE
NON-GOALS
```

Main owns scope, write/resource allocation, integration, external writes, Git, and the final evidence claim. Use the fewest agents that create independent value.
