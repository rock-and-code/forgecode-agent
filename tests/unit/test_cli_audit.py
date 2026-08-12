from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from forgecode_agent import cli


def test_audit_prints_most_recent_events_in_jsonl_order(tmp_path, capsys) -> None:
    audit_log = tmp_path / "audit.jsonl"
    events = [
        {"command": "status", "outcome": "success", "timestamp": "one"},
        {"command": "config", "outcome": "failure", "timestamp": "two"},
        {"command": "doctor", "outcome": "success", "timestamp": "three"},
    ]
    audit_log.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    assert cli.main(["audit", "--audit-log", str(audit_log), "--limit", "2"]) == 0

    assert capsys.readouterr().out == "".join(json.dumps(event) + "\n" for event in events[-2:])


def test_audit_uses_small_default_limit(tmp_path, capsys) -> None:
    audit_log = tmp_path / "audit.jsonl"
    events = [{"number": number} for number in range(6)]
    audit_log.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 0

    assert capsys.readouterr().out == "".join(json.dumps(event) + "\n" for event in events[-5:])


def test_audit_reports_missing_log_without_creating_or_auditing_it(tmp_path, capsys) -> None:
    audit_log = tmp_path / "missing.jsonl"

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 1

    assert capsys.readouterr().out == f"audit log missing: {audit_log}\n"
    assert not audit_log.exists()


def test_audit_tail_does_not_read_entire_file_into_memory(tmp_path, monkeypatch) -> None:
    audit_log = tmp_path / "audit.jsonl"
    audit_log.write_text(json.dumps({"number": 1}) + "\n", encoding="utf-8")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("audit viewer must stream the file")

    monkeypatch.setattr(type(audit_log), "read_text", fail_if_called)

    assert cli._read_audit_events(audit_log, 1) == [{"number": 1}]


def test_audit_reads_log_through_canonicalized_parent_path(tmp_path, capsys) -> None:
    real_parent = tmp_path / "real"
    symlinked_parent = tmp_path / "linked"
    real_parent.mkdir()
    symlinked_parent.symlink_to(real_parent, target_is_directory=True)
    audit_log = symlinked_parent / "audit.jsonl"
    audit_log.write_text(json.dumps({"ok": True}) + "\n", encoding="utf-8")

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 0

    assert capsys.readouterr().out == json.dumps({"ok": True}) + "\n"


def test_audit_rejects_fifo_without_blocking(tmp_path) -> None:
    audit_log = tmp_path / "audit.jsonl"
    if not hasattr(os, "mkfifo"):
        return
    os.mkfifo(audit_log)

    result = subprocess.run(
        [sys.executable, "-c", "from forgecode_agent import cli; raise SystemExit(cli.main(__import__('sys').argv[1:]))", "audit", "--audit-log", str(audit_log)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=2,
        env={"PYTHONPATH": str(Path(__file__).parents[2] / "src")},
    )

    assert result.returncode == 1
    assert "regular file" in result.stdout


def test_audit_rejects_symlink_log(tmp_path, capsys) -> None:
    target = tmp_path / "secret.jsonl"
    audit_log = tmp_path / "audit.jsonl"
    target.write_text(json.dumps({"secret": "do not disclose"}) + "\n", encoding="utf-8")
    audit_log.symlink_to(target)

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 1

    output = capsys.readouterr().out
    assert "do not disclose" not in output
    assert "audit log unavailable" in output or "audit log missing" in output


def test_audit_reports_symlink_loop_parent_without_traceback(tmp_path, capsys) -> None:
    loop = tmp_path / "loop"
    loop.symlink_to(loop, target_is_directory=True)
    audit_log = loop / "audit.jsonl"

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 1

    output = capsys.readouterr().out
    assert "audit log unavailable" in output
    assert "Traceback" not in output
