# 06 — AWS Bedrock Guardrails

## Learning objectives

Configure **managed** content filters, denied topics, PII handling, and **grounding** on Bedrock; version guardrails with app releases and gate changes with adversarial tests in CI.

---

Managed safety layer for **Bedrock model invocations** — no custom Colang required.

---

## Core topics (course M1–M5)

| Module | Topic |
|--------|--------|
| M1 | Clients, anatomy, first guardrail, trace structure |
| M2 | Content filters, confidence vs threshold, prompt attacks |
| M3 | Denied topics, word filters, **PII redaction** |
| M4 | **Grounding** and hallucination control for RAG |
| M5 | Versioning, monitoring, automated tests, cost vs open source |

---

## Concepts

**Confidence vs threshold:** filter fires when model confidence **>** configured threshold — tune to balance false positives/negatives.

\[
\text{block} \iff \text{confidence}(\text{category}) > \tau
\]

**Grounding:** require claims supported by **source documents** (RAG) — reduces hallucination on factual Q&A.

> **What is grounding?** When a model answers a question using RAG, it has access to retrieved document chunks. **Grounding** verifies that every claim in the model's answer is actually supported by those source chunks. If the model says "refund policy is 90 days" but no source document says that — it's **ungrounded** (a hallucination). Bedrock's grounding filter **automatically** checks this and blocks ungrounded answers. Without Bedrock, you'd build this yourself using NLI (Natural Language Inference) models or the RAGAS faithfulness metric (module 08).

---

## API pattern (conceptual)

```python
import boto3

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

response = bedrock.converse(
    modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
    guardrailConfig={
        "guardrailIdentifier": "gr-abc123",
        "guardrailVersion": "1",
    },
    messages=[{"role": "user", "content": [{"text": user_message}]}],
)
```

**Versioning:** ship `guardrailVersion` with app releases — rollback guardrail like code.

---

## When to use Bedrock guardrails vs app-level

| Use Bedrock guardrails | Use app-level (Guardrails AI / NeMo) |
|------------------------|--------------------------------------|
| All traffic through Bedrock | Multi-provider (OpenAI + Anthropic) |
| Central AWS IAM governance | Complex dialog flows |
| Grounding with Bedrock KB | Custom business validators |

---

## Monitoring

CloudWatch metrics: `GuardrailInterventions`, latency overhead. **Automated test suite:** golden adversarial prompts in CI (course M5).

---

## Content filters and prompt attacks (M2)

| Attack type | Mitigation |
|-------------|------------|
| Jailbreak templates | Content filter + denied topics |
| Prompt injection via RAG | Input filter + scoped retrieval |
| Low-confidence toxic | Tune threshold \(\tau\) — measure FP/FN on golden set |

**False positive:** legitimate medical HR question blocked → lower threshold or allowlist topic.

**False negative:** harassment slips through → raise threshold + output filter.

---

## PII and grounding (M3–M4)

- **PII redaction:** PII = Personally Identifiable Information (names, emails, SSNs, credit card numbers). Bedrock's PII filter **automatically detects** these in user input or model output and either **masks** them (replaces with `[PII]`) or **blocks** the request entirely. You configure which entity types to catch (e.g., catch SSN + credit card, but allow names).

- **Grounding:** answers must cite `source` chunks from Bedrock Knowledge Base. Bedrock checks each sentence in the model's response against the retrieved documents. If a claim has **no supporting evidence** in the source chunks, Bedrock flags it as ungrounded. This ties directly to the **faithfulness** eval metric (module 08) — both measure the same thing: "did the model make this up?"

---

## M5: versioning and ops

Treat `guardrailVersion` like **API version** in deploy manifest:

```yaml
# deploy manifest sketch
model_id: anthropic.claude-3-5-sonnet-...
guardrail_id: gr-abc123
guardrail_version: "3"
prompt_version: "hr-assistant-2026-03-01"
```

Run **automated adversarial suite** on version bump; compare block rates and latency.

---

## Open source vs AWS (course M5_P2)

| | Self-hosted validators | Bedrock guardrails |
|---|------------------------|-------------------|
| Multi-cloud | Yes | AWS only |
| Ops burden | You run | Managed |
| Grounding with KB | DIY | Integrated |

Many teams use **both**: Guardrails AI in app + Bedrock guardrails when on Bedrock.

---

## Production notes

### Terraform / IaC for guardrails

```hcl
# Conceptual — AWS provider resource
resource "aws_bedrock_guardrail" "hr_bot" {
  name        = "hr-bot-guardrail"
  description = "Content + PII + grounding for HR assistant"

  content_policy_config {
    filters_config {
      type                  = "HATE"
      input_strength        = "HIGH"
      output_strength       = "HIGH"
    }
  }

  word_policy_config {
    words_config {
      text = "competitor-name"
    }
  }
}
```

Version guardrail alongside app in the **same Terraform state** — `guardrail_version` in deploy manifest changes atomically with code.

### CloudWatch alerting

| Metric | Alert condition | Action |
|--------|----------------|--------|
| `GuardrailInterventions` | > 50/min sustained 5min | Investigate attack wave or false-positive spike |
| `GuardrailLatency` p99 | > 400ms | Check filter complexity; reduce denied topics |
| `ModelInvocationErrors` | > 5% rate | Provider issue — trigger fallback |

```yaml
# CloudWatch alarm sketch
AlarmName: guardrail-block-spike
MetricName: GuardrailInterventions
Threshold: 50
Period: 300
EvaluationPeriods: 1
ComparisonOperator: GreaterThanThreshold
AlarmActions: [arn:aws:sns:us-east-1:...:oncall-topic]
```

### Incident: guardrail blocks valid traffic

1. Check `GuardrailInterventions` CloudWatch metric for spike time.
2. Pull blocked request traces — identify which filter triggered.
3. If false positive: lower threshold for that category or add topic to allowlist.
4. If true positive: confirm guardrail working as intended; document.
5. Deploy updated `guardrailVersion` via Terraform; run adversarial suite.

### Cost awareness

Bedrock guardrails add **per-invocation cost** (check current pricing). At 100k requests/day, guardrail cost can exceed model cost if using multiple filters. Profile and disable unused filters.

---

## Senior pitfalls

| Mistake | Impact | Fix |
|---------|--------|-----|
| Same guardrail for dev and prod | Dev blocked by prod-strict rules | Separate guardrail IDs per environment |
| No automated adversarial test on version bump | Regression: old attacks pass | CI suite of 50+ attack prompts |
| Grounding enabled without Knowledge Base | Grounding check always fails | Only enable grounding when KB is configured |
| PII filter too aggressive | Blocks names in normal conversation | Tune entity types; test with realistic data |
| No fallback when guardrail service is degraded | Requests fail with 5xx | Catch `ThrottlingException`; degrade gracefully |

---

## Practice

Document FP/FN trade-off for one denied topic; run 20 prompt-attack strings from module 10 against Bedrock guardrail.

## Production-grade practice

4. **Write Terraform** (or CloudFormation) for a guardrail with 2 content filters + 1 denied topic; apply to a test Bedrock endpoint.
5. **Set up CloudWatch alarm** for `GuardrailInterventions > 50/min`; trigger it with a burst of adversarial prompts; verify alert fires.
6. **Run a FP/FN analysis** — send 50 benign + 50 adversarial prompts; compute precision and recall; tune one threshold to improve F1.
7. **Simulate a guardrail outage** — wrap `converse()` in try/except; return a safe fallback message; verify no user-visible error.

---

## Lecture map

Full M1_P1 through M5_P2 Bedrock guardrails track in course syllabus.

**Next:** [07-llm-gateways.md](./07-llm-gateways.md)
