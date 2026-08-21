#!/usr/bin/env python3
"""Safely bootstrap, refresh, or audit the Jam Coding Role."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
MARKER = "<!-- managed-by: jam-coding-role;"


def specs(profile: str, runtimes: list[str]) -> dict[Path, tuple[Path | None, bool]]:
    files: dict[Path, tuple[Path | None, bool]] = {
        Path(".ai/ROLE.md"): (ROOT / "references/ROLE.md", True),
        Path(".ai/WORKFLOW.md"): (ROOT / "references/WORKFLOW.md", True),
        Path(".ai/ROLE_VERSION"): (None, True),
        Path("AGENTS.md"): (ROOT / "templates/AGENTS.md", False),
        Path(".ai/PROJECT.md"): (ROOT / "templates/PROJECT.md", False),
        Path("MEMORY.md"): (ROOT / "templates/MEMORY.md", False),
    }
    if profile == "scientific":
        files[Path(".ai/SCIENTIFIC_ENGINEERING.md")] = (
            ROOT / "references/SCIENTIFIC_ENGINEERING.md",
            True,
        )
    if "codex" in runtimes:
        files[Path(".codex/AGENTS.md")] = (
            ROOT / "templates/CODEX_AGENTS.md",
            False,
        )
    if "omo" in runtimes:
        files[Path(".omo/AGENTS.md")] = (
            ROOT / "templates/OMO_AGENTS.md",
            False,
        )
    if "claude" in runtimes:
        files[Path("CLAUDE.md")] = (
            ROOT / "templates/CLAUDE.md",
            False,
        )
    return files


def content(source: Path | None, destination: Path) -> str:
    if destination == Path(".ai/ROLE_VERSION"):
        return f"{VERSION}\n"
    if source is None:
        raise ValueError(f"No source for {destination}")
    return source.read_text(encoding="utf-8")


def target_dir(raw: Path) -> Path:
    target = raw.expanduser().resolve()
    if not target.is_dir():
        raise SystemExit(f"Target is not a directory: {target}")
    return target


def write(path: Path, text: str, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def init(
    target: Path,
    files: dict[Path, tuple[Path | None, bool]],
    dry: bool,
) -> int:
    for destination, (source, _) in files.items():
        path = target / destination
        if path.exists():
            print(f"SKIPPED EXISTING: {destination}")
            continue
        write(path, content(source, destination), dry)
        print(f"{'WOULD CREATE' if dry else 'CREATED'}: {destination}")
    print("\nFill .ai/PROJECT.md from real code/config paths, then run audit.")
    return 0


def refresh(
    target: Path,
    files: dict[Path, tuple[Path | None, bool]],
    dry: bool,
) -> int:
    conflicts: list[Path] = []
    changed = 0

    for destination, (source, managed) in files.items():
        if not managed:
            continue
        path = target / destination
        expected = content(source, destination)

        if not path.exists():
            write(path, expected, dry)
            print(f"{'WOULD CREATE' if dry else 'CREATED'}: {destination}")
            changed += 1
            continue

        actual = path.read_text(encoding="utf-8")
        if destination != Path(".ai/ROLE_VERSION") and not actual.startswith(MARKER):
            conflicts.append(destination)
            continue
        if actual != expected:
            write(path, expected, dry)
            print(f"{'WOULD REFRESH' if dry else 'REFRESHED'}: {destination}")
            changed += 1

    for path in conflicts:
        print(f"REFUSED UNMANAGED FILE: {path}", file=sys.stderr)
    if conflicts:
        return 2
    if not changed:
        print("Managed core is already current.")
    return 0


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def audit(target: Path, files: dict[Path, tuple[Path | None, bool]]) -> int:
    issues: list[str] = []

    for destination, (source, managed) in files.items():
        path = target / destination
        if not path.exists():
            issues.append(f"missing: {destination}")
            continue
        if managed:
            actual = path.read_text(encoding="utf-8")
            expected = content(source, destination)
            if actual != expected:
                issues.append(
                    f"managed drift: {destination} "
                    f"(actual {digest(actual)}, expected {digest(expected)})"
                )

    checks = {
        Path("AGENTS.md"): (".ai/ROLE.md", ".ai/PROJECT.md"),
        Path(".codex/AGENTS.md"): ("AGENTS.md", ".ai/"),
        Path(".omo/AGENTS.md"): ("AGENTS.md", ".ai/"),
        Path("CLAUDE.md"): ("AGENTS.md", ".ai/"),
    }
    for relative, needles in checks.items():
        path = target / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"{relative} does not route to {needle}")

    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        return 1

    print("PASS: canonical role files and adapters match this pack.")
    project = target / ".ai/PROJECT.md"
    if project.exists() and "Complete this file" in project.read_text(encoding="utf-8"):
        print("NOTE: .ai/PROJECT.md still contains bootstrap placeholders.")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    for name in ("init", "refresh", "audit"):
        command = commands.add_parser(name)
        command.add_argument("target", type=Path)
        command.add_argument(
            "--profile",
            choices=("general", "scientific"),
            default="general",
        )
        command.add_argument(
            "--runtime",
            action="append",
            choices=("codex", "omo", "claude"),
            default=[],
        )
        if name != "audit":
            command.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    target = target_dir(args.target)
    files = specs(args.profile, args.runtime)
    if args.command == "init":
        return init(target, files, args.dry_run)
    if args.command == "refresh":
        return refresh(target, files, args.dry_run)
    return audit(target, files)


if __name__ == "__main__":
    raise SystemExit(main())
