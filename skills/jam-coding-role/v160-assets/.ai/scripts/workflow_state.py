#!/usr/bin/env python3
"""Local v1.6.0 identity, stage grants and logical-team quota.

The existing v150 database and five table shapes are retained. A stage binding
explicitly selects v160 authority; unbound teams retain their existing policy.
This is a cooperating-agent workflow, not an operating-system security sandbox.
"""
from __future__ import annotations
import argparse
import contextlib
import json
import re
import socket
import sqlite3
import subprocess
import time
import tomllib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from generated_role_policy import POLICY, BASE_ROLE, ROLE_BUDGETS, MAX_ACTIVE, CAN_SPAWN
from agent_boundary import Actor, can_contact, can_spawn

LIVE = ('reserved', 'active', 'uncertain')
OPERATIONS = {'read', 'edit', 'check', 'spawn', 'message', 'run', 'evaluate',
              'commit', 'push', 'publish', 'hardware'}
TASK_RE = re.compile(r'^[a-z0-9]+(?:_[a-z0-9]+)*$')
TOOLS = {'spawn_agent', 'resume_agent', 'close_agent', 'send_message',
         'followup_task', 'interrupt_agent', 'list_agents'}
TOOL_PREFIXES = ('', 'agents.', 'collaboration.', 'functions.collaboration.')


def tool_name(data: dict) -> str | None:
    value = data.get('tool_name', data.get('toolName', ''))
    for prefix in TOOL_PREFIXES:
        for name in TOOLS:
            if value == prefix + name:
                return name
    if isinstance(value, str) and value.rsplit('.', 1)[-1] in TOOLS:
        raise ValueError(f'Unsupported agent tool namespace: {value}')
    return None


def state_path(root: Path) -> Path:
    root = root.resolve()
    r = subprocess.run(['git', 'rev-parse', '--git-common-dir'], cwd=root,
                       text=True, capture_output=True, timeout=5)
    if r.returncode == 0:
        p = Path(r.stdout.strip())
        return (p if p.is_absolute() else root / p).resolve() / 'jam-workflow-v150/state.sqlite3'
    return root / '.ai/runtime/v150/state.sqlite3'


SCHEMA = '''
CREATE TABLE IF NOT EXISTS actors (
 session TEXT PRIMARY KEY, team TEXT NOT NULL, is_main INTEGER NOT NULL,
 role TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS spawns (
 request TEXT PRIMARY KEY, team TEXT NOT NULL, actor TEXT NOT NULL,
 role TEXT NOT NULL, model TEXT NOT NULL, state TEXT NOT NULL,
 child TEXT UNIQUE, created REAL NOT NULL, evidence TEXT);
CREATE TABLE IF NOT EXISTS astra_slot (
 team TEXT PRIMARY KEY, request TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS actor_aliases (alias TEXT PRIMARY KEY, session TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit (
 at REAL NOT NULL, event TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS actor_bindings_v160 (
 actor_id TEXT PRIMARY KEY, runtime_root_id TEXT NOT NULL, parent_id TEXT,
 host_id TEXT NOT NULL, policy_binding TEXT NOT NULL, evidence_ref TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS stage_bindings_v160 (
 team_id TEXT NOT NULL, stage_id TEXT NOT NULL, revision TEXT NOT NULL,
 planner_actor TEXT NOT NULL, lead_actor TEXT, root_grant_id TEXT NOT NULL,
 status TEXT NOT NULL, plan_ref TEXT NOT NULL, payload TEXT NOT NULL,
 PRIMARY KEY(team_id,stage_id));
CREATE TABLE IF NOT EXISTS stage_grants_v160 (
 grant_id TEXT PRIMARY KEY, team_id TEXT NOT NULL, stage_id TEXT NOT NULL,
 revision TEXT NOT NULL, actor_id TEXT, parent_grant_id TEXT,
 payload TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS spawn_intents_v160 (
 parent_actor TEXT NOT NULL, task_name TEXT NOT NULL, role TEXT NOT NULL,
 grant_id TEXT NOT NULL UNIQUE, request TEXT UNIQUE,
 PRIMARY KEY(parent_actor,task_name));
'''


@contextlib.contextmanager
def transaction(path: Path) -> Iterator[sqlite3.Connection]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    db = sqlite3.connect(path, timeout=5, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA busy_timeout=5000')
        db.executescript(SCHEMA)
        path.chmod(0o600)
        db.execute('BEGIN IMMEDIATE')
        yield db
        db.execute('COMMIT')
    except BaseException:
        if db.in_transaction:
            db.execute('ROLLBACK')
        raise
    finally:
        db.close()


def audit_event(db: sqlite3.Connection, event: str, data: Any) -> None:
    db.execute('INSERT INTO audit VALUES (?,?,?)',
               (time.time(), event, json.dumps(data, ensure_ascii=False)))


def session_metadata(path: Path) -> dict:
    with path.open(encoding='utf-8') as handle:
        record = json.loads(next(handle))
    if record.get('type') != 'session_meta':
        raise ValueError('Identity evidence must start with native session_meta.')
    return record['payload']


def transcript_for(actor: str) -> Path:
    paths = [p for directory in ('sessions', 'archived_sessions')
             for p in (Path.home() / '.codex' / directory).glob(f'**/*{actor}.jsonl')]
    if len(paths) != 1:
        raise ValueError(f'Need one actual transcript for {actor}; supply --transcript.')
    return paths[0]


def runtime_identity(actor: str | None = None, transcript: Path | None = None) -> dict:
    source = (transcript or transcript_for(str(actor))).resolve()
    meta = session_metadata(source)
    actual = meta.get('id')
    if not isinstance(actual, str) or not actual or (actor and actor != actual):
        raise ValueError('Actor id does not match native session_meta.id.')
    origin = meta.get('source')
    spawn = origin.get('subagent', {}).get('thread_spawn') if isinstance(origin, dict) else None
    parent = spawn.get('parent_thread_id') if spawn else None
    if meta.get('parent_thread_id') not in (None, parent):
        raise ValueError('Conflicting native parent metadata.')
    if meta.get('thread_source') == 'subagent' and not parent:
        raise ValueError('Subagent identity lacks its actual creator.')
    runtime_root = meta.get('session_id')
    if parent and (not runtime_root or runtime_root == actual):
        runtime_root = runtime_identity(parent)['runtime_root_id']
    if not parent:
        if meta.get('thread_source') not in (None, 'user') or not isinstance(origin, str):
            raise ValueError('Unknown root identity source.')
        runtime_root = actual
    return {'actor_id': actual, 'runtime_root_id': runtime_root, 'parent_id': parent,
            'host_id': socket.gethostname(), 'role': spawn.get('agent_role') if spawn else 'main',
            'canonical_path': spawn.get('agent_path') if spawn else '/root',
            'evidence_ref': str(source)}


def save_identity(db: sqlite3.Connection, identity: dict, policy: str = 'v151') -> None:
    old = db.execute('SELECT * FROM actor_bindings_v160 WHERE actor_id=?',
                     (identity['actor_id'],)).fetchone()
    values = tuple(identity[k] for k in ('actor_id', 'runtime_root_id', 'parent_id', 'host_id'))
    if old:
        if values != tuple(old[k] for k in ('actor_id', 'runtime_root_id', 'parent_id', 'host_id')):
            raise ValueError('Cannot rebind an existing runtime identity.')
        return
    db.execute('INSERT INTO actor_bindings_v160 VALUES (?,?,?,?,?,?)',
               (*values, policy, identity['evidence_ref']))


def initialize_team(path: Path, session: str, team: str,
                    transcript: Path | None = None) -> dict:
    if not team.strip():
        raise ValueError('Stable logical team id is required.')
    identity = runtime_identity(session, transcript)
    with transaction(path) as db:
        old = db.execute('SELECT * FROM actors WHERE session=?', (session,)).fetchone()
        is_root = identity['parent_id'] is None
        if old and (old['team'] != team or bool(old['is_main']) != is_root):
            raise ValueError('Cannot remap a team or turn a child into Main.')
        if not old:
            if not is_root:
                parent = db.execute('SELECT team FROM actors WHERE session=?',
                                    (identity['parent_id'],)).fetchone()
                if not parent or parent['team'] != team:
                    raise ValueError('Register the actual parent in this team first.')
            db.execute('INSERT INTO actors VALUES (?,?,?,?)',
                       (session, team, int(is_root), identity['role'] or 'default'))
        save_identity(db, identity)
        audit_event(db, 'team-init', {'actor': session, 'team': team, 'identity': identity})
    return identity


def actor_id(data: dict[str, Any]) -> str:
    transcript = data.get('transcript_path')
    if transcript:
        identity = runtime_identity(transcript=Path(transcript))
        if data.get('session_id') not in (identity['actor_id'], identity['runtime_root_id'], identity['parent_id']):
            raise ValueError('Hook session does not match transcript ancestry.')
        return identity['actor_id']
    value = data.get('session_id')
    if not isinstance(value, str) or not value:
        raise ValueError('Missing native hook identity.')
    return value  # Existing v151 hooks without transcripts keep their old identity path.


def require_hook_identity(db: sqlite3.Connection, data: dict) -> str:
    actor = actor_id(data)
    binding = db.execute('SELECT * FROM actor_bindings_v160 WHERE actor_id=?', (actor,)).fetchone()
    if binding and binding['policy_binding'] == 'v160':
        if not data.get('transcript_path'):
            raise ValueError('v160 agent actions need actual transcript identity, not session_id alone.')
        save_identity(db, runtime_identity(actor, Path(data['transcript_path'])), 'v160')
    return actor


def role_config(root: Path, role: str) -> dict[str, Any]:
    if role not in POLICY:
        raise ValueError(f'Unregistered role {role!r}; no implicit model fallback.')
    matches = [d for p in (root / '.codex/agents').glob('*.toml')
               if (d := tomllib.loads(p.read_text(encoding='utf-8'))).get('name') == role]
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one TOML for {role}.')
    cfg = matches[0]
    if (cfg.get('model'), cfg.get('model_reasoning_effort')) != POLICY[role]:
        raise ValueError(f'Role {role} violates the model/effort policy.')
    if (cfg.get('model_context_window'), cfg.get('model_auto_compact_token_limit')) != ROLE_BUDGETS[role]:
        raise ValueError('Invalid explicit child context budget.')
    if cfg.get('model_auto_compact_token_limit_scope') != 'total':
        raise ValueError('Child compact scope must be total.')
    if cfg.get('agents', {}).get('enabled') is not CAN_SPAWN[role]:
        raise ValueError('Role spawn capability disagrees with generated policy.')
    features = cfg.get('features', {})
    if features.get('context_management', {}).get('experimental_mode') is not (BASE_ROLE[role] == 'deep_researcher'):
        raise ValueError('Wrong model-specific context strategy.')
    if 'use_history_notes_extension' in features.get('token_budget', {}):
        raise ValueError('Do not pin history_notes_extension in project roles.')
    return cfg


def tool_input(data: dict) -> dict:
    value = data.get('tool_input', data.get('toolInput', {}))
    if not isinstance(value, dict):
        raise ValueError('Unrecognized agent tool input.')
    return value


def request_id(data: dict) -> str:
    value = data.get('tool_use_id')
    if not isinstance(value, str) or not value:
        raise ValueError('Missing stable tool_use_id; cannot reserve a spawn.')
    return value


def stage_context(db: sqlite3.Connection, team_id: str, stage_id: str) -> dict:
    row = db.execute('SELECT * FROM stage_bindings_v160 WHERE team_id=? AND stage_id=?',
                     (team_id, stage_id)).fetchone()
    if not row:
        raise ValueError('Stage is not explicitly bound.')
    result = dict(row)
    result['payload'] = json.loads(result['payload'])
    return result


def grant_row(db: sqlite3.Connection, grant_id: str, *, statuses=('active',)) -> dict:
    row = db.execute('SELECT * FROM stage_grants_v160 WHERE grant_id=?', (grant_id,)).fetchone()
    if not row or row['status'] not in statuses:
        raise ValueError('Grant is not current/active.')
    result = dict(row)
    result['payload'] = json.loads(result['payload'])
    stage = stage_context(db, row['team_id'], row['stage_id'])
    if stage['status'] != 'active' or stage['revision'] != row['revision']:
        raise ValueError('Grant belongs to an inactive or superseded plan revision.')
    return result


def active_grant(db: sqlite3.Connection, actor: str) -> dict:
    rows = db.execute("SELECT grant_id FROM stage_grants_v160 WHERE actor_id=? AND status='active'",
                      (actor,)).fetchall()
    valid = [grant_row(db, r[0]) for r in rows]
    if len(valid) != 1:
        raise ValueError('Actor needs exactly one current stage grant.')
    return valid[0]


def read_reference(source_ref: str) -> tuple[Path, dict]:
    file_name, marker, line = source_ref.rpartition('#L')
    if not marker or not line.isdigit() or int(line) < 1:
        raise ValueError('Source evidence must be an actual transcript path#Lnumber.')
    path = Path(file_name).resolve()
    with path.open(encoding='utf-8') as handle:
        for index, text in enumerate(handle, 1):
            if index == int(line):
                return path, json.loads(text)
    raise ValueError('Evidence reference line does not exist.')


def owner_authority(source_ref: str, issuer: dict) -> None:
    source, record = read_reference(source_ref)
    payload = record.get('payload', {})
    is_user = (record.get('type') == 'response_item' and payload.get('type') == 'message'
               and payload.get('role') == 'user') or (
                   record.get('type') == 'event_msg' and payload.get('type') == 'user_message')
    identity = runtime_identity(transcript=source)
    if not is_user or identity['parent_id'] is not None or identity['actor_id'] != issuer['runtime_root_id']:
        raise ValueError('Initial stage authority must cite an Owner message in the issuer root transcript.')


def normalize_scope(scope: dict) -> dict:
    workspace = Path(scope['workspace_root']).resolve()
    if not workspace.is_dir():
        raise ValueError('Scope workspace_root must be a real directory.')
    paths = []
    for value in scope.get('write_paths', []):
        candidate = (workspace / value).resolve()
        if not candidate.is_relative_to(workspace) or any(c in str(value) for c in '*?['):
            raise ValueError('Write scope needs explicit paths within workspace_root.')
        paths.append(str(candidate))
    operations = set(scope.get('allowed_operations', []))
    if not operations <= OPERATIONS:
        raise ValueError(f'Unsupported operations: {sorted(operations - OPERATIONS)}')
    return {'workspace_root': str(workspace), 'write_paths': sorted(set(paths)),
            'allowed_operations': sorted(operations),
            'resources': sorted(set(scope.get('resources', [])))}


def projection(data: dict, *, depth: int) -> dict:
    budget = data.get('budget', {})
    runs = budget.get('approved_runs', [])
    if not isinstance(runs, list) or any(not isinstance(v, str) or not v for v in runs):
        raise ValueError('approved_runs must be explicit stable run/attempt names.')
    if type(depth) is not int or not 0 <= depth <= 3:
        raise ValueError('Invalid delegation depth.')
    return {'scope': normalize_scope(data['scope']),
            'budget': {'approved_runs': sorted(set(runs))},
            'delegate_depth_left': depth}


def overlaps(a: list[str], b: list[str]) -> bool:
    return any(Path(x).is_relative_to(y) or Path(y).is_relative_to(x) for x in a for y in b)


def check_subset(db: sqlite3.Connection, parent: dict, payload: dict,
                 *, exclude_grant: str | None = None) -> None:
    base, child = parent['payload'], payload
    outer, inner = base['scope'], child['scope']
    if (inner['workspace_root'] != outer['workspace_root'] or
        not set(inner['allowed_operations']) <= set(outer['allowed_operations']) or
        not set(inner['resources']) <= set(outer['resources']) or
        any(not any(Path(p).is_relative_to(q) for q in outer['write_paths']) for p in inner['write_paths']) or
        not set(child['budget']['approved_runs']) <= set(base['budget']['approved_runs']) or
        child['delegate_depth_left'] >= base['delegate_depth_left']):
        raise ValueError('Child grant must be a strict depth-decreasing subset of its parent.')
    for row in db.execute("SELECT grant_id,payload FROM stage_grants_v160 WHERE parent_grant_id=? AND status IN ('pending','active')",
                          (parent['grant_id'],)):
        if row['grant_id'] == exclude_grant:
            continue
        peer = json.loads(row['payload'])
        if (overlaps(peer['scope']['write_paths'], inner['write_paths']) or
            set(peer['scope']['resources']) & set(inner['resources']) or
            set(peer['budget']['approved_runs']) & set(child['budget']['approved_runs'])):
            raise ValueError('Child grant overlaps an allocated sibling write/resource/run budget.')


def insert_grant(db: sqlite3.Connection, grant: str, stage: dict, actor: str | None,
                 parent: str | None, payload: dict, status='active') -> None:
    db.execute('INSERT INTO stage_grants_v160 VALUES (?,?,?,?,?,?,?,?)',
               (grant, stage['team_id'], stage['stage_id'], stage['revision'], actor,
                parent, json.dumps(payload, ensure_ascii=False), status))


def create_subgrant(db: sqlite3.Connection, actor: str, parent_id: str, task_name: str,
                    role: str, data: dict) -> str:
    parent = grant_row(db, parent_id)
    if parent['actor_id'] != actor:
        raise ValueError('Only the current grant holder can delegate it.')
    stage = stage_context(db, parent['team_id'], parent['stage_id'])
    parent_role = parent['payload']['role']
    capable = CAN_SPAWN.get(parent_role, False) or parent_role == 'planner'
    if not capable or parent['payload']['delegate_depth_left'] <= 0:
        raise ValueError('This role/grant has no delegation authority.')
    if 'spawn' not in parent['payload']['scope']['allowed_operations']:
        raise ValueError('The approved stage does not include spawn.')
    if role not in POLICY or not TASK_RE.fullmatch(task_name):
        raise ValueError('Choose a registered role and semantic task_name.')
    depth = data.get('delegate_depth_left', 0)
    if depth and not CAN_SPAWN[role]:
        raise ValueError('Leaf roles cannot receive further delegation depth.')
    if parent_role == 'planner':
        if BASE_ROLE[role] == 'execution_lead':
            if stage['lead_actor'] or db.execute("SELECT 1 FROM spawn_intents_v160 i JOIN stage_grants_v160 g ON i.grant_id=g.grant_id WHERE g.parent_grant_id=? AND g.status IN ('pending','active') AND json_extract(g.payload,'$.is_lead')=1", (parent_id,)).fetchone():
                raise ValueError('Stage already has an execution lead.')
        elif depth:
            raise ValueError('Planner support grants cannot create a second execution tree.')
    payload = projection(data, depth=depth)
    payload.update(role=role, is_lead=parent_role == 'planner' and BASE_ROLE[role] == 'execution_lead')
    check_subset(db, parent, payload)
    grant = data.get('grant_id') or str(uuid.uuid4())
    insert_grant(db, grant, stage, None, parent_id, payload, 'pending')
    db.execute('INSERT INTO spawn_intents_v160 VALUES (?,?,?,?,NULL)', (actor, task_name, role, grant))
    audit_event(db, 'subgrant', {'actor': actor, 'grant': grant, 'parent': parent_id, 'task_name': task_name})
    return grant


def bind_stage(path: Path, actor: str, plan_file: Path) -> dict:
    plan = json.loads(plan_file.read_text(encoding='utf-8'))
    if plan.get('format_version') != '1.6.0' or plan.get('status') != 'approved':
        raise ValueError('bind-stage needs an approved v1.6.0 plan projection.')
    if plan['authorization']['issuer_actor'] != actor:
        raise ValueError('Requester does not match the plan issuer.')
    plan_ref = Path(plan['plan_ref']).resolve()
    if not plan_ref.is_file() or not plan.get('completion_ref'):
        raise ValueError('The human plan and completion reference are required.')
    if plan['budget']['team_work_slots'] != MAX_ACTIVE or plan['budget']['max_edges_below_lead'] != 2:
        raise ValueError('v160 uses five work slots and two edges below the lead.')
    team, stage_id, revision = (str(plan[k]) for k in ('team_id', 'stage_id', 'plan_revision'))
    lead = plan.get('responsible_actor')
    planner = plan.get('planner_actor') or actor
    with transaction(path) as db:
        issuer = db.execute('SELECT * FROM actor_bindings_v160 WHERE actor_id=?', (actor,)).fetchone()
        registered = db.execute('SELECT * FROM actors WHERE session=?', (actor,)).fetchone()
        if not issuer or not registered or registered['team'] != team or issuer['parent_id']:
            raise ValueError('A registered actual root binds the approved stage; children use subgrants.')
        owner_authority(plan['authorization']['source_ref'], dict(issuer))
        assigned = db.execute('SELECT * FROM actor_bindings_v160 WHERE actor_id=?', (planner,)).fetchone()
        member = db.execute('SELECT * FROM actors WHERE session=?', (planner,)).fetchone()
        if not assigned or not member or member['team'] != team or assigned['parent_id']:
            raise ValueError('Assigned Planner must be a registered actual root in this logical team.')
        old = db.execute('SELECT * FROM stage_bindings_v160 WHERE team_id=? AND stage_id=?', (team, stage_id)).fetchone()
        encoded = json.dumps(plan, ensure_ascii=False, sort_keys=True)
        if old and old['revision'] == revision:
            if old['payload'] != encoded:
                raise ValueError('Plan content changed without a new revision.')
            return stage_context(db, team, stage_id)
        if old and (json.loads(old['payload'])['authorization']['issuer_actor'] != actor
                    or old['planner_actor'] != planner):
            raise ValueError('Stage revisions retain their original issuer and assigned Planner.')
        if not db.execute('SELECT 1 FROM stage_bindings_v160 WHERE team_id=?', (team,)).fetchone():
            if db.execute("SELECT 1 FROM spawns WHERE team=? AND state IN ('reserved','active','uncertain')", (team,)).fetchone():
                raise ValueError('An active unbound v151 team keeps its policy; bind a drained/new team.')
        if db.execute("SELECT 1 FROM stage_bindings_v160 WHERE team_id=? AND stage_id<>? AND status='active'", (team, stage_id)).fetchone():
            raise ValueError('Finish the current stage before binding another stage in this team.')
        if old:
            if db.execute("SELECT 1 FROM spawns WHERE team=? AND state IN ('reserved','active','uncertain') AND (child IS NULL OR child<>?)", (team, lead or '')).fetchone():
                raise ValueError('Reconcile running support members before replacing their grant projection.')
            db.execute("UPDATE stage_grants_v160 SET status='superseded' WHERE team_id=? AND stage_id=?", (team, stage_id))
        if lead:
            identity = db.execute('SELECT * FROM actor_bindings_v160 WHERE actor_id=?', (lead,)).fetchone()
            member = db.execute('SELECT * FROM actors WHERE session=?', (lead,)).fetchone()
            if not identity or not member or member['team'] != team:
                raise ValueError('Register the actual lead identity in this team before binding.')
            if identity['parent_id'] and BASE_ROLE.get(member['role']) != 'execution_lead':
                raise ValueError('A child lead must actually use an execution_lead role.')
        grant = str(uuid.uuid4())
        stage = {'team_id': team, 'stage_id': stage_id, 'revision': revision}
        db.execute('INSERT INTO stage_bindings_v160 VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(team_id,stage_id) DO UPDATE SET revision=excluded.revision,lead_actor=excluded.lead_actor,root_grant_id=excluded.root_grant_id,status=excluded.status,plan_ref=excluded.plan_ref,payload=excluded.payload',
                   (team, stage_id, revision, planner, lead, grant, 'active', str(plan_ref), encoded))
        payload = projection(plan, depth=2 if lead == planner else 3)
        payload.update(role='execution_lead' if lead == planner else 'planner', is_lead=lead == planner)
        insert_grant(db, grant, stage, planner, None, payload)
        db.execute("UPDATE actor_bindings_v160 SET policy_binding='v160' WHERE actor_id IN (SELECT session FROM actors WHERE team=?)", (team,))
        if lead and lead != planner:
            child = projection(plan, depth=2)
            child.update(role='execution_lead', is_lead=True)
            insert_grant(db, str(uuid.uuid4()), stage, lead, grant, child)
        elif not lead:
            create_subgrant(db, planner, grant, plan['lead_task_name'], plan.get('lead_role', 'execution_lead'),
                            {**plan, 'delegate_depth_left': 2})
        audit_event(db, 'bind-stage', {'actor': actor, 'planner_actor': planner, 'stage': stage, 'plan_file': str(plan_file.resolve()),
                                     'source_ref': plan['authorization']['source_ref']})
        return stage_context(db, team, stage_id)


def subgrant(path: Path, actor: str, parent: str, task: str, role: str, grant_file: Path) -> str:
    with transaction(path) as db:
        return create_subgrant(db, actor, parent, task, role,
                               json.loads(grant_file.read_text(encoding='utf-8')))


def team_is_v160(db: sqlite3.Connection, team: str) -> bool:
    return bool(db.execute('SELECT 1 FROM stage_bindings_v160 WHERE team_id=?', (team,)).fetchone())


def active_count(db: sqlite3.Connection, team: str) -> int:
    count = db.execute("SELECT count(*) FROM spawns WHERE team=? AND state IN ('reserved','active','uncertain')", (team,)).fetchone()[0]
    if team_is_v160(db, team):
        count += db.execute("SELECT count(DISTINCT b.lead_actor) FROM stage_bindings_v160 b JOIN actors a ON a.session=b.lead_actor WHERE b.team_id=? AND b.status='active' AND a.is_main=1 AND NOT EXISTS (SELECT 1 FROM spawns s WHERE s.child=b.lead_actor AND s.state IN ('reserved','active','uncertain'))", (team,)).fetchone()[0]
    return count


def reserve_checked(db: sqlite3.Connection, root: Path, actor: str, req: str,
                    role: str, task_name: str | None, *, origin: str) -> dict:
    """Shared authorization and allocation for native hooks and explicit lifecycle."""
    cfg = role_config(root, role)
    member = db.execute('SELECT * FROM actors WHERE session=?', (actor,)).fetchone()
    if not member:
        raise ValueError('Register actual identity with team-init first.')
    intent = None
    if team_is_v160(db, member['team']):
        grant = active_grant(db, actor)
        binding = db.execute('SELECT * FROM actor_bindings_v160 WHERE actor_id=?', (actor,)).fetchone()
        role_capability = CAN_SPAWN.get(grant['payload']['role'], False) or grant['payload']['role'] == 'planner'
        identity = Actor(actor, binding['runtime_root_id'], binding['parent_id'] is None, binding['parent_id'])
        if not can_spawn(identity, role_can_spawn=role_capability,
                         delegate_depth_left=grant['payload']['delegate_depth_left'], stage_bound=True):
            raise ValueError('Actor role/stage grant cannot spawn.')
        intent = db.execute('SELECT * FROM spawn_intents_v160 WHERE parent_actor=? AND task_name=?',
                            (actor, task_name)).fetchone()
        if not intent or intent['role'] != role:
            raise ValueError('Register a matching subgrant/task_name before native spawn.')
        child = grant_row(db, intent['grant_id'], statuses=('pending',))
        if child['parent_grant_id'] != grant['grant_id']:
            raise ValueError('Spawn intent belongs to a different parent grant.')
        check_subset(db, grant, child['payload'], exclude_grant=child['grant_id'])
        if intent['request']:
            prepared = db.execute('SELECT * FROM spawns WHERE request=?', (intent['request'],)).fetchone()
            if not prepared or prepared['child'] or prepared['actor'] != actor or prepared['role'] != role or prepared['model'] != cfg['model']:
                raise ValueError('Prepared intent no longer matches this actor/role; reconcile it.')
            if origin == 'project-cli' and prepared['state'] in LIVE:
                return {'allow': True, 'request': prepared['request'], 'role': role, 'team': member['team'],
                        'state': prepared['state'], 'new_reservation': False,
                        'next_action': 'Record/reconcile the original native result; do not repeat spawn.'}
            if origin == 'native-hook' and prepared['request'].startswith('project:') and prepared['state'] == 'reserved':
                old_request = prepared['request']
                db.execute('UPDATE spawns SET request=? WHERE request=?', (req, old_request))
                db.execute('UPDATE astra_slot SET request=? WHERE request=?', (req, old_request))
                db.execute('UPDATE spawn_intents_v160 SET request=? WHERE request=?', (req, old_request))
                audit_event(db, 'prepared-spawn-promoted', {'project_request': old_request,
                            'native_request': req, 'actor': actor, 'task_name': task_name, 'origin': origin})
                return {'allow': True, 'request': req, 'role': role, 'team': member['team'],
                        'state': 'reserved', 'new_reservation': False}
            raise ValueError('Spawn request already exists; reconcile it rather than retry.')
    elif not member['is_main']:
        raise ValueError('Unbound v151 children retain their old no-spawn policy; bind a new stage.')
    if db.execute('SELECT 1 FROM spawns WHERE request=?', (req,)).fetchone():
        raise ValueError('Spawn request already exists; reconcile it rather than retry.')
    if active_count(db, member['team']) >= MAX_ACTIVE:
        raise ValueError('Logical team has five active/reserved/uncertain work slots.')
    if cfg['model'] == 'gpt-6-astra':
        if BASE_ROLE[role] != 'deep_researcher':
            raise ValueError('Only deep_researcher may use Astra.')
        if db.execute('SELECT 1 FROM astra_slot WHERE team=?', (member['team'],)).fetchone():
            raise ValueError('Astra identity already allocated; resume that same identity.')
        db.execute('INSERT INTO astra_slot VALUES (?,?)', (member['team'], req))
    db.execute('INSERT INTO spawns VALUES (?,?,?,?,?,?,NULL,?,NULL)',
               (req, member['team'], actor, role, cfg['model'], 'reserved', time.time()))
    if intent:
        db.execute('UPDATE spawn_intents_v160 SET request=? WHERE grant_id=?', (req, intent['grant_id']))
    audit_event(db, 'reserve', {'request': req, 'actor': actor, 'role': role,
                              'team': member['team'], 'origin': origin})
    return {'allow': True, 'request': req, 'role': role, 'team': member['team'],
            'state': 'reserved', 'new_reservation': True}


def reserve_spawn(root: Path, data: dict, path: Path | None = None) -> dict:
    ti = tool_input(data)
    role = ti.get('agent_type') or ti.get('agentType') or 'default'
    if any(k in ti for k in ('model', 'model_reasoning_effort', 'reasoning_effort', 'effort')):
        raise ValueError('Choose a registered role instead of child model/effort overrides.')
    if ti.get('fork_turns') != 'none' or 'fork_context' in ti:
        raise ValueError('Use explicit fork_turns="none" and a focused brief.')
    with transaction(path or state_path(root)) as db:
        actor = require_hook_identity(db, data)
        return reserve_checked(db, root, actor, request_id(data), role,
                               ti.get('task_name'), origin='native-hook')


def require_cli_identity(db: sqlite3.Connection, actor: str) -> dict:
    identity = runtime_identity(actor)
    if not db.execute('SELECT 1 FROM actor_bindings_v160 WHERE actor_id=?', (actor,)).fetchone():
        raise ValueError('Register this actual actor identity before lifecycle operations.')
    save_identity(db, identity)
    return identity


def prepare_spawn(root: Path, path: Path, actor: str, task_name: str) -> dict:
    with transaction(path) as db:
        require_cli_identity(db, actor)
        intent = db.execute('SELECT * FROM spawn_intents_v160 WHERE parent_actor=? AND task_name=?',
                            (actor, task_name)).fetchone()
        if not intent:
            raise ValueError('prepare-spawn requires an existing pending subgrant.')
        return reserve_checked(db, root, actor, 'project:' + str(uuid.uuid4()),
                               intent['role'], task_name, origin='project-cli')


def response_object(data: dict) -> dict:
    result = data.get('tool_response', data.get('toolResponse', {}))
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            return {}
    return result if isinstance(result, dict) else {}


def child_identity(result: dict, spawn: sqlite3.Row, parent: dict) -> dict | None:
    child = result.get('agent_id') or result.get('agentId') or result.get('thread_id')
    if child:
        if not isinstance(child, str):
            raise ValueError('Native child id must be a string.')
        return {'actor_id': child, 'runtime_root_id': parent['runtime_root_id'],
                'parent_id': spawn['actor'], 'host_id': parent['host_id'],
                'role': spawn['role'], 'canonical_path': result.get('task_name'),
                'evidence_ref': 'native-spawn:' + spawn['request']}
    canonical = result.get('task_name') or result.get('taskName')
    if not canonical:
        return None
    found = []
    for path in (Path.home() / '.codex/sessions').glob('**/*.jsonl'):
        if path.stat().st_mtime < spawn['created'] - 5:
            continue
        meta = session_metadata(path)
        source = meta.get('source')
        created = source.get('subagent', {}).get('thread_spawn', {}) if isinstance(source, dict) else {}
        if created.get('agent_path') == canonical and created.get('parent_thread_id') == spawn['actor']:
            found.append(runtime_identity(transcript=path))
    if len(found) > 1:
        raise ValueError('Canonical task name has multiple identities; reconcile exact transcript.')
    return found[0] if found else None


def complete_spawn_checked(db: sqlite3.Connection, req: str, actor: str, result: dict,
                           *, identity: dict | None = None, origin: str) -> dict:
    spawn = db.execute('SELECT * FROM spawns WHERE request=?', (req,)).fetchone()
    if not spawn:
        raise ValueError('Unreserved spawn result; inspect the lifecycle path.')
    if actor != spawn['actor']:
        raise ValueError('Spawn result belongs to another creator.')
    parent_row = db.execute('SELECT * FROM actor_bindings_v160 WHERE actor_id=?', (spawn['actor'],)).fetchone()
    parent = dict(parent_row) if parent_row else {'runtime_root_id': spawn['actor'], 'host_id': socket.gethostname()}
    identity = identity or child_identity(result, spawn, parent)
    if not identity:
        db.execute("UPDATE spawns SET state='uncertain' WHERE request=? AND child IS NULL", (req,))
        audit_event(db, 'spawn-uncertain', {'request': req, 'result': result, 'origin': origin})
        return {'request': req, 'state': 'uncertain', 'origin': origin}
    child = identity['actor_id']
    if identity['parent_id'] != spawn['actor'] or identity['runtime_root_id'] != parent['runtime_root_id'] or identity['role'] != spawn['role']:
        raise ValueError('Native child ancestry/role does not match its spawn reservation.')
    if spawn['child']:
        if spawn['child'] != child:
            raise ValueError('Spawn result changed identity.')
        return {'request': req, 'child': child, 'state': spawn['state'], 'origin': origin}
    db.execute('UPDATE spawns SET child=?,state=? WHERE request=?', (child, 'active', req))
    db.execute('INSERT INTO actors VALUES (?,?,0,?)', (child, spawn['team'], spawn['role']))
    save_identity(db, identity, 'v160' if team_is_v160(db, spawn['team']) else 'v151')
    alias = identity.get('canonical_path')
    if alias:
        scoped_alias = identity['runtime_root_id'] + ':' + alias if team_is_v160(db, spawn['team']) else alias
        db.execute('INSERT INTO actor_aliases VALUES (?,?)', (scoped_alias, child))
    intent = db.execute('SELECT * FROM spawn_intents_v160 WHERE request=?', (req,)).fetchone()
    if intent:
        grant = grant_row(db, intent['grant_id'], statuses=('pending',))
        db.execute("UPDATE stage_grants_v160 SET actor_id=?,status='active' WHERE grant_id=?", (child, grant['grant_id']))
        if grant['payload'].get('is_lead'):
            db.execute('UPDATE stage_bindings_v160 SET lead_actor=? WHERE team_id=? AND stage_id=?',
                       (child, spawn['team'], grant['stage_id']))
    audit_event(db, 'spawn-result', {'request': req, 'child': child, 'identity': identity, 'origin': origin})
    return {'request': req, 'child': child, 'state': 'active', 'origin': origin}


def complete_spawn(path: Path, data: dict, *, identity: dict | None = None) -> None:
    with transaction(path) as db:
        complete_spawn_checked(db, request_id(data), require_hook_identity(db, data), response_object(data),
                               identity=identity, origin='transcript-reconciliation' if identity else 'native-hook')


def record_spawn(path: Path, actor: str, task_name: str, result_file: Path) -> dict:
    result = json.loads(result_file.read_text(encoding='utf-8'))
    if not isinstance(result, dict):
        raise ValueError('result must contain the actual native spawn result object.')
    with transaction(path) as db:
        parent = require_cli_identity(db, actor)
        intent = db.execute('SELECT * FROM spawn_intents_v160 WHERE parent_actor=? AND task_name=?',
                            (actor, task_name)).fetchone()
        if not intent or not intent['request']:
            raise ValueError('No prepared reservation exists for this actor/task_name.')
        spawn = db.execute('SELECT * FROM spawns WHERE request=?', (intent['request'],)).fetchone()
        reported_id = result.get('agent_id') or result.get('agentId') or result.get('thread_id')
        identity = runtime_identity(reported_id) if reported_id else child_identity(result, spawn, parent)
        if identity and identity.get('canonical_path', '').rsplit('/', 1)[-1] != task_name:
            raise ValueError('Actual child task path does not match the prepared intent.')
        recorded = complete_spawn_checked(db, intent['request'], actor, result,
                                         identity=identity, origin='project-cli')
        audit_event(db, 'project-spawn-result-recorded', {'actor': actor, 'task_name': task_name,
                    'result_ref': str(result_file.resolve()), **recorded})
        return recorded


def target_actor(db: sqlite3.Connection, data: dict) -> str:
    ti = tool_input(data)
    target = ti.get('target') or ti.get('id') or ti.get('agent_id')
    if not isinstance(target, str) or not target:
        raise ValueError('Agent target is required.')
    if db.execute('SELECT 1 FROM actors WHERE session=?', (target,)).fetchone():
        return target
    caller = boundary_actor(db, actor_id(data))
    candidates = [target]
    if not target.startswith('/'):
        alias = db.execute('SELECT alias FROM actor_aliases WHERE session=?', (caller.session,)).fetchone()
        caller_path = alias[0].split(':', 1)[-1] if alias else '/root'
        candidates.append(caller_path + '/' + target)
    for candidate in candidates:
        for alias in (caller.root_session + ':' + candidate, candidate):
            row = db.execute('SELECT session FROM actor_aliases WHERE alias=?', (alias,)).fetchone()
            if row and boundary_actor(db, row[0]).root_session == caller.root_session:
                return row[0]
    raise ValueError('Target is not a registered actor or native task path.')


def require_owned_child(db: sqlite3.Connection, data: dict) -> str:
    actor = require_hook_identity(db, data)
    child = target_actor(db, data)
    parent = db.execute('SELECT * FROM actors WHERE session=?', (actor,)).fetchone()
    spawn = db.execute('SELECT * FROM spawns WHERE child=?', (child,)).fetchone()
    if not parent or not spawn or spawn['actor'] != actor or spawn['team'] != parent['team']:
        raise ValueError('Only the actual creator may control this child.')
    if team_is_v160(db, parent['team']):
        active_grant(db, actor)
    elif not parent['is_main']:
        raise ValueError('Unbound v151 control remains with its owning Main.')
    return child


def boundary_actor(db: sqlite3.Connection, actor: str) -> Actor:
    row = db.execute('SELECT * FROM actors WHERE session=?', (actor,)).fetchone()
    if not row:
        raise ValueError('Unknown actor.')
    identity = db.execute('SELECT * FROM actor_bindings_v160 WHERE actor_id=?', (actor,)).fetchone()
    if identity:
        return Actor(actor, identity['runtime_root_id'], identity['parent_id'] is None, identity['parent_id'])
    parent = db.execute('SELECT actor FROM spawns WHERE child=?', (actor,)).fetchone()
    if row['is_main']:
        return Actor(actor, actor, True)
    if not parent:
        raise ValueError('Child has no recorded creator.')
    ancestor = boundary_actor(db, parent['actor'])
    return Actor(actor, ancestor.root_session, False, parent['actor'])


def validate_contact(path: Path, data: dict, *, technical_message: bool) -> None:
    with transaction(path) as db:
        actor = require_hook_identity(db, data)
        target = target_actor(db, data)
        if not technical_message:
            require_owned_child(db, data)
            return
        members = db.execute('SELECT team FROM actors WHERE session IN (?,?)', (actor, target)).fetchall()
        if len(members) != 2 or members[0]['team'] != members[1]['team']:
            raise ValueError('Technical contact requires the same logical team.')
        identities = {item: boundary_actor(db, item) for item in (actor, target)}
        if not can_contact(actor, target, identities):
            raise ValueError('Cross-root messages need an explicitly bound stage_channel endpoint.')
        if tool_input(data).get('interrupt'):
            require_owned_child(db, data)


def validate_resume(path: Path, data: dict) -> None:
    if any(k in tool_input(data) for k in ('model', 'effort', 'reasoning_effort', 'model_reasoning_effort')):
        raise ValueError('Follow-up/resume cannot change model or effort.')
    with transaction(path) as db:
        child = require_owned_child(db, data)
        spawn = db.execute('SELECT * FROM spawns WHERE child=?', (child,)).fetchone()
        if spawn['state'] == 'closed':
            if active_count(db, spawn['team']) >= MAX_ACTIVE:
                raise ValueError('No free logical team work slot for follow-up/resume.')
            row = db.execute('SELECT g.grant_id FROM stage_grants_v160 g JOIN spawn_intents_v160 i ON i.grant_id=g.grant_id WHERE i.request=?', (spawn['request'],)).fetchone()
            if row:
                grant = grant_row(db, row[0], statuses=('active', 'completed'))
                parent = grant_row(db, grant['parent_grant_id'])
                check_subset(db, parent, grant['payload'], exclude_grant=grant['grant_id'])
                db.execute("UPDATE stage_grants_v160 SET status='active' WHERE grant_id=?", (grant['grant_id'],))
            db.execute("UPDATE spawns SET state='reserved' WHERE child=?", (child,))
        audit_event(db, 'resume', {'child': child, 'actor': actor_id(data)})


def resume_done(path: Path, data: dict) -> None:
    with transaction(path) as db:
        child = require_owned_child(db, data)
        result = response_object(data)
        # Ambiguous or explicitly failed results keep their slot for reconciliation.
        if result and result.get('success') is not False and not result.get('error'):
            db.execute("UPDATE spawns SET state='active' WHERE child=? AND state='reserved'", (child,))


def mark_terminal(db: sqlite3.Connection, child: str, evidence: dict) -> None:
    db.execute("UPDATE spawns SET state='closed',evidence=? WHERE child=?", (json.dumps(evidence), child))
    grant = db.execute("SELECT * FROM stage_grants_v160 WHERE actor_id=? AND status='active'", (child,)).fetchone()
    while grant:
        if db.execute("SELECT 1 FROM stage_grants_v160 WHERE parent_grant_id=? AND status IN ('pending','active')", (grant['grant_id'],)).fetchone():
            break
        holder = db.execute('SELECT state FROM spawns WHERE child=?', (grant['actor_id'],)).fetchone()
        if not holder or holder['state'] != 'closed':
            break
        db.execute("UPDATE stage_grants_v160 SET status='completed' WHERE grant_id=?", (grant['grant_id'],))
        grant = db.execute("SELECT * FROM stage_grants_v160 WHERE grant_id=? AND status='active'", (grant['parent_grant_id'],)).fetchone()
    audit_event(db, 'terminal', {'child': child, 'evidence': evidence})
    # Astra's identity allocation deliberately survives terminal completion.


def close_child(path: Path, data: dict) -> None:
    result = response_object(data)
    if not (result.get('success') is True or result.get('status') == 'closed'):
        return
    with transaction(path) as db:
        mark_terminal(db, require_owned_child(db, data), {'tool': 'close_agent', 'result': result})


def observe_agent_status(path: Path, data: dict) -> None:
    result = response_object(data)
    with transaction(path) as db:
        actor = require_hook_identity(db, data)
        member = db.execute('SELECT team FROM actors WHERE session=?', (actor,)).fetchone()
        if not member:
            return
        for entry in result.get('agents', []):
            status = entry.get('agent_status')
            if isinstance(status, dict) and len(status) == 1:
                status = next(iter(status))
            if status not in ('completed', 'failed', 'interrupted'):
                continue
            root_id = boundary_actor(db, actor).root_session
            row = db.execute("SELECT s.child FROM spawns s JOIN actor_aliases a ON a.session=s.child WHERE a.alias IN (?,?) AND s.team=? AND s.state IN ('active','reserved','uncertain')",
                             (root_id + ':' + entry['agent_name'], entry['agent_name'], member['team'])).fetchone()
            if row and boundary_actor(db, row[0]).root_session != root_id:
                raise ValueError('Agent status result belongs to a different runtime root.')
            if row:
                mark_terminal(db, row[0], {'tool': 'list_agents', 'request': request_id(data), 'result': entry})


def reconcile_terminal(path: Path, child: str, transcript: Path) -> None:
    identity = runtime_identity(child, transcript)
    latest = None
    for line in transcript.open(encoding='utf-8'):
        record = json.loads(line)
        if record.get('type') == 'event_msg' and record.get('payload', {}).get('type') in ('task_started', 'task_complete'):
            latest = record
    if not latest or latest['payload']['type'] != 'task_complete':
        raise ValueError('Transcript has no final native task_complete after its latest task_started.')
    completed = datetime.fromisoformat(latest['timestamp'].replace('Z', '+00:00')).timestamp()
    with transaction(path) as db:
        spawn = db.execute('SELECT * FROM spawns WHERE child=?', (child,)).fetchone()
        if not spawn or spawn['actor'] != identity['parent_id']:
            raise ValueError('Terminal transcript is not this registered child.')
        since = spawn['created']
        for row in db.execute("SELECT at,data FROM audit WHERE event='resume'"):
            if json.loads(row['data']).get('child') == child:
                since = max(since, row['at'])
        if completed < since:
            raise ValueError('Completion evidence predates the latest spawn/resume request.')
        mark_terminal(db, child, {'source_ref': str(transcript.resolve()), 'event': latest})


def reconcile_failed(path: Path, req: str, evidence: Path) -> None:
    if not evidence.is_file() or not evidence.stat().st_size:
        raise ValueError('Nonempty evidence of NO child created is required.')
    text = evidence.read_text(encoding='utf-8')
    with transaction(path) as db:
        spawn = db.execute('SELECT * FROM spawns WHERE request=?', (req,)).fetchone()
        if not spawn or spawn['child'] or spawn['state'] not in ('reserved', 'uncertain'):
            raise ValueError('Only unbound reservations can be reconciled as never created.')
        db.execute("UPDATE spawns SET state='failed',evidence=? WHERE request=?", (text, req))
        db.execute('DELETE FROM astra_slot WHERE request=?', (req,))
        db.execute('UPDATE spawn_intents_v160 SET request=NULL WHERE request=?', (req,))
        audit_event(db, 'operator-reconciled-no-child', {'request': req, 'evidence_path': str(evidence.resolve()), 'evidence_text': text})


def finish_stage(path: Path, actor: str, team: str, stage_id: str) -> None:
    with transaction(path) as db:
        stage = stage_context(db, team, stage_id)
        if actor not in (stage['planner_actor'], stage['lead_actor']):
            raise ValueError('Only the bound Planner or lead may record stage completion.')
        own_lead = actor if actor == stage['lead_actor'] else ''
        if db.execute("SELECT 1 FROM spawns WHERE team=? AND state IN ('reserved','active','uncertain') AND (child IS NULL OR child<>?)", (team, own_lead)).fetchone():
            raise ValueError('Reconcile active support members before finishing the stage.')
        status = 'execution_complete' if actor != stage['planner_actor'] else 'completed'
        db.execute('UPDATE stage_bindings_v160 SET status=? WHERE team_id=? AND stage_id=?', (status, team, stage_id))
        db.execute("UPDATE stage_grants_v160 SET status='completed' WHERE team_id=? AND stage_id=? AND status IN ('pending','active')", (team, stage_id))
        audit_event(db, 'stage-complete', {'actor': actor, 'team': team, 'stage': stage_id, 'status': status})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--state', type=Path, help='Explicit single-host state authority; use a temporary path for isolated exercises.')
    commands = parser.add_subparsers(dest='command', required=True)
    q = commands.add_parser('identity'); q.add_argument('--session'); q.add_argument('--transcript', type=Path)
    q = commands.add_parser('team-init'); q.add_argument('--session', required=True); q.add_argument('--team', required=True); q.add_argument('--transcript', type=Path)
    q = commands.add_parser('bind-stage'); q.add_argument('--actor', required=True); q.add_argument('--plan', type=Path, required=True)
    q = commands.add_parser('subgrant'); q.add_argument('--actor', required=True); q.add_argument('--parent-grant', required=True); q.add_argument('--task-name', required=True); q.add_argument('--role', required=True); q.add_argument('--grant', type=Path, required=True)
    q = commands.add_parser('prepare-spawn'); q.add_argument('--actor', required=True); q.add_argument('--task-name', required=True)
    q = commands.add_parser('record-spawn'); q.add_argument('--actor', required=True); q.add_argument('--task-name', required=True); q.add_argument('--result', type=Path, required=True)
    q = commands.add_parser('finish-stage'); q.add_argument('--actor', required=True); q.add_argument('--team', required=True); q.add_argument('--stage', required=True)
    q = commands.add_parser('reconcile-terminal'); q.add_argument('--child', required=True); q.add_argument('--transcript', type=Path, required=True)
    q = commands.add_parser('reconcile-spawn'); q.add_argument('--request', required=True); q.add_argument('--transcript', type=Path, required=True); q.add_argument('--creator-transcript', type=Path, required=True)
    q = commands.add_parser('reconcile-no-child'); q.add_argument('--request', required=True); q.add_argument('--evidence', type=Path, required=True)
    commands.add_parser('status')
    args = parser.parse_args()
    path = args.state or state_path(args.root)
    try:
        if args.command == 'identity':
            print(json.dumps(runtime_identity(args.session, args.transcript), ensure_ascii=False, indent=2)); return 0
        if args.command == 'team-init': initialize_team(path, args.session, args.team, args.transcript)
        elif args.command == 'bind-stage': bind_stage(path, args.actor, args.plan)
        elif args.command == 'subgrant':
            print(json.dumps({'grant_id': subgrant(path, args.actor, args.parent_grant, args.task_name, args.role, args.grant)})); return 0
        elif args.command == 'prepare-spawn':
            print(json.dumps(prepare_spawn(args.root, path, args.actor, args.task_name), ensure_ascii=False)); return 0
        elif args.command == 'record-spawn':
            result = record_spawn(path, args.actor, args.task_name, args.result)
            print(json.dumps(result, ensure_ascii=False)); return 2 if result['state'] == 'uncertain' else 0
        elif args.command == 'finish-stage': finish_stage(path, args.actor, args.team, args.stage)
        elif args.command == 'reconcile-terminal': reconcile_terminal(path, args.child, args.transcript)
        elif args.command == 'reconcile-no-child': reconcile_failed(path, args.request, args.evidence)
        elif args.command == 'reconcile-spawn':
            parent = runtime_identity(transcript=args.creator_transcript)
            complete_spawn(path, {'session_id': parent['runtime_root_id'], 'transcript_path': str(args.creator_transcript), 'tool_use_id': args.request}, identity=runtime_identity(transcript=args.transcript))
        with transaction(path) as db:
            result = {table: [dict(row) for row in db.execute(f'SELECT * FROM {table}')]
                      for table in ('actors', 'spawns', 'astra_slot', 'actor_bindings_v160', 'stage_bindings_v160', 'stage_grants_v160', 'spawn_intents_v160')}
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, KeyError, sqlite3.Error, subprocess.SubprocessError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
