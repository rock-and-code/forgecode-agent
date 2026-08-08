from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DoctorStatus:
    ok: bool
    workspace: Path
    checks: dict[str, str]
    messages: list[str]


def doctor_status(workspace: Path) -> DoctorStatus:
    workspace = Path(workspace)
    messages: list[str] = []
    config_file = workspace / ".forge" / "config.toml"
    provider = os.environ.get("FORGECODE_MODEL_PROVIDER")
    api_key = os.environ.get("FORGECODE_API_KEY")

    checks = {
        "python": "ok",
        "workspace": "ok" if workspace.exists() and workspace.is_dir() else "missing",
        "config_file": "ok" if config_file.exists() else "missing",
        "model_provider": f"ok: {provider}" if provider else "missing",
        "credentials": "ok" if api_key else "missing",
    }

    if checks["workspace"] != "ok":
        messages.append("Workspace does not exist or is not a directory.")
    if checks["config_file"] != "ok":
        messages.append("No ForgeCode config file found in workspace.")
    if provider is None:
        messages.append("FORGECODE_MODEL_PROVIDER is not set.")
    if api_key is None:
        messages.append("FORGECODE_API_KEY is not set.")

    return DoctorStatus(ok=not messages, workspace=workspace, checks=checks, messages=messages)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    status = doctor_status(Path.cwd())
    print("ok" if status.ok else "not ok")
    for message in status.messages:
        print(message)
    return 0 if status.ok else 1
