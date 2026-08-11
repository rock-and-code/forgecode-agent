from pathlib import Path

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
