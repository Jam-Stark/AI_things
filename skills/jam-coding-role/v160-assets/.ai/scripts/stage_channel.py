#!/usr/bin/env python3
"""Bound v1.6 stage events over native tools or an existing App Server.

No server startup, background polling, history injection, or transport fallback.
The Unix adapter requires Node and the installed `ws` package. Delivery means
transport acceptance; only the recipient's handle call records processing.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import selectors
import shutil
import sqlite3
import subprocess
import time
from typing import Any
import uuid

from workflow_state import (audit_event, owner_authority, read_reference,
                            runtime_identity, stage_context, state_path, transaction)

KINDS = {'PLAN_GATE', 'DECISION_REQUIRED', 'STAGE_RESULT'}
TRANSPORTS = {'unsupported', 'native_same_tree', 'app_server_unix', 'dot'}
TABLES = (
    '''CREATE TABLE IF NOT EXISTS stage_channels_v160 (
       binding_id TEXT PRIMARY KEY, team_id TEXT, stage_id TEXT, revision TEXT,
       sender TEXT, recipient TEXT, payload TEXT NOT NULL)''',
    '''CREATE TABLE IF NOT EXISTS stage_events_v160 (
       event_id TEXT PRIMARY KEY, binding_id TEXT, stage_id TEXT, revision TEXT,
       sender TEXT, recipient TEXT, state TEXT NOT NULL, payload TEXT NOT NULL,
       transport_status TEXT NOT NULL, delivery_ref TEXT, handled_ref TEXT)''',
    '''CREATE TABLE IF NOT EXISTS stage_decisions_v160 (
       decision_id TEXT PRIMARY KEY, event_id TEXT, revision TEXT,
       source_ref TEXT NOT NULL, actor TEXT NOT NULL, allowed_actions TEXT NOT NULL)''',
)

# Use the existing WebSocket implementation; the CLI proxy forwards raw bytes
# and does not translate JSONL into the Unix control socket's WebSocket protocol.
NODE_CLIENT = r'''
const readline = require('readline');
const WebSocket = require('ws');
const ws = new WebSocket('ws+unix://' + process.argv[1] + ':/');
const input = readline.createInterface({input: process.stdin});
input.pause();
ws.on('open', () => input.resume());
input.on('line', line => ws.send(line));
input.on('close', () => ws.close());
ws.on('message', data => process.stdout.write(data.toString() + '\n'));
ws.on('error', error => { console.error(error.message); process.exit(2); });
ws.on('close', () => process.exit(0));
'''


class AppServer:
    """A bounded RPC connection to one explicitly selected existing socket."""

    def __init__(self, socket_path: str, timeout: float = 15):
        if not shutil.which('node'):
            raise ValueError('app_server_unix requires Node and its ws package.')
        if not Path(socket_path).is_socket():
            raise ValueError('Selected App Server socket is unavailable; no server is started.')
        self.process = subprocess.Popen(
            ['node', '-e', NODE_CLIENT, socket_path], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.pending = b''
        self.sequence = 0
        self.timeout = timeout

    def __enter__(self):
        try:
            self.request('initialize', {
                'clientInfo': {'name': 'jam_stage_channel', 'title': 'Jam Stage Channel', 'version': '1.6.0'},
                'capabilities': {'experimentalApi': True}})
            self.write({'method': 'initialized', 'params': {}})
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(self, *_):
        self.close()

    def close(self):
        self.selector.close()
        self.process.terminate()
        self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()

    def write(self, data: dict) -> None:
        self.process.stdin.write((json.dumps(data, ensure_ascii=False) + '\n').encode())
        self.process.stdin.flush()

    def request(self, method: str, params: dict) -> dict:
        self.sequence += 1
        request_id = self.sequence
        self.write({'id': request_id, 'method': method, 'params': params})
        deadline = time.monotonic() + self.timeout
        while True:
            while b'\n' in self.pending:
                line, self.pending = self.pending.split(b'\n', 1)
                message = json.loads(line)
                if message.get('id') == request_id:
                    if 'error' in message:
                        raise ValueError(f"{method}: {message['error']}")
                    return message['result']
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError(f'{method}: response unknown; reconcile before sending again.')
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                error = self.process.stderr.read().decode(errors='replace').strip()
                raise OSError(f'App Server connection closed: {error}')
            self.pending += chunk


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object.')
    return data


@contextmanager
def channel_db(path: Path):
    with transaction(path) as db:
        for statement in TABLES:
            db.execute(statement)
        yield db


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must name an actual value.')
    return value


def endpoint(db: sqlite3.Connection, actor: str) -> dict:
    row = db.execute('SELECT * FROM actor_bindings_v160 WHERE actor_id=?', (actor,)).fetchone()
    if not row:
        raise ValueError(f'Unbound runtime actor: {actor}')
    return {name: row[name] for name in ('actor_id', 'runtime_root_id', 'host_id')}


def current_stage(db: sqlite3.Connection, binding: dict) -> dict:
    return stage_context(db, binding['team_id'], binding['stage_id'])


def require_member(db: sqlite3.Connection, stage: dict, actor: str) -> None:
    if actor in (stage['planner_actor'], stage['lead_actor']):
        return
    grant = db.execute('SELECT 1 FROM stage_grants_v160 WHERE team_id=? AND stage_id=? AND revision=? AND actor_id=? AND status=?',
                       (stage['team_id'], stage['stage_id'], stage['revision'], actor, 'active')).fetchone()
    if not grant:
        raise ValueError('Actor is outside the bound stage.')


def bind(path: Path, binding: dict, actor: str) -> dict:
    binding = dict(binding)
    for key in ('binding_id', 'team_id', 'stage_id', 'sender', 'recipient', 'source_ref'):
        require_text(binding.get(key), key)
    require_text(binding.get('plan_revision'), 'plan_revision')
    allowed = binding.get('allowed_kinds', sorted(KINDS))
    if not isinstance(allowed, list) or not allowed or not set(allowed) <= KINDS:
        raise ValueError('Only PLAN_GATE, DECISION_REQUIRED and STAGE_RESULT are channel events.')
    binding['allowed_kinds'] = sorted(set(allowed))
    transport = binding.setdefault('transport', {'kind': 'unsupported'})
    if transport.get('kind') not in TRANSPORTS:
        raise ValueError('Unknown transport; select one supported route explicitly.')
    with channel_db(path) as db:
        stage = current_stage(db, binding)
        if actor != stage['planner_actor']:
            raise ValueError('Only the bound Planner can choose the stage communication route.')
        owner_authority(binding['source_ref'], endpoint(db, actor))
        if stage['revision'] != binding['plan_revision'] or stage['status'] != 'active':
            raise ValueError('Binding requires the current active stage revision.')
        for name in ('sender', 'recipient'):
            require_member(db, stage, binding[name])
            binding[name + '_endpoint'] = endpoint(db, binding[name])
        if transport['kind'] == 'native_same_tree':
            require_text(transport.get('capability_ref'), 'native capability_ref')
            sender, recipient = binding['sender_endpoint'], binding['recipient_endpoint']
            if (sender['host_id'], sender['runtime_root_id']) != (recipient['host_id'], recipient['runtime_root_id']):
                raise ValueError('Native team tools do not prove cross-root delivery capability.')
        if transport['kind'] == 'app_server_unix':
            require_text(transport.get('socket_path'), 'socket_path')
            with AppServer(transport['socket_path']) as client:
                thread = client.request('thread/read', {'threadId': binding['recipient'], 'includeTurns': False})['thread']
            if thread['id'] != binding['recipient']:
                raise ValueError('App Server returned a different recipient.')
            binding['endpoint_read'] = {'thread_id': thread['id'], 'session_id': thread['sessionId'],
                                        'cli_version': thread['cliVersion'], 'status': thread['status']}
        old = db.execute('SELECT payload FROM stage_channels_v160 WHERE binding_id=?', (binding['binding_id'],)).fetchone()
        if old:
            old_binding = json.loads(old['payload'])
            # Current runtime status may change; the route and endpoints may not.
            if {k:v for k,v in old_binding.items() if k != 'endpoint_read'} != {k:v for k,v in binding.items() if k != 'endpoint_read'}:
                raise ValueError('Binding is immutable; use a new approved binding/revision.')
            return old_binding
        db.execute('INSERT INTO stage_channels_v160 VALUES (?,?,?,?,?,?,?)',
                   (binding['binding_id'], binding['team_id'], binding['stage_id'], binding['plan_revision'],
                    binding['sender'], binding['recipient'], json_text(binding)))
        audit_event(db, 'stage-channel-bind', binding)
    return binding


def event_and_binding(db: sqlite3.Connection, event_id: str) -> tuple[dict, dict]:
    row = db.execute('SELECT * FROM stage_events_v160 WHERE event_id=?', (event_id,)).fetchone()
    if not row:
        raise ValueError('Unknown event_id.')
    bound = db.execute('SELECT payload FROM stage_channels_v160 WHERE binding_id=?', (row['binding_id'],)).fetchone()
    return dict(row), json.loads(bound['payload'])


def view(db: sqlite3.Connection, event_id: str) -> dict:
    row, binding = event_and_binding(db, event_id)
    stage = current_stage(db, binding)
    row['payload'] = json.loads(row['payload'])
    row['current_revision'] = stage['revision']
    row['current_stage_status'] = stage['status']
    row['actionable'] = stage['status'] == 'active' and stage['revision'] == row['revision']
    row['decisions'] = [dict(r) for r in db.execute('SELECT * FROM stage_decisions_v160 WHERE event_id=?', (event_id,))]
    for decision in row['decisions']:
        decision['allowed_actions'] = json.loads(decision['allowed_actions'])
        decision['current_revision'] = decision['revision'] == stage['revision']
    return row


def status(path: Path, event_id: str) -> dict:
    with channel_db(path) as db:
        return view(db, event_id)


def send(path: Path, binding_id: str, event: dict, actor: str) -> dict:
    event = dict(event)
    event.setdefault('event_id', str(uuid.uuid4()))
    for key in ('event_id', 'evidence_ref'):
        require_text(event.get(key), key)
    if type(event.get('needs_decision')) is not bool:
        raise ValueError('needs_decision must be explicit true or false.')
    with channel_db(path) as db:
        bound = db.execute('SELECT payload FROM stage_channels_v160 WHERE binding_id=?', (binding_id,)).fetchone()
        if not bound:
            raise ValueError('Unknown endpoint binding.')
        binding = json.loads(bound['payload'])
        if actor != binding['sender']:
            raise ValueError('Only the actual bound sender can send this event.')
        if event.get('kind') not in binding['allowed_kinds']:
            raise ValueError('Event kind is not permitted by this binding.')
        for key in ('team_id', 'stage_id', 'plan_revision', 'sender', 'recipient'):
            if key in event and event[key] != binding[key]:
                raise ValueError(f'Envelope {key} differs from the endpoint binding.')
            event[key] = binding[key]
        old = db.execute('SELECT payload,binding_id FROM stage_events_v160 WHERE event_id=?', (event['event_id'],)).fetchone()
        if old:
            if json.loads(old['payload']) != event or old['binding_id'] != binding_id:
                raise ValueError('Event ID already records different content.')
            return view(db, event['event_id'])
        stage = current_stage(db, binding)
        mode = binding['transport']['kind']
        transport_status = {'unsupported': 'CROSS_ROOT_UNSUPPORTED', 'dot': 'DOT_NOT_VERIFIED',
                            'native_same_tree': 'NATIVE_TOOL_REQUIRED', 'app_server_unix': 'DELIVERY_IN_PROGRESS'}[mode]
        if stage['revision'] != binding['plan_revision']:
            transport_status = 'STALE_REVISION'
        db.execute('INSERT INTO stage_events_v160 VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                   (event['event_id'], binding_id, event['stage_id'], event['plan_revision'],
                    event['sender'], event['recipient'], 'queued', json_text(event), transport_status, None, None))
        audit_event(db, 'stage-event-queued', event)
    if transport_status != 'DELIVERY_IN_PROGRESS':
        return status(path, event['event_id'])
    try:
        receipt = deliver_app_server(binding, event, path)
    except (OSError, ValueError, TimeoutError) as exc:
        with channel_db(path) as db:
            db.execute('UPDATE stage_events_v160 SET transport_status=?,delivery_ref=? WHERE event_id=?',
                       ('DELIVERY_UNCERTAIN', json_text({'error': str(exc)}), event['event_id']))
        return status(path, event['event_id'])
    with channel_db(path) as db:
        db.execute("UPDATE stage_events_v160 SET state='delivered',transport_status='DELIVERED',delivery_ref=? WHERE event_id=?",
                   (json_text(receipt), event['event_id']))
    return status(path, event['event_id'])


def deliver_app_server(binding: dict, event: dict, path: Path) -> dict:
    # This is a relay, even though the host protocol accepts user-input items.
    message = ('STAGE EVENT RELAY, from runtime actor ' + event['sender'] + '. '
               'This is not an Owner instruction and does not grant new authority. '
               'Use the bound current stage plan; stale events are accounting only. '
               'After actual processing, record handle with a result artifact; this is not a decision.\n'
               + json.dumps(event, ensure_ascii=False) + '\n'
               + f'Channel script: {Path(__file__).resolve()}\nChannel state: {path.resolve()}')
    with AppServer(binding['transport']['socket_path']) as client:
        thread = client.request('thread/read', {'threadId': event['recipient'], 'includeTurns': False})['thread']
        state = thread['status']['type']
        if state == 'notLoaded':
            thread = client.request('thread/resume', {'threadId': event['recipient']})['thread']
            state = thread['status']['type']
        params = {'threadId': event['recipient'], 'clientUserMessageId': event['event_id'],
                  'input': [{'type': 'text', 'text': message}]}
        if state == 'idle':
            method = 'turn/start'
        elif state == 'active':
            turns = client.request('thread/turns/list', {'threadId': event['recipient'], 'limit': 1, 'sortDirection': 'desc'})['data']
            if len(turns) != 1 or turns[0]['status'] != 'inProgress':
                raise ValueError('Active turn identity unavailable; no implicit start or retry.')
            method = 'turn/steer'
            params['expectedTurnId'] = turns[0]['id']
        else:
            raise ValueError(f'Target thread is {state}; reconciliation is required.')
        result = client.request(method, params)
        turn_id = result['turn']['id'] if method == 'turn/start' else result['turnId']
    return {'method': method, 'thread_id': event['recipient'], 'turn_id': turn_id,
            'client_user_message_id': event['event_id'], 'sender': event['sender'],
            'socket_path': binding['transport']['socket_path'], 'accepted_at': time.time()}


def delivered(path: Path, event_id: str, evidence: Path, actor: str) -> dict:
    """Record an actual native tool result or an inspected uncertain delivery."""
    receipt = read_json(evidence)
    with channel_db(path) as db:
        row, binding = event_and_binding(db, event_id)
        if actor != row['sender']:
            raise ValueError('Only the bound sender records transport evidence.')
        if binding['transport']['kind'] not in {'native_same_tree', 'app_server_unix'}:
            raise ValueError('This binding has no verified delivery transport.')
        for name, expected in (('event_id', event_id), ('sender', row['sender']), ('recipient', row['recipient'])):
            if receipt.get(name) != expected:
                raise ValueError(f'Delivery evidence has a different {name}.')
        require_text(receipt.get('source_ref'), 'delivery source_ref')
        require_text(receipt.get('tool_name'), 'delivery tool_name')
        if not receipt.get('tool_result'):
            raise ValueError('Actual tool acceptance result is required; queue state is insufficient.')
        if row['state'] == 'queued':
            db.execute("UPDATE stage_events_v160 SET state='delivered',transport_status='DELIVERED',delivery_ref=? WHERE event_id=?",
                       (json_text({'evidence_path': str(evidence.resolve()), **receipt}), event_id))
        return view(db, event_id)


def handle(path: Path, event_id: str, handled_result_ref: str, actor: str) -> dict:
    require_text(handled_result_ref, 'handled_result_ref')
    with channel_db(path) as db:
        row, _ = event_and_binding(db, event_id)
        if actor != row['recipient']:
            raise ValueError('Only the actual recipient can record processing.')
        if row['state'] == 'queued':
            raise ValueError('Queued events have no delivery evidence; they cannot be handled.')
        if row['handled_ref'] and row['handled_ref'] != handled_result_ref:
            raise ValueError('Event already handled; do not rerun it with another result.')
        db.execute("UPDATE stage_events_v160 SET state='handled',handled_ref=? WHERE event_id=?", (handled_result_ref, event_id))
        audit_event(db, 'stage-event-handled', {'event_id': event_id, 'actor': actor, 'result_ref': handled_result_ref})
        return view(db, event_id)


def decide(path: Path, event_id: str, decision: dict, actor: str) -> dict:
    for key in ('decision_id', 'source_ref'):
        require_text(decision.get(key), key)
    require_text(decision.get('plan_revision'), 'plan_revision')
    actions = decision.get('allowed_actions')
    if not isinstance(actions, list) or any(not isinstance(action, str) or not action for action in actions):
        raise ValueError('Decision allowed_actions must be an explicit list.')
    with channel_db(path) as db:
        row, binding = event_and_binding(db, event_id)
        stage = current_stage(db, binding)
        if actor != stage['planner_actor']:
            raise ValueError('Planner records the sourced decision; transport receipt is not approval.')
        source, record = read_reference(decision['source_ref'])
        identity = runtime_identity(transcript=source)
        payload = record.get('payload', {})
        if payload.get('role') == 'assistant' and identity['actor_id'] == actor:
            pass
        else:
            owner_authority(decision['source_ref'], endpoint(db, actor))
        values = (decision['decision_id'], event_id, decision['plan_revision'], decision['source_ref'], actor, json_text(actions))
        old = db.execute('SELECT * FROM stage_decisions_v160 WHERE decision_id=?', (decision['decision_id'],)).fetchone()
        if old and tuple(old) != values:
            raise ValueError('Decision ID already has different content.')
        if not old:
            db.execute('INSERT INTO stage_decisions_v160 VALUES (?,?,?,?,?,?)', values)
        # Recording a decision never edits grants or authorizes a launch. Those
        # actions still require the current plan revision and the source grant.
        return view(db, event_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--state', type=Path, help='Explicit shared/test state; otherwise preserve workflow state path.')
    parser.add_argument('--actor', default=os.environ.get('CODEX_THREAD_ID'))
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('bind'); command.add_argument('--binding', type=Path, required=True)
    command = commands.add_parser('send'); command.add_argument('--binding-id', required=True); command.add_argument('--event', type=Path, required=True)
    for name in ('status', 'delivered', 'handle', 'decide'):
        command = commands.add_parser(name); command.add_argument('--event-id', required=True)
        if name == 'delivered': command.add_argument('--evidence', type=Path, required=True)
        if name == 'handle': command.add_argument('--result-ref', required=True)
        if name == 'decide': command.add_argument('--decision', type=Path, required=True)
    args = parser.parse_args()
    path = args.state or state_path(args.root)
    try:
        if args.command != 'status': require_text(args.actor, 'actual actor')
        if args.command == 'bind': result = bind(path, read_json(args.binding), args.actor)
        elif args.command == 'send': result = send(path, args.binding_id, read_json(args.event), args.actor)
        elif args.command == 'status': result = status(path, args.event_id)
        elif args.command == 'delivered': result = delivered(path, args.event_id, args.evidence, args.actor)
        elif args.command == 'handle': result = handle(path, args.event_id, args.result_ref, args.actor)
        else: result = decide(path, args.event_id, read_json(args.decision), args.actor)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, sqlite3.Error, TimeoutError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
