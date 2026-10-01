# Codex adapter v1.5.0

Follow root AGENTS.md. Read .codex/TEAM.md and .ai/MODEL_ROUTING.md before delegation. Main model/effort belong to the App. Project context/compact settings are preserved during migration.

Codex delegation uses the small quota ledger before spawn; full coordination remains conditional. SessionStart/PostCompact retain pending events until explicitly resolved; notification is not acceptance. Review changed hooks through /hooks.

For a host that loads hooks only from the primary checkout, .ai/scripts/install_codex_hooks.py can register worktree-scoped user hooks. Use only when the actual host requires it; it preserves unrelated hooks and does not change trust.
