#!/usr/bin/env python3
"""Safely bootstrap, refresh, or audit Jam Coding Role v1.3.0.

The default install is deliberately lean. Persistent coordination, long-run
continuity, stage planning, artifact handoff, runtime adapters, and a project
memory router are installed only when their explicit flags are selected.
"""

from __future__ import annotations

import argparse
import json
import py_compile
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("Python 3.11+ is required (tomllib missing).") from exc

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
MARKER = "managed-by: jam-coding-role"
OPTIONAL_INSTRUCTION_DOCS = {
    ".ai/TEAM_STATE.md",
    ".ai/MEMORY_GOVERNANCE.md",
    ".ai/LONG_RUNNING_TASKS.md",
    ".ai/SCIENTIFIC_ENGINEERING.md",
    ".ai/STAGE_DECISION.md",
    ".ai/ARTIFACT_HANDOFF.md",
}

Spec = tuple[Path | None, bool]


def specs(
    profile: str,
    runtimes: list[str],
    *,
    memory: bool,
    codex_coordination_state: bool,
    long_run_supervisor: bool,
    stage_workflow: bool,
    artifact_sync: bool,
    omo_team_mode: bool,
) -> dict[Path, Spec]:
    """Return destination -> (source, managed-core) for the selected profile."""

    files: dict[Path, Spec] = {
        Path(".ai/ROLE.md"): (ROOT / "references/ROLE.md", True),
        Path(".ai/WORKFLOW.md"): (ROOT / "references/WORKFLOW.md", True),
        # Installed as a capability, but read only when a durable candidate exists.
        Path(".ai/MEMORY_GOVERNANCE.md"): (
            ROOT / "references/MEMORY_GOVERNANCE.md",
            True,
        ),
        Path(".ai/ROLE_VERSION"): (None, True),
        Path("AGENTS.md"): (ROOT / "templates/AGENTS.md", False),
        Path(".ai/PROJECT.md"): (ROOT / "templates/PROJECT.md", False),
    }

    if memory:
        files[Path("MEMORY.md")] = (ROOT / "templates/MEMORY.md", False)
        files[Path(".ai/scripts/memory_curator.py")] = (
            ROOT / "scripts/memory_curator.py",
            False,
        )

    if runtimes:
        files[Path(".ai/RUNTIME_ADAPTERS.md")] = (
            ROOT / "references/RUNTIME_ADAPTERS.md",
            True,
        )

    if profile == "scientific":
        files[Path(".ai/SCIENTIFIC_ENGINEERING.md")] = (
            ROOT / "references/SCIENTIFIC_ENGINEERING.md",
            True,
        )

    if codex_coordination_state:
        files.update(
            {
                Path(".ai/TEAM_STATE.md"): (ROOT / "references/TEAM_STATE.md", True),
                Path(".ai/team-state.toml"): (ROOT / "templates/TEAM_STATE.toml", False),
                Path(".ai/scripts/team_state.py"): (ROOT / "scripts/team_state.py", False),
                Path(".ai/scripts/codex_team_hook.py"): (
                    ROOT / "scripts/codex_team_hook.py",
                    False,
                ),
                Path(".codex/hooks.json"): (ROOT / "templates/CODEX_HOOKS.json", False),
            }
        )

    if long_run_supervisor:
        files.update(
            {
                Path(".ai/LONG_RUNNING_TASKS.md"): (
                    ROOT / "references/LONG_RUNNING_TASKS.md",
                    True,
                ),
                Path(".ai/scripts/run_supervisor.py"): (
                    ROOT / "scripts/run_supervisor.py",
                    False,
                ),
            }
        )

    if stage_workflow:
        files[Path(".ai/STAGE_DECISION.md")] = (
            ROOT / "references/STAGE_DECISION.md",
            True,
        )

    if artifact_sync:
        files.update(
            {
                Path(".ai/ARTIFACT_HANDOFF.md"): (
                    ROOT / "references/ARTIFACT_HANDOFF.md",
                    True,
                ),
                Path(".ai/artifact-sync.toml"): (
                    ROOT / "templates/ARTIFACT_SYNC.toml",
                    False,
                ),
                Path(".ai/artifact-targets.toml"): (
                    ROOT / "templates/ARTIFACT_TARGETS.toml",
                    False,
                ),
                Path(".ai/scripts/stage_artifacts.py"): (
                    ROOT / "scripts/stage_artifacts.py",
                    False,
                ),
            }
        )

    if "codex" in runtimes:
        files[Path(".codex/AGENTS.md")] = (ROOT / "templates/CODEX_AGENTS.md", False)
        files[Path(".codex/TEAM.md")] = (ROOT / "templates/CODEX_TEAM.md", False)

    if "omo" in runtimes:
        files[Path(".omo/AGENTS.md")] = (ROOT / "templates/OMO_AGENTS.md", False)
        # Both profiles intentionally preload only the core route, not optional docs.
        files[Path("opencode.json")] = (ROOT / "templates/OPENCODE.json", False)
        if omo_team_mode:
            files[Path(".omo/omo.jsonc")] = (ROOT / "templates/OMO_TEAM.jsonc", False)

    if "claude" in runtimes:
        files[Path("CLAUDE.md")] = (ROOT / "templates/CLAUDE.md", False)
        files[Path(".claude/settings.json")] = (
            ROOT / "templates/CLAUDE_SETTINGS.json",
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
    if path.suffix == ".py":
        path.chmod(path.stat().st_mode | 0o111)


def init(target: Path, files: dict[Path, Spec], dry: bool) -> int:
    for destination, (source, _) in files.items():
        path = target / destination
        if path.exists():
            print(f"SKIPPED EXISTING: {destination}")
            continue
        write(path, content(source, destination), dry)
        print(f"{'WOULD CREATE' if dry else 'CREATED'}: {destination}")

    print("\nFill .ai/PROJECT.md from real code/config paths, then run audit.")
    if Path(".ai/team-state.toml") in files:
        print("NOTE: coordination tooling is installed but remains inactive until explicit activation.")
    if Path(".ai/artifact-sync.toml") in files:
        print(
            "NOTE: artifact handoff remains explicit. Public-write folder permission does not "
            "replace runtime/API authentication, and no upload is performed by bootstrap."
        )
    return 0


def is_managed_text(text: str) -> bool:
    return MARKER in "\n".join(text.splitlines()[:3])


def refresh(target: Path, files: dict[Path, Spec], dry: bool) -> int:
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
        if destination != Path(".ai/ROLE_VERSION") and not is_managed_text(actual):
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


def parse_json(path: Path, issues: list[str]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"invalid JSON: {path}: {exc}")
        return None


def parse_toml(path: Path, issues: list[str]) -> dict[str, Any] | None:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        issues.append(f"invalid TOML: {path}: {exc}")
        return None


def compile_python(path: Path, issues: list[str]) -> None:
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        issues.append(f"invalid Python: {path}: {exc.msg}")


def audit(
    target: Path,
    files: dict[Path, Spec],
    *,
    profile: str,
    runtimes: list[str],
    memory: bool,
    codex_coordination_state: bool,
    long_run_supervisor: bool,
    artifact_sync: bool,
    omo_team_mode: bool,
) -> int:
    issues: list[str] = []

    for destination, (source, managed) in files.items():
        path = target / destination
        if not path.exists():
            issues.append(f"missing: {destination}")
            continue
        if managed and path.read_text(encoding="utf-8") != content(source, destination):
            issues.append(f"managed drift: {destination}")

    route_checks = {
        Path("AGENTS.md"): (".ai/ROLE.md", ".ai/PROJECT.md", ".ai/WORKFLOW.md", "FAST"),
        Path(".codex/AGENTS.md"): ("AGENTS.md", ".codex/TEAM.md"),
        Path(".omo/AGENTS.md"): ("AGENTS.md", "Team Mode"),
        Path("CLAUDE.md"): ("@AGENTS.md", "single-agent"),
    }
    for relative, needles in route_checks.items():
        path = target / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"{relative} does not route/declare {needle}")

    if not memory and (target / "MEMORY.md").exists() and Path("MEMORY.md") not in files:
        # Existing project memory is allowed; bootstrap simply did not require/create it.
        pass

    if "omo" in runtimes:
        path = target / "opencode.json"
        if path.exists():
            data = parse_json(path, issues)
            if isinstance(data, dict):
                instructions = data.get("instructions", [])
                required = [
                    "AGENTS.md",
                    ".ai/ROLE.md",
                    ".ai/PROJECT.md",
                    ".ai/WORKFLOW.md",
                    ".ai/RUNTIME_ADAPTERS.md",
                    ".omo/AGENTS.md",
                ]
                for item in required:
                    if item not in instructions:
                        issues.append(f"opencode.json instructions missing {item}")
                for item in sorted(OPTIONAL_INSTRUCTION_DOCS):
                    if item in instructions:
                        issues.append(
                            f"opencode.json eagerly preloads optional document {item}; v1.3 requires lazy routing"
                        )
        if omo_team_mode:
            path = target / ".omo/omo.jsonc"
            if path.exists():
                data = parse_json(path, issues)
                if isinstance(data, dict) and not data.get("team_mode", {}).get("enabled"):
                    issues.append(".omo/omo.jsonc does not enable team_mode")

    if "claude" in runtimes:
        path = target / ".claude/settings.json"
        if path.exists():
            data = parse_json(path, issues)
            if isinstance(data, dict):
                deny = data.get("permissions", {}).get("deny", [])
                if "Agent" not in deny:
                    issues.append(".claude/settings.json does not deny Agent")
                if data.get("disableAgentView") is not True:
                    issues.append(".claude/settings.json does not disable Agent view")

    if codex_coordination_state:
        team_cfg = target / ".ai/team-state.toml"
        data = parse_toml(team_cfg, issues) if team_cfg.exists() else None
        if isinstance(data, dict) and data.get("default_mode") != "inactive":
            issues.append("team-state.toml default_mode must be inactive")
        hooks = target / ".codex/hooks.json"
        if hooks.exists():
            hooks_data = parse_json(hooks, issues)
            if isinstance(hooks_data, dict):
                for event_groups in hooks_data.get("hooks", {}).values():
                    if not isinstance(event_groups, list):
                        continue
                    for group in event_groups:
                        if not isinstance(group, dict):
                            continue
                        for handler in group.get("hooks", []):
                            if not isinstance(handler, dict) or handler.get("type") != "command":
                                continue
                            command = str(handler.get("command", ""))
                            if ".ai/scripts/" in command and "git rev-parse --show-toplevel" not in command:
                                issues.append(
                                    "repo-local Codex hook command does not resolve from git root"
                                )
        for script in ("team_state.py", "codex_team_hook.py"):
            path = target / ".ai/scripts" / script
            if path.exists():
                compile_python(path, issues)
        runtime_marker = target / ".ai/runtime/team/coordination.json"
        if runtime_marker.exists():
            print("NOTE: coordination state is currently active in the target project.")

    if long_run_supervisor:
        path = target / ".ai/scripts/run_supervisor.py"
        if path.exists():
            compile_python(path, issues)

    if artifact_sync:
        sync_path = target / ".ai/artifact-sync.toml"
        sync_data = parse_toml(sync_path, issues) if sync_path.exists() else None
        if isinstance(sync_data, dict):
            activation = sync_data.get("activation", {})
            if activation.get("mode") != "explicit":
                issues.append("artifact-sync.toml activation.mode must be explicit")
            if activation.get("require_confirm_stage_handoff") is not True:
                issues.append("artifact-sync.toml must require stage-handoff confirmation")
            if not sync_data.get("upload", {}).get("root_folder_id"):
                issues.append("artifact-sync.toml missing upload.root_folder_id")
            packaging = sync_data.get("packaging", {})
            if int(packaging.get("max_single_zip_bytes", 0)) != 95 * 1024 * 1024:
                issues.append("artifact-sync.toml max_single_zip_bytes must be 95 MiB")
            if packaging.get("split_volume_archives") is not False:
                issues.append("artifact-sync.toml must reject split-volume archives")
            if packaging.get("index_filename") != "BUNDLE_INDEX.md":
                issues.append("artifact-sync.toml index_filename must be BUNDLE_INDEX.md")
        targets_path = target / ".ai/artifact-targets.toml"
        if targets_path.exists():
            parse_toml(targets_path, issues)
        script = target / ".ai/scripts/stage_artifacts.py"
        if script.exists():
            compile_python(script, issues)

    if profile == "scientific" and not (target / ".ai/SCIENTIFIC_ENGINEERING.md").exists():
        issues.append("scientific profile missing .ai/SCIENTIFIC_ENGINEERING.md")

    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        return 1

    print("PASS: requested v1.3 core, adapters, and optional facilities match this pack.")
    print("PASS: optional workflow documents remain lazy-routed rather than globally preloaded.")
    project = target / ".ai/PROJECT.md"
    if project.exists() and "Complete this file" in project.read_text(encoding="utf-8"):
        print("NOTE: .ai/PROJECT.md still contains bootstrap placeholders.")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("init", "refresh", "audit"):
        command = commands.add_parser(name)
        command.add_argument("target", type=Path)
        command.add_argument("--profile", choices=("general", "scientific"), default="general")
        command.add_argument(
            "--runtime", action="append", choices=("codex", "omo", "claude"), default=[]
        )
        command.add_argument(
            "--memory",
            action="store_true",
            help="Create a project MEMORY.md router. Omit for a memory-free lean project.",
        )
        command.add_argument("--codex-coordination-state", action="store_true")
        command.add_argument("--long-run-supervisor", action="store_true")
        command.add_argument("--stage-workflow", action="store_true")
        command.add_argument("--artifact-sync", action="store_true")
        command.add_argument("--omo-team-mode", action="store_true")
        if name != "audit":
            command.add_argument("--dry-run", action="store_true")
    return root


def validate_args(args: argparse.Namespace) -> None:
    if args.omo_team_mode and "omo" not in args.runtime:
        raise SystemExit("--omo-team-mode requires --runtime omo")
    if args.codex_coordination_state and "codex" not in args.runtime:
        raise SystemExit("--codex-coordination-state requires --runtime codex")


def main() -> int:
    args = parser().parse_args()
    validate_args(args)
    target = target_dir(args.target)
    files = specs(
        args.profile,
        args.runtime,
        memory=args.memory,
        codex_coordination_state=args.codex_coordination_state,
        long_run_supervisor=args.long_run_supervisor,
        stage_workflow=args.stage_workflow,
        artifact_sync=args.artifact_sync,
        omo_team_mode=args.omo_team_mode,
    )
    if args.command == "init":
        return init(target, files, args.dry_run)
    if args.command == "refresh":
        return refresh(target, files, args.dry_run)
    return audit(
        target,
        files,
        profile=args.profile,
        runtimes=args.runtime,
        memory=args.memory,
        codex_coordination_state=args.codex_coordination_state,
        long_run_supervisor=args.long_run_supervisor,
        artifact_sync=args.artifact_sync,
        omo_team_mode=args.omo_team_mode,
    )


if __name__ == "__main__":
    raise SystemExit(main())
