from __future__ import annotations

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
