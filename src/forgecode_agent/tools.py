from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from forgecode_agent.policy import ApprovalPolicy


class ToolCallDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    risk: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]


@dataclass
class ToolRegistry:
    approval_policy: ApprovalPolicy | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def execute(self, name: str, arguments: Any) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            self.calls.append({"tool": name, "arguments": arguments, "status": "denied", "reason": "unknown_tool"})
            raise ToolCallDenied(f"Unknown tool: {name}")

        if not _arguments_match_schema(tool.parameters, arguments):
            self.calls.append({"tool": name, "arguments": arguments, "status": "denied", "reason": "invalid_arguments"})
            raise ToolCallDenied(f"Tool call denied: {name} invalid_arguments")

        if self.approval_policy is not None:
            decision = self.approval_policy.decide(tool_name=name, risk=tool.risk, arguments=arguments)
            if not decision.allowed:
                self.calls.append({"tool": name, "arguments": arguments, "status": "denied", "reason": decision.reason})
                detail = "requires approval" if decision.requires_approval else decision.reason
                raise ToolCallDenied(f"Tool call denied: {name} {detail}")

        result = tool.handler(**arguments)
        self.calls.append({"tool": name, "arguments": arguments, "status": "completed"})
        return result

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def clone_empty_history(self) -> "ToolRegistry":
        clone = ToolRegistry(approval_policy=self.approval_policy)
        for tool in self._tools.values():
            clone.register(tool)
        return clone


def _arguments_match_schema(schema: dict[str, Any], arguments: Any) -> bool:
    if not isinstance(arguments, dict):
        return False

    for required_name in schema.get("required", []):
        if required_name not in arguments:
            return False

    properties = schema.get("properties", {})
    if schema.get("additionalProperties") is not True:
        for name in arguments:
            if name not in properties:
                return False

    for name, value in arguments.items():
        expected_type = properties.get(name, {}).get("type")
        if expected_type == "string" and not isinstance(value, str):
            return False

    return True
