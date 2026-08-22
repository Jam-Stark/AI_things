<!-- managed-by: jam-coding-role; file: LONG_RUNNING_TASKS.md -->
# Long-running task continuity

Use for work expected to exceed 30 minutes, tmux persistence, checkpoint/eval finalization, or recovery after a disconnected interactive session.

The run supervisor can operate without the team ledger. Add ledger/lease only when shared resources or cross-task dependencies require it.

Record command, cwd, source revision, config, resource, output, expected checkpoint, stop condition and state. Use named detached tmux and avoid high-frequency polling.

Process exit, checkpoint presence, evaluation return code and experiment quality are different evidence levels. Pending events can be read on a later session start, but do not guarantee revival of an ended Main turn. A delivered event must be marked and moved to the archive before its pending copy is removed; later sessions must not inject the same event again.
