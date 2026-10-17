"""A deterministic mock LLM for offline testing of the runner.

This lets the eval harness run without API keys by scripting tool-call
trajectories. It is used only for local verification; real evals should use a
real model via MODEL_NAME.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class MockLlm(BaseLlm):
    """A scripted LLM that returns a fixed sequence of responses.

    Each scripted string is interpreted as a tool call: the first whitespace-
    separated token is the tool name, the remainder is parsed as JSON args
    (or treated as free text if not valid JSON). This simulates an agent that
    lists snapshots, checks anomalies, and restores snapshots.
    """

    def __init__(self, responses: list[str], model: str = "mock-model", final_text: str = "Done.", **data: Any):
        super().__init__(model=model, **data)
        self._responses = responses
        self._final_text = final_text
        self._index = 0

    @staticmethod
    def _make_part(text: str) -> types.Part:
        parts = text.strip().split(None, 1)
        name = parts[0]
        arg_text = parts[1] if len(parts) > 1 else "{}"
        try:
            import json

            args = json.loads(arg_text)
        except (json.JSONDecodeError, ValueError):
            args = {"query": text}
        return types.Part(
            function_call=types.FunctionCall(name=name, args=args)
        )

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncIterator[LlmResponse]:
        if self._index < len(self._responses):
            text = self._responses[self._index]
            self._index += 1
            yield LlmResponse(
                content=types.Content(role="model", parts=[self._make_part(text)])
            )
        else:
            # After all scripted tool calls, emit a final summarization text so
            # the agent produces a proper final response.
            yield LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=self._final_text)],
                )
            )
