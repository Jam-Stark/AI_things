#!/usr/bin/env python3
"""Generate Jam Coding Role configurations from the shared role policy.

Init, refresh and migration use the same renderer. Generation does not install
hooks, call Codex, change runtime state or change Main's App-owned model/effort.
"""
from __future__ import annotations

import argparse
import ast
import copy
import datetime
import json
from pathlib import Path
import re
import sys
import tomllib
from typing import Any

HERE = Path(__file__).resolve().parent
SPECIALIST = '''[V1.6.0 SPECIALIST]
完成分配给你的独立产出，遵守当前子授权的写入、资源和完成条件。与依赖方直接交换技术事实；把影响阶段结论的问题交 execution lead，不让 Planner 中转普通依赖。转派仅在角色能力与子授权均允许时使用，不能扩出新预算或新权限。控制其他 agent 需要真实归属或明确移交。不要擅自提交、推送、发布或改科学比较。
'''
OLD_GUARDS = (
    '''[V1.5.0 CHILD GUARD]
No child spawning, model/effort override, Git, external authority changes or full-history fork. Report to your Main, not the other team. Stop at your assigned boundary. Return exact evidence and unresolved claims; never run a model polling loop. These guards supersede older model/effort wording above. The deep_researcher is the sole Astra/medium identity per team and is reserved for the hardest mathematical/causal/complex question, not routine review.
''',
    '''[V1.5.1 CHILD GUARD]
You are a spawned child, not the independent root Main. No descendant spawning,
Git operations, new external authority, unassigned writes or full-history fork.
Stay within the original role's assigned scope and return exact evidence to your
Main. An effort variant changes reasoning effort, never authority or acceptance.
Never hire a model to poll logs. Preserve existing long-run ownership. Only the
single deep_researcher identity may use Astra, at medium. Do not cycle identities.
''',
)
OLD_COMMON = 'Stay within the assigned authority. Use .ai/LONG_RUNNING_TASKS.md for durable waits; never hire a model to poll. Return a bounded result, evidence and unresolved claims.'
OLD_CONTEXT = '''[V1.5.1 CONTEXT SCOPE]
Integrate the assigned cross-file question with precise evidence and bounded implications. Keep facts separate from hypotheses. Do not expand scope, redesign architecture or edit files.'''


def migrate_instructions(text: str, base: str) -> str:
    """Replace known workflow prose while retaining specialist/local content."""
    for known in (*OLD_GUARDS, SPECIALIST):
        marker = known.splitlines()[0]
        if marker in text:
            if text.count(marker) != 1 or known.rstrip() not in text:
                raise ValueError('Locally modified managed role paragraph requires explicit merge: ' + base)
            text = text.replace(known.rstrip(), '', 1)
    text = text.replace(OLD_COMMON, '')
    text = text.replace(OLD_CONTEXT, '')
    replacements = {
        'Main owns integration/authority. ': '',
        'the responsible worker and Main.': 'the responsible worker and execution lead.',
        'ask Main for a bounded additional fact': 'ask the assigning lead for a bounded additional fact',
        'Require Main to supply evidence': 'Require the assigning lead to supply evidence',
        'Escalate an unresolved semantic decision to Main': 'Escalate an unresolved semantic decision to the execution lead',
        'High effort is authorized for this bounded role; no obsolete Ultra approval ritual. ': 'Use the sole deep_researcher identity at its registered Astra/medium setting. ',
        'gpt-6-sol': 'gpt-6.1-sol',
        'GPT-6 Sol': 'GPT-6.1 Sol',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if base not in ('execution_lead', 'outside_view'):
        text += '\n\n' + SPECIALIST.rstrip()
    return text + '\n'


def toml_text(data: dict[str, Any]) -> str:
    def atom(value: Any) -> str:
        if isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, (int, float)):
            return repr(value)
        if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
            return value.isoformat()
        if isinstance(value, list):
            return '[' + ', '.join(atom(v) for v in value) + ']'
        if isinstance(value, dict):
            return '{' + ', '.join(json.dumps(k) + '=' + atom(v) for k, v in value.items()) + '}'
        raise ValueError(f'Unsupported TOML value: {type(value).__name__}')
    lines = ['# Generated Jam Coding Role v1.6.0.']
    def table(obj: dict, prefix: list[str]) -> None:
        if prefix:
            lines.extend(['', '[' + '.'.join(json.dumps(k) for k in prefix) + ']'])
        for key, value in obj.items():
            if not isinstance(value, dict):
                lines.append(json.dumps(key) + ' = ' + atom(value))
        for key, value in obj.items():
            if isinstance(value, dict):
                table(value, prefix + [key])
    table(data, [])
    return '\n'.join(lines) + '\n'


def read_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding='utf-8'))


def render(source: Path, profile: str = 'generic', template: bool = False) -> dict[str, str]:
    source = source.resolve()
    if profile not in ('generic', 'doordog'):
        raise ValueError('Unknown profile.')
    if template and profile != 'generic':
        raise ValueError('--template is only for a generic portable template.')
    policy = json.loads((HERE / 'role-policy.json').read_text())
    targets = {k: v for k, v in policy['roles'].items()
               if profile == 'doordog' or v['profile'] == 'generic'}
    previous: dict[str, dict] = {}
    for path in sorted((source / '.codex/agents').glob('*.toml')):
        obj = read_toml(path)
        name = obj.get('name')
        if not isinstance(name, str) or name in previous:
            raise ValueError(f'Missing or duplicate role name in {path}')
        previous[name] = obj
    known = {base if effort == spec['default_effort'] else base + '__' + effort
             for base, spec in targets.items() for effort in spec['allowed_efforts']}
    if set(previous) - known:
        raise ValueError('Custom roles require an explicit merge: ' + ', '.join(sorted(set(previous) - known)))
    missing = {base for base, spec in targets.items()
               if base not in previous and 'developer_instructions' not in spec}
    if missing:
        raise ValueError('Missing original role instructions: ' + ', '.join(sorted(missing)))

    if template:
        cfg = {'background_terminal_max_timeout': 86400000,
               'features': {'hooks': True}, 'agents': {}}
    else:
        cfg = read_toml(source / '.codex/config.toml')
        for layer in [cfg, *cfg.get('profiles', {}).values()]:
            if 'model' in layer or 'model_reasoning_effort' in layer:
                raise ValueError('Project Main model/effort override found; explicit merge is required.')
    agents = cfg.setdefault('agents', {})
    unknown_entries = [k for k, v in agents.items() if isinstance(v, dict) and k not in known]
    if unknown_entries:
        raise ValueError('Custom role registrations require an explicit merge: ' + ', '.join(unknown_entries))
    for name in known:
        agents.pop(name, None)
    agents.pop('max_threads', None)
    agents.update(enabled=True, max_concurrent_threads_per_session=policy['max_active_children'],
                  default_subagent_model=targets['default']['model'],
                  default_subagent_reasoning_effort=targets['default']['default_effort'])
    cfg.setdefault('features', {})['hooks'] = True
    generated: dict[str, str] = {}
    allowlist: dict[str, tuple[str, str]] = {}
    base_roles: dict[str, str] = {}
    can_spawn: dict[str, bool] = {}
    variants: dict[str, dict[str, str]] = {}
    for base, spec in targets.items():
        seed = previous.get(base) or {
            'description': spec['description'],
            'developer_instructions': spec['developer_instructions'],
            'sandbox_mode': spec['sandbox_mode'],
            'background_terminal_max_timeout': 86400000,
        }
        variants[base] = {}
        for effort in spec['allowed_efforts']:
            name = base if effort == spec['default_effort'] else base + '__' + effort
            obj = copy.deepcopy(previous.get(name, seed))
            original = obj.get('developer_instructions')
            if not isinstance(original, str) or not original.strip():
                raise ValueError(f'No instructions for {name}; explicit merge is required.')
            if template and re.search(r'DoorDog|IsaacLab|PiPER|/(?:home|Users)/[^/\s]+/', original, flags=re.I):
                raise ValueError('Portable templates require generic role instructions.')
            obj['developer_instructions'] = migrate_instructions(original, base)
            obj.update(name=name, model=spec['model'], model_reasoning_effort=effort,
                       model_context_window=spec['window'],
                       model_auto_compact_token_limit=spec['compact'],
                       model_auto_compact_token_limit_scope='total')
            desc = re.sub(r' \[(low|medium|high|xhigh|max); same [^\]]+ scope\]$', '', obj.get('description', base))
            obj['description'] = str(desc) + f' [{effort}; same {base} scope]'
            capability = spec['can_spawn']
            obj.setdefault('agents', {})['enabled'] = capability
            obj['agents'].pop('max_threads', None)
            if capability:
                obj['agents']['max_concurrent_threads_per_session'] = policy['max_active_children']
            else:
                obj['agents'].pop('max_concurrent_threads_per_session', None)
            obj.setdefault('features', {}).setdefault('context_management', {})['experimental_mode'] = base == 'deep_researcher'
            obj['features'].get('token_budget', {}).pop('use_history_notes_extension', None)
            if base == 'deep_researcher' and (spec['model'], effort) != ('gpt-6-astra', 'medium'):
                raise ValueError('Astra identity/effort invariant failed.')
            rel = '.codex/agents/' + name.replace('_', '-') + '.toml'
            generated[rel] = toml_text(obj)
            allowlist[name] = (spec['model'], effort)
            base_roles[name] = base
            can_spawn[name] = capability
            variants[base][effort] = name
            agents[name] = {'description': obj['description'], 'config_file': rel[len('.codex/'): ]}
    generated['.codex/config.toml'] = toml_text(cfg)
    generated['.ai/scripts/generated_role_policy.py'] = (
        '# Generated from role-policy.json; do not hand edit.\n'
        + 'POLICY = ' + repr(allowlist) + '\n'
        + 'BASE_ROLE = ' + repr(base_roles) + '\n'
        + 'CAN_SPAWN = ' + repr(can_spawn) + '\n'
        + 'ROLE_VARIANTS = ' + repr(variants) + '\n'
        + 'ROLE_BUDGETS = ' + repr({name: (targets[base]['window'], targets[base]['compact']) for name, base in base_roles.items()}) + '\n'
        + 'MAX_ACTIVE = ' + repr(policy['max_active_children']) + '\n'
        + 'STAGE_DEFAULTS = ' + repr(policy['stage_defaults']) + '\n')
    generated['.ai/ROLE_VARIANTS.json'] = json.dumps(variants, ensure_ascii=False, indent=2) + '\n'
    installed_policy = copy.deepcopy(policy)
    installed_policy['roles'] = targets
    generated['.ai/role-policy.json'] = json.dumps(installed_policy, ensure_ascii=False, indent=2) + '\n'
    for rel in ('.ai/ROLE_VERSION', '.codex/MODEL_TEAM_VERSION'):
        generated[rel] = policy['version'] + '\n'
    for rel, content in generated.items():
        if rel.endswith('.toml'):
            tomllib.loads(content)
        if rel.endswith('.py'):
            ast.parse(content)
    return generated


def compile_roles(source: Path, output: Path, profile: str = 'generic', template: bool = False) -> dict:
    source, output = source.resolve(), output.resolve()
    if output.exists() or output == source or source in output.parents:
        raise ValueError('Output must be a NEW directory outside the source project.')
    generated = render(source, profile, template)
    output.mkdir(mode=0o700, parents=True)
    for rel, content in generated.items():
        path = output / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    variants = json.loads(generated['.ai/ROLE_VARIANTS.json'])
    report = {'version': '1.6.0', 'source': str(source), 'staging': str(output),
              'profile': profile, 'portable_template': template,
              'semantic_roles': len(variants),
              'registered_configurations': sum(len(v) for v in variants.values()),
              'source_modified': False, 'native_config_verified': False}
    (output / 'GENERATION_REPORT.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profile', choices=['generic', 'doordog'], default='generic')
    parser.add_argument('--template', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(compile_roles(args.source_root, args.output, args.profile, args.template), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
