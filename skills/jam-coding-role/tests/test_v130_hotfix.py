from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / 'scripts/codex_team_hook.py'
TEAM = ROOT / 'scripts/team_state.py'
STAGE = ROOT / 'scripts/stage_artifacts.py'
TEAM_CFG = ROOT / 'templates/TEAM_STATE.toml'
HOOKS_CFG = ROOT / 'templates/CODEX_HOOKS.json'
ART_CFG = ROOT / 'templates/ARTIFACT_SYNC.toml'


def run(*cmd: str, cwd: Path, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(cmd), cwd=cwd, input=input_text, text=True, capture_output=True, check=False)


def repo(raw: str) -> Path:
    root = Path(raw); run('git','init','-q',cwd=root); run('git','config','user.email','t@example.com',cwd=root); run('git','config','user.name','T',cwd=root)
    (root/'README.md').write_text('x\n'); run('git','add','README.md',cwd=root); run('git','commit','-qm','init',cwd=root)
    return root


class HotfixTests(unittest.TestCase):
    def hook(self, root: Path, mode: str, data: dict | str) -> subprocess.CompletedProcess[str]:
        raw = data if isinstance(data,str) else json.dumps(data)
        return run(sys.executable,str(HOOK),mode,cwd=root,input_text=raw)

    def payload(self, root: Path, event: str, tool: str | None=None) -> dict:
        data={'session_id':'s1','turn_id':'t1','cwd':str(root),'hook_event_name':event}
        if tool: data['tool_name']=tool
        return data

    def install_team(self, root: Path) -> None:
        scripts=root/'.ai/scripts'; scripts.mkdir(parents=True,exist_ok=True); shutil.copy2(TEAM,scripts/'team_state.py'); (root/'.ai/team-state.toml').write_text(TEAM_CFG.read_text())

    def test_pre_allow_is_empty(self):
        with tempfile.TemporaryDirectory() as raw:
            root=repo(raw); data=self.payload(root,'PreToolUse','spawn_agent'); data['tool_input']={'task_name':'read','agent_type':'context_researcher'}
            result=self.hook(root,'pre',data); self.assertEqual(result.returncode,0,result.stderr); self.assertEqual(result.stdout,'')

    def test_pre_deny_has_only_specific_fields(self):
        with tempfile.TemporaryDirectory() as raw:
            root=repo(raw); self.install_team(root); run(sys.executable,str(root/'.ai/scripts/team_state.py'),'activate','--mode','strict','--reason','formal',cwd=root)
            data=self.payload(root,'PreToolUse','spawn_agent'); data['tool_input']={'task_name':'writer_a','agent_type':'isaaclab_worker'}
            result=self.hook(root,'pre',data); self.assertEqual(result.returncode,0,result.stderr); out=json.loads(result.stdout); self.assertNotIn('continue',out); self.assertEqual(out['hookSpecificOutput']['permissionDecision'],'deny')

    def test_malformed_and_non_git_pre_fail_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            root=repo(raw); bad=self.hook(root,'pre','{broken'); self.assertEqual(bad.returncode,2); self.assertEqual(bad.stdout,'')
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); data=self.payload(root,'PreToolUse','spawn_agent'); data['tool_input']={}
            bad=self.hook(root,'pre',data); self.assertEqual(bad.returncode,2); self.assertIn('repository root',bad.stderr)

    def test_post_redacts_payload(self):
        with tempfile.TemporaryDirectory() as raw:
            root=repo(raw); marker=root/'.ai/runtime/team/coordination.json'; marker.parent.mkdir(parents=True); marker.write_text('{"mode":"adaptive"}\n')
            data=self.payload(root,'PostToolUse','send_message'); data.update({'tool_use_id':'c1','tool_input':{'target':'/root/w','message':'SECRET-PROMPT'},'tool_response':{'success':True,'output':'SECRET-OUTPUT'}})
            result=self.hook(root,'post',data); self.assertEqual(result.returncode,0,result.stderr); event=(root/'.ai/runtime/team/hook-events.jsonl').read_text(); self.assertNotIn('SECRET-PROMPT',event); self.assertNotIn('SECRET-OUTPUT',event); self.assertEqual(json.loads(event)['input']['target'],'/root/w')

    def test_session_start_delivers_once(self):
        with tempfile.TemporaryDirectory() as raw:
            root=repo(raw); pending=root/'.ai/runtime/pending-events'; pending.mkdir(parents=True); (pending/'r.json').write_text('{"state":"PASS","summary":"done"}')
            data=self.payload(root,'SessionStart'); first=self.hook(root,'session-start',data); self.assertIn('r.json',json.loads(first.stdout)['hookSpecificOutput']['additionalContext']); self.assertFalse((pending/'r.json').exists()); self.assertTrue(any((pending/'archive').glob('r*.json')))
            second=self.hook(root,'session-start',data); self.assertEqual(json.loads(second.stdout),{'continue':True})

    def test_hook_commands_use_git_root(self):
        cfg=json.loads(HOOKS_CFG.read_text()); commands=[h['command'] for groups in cfg['hooks'].values() for group in groups for h in group['hooks']]
        self.assertTrue(commands); self.assertTrue(all('$(git rev-parse --show-toplevel)' in x for x in commands))

    def test_team_state_is_optional_and_strict(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); inactive=run(sys.executable,str(TEAM),'status',cwd=root); self.assertEqual(inactive.stdout.strip(),'INACTIVE'); self.assertFalse((root/'.ai/runtime/team').exists())
            run(sys.executable,str(TEAM),'activate','--mode','strict','--reason','formal',cwd=root)
            denied=run(sys.executable,str(TEAM),'hook-check-spawn','--task-name','writer_a','--role','isaaclab_worker',cwd=root); self.assertEqual(denied.returncode,2); self.assertFalse(json.loads(denied.stdout)['allow'])
            created=run(sys.executable,str(TEAM),'task-create','--task-name','writer_a','--role','isaaclab_worker','--outcome','fix','--revision','r1','--write-set','x.py','--acceptance','proof',cwd=root); self.assertEqual(created.returncode,0,created.stderr)
            allowed=run(sys.executable,str(TEAM),'hook-check-spawn','--task-name','writer_a','--role','isaaclab_worker',cwd=root); self.assertTrue(json.loads(allowed.stdout)['allow'])

    def test_stage_semantic_zips_and_checkpoint_exception(self):
        with tempfile.TemporaryDirectory() as raw:
            root=repo(raw); cfg=root/'.ai/artifact-sync.toml'; cfg.parent.mkdir(parents=True); text=ART_CFG.read_text().replace('99614720','32768'); cfg.write_text(text)
            for rel,seed in [('outputs/s/resolved_config.yaml',1),('logs_eval/s/metrics.jsonl',2),('renders/s/evidence.png',3)]:
                path=root/rel; path.parent.mkdir(parents=True,exist_ok=True); rng=random.Random(seed); path.write_bytes(bytes(rng.randrange(256) for _ in range(18000)))
            cp=root/'logs_rl/s/model.pt'; cp.parent.mkdir(parents=True,exist_ok=True); cp.write_bytes(os.urandom(50000))
            out=root/'out'; result=run(sys.executable,str(STAGE),'pack','--repo',str(root),'--config',str(cfg),'--stage','s','--project','P','--worktree','W','--output',str(out),'--trigger','stage-closure','--confirm-stage-handoff','--include-checkpoints',cwd=root); self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            release=next((out/'P'/'W'/'s').iterdir()); names={x.name for x in release.glob('*.zip')}; self.assertIn('source_and_configs.zip',names); self.assertIn('logs_and_metrics.zip',names); self.assertIn('plots_and_evidence.zip',names); self.assertFalse(any('.z0' in x or '.zip.' in x for x in names)); self.assertFalse(any(x.startswith('checkpoints') for x in names))
            for path in release.glob('*.zip'): self.assertLessEqual(path.stat().st_size,32768); zipfile.ZipFile(path).testzip()
            index=(release/'BUNDLE_INDEX.md').read_text(); self.assertIn('model.pt',index); self.assertIn('rclone',index); self.assertNotIn('SHA-256',index)


if __name__ == '__main__': unittest.main()
