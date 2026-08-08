from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


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
