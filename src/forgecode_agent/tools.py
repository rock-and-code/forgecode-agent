from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from forgecode_agent.policy import ApprovalPolicy


class ToolCallDenied(RuntimeError):
    def __init__(self, message: str, *, reason: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason


class ToolExecutionError(RuntimeError):
    def __init__(self, tool_name: str, error_type: str) -> None:
        super().__init__("tool execution failed")
        self.tool_name = tool_name
        self.error_type = error_type


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
        self.validate_arguments(name, arguments)

        tool = self._tools.get(name)
        if tool is None:
            raise ToolCallDenied(f"Unknown tool: {name}", reason="unknown_tool")

        if self.approval_policy is not None:
            decision = self.approval_policy.decide(tool_name=name, risk=tool.risk, arguments=arguments)
            if not decision.allowed:
                self.calls.append({"tool": name, "arguments": arguments, "status": "denied", "reason": decision.reason})
                detail = "requires approval" if decision.requires_approval else decision.reason
                raise ToolCallDenied(f"Tool call denied: {name} {detail}", reason=decision.reason)

        try:
            if _root_arguments_should_be_passed_as_single_value(tool.parameters, arguments):
                result = tool.handler(arguments)
            else:
                result = tool.handler(**arguments)
        except Exception as exc:
            error_type = type(exc).__name__
            self.calls.append(
                {
                    "tool": name,
                    "arguments": arguments,
                    "status": "failed",
                    "reason": "tool_error",
                    "error_type": error_type,
                }
            )
            raise ToolExecutionError(name, error_type) from exc
        self.calls.append({"tool": name, "arguments": arguments, "status": "completed"})
        return result

    def validate_arguments(self, name: str, arguments: Any) -> None:
        tool = self._tools.get(name)
        if tool is None:
            self.calls.append({"tool": name, "arguments": arguments, "status": "denied", "reason": "unknown_tool"})
            raise ToolCallDenied(f"Unknown tool: {name}", reason="unknown_tool")

        if not _arguments_match_schema(tool.parameters, arguments):
            self.calls.append({"tool": name, "arguments": arguments, "status": "denied", "reason": "invalid_arguments"})
            raise ToolCallDenied(f"Tool call denied: {name} invalid_arguments", reason="invalid_arguments")

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def clone_empty_history(self) -> "ToolRegistry":
        clone = ToolRegistry(approval_policy=self.approval_policy)
        for tool in self._tools.values():
            clone.register(tool)
        return clone


def _arguments_match_schema(schema: dict[str, Any], arguments: Any) -> bool:
    if "const" in schema and not _value_matches_const(arguments, schema["const"]):
        return False
    expected_type = schema.get("type")
    if expected_type is None:
        return _object_matches_schema(arguments, schema)
    if _schema_type_includes(expected_type, {"array"}) and isinstance(arguments, list):
        return _array_matches_schema(arguments, schema)
    if _schema_type_includes(expected_type, {"object"}) and isinstance(arguments, dict):
        return _object_matches_schema(arguments, schema)
    return _value_matches_schema(arguments, schema)


def _root_arguments_should_be_passed_as_single_value(schema: dict[str, Any], arguments: Any) -> bool:
    return schema.get("type") == "array" or not isinstance(arguments, dict)


def _array_matches_schema(value: Any, schema: dict[str, Any]) -> bool:
    if not isinstance(value, list):
        return False
    if "minItems" in schema and len(value) < schema["minItems"]:
        return False
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        return False
    if schema.get("uniqueItems") is True and not _array_items_are_unique(value):
        return False
    item_schema = schema.get("items", {})
    return all(_value_matches_schema(item, item_schema, enforce_string_pattern=True) for item in value)


def _array_items_are_unique(value: list[Any]) -> bool:
    for index, item in enumerate(value):
        if any(_value_matches_const(item, other) for other in value[index + 1 :]):
            return False
    return True


def _object_matches_schema(value: Any, schema: dict[str, Any]) -> bool:
    if not isinstance(value, dict):
        return False

    for required_name in schema.get("required", []):
        if required_name not in value:
            return False

    properties = schema.get("properties", {})
    additional_properties = schema.get("additionalProperties", False)

    for name, item in value.items():
        if name in properties:
            property_schema = properties[name]
        elif additional_properties is True:
            property_schema = {}
        elif isinstance(additional_properties, dict):
            property_schema = additional_properties
        else:
            return False

        if not _value_matches_schema(item, property_schema, enforce_string_pattern=True):
            return False

    return True


def _value_matches_schema(value: Any, schema: dict[str, Any], *, enforce_string_pattern: bool = False) -> bool:
    if "const" in schema and not _value_matches_const(value, schema["const"]):
        return False

    expected_type = schema.get("type")
    if _schema_type_includes(expected_type, {"array"}) and isinstance(value, list):
        return _array_matches_schema(value, schema)
    if _schema_type_includes(expected_type, {"object"}) and isinstance(value, dict):
        if _is_bare_object_schema(schema):
            return _value_matches_type(value, expected_type)
        return _object_matches_schema(value, schema)

    if not _value_matches_type(value, expected_type):
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if (
        _schema_type_includes(expected_type, {"integer", "number"})
        and _value_matches_type(value, "number")
        and "minimum" in schema
        and value < schema["minimum"]
    ):
        return False
    if (
        _schema_type_includes(expected_type, {"integer", "number"})
        and _value_matches_type(value, "number")
        and "maximum" in schema
        and value > schema["maximum"]
    ):
        return False
    if (
        _schema_type_includes(expected_type, {"string"})
        and _value_matches_type(value, "string")
        and "minLength" in schema
        and len(value) < schema["minLength"]
    ):
        return False
    if (
        _schema_type_includes(expected_type, {"string"})
        and _value_matches_type(value, "string")
        and "maxLength" in schema
        and len(value) > schema["maxLength"]
    ):
        return False
    if (
        enforce_string_pattern
        and _schema_type_includes(expected_type, {"string"})
        and _value_matches_type(value, "string")
        and "pattern" in schema
        and re.search(schema["pattern"], value) is None
    ):
        return False

    return True


def _is_bare_object_schema(schema: dict[str, Any]) -> bool:
    return (
        _schema_type_includes(schema.get("type"), {"object"})
        and "properties" not in schema
        and "required" not in schema
        and "additionalProperties" not in schema
    )


def _schema_type_includes(expected_type: Any, type_names: set[str]) -> bool:
    if isinstance(expected_type, list):
        return any(type_name in type_names for type_name in expected_type)
    return expected_type in type_names


def _value_matches_type(value: Any, expected_type: Any) -> bool:
    if isinstance(expected_type, list):
        return any(_value_matches_type(value, type_name) for type_name in expected_type)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return True


def _value_matches_const(value: Any, const: Any) -> bool:
    if type(value) is not type(const):
        return False
    if isinstance(value, dict):
        if value.keys() != const.keys():
            return False
        return all(_value_matches_const(value[key], const[key]) for key in value)
    if isinstance(value, list):
        if len(value) != len(const):
            return False
        return all(_value_matches_const(item, const_item) for item, const_item in zip(value, const))
    return value == const
