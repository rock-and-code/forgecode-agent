from __future__ import annotations

from pathlib import Path

from forgecode_agent import cli
from forgecode_agent.cli import InitStatus, initialize_workspace


def test_initialize_workspace_creates_forge_metadata_without_touching_source(tmp_path) -> None:
    source_file = tmp_path / "README.md"
    source_file.write_text("project source\n", encoding="utf-8")

    status = initialize_workspace(tmp_path)

    assert isinstance(status, InitStatus)
    assert status.ok is True
    assert status.workspace == tmp_path
    assert status.forge_dir_created is True
    assert status.config_created is True
    assert (tmp_path / ".forge").is_dir()
    assert (tmp_path / ".forge" / "config.toml").read_text(encoding="utf-8") == (
        'model_provider = ""\n'
    )
    assert source_file.read_text(encoding="utf-8") == "project source\n"


def test_initialize_workspace_preserves_existing_metadata_and_source(tmp_path) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    config_file = forge_dir / "config.toml"
    config_file.write_text('model_provider = "fake"\ncustom = "keep"\n', encoding="utf-8")
    source_file = tmp_path / "src.py"
    source_file.write_text("print('keep')\n", encoding="utf-8")

    status = initialize_workspace(tmp_path)

    assert status.ok is True
    assert status.forge_dir_created is False
    assert status.config_created is False
    assert config_file.read_text(encoding="utf-8") == 'model_provider = "fake"\ncustom = "keep"\n'
    assert source_file.read_text(encoding="utf-8") == "print('keep')\n"


def test_main_init_reports_created_metadata_and_returns_success(tmp_path, capsys) -> None:
    exit_code = cli.main(["init", "--workspace", str(tmp_path)])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        f"initialized: {tmp_path}\nforge_dir: created\nconfig: created\n"
    )


def test_main_init_reports_existing_config_as_preserved(tmp_path, capsys) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    config_file = forge_dir / "config.toml"
    config_file.write_text('model_provider = "fake"\n', encoding="utf-8")

    exit_code = cli.main(["init", "--workspace", str(tmp_path)])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        f"initialized: {tmp_path}\nforge_dir: exists\nconfig: preserved\n"
    )


def test_initialize_workspace_refuses_symlinked_forge_directory(tmp_path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    forge_dir = tmp_path / ".forge"
    forge_dir.symlink_to(outside, target_is_directory=True)

    status = initialize_workspace(tmp_path)

    assert status.ok is False
    assert "symlink" in (status.message or "")
    assert not (outside / "config.toml").exists()


def test_initialize_workspace_refuses_config_path_conflict_without_replacing_it(tmp_path) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    config_file = forge_dir / "config.toml"
    config_file.mkdir()

    status = initialize_workspace(tmp_path)

    assert status.ok is False
    assert "not a file" in (status.message or "")
    assert config_file.is_dir()


def test_initialize_workspace_refuses_symlinked_config_without_following_it(tmp_path) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    outside = tmp_path / "outside.toml"
    outside.write_text("keep me\n", encoding="utf-8")
    config_file = forge_dir / "config.toml"
    config_file.symlink_to(outside)

    status = initialize_workspace(tmp_path)

    assert status.ok is False
    assert "symlink" in (status.message or "")
    assert outside.read_text(encoding="utf-8") == "keep me\n"


def test_initialize_workspace_preserves_config_created_by_racing_process(tmp_path, monkeypatch) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    config_file = forge_dir / "config.toml"
    real_open = cli.os.open

    def create_then_report_conflict(path, flags, mode=0o777, *, dir_fd=None):
        if path == "config.toml" and flags & cli.os.O_EXCL:
            config_file.write_text("created by another process\n", encoding="utf-8")
            raise FileExistsError("config was created concurrently")
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(cli.os, "open", create_then_report_conflict)

    status = initialize_workspace(tmp_path)

    assert status.ok is True
    assert status.config_created is False
    assert config_file.read_text(encoding="utf-8") == "created by another process\n"


def test_initialize_workspace_rejects_symlinked_workspace_before_writing(tmp_path) -> None:
    real_workspace = tmp_path / "real-workspace"
    real_workspace.mkdir()
    workspace = tmp_path / "workspace-link"
    workspace.symlink_to(real_workspace, target_is_directory=True)

    status = initialize_workspace(workspace)

    assert status.ok is False
    assert "symlink" in (status.message or "")
    assert not (real_workspace / ".forge").exists()


def test_initialize_workspace_rejects_symlinked_workspace_ancestor_before_writing(tmp_path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    symlinked_parent = tmp_path / "workspace-parent"
    symlinked_parent.symlink_to(outside, target_is_directory=True)
    workspace = symlinked_parent / "new-workspace"

    status = initialize_workspace(workspace)

    assert status.ok is False
    assert "symlink" in (status.message or "")
    assert not (outside / "new-workspace" / ".forge").exists()


def test_initialize_workspace_rejects_workspace_ancestor_replaced_during_creation(
    tmp_path, monkeypatch
) -> None:
    real_parent = tmp_path / "workspace-parent"
    real_parent.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    workspace = real_parent / "new-workspace"
    original_parent = tmp_path / "original-parent"
    real_mkdir = cli.os.mkdir
    swapped = False

    def swap_parent_before_mkdir(path, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if not swapped and (Path(path) == workspace or path == workspace.name):
            swapped = True
            real_parent.rename(original_parent)
            real_parent.symlink_to(outside, target_is_directory=True)
        return real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(cli.os, "mkdir", swap_parent_before_mkdir)

    status = initialize_workspace(workspace)

    assert status.ok is True
    assert (original_parent / "new-workspace" / ".forge").is_dir()
    assert not (outside / "new-workspace" / ".forge").exists()


def test_initialize_workspace_keeps_config_inside_original_forge_directory_if_replaced(
    tmp_path, monkeypatch
) -> None:
    forge_dir = tmp_path / ".forge"
    forge_dir.mkdir()
    config_file = forge_dir / "config.toml"
    outside = tmp_path / "outside"
    outside.mkdir()
    original_forge = tmp_path / "original-forge"
    real_open = cli.os.open
    replaced = False

    def replace_forge_after_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal replaced
        descriptor = real_open(path, flags, mode, dir_fd=dir_fd)
        if not replaced and (Path(path) == forge_dir or path == ".forge"):
            replaced = True
            forge_dir.rename(original_forge)
            forge_dir.symlink_to(outside, target_is_directory=True)
        return descriptor

    monkeypatch.setattr(cli.os, "open", replace_forge_after_open)

    status = initialize_workspace(tmp_path)

    assert status.ok is True
    assert not (outside / "config.toml").exists()
    assert (original_forge / "config.toml").read_text(encoding="utf-8") == (
        'model_provider = ""\n'
    )
