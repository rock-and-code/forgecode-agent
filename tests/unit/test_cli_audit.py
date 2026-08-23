from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from forgecode_agent import cli


def test_audit_rejects_zero_limit_as_golden_error_transcript(capsys) -> None:
    golden_transcript = (
        Path(__file__).parents[1] / "golden" / "audit_limit_zero_invalid.txt"
    ).read_text(encoding="utf-8")

    assert cli.main(["audit", "--audit-log", "audit.jsonl", "--limit", "0"]) == 2

    captured = capsys.readouterr()
    assert captured.out + captured.err == golden_transcript


def test_audit_rejects_non_integer_limit_as_golden_error_transcript(capsys) -> None:
    golden_transcript = (
        Path(__file__).parents[1] / "golden" / "audit_limit_non_integer_invalid.txt"
    ).read_text(encoding="utf-8")

    assert cli.main(["audit", "--audit-log", "audit.jsonl", "--limit", "not-an-integer"]) == 2

    captured = capsys.readouterr()
    assert captured.out + captured.err == golden_transcript


def test_audit_prints_last_limit_events_as_golden_sorted_key_jsonl(tmp_path, capsys) -> None:
    audit_log = tmp_path / "audit.jsonl"
    audit_log.write_text(
        "".join(
            json.dumps(event) + "\n"
            for event in [
                {"zeta": "first", "alpha": 1, "event": "old"},
                {"zeta": "second", "alpha": 2, "event": "middle"},
                {"zeta": "last", "alpha": 3, "event": "new"},
            ]
        ),
        encoding="utf-8",
    )
    golden_transcript = (Path(__file__).parents[1] / "golden" / "audit_limit_two.jsonl").read_text(
        encoding="utf-8"
    )

    assert cli.main(["audit", "--audit-log", str(audit_log), "--limit", "2"]) == 0

    assert capsys.readouterr().out == golden_transcript


def test_audit_reports_malformed_json_as_golden_error_transcript(tmp_path, capsys) -> None:
    audit_log = tmp_path / "audit.jsonl"
    audit_log.write_text(
        json.dumps({"event": "valid"}) + "\n" + '{"malformed": "do not disclose"' + "\n",
        encoding="utf-8",
    )
    golden_transcript = (Path(__file__).parents[1] / "golden" / "audit_malformed_json.txt").read_text(
        encoding="utf-8"
    )

    assert cli.main(["audit", "--audit-log", str(audit_log), "--limit", "2"]) == 1

    output = capsys.readouterr().out
    assert output == golden_transcript
    assert "do not disclose" not in output


@pytest.mark.parametrize(
    "non_object_value",
    [
        ["unrelated payload data", {"secret": "do not disclose"}],
        "unrelated payload data",
    ],
    ids=["array", "string"],
)
def test_audit_reports_non_object_json_as_golden_error_transcript_without_traceback(
    non_object_value, tmp_path, capsys, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    audit_log = Path("audit.jsonl")
    audit_log.write_text(
        json.dumps({"event": "valid"})
        + "\n"
        + json.dumps(non_object_value)
        + "\n",
        encoding="utf-8",
    )
    golden_transcript = (
        Path(__file__).parents[1] / "golden" / "audit_non_object_json.txt"
    ).read_text(encoding="utf-8")

    assert cli.main(["audit", "--audit-log", str(audit_log), "--limit", "2"]) == 1

    output = capsys.readouterr().out
    assert output == golden_transcript
    assert "audit event on line 2 is not an object" in output
    assert "Traceback" not in output
    assert "unrelated payload data" not in output
    assert "do not disclose" not in output


def test_audit_reports_invalid_utf8_as_golden_error_transcript_without_traceback(
    tmp_path, capsys
) -> None:
    audit_log = tmp_path / "audit.jsonl"
    audit_log.write_bytes(b"\xff\n")
    golden_transcript = (
        Path(__file__).parents[1] / "golden" / "audit_invalid_utf8.txt"
    ).read_text(encoding="utf-8")

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 1

    output = capsys.readouterr().out
    assert output == golden_transcript
    assert "audit log unavailable" in output
    assert "Traceback" not in output
    assert b"\xff\n" not in output.encode("utf-8")


def test_audit_uses_small_default_limit(tmp_path, capsys) -> None:
    audit_log = tmp_path / "audit.jsonl"
    events = [{"number": number} for number in range(6)]
    audit_log.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 0

    assert capsys.readouterr().out == "".join(json.dumps(event) + "\n" for event in events[-5:])


def test_audit_reports_missing_log_as_golden_error_transcript_without_creating_it(
    tmp_path, capsys, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    audit_log = Path("missing.jsonl")
    golden_transcript = (Path(__file__).parents[1] / "golden" / "audit_missing_log.txt").read_text(
        encoding="utf-8"
    )

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 1

    assert capsys.readouterr().out == golden_transcript
    assert not audit_log.exists()


def test_audit_reports_directory_log_as_golden_error_transcript(tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    audit_log = Path("audit.jsonl")
    audit_log.mkdir()
    golden_transcript = (
        Path(__file__).parents[1] / "golden" / "audit_directory_log.txt"
    ).read_text(encoding="utf-8")

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 1

    assert capsys.readouterr().out == golden_transcript


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


def test_audit_rejects_symlink_log_as_golden_error_transcript(tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = Path("secret.jsonl")
    audit_log = Path("audit.jsonl")
    target.write_text(json.dumps({"secret": "do not disclose"}) + "\n", encoding="utf-8")
    audit_log.symlink_to(target)
    golden_transcript = (Path(__file__).parents[1] / "golden" / "audit_symlink_log.txt").read_text(
        encoding="utf-8"
    )

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 1

    output = capsys.readouterr().out
    output = re.sub(r"\[Errno \d+\]", "[Errno <platform>]", output)
    assert output == golden_transcript
    assert "do not disclose" not in output


def test_audit_reports_symlink_loop_parent_as_golden_error_transcript_without_traceback(
    tmp_path, capsys, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "absolute", lambda path: path)
    loop = Path("loop")
    loop.symlink_to(loop, target_is_directory=True)
    audit_log = loop / "audit.jsonl"
    golden_transcript = (
        Path(__file__).parents[1] / "golden" / "audit_symlink_loop_parent.txt"
    ).read_text(encoding="utf-8")

    assert cli.main(["audit", "--audit-log", str(audit_log)]) == 1

    output = capsys.readouterr().out
    output = re.sub(r"\[Errno \d+\]", "[Errno <platform>]", output)
    assert output == golden_transcript
    assert "audit log unavailable" in output
    assert "Traceback" not in output
