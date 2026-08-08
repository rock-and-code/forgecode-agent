"""Shared pytest fixtures for ForgeCode Agent MVP Slice 1.

These fixtures exercise the public production API and intentionally avoid
private test doubles so behavior stays grounded in package code.
"""

from __future__ import annotations

import pytest

from forgecode_agent.ledger import RunLedger
from forgecode_agent.models import AssistantMessage, FakeModelProvider, ToolIntent
from forgecode_agent.policy import ApprovalPolicy, ApprovalMode
from forgecode_agent.tools import ToolDefinition, ToolRegistry


@pytest.fixture
def read_file_tool() -> ToolDefinition:
    return ToolDefinition(
        name="read_file",
        risk="read_only",
        description="Read a UTF-8 text file from the workspace.",
        parameters={"type": "object", "required": ["path"], "properties": {"path": {"type": "string"}}},
        handler=lambda path: {"path": path, "content": "# ForgeCode\nMinimal fixture README.\n"},
    )


@pytest.fixture
def read_only_registry(read_file_tool: ToolDefinition) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(read_file_tool)
    return registry


@pytest.fixture
def auto_read_policy() -> ApprovalPolicy:
    return ApprovalPolicy(mode=ApprovalMode.SUPERVISED, approved_actions=set())


@pytest.fixture
def run_ledger() -> RunLedger:
    return RunLedger(run_id="test-run-001")


@pytest.fixture
def scripted_read_then_answer_model() -> FakeModelProvider:
    return FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to inspect the README first.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})],
            ),
            AssistantMessage(content="README.md says this is the minimal fixture project."),
        ]
    )
