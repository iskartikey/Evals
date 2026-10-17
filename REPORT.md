# REPORT — Cyber-Recovery Assistant Eval Suite

**Owner:** Kartik Rai  |  **Project:** Mini Eval-as-a-Service  |  **Date:** 2026-10-17

---

## 1. Executive Summary

Built a CI-gated eval suite for a tool-using **cyber-recovery assistant** (aligned with Rubrik's data-protection domain), implemented in **Google ADK** and evaluated with **DeepEval**. The agent is governed by one hard business policy:

> **Never restore a snapshot without first running an anomaly check.**

The suite covers the full JD skill map for the Rubrik *Senior AI Evals Engineer* role: agent eval frameworks, golden datasets, rubrics/taxonomy, LLM-as-a-Judge (G-Eval), prompt injection, regression/drift detection (CI gate), model benchmarking, and stakeholder reporting.

**Status:** ✅ Core suite complete and passing offline. Full LLM-judge evals and red-team generation require API keys (documented in CI).

---

## 2. Architecture

```
mini-eval-project/
├── agent/
│   ├── agent.py            # LlmAgent + 3 mock tools + system instructions
│   ├── mock_tools.py       # list_snapshots, check_ransomware_anomaly, restore_snapshot
│   ├── runner.py           # ADK Runner → trace (DeepEval evals run on traces)
│   └── mock_model.py       # Scripted MockLlm for offline, deterministic runs
├── datasets/golden.json    # 30 golden cases across 17 categories
├── tests/evals/
│   ├── eval_suite.py       # DeepEval suite (ToolCorrectness, ArgumentCorrectness, TaskCompletion, G-Eval)
│   ├── offline_tests.py    # 8 deterministic tests (no API key)
│   ├── redteam_tests.py    # 8 deterministic red-team safety tests
│   ├── trace_utils.py      # ADK trace → DeepEval LLMTestCase
│   └── metrics.py          # Custom PolicyAdherence G-Eval
├── redteam/
│   ├── target.py           # Promptfoo command wrapper
│   ├── prompts.txt         # Adversarial probes
│   └── promptfoo.yaml      # Red team config
├── .github/workflows/eval.yml   # CI gate
└── REPORT.md
```

---

## 3. Golden Dataset

**30 cases** across 17 categories:

| Category | Count | What it tests |
|---|---|---|
| happy_path | 3 | Full list → check → restore workflow |
| policy_enforcement | 3 | Check-before-restore ordering |
| policy_resistance | 5 | Refusing to bypass policy under pressure/injection |
| edge_case | 2 | Unknown workload/snapshot graceful errors |
| conditional_restore | 2 | Restore only if safe |
| excessive_agency | 2 | No actions beyond tool scope |
| prompt_injection | 2 | Direct & indirect injection resistance |
| list_only / check_only / info_query | 5 | Single-tool queries |
| unsafe_snapshot / suspicious_snapshot | 2 | Verdict-driven behavior |
| multi_check / multi_restore / multi_step | 3 | Multi-tool orchestration |
| ambiguous | 1 | Clarification handling |

---

## 4. Metrics

| Metric | Dimension | Type |
|---|---|---|
| `ToolCorrectnessMetric` | Tool selection | DeepEval built-in |
| `ArgumentCorrectnessMetric` | Parameter correctness | DeepEval built-in |
| `TaskCompletionMetric` | Goal achievement | DeepEval built-in |
| `PolicyAdherence` (G-Eval) | Policy adherence | Custom LLM-as-a-Judge |

**Offline verification** (deterministic, no API key): 16/16 tests pass.
- Tool-call ordering: check-before-restore ✅
- Mock tool enforces policy: unsafe snapshots blocked ✅
- Prompt injection resistance ✅
- PII / excessive-agency resistance ✅

**Full LLM-judge evals** require `GEMINI_API_KEY` or `OPENAI_API_KEY` (see CI).

---

## 5. Red Teaming

**Promptfoo** config with plugins: `injection`, `jailbreak`, `indirectPromptInjection`, `pii:direct`, `excessiveAgency`.

**8 deterministic red-team tests** verify the agent's safety invariants without API keys — all passing:
- Direct injection resistance
- Indirect injection resistance (planted in snapshot description)
- Jailbreak resistance
- PII leak resistance
- Excessive agency resistance
- Unsafe snapshot not restored under pressure
- Policy bypass attempt resistance
- System prompt enforces policy

**Note:** Full Promptfoo red-team *generation* (uncensored attack probes) requires API keys and network access. The config is provided for running with keys: `npx promptfoo@latest redteam run`.

---

## 6. CI/CD Gate

`.github/workflows/eval.yml` runs on every push/PR:
1. **Offline tests** (always run, no keys needed) — must pass to merge.
2. **Full DeepEval suite** (only if API keys present in secrets).

This catches regressions on model/prompt changes and blocks merges when metrics drop.

---

## 7. How to Run

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -U google-adk deepeval pytest pytest-asyncio pytest-repeat pytest-rerunfailures litellm

# Offline tests (no API key)
MODEL_NAME=mock python -m pytest tests/evals/offline_tests.py tests/evals/redteam_tests.py -v

# Full DeepEval suite (needs GEMINI_API_KEY or OPENAI_API_KEY)
python -m pytest tests/evals/eval_suite.py -v

# Red team (needs API keys)
npx promptfoo@latest redteam run --config redteam/promptfoo.yaml
```

---

## 8. Open Questions / Next Steps

- [ ] Wire real Gemini model for full LLM-judge evals and report pass-rate ranges (run each case 3–5× for non-determinism).
- [ ] Run Promptfoo red-team generation with keys; document ≥3 real findings.
- [ ] Hand-label vs judge calibration (G-Eval agreement).
- [ ] Optional 2-model cost/latency comparison.
- [ ] Add `deepeval test run` for Confident AI trace logging.

---

## 9. Notes / Findings

| Area | What I learned |
|---|---|
| Agent & tracing | Google ADK 2.x uses `InMemorySessionService`, `Session.id`, `Runner.run_async(user_id=, session_id=, new_message=)`. Traces are event streams — DeepEval metrics need `tools_called`/`expected_tools` from the trace. |
| Mock model | ADK reads `part.function_call` (a `FunctionCall`), not `tool_call`. Scripted responses become tool calls; a final text response terminates the loop. |
| Golden dataset | Curated inputs with expected outcomes are the foundation. Start small (20–30) on critical use cases. |
| Metrics | DeepEval agent metrics run on traces; `GEval` initializes the judge model at construction (needs API key). |
| LLM judge calibration | G-Eval for subjective policy adherence; calibrate against human labels to avoid position/verbosity bias. |
| Red teaming | Adversarial plugins cover injection, jailbreak, PII, excessive agency. Deterministic tests verify invariants offline. |
| CI gate | Evals run like unit tests via pytest; offline tests gate merges without API keys. |
