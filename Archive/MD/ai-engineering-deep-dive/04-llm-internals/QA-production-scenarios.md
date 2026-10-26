# Module 04 — Q&A + Production Scenarios: LLM Internals

---

## Top 20 Interview Questions & Answers

### Q1: How much GPU memory do you need to serve Llama 3.1 70B? Show your work.

**A:**
```python
# Memory = Model Weights + KV Cache + Activations + Overhead

# 1. MODEL WEIGHTS
params = 70e9  # 70 billion
dtype_bytes = 2  # float16
model_memory = params * dtype_bytes  # = 140 GB

# With AWQ int4 quantization:
model_memory_quantized = params * 0.5  # = 35 GB

# 2. KV CACHE (per request)
layers = 80
kv_heads = 8          # GQA: 8 KV heads (not 64 query heads)
head_dim = 128
seq_len = 4096        # 4K context
dtype = 2             # float16

kv_per_request = 2 * layers * kv_heads * head_dim * seq_len * dtype
# = 2 × 80 × 8 × 128 × 4096 × 2 = 1.34 GB per request

# For 32 concurrent requests:
kv_total = kv_per_request * 32  # = 42.9 GB

# 3. ACTIVATIONS (~10% of model)
activations = model_memory_quantized * 0.10  # = 3.5 GB

# 4. TOTAL
total = model_memory_quantized + kv_total + activations
# = 35 + 42.9 + 3.5 = 81.4 GB

# VERDICT:
# Float16: 140 GB model → needs 2× H100 (160 GB)
# AWQ int4: 35 GB model → fits on 1× H100 (80 GB) for ~20 concurrent requests
# With int8 KV cache: double the concurrent requests

print(f"""
GPU Memory Budget for Llama 3.1 70B:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model (AWQ int4):      35.0 GB
KV Cache (32 req):     42.9 GB
Activations:            3.5 GB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:                 81.4 GB → 2× A100 or 2× H100
                                 (or 1× H100 with fewer concurrent)
""")
```

---

### Q2: Explain KV Cache to a junior engineer.

**A:**
```
Imagine you're writing a story word by word.

WITHOUT KV cache (inefficient):
  Word 1: Read "Once" → write "upon"
  Word 2: Read "Once upon" → write "a"
  Word 3: Read "Once upon a" → write "time"
  
  Every time, you re-read ALL previous words from the start.
  At word 1000, you read 999 words just to write 1 new word!

WITH KV cache (efficient):
  Word 1: Read "Once" → remember it in notepad → write "upon"
  Word 2: Check notepad (has "Once") → read only "upon" → write "a"
  Word 3: Check notepad (has "Once upon") → read only "a" → write "time"
  
  You REMEMBER what you've already processed.
  At word 1000, you only process the 1 new word.

Technical detail:
  The "notepad" stores Keys and Values (K, V) from previous tokens.
  Each new token only computes its Query (Q) and looks up cached K, V.
  
  Memory trade-off: storing K, V uses GPU memory,
  but saves massive computation (O(n) instead of O(n²) per token).
```

---

### Q3: Why does attention have O(n²) complexity? Can we avoid it?

**A:**
```
WHY O(n²):
  Every token computes an attention score with EVERY other token.
  n tokens → n × n score matrix.
  
  n = 1,000   → 1,000,000 scores       (fast)
  n = 10,000  → 100,000,000 scores     (slow)
  n = 100,000 → 10,000,000,000 scores  (very slow)

HOW TO AVOID IT:

1. SLIDING WINDOW (Mistral) — O(n × w)
   Each token only looks at last w tokens
   w=4096 for Mistral → linear in n

2. FLASH ATTENTION — Still O(n²) but 2-4x faster
   Doesn't reduce theoretical complexity
   Reduces memory IO (the real bottleneck)

3. LINEAR ATTENTION — O(n)
   Replace softmax(QK^T)V with φ(Q)(φ(K)^T V)
   Kernel trick: compute K^T V first (d×d matrix, not n×n)
   Lower quality, used in Mamba, RWKV

4. SPARSE ATTENTION (BigBird, Longformer) — O(n × √n)
   Combine local + global + random attention
   Only compute subset of n×n scores

5. RING ATTENTION — O(n²) total but distributed
   Distribute sequence across multiple GPUs
   Each GPU handles a chunk, passes KV to neighbors
   Enables million-token contexts on GPU clusters
```

---

### Q4: What is RoPE and why is it better than learned positional embeddings?

**A:**
```
LEARNED POSITIONAL EMBEDDINGS (GPT-2, BERT):
  Position 0 → trainable vector [v₀]
  Position 1 → trainable vector [v₁]
  ...
  Position 1023 → trainable vector [v₁₀₂₃]
  
  Problem: trained for 1024 positions → CANNOT handle position 1025
  The model has a hard context limit from training.

RoPE (Llama, Mistral, Phi):
  Instead of ADDING a position vector, ROTATE the embedding.
  Position k → rotate embedding by angle k × θ
  
  Why it's better:
  1. RELATIVE POSITION: The attention between pos 5 and pos 3 depends
     only on the DISTANCE (2), not absolute positions.
     
  2. EXTRAPOLATION: Can extend beyond training length using scaling:
     - Position Interpolation: scale positions to fit
     - NTK-aware scaling: adjust rotation frequencies
     - YaRN: best of both worlds
     
     Llama 3.1: trained on 8K → extended to 128K using RoPE scaling!
  
  3. NO EXTRA PARAMETERS: computed mathematically, not learned
```

---

### Q5: A transformer has 70B params with 80 layers. How many params per layer?

**A:**
```python
# Llama 3.1 70B architecture
d_model = 8192       # hidden dimension
n_heads = 64         # query heads
n_kv_heads = 8       # KV heads (GQA)
d_ff = 28672         # FFN intermediate dimension (3.5x d_model)
vocab_size = 128256  # vocabulary
n_layers = 80

# Per-layer parameter count:

# Attention Q projection: d_model × d_model = 8192² = 67M
attn_q = d_model * d_model  # 67,108,864

# Attention K projection: d_model × (n_kv_heads × d_k)
d_k = d_model // n_heads  # 128
attn_k = d_model * (n_kv_heads * d_k)  # 8192 × 1024 = 8,388,608

# Attention V projection: same as K
attn_v = attn_k  # 8,388,608

# Attention output: d_model × d_model
attn_o = d_model * d_model  # 67,108,864

# FFN (SwiGLU has 3 matrices)
ffn_w1 = d_model * d_ff      # 8192 × 28672 = 234,881,024
ffn_w2 = d_ff * d_model       # 234,881,024
ffn_w3 = d_model * d_ff       # 234,881,024 (gate)

# RMSNorm: 2 × d_model
norm = 2 * d_model  # 16,384

per_layer = attn_q + attn_k + attn_v + attn_o + ffn_w1 + ffn_w2 + ffn_w3 + norm
print(f"Per layer: {per_layer:,} = {per_layer/1e9:.2f}B")  # ~0.86B per layer

all_layers = per_layer * n_layers
print(f"All layers: {all_layers/1e9:.1f}B")  # ~68.6B

# Embedding + output
embedding = vocab_size * d_model  # 128256 × 8192 = 1.05B
# Output projection shares weights with embedding

total = all_layers + embedding
print(f"Total: {total/1e9:.1f}B")  # ~69.7B ≈ 70B ✓
```

---

### Q6: Your model generates 30 tokens/second but you need 100. What options do you have?

**A:**
```
OPTION 1: SPECULATIVE DECODING (2-3x speedup, zero quality loss)
  Use Llama 8B as draft model for Llama 70B
  Draft 5 tokens → verify all at once
  Effective: ~70-90 tokens/second

OPTION 2: QUANTIZATION (1.5-2x speedup)
  Float16 → Int4 (AWQ or GPTQ)
  Less memory → more KV cache → more batching → higher throughput
  Effective: ~50-60 tokens/second

OPTION 3: BATCHING + PAGED ATTENTION (vLLM)
  Batch multiple requests together
  GPU utilization goes from 30% to 90%
  Per-request speed same, but total throughput 3-5x
  
OPTION 4: TENSOR PARALLELISM
  Split model across 2-4 GPUs
  Each GPU processes part of each layer in parallel
  ~1.8x speedup per doubling of GPUs

OPTION 5: SMALLER MODEL + FINE-TUNING
  Fine-tune Llama 8B on your task
  8B generates at ~150 tokens/second
  Quality might be 90% of 70B for your specific task
  
OPTION 6: STREAMING
  Send tokens as they're generated
  User perceives first token in ~100ms instead of waiting 3s
  Doesn't actually speed up generation, improves UX

COMBINED APPROACH FOR 100 tok/s:
  Quantize (int4) + Speculative decoding + vLLM batching
  → Achievable on 2× H100 GPUs
```

---

## Production Scenario: Serving a 200B Parameter Model

```python
class LargeModelServingPlan:
    """
    Scenario: Deploy a 200B parameter model for internal use.
    Requirements: 50 QPS, p95 < 3s, 8K context, 24/7 availability.
    """
    
    def capacity_plan(self):
        model_params = 200e9
        
        # Option A: Float16 (no quantization)
        option_a = {
            "name": "Float16 — Maximum Quality",
            "model_memory_gb": model_params * 2 / 1e9,  # 400 GB
            "gpus_for_model": 6,  # 6× H100 80GB (need ~5.5, round up)
            "parallelism": "tensor parallel across 6 GPUs",
            "throughput_per_replica": "~15 QPS",
            "replicas_for_50qps": 4,
            "total_gpus": 24,
            "monthly_cost": 24 * 4.5 * 24 * 30,  # $77,760/month
        }
        
        # Option B: AWQ Int4 quantization
        option_b = {
            "name": "AWQ Int4 — Best Value",
            "model_memory_gb": model_params * 0.5 / 1e9,  # 100 GB
            "gpus_for_model": 2,  # 2× H100 80GB
            "parallelism": "tensor parallel across 2 GPUs",
            "throughput_per_replica": "~25 QPS",
            "replicas_for_50qps": 2,
            "total_gpus": 4,
            "monthly_cost": 4 * 4.5 * 24 * 30,  # $12,960/month
            "quality_impact": "< 1% degradation on benchmarks",
        }
        
        # Option C: Use API instead
        option_c = {
            "name": "API (GPT-4o) — Simplest",
            "gpus": 0,
            "infrastructure": "None",
            "cost_per_query": 0.02,  # ~2000 tokens
            "monthly_at_50qps": 50 * 86400 * 30 * 0.02,  # $2,592,000
            "verdict": "WAY too expensive at 50 QPS!",
        }
        
        return {
            "recommendation": "Option B (AWQ Int4)",
            "reason": "6x cheaper than float16, 200x cheaper than API, <1% quality loss",
            "options": [option_a, option_b, option_c]
        }
    
    def deployment_architecture(self):
        return """
        ┌──────────────────────────────────────────────┐
        │                Load Balancer                  │
        ├──────────────────────────────────────────────┤
        │         vLLM Serving Layer (4 GPUs)           │
        │                                              │
        │  Replica 1: GPU-0 + GPU-1 (tensor parallel)  │
        │  Replica 2: GPU-2 + GPU-3 (tensor parallel)  │
        │                                              │
        │  Configuration:                              │
        │    --model my-200b-model                     │
        │    --tensor-parallel-size 2                   │
        │    --quantization awq                        │
        │    --max-model-len 8192                      │
        │    --max-num-seqs 64                         │
        │    --enable-prefix-caching                   │
        │    --gpu-memory-utilization 0.90             │
        ├──────────────────────────────────────────────┤
        │  Monitoring:                                 │
        │    Prometheus + Grafana                      │
        │    Request latency, throughput, GPU util      │
        │    Queue depth, cache hit rate               │
        └──────────────────────────────────────────────┘
        
        Failover: If one replica fails, other handles load at 25 QPS
        Scale: Add GPU pairs for +25 QPS each
        """
```

---

## Production Scenario: Context Length Migration (8K → 128K)

```python
class ContextLengthMigration:
    """
    Scenario: Upgrade from 8K to 128K context model.
    
    This is NOT just swapping the model. Everything changes.
    """
    
    MIGRATION_PLAN = {
        "step_1_memory": {
            "problem": "KV cache grows 16x (8K→128K)",
            "before": "KV cache: 2 GB per request",
            "after": "KV cache: 32 GB per request",
            "solution": [
                "Enable GQA (8 KV heads instead of 64) → 4x reduction",
                "Int8 KV cache quantization → 2x reduction",
                "Paged attention (vLLM) → 90% less waste",
                "Net: 32 GB → ~2 GB effective per request",
            ]
        },
        "step_2_retrieval": {
            "problem": "More context ≠ better results (lost in the middle)",
            "research": "Studies show LLMs struggle with info in the middle of long contexts",
            "solution": [
                "Put most important context at START and END of prompt",
                "Use hierarchical retrieval: summaries first, details on demand",
                "Don't stuff 128K just because you can — retrieve what's relevant",
            ]
        },
        "step_3_cost": {
            "problem": "Input tokens cost money. 128K tokens = 16x cost per query",
            "solution": [
                "Smart context selection — don't fill to max",
                "Summarize long documents before injecting",
                "Use map-reduce for very long documents",
                "Cache long-context computations aggressively",
            ]
        },
        "step_4_latency": {
            "problem": "Prefill time grows linearly with context length",
            "numbers": {
                "8K": "~100ms prefill",
                "32K": "~400ms prefill",
                "128K": "~1.5s prefill",
            },
            "solution": [
                "Prefix caching — reuse common prefixes",
                "Chunked prefill — process in stages",
                "Streaming — send tokens as they generate",
            ]
        },
    }
```
