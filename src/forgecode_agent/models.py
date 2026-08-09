from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolIntent:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class AssistantMessage:
    content: str = ""
    tool_intents: list[ToolIntent] = field(default_factory=list)


class FakeModelProvider:
    def __init__(self, script: list[AssistantMessage]) -> None:
        self.script = list(script)
        self.requests: list[dict[str, Any]] = []
        self._cursor = 0

    def complete(self, *, messages: list[dict[str, Any]]) -> AssistantMessage:
        self.requests.append({"messages": deepcopy(messages)})
        if self._cursor >= len(self.script):
            raise IndexError("FakeModelProvider script exhausted")
        response = self.script[self._cursor]
        self._cursor += 1
        return response
