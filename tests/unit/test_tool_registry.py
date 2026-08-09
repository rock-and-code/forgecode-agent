from __future__ import annotations

import pytest

from forgecode_agent.policy import ApprovalPolicy, ApprovalMode
from forgecode_agent.tools import (
    ToolCallDenied,
    ToolDefinition,
    ToolExecutionError,
    ToolRegistry,
)


def test_tool_registry_executes_only_registered_tools(read_file_tool: ToolDefinition) -> None:
    registry = ToolRegistry()
    registry.register(read_file_tool)

    result = registry.execute("read_file", {"path": "README.md"})

    assert result == {"path": "README.md", "content": "# ForgeCode\nMinimal fixture README.\n"}
    assert registry.calls == [
        {"tool": "read_file", "arguments": {"path": "README.md"}, "status": "completed"}
    ]


def test_tool_registry_denies_unknown_tool_names(read_only_registry: ToolRegistry) -> None:
    with pytest.raises(ToolCallDenied, match="Unknown tool: shell"):
        read_only_registry.execute("shell", {"command": "echo should-not-run"})

    assert read_only_registry.calls == [
        {"tool": "shell", "arguments": {"command": "echo should-not-run"}, "status": "denied", "reason": "unknown_tool"}
    ]


def test_tool_registry_applies_approval_policy_before_handler_runs() -> None:
    calls: list[str] = []
    registry = ToolRegistry(
        approval_policy=ApprovalPolicy(mode=ApprovalMode.SUPERVISED, approved_actions=set())
    )
    registry.register(
        ToolDefinition(
            name="write_file",
            risk="write",
            description="Write a file in the workspace.",
            parameters={"type": "object", "additionalProperties": True},
            handler=lambda path, content: calls.append(path),
        )
    )

    with pytest.raises(ToolCallDenied, match="requires approval"):
        registry.execute("write_file", {"path": "README.md", "content": "mutated"})

    assert calls == []
    assert registry.calls[-1] == {
        "tool": "write_file",
        "arguments": {"path": "README.md", "content": "mutated"},
        "status": "denied",
        "reason": "approval_required",
    }


def test_tool_registry_denies_missing_required_arguments_before_handler_runs(
    read_file_tool: ToolDefinition,
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name=read_file_tool.name,
            risk=read_file_tool.risk,
            description=read_file_tool.description,
            parameters=read_file_tool.parameters,
            handler=lambda path: calls.append({"path": path}),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("read_file", {})

    assert calls == []
    assert registry.calls == [
        {"tool": "read_file", "arguments": {}, "status": "denied", "reason": "invalid_arguments"}
    ]


def test_tool_registry_denies_argument_type_mismatch_before_handler_runs(
    read_file_tool: ToolDefinition,
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name=read_file_tool.name,
            risk=read_file_tool.risk,
            description=read_file_tool.description,
            parameters=read_file_tool.parameters,
            handler=lambda path: calls.append({"path": path}),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("read_file", {"path": 123})

    assert calls == []
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": {"path": 123},
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_integer_argument_type_mismatch_before_handler_runs() -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="repeat",
            risk="read_only",
            description="Repeat a message a number of times.",
            parameters={
                "type": "object",
                "properties": {"count": {"type": "integer"}},
                "required": ["count"],
            },
            handler=lambda count: calls.append({"count": count}),
        )
    )
    arguments = {"count": True}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("repeat", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "repeat",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_boolean_argument_type_mismatch_before_handler_runs() -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="set_enabled",
            risk="read_only",
            description="Set enabled state.",
            parameters={
                "type": "object",
                "properties": {"enabled": {"type": "boolean"}},
                "required": ["enabled"],
            },
            handler=lambda enabled: calls.append({"enabled": enabled}),
        )
    )
    arguments = {"enabled": "true"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("set_enabled", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "set_enabled",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("arguments", [None, ["README.md"], "README.md"])
def test_tool_registry_denies_non_dict_arguments_before_handler_runs(
    read_file_tool: ToolDefinition,
    arguments: object,
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name=read_file_tool.name,
            risk=read_file_tool.risk,
            description=read_file_tool.description,
            parameters=read_file_tool.parameters,
            handler=lambda path: calls.append({"path": path}),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("read_file", arguments)  # type: ignore[arg-type]

    assert calls == []
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_dict_for_array_schema_before_handler_runs() -> None:
    calls: list[str] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={"type": "array"},
            handler=lambda: calls.append("ran"),
        )
    )
    arguments: dict[str, object] = {}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_array_item_type_mismatch_before_handler_runs() -> None:
    calls: list[list[object]] = []

    def handler(paths: list[object]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={"type": "array", "items": {"type": "string"}},
            handler=handler,
        )
    )
    arguments = ["README.md", 123]

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("invalid_item", [True, False])
def test_tool_registry_denies_integer_array_item_bool_before_handler_runs(
    invalid_item: bool,
) -> None:
    calls: list[list[object]] = []

    def handler(counts: list[object]) -> dict[str, int]:
        calls.append(counts)
        return {"count": len(counts)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sum_counts",
            risk="read_only",
            description="Sum integer counts.",
            parameters={"type": "array", "items": {"type": "integer"}},
            handler=handler,
        )
    )
    arguments = [1, invalid_item]

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("sum_counts", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "sum_counts",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_boolean_array_item_type_mismatch_before_handler_runs() -> None:
    calls: list[list[object]] = []

    def handler(flags: list[object]) -> dict[str, int]:
        calls.append(flags)
        return {"count": len(flags)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="set_flags",
            risk="read_only",
            description="Set boolean flags.",
            parameters={"type": "array", "items": {"type": "boolean"}},
            handler=handler,
        )
    )
    arguments = [True, "false"]

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("set_flags", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "set_flags",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_executes_array_schema_with_list_as_single_positional_argument() -> None:
    calls: list[list[str]] = []

    def handler(paths: list[str]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={"type": "array"},
            handler=handler,
        )
    )
    arguments = ["README.md", "pyproject.toml"]

    result = registry.execute("batch_read", arguments)

    assert result == {"count": 2}
    assert calls == [arguments]
    assert registry.calls == [
        {"tool": "batch_read", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_wraps_handler_failures_without_leaking_raw_message() -> None:
    def handler(path: str) -> dict[str, str]:
        raise RuntimeError("password=supersecret disk read failed")

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="read_file",
            risk="read_only",
            description="Read a UTF-8 text file from the workspace.",
            parameters={
                "type": "object",
                "required": ["path"],
                "properties": {"path": {"type": "string"}},
            },
            handler=handler,
        )
    )
    arguments = {"path": "README.md"}

    with pytest.raises(ToolExecutionError) as exc_info:
        registry.execute("read_file", arguments)

    assert exc_info.value.tool_name == "read_file"
    assert exc_info.value.error_type == "RuntimeError"
    assert str(exc_info.value) == "tool execution failed"
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": arguments,
            "status": "failed",
            "reason": "tool_error",
            "error_type": "RuntimeError",
        }
    ]
    assert "supersecret" not in repr(registry.calls)


def test_tool_registry_denies_unknown_extra_arguments_before_handler_runs(
    read_file_tool: ToolDefinition,
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name=read_file_tool.name,
            risk=read_file_tool.risk,
            description=read_file_tool.description,
            parameters=read_file_tool.parameters,
            handler=lambda path: calls.append({"path": path}),
        )
    )
    arguments = {"path": "README.md", "extra": "x"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("read_file", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_unknown_arguments_for_object_schema_before_handler_runs() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="ping",
            risk="read_only",
            description="Ping with no arguments.",
            parameters={"type": "object"},
            handler=lambda: calls.append({"called": "yes"}),
        )
    )
    arguments = {"unexpected": "value"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("ping", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "ping",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_unknown_arguments_for_empty_schema_before_handler_runs() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="ping",
            risk="read_only",
            description="Ping with no arguments.",
            parameters={},
            handler=lambda: calls.append({"called": "yes"}),
        )
    )
    arguments = {"unexpected": "value"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("ping", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "ping",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]
