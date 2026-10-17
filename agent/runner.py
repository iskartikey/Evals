"""Runner that executes the cyber-recovery agent against a user prompt.

DeepEval agent evals run on traces, so this module drives the ADK Runner and
returns the resulting trace as a JSON-serializable dict. It also exposes a
convenience function that runs the agent N times (for the non-deterministic
pass-rate reporting described in the project plan).
"""

from __future__ import annotations

import asyncio
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agent.agent import get_agent


def run_agent(user_prompt: str, model_name: str | None = None, model: Any = None) -> dict:
    """Run the agent once and return a JSON-serializable trace.

    Args:
        user_prompt: The operator's request.
        model_name: Optional model override.
        model: Optional pre-built model instance (used for offline testing).
    """
    agent = get_agent(model_name)
    if model is not None:
        agent.model = model
    runner = Runner(
        agent=agent,
        app_name="mini-eval-project",
        session_service=InMemorySessionService(),
    )

    async def _run() -> dict:
        session = await runner.session_service.create_session(
            app_name="mini-eval-project", user_id="evaluator"
        )

        final_event: Any = None
        all_events: list[Any] = []
        async_gen = runner.run_async(
            user_id="evaluator",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part(text=user_prompt)]
            ),
        )

        async for event in async_gen:
            all_events.append(event)
            final_event = event

        trace = final_event.model_dump() if final_event is not None else {}
        trace["_all_events"] = [e.model_dump() for e in all_events]
        return trace

    return asyncio.run(_run())


def run_agent_n_times(user_prompt: str, n: int = 3) -> list[dict]:
    """Run the agent n times, returning a list of traces.

    Used to compute pass-rate ranges for non-deterministic metrics.
    """
    return [run_agent(user_prompt) for _ in range(n)]


if __name__ == "__main__":
    prompt = "List snapshots for wl-web-02 and restore the cleanest one."
    trace = run_agent(prompt)
    print("Final event author:", trace.get("author"))
    print("Final event text:", str(trace.get("content"))[:200])
