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
            parameters={"type": "object"},
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
