# Module 07 — Q&A + Production Scenarios: Model Tradeoffs

---

## Top 20 Interview Questions & Answers

### Q1: Your 70B model doesn't fit on a single GPU. Walk through every option to deploy it.

**A:**
```
70B model in float16 = 140 GB  (70B × 2 bytes)
Single H100 = 80 GB VRAM

OPTION 1: QUANTIZATION — Make the model smaller
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  INT8 quantization:  70B × 1 byte = 70 GB  → fits on 1× H100!
  INT4 quantization:  70B × 0.5 byte = 35 GB → fits on 1× A100-40GB!
  
  Quality loss:
    INT8: <1% degradation (almost free)
    INT4: 2-5% degradation (usually acceptable)
  
  Methods: GPTQ (fast, GPU), AWQ (quality-preserving), GGUF (CPU+GPU)
  
  ✅ Best option for most production use cases

OPTION 2: TENSOR PARALLELISM — Split across GPUs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Split each layer's weights across 2+ GPUs
  
  GPU 0: left half of every weight matrix
  GPU 1: right half of every weight matrix
  
  140 GB / 2 GPUs = 70 GB each → fits on 2× H100
  
  Requirements: NVLink between GPUs (600 GB/s)
  Without NVLink: PCIe is too slow, becomes bottleneck
  
  ✅ Best for lowest latency (GPUs work in parallel)

OPTION 3: PIPELINE PARALLELISM — Stack layers across GPUs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GPU 0: layers 0-39 (70 GB)
  GPU 1: layers 40-79 (70 GB)
  
  Data flows: GPU0 → GPU1 sequentially
  Only needs regular PCIe or InfiniBand
  
  ⚠️ Higher latency (sequential), but simpler networking

OPTION 4: OFFLOADING — Use CPU RAM and disk
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Keep some layers in CPU RAM, swap to GPU when needed
  
  Speed: 10-50x slower than full GPU
  Cost: cheapest option
  
  ⚠️ Only for development/testing, not production

OPTION 5: COMBINATION (most common in practice)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AWQ INT4 (35 GB) + Tensor Parallel across 2× A100-40GB
  Each GPU: 17.5 GB model + 22.5 GB for KV cache
  
  Result: fast inference + room for large batch sizes
  This is what most companies actually deploy.
```

---

### Q2: Explain quantization like I'm a product manager.

**A:**
```
ANALOGY: Photo quality

  float16 (full precision):
    📸 RAW photo — 25 MB, perfect quality
    Every pixel stored with extreme precision
    
  INT8 (8-bit quantization):
    📸 High-quality JPEG — 5 MB, looks identical
    Slightly less precision, but you can't tell
    99% quality, 50% the size
    
  INT4 (4-bit quantization):
    📸 Compressed JPEG — 1.5 MB, minor artifacts
    A trained eye might spot slight differences
    95-98% quality, 25% the size

FOR THE BUSINESS:
  ┌──────────┬──────────┬──────────┬──────────┐
  │ Precision│ GPU cost │ Speed    │ Quality  │
  ├──────────┼──────────┼──────────┼──────────┤
  │ float16  │ $9,000/mo│ 1×       │ 100%     │
  │          │ (2× H100)│          │          │
  ├──────────┼──────────┼──────────┼──────────┤
  │ INT8     │ $4,500/mo│ 1.5×     │ 99%      │
  │          │ (1× H100)│          │          │
  ├──────────┼──────────┼──────────┼──────────┤
  │ INT4     │ $800/mo  │ 2×       │ 95-98%   │
  │          │ (1× L4)  │          │          │
  └──────────┴──────────┴──────────┴──────────┘
  
  "We can cut our GPU costs by 80% with barely noticeable quality loss."
  
WHEN NOT TO QUANTIZE:
  - Medical/legal: every % of quality matters
  - Math-heavy tasks: quantization hurts precision most here
  - Your model is already small (<7B): less room to compress
```

---

### Q3: Compare GPTQ, AWQ, and GGUF quantization.

**A:**
```
┌─────────────┬────────────────┬────────────────┬───────────────────┐
│ Feature     │ GPTQ           │ AWQ            │ GGUF              │
├─────────────┼────────────────┼────────────────┼───────────────────┤
│ Full name   │ GPT Quantization│ Activation-   │ GPT-Generated     │
│             │ (post-training)│ Aware Weight Q.│ Unified Format    │
├─────────────┼────────────────┼────────────────┼───────────────────┤
│ Runs on     │ GPU only       │ GPU only       │ CPU, GPU, or both │
├─────────────┼────────────────┼────────────────┼───────────────────┤
│ Speed       │ Fast           │ Fast           │ Slower on CPU,    │
│             │                │                │ fast w/ GPU offload│
├─────────────┼────────────────┼────────────────┼───────────────────┤
│ Quality     │ Good           │ BEST           │ Good              │
│ (INT4)      │                │ (preserves     │                   │
│             │                │ important      │                   │
│             │                │ weights)       │                   │
├─────────────┼────────────────┼────────────────┼───────────────────┤
│ Key idea    │ Minimize       │ Keep "salient" │ Split layers      │
│             │ reconstruction │ weights at     │ between CPU/GPU,  │
│             │ error per layer│ higher precision│ single file format│
├─────────────┼────────────────┼────────────────┼───────────────────┤
│ Quant time  │ 30 min - 4 hrs │ 30 min - 4 hrs │ Minutes (convert) │
├─────────────┼────────────────┼────────────────┼───────────────────┤
│ Framework   │ AutoGPTQ,      │ AutoAWQ,       │ llama.cpp         │
│             │ ExLlamaV2      │ vLLM           │                   │
├─────────────┼────────────────┼────────────────┼───────────────────┤
│ Best for    │ GPU inference  │ Production GPU │ Local/edge,       │
│             │ servers        │ deployment     │ MacBooks, phones  │
├─────────────┼────────────────┼────────────────┼───────────────────┤
│ Used by     │ HuggingFace    │ vLLM, TGI      │ Ollama, LM Studio│
│             │ community      │ (recommended)  │ local AI apps     │
└─────────────┴────────────────┴────────────────┴───────────────────┘

DECISION TREE:
  Need to run on CPU/laptop? → GGUF
  Need best quality on GPU?  → AWQ
  Quick prototyping on GPU?  → GPTQ
  Production GPU serving?    → AWQ with vLLM
```

---

### Q4: What is knowledge distillation? Give a real-world example.

**A:**
```
CONCEPT:
  Teacher: Large, expensive, accurate model (GPT-4, 1.7T params)
  Student: Small, cheap, fast model (8B params)
  
  Train the student to mimic the teacher's behavior.
  Student learns not just the right answer, but the DISTRIBUTION.

EXAMPLE: Customer support classifier

  TEACHER (GPT-4): "Is this customer angry?"
    Output probabilities: [angry: 0.72, frustrated: 0.20, neutral: 0.08]
    
  HARD LABELS (traditional training):
    Target: [angry: 1.0, frustrated: 0.0, neutral: 0.0]
    Student only learns: "this is angry." Period.
    
  SOFT LABELS (distillation):
    Target: [angry: 0.72, frustrated: 0.20, neutral: 0.08]
    Student learns: "this is mostly angry, somewhat frustrated"
    The 0.20 for frustrated carries RICH INFORMATION!

WHY SOFT LABELS ARE BETTER:
  "A BMW looks more like an Audi than a carrot."
  
  Hard labels: BMW=1, everything else=0
  Soft labels: BMW=0.7, Audi=0.15, Mercedes=0.1, carrot=0.00001
  
  The student learns RELATIONSHIPS between classes!

PRODUCTION EXAMPLE:
  Step 1: Run 100K customer queries through GPT-4     Cost: $1,500
  Step 2: Save all (query, GPT-4 probabilities) pairs  
  Step 3: Fine-tune Llama 8B on these pairs             Cost: $50
  Step 4: Deploy Llama 8B                                Cost: $800/month
  
  RESULT:
    GPT-4 accuracy on your task: 94%
    Distilled Llama 8B accuracy: 91% ← Only 3% drop!
    GPT-4 cost: $3,000/month (API)
    Llama 8B cost: $800/month (1× L4)
    Savings: $2,200/month = $26,400/year
```

---

### Q5: Explain speculative decoding. When does it help and when doesn't it?

**A:**
```
PROBLEM:
  Large model generates tokens one at a time.
  Each token: ~50ms (bound by memory bandwidth, not compute).
  100 tokens = 5 seconds. Too slow!
  
  The GPU is actually UNDERUTILIZED — it could process more tokens
  in parallel, but autoregressive generation is sequential.

SPECULATIVE DECODING:
  1. Draft model (8B, fast): generates K=5 tokens quickly
     "The quick brown fox jumps"           → 5 × 10ms = 50ms
  
  2. Target model (70B, accurate): verifies all 5 in ONE pass
     "The quick brown fox jumps"           → 1 × 50ms = 50ms
     Check: [✓, ✓, ✓, ✗, -]
     "fox" was right, but model wanted "dog" not "jumps"
  
  3. Accept first 3, regenerate from "dog"
     Net: 3 tokens in 100ms instead of 3 × 50ms = 150ms
     
SPEEDUP: 2-3× for well-matched draft models

WHEN IT HELPS:
  ✅ Long outputs (stories, code, articles)
  ✅ Predictable text (boilerplate, common patterns)
  ✅ Draft model is good (same family, e.g., Llama 8B → 70B)
  ✅ Single-user latency-sensitive applications
  
WHEN IT DOESN'T HELP:
  ❌ Short outputs (<20 tokens) — overhead dominates
  ❌ High-batch throughput — GPU already saturated
  ❌ Very creative tasks — draft model guesses wrong often
  ❌ Draft model too different from target — low acceptance rate
  
ACCEPTANCE RATE MATTERS:
  Rate=80% (typical): draft 5, accept 4 → 4×/2 passes = 2× speedup
  Rate=40% (creative): draft 5, accept 2 → 2×/2 passes = 1× (no gain!)
  Rate=95% (boilerplate): draft 5, accept 5 → 5×/2 = 2.5× speedup
```

---

### Q6: Your model is memory-bound during inference. How do you diagnose and fix this?

**A:**
```
MEMORY-BOUND vs COMPUTE-BOUND:

  COMPUTE-BOUND: GPU math units are the bottleneck
    → Fix: get a GPU with more FLOPS
    → When: large batch sizes, prefill phase
  
  MEMORY-BOUND: Reading weights from memory is the bottleneck
    → Fix: reduce memory reads or get higher bandwidth
    → When: small batch sizes, token generation phase

DIAGNOSIS:
  1. Profile with nvidia-smi:
     GPU utilization: 30%  ← Low! (GPU is WAITING for data)
     Memory bandwidth: 95%  ← High! (bottleneck!)
     → Memory-bound confirmed
  
  2. Check arithmetic intensity:
     FLOPs per byte = 2 × model_params / (model_size_bytes)
     For float16: 2 × 70B / (140 GB) = 1 FLOP/byte
     H100 balance: 4000 TFLOPS / 3.35 TB/s = 1194 FLOPs/byte
     
     Model intensity (1) << GPU balance (1194)
     → Severely memory-bound at batch_size=1

FIXES (in order of effectiveness):

  1. INCREASE BATCH SIZE (free!)
     Batch=1:  read weights once, compute 1 token  → 1 FLOP/byte
     Batch=32: read weights once, compute 32 tokens → 32 FLOP/byte
     Batch=128: fully utilizing the GPU!
     Use vLLM continuous batching to naturally increase batch size.
  
  2. QUANTIZE (reduces memory reads)
     float16 → INT4: 4× less data to read = 4× less memory pressure
     Effectively: weights are smaller, fewer bytes to transfer.
  
  3. USE TENSOR PARALLELISM (more bandwidth)
     2× GPUs = 2× memory bandwidth = 2× throughput for small batches
     Only helps if single-GPU bandwidth is the limit.
  
  4. GQA / MQA (for KV cache bottleneck)
     Reduce KV heads from 32 to 8 → 4× smaller KV cache reads.
```

---

### Q7: You need to serve a model on mobile/edge devices. What are your options?

**A:**
```
CONSTRAINTS:
  Phone: 6 GB RAM, ARM CPU, maybe GPU
  Edge device: 4-16 GB RAM, limited power
  Latency target: <2 seconds for response
  Model: need at least "good enough" quality

OPTION 1: Small model + heavy quantization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Llama 3.2 1B, GGUF Q4_K_M format
  Size: ~700 MB
  Speed: ~15 tokens/sec on iPhone 15
  Quality: Good for simple tasks (summaries, classification)
  
  Framework: llama.cpp, MLC-LLM
  Pro: Fully offline, no network needed
  Con: Limited quality for complex reasoning

OPTION 2: Distilled task-specific model
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Distill GPT-4 into a 500M model for YOUR specific task
  Size: ~300 MB (INT8)
  Speed: ~50 tokens/sec
  Quality: 90%+ of GPT-4 ON YOUR SPECIFIC TASK
  
  Pro: Tiny, fast, specialized
  Con: Only handles one task (not general-purpose)

OPTION 3: Hybrid (on-device + cloud)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Simple queries → on-device small model (80% of queries)
  Complex queries → API call to cloud model (20% of queries)
  
  Pro: Best quality + offline capability
  Con: Needs network for complex queries

OPTION 4: Sparse attention model
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Use sliding window attention (2K window)
  Reduces memory from O(n²) to O(n × W)
  Fits larger context in limited RAM
  
RECOMMENDED for most mobile apps:
  Option 3 (Hybrid) with:
  - On-device: Llama 3.2 1B Q4 (700 MB)
  - Cloud fallback: GPT-4o-mini or Llama 70B API
  - Router: simple keyword + length heuristic on-device
```

---

### Q8: Compare sparse attention patterns. When would you use each?

**A:**
```
┌────────────────┬────────────────┬──────────────┬─────────────────┐
│ Pattern        │ Complexity     │ Quality      │ Best for        │
├────────────────┼────────────────┼──────────────┼─────────────────┤
│ Full attention │ O(n²)          │ Baseline     │ Short context   │
│                │                │              │ (<4K tokens)    │
├────────────────┼────────────────┼──────────────┼─────────────────┤
│ Sliding window │ O(n × W)       │ ~99% of full │ Chat, streaming │
│ (Mistral)      │ W=4096         │              │ real-time       │
├────────────────┼────────────────┼──────────────┼─────────────────┤
│ BigBird        │ O(n × (W+G+R))│ ~98% of full │ Long documents  │
│ (local+global  │                │              │ (NLP tasks)     │
│  +random)      │                │              │                 │
├────────────────┼────────────────┼──────────────┼─────────────────┤
│ Longformer     │ O(n × (W+G))  │ ~98% of full │ Long documents  │
│ (local+global) │                │              │ with key tokens │
├────────────────┼────────────────┼──────────────┼─────────────────┤
│ Dilated        │ O(n × W/gap)  │ ~95% of full │ Very long seq   │
│                │                │              │ (DNA, audio)    │
├────────────────┼────────────────┼──────────────┼─────────────────┤
│ Ring attention │ O(n²/GPUs)     │ 100% of full │ 1M+ tokens,    │
│ (distributed)  │                │              │ multi-GPU       │
└────────────────┴────────────────┴──────────────┴─────────────────┘

SLIDING WINDOW (most popular):
  Token at position i attends to [i-W, i]
  
  ┌────────────────────────────┐
  │ ████░░░░░░░░░░░░░░░░░░░░░│ Token 1
  │ █████░░░░░░░░░░░░░░░░░░░░│ Token 2
  │ ██████░░░░░░░░░░░░░░░░░░░│ Token 3
  │ ░██████░░░░░░░░░░░░░░░░░░│ Token 4  (window = 6)
  │ ░░██████░░░░░░░░░░░░░░░░░│ Token 5
  │ ...                       │
  └────────────────────────────┘
  
  Information propagates through layers:
  Layer 1: each token sees 4K neighbors
  Layer 32: information from 32 × 4K = 128K tokens away!
  
  Like a telephone game, but through neural network layers.
```

---

## Production Scenario: Choosing the Right Optimization for Your Bottleneck

```python
class OptimizationDecisionEngine:
    """
    Scenario: Given a production deployment's symptoms, 
    choose the right optimization.
    
    This is the #1 system design question at FAANG for ML infra.
    """
    
    DECISION_MATRIX = """
    ┌─────────────────────┬───────────────┬────────────────────────┐
    │ Bottleneck          │ Symptom       │ Best Optimization      │
    ├─────────────────────┼───────────────┼────────────────────────┤
    │ MODEL TOO BIG       │ OOM error     │ 1. Quantize (INT4/INT8)│
    │ for GPU             │               │ 2. Tensor parallelism  │
    │                     │               │ 3. Offload to CPU      │
    ├─────────────────────┼───────────────┼────────────────────────┤
    │ KV CACHE TOO BIG    │ OOM at long   │ 1. Paged attention     │
    │                     │ contexts      │ 2. GQA (fewer KV heads)│
    │                     │               │ 3. Sliding window attn │
    │                     │               │ 4. Quantize KV cache   │
    ├─────────────────────┼───────────────┼────────────────────────┤
    │ PREFILL TOO SLOW    │ TTFT > 2s     │ 1. FlashAttention      │
    │ (long prompts)      │               │ 2. Shorter prompts     │
    │                     │               │ 3. Prefix caching      │
    │                     │               │ 4. Chunked prefill     │
    ├─────────────────────┼───────────────┼────────────────────────┤
    │ GENERATION TOO SLOW │ TPS < 20      │ 1. Increase batch size │
    │ (per token)         │               │ 2. Quantize weights    │
    │                     │               │ 3. Speculative decoding│
    │                     │               │ 4. Tensor parallelism  │
    ├─────────────────────┼───────────────┼────────────────────────┤
    │ THROUGHPUT TOO LOW  │ QPS < target  │ 1. Continuous batching │
    │ (total system)      │               │ 2. Add replicas        │
    │                     │               │ 3. Semantic caching    │
    │                     │               │ 4. Model routing       │
    ├─────────────────────┼───────────────┼────────────────────────┤
    │ COST TOO HIGH       │ $$$           │ 1. Route to smaller    │
    │                     │               │ 2. Quantize            │
    │                     │               │ 3. Distill             │
    │                     │               │ 4. Cache responses     │
    ├─────────────────────┼───────────────┼────────────────────────┤
    │ QUALITY TOO LOW     │ User complaints│ 1. Bigger model       │
    │                     │               │ 2. Better prompts      │
    │                     │               │ 3. Fine-tune           │
    │                     │               │ 4. RAG (add knowledge) │
    └─────────────────────┴───────────────┴────────────────────────┘
    """
    
    REAL_SCENARIO = """
    CASE STUDY: E-commerce product description generator
    
    BEFORE OPTIMIZATION:
    ┌──────────────────────────────────────────────┐
    │ Model: Llama 70B float16                     │
    │ Hardware: 4× A100-40GB (tensor parallel)     │
    │ Monthly cost: $12,000                        │
    │ Throughput: 50 QPS                           │
    │ TTFT: 1.2 seconds                            │
    │ Tokens/sec: 35                               │
    │ Quality: 4.5/5 (human eval)                  │
    │ Context: 4K tokens (product info + examples) │
    └──────────────────────────────────────────────┘
    
    REQUIREMENTS: Need 200 QPS, <500ms TTFT, keep quality ≥4.0/5
    
    OPTIMIZATION STEPS:
    
    Step 1: Quantize to AWQ INT4 (35 GB → fits on 1× H100)
      Cost: $12,000 → $4,500 (63% reduction!)
      Quality: 4.5 → 4.4 (barely changed)
      TTFT: 1.2s → 0.8s (smaller model, faster prefill)
      QPS: 50 → 80 (more memory for batching)
    
    Step 2: Enable vLLM continuous batching
      QPS: 80 → 200 ✓
      TTFT: 0.8s → 0.6s (continuous batching = less queuing)
    
    Step 3: Prefix caching for system prompt
      TTFT: 0.6s → 0.3s ✓ (1K token system prompt cached)
    
    Step 4: Distill to Llama 8B for simple products
      Route: Simple (60%) → 8B, Complex (40%) → 70B
      Cost: 0.6 × $800 + 0.4 × $4,500 = $2,280
      Quality: Simple=4.1, Complex=4.4, Avg=4.2 ✓
    
    AFTER OPTIMIZATION:
    ┌──────────────────────────────────────────────┐
    │ Models: Llama 8B + Llama 70B AWQ             │
    │ Hardware: 1× L4 + 1× H100                   │
    │ Monthly cost: $2,280 (81% reduction!)        │
    │ Throughput: 350 QPS ✓                        │
    │ TTFT: 300ms ✓                                │
    │ Tokens/sec: 45 (8B) / 35 (70B)              │
    │ Quality: 4.2/5 ✓                             │
    └──────────────────────────────────────────────┘
    """
```

---

## Production Scenario: A/B Testing Model Optimizations

```python
class ModelOptimizationABTest:
    """
    Scenario: You want to deploy a quantized model but need to prove
    it doesn't hurt user experience before fully rolling out.
    """
    
    EXPERIMENT_DESIGN = """
    HYPOTHESIS: AWQ INT4 quantization of Llama 70B produces
    indistinguishable results from FP16 for our use case.
    
    METRICS:
    ┌────────────────────┬────────────┬─────────────┐
    │ Metric             │ Type       │ Threshold   │
    ├────────────────────┼────────────┼─────────────┤
    │ Task accuracy      │ Quality    │ <2% drop    │
    │ User satisfaction  │ Quality    │ <0.2 drop   │
    │ Hallucination rate │ Safety     │ <1% increase│
    │ TTFT               │ Latency    │ Should drop │
    │ Tokens per second  │ Latency    │ Should rise │
    │ GPU utilization    │ Efficiency │ Should drop │
    │ Cost per query     │ Cost       │ Should drop │
    └────────────────────┴────────────┴─────────────┘
    
    TRAFFIC SPLIT:
    Week 1: 5% to INT4, 95% to FP16 (safety check)
    Week 2: 20% to INT4, 80% to FP16 (statistical significance)
    Week 3: 50/50 (final validation)
    Week 4: 100% to INT4 (if all metrics pass)
    """
    
    IMPLEMENTATION = """
    class ModelABRouter:
        def __init__(self):
            self.control = "llama-70b-fp16"    # Variant A
            self.treatment = "llama-70b-awq4"  # Variant B
            self.traffic_pct = 0.20            # 20% to treatment
        
        async def route(self, request):
            # Deterministic: same user always gets same variant
            variant = "treatment" if hash(request.user_id) % 100 < self.traffic_pct * 100 else "control"
            
            model = self.treatment if variant == "treatment" else self.control
            
            start = time.time()
            response = await generate(model, request.prompt)
            latency = time.time() - start
            
            # Log for analysis
            log_experiment({
                "user_id": request.user_id,
                "variant": variant,
                "model": model,
                "latency_ms": latency * 1000,
                "input_tokens": count_tokens(request.prompt),
                "output_tokens": count_tokens(response),
                "timestamp": datetime.now(),
            })
            
            return response
    
    STATISTICAL ANALYSIS (after 2 weeks):
    ┌────────────────────┬──────────┬──────────┬──────────┐
    │ Metric             │ FP16     │ INT4     │ P-value  │
    ├────────────────────┼──────────┼──────────┼──────────┤
    │ Task accuracy      │ 92.3%    │ 91.8%    │ 0.34     │
    │ User satisfaction  │ 4.31     │ 4.28     │ 0.42     │
    │ Hallucination rate │ 2.1%     │ 2.3%     │ 0.61     │
    │ TTFT (p50)         │ 820ms    │ 340ms    │ <0.001 ✓ │
    │ TPS                │ 35       │ 52       │ <0.001 ✓ │
    │ Cost per query     │ $0.012   │ $0.004   │ <0.001 ✓ │
    └────────────────────┴──────────┴──────────┴──────────┘
    
    CONCLUSION:
    - Quality metrics: no statistically significant difference (p > 0.05)
    - Performance metrics: significantly better with INT4
    - DECISION: Roll out INT4 to 100% ✓
    - SAVINGS: $0.008/query × 2M queries/month = $16,000/month
    """
```

---

## Quick Reference: When to Use What

```
OPTIMIZATION CHEAT SHEET (print this and pin it to your desk)

Got 30 seconds? Here's what to try first:

  OOM error?           → Quantize to INT4 (AWQ or GGUF)
  Slow first token?    → Enable FlashAttention + reduce prompt size
  Slow generation?     → Increase batch size + continuous batching
  Too expensive?       → Route simple → small model, complex → big
  Need offline/edge?   → GGUF + llama.cpp
  100K+ context?       → Sliding window attention + RoPE
  Need 99.9% quality?  → DON'T quantize; scale horizontally instead

Still stuck? Read Module 06 (optimizations) and Module 04 (internals).
```

---

*Continue to [Module 08 QA](../08-reasoning-and-verification/QA-production-scenarios.md)*
