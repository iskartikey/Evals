"""Helpers to convert ADK agent traces into DeepEval test cases.

DeepEval's agent metrics (ToolCorrectness, ArgumentCorrectness, TaskCompletion,
etc.) operate on ``LLMTestCase`` objects. This module extracts the tool calls
and final text from an ADK trace and builds a ready-to-evaluate test case.
"""

from __future__ import annotations

from typing import Any

from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams, ToolCallType


def extract_tool_calls(trace: dict) -> list[ToolCall]:
    """Extract tool calls from an ADK trace's event stream.

    Args:
        trace: The trace dict returned by ``agent.runner.run_agent``.

    Returns:
        A list of DeepEval ``ToolCall`` objects.
    """
    tool_calls: list[ToolCall] = []
    for event in trace.get("_all_events", []):
        content = event.get("content") or {}
        for part in content.get("parts", []):
            fc = part.get("function_call")
            if fc and fc.get("name"):
                tool_calls.append(
                    ToolCall(
                        name=fc["name"],
                        type=ToolCallType.FUNCTION,
                        input_parameters=fc.get("args", {}),
                        output=part.get("tool_response"),
                    )
                )
    return tool_calls


def extract_final_text(trace: dict) -> str:
    """Extract the final assistant text from an ADK trace.

    Walks the event stream and returns the last non-empty text part.
    """
    text = ""
    for event in trace.get("_all_events", []):
        content = event.get("content") or {}
        for part in content.get("parts", []):
            if part.get("text"):
                text = part["text"]
    return text


def build_test_case(
    input_prompt: str,
    trace: dict,
    expected_tools: list[str] | None = None,
) -> LLMTestCase:
    """Build an ``LLMTestCase`` from an ADK trace.

    Args:
        input_prompt: The original user prompt.
        trace: The trace dict from ``agent.runner.run_agent``.
        expected_tools: Optional list of expected tool names for
            ToolCorrectness evaluation.

    Returns:
        A DeepEval ``LLMTestCase`` ready for metric evaluation.
    """
    tools_called = extract_tool_calls(trace)
    actual_output = extract_final_text(trace)

    return LLMTestCase(
        input=input_prompt,
        actual_output=actual_output,
        tools_called=tools_called,
        expected_tools=[
            ToolCall(name=name, type=ToolCallType.FUNCTION)
            for name in (expected_tools or [])
        ],
    )
