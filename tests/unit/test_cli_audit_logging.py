from __future__ import annotations

import json
import os
from pathlib import Path

from forgecode_agent import cli


def read_events(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def read_event(path: Path) -> dict[str, object]:
    return read_events(path)[-1]


def test_main_writes_jsonl_audit_event_for_successful_command(tmp_path, monkeypatch, capsys) -> None:
    audit_log = tmp_path / "audit.jsonl"
    monkeypatch.setattr(cli, "_audit_timestamp", lambda: "2026-01-01T00:00:00+00:00")

    exit_code = cli.main(["status", "--workspace", str(tmp_path), "--audit-log", str(audit_log)])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "workspace: ok\nconfig: missing\nmodel_provider: none\nactive_task: none\n"
    )
    event = read_event(audit_log)
    assert event == {
        "command": "status",
        "action": "status",
        "outcome": "success",
        "timestamp": "2026-01-01T00:00:00+00:00",
    }


def test_main_writes_jsonl_audit_event_for_failed_command(tmp_path, capsys) -> None:
    audit_log = tmp_path / "audit.jsonl"

    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--audit-log", str(audit_log)])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"
    assert read_event(audit_log)["command"] == "config"
    assert read_event(audit_log)["action"] == "config"
    assert read_event(audit_log)["outcome"] == "failure"


def test_audit_log_failure_does_not_replace_command_result(tmp_path, monkeypatch, capsys) -> None:
    audit_log = tmp_path / "audit.jsonl"

    def fail_write(*args, **kwargs):
        raise OSError("audit unavailable")

    monkeypatch.setattr(cli, "_write_audit_event", fail_write)

    exit_code = cli.main(["config", "--workspace", str(tmp_path), "--audit-log", str(audit_log)])

    assert exit_code == 1
    assert capsys.readouterr().out == "config: missing\n"


def test_audit_log_supports_equals_syntax_and_appends_records(tmp_path, monkeypatch) -> None:
    audit_log = tmp_path / "audit.jsonl"
    monkeypatch.setattr(cli, "_audit_timestamp", lambda: "fixed")

    assert cli.main(["status", "--workspace", str(tmp_path), f"--audit-log={audit_log}"]) == 0
    assert cli.main(["status", "--workspace", str(tmp_path), "--audit-log", str(audit_log)]) == 0

    events = read_events(audit_log)
    assert len(events) == 2
    assert all(event["command"] == "status" for event in events)


def test_repeated_audit_log_uses_argparse_final_value(tmp_path, monkeypatch) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    monkeypatch.setattr(cli, "_audit_timestamp", lambda: "fixed")

    assert cli.main([
        "status", "--workspace", str(tmp_path), "--audit-log", str(first), "--audit-log", str(second)
    ]) == 0

    assert not first.exists()
    assert len(read_events(second)) == 1


def test_symlink_audit_destination_is_not_followed(tmp_path) -> None:
    target = tmp_path / "target.jsonl"
    link = tmp_path / "audit.jsonl"
    link.symlink_to(target)

    assert cli.main(["status", "--workspace", str(tmp_path), "--audit-log", str(link)]) == 0
    assert not target.exists()


def test_symlinked_audit_parent_is_not_followed(tmp_path) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    link_parent = tmp_path / "audit-parent"
    link_parent.symlink_to(real_parent, target_is_directory=True)

    assert cli.main([
        "status", "--workspace", str(tmp_path), "--audit-log", str(link_parent / "audit.jsonl")
    ]) == 0
    assert not (real_parent / "audit.jsonl").exists()


def test_audit_logging_fails_closed_without_no_follow(tmp_path, monkeypatch, capsys) -> None:
    target = tmp_path / "target.jsonl"
    target.write_text("sentinel\n", encoding="utf-8")
    audit_log = tmp_path / "audit.jsonl"
    audit_log.symlink_to(target)
    monkeypatch.delattr(cli.os, "O_NOFOLLOW", raising=False)

    assert cli.main(["status", "--workspace", str(tmp_path), "--audit-log", str(audit_log)]) == 0
    assert capsys.readouterr().out == (
        "workspace: ok\nconfig: missing\nmodel_provider: none\nactive_task: none\n"
    )
    assert target.read_text(encoding="utf-8") == "sentinel\n"


def test_special_audit_destination_does_not_block(tmp_path) -> None:
    fifo = tmp_path / "audit.pipe"
    os.mkfifo(fifo)

    assert cli.main(["status", "--workspace", str(tmp_path), "--audit-log", str(fifo)]) == 0
    assert fifo.is_fifo()


def test_non_oserror_audit_failure_does_not_replace_command_result(tmp_path, monkeypatch, capsys) -> None:
    def fail_write(*args, **kwargs):
        raise UnicodeEncodeError("ascii", "x", 0, 1, "audit unavailable")

    monkeypatch.setattr(cli, "_write_audit_event", fail_write)

    assert cli.main(["config", "--workspace", str(tmp_path), "--audit-log", str(tmp_path / "audit")]) == 1
    assert capsys.readouterr().out == "config: missing\n"
