#!/usr/bin/env python3
"""Preview/apply a scoped v1.5.0 workflow upgrade; no Git commits or runtime probes."""
from __future__ import annotations
import argparse
import ast
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib

SKILL = Path(__file__).resolve().parents[1]
CORE_DOCS = ('ROLE.md', 'WORKFLOW.md', 'MODEL_ROUTING.md', 'CONTEXT_POLICY.md',
             'SESSION_PROTOCOL.md', 'TOOL_LIFECYCLE.md')
SCRIPTS = ('codex_preflight.py', 'codex_v150_hook.py', 'workflow_state.py',
           'session_bus.py', 'process_inventory.py', 'tool_guard.py', 'install_codex_hooks.py')


def toml_text(data: dict) -> str:
    def atom(value):
        if isinstance(value, str): return json.dumps(value, ensure_ascii=False)
        if isinstance(value, bool): return 'true' if value else 'false'
        if isinstance(value, (int, float)): return repr(value)
        if isinstance(value, (datetime.date, datetime.time)): return value.isoformat()
        if isinstance(value, list): return '[' + ', '.join(atom(v) for v in value) + ']'
        if isinstance(value, dict): return '{' + ', '.join(json.dumps(k) + ' = ' + atom(v) for k, v in value.items()) + '}'
        raise ValueError('Unsupported TOML value: ' + repr(value))
    lines = ['# Jam Coding Role v1.5.0; Main model/effort remain App-owned.']
    def table(value, prefix):
        if prefix: lines.extend(['', '[' + '.'.join(json.dumps(k) for k in prefix) + ']'])
        lines.extend(json.dumps(k) + ' = ' + atom(v) for k, v in value.items() if not isinstance(v, dict))
        for key, item in value.items():
            if isinstance(item, dict): table(item, prefix + [key])
    table(data, [])
    return '\n'.join(lines) + '\n'


def strip_extension(value):
    if isinstance(value, dict):
        value.pop('use_history_notes_extension', None)
        for item in value.values(): strip_extension(item)
    elif isinstance(value, list):
        for item in value: strip_extension(item)


def plan(root: Path, workflow_source: Path | None) -> dict[str, bytes]:
    source = workflow_source or SKILL / 'v150-assets'
    result = {}
    for name in CORE_DOCS:
        path = source / '.ai' / name if workflow_source else SKILL / 'references' / name
        result['.ai/' + name] = path.read_bytes()
    for name in SCRIPTS: result['.ai/scripts/' + name] = (source / '.ai/scripts' / name).read_bytes()
    for rel, template in (('AGENTS.md', 'AGENTS.md'), ('.codex/AGENTS.md', 'CODEX_AGENTS.md')):
        if workflow_source:
            result[rel] = (source / rel).read_bytes()
        else:
            # Generic migration adds routing while retaining project-specific instructions.
            path = root / rel
            existing = path.read_text() if path.exists() else (SKILL / 'templates' / template).read_text()
            begin, end = '<!-- JAM-V150-ROUTE-BEGIN -->', '<!-- JAM-V150-ROUTE-END -->'
            route = (SKILL / 'templates/AGENTS.md').read_text().split(begin, 1)[1].split(end, 1)[0]
            if begin in existing:
                before, tail = existing.split(begin, 1)
                _, after = tail.split(end, 1)
                existing = before + begin + route + end + after
            else:
                existing = begin + route + end + '\n\n' + existing
            result[rel] = existing.encode()
    result['.codex/TEAM.md'] = (source / '.codex/TEAM.md').read_bytes()
    for rel in ('.ai/ROLE_VERSION', '.codex/MODEL_TEAM_VERSION'): result[rel] = b'1.5.0\n'
    legacy = root / '.ai/scripts/codex_team_hook.py'
    if not legacy.exists(): result['.ai/scripts/codex_team_hook.py'] = (SKILL / 'scripts/codex_team_hook.py').read_bytes()

    cfg_file = root / '.codex/config.toml'
    cfg = tomllib.loads(cfg_file.read_text()) if cfg_file.exists() else {}
    seed = tomllib.loads((source / '.codex/config.toml').read_text())
    for table in [cfg] + list(cfg.get('profiles', {}).values()):
        table.pop('model', None); table.pop('model_reasoning_effort', None)
    for key in ('model_context_window', 'model_auto_compact_token_limit', 'model_auto_compact_token_limit_scope'):
        if key in seed: cfg.setdefault(key, seed[key])
    strip_extension(cfg)
    cfg['background_terminal_max_timeout'] = seed['background_terminal_max_timeout']
    features = cfg.setdefault('features', {}); features.pop('token_budget', None)
    features['context_management'] = {'experimental_mode': True}; features['hooks'] = True
    agents = cfg.setdefault('agents', {})
    for key in ('enabled', 'max_concurrent_threads_per_session', 'default_subagent_model', 'default_subagent_reasoning_effort', 'interrupt_message'):
        agents[key] = seed['agents'][key]
    existing_roles = {}
    for path in (root / '.codex/agents').glob('*.toml'):
        data = tomllib.loads(path.read_text()); name = data['name']
        if name in existing_roles: raise ValueError('Duplicate role: ' + name)
        existing_roles[name] = (path, data)
    supported = set()
    for path in sorted((source / '.codex/agents').glob('*.toml')):
        target_role = tomllib.loads(path.read_text()); name = target_role['name']; supported.add(name)
        previous = existing_roles.get(name)
        rel = str(previous[0].relative_to(root)) if previous else '.codex/agents/' + path.name
        if previous:
            old = previous[1]
            instructions = old.get('developer_instructions', '').split('\n\n[V1.5.0 CHILD GUARD]')[0]
            if name == 'deep_researcher': instructions = instructions.replace('Astra/high', 'Astra/medium').replace('high-effort Astra', 'medium-effort Astra')
            guard = target_role['developer_instructions'].split('\n\n[V1.5.0 CHILD GUARD]', 1)[1]
            merged = {**old, **target_role}
            merged['description'] = old.get('description', target_role['description'])
            if instructions: merged['developer_instructions'] = instructions + '\n\n[V1.5.0 CHILD GUARD]' + guard
            merged['features'] = {**old.get('features', {}), **target_role.get('features', {})}
            merged['agents'] = {**old.get('agents', {}), **target_role.get('agents', {})}
            if name != 'deep_researcher' and 'sandbox_mode' in old: merged['sandbox_mode'] = old['sandbox_mode']
            strip_extension(merged); target_role = merged
        result[rel] = toml_text(target_role).encode()
        agents[name] = {'description': target_role['description'], 'config_file': rel.split('.codex/', 1)[1]}
    if set(existing_roles) - supported:
        raise ValueError('Explicit mapping needed for custom roles: ' + ', '.join(sorted(set(existing_roles) - supported)))
    result['.codex/config.toml'] = toml_text(cfg).encode()
    hooks_file = root / '.codex/hooks.json'
    hooks = json.loads(hooks_file.read_text()) if hooks_file.exists() else {'hooks': {}}
    for event, groups in hooks['hooks'].items():
        for group in groups:
            group['hooks'] = [h for h in group.get('hooks', []) if not any(n in h.get('command', '') for n in ('codex_team_hook.py', 'codex_v150_hook.py'))]
        hooks['hooks'][event] = [g for g in groups if g['hooks']]
    new_hooks = json.loads((source / '.codex/hooks.json').read_text())
    for event, groups in new_hooks['hooks'].items(): hooks['hooks'].setdefault(event, []).extend(groups)
    hooks['description'] = new_hooks['description']
    result['.codex/hooks.json'] = (json.dumps(hooks, ensure_ascii=False, indent=2) + '\n').encode()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--workflow-source', type=Path, help='Approved project-specific source; only workflow paths are copied.')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(); root = args.root.resolve()
    if not (root / '.ai/PROJECT.md').is_file(): raise ValueError('Existing project overlay required; use bootstrap init for a new project.')
    changes = plan(root, args.workflow_source.resolve() if args.workflow_source else None)
    changes = {rel: data for rel, data in changes.items() if not (root / rel).exists() or (root / rel).read_bytes() != data}
    for rel, data in changes.items():
        if rel.endswith('.py'): ast.parse(data, filename=rel)
        elif rel.endswith('.toml'): tomllib.loads(data.decode())
        elif rel.endswith('.json'): json.loads(data)
    report = {'root': str(root), 'applied': False, 'files': list(changes)}
    if args.apply and changes:
        common = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--git-common-dir'], text=True).strip()
        common = (root / common).resolve()
        parent = common / 'jam-workflow-v150/backups'; parent.mkdir(parents=True, exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix=root.name + '-', dir=parent))
        manifest = {'root': str(root), 'files': [{'path': rel, 'existed': (root / rel).exists()} for rel in changes]}
        for rel in changes:
            path = root / rel
            if path.exists():
                dest = backup / 'files' / rel; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, dest)
        (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        for rel, data in changes.items():
            path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        report.update(applied=True, backup=str(backup))
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
