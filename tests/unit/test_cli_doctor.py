from __future__ import annotations

from pathlib import Path

from forgecode_agent import cli
from forgecode_agent.cli import DoctorStatus, doctor_status


def test_doctor_status_reports_configuration_without_running_subprocess(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FORGECODE_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("FORGECODE_API_KEY", raising=False)

    status = doctor_status(workspace=tmp_path)

    assert isinstance(status, DoctorStatus)
    assert status.ok is False
    assert status.workspace == tmp_path
    assert status.checks == {
        "python": "ok",
        "workspace": "ok",
        "config_file": "missing",
        "model_provider": "missing",
        "credentials": "missing",
    }
    assert status.messages == [
        "No ForgeCode config file found in workspace.",
        "FORGECODE_MODEL_PROVIDER is not set.",
        "FORGECODE_API_KEY is not set.",
    ]


def test_doctor_status_reports_configured_provider(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / ".forge"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text('model_provider = "fake"\n', encoding="utf-8")
    monkeypatch.setenv("FORGECODE_MODEL_PROVIDER", "fake")
    monkeypatch.setenv("FORGECODE_API_KEY", "test-key")

    status = doctor_status(workspace=tmp_path)

    assert status.ok is True
    assert status.checks == {
        "python": "ok",
        "workspace": "ok",
        "config_file": "ok",
        "model_provider": "ok: fake",
        "credentials": "ok",
    }
    assert status.messages == []


def test_main_doctor_uses_current_working_directory(tmp_path, monkeypatch, capsys) -> None:
    called_with: list[Path] = []

    def fake_doctor_status(workspace: Path) -> DoctorStatus:
        called_with.append(workspace)
        return DoctorStatus(ok=True, workspace=workspace, checks={}, messages=[])

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "doctor_status", fake_doctor_status)

    exit_code = cli.main(["doctor"])

    assert exit_code == 0
    assert called_with == [tmp_path]
    assert capsys.readouterr().out == "ok\n"


def test_main_doctor_workspace_option_uses_provided_workspace(tmp_path, monkeypatch, capsys) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    called_with: list[Path] = []

    def fake_doctor_status(workspace_arg: Path) -> DoctorStatus:
        called_with.append(workspace_arg)
        return DoctorStatus(ok=True, workspace=workspace_arg, checks={}, messages=[])

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "doctor_status", fake_doctor_status)

    exit_code = cli.main(["doctor", "--workspace", str(workspace)])

    assert exit_code == 0
    assert called_with == [workspace]
    assert capsys.readouterr().out == "ok\n"


def test_main_unknown_command_returns_error(capsys) -> None:
    exit_code = cli.main(["unknown"])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "usage:" in captured.err
    assert "unknown" in captured.err
