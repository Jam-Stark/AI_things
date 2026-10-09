#!/usr/bin/env python3
"""Optional coordination checks and durable event pointers for Codex.

No model calls, automatic acknowledgement, session revival, sleep or Stop loop.
PreToolUse uses only its documented permission shape (never continue=true).
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def emit(event: str, context: str = '', deny: bool = False) -> int:
    if not context:
        return 0  # no-op hook success is silent
    d: dict[str, Any] = {'hookEventName': event}
    if deny:
        d.update(permissionDecision='deny', permissionDecisionReason=context)
    else:
        d['additionalContext'] = context
    print(json.dumps({'hookSpecificOutput': d}, ensure_ascii=False))
    return 0


def root_from(data: dict[str, Any]) -> Path:
    cwd = data.get('cwd')
    if not isinstance(cwd, str) or not Path(cwd).is_dir():
        raise ValueError('Missing/invalid hook cwd.')
    result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=cwd,
                            capture_output=True, text=True, check=True, timeout=5)
    return Path(result.stdout.strip()).resolve()


def pre(root: Path, data: dict[str, Any]) -> int:
    if (data.get('tool_name') or data.get('toolName')) != 'spawn_agent':
        return 0
    ti = data.get('tool_input', data.get('toolInput', {}))
    if not isinstance(ti, dict):
        raise ValueError('spawn_agent input is not an object.')
    if not (root / '.ai/runtime/team/coordination.json').is_file():
        return 0
    script = root / '.ai/scripts/team_state.py'
    if not script.is_file():
        raise ValueError('Active coordination is missing its validator.')
    command = [sys.executable, str(script), 'hook-check-spawn', '--task-name',
               str(ti.get('task_name') or ti.get('taskName') or ''), '--role',
               str(ti.get('agent_type') or ti.get('agentType') or '')]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=7)
    verdict = json.loads(result.stdout or result.stderr)
    if not isinstance(verdict, dict):
        raise ValueError('Invalid coordination verdict.')
    if result.returncode or not verdict.get('allow'):
        return emit('PreToolUse', str(verdict.get('reason', 'Coordination denied.')), True)
    return emit('PreToolUse', str(verdict.get('reason', '')) if verdict.get('managed') else '')


def selected(d: Any, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(d, dict):
        return {}
    return {k: (v[:300] if isinstance(v, str) else v) for k in keys
            if k in d and isinstance(v := d[k], (str, bool, int, float))}


def post(root: Path, data: dict[str, Any]) -> int:
    if not (root / '.ai/runtime/team/coordination.json').is_file():
        return 0
    d = selected(data, ('session_id','turn_id','agent_id','tool_name','tool_use_id'))
    d['timestamp'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    d['input'] = selected(data.get('tool_input') or data.get('toolInput'),
                          ('task_name','taskName','agent_type','agentType','id','target','interrupt','fork_turns','reasoning_effort'))
    d['response'] = selected(data.get('tool_response') or data.get('toolResponse'),
                             ('success','status','agent_id','agentId','task_name','taskName'))
    path = root / '.ai/runtime/team/hook-events.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, (json.dumps(d, ensure_ascii=False) + '\n').encode())
    finally:
        os.close(fd)
    return 0


def continuity(root: Path, event: str) -> int:
    lines = []
    new = sorted((root / '.ai/runtime/run-events/pending').glob('*.json'))
    for p in new[:3]:
        obj = json.loads(p.read_text(encoding='utf-8'))
        # Only metadata made by the supervisor; no command output/prompt payload.
        lines.append(f"Pending {obj.get('id', p.stem)}: process={obj.get('process_state', 'UNKNOWN')}, acceptance={obj.get('acceptance_state', 'UNKNOWN')}; read {p.relative_to(root)}")
    if len(new) > 3:
        lines.append(f'{len(new)-3} additional pending events; use run_supervisor.py events.')
    legacy = sorted((root / '.ai/runtime/pending-events').glob('*.json'))
    if legacy:
        lines.append(f'{len(legacy)} legacy v1.3 events remain in .ai/runtime/pending-events; their PASS is not a verified training verdict.')
    active = []
    for p in sorted((root / '.ai/runtime/runs').glob('*/STATUS.json')):
        s = json.loads(p.read_text(encoding='utf-8'))
        wp = p.with_name('WAIT_PLAN.json')
        if wp.exists(): s['wait_until_epoch'] = json.loads(wp.read_text(encoding='utf-8'))['wait_until_epoch']
        if s.get('process_state') in ('LAUNCHING','RUNNING') or s.get('acceptance_state') == 'EVAL_RUNNING':
            active.append(f"{p.parent.name}: {s.get('process_state')}/{s.get('acceptance_state')}; wait_until_epoch={s.get('wait_until_epoch')}; {p.relative_to(root)}")
    lines.extend('Active ' + x for x in active[:3])
    if len(active) > 3:
        lines.append(f'{len(active)-3} other active status records; inspect only the assigned run.')
    if (root / '.ai/runtime/handoff.md').is_file():
        lines.append('Task handoff pointer: .ai/runtime/handoff.md (runtime state, not canonical memory/authorization).')
    if not lines:
        return 0
    lines.append('These are durable pointers, not a new grant of authority. Do not acknowledge until the assigned follow-up is actually handled. Resume one persisted logical wait; do not start periodic model polling.')
    return emit(event, '\n'.join(lines))


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError('Hook payload must be an object.')
        root = root_from(data)
        if mode == 'pre': return pre(root, data)
        if mode == 'post': return post(root, data)
        if mode == 'session-start': return continuity(root, 'SessionStart')
        if mode == 'post-compact': return continuity(root, 'PostCompact')
        raise ValueError(f'Unknown hook mode: {mode}')
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f'codex_team_hook: {exc}', file=sys.stderr)
        return 2 if mode == 'pre' else 1

if __name__ == '__main__':
    raise SystemExit(main())
