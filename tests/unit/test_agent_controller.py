from __future__ import annotations

import json
from pathlib import Path

import pytest

from forgecode_agent.agent import AgentController
from forgecode_agent.ledger import RunLedger
from forgecode_agent.models import AssistantMessage, FakeModelProvider, ToolIntent
from forgecode_agent.policy import ApprovalPolicy
from forgecode_agent.tools import ToolDefinition, ToolRegistry


GOLDEN_DIR = Path(__file__).parents[1] / "golden"


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


def test_agent_controller_exhausts_budget_when_second_model_response_requests_another_tool(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    ledger = RunLedger(run_id="second-tool-after-budget")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to inspect README.md first.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})],
            ),
            AssistantMessage(
                content="Now I need pyproject.toml too.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "pyproject.toml"})],
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

    result = controller.run(goal="Read README.md and pyproject.toml")

    assert result.final_answer == "Now I need pyproject.toml too."
    assert result.completed is False
    assert result.iterations == 1
    assert result.stop_reason == "max_iterations"
    assert len(provider.requests) == 2
    assert registry.calls == [{"tool": "read_file", "arguments": {"path": "README.md"}, "status": "completed"}]
    assert [event.type for event in ledger.events] == [
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
    assert ledger.events[-2].data == {
        "content": "Now I need pyproject.toml too.",
        "tool_intents": [{"name": "read_file", "arguments": {"path": "pyproject.toml"}}],
    }
    assert ledger.events[-1].data == {
        "final_answer": "Now I need pyproject.toml too.",
        "completed": False,
        "stop_reason": "max_iterations",
    }


def test_agent_controller_executes_second_tool_request_when_budget_remains(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    ledger = RunLedger(run_id="second-tool-within-budget")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to inspect README.md first.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})],
            ),
            AssistantMessage(
                content="Now I need pyproject.toml too.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "pyproject.toml"})],
            ),
            AssistantMessage(content="README.md and pyproject.toml have both been read."),
        ]
    )
    registry = read_only_registry.clone_empty_history()
    controller = AgentController(
        model_provider=provider,
        tools=registry,
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=2,
    )

    result = controller.run(goal="Read README.md and pyproject.toml")

    assert result.final_answer == "README.md and pyproject.toml have both been read."
    assert result.completed is True
    assert result.iterations == 2
    assert result.stop_reason is None
    assert len(provider.requests) == 3
    assert registry.calls == [
        {"tool": "read_file", "arguments": {"path": "README.md"}, "status": "completed"},
        {"tool": "read_file", "arguments": {"path": "pyproject.toml"}, "status": "completed"},
    ]
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "tool_call_completed",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "tool_call_completed",
        "model_requested",
        "model_responded",
        "run_completed",
    ]
    assert ledger.events[3].data == {"tool": "read_file", "arguments": {"path": "README.md"}}
    assert ledger.events[8].data == {"tool": "read_file", "arguments": {"path": "pyproject.toml"}}
    assert ledger.events[-1].data == {
        "final_answer": "README.md and pyproject.toml have both been read.",
        "completed": True,
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


def test_agent_controller_read_loop_matches_golden_transcript(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    ledger = RunLedger(run_id="deterministic-read-loop")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to inspect the README first.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})],
            ),
            AssistantMessage(content="README.md says this is the minimal fixture project."),
        ]
    )
    controller = AgentController(
        model_provider=provider,
        tools=read_only_registry.clone_empty_history(),
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=1,
    )

    controller.run(goal="Summarize README.md")

    actual_transcript = [event.to_dict(exclude={"timestamp"}) for event in ledger.events]
    golden_transcript = json.loads((GOLDEN_DIR / "deterministic_read_loop.json").read_text(encoding="utf-8"))
    assert actual_transcript == golden_transcript


def test_agent_controller_max_iterations_zero_tool_request_matches_golden_transcript(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    ledger = RunLedger(run_id="max-iterations-zero-golden")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need a tool.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})],
            )
        ]
    )
    controller = AgentController(
        model_provider=provider,
        tools=read_only_registry.clone_empty_history(),
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=0,
    )

    controller.run(goal="Read README.md")

    actual_transcript = [event.to_dict(exclude={"timestamp"}) for event in ledger.events]
    golden_transcript = json.loads(
        (GOLDEN_DIR / "max_iterations_zero_tool_request.json").read_text(encoding="utf-8")
    )
    assert actual_transcript == golden_transcript
    assert "tool_call_requested" not in [event["type"] for event in actual_transcript]


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


def test_agent_controller_prioritizes_max_iterations_zero_before_multiple_tool_calls(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    ledger = RunLedger(run_id="max-iterations-zero-multiple-tool-calls")
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
        max_iterations=0,
    )

    result = controller.run(goal="Read README.md and pyproject.toml")

    assert result.final_answer == "I need two tools."
    assert result.completed is False
    assert result.iterations == 0
    assert result.stop_reason == "max_iterations"
    assert registry.calls == []
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "run_completed",
    ]
    assert ledger.events[-1].data == {
        "final_answer": "I need two tools.",
        "completed": False,
        "stop_reason": "max_iterations",
    }


def test_agent_controller_rejects_negative_max_iterations(
    scripted_read_then_answer_model: FakeModelProvider,
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
    run_ledger: RunLedger,
) -> None:
    with pytest.raises(ValueError, match=r"max_iterations.*non-negative"):
        AgentController(
            model_provider=scripted_read_then_answer_model,
            tools=read_only_registry,
            approval_policy=auto_read_policy,
            ledger=run_ledger,
            max_iterations=-1,
        )


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


def test_agent_controller_model_error_normalizes_provider_failure_after_safe_response(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    class FailingProvider:
        def __init__(self) -> None:
            self.requests: list[dict[str, object]] = []

        def complete(self, *, messages: list[dict[str, object]]) -> AssistantMessage:
            self.requests.append({"messages": messages})
            if len(self.requests) == 1:
                return AssistantMessage(
                    content="Safe fallback answer.",
                    tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})],
                )
            raise RuntimeError("provider payload contains sensitive details")

    ledger = RunLedger(run_id="model-error")
    provider = FailingProvider()
    controller = AgentController(
        model_provider=provider,
        tools=read_only_registry.clone_empty_history(),
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=1,
    )

    result = controller.run(goal="Read README.md")

    assert result.final_answer == "Safe fallback answer."
    assert result.completed is False
    assert result.iterations == 1
    assert result.stop_reason == "model_error"
    assert len(provider.requests) == 2
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "tool_call_completed",
        "model_requested",
        "model_error",
        "run_completed",
    ]
    assert ledger.events[-2].data == {"error_type": "RuntimeError"}
    assert ledger.events[-1].data == {
        "final_answer": "Safe fallback answer.",
        "completed": False,
        "stop_reason": "model_error",
    }
    assert all("sensitive details" not in str(event.data) for event in ledger.events)


def test_agent_controller_model_error_terminal_path_matches_golden_transcript(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
) -> None:
    class FailingProvider:
        def complete(self, *, messages: list[dict[str, object]]) -> AssistantMessage:
            raise RuntimeError("deterministic provider failure")

    ledger = RunLedger(run_id="model-error-terminal")
    controller = AgentController(
        model_provider=FailingProvider(),
        tools=read_only_registry.clone_empty_history(),
        approval_policy=auto_read_policy,
        ledger=ledger,
    )

    controller.run(goal="Read README.md")

    actual_transcript = [event.to_dict(exclude={"timestamp"}) for event in ledger.events]
    golden_transcript = json.loads(
        (GOLDEN_DIR / "model_error_terminal.json").read_text(encoding="utf-8")
    )
    assert actual_transcript == golden_transcript


def test_agent_controller_multiple_tool_calls_terminal_path_matches_golden_transcript(
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
    controller = AgentController(
        model_provider=provider,
        tools=read_only_registry.clone_empty_history(),
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=1,
    )

    controller.run(goal="Read README.md and pyproject.toml")

    actual_transcript = [event.to_dict(exclude={"timestamp"}) for event in ledger.events]
    golden_transcript = json.loads(
        (GOLDEN_DIR / "multiple_tool_calls_terminal.json").read_text(encoding="utf-8")
    )
    assert actual_transcript == golden_transcript
    event_types = [event["type"] for event in actual_transcript]
    assert "tool_call_requested" not in event_types
    assert "tool_call_completed" not in event_types


def test_agent_controller_stops_safely_for_unknown_tools(
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

    result = controller.run(goal="Use a missing tool")

    assert result.final_answer == "I need a missing tool."
    assert result.completed is False
    assert result.iterations == 1
    assert result.stop_reason == "unknown_tool"
    assert registry.calls == []
    assert len(provider.requests) == 1
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "tool_call_failed",
        "run_completed",
    ]
    assert ledger.events[4].data == {
        "tool": "missing_tool",
        "allowed": False,
        "reason": "unknown_tool",
    }
    assert ledger.events[5].data == {"tool": "missing_tool", "reason": "unknown_tool"}
    assert ledger.events[-1].data == {
        "final_answer": "I need a missing tool.",
        "completed": False,
        "stop_reason": "unknown_tool",
    }


def test_agent_controller_redacts_unknown_tool_arguments_from_serialized_ledger(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
    tmp_path: Path,
) -> None:
    secret_payload = "UNKNOWN_TOOL_PAYLOAD_DO_NOT_LOG_8f2d58b694"
    ledger = RunLedger(run_id="unknown-tool-redacted-arguments")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need a missing tool.",
                tool_intents=[
                    ToolIntent(
                        name="missing_tool",
                        arguments={"payload": secret_payload, "nested": {"copy": secret_payload}},
                    )
                ],
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

    result = controller.run(goal="Use a missing tool with secret arguments")
    ledger_path = tmp_path / "ledger.jsonl"
    ledger.write_jsonl(ledger_path)
    serialized_ledger = ledger_path.read_text(encoding="utf-8")

    assert result.stop_reason == "unknown_tool"
    assert registry.calls == []
    assert len(provider.requests) == 1
    assert ledger.events[5].data == {"tool": "missing_tool", "reason": "unknown_tool"}
    assert secret_payload not in serialized_ledger


def test_agent_controller_stops_safely_for_unknown_tools_with_non_dict_arguments(
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

    result = controller.run(goal="Use a missing tool with malformed arguments")

    assert result.final_answer == "I need a missing tool with malformed arguments."
    assert result.completed is False
    assert result.iterations == 1
    assert result.stop_reason == "unknown_tool"
    assert registry.calls == []
    assert len(provider.requests) == 1
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "tool_call_failed",
        "run_completed",
    ]
    assert ledger.events[4].data == {
        "tool": "missing_tool",
        "allowed": False,
        "reason": "unknown_tool",
    }
    assert ledger.events[5].data == {"tool": "missing_tool", "reason": "unknown_tool"}
    assert ledger.events[-1].data == {
        "final_answer": "I need a missing tool with malformed arguments.",
        "completed": False,
        "stop_reason": "unknown_tool",
    }


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
        "tool_call_failed",
        "run_completed",
    ]
    assert ledger.events[5].data == {"tool": "run_shell", "reason": "invalid_arguments"}
    assert ledger.events[-1].data == {
        "final_answer": "I need to run a command.",
        "completed": False,
        "stop_reason": "invalid_tool_arguments",
    }


def test_agent_controller_stops_safely_when_supervised_policy_denies_known_shell_tool(
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
    ledger = RunLedger(run_id="supervised-policy-denies-known-shell-tool")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to run a command.",
                tool_intents=[ToolIntent(name="run_shell", arguments={"command": "ls"})],
            ),
            AssistantMessage(content="This response must not be requested."),
        ]
    )
    controller = AgentController(
        model_provider=provider,
        tools=registry,
        approval_policy=ApprovalPolicy(mode=auto_read_policy.mode, approved_actions=set()),
        ledger=ledger,
        max_iterations=1,
    )

    result = controller.run(goal="Run ls")

    assert result.final_answer == "I need to run a command."
    assert result.completed is False
    assert result.iterations == 1
    assert result.stop_reason == "approval_required"
    assert handler_calls == []
    assert registry.calls == []
    assert len(provider.requests) == 1
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "tool_call_failed",
        "run_completed",
    ]
    assert ledger.events[4].data == {
        "tool": "run_shell",
        "allowed": False,
        "reason": "approval_required",
    }
    assert ledger.events[5].data == {"tool": "run_shell", "reason": "approval_required"}
    assert ledger.events[-1].data == {
        "final_answer": "I need to run a command.",
        "completed": False,
        "stop_reason": "approval_required",
    }


def test_agent_controller_supervised_policy_denial_matches_golden_transcript(
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
    ledger = RunLedger(run_id="supervised-policy-denial-golden")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to run a command.",
                tool_intents=[ToolIntent(name="run_shell", arguments={"command": "ls"})],
            ),
            AssistantMessage(content="This response must not be requested."),
        ]
    )
    controller = AgentController(
        model_provider=provider,
        tools=registry,
        approval_policy=ApprovalPolicy(mode=auto_read_policy.mode, approved_actions=set()),
        ledger=ledger,
        max_iterations=1,
    )

    controller.run(goal="Run ls")

    actual_transcript = [event.to_dict(exclude={"timestamp"}) for event in ledger.events]
    golden_transcript = json.loads(
        (GOLDEN_DIR / "supervised_policy_denial_terminal.json").read_text(encoding="utf-8")
    )
    assert actual_transcript == golden_transcript
    assert handler_calls == []
    assert registry.calls == []


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
        "tool_call_failed",
        "run_completed",
    ]
    assert ledger.events[5].data == {"tool": "read_file", "reason": "invalid_arguments"}
    assert ledger.events[-1].data == {
        "final_answer": "I need to inspect the README first.",
        "completed": False,
        "stop_reason": "invalid_tool_arguments",
    }


def test_agent_controller_records_sanitized_tool_call_failed_for_invalid_arguments(
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
    ledger = RunLedger(run_id="invalid-tool-arguments-ledger")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to inspect a secret path.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": 123, "token": "secret-token-123"})],
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

    result = controller.run(goal="Read a sensitive path")

    assert result.final_answer == "I need to inspect a secret path."
    assert result.completed is False
    assert result.iterations == 1
    assert result.stop_reason == "invalid_tool_arguments"
    assert handler_calls == []
    assert len(provider.requests) == 1
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "tool_call_failed",
        "run_completed",
    ]
    assert ledger.events[5].data == {"tool": "read_file", "reason": "invalid_arguments"}
    assert "secret-token-123" not in json.dumps(ledger.events[5].data)
    assert ledger.events[-1].data == {
        "final_answer": "I need to inspect a secret path.",
        "completed": False,
        "stop_reason": "invalid_tool_arguments",
    }


def test_agent_controller_stops_safely_when_tool_handler_raises_runtime_exception(
    auto_read_policy: ApprovalPolicy,
) -> None:
    def failing_read_file(path: str) -> dict[str, str]:
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
            handler=failing_read_file,
        )
    )
    ledger = RunLedger(run_id="tool-handler-runtime-error")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to inspect the README first.",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})],
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
    assert result.stop_reason == "tool_error"
    assert len(provider.requests) == 1
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": {"path": "README.md"},
            "status": "failed",
            "reason": "tool_error",
            "error_type": "RuntimeError",
        }
    ]
    assert [event.type for event in ledger.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "tool_call_requested",
        "policy_decision",
        "tool_call_failed",
        "run_completed",
    ]
    assert ledger.events[4].data == {
        "tool": "read_file",
        "allowed": True,
        "reason": "auto_allowed_read_only",
    }
    assert ledger.events[5].data == {
        "tool": "read_file",
        "reason": "tool_error",
        "error": "tool execution failed",
        "error_type": "RuntimeError",
    }
    assert "supersecret" not in json.dumps(ledger.events[5].data)
    assert ledger.events[-1].data == {
        "final_answer": "I need to inspect the README first.",
        "completed": False,
        "stop_reason": "tool_error",
    }


def test_agent_controller_redacts_known_invalid_arguments_from_audit_events(
    read_only_registry: ToolRegistry,
    auto_read_policy: ApprovalPolicy,
    tmp_path: Path,
) -> None:
    secret_payload = "KNOWN_TOOL_INVALID_PAYLOAD_DO_NOT_LOG_4b7e9c21"
    ledger = RunLedger(run_id="known-tool-invalid-arguments-redacted")
    provider = FakeModelProvider(
        script=[
            AssistantMessage(
                content="I need to inspect a sensitive path.",
                tool_intents=[
                    ToolIntent(
                        name="read_file",
                        arguments={"path": 123, "payload": secret_payload},
                    )
                ],
            ),
            AssistantMessage(content="This response must not be requested."),
        ]
    )
    controller = AgentController(
        model_provider=provider,
        tools=read_only_registry.clone_empty_history(),
        approval_policy=auto_read_policy,
        ledger=ledger,
        max_iterations=1,
    )

    result = controller.run(goal="Read a sensitive path")
    ledger_path = tmp_path / "ledger.jsonl"
    ledger.write_jsonl(ledger_path)
    serialized_ledger = ledger_path.read_text(encoding="utf-8")

    assert result.stop_reason == "invalid_tool_arguments"
    assert ledger.events[2].data == {
        "content": "I need to inspect a sensitive path.",
        "tool_intents": [{"name": "read_file", "arguments": "[REDACTED]"}],
    }
    assert ledger.events[3].data == {"tool": "read_file", "arguments": "[REDACTED]"}
    assert secret_payload not in serialized_ledger
