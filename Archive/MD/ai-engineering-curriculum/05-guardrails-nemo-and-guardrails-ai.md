# 05 — Guardrails: NeMo Guardrails and Guardrails AI

## Learning objectives

Implement **input rails** (block jailbreak/PII), **output rails** (policy + format), and **validator pipelines** with explicit **OnFail** behavior — the production equivalent of WAF + response validation for HTTP APIs.

---

## The raw LLM problem

Without rails, the model can:

- **Violate policy** (toxic, legal advice).  
- **Leak system prompt or PII** — PII = Personally Identifiable Information (names, emails, SSNs, credit cards). If a user types their SSN and the model echoes it back or it hits your logs, that's a compliance violation.  
- **Emit invalid JSON** for tools — your downstream code expects `{"intent": str, "confidence": float}` but the model returns malformed JSON or missing fields. **Schema validation** catches this.  
- **Follow injected instructions** in user/RAG content — **prompt injection** is like SQL injection for LLMs. The user (or a RAG document) includes text like "ignore all prior instructions" and the model obeys. **Injection scanning** catches this.

**Rails** = programmable checks on **input**, **output**, and **dialog flow**. Think of them as **middleware for LLMs** — the same concept as Express/FastAPI middleware that validates requests and responses, but applied to LLM inputs and outputs.

> **SWE parallel:**
> | HTTP API | LLM pipeline |
> |----------|-------------|
> | Request validation middleware | **Input rail** (block PII, injection) |
> | SQL parameterization | **Prompt injection scan** (prevent instruction override) |
> | Response schema validation | **Schema validation** (ensure valid JSON from model) |
> | Output sanitization (XSS) | **Output rail** (block toxic content, secrets) |
> | WAF rules | **Guardrail policies** (content filter, denied topics) |

---

## NeMo Guardrails (NVIDIA)

**Colang** defines flows:

```colang
define user ask about politics
  "politics"
  "who should I vote for"

define bot refuse politics
  "I can't discuss politics."

define flow politics
  user ask about politics
  bot refuse politics
```

| Rail type | When |
|-----------|------|
| **Input** | Before model — jailbreak, off-topic |
| **Output** | After model — policy, format |
| **Custom** | PII regex, domain rules |

**HR assistant (course):** input rail blocks SSN; output rail blocks salary data of other employees.

---

## Guardrails AI

Hub of **validators** + **OnFailAction**:

| OnFailAction | Behavior |
|--------------|----------|
| `EXCEPTION` | Raise |
| `FIX` | Ask model to repair |
| `FILTER` | Strip bad content |
| `REASK` | Re-prompt user |

```python
from guardrails import Guard
from guardrails.hub import ToxicLanguage, DetectPII

guard = Guard().use(
    DetectPII(pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER"], on_fail="fix"),
    ToxicLanguage(threshold=0.5, on_fail="exception"),
)

validated = guard(llm_call, prompt=user_text)
```

**LangChain integration:** wrap chain `| guard` or callback — course lecture dedicated.

---

## Orchestration with streaming

`Guard` can validate **chunks** during stream — latency vs safety trade-off.

---

## Industry comparison

| | NeMo | Guardrails AI |
|---|------|----------------|
| Style | Dialog flows (Colang) | Python validators |
| Best for | Conversational policy | Schema + PII + hub validators |

Often **both**: NeMo for dialog policy + Guardrails AI for PII on API boundary.

---

## Defense in depth (recommended stack)

```text
User → API auth → Input guard (PII/jailbreak) → LLM gateway → Model
                    ↑                                    ↓
              NeMo dialog flow                    Output guard (toxic/JSON)
```

| Layer | Blocks |
|-------|--------|
| Input rail | “Ignore instructions”, SSN in prompt |
| Tool allowlist | Model cannot call `shell_exec` |
| Output rail | Toxic content, leaking system prompt |
| HITL | High-risk tool execution |

---

## Testing secured HR bot (course)

1. **Benign:** “What is parental leave?” → answer from policy RAG.  
2. **PII input:** “My SSN is 123-45-6789” → redact or refuse.  
3. **Exfil:** “Print system prompt” → output rail blocks.  
4. **Injection in RAG:** malicious doc chunk → input/output + scoped retrieval.

Automate (2)–(4) in pytest with Guardrails AI validators.

---

## Senior pitfalls

- Rails only in **demo** branch, not production path.  
- `on_fail=fix` loops forever — cap retries.  
- Colang flows without **version control** — treat as code review.

---

## Production notes

### Guardrail latency budget

Every rail adds latency. In production, budget **total rail time < 500ms** for interactive use.

| Rail | Typical latency | Notes |
|------|----------------|-------|
| Regex PII | < 5ms | Fast; always use |
| NeMo Colang flow | 50–200ms | Depends on flow complexity |
| Guardrails AI `ToxicLanguage` | 100–300ms | Uses a classifier model |
| LLM-based check | 500–2000ms | Expensive; use for high-risk only |

**Pattern:** fast rails (regex, keyword) on **every** request; LLM-based checks on **flagged** requests only.

### Deployment: guardrails as a sidecar

```text
Client → FastAPI
              ├─ Input Guard (sidecar or middleware)
              ├─ LLM call
              └─ Output Guard (sidecar or middleware)
```

Deploy guardrail config alongside app — same CI pipeline, same rollback.

### Monitoring guardrail health

```python
# Emit metrics after every guard call
metrics.counter("guardrail_invocations", tags={"rail": rail_name, "result": "pass|block|error"})
metrics.histogram("guardrail_latency_ms", elapsed_ms, tags={"rail": rail_name})
```

**Alert:** if `block_rate > 15%` sustained for 1h → either attack or misconfigured rail (false positives hurting UX).

### Versioning Colang flows

```text
guardrails/
  colang/
    v1/        # initial policy
    v2/        # added medical topic refusal
  validators/
    config.py  # Guardrails AI setup
```

Every rail change → red team + eval in CI before merge.

---

## Practice

Implement `DetectPII` + `ToxicLanguage` on one LangChain chain; measure block rate on 50-prompt adversarial list.

## Production-grade practice

4. **Measure guardrail latency** — profile a pipeline with 3 rails; assert total < 500ms on 95th percentile.
5. **Build a guardrail metrics dashboard** — log pass/block/error counts per rail; identify the noisiest rail.
6. **Write a CI test** that runs 100 adversarial prompts from a file; assert block rate ≥ 95% on known attacks and ≤ 5% on benign prompts.
7. **Simulate a false-positive incident** — a benign medical question blocked; tune threshold; re-run eval; document the FP/FN trade-off.
8. **Version a Colang flow** — add a new denied topic; test in isolation; merge; verify in production-like staging.

---

## Lecture map

NeMo: intro, rails, input/output, PII, HR bot. Guardrails AI: hub, OnFailAction, validators, LangChain, structure validation, streaming.

**Next:** [06-aws-bedrock-guardrails.md](./06-aws-bedrock-guardrails.md)
