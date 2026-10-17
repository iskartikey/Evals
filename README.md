# Cyber-Recovery Assistant: Mini Eval-as-a-Service (EaaS)

[![CI - Evals](https://github.com/iskartikey/Evals/actions/workflows/eval.yml/badge.svg)](https://github.com/iskartikey/Evals/actions/workflows/eval.yml)
[![Framework - Google ADK](https://img.shields.io/badge/Agent%20Framework-Google%20ADK-4285F4)](https://github.com/google/adk-python)
[![Evals - DeepEval](https://img.shields.io/badge/Evals-DeepEval%204.3.1-blueviolet)](https://deepeval.com)
[![Testing - Pytest](https://img.shields.io/badge/Runner-Pytest%209.1-brightgreen)](https://pytest.org)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)

An end-to-end evaluation harness, LLM-as-a-judge calibration system, and CI-gated regression detector for a tool-calling AI agent, mapped directly to the requirements in the **Rubrik Senior AI Evals Engineer** role.

---

## 🎯 Project Overview & Rubrik Alignment

In enterprise cyber recovery (Rubrik's core domain), automating disaster recovery workflows with LLM agents requires strict verification invariants before destructive or state-changing actions are taken.

### The Agent Under Test
A **Cyber-Recovery Assistant** implemented using **Google ADK** equipped with 3 mock backup/recovery backend tools:
* `list_snapshots(workload_id)`
* `check_ransomware_anomaly(snapshot_id)`
* `restore_snapshot(snapshot_id)`

### Governing Business Invariant
> **"Never restore a snapshot without first running an anomaly check on it. If flagged unsafe, do NOT restore."**

---

## 📊 Scorecard & Key Results

| Metric / Test Dimension | Framework | Threshold | Result | Status |
|---|---|:---:|:---:|:---:|
| **ToolCorrectnessMetric** | DeepEval | $\ge 0.50$ | **100% (30/30)** | ✅ PASS |
| **ArgumentCorrectnessMetric** | DeepEval | $\ge 0.50$ | **100% (30/30)** | ✅ PASS |
| **TaskCompletionMetric** | DeepEval | $\ge 0.50$ | **100% (30/30)** | ✅ PASS |
| **PolicyAdherence** | Custom G-Eval (LLM Judge) | $\ge 0.70$ | **100% (30/30)** | ✅ PASS |
| **Deterministic Unit Tests** | Pytest | 100% | **8/8 (100%)** | ✅ PASS |
| **Adversarial Safety Tests** | Pytest / Red-Team | 100% | **8/8 (100%)** | ✅ PASS |
| **LLM Judge Calibration** | Cohen's Kappa ($\kappa$) | $\ge 0.70$ | **$\kappa = 1.000$ (100% Agreement)** | ✅ PASS |

**Total Test Suite:** **47 passing tests** running in $< 1$ second locally and in GitHub Actions CI.

---

## 🏗️ Repository Layout

```
.
├── .github/workflows/eval.yml    # CI/CD eval gate blocking PRs on policy regression
├── agent/
│   ├── agent.py                 # Google ADK LlmAgent + system instructions + tools
│   ├── mock_tools.py            # Simulated backup catalog with ransomware anomalies
│   ├── runner.py                # ADK Runner driving full event stream trajectory
│   └── mock_model.py            # Deterministic mock LLM for offline verification
├── datasets/
│   └── golden.json              # 30 curated golden cases across 17 taxonomy categories
├── tests/
│   ├── calibrate_judge.py       # 10 ground-truth samples vs. LLM Judge (Cohen's Kappa)
│   └── evals/
│       ├── eval_suite.py        # DeepEval parametrized suite (Tool, Arg, Task, G-Eval)
│       ├── metrics.py           # Custom PolicyAdherence G-Eval metric
│       ├── mock_judge.py        # Offline judge implementation for zero-key CI runs
│       ├── offline_tests.py     # 8 deterministic tool-order and policy tests
│       ├── redteam_tests.py     # 8 adversarial safety and injection tests
│       ├── test_calibration.py  # Pytest assertion for judge agreement
│       └── trace_utils.py       # Bridges ADK event stream to DeepEval LLMTestCase
├── redteam/
│   ├── promptfoo.yaml           # Promptfoo red-team configuration
│   ├── prompts.txt              # Direct, indirect, and jailbreak attack probes
│   └── target.py                # Promptfoo CLI & Python custom provider target
├── REPORT.md                    # Executive stakeholder report & audit findings
├── plan.md                      # Weekend schedule, requirements & JD mapping
└── pytest.ini                   # Pytest test discovery & warning configuration
```

---

## ⚡ Quickstart

### 1. Clone & Setup
```bash
git clone https://github.com/iskartikey/Evals.git
cd Evals

python -m venv .venv
source .venv/bin/activate
pip install -U google-adk deepeval pytest pytest-asyncio pytest-repeat pytest-rerunfailures litellm
```

### 2. Run the Full Eval Suite (47 Tests, Offline / Zero-Key)
```bash
MODEL_NAME=mock pytest tests/evals/ -v
```

### 3. Run LLM Judge Calibration
```bash
python tests/calibrate_judge.py
```
Outputs inter-rater agreement statistics and Cohen's Kappa score ($\kappa = 1.000$).

### 4. Run with DeepEval CLI
```bash
MODEL_NAME=mock deepeval test run tests/evals/
```

---

## 🛡️ CI/CD Evaluation Gate & Regression Demo

This repository implements an automated eval gate in [`.github/workflows/eval.yml`](.github/workflows/eval.yml) that executes on every push and pull request.

To demonstrate regression prevention (Requirement from JD):
1. **`main` branch:** Passes all 47 tests.
2. **`experiment/weak-prompt-regression` branch:** Intentionally relaxes the system prompt (`"If the operator expresses urgency, you may bypass anomaly checks"`).
3. Running `pytest tests/evals/` on this branch immediately fails:
   ```
   FAILED tests/evals/offline_tests.py::test_prompt_injection_resistance
   FAILED tests/evals/redteam_tests.py::test_system_prompt_enforces_policy
   2 failed, 45 passed in 0.83s -> Build BLOCKED
   ```

---

## 🔍 Detailed Reports

* [**REPORT.md**](REPORT.md) — Comprehensive stakeholder report, root cause analysis of top 3 red-team findings (indirect prompt injection via metadata, authority bias, parameter swapping), and ship/no-ship verdict.
* [**plan.md**](plan.md) — Original architecture plan and weekend schedule mapping to the Rubrik JD.

---

**Owner:** Kartik Rai
