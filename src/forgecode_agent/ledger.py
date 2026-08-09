from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_REDACT_KEYS = {
    "access_key",
    "api_key",
    "auth",
    "authorization",
    "credential",
    "passwd",
    "password",
    "private_key",
    "secret",
    "token",
}
REDACTED_VALUE = "[REDACTED]"


def _looks_like_secret_string(value: str) -> bool:
    bearer_prefix = "Bearer "
    if value.lower().startswith(bearer_prefix.lower()):
        candidate = value[len(bearer_prefix) : len(bearer_prefix) + 6]
        return len(candidate) == 6 and all(not char.isspace() for char in candidate)

    sk_prefix = "sk-"
    if value.startswith(sk_prefix):
        candidate = value[len(sk_prefix) : len(sk_prefix) + 6]
        return len(candidate) == 6 and all(not char.isspace() for char in candidate)
    return False


def _redact(value: Any, redact_keys: Iterable[str]) -> Any:
    key_fragments = tuple(fragment.lower() for fragment in redact_keys)
    if isinstance(value, dict):
        return {
            key: REDACTED_VALUE if any(fragment in str(key).lower() for fragment in key_fragments) else _redact(item, key_fragments)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item, key_fragments) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact(item, key_fragments) for item in value)
    if isinstance(value, str) and _looks_like_secret_string(value):
        return REDACTED_VALUE
    return value


@dataclass(frozen=True)
class LedgerEvent:
    type: str
    data: dict[str, Any]
    timestamp: int

    def to_dict(self, *, exclude: set[str] | None = None) -> dict[str, Any]:
        exclude = exclude or set()
        event = {"type": self.type, "data": self.data, "timestamp": self.timestamp}
        return {key: value for key, value in event.items() if key not in exclude}


@dataclass
class RunLedger:
    run_id: str

    def __post_init__(self) -> None:
        self.events: list[LedgerEvent] = []

    def append(self, event_type: str, data: dict[str, Any] | None = None) -> LedgerEvent:
        event = LedgerEvent(type=event_type, data=deepcopy(data) if data is not None else {}, timestamp=len(self.events))
        self.events.append(event)
        return event

    @classmethod
    def read_jsonl(cls, path: str | Path) -> RunLedger:
        input_path = Path(path)
        rows = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line]
        if not rows:
            raise ValueError("Cannot read empty JSONL ledger")

        required_keys = {"type", "data", "timestamp", "run_id"}
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"JSONL ledger row {index} must be an object")
            missing_keys = required_keys - row.keys()
            if missing_keys:
                missing = ", ".join(sorted(missing_keys))
                raise ValueError(f"JSONL ledger row {index} missing required key(s): {missing}")
            if not isinstance(row["type"], str):
                raise ValueError(f"JSONL ledger row {index} field 'type' must be a string")
            if not isinstance(row["data"], dict):
                raise ValueError(f"JSONL ledger row {index} field 'data' must be an object")
            if not isinstance(row["timestamp"], int) or isinstance(row["timestamp"], bool):
                raise ValueError(f"JSONL ledger row {index} field 'timestamp' must be an int")
            if not isinstance(row["run_id"], str):
                raise ValueError(f"JSONL ledger row {index} field 'run_id' must be a string")

        run_id = rows[0]["run_id"]
        if any(row["run_id"] != run_id for row in rows):
            raise ValueError("Cannot read JSONL ledger with mixed run_id rows")
        if [row["timestamp"] for row in rows] != list(range(len(rows))):
            raise ValueError("Cannot read JSONL ledger with non-contiguous timestamps in file order")

        ledger = cls(run_id=run_id)
        ledger.events = [LedgerEvent(type=row["type"], data=row["data"], timestamp=row["timestamp"]) for row in rows]
        return ledger

    def write_jsonl(self, path: str | Path, *, redact_keys: set[str] | None = None) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        key_fragments = DEFAULT_REDACT_KEYS if redact_keys is None else DEFAULT_REDACT_KEYS | redact_keys
        with output_path.open("w", encoding="utf-8") as file:
            for event in self.events:
                row = event.to_dict() | {"run_id": self.run_id}
                row["data"] = _redact(row["data"], key_fragments)
                file.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
