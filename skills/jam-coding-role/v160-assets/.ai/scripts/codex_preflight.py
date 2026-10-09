#!/usr/bin/env python3
"""Static v1.6.0 configuration check; effective host behavior requires separate evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import tomllib
from generated_role_policy import POLICY, BASE_ROLE, CAN_SPAWN, ROLE_BUDGETS, MAX_ACTIVE, STAGE_DEFAULTS
from workflow_state import role_config


def extensions(value, path=''):
    issues=[]
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'use_history_notes_extension': issues.append('Pinned extension: '+path+'.'+key)
            issues.extend(extensions(child, path+'.'+key))
    elif isinstance(value,list):
        for child in value: issues.extend(extensions(child,path))
    return issues


def schema_issues(schema):
    def resolve(node):
        while '$ref' in node:
            ref=node['$ref']
            if not ref.startswith('#/'): raise ValueError('External schema reference is not supported.')
            node=schema
            for part in ref[2:].split('/'): node=node[part]
        return node
    def values(node):
        node=resolve(node)
        result=set(node.get('enum',[]))
        for option in node.get('anyOf',[])+node.get('oneOf',[]): result.update(values(option))
        return result
    props=schema.get('properties',{})
    agents=resolve(props.get('agents',{})).get('properties',{})
    required={'enabled','max_concurrent_threads_per_session','default_subagent_model','default_subagent_reasoning_effort'}
    issues=['Schema lacks agents.'+key for key in sorted(required-set(agents))]
    expected={effort for _,effort in POLICY.values()}
    for path,node in [('model_reasoning_effort',props.get('model_reasoning_effort',{})),('agents.default_subagent_reasoning_effort',agents.get('default_subagent_reasoning_effort',{}))]:
        missing=expected-values(node)
        if missing: issues.append('Schema '+path+' lacks efforts: '+', '.join(sorted(missing)))
    return issues


def audit(root: Path, schema: Path | None = None):
    issues=[]; roles=[]
    try:
        cfg=tomllib.loads((root/'.codex/config.toml').read_text())
        source_policy=json.loads((root/'.ai/role-policy.json').read_text())
        expected={}
        for base,spec in source_policy['roles'].items():
            for effort in spec['allowed_efforts']:
                name=base if effort==spec['default_effort'] else base+'__'+effort
                expected[name]=(base,spec['model'],effort,spec['can_spawn'],(spec['window'],spec['compact']))
        actual={name:(BASE_ROLE[name],*values,CAN_SPAWN[name],ROLE_BUDGETS[name]) for name,values in POLICY.items()}
        if actual!=expected: issues.append('Generated role policy differs from role-policy.json.')
        if source_policy['version']!='1.6.0': issues.append('Wrong role policy version.')
        if source_policy['max_active_children']!=MAX_ACTIVE or source_policy['stage_defaults']!=STAGE_DEFAULTS:
            issues.append('Generated team defaults differ from role-policy.json.')
        for label,layer in [('project',cfg),*cfg.get('profiles',{}).items()]:
            for key in ('model','model_reasoning_effort'):
                if key in layer: issues.append('Main override: '+label+'.'+key)
        issues.extend(extensions(cfg))
        agents=cfg.get('agents',{})
        for key,value in [('enabled',True),('max_concurrent_threads_per_session',MAX_ACTIVE),('default_subagent_model',POLICY['default'][0]),('default_subagent_reasoning_effort',POLICY['default'][1])]:
            if agents.get(key)!=value: issues.append('Unexpected agents.'+key)
        if cfg.get('features',{}).get('hooks') is not True: issues.append('Hooks feature is not enabled.')
        registered={name for name,value in agents.items() if isinstance(value,dict)}
        if registered!=set(POLICY): issues.append('Role registrations differ from generated policy.')
        found=set(); astra=[]
        for path in sorted((root/'.codex/agents').glob('*.toml')):
            role=tomllib.loads(path.read_text()); name=role.get('name')
            if name in found: issues.append('Duplicate role: '+str(name))
            found.add(name)
            try: role_config(root,name)
            except ValueError as exc: issues.append(str(exc))
            if agents.get(name,{}).get('config_file')!='agents/'+path.name: issues.append('Wrong role path: '+str(name))
            if role.get('model')=='gpt-6-astra': astra.append(name)
            if BASE_ROLE.get(name)=='outside_view' and role.get('sandbox_mode')!='read-only': issues.append('Outside view must be read-only.')
            if role.get('agents',{}).get('enabled') is not CAN_SPAWN.get(name): issues.append('Unexpected spawn capability: '+str(name))
            issues.extend(extensions(role,path.name))
            roles.append({'name':name,'model':role.get('model'),'effort':role.get('model_reasoning_effort')})
        if found!=set(POLICY): issues.append('Role files differ from generated policy.')
        if astra!=['deep_researcher']: issues.append('Only one deep_researcher/Astra role is permitted.')
        hooks=json.loads((root/'.codex/hooks.json').read_text()).get('hooks',{})
        for event in ('PreToolUse','PostToolUse','SessionStart','PostCompact'):
            groups=[g for g in hooks.get(event,[]) if any('codex_v160_hook.py' in h.get('command','') for h in g.get('hooks',[]))]
            if not groups: issues.append('Missing hook: '+event)
            if event=='PreToolUse':
                for tool in ('spawn_agent','resume_agent','close_agent','send_message','followup_task','interrupt_agent'):
                    if not any(re.search(g.get('matcher','.*'),'collaboration.'+tool) for g in groups): issues.append('Missing control hook: '+tool)
        post_groups=[g for g in hooks.get('PostToolUse',[]) if any('codex_v160_hook.py' in h.get('command','') for h in g.get('hooks',[]))]
        if not any(re.search(g.get('matcher','.*'),'agents.list_agents') for g in post_groups): issues.append('Missing terminal receipt hook: list_agents')
        for rel in ('.ai/ROLE_VERSION','.codex/MODEL_TEAM_VERSION'):
            if (root/rel).read_text().strip()!='1.6.0': issues.append('Wrong version: '+rel)
        if schema: issues.extend(schema_issues(json.loads(schema.read_text())))
    except (OSError,ValueError,TypeError,KeyError) as exc: issues.append(str(exc))
    return {'project_config':'STATIC_PASS' if not issues else 'FAIL','issues':issues,'roles':roles,
            'native_hook_interception':'UNVERIFIED','effective_child_config':'UNVERIFIED','billing_hard_cap':'NOT_PROVIDED'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--schema',type=Path);p.add_argument('--probe-version',action='store_true');a=p.parse_args()
    result=audit(a.root.resolve(),a.schema)
    if a.probe_version:
        r=subprocess.run(['codex','--version'],capture_output=True,text=True,timeout=5);result['codex_version']={'exit':r.returncode,'stdout':r.stdout.strip()}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if not result['issues'] else 2
if __name__=='__main__':raise SystemExit(main())
