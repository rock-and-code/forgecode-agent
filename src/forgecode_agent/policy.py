from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ApprovalMode(str, Enum):
    READONLY = "readonly"
    SUPERVISED = "supervised"


@dataclass(frozen=True)
class ApprovalDecision:
    allowed: bool
    requires_approval: bool
    reason: str


@dataclass(frozen=True)
class ApprovalPolicy:
    mode: ApprovalMode = ApprovalMode.SUPERVISED
    approved_actions: set[str] = field(default_factory=set)

    def decide(self, *, tool_name: str, risk: str, arguments: Any) -> ApprovalDecision:
        if risk == "read_only":
            return ApprovalDecision(True, False, "auto_allowed_read_only")

        if self.mode == ApprovalMode.READONLY:
            return ApprovalDecision(False, False, "readonly_mode_blocks_mutation")

        if self._action_key(tool_name, arguments) in self.approved_actions:
            return ApprovalDecision(True, False, "preapproved")

        return ApprovalDecision(False, True, "approval_required")

    @staticmethod
    def _action_key(tool_name: str, arguments: Any) -> str:
        if not isinstance(arguments, dict):
            return tool_name

        for key in ("command", "path", "message"):
            if key in arguments:
                return f"{tool_name}:{arguments[key]}"
        return tool_name
