from __future__ import annotations

import errno
import json
import os
import re
import stat
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


@dataclass(frozen=True)
class InitStatus:
    workspace: Path
    forge_dir_created: bool
    config_created: bool
    ok: bool
    message: str | None = None


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


def _read_simple_toml_strings_from_descriptor(descriptor: int) -> dict[str, str]:
    values: dict[str, str] = {}
    with os.fdopen(descriptor, "r", encoding="utf-8") as config:
        for line in config:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, raw_value = stripped.split("=", 1)
            value = raw_value.strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                values[key.strip()] = value[1:-1]
    return values


def _update_config_from_descriptor(forge_descriptor: int, descriptor: int, key: str, value: str) -> None:
    try:
        mode = stat.S_IMODE(os.fstat(descriptor).st_mode)
        with os.fdopen(descriptor, "r", encoding="utf-8") as config:
            lines = config.read().splitlines(keepends=True)
        replacement = f'{key} = {json.dumps(value)}\n'
        pattern = re.compile(rf"^(\s*{re.escape(key)}\s*=).*$")
        matches = [index for index, line in enumerate(lines) if pattern.match(line.rstrip("\r\n"))]
        if len(matches) > 1:
            raise ValueError("duplicate supported config key")
        if matches:
            lines[matches[0]] = replacement
        else:
            if lines and not lines[-1].endswith(("\n", "\r")):
                lines.append("\n")
            lines.append(replacement)

        temporary_name: str | None = None
        temporary_descriptor: int | None = None
        try:
            for attempt in range(100):
                candidate = f".config.toml.tmp.{os.getpid()}.{attempt}"
                try:
                    temporary_descriptor = os.open(
                        candidate,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        mode,
                        dir_fd=forge_descriptor,
                    )
                    temporary_name = candidate
                    break
                except FileExistsError:
                    continue
            if temporary_descriptor is None or temporary_name is None:
                raise OSError("unable to create temporary config")
            with os.fdopen(temporary_descriptor, "w", encoding="utf-8") as temporary:
                temporary_descriptor = None
                temporary.writelines(lines)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.chmod(temporary_name, mode, dir_fd=forge_descriptor, follow_symlinks=False)
            os.replace(
                temporary_name,
                "config.toml",
                src_dir_fd=forge_descriptor,
                dst_dir_fd=forge_descriptor,
            )
            temporary_name = None
            os.fsync(forge_descriptor)
        finally:
            if temporary_descriptor is not None:
                os.close(temporary_descriptor)
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name, dir_fd=forge_descriptor)
                except FileNotFoundError:
                    pass
    finally:
        # The descriptor is owned by this function, including on validation errors.
        try:
            os.close(descriptor)
        except OSError:
            pass


def _open_config_descriptor(workspace: Path, access: int) -> tuple[int, int]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise OSError("no-follow traversal is unavailable")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | nofollow
    absolute_workspace = Path(workspace).absolute()
    workspace_descriptor = os.open(absolute_workspace.anchor, directory_flags)
    try:
        for component in absolute_workspace.parts[1:]:
            child_descriptor = os.open(component, directory_flags, dir_fd=workspace_descriptor)
            os.close(workspace_descriptor)
            workspace_descriptor = child_descriptor
        forge_descriptor = os.open(".forge", directory_flags, dir_fd=workspace_descriptor)
    except OSError:
        os.close(workspace_descriptor)
        raise
    os.close(workspace_descriptor)
    try:
        descriptor = os.open("config.toml", access | nofollow, dir_fd=forge_descriptor)
    except OSError:
        os.close(forge_descriptor)
        raise
    return forge_descriptor, descriptor


def _parse_config_setting(raw_value: str) -> str | None:
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        if len(raw_value) >= 2 and raw_value[0] == raw_value[-1] == "'":
            value = raw_value[1:-1]
        else:
            return None
    return value if isinstance(value, str) and value else None


def workspace_status(workspace: Path) -> WorkspaceStatus:
    workspace = Path(workspace)
    workspace_ok = workspace.exists() and workspace.is_dir()
    forge_dir = workspace / ".forge"
    config_file = forge_dir / "config.toml"
    active_task_file = forge_dir / "active-task.toml"

    model_provider: str | None = None
    config_file_ok = config_file.is_file()
    if config_file_ok:
        try:
            config = _read_simple_toml_strings(config_file)
        except (OSError, UnicodeDecodeError):
            config = {}
        model_provider = config.get("model_provider")

    active_task: str | None = None
    if active_task_file.exists():
        try:
            task = _read_simple_toml_strings(active_task_file)
        except (OSError, UnicodeDecodeError):
            task = {}
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


def initialize_workspace(workspace: Path) -> InitStatus:
    workspace = Path(workspace)
    forge_dir = workspace / ".forge"
    config_file = forge_dir / "config.toml"
    forge_dir_created = False
    config_created = False
    workspace_descriptor: int | None = None
    forge_descriptor: int | None = None
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)

    try:
        # Walk from the root one component at a time.  Every lookup is
        # relative to an already-open directory and refuses symlinks, so a
        # replacement between lookup and mkdir cannot redirect initialization.
        absolute_workspace = workspace.absolute()
        workspace_descriptor = os.open(absolute_workspace.anchor, directory_flags)
        current = Path(absolute_workspace.anchor)
        for component in absolute_workspace.parts[1:]:
            current /= component
            try:
                child_descriptor = os.open(component, directory_flags, dir_fd=workspace_descriptor)
            except FileNotFoundError:
                try:
                    os.mkdir(component, dir_fd=workspace_descriptor)
                except FileExistsError:
                    pass
                try:
                    child_descriptor = os.open(component, directory_flags, dir_fd=workspace_descriptor)
                except OSError as exc:
                    if exc.errno in (errno.ELOOP, errno.ENOTDIR) and stat.S_ISLNK(os.lstat(current).st_mode):
                        raise OSError(f"{current} is a symlink.") from exc
                    raise
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOTDIR) and stat.S_ISLNK(os.lstat(current).st_mode):
                    raise OSError(f"{current} is a symlink.") from exc
                raise
            os.close(workspace_descriptor)
            workspace_descriptor = child_descriptor

        try:
            os.mkdir(".forge", dir_fd=workspace_descriptor)
            forge_dir_created = True
        except FileExistsError:
            forge_mode = os.stat(".forge", dir_fd=workspace_descriptor, follow_symlinks=False).st_mode
            if stat.S_ISLNK(forge_mode):
                return InitStatus(workspace, False, False, False, f"{forge_dir} is a symlink.")
            if not stat.S_ISDIR(forge_mode):
                return InitStatus(workspace, False, False, False, f"{forge_dir} is not a directory.")

        forge_descriptor = os.open(".forge", directory_flags, dir_fd=workspace_descriptor)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open("config.toml", flags, 0o644, dir_fd=forge_descriptor)
        except FileExistsError:
            config_mode = os.stat("config.toml", dir_fd=forge_descriptor, follow_symlinks=False).st_mode
            if stat.S_ISLNK(config_mode):
                return InitStatus(workspace, forge_dir_created, False, False, f"{config_file} is a symlink.")
            if not stat.S_ISREG(config_mode):
                return InitStatus(workspace, forge_dir_created, False, False, f"{config_file} is not a file.")
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8") as config:
                config.write('model_provider = ""\n')
            config_created = True
    except OSError as exc:
        return InitStatus(workspace, forge_dir_created, config_created, False, str(exc))
    finally:
        if forge_descriptor is not None:
            os.close(forge_descriptor)
        if workspace_descriptor is not None:
            os.close(workspace_descriptor)

    return InitStatus(workspace, forge_dir_created, config_created, True)


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
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--workspace", type=Path, default=Path.cwd())
    config_parser = subparsers.add_parser("config")
    config_parser.add_argument("--workspace", type=Path, default=Path.cwd())
    config_parser.add_argument("--set", dest="setting")

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

    if args.command == "init":
        status = initialize_workspace(args.workspace)
        if status.ok:
            print(f"initialized: {status.workspace}")
            print(f"forge_dir: {'created' if status.forge_dir_created else 'exists'}")
            print(f"config: {'created' if status.config_created else 'preserved'}")
        else:
            print(f"init failed: {status.message}")
        return 0 if status.ok else 1

    if args.command == "config":
        config_file = args.workspace / ".forge" / "config.toml"
        setting: tuple[str, str] | None = None
        if args.setting is not None:
            match = re.fullmatch(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*", args.setting)
            if not match or match.group(1) not in {"model_provider", "approval_mode"}:
                print("config: invalid")
                return 1
            value = _parse_config_setting(match.group(2))
            if value is None:
                print("config: invalid")
                return 1
            setting = (match.group(1), value)
        forge_descriptor: int | None = None
        descriptor: int | None = None
        try:
            access = os.O_RDWR if setting is not None else os.O_RDONLY
            forge_descriptor, descriptor = _open_config_descriptor(args.workspace, access)
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError("config is not a regular file")
        except OSError:
            if descriptor is not None:
                os.close(descriptor)
                descriptor = None
            if forge_descriptor is not None:
                os.close(forge_descriptor)
                forge_descriptor = None
            print("config: missing")
            return 1
        if setting is not None:
            try:
                update_descriptor = descriptor
                descriptor = None
                _update_config_from_descriptor(forge_descriptor, update_descriptor, *setting)
            except ValueError:
                print("config: invalid")
                return 1
            except (OSError, UnicodeDecodeError):
                print("config: missing")
                return 1
            finally:
                os.close(forge_descriptor)
            print("config: updated")
            return 0
        try:
            read_descriptor = descriptor
            descriptor = None
            values = _read_simple_toml_strings_from_descriptor(read_descriptor)
        except (OSError, UnicodeDecodeError):
            print("config: missing")
            return 1
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(forge_descriptor)
        for key in sorted(values):
            print(f"{key}: {values[key]}")
        if not values:
            print("config: ok")
        return 0

    status = doctor_status(args.workspace)
    print("ok" if status.ok else "not ok")
    for name, value in status.checks.items():
        print(f"{name}: {value}")
    for message in status.messages:
        print(message)
    return 0 if status.ok else 1
