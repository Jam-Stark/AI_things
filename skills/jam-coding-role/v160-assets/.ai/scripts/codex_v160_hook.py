#!/usr/bin/env python3
"""Codex v1.6.0 hooks: actual identity, grant checks, quota, and run pointers.

PreToolUse checks before reserving. PostToolUse records native results. Hook
installation/trust and native execution need separate host evidence.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from workflow_state import (actor_id, close_child, complete_spawn, observe_agent_status,
                            require_owned_child, reserve_spawn, resume_done, state_path,
                            team_is_v160, tool_name, transaction, validate_contact,
                            validate_resume)
from codex_team_hook import continuity, post as coordination_post


def emit(event: str, reason: str, deny: bool = False) -> None:
    output: dict[str, Any] = {'hookEventName': event}
    if deny:
        output.update(permissionDecision='deny', permissionDecisionReason=reason)
    else:
        output['additionalContext'] = reason
    print(json.dumps({'hookSpecificOutput': output}, ensure_ascii=False))


def root_for(data: dict) -> Path:
    cwd = data.get('cwd')
    if not isinstance(cwd, str) or not Path(cwd).is_dir():
        raise ValueError('Invalid hook cwd.')
    result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=cwd,
                            capture_output=True, text=True, check=True, timeout=5)
    return Path(result.stdout.strip()).resolve()


def check_optional_coordination(root: Path, data: dict, path: Path) -> None:
    # The old optional task ledger still applies to unbound teams. New stages
    # already carry their own scope/ownership and do not acquire a second gate.
    with transaction(path) as db:
        member = db.execute('SELECT team FROM actors WHERE session=?', (actor_id(data),)).fetchone()
        if member and team_is_v160(db, member['team']):
            return
    script = root / '.ai/scripts/codex_team_hook.py'
    if not script.is_file():
        raise ValueError('Optional coordination helper is missing.')
    normalized = {**data, 'tool_name': 'spawn_agent'}
    result = subprocess.run([sys.executable, str(script), 'pre'], input=json.dumps(normalized),
                            text=True, capture_output=True, cwd=root, timeout=9)
    if result.returncode:
        raise ValueError('Coordination check failed: ' + result.stderr[-1000:])
    if result.stdout.strip():
        output = json.loads(result.stdout).get('hookSpecificOutput', {})
        if output.get('permissionDecision') == 'deny':
            raise ValueError(output['permissionDecisionReason'])


def run(mode: str, data: dict, root: Path, path: Path | None = None) -> None:
    path = path or state_path(root)
    tool = tool_name(data)
    if mode == 'pre':
        if tool == 'spawn_agent':
            check_optional_coordination(root, data, path)
            reserve_spawn(root, data, path)
        elif tool in ('resume_agent', 'followup_task'):
            validate_resume(path, data)
        elif tool in ('close_agent', 'interrupt_agent'):
            with transaction(path) as db:
                require_owned_child(db, data)
        elif tool == 'send_message':
            validate_contact(path, data, technical_message=True)
        # Successful PreToolUse is silent; no output fields from another event.
    elif mode == 'post':
        if tool == 'spawn_agent': complete_spawn(path, data)
        elif tool == 'close_agent': close_child(path, data)
        elif tool in ('resume_agent', 'followup_task'): resume_done(path, data)
        elif tool == 'list_agents': observe_agent_status(path, data)
        coordination_post(root, data)
    elif mode in ('session-start', 'post-compact'):
        continuity(root, 'SessionStart' if mode == 'session-start' else 'PostCompact')
    else:
        raise ValueError('Unknown hook mode.')


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError('Hook payload must be an object.')
        run(mode, data, root_for(data))
        return 0
    except Exception as exc:  # Hook boundary: parsing/check failures must block the restricted call.
        if mode == 'pre':
            emit('PreToolUse', 'v1.6.0 blocked: ' + str(exc), True)
            return 0
        print('codex_v160_hook: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
