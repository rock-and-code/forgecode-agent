from __future__ import annotations

import os
import sys
import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DoctorStatus:
    ok: bool
    workspace: Path
    checks: dict[str, str]
    messages: list[str]


@dataclass(frozen=True)
class WorkspaceStatus:
    workspace: Path
    workspace_state: str
    config_state: str
    model_provider: str | None
    active_task: str | None


def _read_simple_toml_strings(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            values[key.strip()] = value[1:-1]
    return values


def workspace_status(workspace: Path) -> WorkspaceStatus:
    workspace = Path(workspace)
    workspace_ok = workspace.exists() and workspace.is_dir()
    forge_dir = workspace / ".forge"
    config_file = forge_dir / "config.toml"
    active_task_file = forge_dir / "active-task.toml"

    model_provider: str | None = None
    config_file_ok = config_file.is_file()
    if config_file_ok:
        config = _read_simple_toml_strings(config_file)
        model_provider = config.get("model_provider")

    active_task: str | None = None
    if active_task_file.exists():
        task = _read_simple_toml_strings(active_task_file)
        task_name = task.get("name")
        task_path = task.get("path")
        if task_name and task_path:
            active_task = f"{task_name} ({task_path})"
        elif task_name:
            active_task = task_name
        elif task_path:
            active_task = task_path

    return WorkspaceStatus(
        workspace=workspace,
        workspace_state="ok" if workspace_ok else "missing",
        config_state="ok" if config_file_ok else "missing",
        model_provider=model_provider,
        active_task=active_task,
    )


def doctor_status(workspace: Path) -> DoctorStatus:
    workspace = Path(workspace)
    messages: list[str] = []
    config_file = workspace / ".forge" / "config.toml"
    provider = os.environ.get("FORGECODE_MODEL_PROVIDER")
    if not provider and config_file.is_file():
        try:
            provider = _read_simple_toml_strings(config_file).get("model_provider")
        except (OSError, UnicodeDecodeError):
            provider = None
    api_key = os.environ.get("FORGECODE_API_KEY")

    checks = {
        "python": "ok",
        "workspace": "ok" if workspace.exists() and workspace.is_dir() else "missing",
        "config_file": "ok" if config_file.is_file() else "missing",
        "model_provider": f"ok: {provider}" if provider else "missing",
        "credentials": "ok" if api_key else "missing",
    }

    if checks["workspace"] != "ok":
        messages.append("Workspace does not exist or is not a directory.")
    if checks["config_file"] != "ok":
        messages.append("No ForgeCode config file found in workspace.")
    if not provider:
        messages.append("FORGECODE_MODEL_PROVIDER is not set.")
    if not api_key:
        messages.append("FORGECODE_API_KEY is not set.")

    return DoctorStatus(ok=not messages, workspace=workspace, checks=checks, messages=messages)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="forgecode")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("--workspace", type=Path, default=Path.cwd())
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--workspace", type=Path, default=Path.cwd())

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1

    if args.command == "status":
        status = workspace_status(args.workspace)
        print(f"workspace: {status.workspace_state}")
        print(f"config: {status.config_state}")
        print(f"model_provider: {status.model_provider or 'none'}")
        print(f"active_task: {status.active_task or 'none'}")
        return 0 if status.workspace_state == "ok" else 1

    status = doctor_status(args.workspace)
    print("ok" if status.ok else "not ok")
    for name, value in status.checks.items():
        print(f"{name}: {value}")
    for message in status.messages:
        print(message)
    return 0 if status.ok else 1
