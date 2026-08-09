from __future__ import annotations

import json

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
