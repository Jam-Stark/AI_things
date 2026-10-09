#!/usr/bin/env python3
"""Plan or apply v1.6.0 workflow files, with reversible file backups.

Default: dry-run. No Git writes, hook-trust changes, model calls or runtime-state
resets. Init and refresh call this same plan and role renderer.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import shutil
import tempfile
import tomllib

from render_roles import render

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / 'v160-assets'
VERSION = '1.6.0'
REMOVED = (
    '.ai/SESSION_PROTOCOL.md', '.ai/scripts/session_bus.py',
    '.ai/scripts/codex_v150_hook.py', '.ai/scripts/codex_v151_hook.py',
)
CORE_DOCS = (
    'ROLE.md', 'WORKFLOW.md', 'MODEL_ROUTING.md', 'CONTEXT_POLICY.md',
    'TOOL_LIFECYCLE.md', 'MEMORY_GOVERNANCE.md', 'TEAM_STATE.md',
    'EXECUTION_TEAM.md', 'OUTSIDE_VIEW.md',
)
OPTIONAL_DOCS = ('LONG_RUNNING_TASKS.md', 'STAGE_DECISION.md', 'ARTIFACT_HANDOFF.md', 'RUNTIME_ADAPTERS.md')
PROJECT_DOCS = {'MEMORY_GOVERNANCE.md', 'TEAM_STATE.md', *OPTIONAL_DOCS}
STAGE_TEMPLATES = (
    'START_A_ROOT_zh.md', 'START_B_CHILD_zh.md',
    'OUTSIDE_VIEW_REQUEST_zh.md', 'STAGE_CONTRACT.example.json',
)


def correct_authority(text: str) -> str:
    """Correct known workflow sentences without replacing project content."""
    replacements = {
        'Main owns scope、acceptance、write/resource ownership、Git 和 final integration.':
            'Owner/Planner 确定阶段边界与验收；execution lead 在已授范围内分配写入/资源并整合。Git 和外部发布按明确授权分别处理。',
        'Main `/root` is the control plane and final integrator.':
            'The execution lead integrates the approved stage, as an independent root or a real child. Runtime identity and stage authority are separate.',
        'Main alone owns scope, acceptance, write/resource assignment, Git and external writes.':
            'Owner/Planner sets stage boundaries and acceptance. The execution lead manages delegated writes/resources and integration; Git and external writes need explicit authority.',
        'Named subagents may communicate directly with `send_message` and `followup_task`.':
            'Named agents exchange technical facts directly with `send_message`; lifecycle controls such as `followup_task` require actual creator/management authority.',
        '`send_message` / `followup_task` may carry P2P facts and bounded requests by task path.':
            '`send_message` carries P2P technical facts. `followup_task` and other lifecycle controls require actual creator/management authority.',
        '`.codex/hooks.json` is adaptive: when coordination state is inactive it permits ordinary spawns and does not create a ledger. When Main explicitly activates coordination, hooks validate only the applicable controlled contracts and record metadata.':
            'The small stage/quota state is separate from optional full coordination. Use explicit prepare/native/record to check identity, grant and role capability and bind actual results. Trusted hooks remain separately observable; full coordination stays conditional.',
        'Persist only coordination metadata after tool use. Deliver pending long-run events once and archive them after SessionStart injection.':
            'Persist real tool outcomes and retain pending long-run events until explicitly handled; SessionStart notification never archives unresolved events.',
        'Main 独占 scope、acceptance、WRITE_SET、资源、Git 和整合权；子 agent P2P 只交换技术事实。':
            'Owner/Planner 确定阶段边界与验收；execution lead 在已授范围内组织成员、分配 WRITE_SET/资源并整合结果。P2P 可直接交换技术事实；Git 权限按当前明确授权。',
        'Main 独占 scope、acceptance、WRITE_SET、资源、Git 和整合权；P2P 只交换技术事实。':
            'Owner/Planner 确定阶段边界与验收；execution lead 在已授范围内组织成员、分配 WRITE_SET/资源并整合结果。P2P 可直接交换技术事实；Git 权限按当前明确授权。',
        'Main retains write/resource/Git authority.':
            'The execution lead manages assigned writes/resources and integration under the current stage grant; Git needs explicit authorization.',
        'Main owns scope、acceptance、write/resource authority、Git、external writes and final integration.':
            'Owner/Planner sets stage scope and acceptance; the execution lead manages assigned writes/resources and integration. Git and external writes require current explicit authorization.',
        'FAST 直接完成；STANDARD 存在独立工作线、specialist context 或实质审阅/并行收益时，Main 必须主动委托最少必要 agent，不等 Owner 说“team”。更高层/runtime 不允许则直接完成。HIGH_RISK 的副作用须另有授权。':
            '普通小任务直接完成；有明确独立产出或并行价值时再委托。阶段内已批步骤连续执行；扩展范围或新增副作用需有效授权。',
        '；Owner 已授权的 Main 间阶段决策按 .ai/SESSION_PROTOCOL.md。': '。',
        '；Owner 已授权的 Main 间决策按 .ai/SESSION_PROTOCOL.md。': '。',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def entry(text: str, *, root_route: bool = True) -> str:
    """Replace the route and known obsolete authority prose, preserving facts."""
    pattern = r'<!-- JAM-V(?:150|151|160)-ROUTE-BEGIN -->.*?<!-- JAM-V(?:150|151|160)-ROUTE-END -->'
    if not root_route:
        text = re.sub(pattern + r'\n*', '', text, flags=re.S)
    else:
        block = (SKILL / 'templates/ENTRY_BLOCK.md').read_text().strip()
        if re.search(pattern, text, flags=re.S):
            text = re.sub(pattern, lambda _: block, text, count=1, flags=re.S)
        else:
            text = block + '\n\n' + text
    text = correct_authority(text)
    text = re.sub(r'^(# .*?)(?:v1\.5\.[01])$', r'\g<1>v1.6.0', text, flags=re.M)
    return text


def role_profile(root: Path, requested: str | None) -> str:
    if requested:
        return requested
    policy_file = root / '.ai/role-policy.json'
    if policy_file.exists():
        roles = json.loads(policy_file.read_text())['roles']
        if any(spec['profile'] == 'doordog' for spec in roles.values()):
            return 'doordog'
    if (root / '.codex/agents/isaaclab-worker.toml').exists():
        return 'doordog'
    return 'generic'


def plan(root: Path, profile: str | None = None) -> dict[str, bytes | None]:
    root = root.resolve()
    profile = role_profile(root, profile)
    if not (ASSETS / '.ai/scripts/codex_v160_hook.py').is_file():
        raise ValueError('v160 runtime assets are incomplete; finish source integration before installing.')
    result = {
        path.relative_to(ASSETS).as_posix(): path.read_bytes()
        for path in ASSETS.rglob('*')
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'
        and path.relative_to(ASSETS).as_posix() not in ('.codex/config.toml', '.codex/hooks.json')
        and '.codex/agents' not in path.relative_to(ASSETS).as_posix()
    }
    config = root / '.codex/config.toml'
    local_roles = list((root / '.codex/agents').glob('*.toml'))
    with tempfile.TemporaryDirectory(prefix='jam-v160-input-') as temporary:
        inputs = Path(temporary)
        (inputs / '.codex/agents').mkdir(parents=True)
        shutil.copy2(config if config.exists() else ASSETS / '.codex/config.toml', inputs / '.codex/config.toml')
        for path in local_roles or list((ASSETS / '.codex/agents').glob('*.toml')):
            shutil.copy2(path, inputs / '.codex/agents' / path.name)
        generated = render(inputs, profile=profile)
    result.update({relative: text.encode() for relative, text in generated.items()})
    generated_roles = {rel for rel in generated if rel.startswith('.codex/agents/')}
    for path in local_roles:
        relative = path.relative_to(root).as_posix()
        if relative not in generated_roles:
            result[relative] = None
    docs = (*CORE_DOCS, *(name for name in OPTIONAL_DOCS if (root / '.ai' / name).exists()))
    for name in docs:
        existing = root / '.ai' / name
        if name in PROJECT_DOCS and existing.exists():
            result['.ai/' + name] = correct_authority(existing.read_text()).encode()
            continue
        source = SKILL / 'references' / name
        if name == 'MODEL_ROUTING.md' and profile == 'doordog':
            source = SKILL / 'references/MODEL_ROUTING_DOORDOG.md'
        result['.ai/' + name] = source.read_bytes()
    for name in STAGE_TEMPLATES:
        result['.ai/templates/' + name] = (SKILL / 'templates' / name).read_bytes()
    result['.codex/TEAM.md'] = (SKILL / 'templates/CODEX_TEAM.md').read_bytes()
    for relative, template in [('AGENTS.md', 'AGENTS.md'), ('.codex/AGENTS.md', 'CODEX_AGENTS.md')]:
        path = root / relative
        text = path.read_text() if path.exists() else (SKILL / 'templates' / template).read_text()
        result[relative] = entry(text, root_route=relative == 'AGENTS.md').encode()
    for relative in REMOVED:
        result.pop(relative, None)
        if (root / relative).exists():
            result[relative] = None
    hooks_file = root / '.codex/hooks.json'
    hooks = json.loads(hooks_file.read_text()) if hooks_file.exists() else {'hooks': {}}
    known_hooks = ('codex_team_hook.py', 'codex_v150_hook.py', 'codex_v151_hook.py', 'codex_v160_hook.py')
    for event, groups in hooks['hooks'].items():
        for group in groups:
            group['hooks'] = [handler for handler in group.get('hooks', [])
                              if not any(name in handler.get('command', '') for name in known_hooks)]
        hooks['hooks'][event] = [group for group in groups if group['hooks']]
    latest = json.loads((ASSETS / '.codex/hooks.json').read_text())
    for event, groups in latest['hooks'].items():
        hooks['hooks'].setdefault(event, []).extend(groups)
    hooks['description'] = latest['description']
    result['.codex/hooks.json'] = (json.dumps(hooks, ensure_ascii=False, indent=2) + '\n').encode()
    return result


def apply_plan(root: Path, files: dict[str, bytes | None], apply: bool = False) -> dict:
    root = root.resolve()
    changed = {rel: data for rel, data in files.items()
               if ((root / rel).exists() if data is None
                   else not (root / rel).exists() or (root / rel).read_bytes() != data)}
    for relative, data in changed.items():
        if data is None:
            continue
        if relative.endswith('.py'):
            ast.parse(data, filename=relative)
        elif relative.endswith('.toml'):
            tomllib.loads(data.decode())
        elif relative.endswith('.json'):
            json.loads(data)
    report = {'version': VERSION, 'root': str(root), 'applied': False,
              'files': list(changed), 'removed': [rel for rel, data in changed.items() if data is None]}
    if not apply or not changed:
        return report
    parent = Path.home() / '.cache/jam-workflow-v160-backups'
    parent.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix=root.name + '-', dir=parent))
    manifest = {'root': str(root), 'files': []}
    for relative in changed:
        path = root / relative
        manifest['files'].append({'path': relative, 'existed': path.exists()})
        if path.exists():
            destination = backup / 'files' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for relative, data in changed.items():
        path = root / relative
        if data is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    report.update(applied=True, backup=str(backup))
    return report


def restore_backup(backup: Path, apply: bool = False) -> dict:
    backup = backup.resolve()
    manifest = json.loads((backup / 'manifest.json').read_text())
    files = {row['path']: (backup / 'files' / row['path']).read_bytes() if row['existed'] else None
             for row in manifest['files']}
    report = apply_plan(Path(manifest['root']), files, apply)
    report['restored_from'] = str(backup)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--root', type=Path)
    mode.add_argument('--restore', type=Path, metavar='BACKUP')
    parser.add_argument('--profile', choices=['generic', 'doordog'])
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.restore:
        result = restore_backup(args.restore, args.apply)
    else:
        root = args.root.resolve()
        result = apply_plan(root, plan(root, args.profile), args.apply)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
