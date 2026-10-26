# 01 — LangChain Fundamentals (UV, Agents, Models, Tools, Messages)

## Learning objectives

After this module you should be able to: explain the **message list** API; call models with **streaming**; bind **tools** and execute tool calls in a loop; set up **UV** for reproducible deps — the same skills you use for any third-party SDK, but with non-deterministic responses.

---

## Environment with UV

[UV](https://github.com/astral-sh/uv) is a fast Python package manager — use it like `pip` + `venv` in one tool.

```bash
uv venv .venv
source .venv/bin/activate
uv pip install langchain langchain-openai langchain-anthropic python-dotenv
```

```bash
# pyproject.toml snippet (recommended for projects)
# [project]
# dependencies = ["langchain>=0.3", "langchain-openai>=0.2"]
```

**Why seniors care:** Reproducible envs match how you already pin Docker images — lockfiles for agents prevent “works on my laptop” prompt deps.

---

## Messages: the real API surface

LangChain models consume **messages**, not raw strings.

| Type | Role | Use |
|------|------|-----|
| `SystemMessage` | Instructions, policy | “You are a support bot; never reveal SSN.” |
| `HumanMessage` | User input | Untrusted |
| `AIMessage` | Model output | May include `tool_calls` |
| `ToolMessage` | Tool result | Feeds back to model |

```python
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
messages = [
    SystemMessage(content="Answer in one sentence."),
    HumanMessage(content="What is a vector database?"),
]
response = llm.invoke(messages)
assert isinstance(response, AIMessage)
print(response.content)
```

**Industry pattern:** System prompt + few-shot examples in messages ≈ “configuration as data” — version in git.

---

## Model integration

```python
from langchain_openai import ChatOpenAI

# Same interface pattern for Anthropic, Bedrock, etc. via langchain-* packages
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    max_tokens=1024,
    timeout=30,
)
```

| Parameter | Effect |
|-----------|--------|
| `temperature` | Higher → more random (creative); 0 for extraction/tools |
| `max_tokens` | Cap cost/latency |
| `timeout` | Fail fast; pair with gateway retry |

---

## Streaming vs batch

**Streaming:** token chunks to UI — better UX, same total cost.

```python
for chunk in llm.stream(messages):
    print(chunk.content, end="", flush=True)
```

**Batch:** `llm.batch(list_of_message_lists)` — offline jobs, eval pipelines.

**Math:** Time-to-first-token (TTFT) dominates perceived latency; streaming does not reduce \(N_{\text{out}}\), only hides it.

---

## Tools

Tools are **JSON-schema functions** the model may invoke.

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Return weather for a city."""
    return f"Sunny in {city}"  # replace with real API

tools = [get_weather]
llm_with_tools = llm.bind_tools(tools)
msg = llm_with_tools.invoke([HumanMessage(content="Weather in Paris?")])
if msg.tool_calls:
    for tc in msg.tool_calls:
        print(tc["name"], tc["args"])
```

**Senior pitfalls:**

- Tools without **auth** on the backend — model is the caller.  
- Unbounded **side effects** — add confirmation (HITL) for payments.  
- Schema too vague — model hallucinates argument shapes.

---

## Agents with LangChain (high level)

Prebuilt agents wire: model + tools + loop. You will use **LangGraph** for production control flow (module 03).

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(llm, tools)
result = agent.invoke({"messages": [HumanMessage(content="Weather in Tokyo?")]})
```

ReAct pattern: **Reason** (text) + **Act** (tool) interleaved.

### Manual tool loop (understand before abstractions)

```python
from langchain_core.messages import ToolMessage

messages = [HumanMessage(content="Weather in Paris?")]
llm_bind = llm.bind_tools(tools)

while True:
    ai = llm_bind.invoke(messages)
    messages.append(ai)
    if not ai.tool_calls:
        break
    for tc in ai.tool_calls:
        if tc["name"] == "get_weather":
            result = get_weather.invoke(tc["args"])
        messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

print(messages[-1].content)
```

This is exactly what LangGraph will compile into nodes — **model node** and **tool node**.

---

## Industry example: support bot

| Component | Choice |
|-----------|--------|
| Model | Small model for triage, large for complex |
| Tools | `ticket_lookup`, `refund_policy_rag` only |
| Messages | System policy + user + tool results |
| Observability | Trace each tool call (module 04) |

---

## Deep dive: message trimming

Long chats exceed context → strategies:

1. **Sliding window** — keep last K turns.  
2. **Summarize** — middleware compresses old turns (module 02).  
3. **Vector memory** — retrieve relevant past facts (module 09).

---

## Math: latency and cost

### Time-to-first-token (TTFT)

\[
\text{TTFT} \approx T_{\text{queue}} + T_{\text{prefill}}
\]

Prefill processes all input tokens at once; first output token appears after. Streaming hides total generation time but TTFT is fixed.

### End-to-end latency

\[
T_{\text{e2e}} = T_{\text{TTFT}} + N_{\text{out}} \times T_{\text{per\_token}}
\]

Example: TTFT = 200ms, 500 output tokens at 20ms/token → \(200 + 500 \times 20 = 10.2\text{s}\).

### Cost per request

\[
\text{cost} = \frac{N_{\text{in}}}{10^6} \cdot p_{\text{in}} + \frac{N_{\text{out}}}{10^6} \cdot p_{\text{out}}
\]

| Model | \(p_{\text{in}}\) ($/1M) | \(p_{\text{out}}\) ($/1M) | 4k in + 500 out |
|-------|--------------------------|---------------------------|-----------------|
| gpt-4o-mini | $0.15 | $0.60 | $0.0009 |
| gpt-4o | $2.50 | $10.00 | $0.015 |
| claude-3.5-sonnet | $3.00 | $15.00 | $0.0195 |

At 10k requests/day on gpt-4o: \(10{,}000 \times 0.015 = \$150/\text{day}\). Caching and routing to smaller models matters.

### Agent cost multiplier

An agent that makes \(K\) LLM calls per request multiplies cost and latency:

\[
\text{agent\_cost} \approx K \times \text{single\_call\_cost}
\]

Typical \(K\): 2–5 for simple agents; 10+ for complex multi-step. Set `recursion_limit` to cap \(K\).

---

## Senior pitfalls

| Pitfall | Fix |
|---------|-----|
| Giant system prompt in code | `prompts/v1.yaml` in git |
| No timeout on `invoke` | `timeout=30` + gateway retry |
| Logging full prompts with PII | Redact in observability layer |
| `temperature>0` on extraction | Use `temperature=0` for tools/JSON |

---

## Production notes

### Deploying LangChain behind FastAPI

```python
from fastapi import FastAPI, Request
from langchain_openai import ChatOpenAI
import time, uuid

app = FastAPI()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=30)

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    try:
        response = llm.invoke(body["messages"])
        return {"request_id": request_id, "content": response.content}
    except Exception as e:
        # structured error — never leak raw LLM error to client
        return {"request_id": request_id, "error": "service_error"}, 500
    finally:
        elapsed = time.perf_counter() - start
        # emit to metrics: histogram llm_latency, counter llm_requests
```

### Error handling patterns

| Error | Cause | Production response |
|-------|-------|-------------------|
| `openai.RateLimitError` | Provider throttle | Retry with backoff; fallback model via gateway |
| `openai.APITimeoutError` | Slow inference | Return cached response or apologize; log |
| `ValidationError` (Pydantic) | Structured output parse fail | Retry up to 3×; return "could not process" |
| `RecursionError` / `GraphRecursionError` | Agent infinite loop | `recursion_limit=25` in config; alert |

### Config management (12-factor for LLM apps)

```bash
# .env (never commit)
OPENAI_API_KEY=...
MODEL_ID=gpt-4o-mini           # change without deploy
PROMPT_VERSION=v3               # pin to git tag
MAX_TOKENS=1024
TEMPERATURE=0
GATEWAY_URL=https://gateway.internal
```

Load via `python-dotenv` or secrets manager; **no hard-coded model names** in code.

### Health check

```python
@app.get("/health")
async def health():
    # verify provider reachable (optional: lightweight embed call)
    return {"status": "ok", "model": MODEL_ID, "prompt_version": PROMPT_VERSION}
```

---

## Practice

1. Stream a 500-token answer and measure TTFT with `time.perf_counter()`.  
2. Add a second tool; observe model **choosing** between them.  
3. Break tool schema (wrong type hint); watch model recover or fail.

## Production-grade practice

4. **Wrap an agent in FastAPI** with request ID, structured error responses, and a `/health` endpoint.
5. **Add tenacity retry** with exponential backoff on `RateLimitError`; prove it works by setting a 1 RPM limit.
6. **Write a `conftest.py`** that mocks `ChatOpenAI.invoke` with deterministic responses for fast CI — no API key needed.
7. **Dockerize** the service: `Dockerfile` → build → run → curl `/health` → curl `/chat`.

---

## Lecture map

| Course lectures | Section |
|-----------------|---------|
| Creating Virtual Environment With UV | Environment |
| Langchain Model Integration | Models |
| Streaming And Batch | Streaming/batch |
| Tools In Langchain | Tools |
| Messages In Langchain | Messages |
| Agents With Langchain | Agents intro |

**Next:** [02-structured-output-and-middleware.md](./02-structured-output-and-middleware.md)
