# 02 — Structured Output and Middleware

## Learning objectives

Parse model outputs into **validated objects**; implement **summarization** and **HITL** middleware without spaghetti `if` statements in every route handler.

---

## Why structured output?

Free-form JSON in chat **breaks parsers**. Production needs **schemas**: APIs, DB rows, tool arguments.

Three LangChain-friendly patterns:

| Approach | Best for |
|----------|----------|
| **Pydantic** | Production — validation, docs, IDE support |
| **TypedDict** | Lightweight typing |
| **dataclass** | Simple immutable structs |

---

## Pydantic structured output

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class TicketIntent(BaseModel):
    category: str = Field(description="billing|technical|other")
    urgency: int = Field(ge=1, le=5)
    summary: str = Field(max_length=200)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured = llm.with_structured_output(TicketIntent)

result: TicketIntent = structured.invoke("I was charged twice and need help ASAP")
print(result.category, result.urgency)
```

**Under the hood:** Provider may use **JSON mode** or **tool calling** with schema — you get a parsed object or a validation error.

**Retry pattern (senior):**

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def parse_ticket(text: str) -> TicketIntent:
    return structured.invoke(text)
```

---

## TypedDict and dataclass

```python
from typing import TypedDict

class IntentTD(TypedDict):
    category: str
    urgency: int

# dataclass
from dataclasses import dataclass

@dataclass
class IntentDC:
    category: str
    urgency: int
```

Use Pydantic when you need **validators** (`ge`, `le`, regex) and clear error messages for evals.

---

## Middleware: summarization

When `sum(tokens(messages)) > threshold`, compress old turns.

Conceptual flow:

```mermaid
flowchart LR
  M[Long history] --> S[Summarize old turns]
  S --> K[Keep recent K turns]
  K --> LLM[Model call]
```

**Trade-off:** Summary loses detail — store **raw** in DB for audit; pass summary to model only.

**Industry:** Customer support bots summarize after 20 turns; keep **ticket ID** and **last user goal** verbatim.

---

## Middleware: human-in-the-loop (HITL)

Pause before dangerous tools (refund, delete, send email).

```python
# LangGraph pattern (detail in 03) — conceptual
if tool_name in HIGH_RISK and not human_approved:
    raise Interrupt("approve_refund")
```

Course implements HITL as **middleware** in LangChain and as **graph interrupts** in LangGraph — same product requirement, different mechanism.

---

## Guardrails introduction (preview)

Middleware can call **guardrails** before/after model:

1. **Input:** block jailbreak, PII in prompt.  
2. **Output:** block policy violations, validate JSON schema.

Full frameworks: module 05–06.

```python
import re

def input_guard(text: str) -> str:
    """
    Input guardrail: scan user text for PII and injection before it reaches the model.
    PII = Personally Identifiable Information (SSN, email, phone, credit card).
    Injection = user trying to override system instructions ("ignore all rules...").
    """
    # PII detection — block or redact before the model ever sees it
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):          # SSN
        raise ValueError("PII detected: SSN in input")
    if re.search(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", text):  # credit card
        raise ValueError("PII detected: credit card in input")

    # Prompt injection detection — like SQL injection but for LLMs
    injection_patterns = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"you\s+are\s+now\s+(DAN|unrestricted)",
        r"reveal\s+(the\s+)?system\s+prompt",
    ]
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Prompt injection attempt blocked")
    return text


def output_guard(response: str, schema_class=None) -> str:
    """
    Output guardrail: validate model response before it reaches the user.
    - Schema validation: does the JSON match the expected Pydantic model?
    - Secret scan: did the model leak API keys or PII in its response?
    """
    # Schema validation — same concept as validating a REST API response
    if schema_class:
        import json
        data = json.loads(response)
        schema_class(**data)  # Pydantic raises ValidationError if wrong shape

    # Secret/PII scan on output — model might echo back or hallucinate PII
    if re.search(r"AKIA[0-9A-Z]{16}", response):
        raise ValueError("Model output contains AWS key — blocked")
    return response
```

> **SWE parallel:** Input guard ≈ request validation middleware. Output guard ≈ response schema validation. Injection scan ≈ SQL injection parameterization. You already do all of this in HTTP APIs — here you do it around the LLM.

---

## Math: schema constraint as search space

Unstructured generation searches all strings. Schema constrains to **valid JSON manifold** — fewer parse failures, lower downstream error rate.

If parse success without schema is \(p_0 \approx 0.85\) and with schema \(p_1 \approx 0.98\), error rate drops **~13×** on the parsing step alone.

---

## Deep dive: eval structured outputs

Golden tests:

```python
def test_intent_schema():
    out = structured.invoke("double charge on invoice 9921")
    assert out.category in {"billing", "technical", "other"}
    assert 1 <= out.urgency <= 5
```

Add **DeepEval** / **G-Eval** for semantic quality (module 08).

---

## Senior pitfalls

- Using structured output for **long prose** — use free text + separate extraction step.  
- Summarization **drops** compliance disclaimers — always keep fixed system footer.  
- HITL only in UI, not in **audit log** — store who approved what.

---

## Production notes

### Schema evolution

When business adds a new `category` to `TicketIntent`, you must:

1. Update Pydantic model.
2. Update system prompt few-shot examples.
3. Re-run eval on golden set — old model may not know new category without examples.
4. Deploy model + prompt version together (atomic release).

**Anti-pattern:** add category in code but not in prompt → model never emits it.

### Middleware ordering in production

```text
Request → Input guard → Summarize history → LLM call → Output guard → Structured parse → Response
```

Order matters: summarize **after** guard strips PII, parse **after** output guard ensures policy compliance.

### Logging structured outputs

```python
import json, logging
logger = logging.getLogger("structured")

result: TicketIntent = structured.invoke(text)
logger.info("parsed", extra={"category": result.category, "urgency": result.urgency})
# NEVER log raw user text with PII — redact or hash
```

### HITL audit table

```sql
CREATE TABLE hitl_audit (
    id UUID PRIMARY KEY,
    thread_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    payload JSONB NOT NULL,
    approved_by TEXT,           -- NULL = pending
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Every approval/denial is **auditable** — required for SOC 2 and regulated industries.

---

## Practice

Define `RefundDecision { approved: bool, reason: str, amount: float }` and eval 10 adversarial prompts.

## Production-grade practice

4. **Schema migration exercise:** add a new field `language: str` to `TicketIntent`; update prompt; re-run eval; confirm backward compatibility.
5. **Build a summarization middleware** that kicks in at > 4000 tokens; verify in a trace that old turns are compressed.
6. **Implement HITL with audit logging** — mock refund tool; log approve/deny to a JSON file; verify audit trail after 5 actions.
7. **Write pytest** that asserts structured output matches schema on 20 edge cases (empty input, emoji, code injection attempt).

---

## Lecture map

| Lectures | Topic |
|----------|--------|
| Pydantic / TypedDict / Data Class Structured Output | Structured output |
| MiddleWare Summarization | Summarization |
| Human In the Loop MiddleWare | HITL |
| Introduction To Guardrails And Implementation | Guardrails preview |

**Next:** [03-langgraph-agents-memory-mcp.md](./03-langgraph-agents-memory-mcp.md)
