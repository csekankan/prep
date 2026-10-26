# Module 06 — Q&A + Production Scenarios: LLM Optimizations

---

## Top 20 Interview Questions & Answers

### Q1: Your inference server can handle 20 QPS but you need 200 QPS. Walk through your optimization plan.

**A:**
```
CURRENT: 20 QPS on 2× H100

Step 1: ENABLE CONTINUOUS BATCHING (vLLM) → 3-5x
  Before: Process requests one at a time
  After: Process 64+ requests simultaneously
  Why: GPU was 30% utilized → now 90%
  Result: 20 → 80 QPS

Step 2: QUANTIZE MODEL (AWQ int4) → 1.5x
  Before: float16, model = 140 GB, 2 GPUs
  After: int4, model = 35 GB, 1 GPU (frees GPU for more batching)
  Result: 80 → 120 QPS

Step 3: SEMANTIC CACHING → 1.3-1.5x effective
  Cache similar queries (cosine > 0.95)
  Typical hit rate: 30-40% for support chatbots
  Result: 120 → 160 effective QPS

Step 4: ADD 1 MORE GPU PAIR → 1.5x
  Scale horizontally: add replica behind load balancer
  Result: 160 → 240 QPS ✓

TOTAL COST:
  Before: 2× H100 = $6,480/month, 20 QPS, $10.80/1K queries
  After: 3× H100 + Redis = $10,220/month, 240 QPS, $1.42/1K queries
  Cost per query: 7.6× cheaper!
```

---

### Q2: Explain FlashAttention to a non-ML engineer.

**A:**
```
Imagine you're doing a massive multiplication table (1000 × 1000).

NAIVE APPROACH:
1. Write out the entire 1M-cell table on paper (slow!)
2. Look up the values you need
3. Problem: writing the table takes more time than the math

FLASHATTENTION APPROACH:
1. Don't write the full table
2. Compute small blocks (32×32) at a time
3. Keep each block in your head (fast memory)
4. Write only the final answer
5. Result: same answer, 2-4x faster

Technical translation:
- "Paper" = GPU main memory (HBM, 3 TB/s)
- "Your head" = GPU on-chip memory (SRAM, 19 TB/s, but tiny)
- FlashAttention tiles the computation to fit in SRAM
- Avoids reading/writing the full N×N attention matrix to HBM
- Uses "online softmax" to process blocks without seeing all values

Key: It's NOT an approximation. The answer is mathematically identical.
It's a memory optimization, not a quality tradeoff.
```

---

### Q3: What is Mixture of Experts? How does GPT-4 use it?

**A:**
```
STANDARD MODEL (Dense):
  Every token uses ALL parameters
  70B model → 70B computations per token

MIXTURE OF EXPERTS (Sparse):
  Model has 8 "expert" FFN networks
  Router selects 2 best experts per token
  Only 2/8 = 25% of FFN params are active

  Total params: 8 × expert_size = very large (knowledge)
  Active params: 2 × expert_size = small (speed)

GPT-4 (estimated):
  Total params: ~1.7 TRILLION
  Active params: ~280 BILLION per token
  Experts: ~16 expert groups
  Top-K: 2 experts per token
  
  Result: Knowledge of a 1.7T model
          Speed of a 280B model
          
WHY IT WORKS:
  Different tokens need different "expertise"
  "Write Python code" → activates code experts
  "Translate to French" → activates language experts
  "Calculate 5×7" → activates math experts
  
CHALLENGE: Load balancing
  If router always picks same 2 experts → other 6 are wasted
  Solution: Auxiliary loss that penalizes uneven expert usage
```

---

### Q4: Compare paged attention vs. standard KV cache allocation.

**A:**
```
STANDARD ALLOCATION (wasteful):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request arrives → allocate KV cache for MAX sequence length

Request: "Hi" (will generate ~10 tokens)
Allocated: [████████████████████████████████] 2048 slots
Used:      [██]                               10 slots
Wasted:    [  ██████████████████████████████] 2038 slots (99.5%!)

With 100 concurrent requests: 100 × 2048 = 204,800 slots allocated
Actually used: maybe 5,000 slots
Waste: 97.5%

PAGED ATTENTION (efficient):
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request arrives → allocate KV cache in PAGES (blocks of 16 tokens)

Request: "Hi" (will generate ~10 tokens)
Allocated: [████] 1 page (16 slots)
Used:      [██]   10 slots
Wasted:    [  ██] 6 slots (37.5% — only within last page!)

With 100 concurrent requests:
  Short (50 req × 10 tokens): 50 pages
  Medium (30 req × 100 tokens): 210 pages  
  Long (20 req × 500 tokens): 640 pages
  Total: 900 pages vs. 204,800 slots = 14x less memory!

RESULT:
  - Serve 3-5x more concurrent requests on same GPU
  - Memory grows proportional to ACTUAL tokens, not MAX tokens
  - Enables efficient beam search (share pages between beams)
```

---

### Q5: Your company spends $50K/month on LLM API calls. Present an optimization plan to the CTO.

**A:**
```python
CURRENT STATE:
  Model: GPT-4o for all 2M queries/month
  Avg input: 1,500 tokens, Avg output: 300 tokens
  Cost: $2.50/M input + $10.00/M output = $0.00675/query
  Monthly: 2M × $0.00675 = $13,500/month
  
  Wait — the user said $50K. Let's check:
  Reality: system prompts, few-shot examples, retries, multi-step agents
  Actual avg input: 5,000 tokens (with context)
  Actual cost: $0.0155/query → 2M × $0.0155 = $31K
  Plus: evaluation runs, dev/test calls, retry overhead = $50K ✓

OPTIMIZATION PLAN:

Phase 1: Quick wins (Week 1-2) — Save $25K/month
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Semantic caching (30% hit rate):       -$15,000
  2. Route simple queries to GPT-4o-mini:   -$8,000
  3. Shorten system prompts (20% shorter):  -$2,000
  Total savings: $25,000/month
  New monthly: $25,000

Phase 2: Architecture (Week 3-6) — Save $10K more
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  4. Prompt compression (summarize context): -$4,000
  5. Eliminate unnecessary LLM calls:        -$3,000
     (use regex/rules for simple classification)
  6. Reduce retries (better error handling): -$3,000
  Total savings: $10,000/month
  New monthly: $15,000

Phase 3: Self-hosting (Week 7-12) — Optional
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  7. Self-host Llama 70B for simple queries:
     GPU cost: $3,000/month (2× H100)
     Replaces: $8,000/month in API calls
     Net savings: $5,000/month
  New monthly: $10,000

SUMMARY:
  Before:  $50,000/month
  After:   $10,000/month
  Savings: $40,000/month = $480,000/year
  ROI:     ~2 weeks of engineering time → pays for itself in 1 month
```

---

## Production Scenario: Building a GPU Inference Cluster

```python
class GPUInferenceCluster:
    """
    Scenario: Build an internal GPU cluster for LLM serving.
    
    Requirements:
    - Serve 3 different models (8B, 70B, 200B)
    - 500 QPS total across all models
    - 99.9% availability
    - Budget: $50K/month
    """
    
    CLUSTER_DESIGN = {
        "models": {
            "llama-8b": {
                "purpose": "Fast responses, simple queries (60% of traffic)",
                "qps": 300,
                "gpus_per_replica": 1,  # Fits on 1 GPU
                "replicas": 3,          # 100 QPS each
                "gpu_type": "L4",       # Cheap, good for small models
                "total_gpus": 3,
                "monthly_cost": 3 * 800,  # $2,400
            },
            "llama-70b": {
                "purpose": "Complex queries, code, analysis (35% of traffic)",
                "qps": 175,
                "gpus_per_replica": 2,  # AWQ int4, tensor parallel
                "replicas": 4,
                "gpu_type": "H100",
                "total_gpus": 8,
                "monthly_cost": 8 * 4500,  # $36,000
            },
            "200b-moe": {
                "purpose": "Most complex, multi-step reasoning (5% of traffic)",
                "qps": 25,
                "gpus_per_replica": 4,
                "replicas": 2,
                "gpu_type": "H100",
                "total_gpus": 8,
                "monthly_cost": 8 * 4500,  # $36,000
            },
        },
        "infrastructure": {
            "load_balancer": "$200/month",
            "monitoring": "$500/month",
            "storage": "$300/month",
            "networking": "$500/month",
        },
        "total": {
            "gpus": 19,
            "monthly": "$75,900 — OVER BUDGET!",
        }
    }
    
    OPTIMIZED_DESIGN = """
    Budget-optimized version ($48K/month):
    
    1. Drop 200B model → use GPT-4o API for 5% complex queries
       200B queries: 25 QPS × 86400 × 30 = 64.8M queries
       GPT-4o cost: 64.8M × $0.015 = ~$972/month (way cheaper!)
    
    2. Reduce 70B replicas from 4 to 3 (with vLLM optimization)
       vLLM continuous batching → 60+ QPS per replica
       3 replicas × 60 = 180 QPS (enough for 175 target)
    
    3. Use spot/preemptible instances for off-peak (save 60%)
    
    FINAL:
    ┌────────────┬──────┬──────────┬────────────┐
    │ Model      │ GPUs │ Type     │ Cost/month │
    ├────────────┼──────┼──────────┼────────────┤
    │ Llama 8B   │ 3    │ L4       │ $2,400     │
    │ Llama 70B  │ 6    │ H100     │ $27,000    │
    │ GPT-4o API │ 0    │ API      │ $972       │
    │ Infra      │ -    │ -        │ $1,500     │
    ├────────────┼──────┼──────────┼────────────┤
    │ TOTAL      │ 9    │ Mixed    │ $31,872    │ ← Under budget!
    └────────────┴──────┴──────────┴────────────┘
    
    Availability: 99.9%
    - 70B: 3 replicas, any 2 can handle full load
    - 8B: 3 replicas, any 2 can handle full load
    - API: OpenAI SLA + circuit breaker to self-hosted fallback
    """
```

---

## Production Scenario: Optimizing Time-to-First-Token (TTFT)

```python
class TTFTOptimization:
    """
    Scenario: Users complain the chatbot "takes forever to start responding."
    Current TTFT: 3-5 seconds.
    Target TTFT: < 500ms.
    """
    
    DIAGNOSIS = """
    TTFT = Time from user pressing Enter to seeing first token
    
    Current breakdown:
      Network (client → server):     50ms
      Queue wait:                    500ms   ← High during peak
      Authentication:                20ms
      Context retrieval (RAG):       200ms
      Prompt assembly:               10ms
      Prefill (process prompt):      2000ms  ← BOTTLENECK (8K tokens!)
      First token generation:        50ms
      Network (server → client):     50ms
      Total:                         ~2900ms ≈ 3 seconds
    """
    
    OPTIMIZATION_PLAN = {
        "1_enable_streaming": {
            "what": "Send tokens as they're generated instead of waiting for full response",
            "impact": "TTFT drops from 'full response time' to 'prefill + 1 token'",
            "effort": "1 day",
            "code": """
                # Before: wait for entire response
                response = await client.chat.completions.create(...)
                send_to_user(response.content)
                
                # After: stream tokens immediately
                stream = await client.chat.completions.create(..., stream=True)
                async for chunk in stream:
                    send_to_user(chunk.choices[0].delta.content)
            """
        },
        
        "2_reduce_prompt_size": {
            "what": "Fewer input tokens = faster prefill",
            "impact": "8K tokens → 2K tokens = 75% faster prefill",
            "effort": "1 week",
            "actions": [
                "Summarize system prompt (2K → 500 tokens)",
                "Reduce few-shot examples (3K → 500 tokens)",
                "Retrieve fewer but more relevant docs (3K → 1K tokens)",
            ]
        },
        
        "3_prefix_caching": {
            "what": "Cache the KV state for common prompt prefixes",
            "impact": "System prompt (500 tokens) processed once, reused forever",
            "effort": "1 day (vLLM supports this natively)",
            "code": """
                # vLLM: enable prefix caching
                # --enable-prefix-caching
                # Common system prompt is cached across all requests
                # Saves: 500 tokens × 50ms/1000tokens = 25ms per request
            """
        },
        
        "4_speculative_decoding": {
            "what": "Small model drafts tokens while large model verifies",
            "impact": "2-3x faster token generation (not prefill)",
            "effort": "2-3 days",
        },
        
        "5_reduce_queue_wait": {
            "what": "Auto-scale inference servers based on queue depth",
            "impact": "Queue wait from 500ms → <50ms",
            "effort": "1 week",
        },
    }
    
    RESULT = """
    After optimization:
      Network:           50ms
      Queue wait:        50ms  (auto-scaling)
      Auth:              20ms
      RAG retrieval:     150ms (fewer docs, parallel search)
      Prompt assembly:   10ms
      Prefill:           300ms (2K tokens instead of 8K, prefix cached)
      First token:       50ms
      Network back:      50ms
      ─────────────────────
      Total TTFT:        ~680ms → close to 500ms target ✓
      
    With prefix caching on hot system prompts: ~400ms ✓✓
    """
```
