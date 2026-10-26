# 08 — Evaluation: RAGAS and DeepEval

## Learning objectives

Build an **eval pipeline** with RAGAS (faithfulness, relevancy, context metrics) and DeepEval (G-Eval, agent tool correctness); run it in **CI** as a quality gate on every prompt/retrieval change — the same discipline as integration tests, but for non-deterministic outputs.

---

## Beginner → senior bridge

**Unit tests** check deterministic code. LLM outputs are **stochastic** — same prompt can vary. Eval replaces “hope it works” with **measured quality on a fixed dataset**, like regression tests for model + prompt + retrieval combined.

**Release rule of thumb:** no change to `prompt.md`, `retriever`, or `model_id` without an **eval diff** attached to the PR.

---

## Why eval is non-optional

Unit tests assert **code**. LLM apps need **quality tests** on:

- Faithfulness (answer grounded in context?)  
- Relevance (answer on-topic?)  
- Tool correctness (right tool, right args?)  
- Agent task success (multi-step)

Ship **eval pipeline** in CI like you ship integration tests.

---

## RAGAS metrics (intuition)

| Metric | Question |
|--------|----------|
| **Faithfulness** | Is each claim supported by retrieved context? |
| **Answer relevancy** | Does answer address the question? |
| **Context precision** | Are retrieved chunks useful? |
| **Context recall** | Did retrieval find all needed info? |

Often uses **LLM-as-judge** — bias aware; use human spot checks.

```python
# Illustrative RAGAS usage — see ragas docs for API
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

dataset = ...  # questions, contexts, answers, ground_truths
result = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
```

**Token efficiency:** eval cost \(\propto\) dataset size × judge tokens — sample in dev, full set nightly.

### Building a RAGAS dataset (concrete)

```python
from datasets import Dataset

rows = [
    {
        "question": "What is the refund window?",
        "contexts": ["Section 4: Refunds within 30 days of purchase."],
        "answer": "You can refund within 30 days.",
        "ground_truth": "30 days",
    },
]
ds = Dataset.from_list(rows)
```

| Column | Required for |
|--------|----------------|
| `question` | User query |
| `contexts` | Retrieved chunks (list of strings) |
| `answer` | Model output |
| `ground_truth` | Optional reference for recall-style metrics |

### Interpreting scores

| Score | Rough meaning | What it measures (plain English) | Action if low |
|-------|---------------|----------------------------------|---------------|
| Faithfulness ↓ | Hallucination | Is every claim in the answer actually supported by the retrieved documents? (= **grounding**) | Tighter prompt, grounding rail, better chunks |
| Answer relevancy ↓ | Off-topic answer | Does the answer actually address what the user asked? | Planner node, query rewrite |
| Context precision ↓ | Junk in retrieval | Are the top-ranked retrieved chunks relevant, or is noise ranked high? | Reranker, chunking, metadata filters |
| Context recall ↓ | Missing docs | Did the retriever find ALL the documents needed to answer? | Ingestion gap, hybrid search |

> **What is "grounding" here?** Faithfulness and grounding measure the same thing: whether the model's claims are backed by evidence in the source documents. A **grounding rail** (module 06) blocks ungrounded answers at runtime. The faithfulness **eval metric** measures the same thing offline, on your test set. If faithfulness score is low, your model is hallucinating — making up facts not in the context.

---

## DeepEval pipeline

| Concept | Meaning |
|---------|---------|
| **Golden** | Expected ideal output / criteria |
| **LLMTestCase** | input, actual_output, retrieval_context, tools_called |
| **Metrics** | G-Eval, DAG, QAG, custom |

```python
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval

metric = GEval(
    name="Correctness",
    criteria="Answer must mention refund policy section 4.",
    threshold=0.7,
)

test_case = LLMTestCase(
    input="Can I refund after 30 days?",
    actual_output=model_output,
    retrieval_context=chunks,
)

assert_test(test_case, [metric])
```

### Metric families

- **G-Eval:** LLM scores with rubric.  
- **DAG:** decision tree of checks.  
- **QAG:** question generation + answer matching.

---

## Agent evals

| Metric | Use |
|--------|-----|
| Tool correctness | Expected tool name/args |
| Task completion | End state matches goal |
| Step efficiency | Too many tool loops? |

Course: DeepEval agent evaluation walkthrough.

```python
from deepeval.metrics import ToolCorrectnessMetric

tool_metric = ToolCorrectnessMetric(
    expected_tools=[{"name": "lookup_order", "input_parameters": {"order_id": "9921"}}],
)
# LLMTestCase includes tools_called from agent trace
```

---

## CI integration (senior pattern)

```yaml
# .github/workflows/eval.yml (sketch)
name: llm-eval
on:
  pull_request:
    paths: ["prompts/**", "app/graph/**", "retrieval/**"]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv sync && uv run pytest tests/eval/ --maxfail=1
```

Keep **golden set** in git (small) + larger set in object storage for nightly.

### Statistical gate

If baseline faithfulness \(\mu_0 = 0.92\), require \(\mu \geq \mu_0 - 0.02\) on PR sample (avoid noise from single run).

---

## Complete pipeline (course “IMPORTANT” lecture)

1. **Dataset** — golden questions from prod logs (de-identified).  
2. **Run app** — fixed prompt/model version.  
3. **Score** — RAGAS + DeepEval metrics.  
4. **Gate** — PR fails if faithfulness ↓ 2 pts vs baseline.  
5. **Dashboard** — LangSmith experiment or custom.

---

## Industry example

Stripe-style: **no prompt change** without eval diff on 500 golden payments support queries.

Netflix/Spotify-style: **offline** eval on logged queries (de-identified) + **online** A/B on engagement — you need both for product metrics LLM eval cannot see.

---

## Senior pitfalls

| Mistake | Why it hurts |
|---------|----------------|
| Eval only on happy path | Production is long tail |
| Same model as judge and app | Bias toward own phrasing |
| No version pin in eval run | “Regression” is config drift |
| One global threshold | Per-locale / per-product thresholds differ |

---

## Production notes

### Golden set management

| Concern | Solution |
|---------|----------|
| Where to store | Small set (< 200 rows): git repo `tests/eval/golden.json`. Large set: S3/GCS with version tag |
| How to curate | Sample from prod logs (de-identify PII); add edge cases manually; review quarterly |
| Schema | `{"question": str, "contexts": [str], "answer": str, "ground_truth": str, "metadata": {...}}` |
| Versioning | Tag golden set version alongside prompt version — eval baseline is meaningless if dataset changed |

### Nightly vs PR pipeline

| Pipeline | Trigger | Dataset | Budget | SLA |
|----------|---------|---------|--------|-----|
| **PR eval** | Pull request touching prompts/retrieval/graph | 20-50 golden questions | < $2 in judge tokens | < 5 min |
| **Nightly eval** | Cron schedule | Full golden set (200+) | < $20 in judge tokens | < 30 min |
| **Weekly deep eval** | Schedule | Full + adversarial + edge cases | < $50 | < 1 hour |

### Cost of eval runs

Eval itself calls the **judge model** — that costs tokens:

\[
\text{eval\_cost} = N_{\text{cases}} \times T_{\text{judge}} \times p_{\text{judge}}
\]

Example: 200 cases x 2000 judge tokens x $0.15/1M = $0.06 per nightly run. Cheap — but at 50 PRs/day x 50 cases each, total eval cost can exceed app cost.

### Incident: eval regression in production

1. Alert fires: rolling 7-day faithfulness drops below baseline.
2. Check last merged PRs touching prompts, retrieval, or model config.
3. Rollback to last known-good prompt version.
4. Re-run eval to confirm recovery.
5. RCA: why did PR eval pass but production regressed? (dataset coverage gap, different model, config drift)

---

## Practice

1. Build 20-question golden set for one capstone (module 12).  
2. Break faithfulness on purpose — inject wrong chunk — confirm metric drops.  
3. Add DeepEval `GEval` for tone (“professional, no legal advice”).

## Production-grade practice

4. **Build a nightly eval pipeline** — cron-triggered script that runs full golden set; writes results to JSONL; alerts on regression.
5. **Add eval to CI** — GitHub Actions workflow that runs 20-case subset on any PR touching `prompts/`; fail PR if faithfulness < 0.90.
6. **Curate a golden set from "production" logs** — take 30 real queries, de-identify PII, add ground truths, version in git.
7. **Run a cost analysis** — measure judge tokens consumed by RAGAS + DeepEval for 100 cases; project monthly eval cost at your PR volume.
8. **Simulate eval regression** — change one retrieval parameter (wrong k or wrong embedding); verify eval catches it before you would notice manually.

---

## Lecture map

LLM evaluation intro, RAGAS demo/terminologies/metrics, DeepEval goldens/pipeline/G-Eval/DAG/QAG, RAG evals, agent evals.

**Next:** [09-agent-memory.md](./09-agent-memory.md)
