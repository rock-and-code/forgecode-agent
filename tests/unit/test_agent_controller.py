from __future__ import annotations

import pytest

from forgecode_agent.agent import AgentController
from forgecode_agent.ledger import RunLedger
from forgecode_agent.models import AssistantMessage, FakeModelProvider, ToolIntent
from forgecode_agent.policy import ApprovalPolicy
from forgecode_agent.tools import ToolCallDenied, ToolDefinition, ToolRegistry


def test_agent_controller_runs_one_iteration_records_events_and_returns_final_answer(
    scripted_read_then_answer_model: FakeModelProvider,
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
    run_ledger: RunLedger,
) -> None:
    controller = AgentController(
        model_provider=scripted_read_then_answer_model,
        tools=read_only_registry,
        approval_policy=auto_read_policy,
        ledger=run_ledger,
        max_iterations=1,
    )

    result = controller.run(goal="Summarize README.md")

    assert result.final_answer == "README.md says this is the minimal fixture project."
    assert result.completed is True
    assert result.iterations == 1

    assert [event.type for event in run_ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "tool_call_completed",
        "model_requested",
        "model_responded",
        "run_completed",
    ]
    assert run_ledger.events[0].data == {"goal": "Summarize README.md"}
    assert run_ledger.events[3].data == {"tool": "read_file", "arguments": {"path": "README.md"}}
    assert run_ledger.events[4].data == {
        "tool": "read_file",
        "allowed": True,
        "reason": "auto_allowed_read_only",
    }
    assert run_ledger.events[5].data == {
        "tool": "read_file",
        "result": {"path": "README.md", "content": "# ForgeCode\nMinimal fixture README.\n"},
    }


def test_agent_controller_is_deterministic_for_same_script(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    def run_once() -> list[dict[str, object]]:
        from forgecode_agent.models import AssistantMessage, ToolIntent

        ledger = RunLedger(run_id="deterministic-test")
        provider = FakeModelProvider(
            script=[
                AssistantMessage(tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})]),
                AssistantMessage(content="done"),
            ]
        )
        controller = AgentController(
            model_provider=provider,
            tools=read_only_registry.clone_empty_history(),
            approval_policy=auto_read_policy,
            ledger=ledger,
            max_iterations=1,
        )
        controller.run(goal="Read README.md")
        return [event.to_dict(exclude={"timestamp"}) for event in ledger.events]

    assert run_once() == run_once()


def test_agent_controller_stops_before_tool_execution_when_max_iterations_is_zero(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    ledger = RunLedger(run_id="max-iterations-zero")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need a tool.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})],
            )
        ]
    )
    registry = read_only_registry.clone_empty_history()
    controller = AgentController(
        model_provider=provider,
        tools=registry,
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=0,
    )

    result = controller.run(goal="Read README.md")

    assert result.final_answer == "I need a tool."
    assert result.completed is False
    assert result.iterations == 0
    assert result.stop_reason == "max_iterations"
    assert registry.calls == []
    assert "tool_call_requested" not in [event.type for event in ledger.events]
    assert ledger.events[-1].type == "run_completed"
    assert ledger.events[-1].data == {
        "final_answer": "I need a tool.",
        "completed": False,
        "stop_reason": "max_iterations",
    }


def test_agent_controller_stops_without_tool_execution_when_model_returns_multiple_tool_calls(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    ledger = RunLedger(run_id="multiple-tool-calls")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need two tools.",
                tool_intents=[
                    ToolIntent(name="read_file", arguments={"path": "README.md"}),
                    ToolIntent(name="read_file", arguments={"path": "pyproject.toml"}),
                ],
            )
        ]
    )
    registry = read_only_registry.clone_empty_history()
    controller = AgentController(
        model_provider=provider,
        tools=registry,
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=1,
    )

    result = controller.run(goal="Read README.md and pyproject.toml")

    assert result.final_answer == "I need two tools."
    assert result.completed is False
    assert result.iterations == 0
    assert result.stop_reason == "multiple_tool_calls"
    assert registry.calls == []
    assert "tool_call_requested" not in [event.type for event in ledger.events]
    assert "tool_call_completed" not in [event.type for event in ledger.events]
    assert ledger.events[-1].type == "run_completed"
    assert ledger.events[-1].data == {
        "final_answer": "I need two tools.",
        "completed": False,
        "stop_reason": "multiple_tool_calls",
    }


def test_agent_controller_preserves_policy_denial_flow_for_unknown_tools(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    ledger = RunLedger(run_id="unknown-tool-policy-denial")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need a missing tool.",
                tool_intents=[ToolIntent(name="missing_tool", arguments={"path": "README.md"})],
            ),
            AssistantMessage(content="This response must not be requested."),
        ]
    )
    registry = read_only_registry.clone_empty_history()
    controller = AgentController(
        model_provider=provider,
        tools=registry,
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=1,
    )

    with pytest.raises(ToolCallDenied, match="approval_required") as exc_info:
        controller.run(goal="Use a missing tool")

    assert exc_info.value.reason == "approval_required"
    assert registry.calls == []
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
    ]
    assert ledger.events[-1].data == {
        "tool": "missing_tool",
        "allowed": False,
        "reason": "approval_required",
    }
    assert "run_completed" not in [event.type for event in ledger.events]


def test_agent_controller_preserves_policy_denial_flow_for_unknown_tools_with_non_dict_arguments(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    ledger = RunLedger(run_id="unknown-tool-non-dict-arguments-policy-denial")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need a missing tool with malformed arguments.",
                tool_intents=[ToolIntent(name="missing_tool", arguments=123)],
            ),
            AssistantMessage(content="This response must not be requested."),
        ]
    )
    registry = read_only_registry.clone_empty_history()
    controller = AgentController(
        model_provider=provider,
        tools=registry,
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=1,
    )

    with pytest.raises(ToolCallDenied, match="approval_required") as exc_info:
        controller.run(goal="Use a missing tool with malformed arguments")

    assert exc_info.value.reason == "approval_required"
    assert registry.calls == []
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
    ]
    assert ledger.events[-1].data == {
        "tool": "missing_tool",
        "allowed": False,
        "reason": "approval_required",
    }
    assert "run_completed" not in [event.type for event in ledger.events]


def test_agent_controller_stops_safely_when_non_read_only_tool_arguments_are_not_a_dict(
    auto_read_policy: ApprovalPolicy,
) -> None:
    handler_calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="run_shell",
            risk="shell",
            description="Run a shell command.",
            parameters={
                "type": "object",
                "required": ["command"],
                "properties": {"command": {"type": "string"}},
            },
            handler=lambda command: handler_calls.append({"command": command}),
        )
    )
    ledger = RunLedger(run_id="malformed-non-readonly-tool-arguments")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to run a command.",
                tool_intents=[ToolIntent(name="run_shell", arguments=123)],
            ),
            AssistantMessage(content="This response must not be requested."),
        ]
    )
    controller = AgentController(
        model_provider=provider,
        tools=registry,
        approval_policy=ApprovalPolicy(mode=auto_read_policy.mode, approved_actions={"run_shell:ls"}),
        ledger=ledger,
        max_iterations=1,
    )

    result = controller.run(goal="Run ls")

    assert result.final_answer == "I need to run a command."
    assert result.completed is False
    assert result.iterations == 1
    assert result.stop_reason == "invalid_tool_arguments"
    assert handler_calls == []
    assert len(provider.requests) == 1
    assert registry.calls == [
        {"tool": "run_shell", "arguments": 123, "status": "denied", "reason": "invalid_arguments"}
    ]
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "run_completed",
    ]
    assert ledger.events[-1].data == {
        "final_answer": "I need to run a command.",
        "completed": False,
        "stop_reason": "invalid_tool_arguments",
    }


def test_agent_controller_stops_safely_when_tool_arguments_are_malformed(
    auto_read_policy: ApprovalPolicy,
) -> None:
    handler_calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="read_file",
            risk="read_only",
            description="Read a UTF-8 text file from the workspace.",
            parameters={"type": "object", "required": ["path"], "properties": {"path": {"type": "string"}}},
            handler=lambda path: handler_calls.append({"path": path}),
        )
    )
    ledger = RunLedger(run_id="malformed-tool-arguments")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to inspect the README first.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": 123})],
            ),
            AssistantMessage(content="This response must not be requested."),
        ]
    )
    controller = AgentController(
        model_provider=provider,
        tools=registry,
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=1,
    )

    result = controller.run(goal="Read README.md")

    assert result.final_answer == "I need to inspect the README first."
    assert result.completed is False
    assert result.iterations == 1
    assert result.stop_reason == "invalid_tool_arguments"
    assert handler_calls == []
    assert len(provider.requests) == 1
    assert registry.calls == [
        {"tool": "read_file", "arguments": {"path": 123}, "status": "denied", "reason": "invalid_arguments"}
    ]
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "run_completed",
    ]
    assert ledger.events[-1].data == {
        "final_answer": "I need to inspect the README first.",
        "completed": False,
        "stop_reason": "invalid_tool_arguments",
    }
