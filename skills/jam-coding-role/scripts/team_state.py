#!/usr/bin/env python3
"""Optional persistent coordination state for Jam Coding Role v1.3.0.

Ordinary FAST/STANDARD spawns do not need this file. Activate it only for
multiple writers, exclusive resources, cross-session coordination, or formal
review/QA.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE = Path('.ai/runtime/team')
MARKER = STATE / 'coordination.json'
TASKS = STATE / 'tasks'
LEASES = STATE / 'leases.json'
FREEZES = STATE / 'freezes'
VERDICTS = STATE / 'verdicts'
STRICT_GROUPS = {'writer', 'reviewer', 'runtime_qa'}
ROLE_GROUPS = {
    'isaaclab_worker': 'writer', 'worker': 'writer', 'writer': 'writer',
    'code_reviewer': 'reviewer', 'isaaclab_reviewer': 'reviewer', 'reviewer': 'reviewer',
    'runtime_qa': 'runtime_qa',
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def atomic_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    data = json.loads(path.read_text(encoding='utf-8'))
    return data


def active() -> dict[str, Any] | None:
    if not MARKER.is_file():
        return None
    data = load_json(MARKER, {})
    if not isinstance(data, dict) or data.get('mode') not in {'adaptive', 'strict'}:
        raise SystemExit(f'invalid coordination marker: {MARKER}')
    return data


def task_path(name: str) -> Path:
    if not name or any(ch not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for ch in name):
        raise SystemExit('task name must use lowercase letters, digits, and underscores')
    return TASKS / f'{name}.json'


def activate(args: argparse.Namespace) -> int:
    if MARKER.exists():
        raise SystemExit('coordination already active')
    STATE.mkdir(parents=True, exist_ok=True)
    atomic_json(MARKER, {'version': 2, 'mode': args.mode, 'reason': args.reason, 'activated_at': now()})
    atomic_json(LEASES, [])
    print(MARKER)
    return 0


def deactivate(args: argparse.Namespace) -> int:
    if not MARKER.exists():
        print('INACTIVE')
        return 0
    leases = load_json(LEASES, [])
    if leases and not args.force:
        raise SystemExit('active leases remain; release them or pass --force')
    if args.archive:
        archive = STATE.parent / f"team-archive-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if archive.exists():
            raise SystemExit(f'archive already exists: {archive}')
        shutil.move(str(STATE), str(archive))
        print(archive)
    else:
        shutil.rmtree(STATE)
        print('DEACTIVATED')
    return 0


def status(_args: argparse.Namespace) -> int:
    marker = active()
    if marker is None:
        print('INACTIVE')
        return 0
    tasks = []
    if TASKS.exists():
        tasks = [load_json(path, {}) for path in sorted(TASKS.glob('*.json'))]
    print(json.dumps({'marker': marker, 'tasks': tasks, 'leases': load_json(LEASES, [])}, ensure_ascii=False, indent=2))
    return 0


def create_task(args: argparse.Namespace) -> int:
    if active() is None:
        raise SystemExit('coordination is inactive')
    path = task_path(args.task_name)
    if path.exists():
        raise SystemExit(f'task already exists: {args.task_name}')
    data = {
        'task_name': args.task_name, 'role': args.role, 'group': args.group or ROLE_GROUPS.get(args.role, 'other'),
        'outcome': args.outcome, 'revision': args.revision, 'read_set': args.read_set or [],
        'write_set': args.write_set or [], 'acceptance': args.acceptance or [], 'state': 'declared',
        'created_at': now(),
    }
    group = data['group']
    if group == 'writer' and (not data['revision'] or not data['write_set'] or not data['acceptance']):
        raise SystemExit('writer tasks require revision, write_set, and acceptance')
    if group == 'reviewer' and (not data['revision'] or not data['read_set'] or not data['acceptance']):
        raise SystemExit('reviewer tasks require revision, read_set, and acceptance')
    atomic_json(path, data)
    print(path)
    return 0


def set_state(args: argparse.Namespace) -> int:
    path = task_path(args.task_name)
    data = load_json(path, None)
    if not isinstance(data, dict):
        raise SystemExit(f'task not found: {args.task_name}')
    data['state'] = args.state; data['updated_at'] = now()
    atomic_json(path, data); print(path); return 0


def path_conflict(a: str, b: str) -> bool:
    pa, pb = Path(a), Path(b)
    return pa == pb or pa in pb.parents or pb in pa.parents


def lease_acquire(args: argparse.Namespace) -> int:
    if active() is None:
        raise SystemExit('coordination is inactive')
    leases = load_json(LEASES, [])
    if not isinstance(leases, list):
        raise SystemExit('invalid lease store')
    requested = {'task': args.task_name, 'kind': args.kind, 'value': args.value, 'created_at': now()}
    for item in leases:
        if item.get('task') == args.task_name:
            continue
        same = item.get('kind') == args.kind and item.get('value') == args.value
        if args.kind == 'path' and item.get('kind') == 'path':
            same = path_conflict(str(item.get('value')), args.value)
        if same:
            raise SystemExit(f"lease conflict with {item.get('task')}: {item.get('kind')}={item.get('value')}")
    leases.append(requested); atomic_json(LEASES, leases); print(json.dumps(requested)); return 0


def lease_release(args: argparse.Namespace) -> int:
    leases = load_json(LEASES, [])
    kept = [x for x in leases if not (x.get('task') == args.task_name and (args.kind is None or x.get('kind') == args.kind) and (args.value is None or x.get('value') == args.value))]
    atomic_json(LEASES, kept); print(f'RELEASED {len(leases)-len(kept)}'); return 0


def hook_check_spawn(args: argparse.Namespace) -> int:
    marker = active()
    if marker is None:
        print(json.dumps({'allow': True, 'managed': False, 'reason': 'coordination inactive'})); return 0
    path = task_path(args.task_name) if args.task_name else None
    if path and path.exists():
        data = load_json(path, {})
        print(json.dumps({'allow': True, 'managed': True, 'reason': f"registered {data.get('group','task')} task"})); return 0
    group = ROLE_GROUPS.get(args.role, 'other')
    if marker['mode'] == 'strict' and group in STRICT_GROUPS:
        print(json.dumps({'allow': False, 'managed': False, 'reason': f'strict mode requires registered {group} contract'})); return 2
    print(json.dumps({'allow': True, 'managed': False, 'reason': 'ephemeral spawn allowed'})); return 0


def freeze(args: argparse.Namespace) -> int:
    if args.purpose not in {'formal-review', 'formal-qa', 'release'}:
        raise SystemExit('freeze purpose must be formal-review, formal-qa, or release')
    if active() is None:
        raise SystemExit('coordination is inactive')
    data = {'revision': args.revision, 'purpose': args.purpose, 'paths': args.path or [], 'contracts': args.contract or [], 'topology': args.topology or [], 'created_at': now()}
    path = FREEZES / f'{args.revision}.json'; atomic_json(path, data); print(path); return 0


def verdict(args: argparse.Namespace) -> int:
    freeze_path = FREEZES / f'{args.revision}.json'
    frozen = load_json(freeze_path, None)
    if not isinstance(frozen, dict):
        raise SystemExit(f'freeze not found: {args.revision}')
    data = {'id': args.id, 'revision': args.revision, 'status': args.status, 'scope': {'paths': args.path or frozen.get('paths', []), 'contracts': args.contract or frozen.get('contracts', []), 'topology': args.topology or frozen.get('topology', [])}, 'evidence': args.evidence or [], 'created_at': now()}
    path = VERDICTS / f'{args.id}.json'; atomic_json(path, data); print(path); return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('activate'); a.add_argument('--mode', choices=['adaptive','strict'], required=True); a.add_argument('--reason', required=True); a.set_defaults(func=activate)
    d = sub.add_parser('deactivate'); d.add_argument('--archive', action='store_true'); d.add_argument('--force', action='store_true'); d.set_defaults(func=deactivate)
    s = sub.add_parser('status'); s.set_defaults(func=status)
    c = sub.add_parser('task-create'); c.add_argument('--task-name', required=True); c.add_argument('--role', required=True); c.add_argument('--group', choices=['researcher','planner','writer','reviewer','runtime_qa','memory_curator','other']); c.add_argument('--outcome', required=True); c.add_argument('--revision'); c.add_argument('--read-set', action='append'); c.add_argument('--write-set', action='append'); c.add_argument('--acceptance', action='append'); c.set_defaults(func=create_task)
    u = sub.add_parser('task-state'); u.add_argument('--task-name', required=True); u.add_argument('--state', choices=['declared','spawned','running','waiting','completed','blocked','errored','interrupted','shutdown'], required=True); u.set_defaults(func=set_state)
    la = sub.add_parser('lease-acquire'); la.add_argument('--task-name', required=True); la.add_argument('--kind', choices=['path','gpu','process','display','port','hardware','output'], required=True); la.add_argument('--value', required=True); la.set_defaults(func=lease_acquire)
    lr = sub.add_parser('lease-release'); lr.add_argument('--task-name', required=True); lr.add_argument('--kind'); lr.add_argument('--value'); lr.set_defaults(func=lease_release)
    h = sub.add_parser('hook-check-spawn'); h.add_argument('--task-name', default=''); h.add_argument('--role', default=''); h.set_defaults(func=hook_check_spawn)
    f = sub.add_parser('freeze'); f.add_argument('--revision', required=True); f.add_argument('--purpose', required=True); f.add_argument('--path', action='append'); f.add_argument('--contract', action='append'); f.add_argument('--topology', action='append'); f.set_defaults(func=freeze)
    v = sub.add_parser('verdict'); v.add_argument('--id', required=True); v.add_argument('--revision', required=True); v.add_argument('--status', choices=['PASS','FAIL','BLOCKED','INCONCLUSIVE'], required=True); v.add_argument('--path', action='append'); v.add_argument('--contract', action='append'); v.add_argument('--topology', action='append'); v.add_argument('--evidence', action='append'); v.set_defaults(func=verdict)
    return p


if __name__ == '__main__':
    args = parser().parse_args(); raise SystemExit(args.func(args))
