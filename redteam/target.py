"""Promptfoo target connector for the cyber-recovery agent.

Supports both:
1. CLI stdin/stdout invocation:
   echo '{"prompt": "Restore snap-1001"}' | python redteam/target.py
2. Promptfoo native Python custom provider:
   call_api(prompt, options, context)
"""

from __future__ import annotations

import io
import json
import os
import sys
import warnings

# Filter warnings so stdout remains strict JSON
warnings.filterwarnings("ignore")

# Ensure the project root is importable when invoked by Promptfoo.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.runner import run_agent
from agent import mock_tools


def invoke_agent(prompt: str) -> str:
    """Run the agent and extract final assistant text output."""
    mock_tools.reset_state()
    model_name = os.environ.get("MODEL_NAME", "mock").lower()

    # Capture any accidental print statements or logs from ADK
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        if model_name == "mock":
            from agent.mock_model import MockLlm
            trace = run_agent(prompt, model=MockLlm(["Done."]))
        else:
            trace = run_agent(prompt)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    final_text = ""
    for event in trace.get("_all_events", []):
        content = event.get("content") or {}
        for part in content.get("parts", []):
            if part.get("text"):
                final_text = part["text"]

    return final_text or "Recovery assistant processed the command."


def call_api(prompt: str, options: dict | None = None, context: dict | None = None) -> dict:
    """Promptfoo custom Python provider entrypoint."""
    try:
        output = invoke_agent(prompt)
        return {"output": output}
    except Exception as exc:
        return {"error": str(exc)}


def main() -> None:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw)
        prompt = payload.get("prompt", "")
    except json.JSONDecodeError:
        prompt = raw

    if not prompt:
        print(json.dumps({"error": "No prompt provided"}))
        return

    try:
        response = invoke_agent(prompt)
        print(json.dumps({"response": response}))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))


if __name__ == "__main__":
    main()
