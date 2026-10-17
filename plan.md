# Mini Eval-as-a-Service — Project Understanding

**Owner:** Kartik Rai  |  **Timeline:** One weekend (Fri night → Sun night)
**Goal:** Learn AI agent evaluation by building a small, CI-gated eval suite for a tool-using agent, mapped to the skills in the *Senior AI Evals Engineer* JD.

---

## 1. What Are "Evals" (Plain English)

Traditional testing is deterministic: `assert add(2,2) == 4`. AI agents are **non-deterministic** — same input can yield different outputs, tool calls and reasoning paths. So instead of assert-equals, we **measure quality along dimensions** and set pass thresholds.

| Dimension | Question it answers |
|---|---|
| Task completion | Did the agent achieve the user's goal? |
| Tool correctness | Did it pick the right tool? |
| Argument correctness | Did it pass the right parameters? |
| Reasoning / plan quality | Was the plan logical and followed? |
| Step efficiency | Did it waste steps? |
| Faithfulness / groundedness | Did it stay grounded in provided context? |
| Safety | Does it resist prompt injection, jailbreaks, PII leakage? |
| Policy adherence | Does it follow business rules? |

### Three layers of agent evaluation
| Layer | Scope | Example metrics (DeepEval) |
|---|---|---|
| Reasoning | Trajectory | PlanQualityMetric, PlanAdherenceMetric |
| Action | Component (LLM span) | ToolCorrectnessMetric, ArgumentCorrectnessMetric |
| Execution | Trajectory | TaskCompletionMetric, StepEfficiencyMetric |

---

## 2. Project Definition

**Agent under test:** A small *cyber-recovery assistant* (enterprise cyber-recovery domain).

**Mock tools:**
- `list_snapshots(workload_id)`
- `check_ransomware_anomaly(snapshot_id)`
- `restore_snapshot(snapshot_id)`

**Key business policy to test:** *Never restore a snapshot without first running an anomaly check.*

**Framework:** Google ADK (preferred, matches JD) — fallback LangGraph.

**Tech stack**
| Purpose | Tool |
|---|---|
| Language | Python |
| Test runner | pytest |
| Eval framework | DeepEval |
| Red teaming | Promptfoo |
| CI/CD | GitHub Actions |
| Judge model | Any API model or local (e.g., Ollama) |

---

## 3. Repo Layout

```
mini-eval-project/
├── agent/                  # agent + mock tools
├── datasets/golden.json    # 25–30 golden test cases
├── tests/evals/            # DeepEval pytest suites
├── redteam/                # Promptfoo config + results
├── .github/workflows/eval.yml
└── REPORT.md               # final findings & ship/no-ship call
```

---

## 4. Weekend Schedule

| When | Block | Tasks | JD mapping |
|---|---|---|---|
| Fri night (~45 min) | Setup | Repo, venv, `pip install -U deepeval`, API keys, skim DeepEval agent quickstart | Python & tooling |
| Sat AM (3 h) | Agent & tracing | Build agent + 3 mock tools; add `@observe` tracing (DeepEval agent evals run on traces) | Agentic patterns, tool use |
| Sat PM (3 h) | Golden dataset & metrics | 25–30 cases (happy path, wrong tool, bad args, ambiguous request, multi-step restore); add ToolCorrectness, ArgumentCorrectness, TaskCompletion | Golden datasets, rubrics, taxonomy |
| Sat eve (1 h) | LLM-as-judge | Custom G-Eval "policy adherence" metric; hand-label 10 outputs and compare with judge | LLM-as-a-Judge (Must) |
| Sun AM (3 h) | Red teaming | Promptfoo red team: prompt injection, jailbreak, PII leak, excessive agency; plant indirect injection in a snapshot description | Safety evals, prompt injection (Must) |
| Sun PM (2.5 h) | CI gate & regression | `eval.yml` runs `deepeval test run` on every PR with thresholds; intentionally break prompt to confirm gate fails | CI/CD eval gates, regression/drift |
| Sun eve (1.5 h) | Report | `REPORT.md`: pass rate per metric, top 3 failures, root causes, ship/no-ship; optional 2-model cost/latency comparison | Stakeholder reporting, model benchmarking |

---

## 5. Key Concepts to Internalise

### Golden dataset
Curated inputs with expected outcomes — the foundation of the suite. Start small (20–30 cases) on the most critical use case.

### LLM-as-a-Judge
Using an LLM to score another LLM's output against a rubric.
- **G-Eval** — custom, subjective, single-output criteria
- **DAG metric** — deterministic, branching criteria
- **QAG-style built-ins** — RAG / agent metrics
- **Pairwise comparison** — which prompt/model is better

**Pitfalls:** position bias, verbosity bias, self-preference. **Mitigate:** rotate answer order, decompose rubrics into discrete checks, calibrate against human labels.

### Red teaming
Adversarial testing: direct & indirect prompt injection, jailbreaks, PII leakage, excessive agency, hallucination. Promptfoo generates attack probes via *plugins* (adversarial generators) wrapped in *strategies* (attack patterns).

### CI/CD eval gate
Evals run like unit tests via `deepeval test run` + `assert_test`, blocking merges when metrics drop below threshold (catches regressions on model/prompt changes).

### Statistics
Agents are non-deterministic → run each case **3–5 times**, report pass-rate ranges, avoid overfitting to the benchmark and metric gaming.

---

## 6. Definition of Done (Sunday Night)

- [ ] Repo with a **passing CI run** and one **intentionally failing PR**
- [ ] Red-team report with **≥ 3 real findings**
- [ ] One-page `REPORT.md` you can walk through in an interview
- [ ] Hand-label vs judge agreement noted

---

## 7. JD Skill Coverage Map

| JD Requirement | Covered by |
|---|---|
| Agent eval frameworks | DeepEval suite + traces |
| Golden datasets & harnesses | `datasets/golden.json` |
| Eval rubrics/taxonomy | Metric set + policy G-Eval |
| LLM-as-a-Judge (Must) | Custom G-Eval + human calibration |
| Prompt injection (Must) | Promptfoo + indirect injection test |
| Regression & drift detection | CI gate with thresholds |
| Model benchmarking | Optional 2-model comparison |
| Reporting to stakeholders | `REPORT.md` |
| Python, pytest, CI/CD | Entire stack |

---

## 8. Quick-Start Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -U deepeval
deepeval login            # optional: store results on Confident AI

# Local judge (optional)
deepeval set-local-model --model-name="ollama/qwen2.5:32b"

# Run evals
deepeval test run tests/evals/

# Red team (requires Node.js >= 22.22.0)
npx promptfoo@latest redteam setup
npx promptfoo@latest redteam run
npx promptfoo@latest redteam report
```

---

## 9. Reference Material

- DeepEval — AI Agent Evaluation Quickstart: https://deepeval.com/docs/getting-started-agents
- DeepEval — Agent Evaluation Metrics: https://deepeval.com/guides/guides-ai-agent-evaluation-metrics
- DeepEval — LLM-as-a-Judge guide: https://deepeval.com/blog/llm-as-a-judge
- Promptfoo — Red team quickstart: https://www.promptfoo.dev/docs/red-team/quickstart/
- Promptfoo — How to red team LLM apps: https://www.promptfoo.dev/docs/guides/llm-redteaming/
- Viva Learning: *Evaluating AI Agents with Google ADK* (LinkedIn Learning)
- Viva Learning: *Design evaluation frameworks for multi-agent solutions with Microsoft Foundry* (Microsoft Learn)

---

## 10. My Notes / Findings (fill in as you go)

| Area | What I learned | Open questions |
|---|---|---|
| Agent & tracing | | |
| Golden dataset | | |
| Metrics | | |
| LLM judge calibration | | |
| Red teaming | | |
| CI gate | | |
