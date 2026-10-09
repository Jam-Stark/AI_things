<!-- managed-by: jam-coding-role; file: LONG_RUNNING_TASKS.md -->
# Long-running task continuity

Use for work expected to exceed 30 minutes, tmux persistence, checkpoint/eval finalization, or recovery after a disconnected interactive session.

The run supervisor can operate without the team ledger. Add ledger/lease only when shared resources or cross-task dependencies require it.

Record command, cwd, source revision, config, resource, output, expected checkpoint, stop condition and state. Use named detached tmux and avoid high-frequency polling.

Process exit, checkpoint presence, evaluation return code and experiment quality are different evidence levels. Pending events can be read on a later session start, but do not guarantee revival of an ended Main turn. Notification alone does not resolve or archive an event. Keep its durable receipt until the responsible lead explicitly handles it; the approved stage controls continuation and resource ownership.
