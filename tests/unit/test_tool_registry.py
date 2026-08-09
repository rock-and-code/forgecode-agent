from __future__ import annotations

import pytest

from forgecode_agent.policy import ApprovalPolicy, ApprovalMode
from forgecode_agent.tools import (
    ToolCallDenied,
    ToolDefinition,
    ToolExecutionError,
    ToolRegistry,
)


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
            parameters={"type": "object", "additionalProperties": True},
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


def test_tool_registry_denies_missing_required_arguments_before_handler_runs(
    read_file_tool: ToolDefinition,
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name=read_file_tool.name,
            risk=read_file_tool.risk,
            description=read_file_tool.description,
            parameters=read_file_tool.parameters,
            handler=lambda path: calls.append({"path": path}),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("read_file", {})

    assert calls == []
    assert registry.calls == [
        {"tool": "read_file", "arguments": {}, "status": "denied", "reason": "invalid_arguments"}
    ]


def test_tool_registry_denies_argument_type_mismatch_before_handler_runs(
    read_file_tool: ToolDefinition,
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name=read_file_tool.name,
            risk=read_file_tool.risk,
            description=read_file_tool.description,
            parameters=read_file_tool.parameters,
            handler=lambda path: calls.append({"path": path}),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("read_file", {"path": 123})

    assert calls == []
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": {"path": 123},
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_integer_argument_type_mismatch_before_handler_runs() -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="repeat",
            risk="read_only",
            description="Repeat a message a number of times.",
            parameters={
                "type": "object",
                "properties": {"count": {"type": "integer"}},
                "required": ["count"],
            },
            handler=lambda count: calls.append({"count": count}),
        )
    )
    arguments = {"count": True}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("repeat", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "repeat",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("note", ["optional note", None])
def test_tool_registry_allows_nullable_union_argument_types(note: str | None) -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="annotate",
            risk="read_only",
            description="Record an optional note.",
            parameters={
                "type": "object",
                "properties": {"note": {"type": ["string", "null"]}},
                "required": ["note"],
            },
            handler=lambda note: calls.append({"note": note}),
        )
    )
    arguments = {"note": note}

    result = registry.execute("annotate", arguments)

    assert result is None
    assert calls == [{"note": note}]
    assert registry.calls == [
        {"tool": "annotate", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize("note", [123, True])
def test_tool_registry_denies_nullable_union_argument_type_mismatch_before_handler_runs(
    note: object,
) -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="annotate",
            risk="read_only",
            description="Record an optional note.",
            parameters={
                "type": "object",
                "properties": {"note": {"type": ["string", "null"]}},
                "required": ["note"],
            },
            handler=lambda note: calls.append({"note": note}),
        )
    )
    arguments = {"note": note}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("annotate", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "annotate",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("paths", [None, ["README.md", "pyproject.toml"]])
def test_tool_registry_applies_nullable_array_schema_constraints(paths: object) -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read an optional batch of paths.",
            parameters={
                "type": "object",
                "properties": {
                    "paths": {
                        "type": ["array", "null"],
                        "items": {"type": "string"},
                        "minItems": 2,
                    }
                },
                "required": ["paths"],
            },
            handler=lambda paths: calls.append({"paths": paths}),
        )
    )
    arguments = {"paths": paths}

    result = registry.execute("batch_read", arguments)

    assert result is None
    assert calls == [{"paths": paths}]
    assert registry.calls == [
        {"tool": "batch_read", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize("paths", [["README.md", 123], ["README.md"]])
def test_tool_registry_denies_nullable_array_schema_violations_before_handler_runs(
    paths: object,
) -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read an optional batch of paths.",
            parameters={
                "type": "object",
                "properties": {
                    "paths": {
                        "type": ["array", "null"],
                        "items": {"type": "string"},
                        "minItems": 2,
                    }
                },
                "required": ["paths"],
            },
            handler=lambda paths: calls.append({"paths": paths}),
        )
    )
    arguments = {"paths": paths}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("config", [None, {"source": "README.md"}])
def test_tool_registry_applies_nullable_object_schema_constraints(config: object) -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="copy_source",
            risk="read_only",
            description="Copy from an optional source config.",
            parameters={
                "type": "object",
                "properties": {
                    "config": {
                        "type": ["object", "null"],
                        "required": ["source"],
                        "properties": {"source": {"type": "string"}},
                        "additionalProperties": False,
                    }
                },
                "required": ["config"],
            },
            handler=lambda config: calls.append({"config": config}),
        )
    )
    arguments = {"config": config}

    result = registry.execute("copy_source", arguments)

    assert result is None
    assert calls == [{"config": config}]
    assert registry.calls == [
        {"tool": "copy_source", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize(
    "config",
    [{}, {"source": "README.md", "extra": True}, {"source": 123}],
)
def test_tool_registry_denies_nullable_object_schema_violations_before_handler_runs(
    config: object,
) -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="copy_source",
            risk="read_only",
            description="Copy from an optional source config.",
            parameters={
                "type": "object",
                "properties": {
                    "config": {
                        "type": ["object", "null"],
                        "required": ["source"],
                        "properties": {"source": {"type": "string"}},
                        "additionalProperties": False,
                    }
                },
                "required": ["config"],
            },
            handler=lambda config: calls.append({"config": config}),
        )
    )
    arguments = {"config": config}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("copy_source", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "copy_source",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("arguments", [{"count": 0}, {"count": 6}])
def test_tool_registry_denies_integer_argument_bounds_before_handler_runs(
    arguments: dict[str, int],
) -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="repeat",
            risk="read_only",
            description="Repeat a message a number of times.",
            parameters={
                "type": "object",
                "properties": {"count": {"type": "integer", "minimum": 1, "maximum": 5}},
                "required": ["count"],
            },
            handler=lambda count: calls.append({"count": count}),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("repeat", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "repeat",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("count", [1, 3, 5])
def test_tool_registry_allows_integer_argument_bounds(
    count: int,
) -> None:
    calls: list[dict[str, int]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="repeat",
            risk="read_only",
            description="Repeat a message a number of times.",
            parameters={
                "type": "object",
                "properties": {"count": {"type": "integer", "minimum": 1, "maximum": 5}},
                "required": ["count"],
            },
            handler=lambda count: calls.append({"count": count}),
        )
    )
    arguments = {"count": count}

    result = registry.execute("repeat", arguments)

    assert result is None
    assert calls == [{"count": count}]
    assert registry.calls == [
        {"tool": "repeat", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize("temperature", ["0.7", True])
def test_tool_registry_denies_number_argument_type_mismatch_before_handler_runs(
    temperature: object,
) -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sample",
            risk="read_only",
            description="Sample with a numeric temperature.",
            parameters={
                "type": "object",
                "properties": {"temperature": {"type": "number"}},
                "required": ["temperature"],
            },
            handler=lambda temperature: calls.append({"temperature": temperature}),
        )
    )
    arguments = {"temperature": temperature}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("sample", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "sample",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("temperature", [0.0, 0.7, 1])
def test_tool_registry_allows_number_arguments(temperature: float | int) -> None:
    calls: list[dict[str, float | int]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sample",
            risk="read_only",
            description="Sample with a numeric temperature.",
            parameters={
                "type": "object",
                "properties": {"temperature": {"type": "number"}},
                "required": ["temperature"],
            },
            handler=lambda temperature: calls.append({"temperature": temperature}),
        )
    )
    arguments = {"temperature": temperature}

    result = registry.execute("sample", arguments)

    assert result is None
    assert calls == [{"temperature": temperature}]
    assert registry.calls == [
        {"tool": "sample", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize("temperature", [-0.1, 1.1])
def test_tool_registry_denies_number_argument_bounds_before_handler_runs(
    temperature: float,
) -> None:
    calls: list[dict[str, float]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sample",
            risk="read_only",
            description="Sample with a numeric temperature.",
            parameters={
                "type": "object",
                "properties": {"temperature": {"type": "number", "minimum": 0.0, "maximum": 1.0}},
                "required": ["temperature"],
            },
            handler=lambda temperature: calls.append({"temperature": temperature}),
        )
    )
    arguments = {"temperature": temperature}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("sample", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "sample",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("temperature", [0.0, 0.5, 1.0])
def test_tool_registry_allows_number_argument_bounds(temperature: float) -> None:
    calls: list[dict[str, float]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sample",
            risk="read_only",
            description="Sample with a numeric temperature.",
            parameters={
                "type": "object",
                "properties": {"temperature": {"type": "number", "minimum": 0.0, "maximum": 1.0}},
                "required": ["temperature"],
            },
            handler=lambda temperature: calls.append({"temperature": temperature}),
        )
    )
    arguments = {"temperature": temperature}

    result = registry.execute("sample", arguments)

    assert result is None
    assert calls == [{"temperature": temperature}]
    assert registry.calls == [
        {"tool": "sample", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize("count", [5, 7])
def test_tool_registry_denies_integer_argument_multiple_of_before_handler_runs(
    count: int,
) -> None:
    calls: list[dict[str, int]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="repeat",
            risk="read_only",
            description="Repeat a message a number of times.",
            parameters={
                "type": "object",
                "properties": {"count": {"type": "integer", "multipleOf": 3}},
                "required": ["count"],
            },
            handler=lambda count: calls.append({"count": count}),
        )
    )
    arguments = {"count": count}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("repeat", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "repeat",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("count", [0, 3, 6])
def test_tool_registry_allows_integer_argument_multiple_of(count: int) -> None:
    calls: list[dict[str, int]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="repeat",
            risk="read_only",
            description="Repeat a message a number of times.",
            parameters={
                "type": "object",
                "properties": {"count": {"type": "integer", "multipleOf": 3}},
                "required": ["count"],
            },
            handler=lambda count: calls.append({"count": count}),
        )
    )
    arguments = {"count": count}

    result = registry.execute("repeat", arguments)

    assert result is None
    assert calls == [{"count": count}]
    assert registry.calls == [
        {"tool": "repeat", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize("temperature", [0.15, 0.26])
def test_tool_registry_denies_number_argument_multiple_of_before_handler_runs(
    temperature: float,
) -> None:
    calls: list[dict[str, float]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sample",
            risk="read_only",
            description="Sample with a numeric temperature.",
            parameters={
                "type": "object",
                "properties": {"temperature": {"type": "number", "multipleOf": 0.25}},
                "required": ["temperature"],
            },
            handler=lambda temperature: calls.append({"temperature": temperature}),
        )
    )
    arguments = {"temperature": temperature}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("sample", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "sample",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("temperature", [0.0, 0.25, 1.0])
def test_tool_registry_allows_number_argument_multiple_of(temperature: float) -> None:
    calls: list[dict[str, float]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sample",
            risk="read_only",
            description="Sample with a numeric temperature.",
            parameters={
                "type": "object",
                "properties": {"temperature": {"type": "number", "multipleOf": 0.25}},
                "required": ["temperature"],
            },
            handler=lambda temperature: calls.append({"temperature": temperature}),
        )
    )
    arguments = {"temperature": temperature}

    result = registry.execute("sample", arguments)

    assert result is None
    assert calls == [{"temperature": temperature}]
    assert registry.calls == [
        {"tool": "sample", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize("divisor", [0, -0.25, "0.25"])
def test_tool_registry_denies_malformed_multiple_of_schema_before_handler_runs(
    divisor: object,
) -> None:
    calls: list[dict[str, float]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sample",
            risk="read_only",
            description="Sample with a numeric temperature.",
            parameters={
                "type": "object",
                "properties": {"temperature": {"type": "number", "multipleOf": divisor}},
                "required": ["temperature"],
            },
            handler=lambda temperature: calls.append({"temperature": temperature}),
        )
    )
    arguments = {"temperature": 0.5}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("sample", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "sample",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("temperature", [1e100, float("inf"), float("nan")])
def test_tool_registry_denies_multiple_of_values_that_cannot_be_checked_without_crashing(
    temperature: float,
) -> None:
    calls: list[dict[str, float]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sample",
            risk="read_only",
            description="Sample with a numeric temperature.",
            parameters={
                "type": "object",
                "properties": {"temperature": {"type": "number", "multipleOf": 0.1}},
                "required": ["temperature"],
            },
            handler=lambda temperature: calls.append({"temperature": temperature}),
        )
    )
    arguments = {"temperature": temperature}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("sample", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "sample",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_boolean_argument_type_mismatch_before_handler_runs() -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="set_enabled",
            risk="read_only",
            description="Set enabled state.",
            parameters={
                "type": "object",
                "properties": {"enabled": {"type": "boolean"}},
                "required": ["enabled"],
            },
            handler=lambda enabled: calls.append({"enabled": enabled}),
        )
    )
    arguments = {"enabled": "true"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("set_enabled", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "set_enabled",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_object_argument_type_mismatch_before_handler_runs() -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="annotate",
            risk="read_only",
            description="Annotate with metadata.",
            parameters={
                "type": "object",
                "required": ["metadata"],
                "properties": {"metadata": {"type": "object"}},
            },
            handler=lambda metadata: calls.append({"metadata": metadata}),
        )
    )
    arguments = {"metadata": "not an object"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("annotate", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "annotate",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_allows_bare_nested_object_properties() -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="annotate",
            risk="read_only",
            description="Annotate with arbitrary metadata.",
            parameters={
                "type": "object",
                "required": ["metadata"],
                "properties": {"metadata": {"type": "object"}},
            },
            handler=lambda metadata: calls.append({"metadata": metadata}),
        )
    )
    arguments = {"metadata": {"any": "value", "nested": {"ok": True}}}

    result = registry.execute("annotate", arguments)

    assert result is None
    assert calls == [{"metadata": arguments["metadata"]}]
    assert registry.calls == [{"tool": "annotate", "arguments": arguments, "status": "completed"}]


@pytest.mark.parametrize(
    "arguments",
    [
        {"metadata": {"source": 123}},
        {"metadata": {}},
        {"metadata": {"source": "fixture", "extra": "not allowed"}},
    ],
)
def test_tool_registry_denies_nested_object_schema_violations_before_handler_runs(
    arguments: dict[str, object],
) -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="annotate",
            risk="read_only",
            description="Annotate with metadata.",
            parameters={
                "type": "object",
                "required": ["metadata"],
                "properties": {
                    "metadata": {
                        "type": "object",
                        "required": ["source"],
                        "properties": {"source": {"type": "string"}},
                        "additionalProperties": False,
                    }
                },
            },
            handler=lambda metadata: calls.append({"metadata": metadata}),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("annotate", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "annotate",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("arguments", [None, ["README.md"], "README.md"])
def test_tool_registry_denies_non_dict_arguments_before_handler_runs(
    read_file_tool: ToolDefinition,
    arguments: object,
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name=read_file_tool.name,
            risk=read_file_tool.risk,
            description=read_file_tool.description,
            parameters=read_file_tool.parameters,
            handler=lambda path: calls.append({"path": path}),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("read_file", arguments)  # type: ignore[arg-type]

    assert calls == []
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_dict_for_array_schema_before_handler_runs() -> None:
    calls: list[str] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={"type": "array"},
            handler=lambda: calls.append("ran"),
        )
    )
    arguments: dict[str, object] = {}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("arguments", [None, ["README.md", "pyproject.toml"]])
def test_tool_registry_allows_root_nullable_array_schema(arguments: object) -> None:
    calls: list[object] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read an optional batch of paths.",
            parameters={
                "type": ["array", "null"],
                "items": {"type": "string"},
                "minItems": 2,
            },
            handler=lambda paths: calls.append(paths),
        )
    )

    result = registry.execute("batch_read", arguments)

    assert result is None
    assert calls == [arguments]
    assert registry.calls == [
        {"tool": "batch_read", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize("arguments", [["README.md", 123], ["README.md"]])
def test_tool_registry_denies_root_nullable_array_schema_violations_before_handler_runs(
    arguments: object,
) -> None:
    calls: list[object] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read an optional batch of paths.",
            parameters={
                "type": ["array", "null"],
                "items": {"type": "string"},
                "minItems": 2,
            },
            handler=lambda paths: calls.append(paths),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("arguments", [None, {"source": "README.md"}])
def test_tool_registry_allows_root_nullable_object_schema(arguments: object) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def handler(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="load_config",
            risk="read_only",
            description="Load an optional config.",
            parameters={
                "type": ["object", "null"],
                "required": ["source"],
                "properties": {"source": {"type": "string"}},
                "additionalProperties": False,
            },
            handler=handler,
        )
    )

    result = registry.execute("load_config", arguments)

    assert result is None
    if arguments is None:
        assert calls == [((None,), {})]
    else:
        assert calls == [((), arguments)]
    assert registry.calls == [
        {"tool": "load_config", "arguments": arguments, "status": "completed"}
    ]


@pytest.mark.parametrize("arguments", [{}, {"a": 1, "b": 2, "c": 3}])
def test_tool_registry_denies_object_property_count_violations_before_handler_runs(
    arguments: dict[str, int],
) -> None:
    calls: list[dict[str, int]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="collect_options",
            risk="read_only",
            description="Collect a bounded set of options.",
            parameters={
                "type": "object",
                "minProperties": 1,
                "maxProperties": 2,
                "additionalProperties": True,
            },
            handler=lambda **kwargs: calls.append(kwargs),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("collect_options", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "collect_options",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("arguments", [{"a": 1}, {"a": 1, "b": 2}])
def test_tool_registry_allows_bare_object_property_counts_within_schema_bounds(
    arguments: dict[str, int],
) -> None:
    calls: list[dict[str, int]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="collect_options",
            risk="read_only",
            description="Collect a bounded set of options.",
            parameters={"type": "object", "minProperties": 1, "maxProperties": 2},
            handler=lambda **kwargs: calls.append(kwargs),
        )
    )

    result = registry.execute("collect_options", arguments)

    assert result is None
    assert calls == [arguments]
    assert registry.calls == [
        {"tool": "collect_options", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_allows_nested_object_property_counts() -> None:
    calls: list[dict[str, dict[str, int]]] = []
    arguments = {"options": {"a": 1, "b": 2}}
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="collect_nested_options",
            risk="read_only",
            description="Collect a bounded nested set of options.",
            parameters={
                "type": "object",
                "required": ["options"],
                "properties": {
                    "options": {
                        "type": "object",
                        "minProperties": 1,
                        "maxProperties": 2,
                        "additionalProperties": {"type": "integer"},
                    }
                },
                "additionalProperties": False,
            },
            handler=lambda **kwargs: calls.append(kwargs),
        )
    )

    result = registry.execute("collect_nested_options", arguments)

    assert result is None
    assert calls == [arguments]
    assert registry.calls == [
        {
            "tool": "collect_nested_options",
            "arguments": arguments,
            "status": "completed",
        }
    ]


@pytest.mark.parametrize("options", [{}, {"a": 1, "b": 2, "c": 3}])
def test_tool_registry_denies_nested_object_property_count_violations(
    options: dict[str, int],
) -> None:
    calls: list[dict[str, dict[str, int]]] = []
    arguments = {"options": options}
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="collect_nested_options",
            risk="read_only",
            description="Collect a bounded nested set of options.",
            parameters={
                "type": "object",
                "required": ["options"],
                "properties": {
                    "options": {
                        "type": "object",
                        "minProperties": 1,
                        "maxProperties": 2,
                        "additionalProperties": {"type": "integer"},
                    }
                },
                "additionalProperties": False,
            },
            handler=lambda **kwargs: calls.append(kwargs),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("collect_nested_options", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "collect_nested_options",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize(
    "arguments", [{}, {"source": 123}, {"source": "README.md", "extra": "x"}]
)
def test_tool_registry_denies_root_nullable_object_schema_violations_before_handler_runs(
    arguments: object,
) -> None:
    calls: list[object] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="load_config",
            risk="read_only",
            description="Load an optional config.",
            parameters={
                "type": ["object", "null"],
                "required": ["source"],
                "properties": {"source": {"type": "string"}},
                "additionalProperties": False,
            },
            handler=lambda config: calls.append(config),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("load_config", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "load_config",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_array_item_type_mismatch_before_handler_runs() -> None:
    calls: list[list[object]] = []

    def handler(paths: list[object]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={"type": "array", "items": {"type": "string"}},
            handler=handler,
        )
    )
    arguments = ["README.md", 123]

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("invalid_item", [True, False])
def test_tool_registry_denies_integer_array_item_bool_before_handler_runs(
    invalid_item: bool,
) -> None:
    calls: list[list[object]] = []

    def handler(counts: list[object]) -> dict[str, int]:
        calls.append(counts)
        return {"count": len(counts)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="sum_counts",
            risk="read_only",
            description="Sum integer counts.",
            parameters={"type": "array", "items": {"type": "integer"}},
            handler=handler,
        )
    )
    arguments = [1, invalid_item]

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("sum_counts", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "sum_counts",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_boolean_array_item_type_mismatch_before_handler_runs() -> None:
    calls: list[list[object]] = []

    def handler(flags: list[object]) -> dict[str, int]:
        calls.append(flags)
        return {"count": len(flags)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="set_flags",
            risk="read_only",
            description="Set boolean flags.",
            parameters={"type": "array", "items": {"type": "boolean"}},
            handler=handler,
        )
    )
    arguments = [True, "false"]

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("set_flags", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "set_flags",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        [{"path": "README.md", "extra": "x"}],
        [{"path": ""}],
        [{}],
        [{"path": 123}],
    ],
)
def test_tool_registry_denies_array_items_that_do_not_match_full_item_schema_before_handler_runs(
    arguments: list[dict[str, object]],
) -> None:
    calls: list[list[dict[str, object]]] = []

    def handler(paths: list[dict[str, object]]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["path"],
                    "properties": {"path": {"type": "string", "minLength": 1}},
                    "additionalProperties": False,
                },
            },
            handler=handler,
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        ["README.md"],
        ["README.md", "pyproject.toml", "src/forgecode_agent/tools.py"],
    ],
)
def test_tool_registry_denies_array_length_constraints_before_handler_runs(
    arguments: list[str],
) -> None:
    calls: list[list[str]] = []

    def handler(paths: list[str]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 2,
            },
            handler=handler,
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_duplicate_array_items_when_unique_items_true_before_handler_runs() -> None:
    calls: list[list[str]] = []

    def handler(paths: list[str]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={
                "type": "array",
                "items": {"type": "string"},
                "uniqueItems": True,
            },
            handler=handler,
        )
    )
    arguments = ["README.md", "README.md"]

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_allows_unique_array_items_when_unique_items_true() -> None:
    calls: list[list[str]] = []

    def handler(paths: list[str]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={
                "type": "array",
                "items": {"type": "string"},
                "uniqueItems": True,
            },
            handler=handler,
        )
    )
    arguments = ["README.md", "pyproject.toml"]

    result = registry.execute("batch_read", arguments)

    assert result == {"count": 2}
    assert calls == [arguments]
    assert registry.calls == [
        {"tool": "batch_read", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_executes_array_schema_with_list_as_single_positional_argument() -> None:
    calls: list[list[str]] = []

    def handler(paths: list[str]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple files.",
            parameters={"type": "array"},
            handler=handler,
        )
    )
    arguments = ["README.md", "pyproject.toml"]

    result = registry.execute("batch_read", arguments)

    assert result == {"count": 2}
    assert calls == [arguments]
    assert registry.calls == [
        {"tool": "batch_read", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_preserves_array_item_type_only_validation() -> None:
    calls: list[list[str]] = []

    def handler(modes: list[str]) -> dict[str, int]:
        calls.append(modes)
        return {"count": len(modes)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="set_modes",
            risk="read_only",
            description="Set modes.",
            parameters={
                "type": "array",
                "items": {"type": "string"},
            },
            handler=handler,
        )
    )
    arguments = ["safe"]

    result = registry.execute("set_modes", arguments)

    assert result == {"count": 1}
    assert calls == [arguments]
    assert registry.calls == [
        {"tool": "set_modes", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_wraps_handler_failures_without_leaking_raw_message() -> None:
    def handler(path: str) -> dict[str, str]:
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
            handler=handler,
        )
    )
    arguments = {"path": "README.md"}

    with pytest.raises(ToolExecutionError) as exc_info:
        registry.execute("read_file", arguments)

    assert exc_info.value.tool_name == "read_file"
    assert exc_info.value.error_type == "RuntimeError"
    assert str(exc_info.value) == "tool execution failed"
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": arguments,
            "status": "failed",
            "reason": "tool_error",
            "error_type": "RuntimeError",
        }
    ]
    assert "supersecret" not in repr(registry.calls)


def test_tool_registry_denies_unknown_extra_arguments_before_handler_runs(
    read_file_tool: ToolDefinition,
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name=read_file_tool.name,
            risk=read_file_tool.risk,
            description=read_file_tool.description,
            parameters=read_file_tool.parameters,
            handler=lambda path: calls.append({"path": path}),
        )
    )
    arguments = {"path": "README.md", "extra": "x"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("read_file", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_allows_additional_properties_matching_schema_dict() -> None:
    calls: list[dict[str, object]] = []

    def handler(name: str, **metadata: object) -> dict[str, object]:
        calls.append({"name": name, **metadata})
        return {"received": {"name": name, **metadata}}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="tag",
            risk="read_only",
            description="Tag with string metadata.",
            parameters={
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
                "additionalProperties": {"type": "string"},
            },
            handler=handler,
        )
    )
    arguments = {"name": "fixture", "source": "unit-test"}

    result = registry.execute("tag", arguments)

    assert result == {"received": arguments}
    assert calls == [arguments]
    assert registry.calls == [{"tool": "tag", "arguments": arguments, "status": "completed"}]


def test_tool_registry_denies_additional_properties_not_matching_schema_dict_before_handler_runs() -> None:
    calls: list[dict[str, object]] = []

    def handler(name: str, **metadata: object) -> None:
        calls.append({"name": name, **metadata})

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="tag",
            risk="read_only",
            description="Tag with string metadata.",
            parameters={
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
                "additionalProperties": {"type": "string"},
            },
            handler=handler,
        )
    )
    arguments = {"name": "fixture", "retries": 3}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("tag", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "tag",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_unknown_arguments_for_object_schema_before_handler_runs() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="ping",
            risk="read_only",
            description="Ping with no arguments.",
            parameters={"type": "object"},
            handler=lambda: calls.append({"called": "yes"}),
        )
    )
    arguments = {"unexpected": "value"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("ping", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "ping",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_object_property_string_not_in_enum_before_handler_runs() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="run_mode",
            risk="read_only",
            description="Run in a configured mode.",
            parameters={
                "type": "object",
                "properties": {"mode": {"type": "string", "enum": ["fast", "safe"]}},
                "required": ["mode"],
            },
            handler=lambda mode: calls.append({"mode": mode}),
        )
    )
    arguments = {"mode": "unsafe"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("run_mode", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "run_mode",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_denies_object_property_const_mismatch_before_handler_runs() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="set_mode",
            risk="read_only",
            description="Set a fixed mode.",
            parameters={
                "type": "object",
                "properties": {"mode": {"type": "string", "const": "safe"}},
                "required": ["mode"],
            },
            handler=lambda mode: calls.append({"mode": mode}),
        )
    )
    arguments = {"mode": "unsafe"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("set_mode", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "set_mode",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_allows_object_property_const_match() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="set_mode",
            risk="read_only",
            description="Set a fixed mode.",
            parameters={
                "type": "object",
                "properties": {"mode": {"type": "string", "const": "safe"}},
                "required": ["mode"],
            },
            handler=lambda mode: calls.append({"mode": mode}),
        )
    )
    arguments = {"mode": "safe"}

    result = registry.execute("set_mode", arguments)

    assert result is None
    assert calls == [{"mode": "safe"}]
    assert registry.calls == [
        {"tool": "set_mode", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_denies_top_level_object_const_mismatch_before_handler_runs() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="fixed_mode",
            risk="read_only",
            description="Run with one exact argument object.",
            parameters={
                "type": "object",
                "const": {"mode": "safe"},
                "properties": {"mode": {"type": "string"}},
                "required": ["mode"],
            },
            handler=lambda mode: calls.append({"mode": mode}),
        )
    )
    arguments = {"mode": "unsafe"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("fixed_mode", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "fixed_mode",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_allows_top_level_object_const_match() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="fixed_mode",
            risk="read_only",
            description="Run with one exact argument object.",
            parameters={
                "type": "object",
                "const": {"mode": "safe"},
                "properties": {"mode": {"type": "string"}},
                "required": ["mode"],
            },
            handler=lambda mode: calls.append({"mode": mode}),
        )
    )
    arguments = {"mode": "safe"}

    result = registry.execute("fixed_mode", arguments)

    assert result is None
    assert calls == [{"mode": "safe"}]
    assert registry.calls == [
        {"tool": "fixed_mode", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_denies_nested_bool_int_const_mismatch_before_handler_runs() -> None:
    calls: list[dict[str, object]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="set_flags",
            risk="read_only",
            description="Set exact nested flags.",
            parameters={
                "type": "object",
                "properties": {
                    "options": {
                        "type": "object",
                        "const": {"flag": 1},
                        "properties": {"flag": {"type": "boolean"}},
                        "required": ["flag"],
                    }
                },
                "required": ["options"],
            },
            handler=lambda options: calls.append({"options": options}),
        )
    )
    arguments = {"options": {"flag": True}}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("set_flags", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "set_flags",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("arguments", [{"name": "ab"}, {"name": "abcdef"}])
def test_tool_registry_denies_object_property_string_length_constraints_before_handler_runs(
    arguments: dict[str, str],
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="rename",
            risk="read_only",
            description="Rename an item.",
            parameters={
                "type": "object",
                "properties": {"name": {"type": "string", "minLength": 3, "maxLength": 5}},
                "required": ["name"],
            },
            handler=lambda name: calls.append({"name": name}),
        )
    )

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("rename", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "rename",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


@pytest.mark.parametrize("name", ["abc", "abcd", "abcde"])
def test_tool_registry_allows_object_property_string_length_boundaries(
    name: str,
) -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="rename",
            risk="read_only",
            description="Rename an item.",
            parameters={
                "type": "object",
                "properties": {"name": {"type": "string", "minLength": 3, "maxLength": 5}},
                "required": ["name"],
            },
            handler=lambda name: calls.append({"name": name}),
        )
    )

    result = registry.execute("rename", {"name": name})

    assert result is None
    assert calls == [{"name": name}]
    assert registry.calls == [
        {"tool": "rename", "arguments": {"name": name}, "status": "completed"}
    ]


def test_tool_registry_denies_object_property_string_pattern_mismatch_before_handler_runs() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="read_file",
            risk="read_only",
            description="Read a safe workspace path.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string", "pattern": r"^[A-Za-z0-9_./-]+$"}},
                "required": ["path"],
            },
            handler=lambda path: calls.append({"path": path}),
        )
    )
    arguments = {"path": "README.md; rm -rf /"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("read_file", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "read_file",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_allows_object_property_string_pattern_match() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="read_file",
            risk="read_only",
            description="Read a safe workspace path.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string", "pattern": r"^[A-Za-z0-9_./-]+$"}},
                "required": ["path"],
            },
            handler=lambda path: calls.append({"path": path}),
        )
    )
    arguments = {"path": "src/forgecode_agent/tools.py"}

    result = registry.execute("read_file", arguments)

    assert result is None
    assert calls == [{"path": "src/forgecode_agent/tools.py"}]
    assert registry.calls == [
        {"tool": "read_file", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_allows_object_property_string_unanchored_pattern_search_match() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="read_file",
            risk="read_only",
            description="Read a matching path.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string", "pattern": r"README"}},
                "required": ["path"],
            },
            handler=lambda path: calls.append({"path": path}),
        )
    )
    arguments = {"path": "docs/README.md"}

    result = registry.execute("read_file", arguments)

    assert result is None
    assert calls == [{"path": "docs/README.md"}]
    assert registry.calls == [
        {"tool": "read_file", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_denies_array_item_string_pattern_mismatch_before_handler_runs() -> None:
    calls: list[list[str]] = []

    def handler(paths: list[str]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple paths.",
            parameters={
                "type": "array",
                "items": {"type": "string", "pattern": r"^[A-Za-z0-9_./-]+$"},
            },
            handler=handler,
        )
    )
    arguments = ["README.md", "unsafe path;rm"]

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("batch_read", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "batch_read",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]


def test_tool_registry_allows_array_item_string_pattern_match() -> None:
    calls: list[list[str]] = []

    def handler(paths: list[str]) -> dict[str, int]:
        calls.append(paths)
        return {"count": len(paths)}

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="batch_read",
            risk="read_only",
            description="Read multiple paths.",
            parameters={
                "type": "array",
                "items": {"type": "string", "pattern": r"^[A-Za-z0-9_./-]+$"},
            },
            handler=handler,
        )
    )
    arguments = ["README.md", "src/forgecode_agent/tools.py"]

    result = registry.execute("batch_read", arguments)

    assert result == {"count": 2}
    assert calls == [arguments]
    assert registry.calls == [
        {"tool": "batch_read", "arguments": arguments, "status": "completed"}
    ]


def test_tool_registry_denies_unknown_arguments_for_empty_schema_before_handler_runs() -> None:
    calls: list[dict[str, str]] = []
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="ping",
            risk="read_only",
            description="Ping with no arguments.",
            parameters={},
            handler=lambda: calls.append({"called": "yes"}),
        )
    )
    arguments = {"unexpected": "value"}

    with pytest.raises(ToolCallDenied, match="invalid_arguments"):
        registry.execute("ping", arguments)

    assert calls == []
    assert registry.calls == [
        {
            "tool": "ping",
            "arguments": arguments,
            "status": "denied",
            "reason": "invalid_arguments",
        }
    ]
