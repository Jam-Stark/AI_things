from __future__ import annotations

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

    def test_scientific_init_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            init = self.run_cli(
                "init",
                str(target),
                "--profile",
                "scientific",
                "--runtime",
                "codex",
                "--runtime",
                "omo",
                "--runtime",
                "claude",
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            self.assertTrue((target / ".ai/ROLE.md").is_file())
            self.assertTrue((target / ".ai/SCIENTIFIC_ENGINEERING.md").is_file())
            self.assertTrue((target / ".codex/AGENTS.md").is_file())
            self.assertTrue((target / ".omo/AGENTS.md").is_file())
            self.assertTrue((target / "CLAUDE.md").is_file())

            audit = self.run_cli(
                "audit",
                str(target),
                "--profile",
                "scientific",
                "--runtime",
                "codex",
                "--runtime",
                "omo",
                "--runtime",
                "claude",
            )
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)
            self.assertIn("PASS:", audit.stdout)

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


if __name__ == "__main__":
    unittest.main()
