from __future__ import annotations

from forgecode_agent.policy import ApprovalMode, ApprovalPolicy


def test_approval_policy_allows_read_only_tools_without_explicit_approval() -> None:
    policy = ApprovalPolicy(mode=ApprovalMode.SUPERVISED, approved_actions=set())

    decision = policy.decide(tool_name="read_file", risk="read_only", arguments={"path": "README.md"})

    assert decision.allowed is True
    assert decision.requires_approval is False
    assert decision.reason == "auto_allowed_read_only"


def test_approval_policy_blocks_write_shell_and_git_operations_unless_approved() -> None:
    policy = ApprovalPolicy(mode=ApprovalMode.SUPERVISED, approved_actions=set())

    for tool_name, risk, arguments in [
        ("write_file", "write", {"path": "README.md"}),
        ("shell", "shell", {"command": "pytest"}),
        ("git_commit", "git", {"message": "commit from agent"}),
    ]:
        decision = policy.decide(tool_name=tool_name, risk=risk, arguments=arguments)
        assert decision.allowed is False
        assert decision.requires_approval is True
        assert decision.reason == "approval_required"


def test_approval_policy_allows_specific_preapproved_action() -> None:
    policy = ApprovalPolicy(
        mode=ApprovalMode.SUPERVISED,
        approved_actions={"shell:pytest"},
    )

    decision = policy.decide(tool_name="shell", risk="shell", arguments={"command": "pytest"})

    assert decision.allowed is True
    assert decision.requires_approval is False
    assert decision.reason == "preapproved"


def test_approval_policy_readonly_mode_blocks_non_read_actions_even_if_preapproved() -> None:
    policy = ApprovalPolicy(
        mode=ApprovalMode.READONLY,
        approved_actions={"write_file:README.md", "shell:pytest", "git_commit:commit from agent"},
    )

    decision = policy.decide(tool_name="write_file", risk="write", arguments={"path": "README.md"})

    assert decision.allowed is False
    assert decision.requires_approval is False
    assert decision.reason == "readonly_mode_blocks_mutation"
