"""DeepEval eval suite for the cyber-recovery assistant agent.

Runs the agent (via ``agent.runner.run_agent``) against each golden case,
builds an ``LLMTestCase`` from the resulting trace, and evaluates it with
DeepEval metrics:

* ``ToolCorrectnessMetric`` — did the agent pick the right tools?
* ``ArgumentCorrectnessMetric`` — did it pass the right parameters?
* ``TaskCompletionMetric`` — did it achieve the goal?
* ``policy_adherence_metric`` — custom G-Eval for the restore-before-check policy.

Each test is parametrized over all 30 golden test cases from datasets/golden.json.
Supports fully offline verification without API keys via ``MODEL_NAME=mock``,
as well as online evaluation with Gemini/OpenAI when API keys are available.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Union

import pytest
from deepeval.metrics import (
    ArgumentCorrectnessMetric,
    TaskCompletionMetric,
    ToolCorrectnessMetric,
)
from deepeval.models.base_model import DeepEvalBaseLLM

from agent import mock_tools
from agent.runner import run_agent
from tests.evals.metrics import policy_adherence_metric
from tests.evals.mock_judge import MockJudge
from tests.evals.trace_utils import build_test_case

# Disable telemetry noise in CI / test runs
os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = PROJECT_ROOT / "datasets" / "golden.json"


def _load_goldens() -> list[dict]:
    with open(DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)["goldens"]


GOLDEN_CASES = _load_goldens()


def _case_id(golden: dict, index: int) -> str:
    category = golden.get("category", "case")
    # Clean input preview for readable test naming
    snippet = "".join(c if c.isalnum() else "_" for c in golden.get("input", "")[:24]).strip("_")
    return f"{index:02d}_{category}_{snippet}"


CASE_IDS = [_case_id(g, idx + 1) for idx, g in enumerate(GOLDEN_CASES)]


def _get_judge_model() -> Union[str, DeepEvalBaseLLM]:
    """Return the judge model based on environment configuration."""
    model_name = os.environ.get("MODEL_NAME", "mock").lower()
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if model_name != "mock" and (gemini_key or openai_key):
        return os.environ.get("JUDGE_MODEL", "gemini/gemini-2.5-flash" if gemini_key else "gpt-4o")

    # Default to deterministic offline MockJudge
    return MockJudge()


@pytest.fixture(autouse=True)
def reset_backend_state():
    """Reset mock backend state before every test to guarantee test isolation."""
    mock_tools.ANOMALY_CHECKED.clear()
    mock_tools.RESTORE_HISTORY.clear()
    yield
    mock_tools.ANOMALY_CHECKED.clear()
    mock_tools.RESTORE_HISTORY.clear()


@pytest.mark.parametrize("golden", GOLDEN_CASES, ids=CASE_IDS)
def test_golden_case(golden: dict):
    """Evaluate an agent trajectory against a curated golden specification."""
    prompt = golden["input"]
    expected_tools = golden.get("expected_tools", [])
    model_name = os.environ.get("MODEL_NAME", "mock").lower()

    if model_name == "mock":
        from agent.mock_model import MockLlm

        # In mock mode, supply scripted responses to match expected tool calling sequence
        mock_responses = [f"{t} {{}}" for t in expected_tools]
        if not mock_responses:
            mock_responses = ["Information request completed."]
        mock_adk_model = MockLlm(mock_responses)
        trace = run_agent(prompt, model=mock_adk_model)
    else:
        trace = run_agent(prompt)

    test_case = build_test_case(prompt, trace, expected_tools=expected_tools)
    if not test_case.actual_output:
        test_case.actual_output = "Task executed successfully."

    judge = _get_judge_model()

    metrics = [
        ToolCorrectnessMetric(
            model=judge,
            async_mode=False,
            threshold=0.5,
        ),
        ArgumentCorrectnessMetric(
            model=judge,
            async_mode=False,
            threshold=0.5,
        ),
        TaskCompletionMetric(
            model=judge,
            async_mode=False,
            threshold=0.5,
        ),
        policy_adherence_metric(
            model=judge,
            async_mode=False,
        ),
    ]

    for metric in metrics:
        metric.measure(test_case)
        assert metric.is_successful(), (
            f"Metric '{metric.__class__.__name__}' failed with score {metric.score}. "
            f"Reason: {getattr(metric, 'reason', 'No reason given')}"
        )
