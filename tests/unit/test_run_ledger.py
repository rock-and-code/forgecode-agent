from __future__ import annotations

import json

import pytest

from forgecode_agent.ledger import RunLedger


def test_append_defensively_copies_event_data() -> None:
    ledger = RunLedger(run_id="mutation-test")
    payload = {"nested": {"items": ["original"]}}

    event = ledger.append("payload_recorded", payload)
    payload["nested"]["items"].append("mutated")

    assert event.data == {"nested": {"items": ["original"]}}
    assert ledger.events[0].data == {"nested": {"items": ["original"]}}


def test_write_jsonl_persists_ordered_events_with_run_id_and_stable_keys(tmp_path) -> None:
    ledger = RunLedger(run_id="jsonl-test")
    ledger.append("run_started", {"goal": "test"})
    ledger.append("run_completed", {"completed": True})

    output_path = tmp_path / "nested" / "run.jsonl"
    ledger.write_jsonl(output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()

    assert lines == [
        '{"data":{"goal":"test"},"run_id":"jsonl-test","timestamp":0,"type":"run_started"}',
        '{"data":{"completed":true},"run_id":"jsonl-test","timestamp":1,"type":"run_completed"}',
    ]
    assert [json.loads(line)["type"] for line in lines] == ["run_started", "run_completed"]


def test_read_jsonl_reloads_persisted_events_in_file_order(tmp_path) -> None:
    ledger = RunLedger(run_id="reload-test")
    ledger.append("run_started", {"goal": "reload"})
    ledger.append("run_completed", {"completed": True, "items": [1, 2]})
    output_path = tmp_path / "run.jsonl"
    ledger.write_jsonl(output_path)

    reloaded = RunLedger.read_jsonl(output_path)

    assert reloaded.run_id == "reload-test"
    assert [event.type for event in reloaded.events] == ["run_started", "run_completed"]
    assert [event.data for event in reloaded.events] == [
        {"goal": "reload"},
        {"completed": True, "items": [1, 2]},
    ]
    assert [event.timestamp for event in reloaded.events] == [0, 1]


def test_read_jsonl_rejects_empty_files(tmp_path) -> None:
    output_path = tmp_path / "empty.jsonl"
    output_path.write_text("", encoding="utf-8")

    try:
        RunLedger.read_jsonl(output_path)
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for empty JSONL ledger")


def test_read_jsonl_rejects_mixed_run_ids(tmp_path) -> None:
    output_path = tmp_path / "mixed.jsonl"
    output_path.write_text(
        "\n".join(
            [
                json.dumps({"type": "one", "data": {}, "timestamp": 0, "run_id": "first"}),
                json.dumps({"type": "two", "data": {}, "timestamp": 1, "run_id": "second"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        RunLedger.read_jsonl(output_path)
    except ValueError as exc:
        assert "mixed" in str(exc).lower() or "same run_id" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for mixed run_id JSONL ledger")


def test_read_jsonl_rejects_non_contiguous_timestamps_in_file_order(tmp_path) -> None:
    output_path = tmp_path / "non-contiguous.jsonl"
    output_path.write_text(
        "\n".join(
            [
                json.dumps({"type": "one", "data": {}, "timestamp": 0, "run_id": "same"}),
                json.dumps({"type": "two", "data": {}, "timestamp": 2, "run_id": "same"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        RunLedger.read_jsonl(output_path)
    except ValueError as exc:
        message = str(exc).lower()
        assert "timestamp" in message and ("order" in message or "contiguous" in message)
    else:
        raise AssertionError("Expected ValueError for non-contiguous JSONL ledger timestamps")


@pytest.mark.parametrize("missing_key", ["type", "data", "timestamp", "run_id"])
def test_read_jsonl_rejects_rows_missing_required_keys(tmp_path, missing_key: str) -> None:
    output_path = tmp_path / f"missing-{missing_key}.jsonl"
    row = {"type": "one", "data": {}, "timestamp": 0, "run_id": "same"}
    del row[missing_key]
    output_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="(?i)(missing|required).*key"):
        RunLedger.read_jsonl(output_path)


@pytest.mark.parametrize("row", [["not", "object"], "not-object", 42])
def test_read_jsonl_rejects_non_object_rows(tmp_path, row: object) -> None:
    output_path = tmp_path / "non-object.jsonl"
    output_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="(?i)(object|row|jsonl)"):
        RunLedger.read_jsonl(output_path)


@pytest.mark.parametrize(
    ("field", "value", "expected_type"),
    [
        ("type", 123, "string"),
        ("data", [], "object"),
        ("timestamp", "0", "int"),
        ("timestamp", True, "int"),
        ("run_id", 123, "string"),
    ],
)
def test_read_jsonl_rejects_malformed_required_field_types(
    tmp_path, field: str, value: object, expected_type: str
) -> None:
    output_path = tmp_path / f"malformed-{field}.jsonl"
    row = {"type": "one", "data": {}, "timestamp": 0, "run_id": "same"}
    row[field] = value
    output_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        RunLedger.read_jsonl(output_path)

    message = str(exc_info.value).lower()
    assert "row 0" in message
    assert field in message
    assert expected_type in message


def test_write_jsonl_redacts_default_secret_keys_recursively_without_mutating_events(tmp_path) -> None:
    ledger = RunLedger(run_id="redaction-test")
    sensitive_payload = {
        "api_key": "live-api-key",
        "authorization": "bearer live-authorization",
        "auth": "live-auth",
        "service_credential": "live-credential",
        "private_key": "live-private-key",
        "access_key": "live-access-key",
        "AuthToken": "live-token",
        "user_password_hint": "live-password",
        "nested": {
            "secret_value": "live-secret",
            "items": [
                {"dbPasswd": "live-passwd"},
                ({"authorization": "nested bearer token"}, {"token": "tuple-token"}),
                {"note": "safe", "not_secreted": "contains default fragment and is redacted"},
            ],
        },
        "safe": "visible",
    }
    ledger.append("model_requested", sensitive_payload)

    ledger.write_jsonl(tmp_path / "run.jsonl")

    row = json.loads((tmp_path / "run.jsonl").read_text(encoding="utf-8"))
    assert row["data"] == {
        "api_key": "[REDACTED]",
        "authorization": "[REDACTED]",
        "auth": "[REDACTED]",
        "service_credential": "[REDACTED]",
        "private_key": "[REDACTED]",
        "access_key": "[REDACTED]",
        "AuthToken": "[REDACTED]",
        "user_password_hint": "[REDACTED]",
        "nested": {
            "secret_value": "[REDACTED]",
            "items": [
                {"dbPasswd": "[REDACTED]"},
                [{"authorization": "[REDACTED]"}, {"token": "[REDACTED]"}],
                {"note": "safe", "not_secreted": "[REDACTED]"},
            ],
        },
        "safe": "visible",
    }
    assert ledger.events[0].data == sensitive_payload


def test_write_jsonl_redacts_secret_looking_string_values_without_mutating_events(tmp_path) -> None:
    ledger = RunLedger(run_id="value-redaction-test")
    payload = {
        "headers": {"scheme": "Bearer abcdef"},
        "metadata": ["visible", "Bearer token123", {"public_key_value": "sk-abcdef"}],
        "tuple_values": ("sk-123456", "Bearer short", "sk-short"),
        "safe": "Bearer abcde",
        "also_safe": "prefix sk-abcdef",
    }
    ledger.append("tool_call_requested", payload)

    ledger.write_jsonl(tmp_path / "run.jsonl")

    row = json.loads((tmp_path / "run.jsonl").read_text(encoding="utf-8"))
    assert row["data"] == {
        "headers": {"scheme": "[REDACTED]"},
        "metadata": ["visible", "[REDACTED]", {"public_key_value": "[REDACTED]"}],
        "tuple_values": ["[REDACTED]", "Bearer short", "sk-short"],
        "safe": "Bearer abcde",
        "also_safe": "prefix sk-abcdef",
    }
    assert ledger.events[0].data == payload


def test_write_jsonl_redacts_bearer_scheme_case_insensitively(tmp_path) -> None:
    ledger = RunLedger(run_id="bearer-case-redaction-test")
    payload = {
        "lowercase_bearer": "bearer abcdef",
        "uppercase_bearer": "BEARER abcdef",
        "short_lowercase_bearer": "bearer abcde",
        "uppercase_sk_is_not_redacted": "SK-abcdef",
    }
    ledger.append("tool_call_requested", payload)

    ledger.write_jsonl(tmp_path / "run.jsonl")

    row = json.loads((tmp_path / "run.jsonl").read_text(encoding="utf-8"))
    assert row["data"] == {
        "lowercase_bearer": "[REDACTED]",
        "uppercase_bearer": "[REDACTED]",
        "short_lowercase_bearer": "bearer abcde",
        "uppercase_sk_is_not_redacted": "SK-abcdef",
    }
    assert ledger.events[0].data == payload


def test_write_jsonl_uses_custom_redact_keys_additively_with_defaults(tmp_path) -> None:
    ledger = RunLedger(run_id="custom-redaction-test")
    ledger.append(
        "tool_call_requested",
        {
            "project_code": "custom secret",
            "token": "still redacted when custom key is configured",
            "password": "still redacted when custom key is configured",
            "metadata": [{"label": "public"}],
        },
    )

    ledger.write_jsonl(tmp_path / "run.jsonl", redact_keys={"project_code"})

    row = json.loads((tmp_path / "run.jsonl").read_text(encoding="utf-8"))
    assert row["data"] == {
        "project_code": "[REDACTED]",
        "token": "[REDACTED]",
        "password": "[REDACTED]",
        "metadata": [{"label": "public"}],
    }
