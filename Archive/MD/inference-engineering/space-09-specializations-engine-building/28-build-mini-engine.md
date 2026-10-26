# Module 28 — Build a Mini Inference Engine

> **8 lessons · Advanced**
> Build a working inference engine from scratch, step by step.

---

## Architecture Evolution

```mermaid
graph LR
    V1["v1: Generation Loop<br/>(60 lines)"] --> V2["v2: + KV Cache<br/>(100 lines)"]
    V2 --> V3["v3: + Batching<br/>(150 lines)"]
    V3 --> V4["v4: + Continuous Batching<br/>(250 lines)"]
    V4 --> V5["v5: + Paged KV<br/>(350 lines)"]
    V5 --> V6["v6: + API<br/>(450 lines)"]
    V6 --> V7["v7: + Caching & Metrics<br/>(500+ lines)"]
```

---

## Step 1: Model Runner & Generation Loop

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class MiniEngine:
    """v1: The simplest possible inference engine."""

    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.bfloat16, device_map="auto"
        )
        self.model.eval()

    def generate(self, prompt, max_tokens=100, temperature=0.7):
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        generated = input_ids.clone()

        for _ in range(max_tokens):
            with torch.inference_mode():
                outputs = self.model(generated)
            logits = outputs.logits[:, -1, :] / temperature
            next_token = torch.multinomial(torch.softmax(logits, dim=-1), 1)
            generated = torch.cat([generated, next_token], dim=-1)
            if next_token.item() == self.tokenizer.eos_token_id:
                break

        return self.tokenizer.decode(generated[0], skip_special_tokens=True)

# engine = MiniEngine("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
# print(engine.generate("Hello!"))
```

---

## Step 2: Add KV Cache

```python
class MiniEngineV2(MiniEngine):
    """v2: Add KV cache to avoid recomputation."""

    def generate(self, prompt, max_tokens=100, temperature=0.7):
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        past_key_values = None
        all_tokens = input_ids.clone()

        for step in range(max_tokens):
            with torch.inference_mode():
                if past_key_values is None:
                    outputs = self.model(input_ids, use_cache=True)  # Prefill
                else:
                    outputs = self.model(
                        all_tokens[:, -1:],                # Only last token!
                        past_key_values=past_key_values,   # Reuse KV cache
                        use_cache=True
                    )

            past_key_values = outputs.past_key_values
            logits = outputs.logits[:, -1, :] / temperature
            next_token = torch.multinomial(torch.softmax(logits, dim=-1), 1)
            all_tokens = torch.cat([all_tokens, next_token], dim=-1)

            if next_token.item() == self.tokenizer.eos_token_id:
                break

        return self.tokenizer.decode(all_tokens[0], skip_special_tokens=True)
```

---

## Step 3: Add Request Batching

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class RequestState(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    FINISHED = "finished"

@dataclass
class Request:
    id: int
    prompt: str
    max_tokens: int
    input_ids: Optional[torch.Tensor] = None
    generated_tokens: List[int] = None
    state: RequestState = RequestState.WAITING
    past_key_values: Optional[tuple] = None

    def __post_init__(self):
        self.generated_tokens = self.generated_tokens or []

class MiniEngineV3:
    """v3: Batch multiple requests together."""

    def __init__(self, model_name, max_batch_size=8):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.bfloat16, device_map="auto"
        )
        self.model.eval()
        self.max_batch_size = max_batch_size
        self.requests: List[Request] = []
        self.next_id = 0

    def add_request(self, prompt: str, max_tokens: int = 100) -> int:
        req = Request(id=self.next_id, prompt=prompt, max_tokens=max_tokens)
        req.input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        self.requests.append(req)
        self.next_id += 1
        return req.id

    def step(self):
        """Run one generation step for all active requests."""
        running = [r for r in self.requests if r.state == RequestState.RUNNING]
        if not running:
            return

        # Pad and batch (simplified — production engines avoid this)
        max_len = max(r.input_ids.shape[1] + len(r.generated_tokens) for r in running)
        batch_ids = []
        for r in running:
            tokens = torch.cat([r.input_ids, torch.tensor([r.generated_tokens], device="cuda")], dim=-1)
            padded = torch.nn.functional.pad(tokens, (0, max_len - tokens.shape[1]),
                                             value=self.tokenizer.pad_token_id)
            batch_ids.append(padded)

        batch = torch.cat(batch_ids, dim=0)

        with torch.inference_mode():
            outputs = self.model(batch)

        for i, r in enumerate(running):
            pos = r.input_ids.shape[1] + len(r.generated_tokens) - 1
            logits = outputs.logits[i, pos, :]
            next_token = logits.argmax().item()
            r.generated_tokens.append(next_token)

            if (next_token == self.tokenizer.eos_token_id or
                len(r.generated_tokens) >= r.max_tokens):
                r.state = RequestState.FINISHED

    def run(self):
        """Run until all requests are done."""
        for r in self.requests:
            if r.state == RequestState.WAITING:
                r.state = RequestState.RUNNING

        while any(r.state == RequestState.RUNNING for r in self.requests):
            self.step()

        return {r.id: self.tokenizer.decode(r.generated_tokens) for r in self.requests}
```

---

## Step 4: Continuous Batching

```python
class MiniEngineV4(MiniEngineV3):
    """v4: Continuous batching — add/remove requests every iteration."""

    def step(self):
        # Admit waiting requests
        running = [r for r in self.requests if r.state == RequestState.RUNNING]
        waiting = [r for r in self.requests if r.state == RequestState.WAITING]

        while waiting and len(running) < self.max_batch_size:
            req = waiting.pop(0)
            req.state = RequestState.RUNNING
            running.append(req)

        # Process batch (same as before but with dynamic composition)
        if not running:
            return

        # ... forward pass, sampling, completion check ...

        # Remove finished requests immediately (not at end!)
        for r in running:
            if r.state == RequestState.FINISHED:
                # KV cache memory freed → admit next waiting request
                pass
```

---

## Step 5-7: Paged KV, API & Metrics

Each step adds another production feature. The full engine grows to ~500 lines but implements the core of what vLLM does.

```python
# Step 5: Paged KV allocator (from Module 08)
# Step 6: FastAPI server with streaming (from Module 01)
# Step 7: Prometheus metrics + prefix caching

class MiniEngineFinal:
    """The complete mini inference engine."""
    # Components:
    # - TokenizerPool: tokenize/detokenize
    # - Scheduler: continuous batching, preemption
    # - BlockManager: paged KV allocation
    # - ModelRunner: forward pass execution
    # - Sampler: temperature, top-k, top-p
    # - APIServer: FastAPI with streaming
    # - MetricsCollector: Prometheus metrics
    pass
```

---

## 🧪 Project — Benchmark Against vLLM

Compare your mini engine against vLLM on the same model and workload:

| Metric | Mini Engine | vLLM | Gap |
|--------|-----------|------|-----|
| Throughput | ? tok/s | ? tok/s | ?× |
| TTFT P50 | ? ms | ? ms | ?× |
| Memory efficiency | ?% | ?% | ? |
| Max concurrent | ? | ? | ?× |

Expected: vLLM should be 5-20× faster due to optimized kernels, CUDA graphs, and proper memory management. But your engine teaches you **why** each optimization matters!

> **🏢 FAANG Deep Dive:** Building a mini engine is the single best way to prepare for inference engineering interviews at top companies. Interviewers love candidates who can explain what PagedAttention does, why continuous batching matters, and how KV cache memory works — not just use vLLM, but understand it deeply.

---

**Next Module:** [29 — Reproduce Inference Research](../space-10-research-capstone/29-reproduce-research.md) →
