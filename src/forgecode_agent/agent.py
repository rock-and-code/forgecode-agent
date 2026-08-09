from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forgecode_agent.ledger import REDACTED_VALUE, RunLedger
from forgecode_agent.models import AssistantMessage
from forgecode_agent.policy import ApprovalPolicy
from forgecode_agent.tools import ToolCallDenied, ToolExecutionError, ToolRegistry


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

    def __post_init__(self) -> None:
        if self.max_iterations < 0:
            raise ValueError("max_iterations must be non-negative")

    def run(self, goal: str) -> AgentRunResult:
        self.ledger.append("run_started", {"goal": goal})
        messages: list[dict[str, Any]] = [{"role": "user", "content": goal}]
        iterations = 0

        while True:
            self.ledger.append("model_requested", {"messages": messages})
            response = self.model_provider.complete(messages=messages)
            self.ledger.append("model_responded", self._message_data(response))

            if not response.tool_intents:
                self.ledger.append("run_completed", {"final_answer": response.content, "completed": True})
                return AgentRunResult(final_answer=response.content, completed=True, iterations=iterations)

            if iterations >= self.max_iterations:
                self.ledger.append(
                    "run_completed",
                    {"final_answer": response.content, "completed": False, "stop_reason": "max_iterations"},
                )
                return AgentRunResult(
                    final_answer=response.content,
                    completed=False,
                    iterations=iterations,
                    stop_reason="max_iterations",
                )

            if len(response.tool_intents) > 1:
                self.ledger.append(
                    "run_completed",
                    {"final_answer": response.content, "completed": False, "stop_reason": "multiple_tool_calls"},
                )
                return AgentRunResult(
                    final_answer=response.content,
                    completed=False,
                    iterations=iterations,
                    stop_reason="multiple_tool_calls",
                )

            intent = response.tool_intents[0]
            iterations += 1
            self.ledger.append("tool_call_requested", self._tool_call_requested_data(intent.name, intent.arguments))

            tool = self.tools.get(intent.name)
            if tool is None:
                self.ledger.append(
                    "policy_decision",
                    {"tool": intent.name, "allowed": False, "reason": "unknown_tool"},
                )
                self.ledger.append(
                    "tool_call_failed",
                    {"tool": intent.name, "reason": "unknown_tool"},
                )
                return self._unknown_tool_result(response, iterations)

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
                    return self._invalid_tool_arguments_result(response, iterations, intent.name)

            risk = tool.risk
            decision = self.approval_policy.decide(tool_name=intent.name, risk=risk, arguments=intent.arguments)
            self.ledger.append(
                "policy_decision",
                {"tool": intent.name, "allowed": decision.allowed, "reason": decision.reason},
            )
            if not decision.allowed:
                return self._policy_denied_result(response, iterations, intent.name, decision.reason)

            try:
                result = self.tools.execute(intent.name, intent.arguments)
            except ToolCallDenied as exc:
                if exc.reason != "invalid_arguments":
                    raise
                return self._invalid_tool_arguments_result(response, iterations, intent.name)
            except ToolExecutionError as exc:
                return self._tool_error_result(response, iterations, exc)
            self.ledger.append("tool_call_completed", {"tool": intent.name, "result": result})

            messages.extend(
                [
                    {"role": "assistant", "content": response.content},
                    {"role": "tool", "name": intent.name, "content": result},
                ]
            )

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

    def _policy_denied_result(
        self,
        message: AssistantMessage,
        iterations: int,
        tool_name: str,
        reason: str,
    ) -> AgentRunResult:
        self.ledger.append(
            "tool_call_failed",
            {"tool": tool_name, "reason": reason},
        )
        self.ledger.append(
            "run_completed",
            {"final_answer": message.content, "completed": False, "stop_reason": reason},
        )
        return AgentRunResult(
            final_answer=message.content,
            completed=False,
            iterations=iterations,
            stop_reason=reason,
        )

    def _invalid_tool_arguments_result(self, message: AssistantMessage, iterations: int, tool_name: str) -> AgentRunResult:
        self.ledger.append(
            "tool_call_failed",
            {"tool": tool_name, "reason": "invalid_arguments"},
        )
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

    def _tool_error_result(
        self,
        message: AssistantMessage,
        iterations: int,
        error: ToolExecutionError,
    ) -> AgentRunResult:
        self.ledger.append(
            "tool_call_failed",
            {
                "tool": error.tool_name,
                "reason": "tool_error",
                "error": str(error),
                "error_type": error.error_type,
            },
        )
        self.ledger.append(
            "run_completed",
            {"final_answer": message.content, "completed": False, "stop_reason": "tool_error"},
        )
        return AgentRunResult(
            final_answer=message.content,
            completed=False,
            iterations=iterations,
            stop_reason="tool_error",
        )

    def _message_data(self, message: AssistantMessage) -> dict[str, Any]:
        return {
            "content": message.content,
            "tool_intents": [
                {
                    "name": intent.name,
                    "arguments": REDACTED_VALUE if self.tools.get(intent.name) is None else intent.arguments,
                }
                for intent in message.tool_intents
            ],
        }

    def _tool_call_requested_data(self, tool_name: str, arguments: Any) -> dict[str, Any]:
        if self.tools.get(tool_name) is None:
            return {"tool": tool_name, "arguments": REDACTED_VALUE}
        return {"tool": tool_name, "arguments": arguments}
