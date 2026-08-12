from pathlib import Path

import pytest

from forgecode_agent import cli


def test_config_reports_missing_config(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(["config", "--workspace", str(tmp_path)])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"


def test_config_prints_supported_string_entries_sorted_by_key(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text(
        'zeta = "last"\nignored = true\nalpha = "first"\n',
        encoding="utf-8",
    )

    exit_code = cli.main(["config", "--workspace", str(tmp_path)])

    assert exit_code == 0
    assert capsys.readouterr().out == "alpha: first\nzeta: last\n"


def test_config_reports_missing_for_non_file_config(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    config_file.mkdir()

    exit_code = cli.main(["config", "--workspace", str(tmp_path)])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"


def test_config_reports_missing_for_symlink_to_regular_file(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    target_file = tmp_path / "target-config.toml"
    config_file.parent.mkdir()
    target_file.write_text('model_provider = "local"\n', encoding="utf-8")
    config_file.symlink_to(target_file)

    exit_code = cli.main(["config", "--workspace", str(tmp_path)])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"


def test_config_reports_missing_for_symlinked_forge_directory(tmp_path: Path, capsys) -> None:
    real_forge = tmp_path / "real-forge"
    real_forge.mkdir()
    (real_forge / "config.toml").write_text(
        'model_provider = "outside"\n', encoding="utf-8"
    )
    (tmp_path / ".forge").symlink_to(real_forge, target_is_directory=True)

    exit_code = cli.main(["config", "--workspace", str(tmp_path)])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"


def test_config_fails_closed_when_no_follow_is_unavailable(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text('model_provider = "local"\n', encoding="utf-8")
    monkeypatch.delattr(cli.os, "O_NOFOLLOW", raising=False)

    exit_code = cli.main(["config", "--workspace", str(tmp_path)])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"


def test_config_reports_ok_for_readable_config_without_supported_strings(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text("enabled = true\n", encoding="utf-8")

    exit_code = cli.main(["config", "--workspace", str(tmp_path)])

    assert exit_code == 0
    assert capsys.readouterr().out == "config: ok\n"


def test_config_reads_from_opened_descriptor_not_path_read_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text('model_provider = "local"\n', encoding="utf-8")

    def deny_read(self, *args, **kwargs):
        raise AssertionError("config command must not call Path.read_text")

    monkeypatch.setattr(Path, "read_text", deny_read)

    exit_code = cli.main(["config", "--workspace", str(tmp_path)])

    assert exit_code == 0
    assert capsys.readouterr().out == "model_provider: local\n"


def test_config_set_updates_supported_string_entry(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text('model_provider = "local"\nother = true\n', encoding="utf-8")

    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--set", 'model_provider="remote"'])

    assert exit_code == 0
    assert capsys.readouterr().out == "config: updated\n"
    assert config_file.read_text(encoding="utf-8") == 'model_provider = "remote"\nother = true\n'


@pytest.mark.parametrize("assignment", ["unknown=value", "model_provider=", "model_provider=true", "model_provider"])
def test_config_set_rejects_invalid_assignment(tmp_path: Path, assignment: str, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    original = 'model_provider = "local"\n'
    config_file.write_text(original, encoding="utf-8")

    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--set", assignment])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: invalid\n"
    assert config_file.read_text(encoding="utf-8") == original


def test_config_set_rejects_missing_config(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--set", 'model_provider="remote"'])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"


def test_config_set_fails_closed_without_no_follow(tmp_path: Path, monkeypatch, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text('model_provider = "local"\n', encoding="utf-8")
    monkeypatch.delattr(cli.os, "O_NOFOLLOW", raising=False)

    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--set", 'model_provider="remote"'])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"
    assert config_file.read_text(encoding="utf-8") == 'model_provider = "local"\n'


def test_config_set_rejects_symlink_config(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    target = tmp_path / "target.toml"
    config_file.parent.mkdir()
    target.write_text('model_provider = "local"\n', encoding="utf-8")
    config_file.symlink_to(target)

    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--set", 'model_provider="remote"'])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"
    assert target.read_text(encoding="utf-8") == 'model_provider = "local"\n'


def test_config_set_rejects_intermediate_workspace_symlink_and_leaves_target_unchanged(
    tmp_path: Path, capsys
) -> None:
    target_workspace = tmp_path / "target-workspace"
    target_config = target_workspace / ".forge" / "config.toml"
    target_config.parent.mkdir(parents=True)
    original = 'model_provider = "local"\n'
    target_config.write_text(original, encoding="utf-8")
    workspace_parent = tmp_path / "workspace-parent"
    workspace_parent.symlink_to(target_workspace, target_is_directory=True)

    exit_code = cli.main(
        ["config", "--workspace", str(workspace_parent), "--set", 'model_provider="remote"']
    )

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"
    assert target_config.read_text(encoding="utf-8") == original


def test_config_set_accepts_toml_literal_single_quoted_string(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    config_file.write_text('model_provider = "local"\n', encoding="utf-8")

    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--set", "model_provider='remote'"])

    assert exit_code == 0
    assert capsys.readouterr().out == "config: updated\n"
    assert config_file.read_text(encoding="utf-8") == 'model_provider = "remote"\n'


def test_config_set_rejects_duplicate_supported_key_without_mutation(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    original = 'model_provider = "first"\nmodel_provider = "last"\n'
    config_file.write_text(original, encoding="utf-8")

    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--set", 'model_provider="new"'])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: invalid\n"
    assert config_file.read_text(encoding="utf-8") == original


def test_config_set_write_failure_preserves_original_config(tmp_path: Path, monkeypatch, capsys) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    original = 'model_provider = "local"\nother = true\n'
    config_file.write_text(original, encoding="utf-8")

    def fail_replace(*args, **kwargs):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(cli.os, "replace", fail_replace)
    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--set", 'model_provider="remote"'])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"
    assert config_file.read_text(encoding="utf-8") == original


def test_config_set_permission_denied_preserves_original_config(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    config_file = tmp_path / ".forge" / "config.toml"
    config_file.parent.mkdir()
    original = 'model_provider = "local"\nother = true\n'
    config_file.write_text(original, encoding="utf-8")

    def deny_replace(*args, **kwargs):
        raise PermissionError(13, "permission denied")

    monkeypatch.setattr(cli.os, "replace", deny_replace)

    exit_code = cli.main(
        ["config", "--workspace", str(tmp_path), "--set", 'model_provider="remote"']
    )

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"
    assert config_file.read_text(encoding="utf-8") == original
