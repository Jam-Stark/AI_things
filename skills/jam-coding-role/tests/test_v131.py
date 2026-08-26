from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pro_review_handoff.py"
TEMPLATE = ROOT / "templates" / "PRO_REVIEW_PROMPT.md"


class V132Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.remote = self.base / "remote.git"
        self.repo = self.base / "repo"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, check=True)
        subprocess.run(["git", "remote", "add", "origin", str(self.remote)], cwd=self.repo, check=True)
        (self.repo / "README.md").write_text("test\n", encoding="utf-8")
        (self.repo / ".ai").mkdir()
        (self.repo / ".ai/artifact-sync.toml").write_text(
            '[pro_review]\nlocal_review_root = "scriptsFORhuman/pro_reviews"\n',
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "README.md", ".ai/artifact-sync.toml"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.repo, check=True)
        subprocess.run(["git", "branch", "-M", "review"], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-qu", "origin", "review"], cwd=self.repo, check=True)
        self.release = self.base / "release_20260826"
        self.release.mkdir()
        with zipfile.ZipFile(self.release / "worker_delivery__logs_and_metrics.zip", "w") as archive:
            archive.writestr("metrics.json", "{}")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_helper(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo",
                str(self.repo),
                "--release-dir",
                str(self.release),
                "--drive-location",
                "Pro_Space/Test/review/stage/release/",
                "--template",
                str(TEMPLATE),
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_prompt_contains_published_git_owner_transfer_and_local_destination(self) -> None:
        result = self.run_helper(
            "--review-type",
            "阶段验收",
            "--owner-request",
            "核查本轮结果",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.release / "PRO_REVIEW_PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("分支：`review`", text)
        self.assertIn("worker_delivery__logs_and_metrics.zip", text)
        self.assertIn("pro_delivery__full_review.zip", text)
        self.assertIn("FULL_REVIEW.md", text)
        self.assertIn("LOCAL_WORKER_PARSE_PROMPT.md", text)
        self.assertIn("精简版", text)
        self.assertIn("全量版", text)
        self.assertIn("One more thing", text)
        self.assertIn("Owner 在当前本地 Worker 对话中上传", text)
        self.assertIn("不要去 Google Drive 寻找 Pro 交付包", text)
        self.assertIn("scriptsFORhuman/pro_reviews/release_20260826/", text)
        self.assertIn("不得自动升级为本地硬门槛", text)
        self.assertIn("NOT_ATTACHED", text)
        self.assertNotIn("把它上传到 Google Drive", text.replace("不要把它上传到 Google Drive", ""))

    def test_missing_review_type_keeps_owner_placeholder(self) -> None:
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.release / "PRO_REVIEW_PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("[OWNER:", text)

    def test_unpushed_commit_is_rejected(self) -> None:
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "local only"], cwd=self.repo, check=True)
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not the verified pushed commit", result.stderr)

    def test_limit_is_compressed_zip_file_size(self) -> None:
        oversized = self.release / "worker_delivery__plots_and_evidence.zip"
        with oversized.open("wb") as handle:
            handle.truncate(95 * 1024 * 1024 + 1)
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("compressed ZIP exceeds 95 MiB", result.stderr)

    def test_existing_pro_zip_is_not_listed_as_worker_input(self) -> None:
        with zipfile.ZipFile(self.release / "pro_delivery__full_review.zip", "w") as archive:
            archive.writestr("FULL_REVIEW.md", "old")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.release / "PRO_REVIEW_PROMPT.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("compressed bytes"), 1)
        self.assertIn("worker_delivery__logs_and_metrics.zip", text)

    def test_custom_pro_filename_must_keep_pro_prefix(self) -> None:
        result = self.run_helper("--pro-delivery-zip", "answer.zip")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pro_delivery__", result.stderr)

    def test_invalid_pro_doc_root_is_rejected(self) -> None:
        result = self.run_helper("--pro-doc-root", "../outside")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("repository-relative", result.stderr)

    def test_templates_require_proactive_delegation_and_owner_transfer(self) -> None:
        agents = (ROOT / "templates" / "AGENTS.md").read_text(encoding="utf-8")
        workflow = (ROOT / "references" / "WORKFLOW.md").read_text(encoding="utf-8")
        team = (ROOT / "templates" / "CODEX_TEAM.md").read_text(encoding="utf-8")
        project = (ROOT / "templates" / "PROJECT.md").read_text(encoding="utf-8")
        handoff = (ROOT / "references" / "ARTIFACT_HANDOFF.md").read_text(encoding="utf-8")
        config = (ROOT / "templates" / "ARTIFACT_SYNC.toml").read_text(encoding="utf-8")
        self.assertIn("Mandatory delegation gate", agents)
        self.assertIn("must immediately spawn", agents)
        self.assertIn("NO_DELEGATION_REASON", agents)
        self.assertIn("Before deep work", workflow)
        self.assertIn("Do not wait for the user", team)
        self.assertIn("Environment and command registry", project)
        self.assertIn("Pro review document root", project)
        self.assertIn("cloud Pro does **not** upload", handoff)
        self.assertIn('delivery_mode = "owner-chat-transfer"', config)
        self.assertIn('local_review_root = "docs/pro-reviews"', config)


if __name__ == "__main__":
    unittest.main()
