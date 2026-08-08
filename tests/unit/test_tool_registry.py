from __future__ import annotations

import pytest

from forgecode_agent.policy import ApprovalPolicy, ApprovalMode
from forgecode_agent.tools import ToolCallDenied, ToolDefinition, ToolRegistry


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
