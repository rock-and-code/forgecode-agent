from __future__ import annotations

import pytest

from forgecode_agent.models import AssistantMessage, FakeModelProvider, ToolIntent


def test_fake_model_provider_returns_scripted_messages_deterministically() -> None:
    provider = FakeModelProvider(
        script=[
            AssistantMessage(content="first response"),
            AssistantMessage(
                content="second response requests a tool",
                tool_intents=[ToolIntent(name="read_file", arguments={"path": "README.md"})],
            ),
        ]
    )

    first = provider.complete(messages=[{"role": "user", "content": "inspect the repo"}])
    second = provider.complete(messages=[{"role": "user", "content": "continue"}])

    assert first.content == "first response"
    assert first.tool_intents == []
    assert second.content == "second response requests a tool"
    assert second.tool_intents == [ToolIntent(name="read_file", arguments={"path": "README.md"})]
    assert provider.requests == [
        {"messages": [{"role": "user", "content": "inspect the repo"}]},
        {"messages": [{"role": "user", "content": "continue"}]},
    ]


def test_fake_model_provider_is_exhaustive_and_fails_when_script_is_consumed() -> None:
    provider = FakeModelProvider(script=[AssistantMessage(content="only response")])

    provider.complete(messages=[{"role": "user", "content": "hello"}])

    with pytest.raises(IndexError, match="FakeModelProvider script exhausted"):
        provider.complete(messages=[{"role": "user", "content": "unexpected extra turn"}])
