from __future__ import annotations

from forgecode_agent.agent import AgentController
from forgecode_agent.ledger import RunLedger
from forgecode_agent.models import AssistantMessage, FakeModelProvider, ToolIntent
from forgecode_agent.policy import ApprovalPolicy
from forgecode_agent.tools import ToolRegistry


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
