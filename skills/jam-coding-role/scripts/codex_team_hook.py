#!/usr/bin/env python3
"""Adaptive Codex hook for optional Jam Coding Role coordination state.

The hook is inert while coordination is inactive.  When strict coordination is
active, malformed hook input or Git-root resolution errors fail closed for
PreToolUse instead of silently allowing the tool call.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HookInputError(RuntimeError):
    """Raised when Codex hook input cannot be interpreted safely."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def payload() -> dict[str, Any]:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise HookInputError(f"invalid hook JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise HookInputError("hook input must be a JSON object")
    return data


def emit(data: dict[str, Any]) -> int:
    print(json.dumps(data, ensure_ascii=False))
    return 0


def allow(event: str, context: str | None = None) -> int:
    """Return the common output shape supported by PostToolUse/SessionStart."""

    out: dict[str, Any] = {"continue": True}
    if context:
        out["hookSpecificOutput"] = {
            "hookEventName": event,
            "additionalContext": context,
        }
    return emit(out)


def pre_allow(context: str | None = None) -> int:
    """Allow PreToolUse without unsupported common output fields.

    Exit 0 with no stdout is the canonical no-op success.  When model-visible
    context is useful, emit only the PreToolUse-specific additionalContext
    shape.  In particular, never return ``continue`` for PreToolUse.
    """

    if not context:
        return 0
    return emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": context,
            }
        }
    )


def pre_deny(reason: str) -> int:
    """Deny PreToolUse using only the supported hook-specific decision shape."""

    return emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )


def root_from(data: dict[str, Any]) -> Path:
    raw_cwd = data.get("cwd")
    if not isinstance(raw_cwd, str) or not raw_cwd.strip():
        raise HookInputError("hook input is missing a valid cwd")
    cwd = Path(raw_cwd).expanduser().resolve()
    if not cwd.is_dir():
        raise HookInputError(f"hook cwd is not a directory: {cwd}")
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise HookInputError(f"cannot resolve repository root from {cwd}: {detail.strip()}") from exc
    raw_root = result.stdout.strip()
    if not raw_root:
        raise HookInputError(f"git returned an empty repository root for {cwd}")
    root = Path(raw_root).expanduser().resolve()
    if not root.is_dir():
        raise HookInputError(f"resolved repository root is not a directory: {root}")
    return root


def marker(root: Path) -> Path:
    return root / ".ai/runtime/team/coordination.json"


def pre(data: dict[str, Any]) -> int:
    tool = data.get("tool_name") or data.get("toolName") or ""
    if tool != "spawn_agent":
        return pre_allow()
    root = root_from(data)
    if not marker(root).is_file():
        return pre_allow()
    tool_input = data.get("tool_input") or data.get("toolInput") or {}
    if not isinstance(tool_input, dict):
        raise HookInputError("spawn_agent tool_input must be an object")
    task_name = tool_input.get("task_name") or tool_input.get("taskName") or ""
    role = tool_input.get("agent_type") or tool_input.get("agentType") or ""
    script = root / ".ai/scripts/team_state.py"
    if not script.is_file():
        raise HookInputError(f"coordination marker exists but validator is missing: {script}")
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "hook-check-spawn",
            "--task-name",
            str(task_name),
            "--role",
            str(role),
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    text = (result.stdout or result.stderr).strip()
    try:
        verdict = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HookInputError(
            f"coordination validator returned invalid JSON: {text or '<empty>'}"
        ) from exc
    if not isinstance(verdict, dict):
        raise HookInputError("coordination validator result must be an object")
    if result.returncode or not verdict.get("allow"):
        return pre_deny(str(verdict.get("reason") or "coordination validation failed"))
    reason = str(verdict.get("reason") or "")
    return pre_allow(reason if verdict.get("managed") else None)


def _selected_input_metadata(tool_input: Any) -> dict[str, Any]:
    if not isinstance(tool_input, dict):
        return {}
    selected: dict[str, Any] = {}
    for key in (
        "task_name",
        "taskName",
        "agent_type",
        "agentType",
        "target",
        "id",
        "path_prefix",
        "pathPrefix",
        "interrupt",
    ):
        value = tool_input.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            if key in tool_input:
                selected[key] = value
    return selected


def _selected_response_metadata(tool_response: Any) -> dict[str, Any]:
    if not isinstance(tool_response, dict):
        return {}
    selected: dict[str, Any] = {}
    for key in (
        "success",
        "status",
        "task_name",
        "taskName",
        "agent_id",
        "agentId",
        "agent_name",
        "agentName",
        "previous_status",
        "previousStatus",
    ):
        value = tool_response.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            if key in tool_response:
                selected[key] = value
    return selected


def coordination_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """Extract coordination metadata without retaining prompts or tool output."""

    result: dict[str, Any] = {
        "timestamp": now(),
        "event": data.get("hook_event_name") or data.get("hookEventName") or "PostToolUse",
        "session_id": data.get("session_id") or data.get("sessionId"),
        "turn_id": data.get("turn_id") or data.get("turnId"),
        "agent_id": data.get("agent_id") or data.get("agentId"),
        "agent_type": data.get("agent_type") or data.get("agentType"),
        "tool_name": data.get("tool_name") or data.get("toolName"),
        "tool_use_id": data.get("tool_use_id") or data.get("toolUseId"),
        "input": _selected_input_metadata(data.get("tool_input") or data.get("toolInput")),
        "response": _selected_response_metadata(
            data.get("tool_response") or data.get("toolResponse")
        ),
    }
    return {key: value for key, value in result.items() if value not in (None, {}, "")}


def append_jsonl(path: Path, item: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(item, ensure_ascii=False, default=str) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, encoded)
    finally:
        os.close(fd)


def post(data: dict[str, Any]) -> int:
    root = root_from(data)
    if not marker(root).is_file():
        return allow("PostToolUse")
    append_jsonl(root / ".ai/runtime/team/hook-events.jsonl", coordination_metadata(data))
    return allow("PostToolUse")


def _archive_path(archive_root: Path, name: str) -> Path:
    candidate = archive_root / name
    if not candidate.exists():
        return candidate
    stem = Path(name).stem
    suffix = Path(name).suffix
    counter = 2
    while True:
        candidate = archive_root / f"{stem}-{counter:02d}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def session_start(data: dict[str, Any]) -> int:
    root = root_from(data)
    pending = root / ".ai/runtime/pending-events"
    if not pending.is_dir():
        return allow("SessionStart")

    paths = sorted(path for path in pending.glob("*.json") if path.is_file())
    if not paths:
        return allow("SessionStart")

    parsed: list[tuple[Path, dict[str, Any]]] = []
    for path in paths:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HookInputError(f"cannot read pending event {path}: {exc}") from exc
        if not isinstance(obj, dict):
            raise HookInputError(f"pending event must be an object: {path}")
        parsed.append((path, obj))

    session_id = str(data.get("session_id") or data.get("sessionId") or "unknown")
    delivered_at = now()
    archive_root = pending / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    items: list[str] = []
    for path, obj in parsed[:20]:
        items.append(f"{path.name}: {obj.get('state', 'UNKNOWN')} - {obj.get('summary', '')}")
        archived = {
            **obj,
            "delivery_state": "delivered",
            "delivered_at": delivered_at,
            "delivered_to_session": session_id,
            "original_pending_name": path.name,
        }
        destination = _archive_path(archive_root, path.name)
        destination.write_text(
            json.dumps(archived, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        path.unlink()

    # Leave events above the per-session context cap pending for a later session.
    context = "Pending long-run events (delivered once and archived):\n" + "\n".join(
        f"- {item}" for item in items
    )
    return allow("SessionStart", context)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        data = payload()
        if mode == "pre":
            return pre(data)
        if mode == "post":
            return post(data)
        if mode == "session-start":
            return session_start(data)
        return allow(
            data.get("hook_event_name") or data.get("hookEventName") or "PostToolUse"
        )
    except HookInputError as exc:
        print(f"codex_team_hook: {exc}", file=sys.stderr)
        # Exit 2 is the documented fail-closed path for PreToolUse.  Other hook
        # events fail visibly with a non-zero status but do not masquerade as an
        # allow decision.
        return 2 if mode == "pre" else 1


if __name__ == "__main__":
    raise SystemExit(main())
