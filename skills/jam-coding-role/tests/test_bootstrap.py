from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap.py"


class BootstrapTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_minimal_init_is_lean(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            result = self.run_cli("init", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            for path in (
                ".ai/ROLE.md",
                ".ai/WORKFLOW.md",
                ".ai/MEMORY_GOVERNANCE.md",
                ".ai/ROLE_VERSION",
                ".ai/PROJECT.md",
                "AGENTS.md",
            ):
                self.assertTrue((target / path).is_file(), path)
            for absent in (
                "MEMORY.md",
                ".ai/TEAM_STATE.md",
                ".ai/LONG_RUNNING_TASKS.md",
                ".ai/ARTIFACT_HANDOFF.md",
                ".ai/runtime/team",
                ".codex/hooks.json",
            ):
                self.assertFalse((target / absent).exists(), absent)
            audit = self.run_cli("audit", str(target))
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)

    def test_full_facilities_are_explicit_and_lazy_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            common = (
                "--profile", "scientific",
                "--runtime", "codex",
                "--runtime", "omo",
                "--runtime", "claude",
                "--memory",
                "--codex-coordination-state",
                "--long-run-supervisor",
                "--omo-team-mode",
                "--stage-workflow",
                "--artifact-sync",
            )
            init = self.run_cli("init", str(target), *common)
            self.assertEqual(init.returncode, 0, init.stderr)
            for path in (
                "MEMORY.md",
                ".ai/RUNTIME_ADAPTERS.md",
                ".ai/SCIENTIFIC_ENGINEERING.md",
                ".ai/TEAM_STATE.md",
                ".ai/team-state.toml",
                ".ai/scripts/team_state.py",
                ".ai/scripts/codex_team_hook.py",
                ".codex/hooks.json",
                ".ai/LONG_RUNNING_TASKS.md",
                ".ai/scripts/run_supervisor.py",
                ".ai/STAGE_DECISION.md",
                ".ai/ARTIFACT_HANDOFF.md",
                ".ai/artifact-sync.toml",
                ".ai/artifact-targets.toml",
                ".ai/scripts/stage_artifacts.py",
                ".codex/TEAM.md",
                ".omo/omo.jsonc",
                "opencode.json",
                "CLAUDE.md",
                ".claude/settings.json",
            ):
                self.assertTrue((target / path).is_file(), path)

            self.assertFalse((target / ".ai/runtime/team").exists())
            settings = json.loads((target / ".claude/settings.json").read_text())
            self.assertIn("Agent", settings["permissions"]["deny"])
            self.assertTrue(settings["disableAgentView"])

            instructions = json.loads((target / "opencode.json").read_text())["instructions"]
            self.assertIn(".ai/RUNTIME_ADAPTERS.md", instructions)
            for optional in (
                ".ai/SCIENTIFIC_ENGINEERING.md",
                ".ai/TEAM_STATE.md",
                ".ai/MEMORY_GOVERNANCE.md",
                ".ai/LONG_RUNNING_TASKS.md",
                ".ai/STAGE_DECISION.md",
                ".ai/ARTIFACT_HANDOFF.md",
            ):
                self.assertNotIn(optional, instructions)

            omo = json.loads((target / ".omo/omo.jsonc").read_text())
            self.assertTrue(omo["team_mode"]["enabled"])

            hooks = json.loads((target / ".codex/hooks.json").read_text())
            commands = [
                handler["command"]
                for groups in hooks["hooks"].values()
                for group in groups
                for handler in group["hooks"]
                if handler.get("type") == "command"
            ]
            self.assertTrue(commands)
            self.assertTrue(
                all("git rev-parse --show-toplevel" in command for command in commands)
            )

            import tomllib
            with (target / ".ai/artifact-sync.toml").open("rb") as handle:
                artifact_sync = tomllib.load(handle)
            self.assertEqual(
                artifact_sync["packaging"]["max_single_zip_bytes"],
                95 * 1024 * 1024,
            )
            self.assertFalse(artifact_sync["packaging"]["split_volume_archives"])

            audit = self.run_cli("audit", str(target), *common)
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)
            self.assertIn("lazy-routed", audit.stdout)

    def test_init_does_not_overwrite_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            agents = target / "AGENTS.md"
            agents.write_text("project-owned\n", encoding="utf-8")
            result = self.run_cli("init", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(agents.read_text(encoding="utf-8"), "project-owned\n")
            self.assertIn("SKIPPED EXISTING: AGENTS.md", result.stdout)

    def test_refresh_refuses_unmanaged_core(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            (target / ".ai").mkdir()
            role = target / ".ai/ROLE.md"
            role.write_text("project-owned\n", encoding="utf-8")
            result = self.run_cli("refresh", str(target))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(role.read_text(encoding="utf-8"), "project-owned\n")
            self.assertIn("REFUSED UNMANAGED FILE: .ai/ROLE.md", result.stderr)

    def test_runtime_specific_flags_require_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            omo = self.run_cli("init", raw, "--omo-team-mode")
            self.assertNotEqual(omo.returncode, 0)
            self.assertIn("requires --runtime omo", omo.stderr)
            codex = self.run_cli("init", raw, "--codex-coordination-state")
            self.assertNotEqual(codex.returncode, 0)
            self.assertIn("requires --runtime codex", codex.stderr)


if __name__ == "__main__":
    unittest.main()
