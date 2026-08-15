from __future__ import annotations

from pathlib import Path

from forgecode_agent import cli
from forgecode_agent.cli import WorkspaceStatus, workspace_status


def test_workspace_status_reports_missing_config_and_no_active_task(tmp_path) -> None:
    status = workspace_status(tmp_path)

    assert isinstance(status, WorkspaceStatus)
    assert status.workspace == tmp_path
    assert status.workspace_state == "ok"
    assert status.config_state == "missing"
    assert status.model_provider is None
    assert status.active_task is None


def test_workspace_status_reports_missing_workspace(tmp_path) -> None:
    workspace = tmp_path / "missing"

    status = workspace_status(workspace)

    assert status.workspace == workspace
    assert status.workspace_state == "missing"
    assert status.config_state == "missing"
    assert status.model_provider is None
    assert status.active_task is None


def test_workspace_status_reports_symlink_workspace_as_missing(tmp_path) -> None:
    target_workspace = tmp_path / "target"
    target_workspace.mkdir()
    target_forge_dir = target_workspace / ".forge"
    target_forge_dir.mkdir()
    (target_forge_dir / "config.toml").write_text(
        'model_provider = "fake"\n', encoding="utf-8"
    )
    workspace = tmp_path / "workspace-link"
    workspace.symlink_to(target_workspace, target_is_directory=True)

    status = workspace_status(workspace)

    assert status.workspace == workspace
    assert status.workspace_state == "missing"
    assert status.config_state == "missing"
    assert status.model_provider is None
    assert status.active_task is None


def test_workspace_status_reports_config_and_active_task(tmp_path) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    (forge_dir / "config.toml").write_text('model_provider = "fake"\n', encoding="utf-8")
    (forge_dir / "active-task.toml").write_text(
        'path = "tasks/001-build-status.md"\nname = "Build status"\n',
        encoding="utf-8",
    )

    status = workspace_status(tmp_path)

    assert status.workspace_state == "ok"
    assert status.config_state == "ok"
    assert status.model_provider == "fake"
    assert status.active_task == "Build status (tasks/001-build-status.md)"


def test_workspace_status_refuses_symlinked_forge_directory(tmp_path) -> None:
    target_forge_dir = tmp_path / "target-forge"
    target_forge_dir.mkdir()
    (target_forge_dir / "config.toml").write_text(
        'model_provider = "fake"\n', encoding="utf-8"
    )
    (target_forge_dir / "active-task.toml").write_text(
        'name = "Should not be read"\npath = "tasks/secret.md"\n', encoding="utf-8"
    )
    (tmp_path / ".forge").symlink_to(target_forge_dir, target_is_directory=True)

    status = workspace_status(tmp_path)

    assert status.workspace_state == "ok"
    assert status.config_state == "missing"
    assert status.model_provider is None
    assert status.active_task is None


def test_workspace_status_ignores_invalid_utf8_config(tmp_path) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    (forge_dir / "config.toml").write_bytes(b'\xffmodel_provider = "fake"\n')

    status = workspace_status(tmp_path)

    assert status.workspace_state == "ok"
    assert status.config_state == "ok"
    assert status.model_provider is None
    assert status.active_task is None


def test_workspace_status_ignores_active_task_decode_error(tmp_path) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    (forge_dir / "config.toml").write_text('model_provider = "fake"\n', encoding="utf-8")
    (forge_dir / "active-task.toml").write_bytes(b'\xffname = "Build status"\n')

    status = workspace_status(tmp_path)

    assert status.workspace_state == "ok"
    assert status.config_state == "ok"
    assert status.model_provider == "fake"
    assert status.active_task is None


def test_workspace_status_treats_config_directory_as_missing(tmp_path) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    (forge_dir / "config.toml").mkdir()

    status = workspace_status(tmp_path)

    assert status.workspace_state == "ok"
    assert status.config_state == "missing"
    assert status.model_provider is None


def test_workspace_status_ignores_active_task_directory(tmp_path, monkeypatch) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    active_task_file = forge_dir / "active-task.toml"
    active_task_file.mkdir()

    def fail_if_active_task_is_read(path: Path) -> dict[str, str]:
        raise AssertionError(f"should not read directory: {path}")

    monkeypatch.setattr(cli, "_read_simple_toml_strings", fail_if_active_task_is_read)

    status = workspace_status(tmp_path)

    assert status.workspace_state == "ok"
    assert status.config_state == "missing"
    assert status.active_task is None


def test_main_status_workspace_option_uses_provided_workspace(tmp_path, monkeypatch, capsys) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    called_with: list[Path] = []

    def fake_workspace_status(workspace_arg: Path) -> WorkspaceStatus:
        called_with.append(workspace_arg)
        return WorkspaceStatus(
            workspace=workspace_arg,
            workspace_state="ok",
            config_state="missing",
            model_provider=None,
            active_task=None,
        )

    monkeypatch.setattr(cli, "workspace_status", fake_workspace_status)

    exit_code = cli.main(["status", "--workspace", str(workspace)])

    assert exit_code == 0
    assert called_with == [workspace]
    assert capsys.readouterr().out == (
        "workspace: ok\nconfig: missing\nmodel_provider: none\nactive_task: none\n"
    )


def test_main_status_prints_configured_model_provider(tmp_path, capsys) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    (forge_dir / "config.toml").write_text('model_provider = "fake"\n', encoding="utf-8")

    exit_code = cli.main(["status", "--workspace", str(tmp_path)])

    assert exit_code == 0
    assert "model_provider: fake\n" in capsys.readouterr().out
