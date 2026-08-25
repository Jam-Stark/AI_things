#!/usr/bin/env python3
"""Verify a Git-published stage release and generate the cloud Pro prompt."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

MIB = 1024 * 1024
MAX_ZIP_BYTES = 95 * MIB
OWNER_PLACEHOLDER = "[OWNER: 请填写诊断问题/阶段验收/事实核查/QA等需求类型]"
REQUEST_PLACEHOLDER = "[OWNER: 请填写本轮具体问题、前置回答要求和验收范围]"


def run(root: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if check and completed.returncode != 0:
        raise SystemExit((completed.stderr or completed.stdout).strip())
    return completed.stdout.strip()


def git_root(start: Path) -> Path:
    return Path(run(start.expanduser().resolve(), "rev-parse", "--show-toplevel")).resolve()


def normalize_remote(url: str) -> str:
    value = url.strip()
    match = re.fullmatch(r"git@github\.com:([^/]+/[^/]+?)(?:\.git)?", value)
    if match:
        return f"https://github.com/{match.group(1)}"
    if value.startswith("https://github.com/"):
        return value[:-4] if value.endswith(".git") else value
    return value


def verify_git_publish(root: Path, remote: str, branch: str | None) -> tuple[str, str, str]:
    dirty = run(root, "status", "--porcelain", "--untracked-files=no")
    if dirty:
        raise SystemExit("tracked Git changes remain; commit the in-scope handoff changes before cloud review")
    current = branch or run(root, "branch", "--show-current")
    if not current:
        raise SystemExit("detached HEAD; specify a published review branch")
    head = run(root, "rev-parse", "HEAD")
    remote_ref = f"refs/remotes/{remote}/{current}"
    remote_head = run(root, "rev-parse", remote_ref, check=False)
    if not remote_head:
        raise SystemExit(
            f"missing local remote-tracking ref {remote}/{current}; run git push -u {remote} HEAD:{current}"
        )
    if remote_head != head:
        raise SystemExit(
            f"local HEAD {head} is not the verified pushed commit {remote_head}; push and verify before handoff"
        )
    return normalize_remote(run(root, "remote", "get-url", remote)), current, head


def zip_lines(release: Path) -> list[str]:
    archives = sorted(path for path in release.glob("*.zip") if path.is_file())
    if not archives:
        raise SystemExit(f"no ZIP packages found in {release}")
    lines: list[str] = []
    for path in archives:
        size = path.stat().st_size
        if size > MAX_ZIP_BYTES:
            raise SystemExit(
                f"compressed ZIP exceeds 95 MiB: {path.name} ({size} bytes); split semantically first"
            )
        lines.append(f"  - `{path.name}` ({size} compressed bytes)")
    return lines


def render(
    template: str,
    *,
    repo_url: str,
    branch: str,
    commit: str,
    drive_location: str,
    zip_list: list[str],
    review_type: str | None,
    owner_request: str | None,
) -> str:
    replacements = {
        "{{REPO_URL}}": repo_url,
        "{{BRANCH}}": branch,
        "{{COMMIT_SHA}}": commit,
        "{{DRIVE_LOCATION}}": drive_location,
        "{{ZIP_LIST}}": "\n".join(zip_list),
        "{{REVIEW_TYPE}}": review_type.strip() if review_type and review_type.strip() else OWNER_PLACEHOLDER,
        "{{OWNER_REQUEST}}": owner_request.strip() if owner_request and owner_request.strip() else REQUEST_PLACEHOLDER,
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--repo", type=Path, default=Path.cwd())
    root.add_argument("--release-dir", type=Path, required=True)
    root.add_argument("--drive-location", required=True)
    root.add_argument("--review-type")
    root.add_argument("--owner-request")
    root.add_argument("--remote", default="origin")
    root.add_argument("--branch")
    root.add_argument("--template", type=Path)
    root.add_argument("--output", type=Path)
    return root


def main() -> int:
    args = parser().parse_args()
    root = git_root(args.repo)
    release = args.release_dir.expanduser().resolve()
    if not release.is_dir():
        raise SystemExit(f"release directory not found: {release}")
    repo_url, branch, commit = verify_git_publish(root, args.remote, args.branch)
    template_path = args.template
    if template_path is None:
        installed = root / ".ai/PRO_REVIEW_PROMPT.md"
        if installed.is_file():
            template_path = installed
        else:
            template_path = Path(__file__).resolve().parents[1] / "templates/PRO_REVIEW_PROMPT.md"
    if not template_path.is_file():
        raise SystemExit(f"prompt template not found: {template_path}")
    output = args.output.expanduser().resolve() if args.output else release / "PRO_REVIEW_PROMPT.md"
    output.write_text(
        render(
            template_path.read_text(encoding="utf-8"),
            repo_url=repo_url,
            branch=branch,
            commit=commit,
            drive_location=args.drive_location,
            zip_list=zip_lines(release),
            review_type=args.review_type,
            owner_request=args.owner_request,
        ),
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
