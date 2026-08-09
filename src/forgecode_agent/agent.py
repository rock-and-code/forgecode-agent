from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forgecode_agent.ledger import RunLedger
from forgecode_agent.models import AssistantMessage
from forgecode_agent.policy import ApprovalPolicy
from forgecode_agent.tools import ToolCallDenied, ToolRegistry


@dataclass(frozen=True)
class AgentRunResult:
    final_answer: str
    completed: bool
    iterations: int
    stop_reason: str | None = None


@dataclass
class AgentController:
    model_provider: Any
    tools: ToolRegistry
    approval_policy: ApprovalPolicy
    ledger: RunLedger
    max_iterations: int = 1

    def run(self, goal: str) -> AgentRunResult:
        self.ledger.append("run_started", {"goal": goal})
        messages: list[dict[str, Any]] = [{"role": "user", "content": goal}]
        iterations = 0

        self.ledger.append("model_requested", {"messages": messages})
        first = self.model_provider.complete(messages=messages)
        self.ledger.append("model_responded", self._message_data(first))

        if len(first.tool_intents) > 1:
            self.ledger.append(
                "run_completed",
                {"final_answer": first.content, "completed": False, "stop_reason": "multiple_tool_calls"},
            )
            return AgentRunResult(
                final_answer=first.content,
                completed=False,
                iterations=iterations,
                stop_reason="multiple_tool_calls",
            )

        if first.tool_intents and iterations >= self.max_iterations:
            self.ledger.append(
                "run_completed",
                {"final_answer": first.content, "completed": False, "stop_reason": "max_iterations"},
            )
            return AgentRunResult(
                final_answer=first.content,
                completed=False,
                iterations=iterations,
                stop_reason="max_iterations",
            )

        if first.tool_intents:
            intent = first.tool_intents[0]
            iterations += 1
            self.ledger.append("tool_call_requested", {"tool": intent.name, "arguments": intent.arguments})

            tool = self.tools.get(intent.name)
            if tool is None:
                self.ledger.append(
                    "policy_decision",
                    {"tool": intent.name, "allowed": False, "reason": "unknown_tool"},
                )
                return self._unknown_tool_result(first, iterations)

            if tool is not None:
                try:
                    self.tools.validate_arguments(intent.name, intent.arguments)
                except ToolCallDenied as exc:
                    if exc.reason != "invalid_arguments":
                        raise
                    self.ledger.append(
                        "policy_decision",
                        {"tool": intent.name, "allowed": False, "reason": "invalid_arguments"},
                    )
                    return self._invalid_tool_arguments_result(first, iterations)

            risk = tool.risk
            decision = self.approval_policy.decide(tool_name=intent.name, risk=risk, arguments=intent.arguments)
            self.ledger.append(
                "policy_decision",
                {"tool": intent.name, "allowed": decision.allowed, "reason": decision.reason},
            )
            if not decision.allowed:
                raise ToolCallDenied(f"Tool call denied: {intent.name} {decision.reason}", reason=decision.reason)

            try:
                result = self.tools.execute(intent.name, intent.arguments)
            except ToolCallDenied as exc:
                if exc.reason != "invalid_arguments":
                    raise
                return self._invalid_tool_arguments_result(first, iterations)
            self.ledger.append("tool_call_completed", {"tool": intent.name, "result": result})

            messages = [
                {"role": "user", "content": goal},
                {"role": "assistant", "content": first.content},
                {"role": "tool", "name": intent.name, "content": result},
            ]
            self.ledger.append("model_requested", {"messages": messages})
            final = self.model_provider.complete(messages=messages)
            self.ledger.append("model_responded", self._message_data(final))
            self.ledger.append("run_completed", {"final_answer": final.content, "completed": True})
            return AgentRunResult(final_answer=final.content, completed=True, iterations=iterations)

        self.ledger.append("run_completed", {"final_answer": first.content, "completed": True})
        return AgentRunResult(final_answer=first.content, completed=True, iterations=iterations)

    def _unknown_tool_result(self, message: AssistantMessage, iterations: int) -> AgentRunResult:
        self.ledger.append(
            "run_completed",
            {"final_answer": message.content, "completed": False, "stop_reason": "unknown_tool"},
        )
        return AgentRunResult(
            final_answer=message.content,
            completed=False,
            iterations=iterations,
            stop_reason="unknown_tool",
        )

    def _invalid_tool_arguments_result(self, message: AssistantMessage, iterations: int) -> AgentRunResult:
        self.ledger.append(
            "run_completed",
            {"final_answer": message.content, "completed": False, "stop_reason": "invalid_tool_arguments"},
        )
        return AgentRunResult(
            final_answer=message.content,
            completed=False,
            iterations=iterations,
            stop_reason="invalid_tool_arguments",
        )

    @staticmethod
    def _message_data(message: AssistantMessage) -> dict[str, Any]:
        return {
            "content": message.content,
            "tool_intents": [
                {"name": intent.name, "arguments": intent.arguments} for intent in message.tool_intents
            ],
        }
