# Module 05 — Q&A + Production Scenarios: Transformer Walkthrough

---

## Top 15 Interview Questions & Answers

### Q1: Why do we use a causal mask in decoder-only models?

**A:**
```
THE PROBLEM WITHOUT A MASK:
  Input sequence: "The cat sat on the ___"
  
  Without mask, token "cat" can see "sat" and "on" during training.
  That's CHEATING! The model should predict "sat" without seeing it.

CAUSAL MASK — Only look backward:
                The   cat   sat   on   ___
  The    [  ✓     ✗     ✗    ✗    ✗  ]
  cat    [  ✓     ✓     ✗    ✗    ✗  ]
  sat    [  ✓     ✓     ✓    ✗    ✗  ]
  on     [  ✓     ✓     ✓    ✓    ✗  ]
  ___    [  ✓     ✓     ✓    ✓    ✓  ]

  ✓ = Can attend to    ✗ = Masked out (set to -infinity before softmax)

WHY THIS ENABLES PARALLEL TRAINING:
  During training, we process ALL positions at once.
  The mask ensures each position only sees its past.
  This simulates autoregressive generation in one forward pass!
  
  Without mask → need to generate tokens one by one during training.
  With mask → train on entire sequence in one shot. Massive speedup.

CODE:
  mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1) * -1e9
  # Upper triangle = -infinity → softmax turns to 0
  attention = softmax(Q @ K.T / sqrt(d_k) + mask)
```

---

### Q2: What is multi-head attention and why not just one big head?

**A:**
```
SINGLE HEAD (d_model = 512):
  Q, K, V are all 512-dimensional
  Learns ONE type of relationship between tokens
  Like reading a document with one lens

MULTI-HEAD (h=8 heads, d_k = 64):
  Split into 8 heads, each with 64 dimensions
  Each head independently computes attention
  Each learns a DIFFERENT relationship

WHAT EACH HEAD LEARNS (observed in GPT-2):
  Head 0: Syntactic — subject looks at its verb
  Head 1: Positional — token looks at previous token
  Head 2: Semantic — word looks at its synonym/antonym
  Head 3: Coreference — pronoun looks at its referent
  Head 4: Punctuation — clause boundaries
  Head 5: Rare patterns — idioms, multi-word expressions
  Head 6: Copy — token looks at same token elsewhere
  Head 7: Global — broad attention across full context

WHY MULTI > SINGLE:
  Single head must learn ALL patterns in one attention distribution.
  Multi-head learns specialized patterns then combines them.
  
  Analogy: 
    Single head = one person reading a book once
    Multi-head = 8 people each reading for different things
                 (grammar, plot, characters, themes, style...)
    Then combining their notes.

COMPUTATION — Exactly the same cost!
  Single:  512 × 512 = 262,144 operations
  Multi:   8 × (64 × 64) = 8 × 4,096 = 32,768... wait, that's less?
  
  The W_Q, W_K, W_V projections: 512 → 512 (same total parameters)
  The attention computation: 8 parallel small attentions ≈ 1 big one
  Final projection W_O: 512 → 512
  Total: same parameter count, same FLOPs, much better representations!
```

---

### Q3: Trace the exact shapes through a Transformer block for batch_size=4, seq_len=128, d_model=768, heads=12.

**A:**
```
GIVEN: B=4, S=128, D=768, H=12, d_k=768/12=64

INPUT:
  x: (4, 128, 768)         # batch, sequence, embedding

LAYER NORM 1:
  norm(x): (4, 128, 768)   # same shape, normalized

MULTI-HEAD ATTENTION:
  ┌─ Q = x @ W_Q            (4, 128, 768) @ (768, 768) → (4, 128, 768)
  ├─ K = x @ W_K            (4, 128, 768) @ (768, 768) → (4, 128, 768)
  └─ V = x @ W_V            (4, 128, 768) @ (768, 768) → (4, 128, 768)
  
  Reshape to heads:
  ┌─ Q: (4, 128, 768) → (4, 12, 128, 64)    # B, H, S, d_k
  ├─ K: (4, 128, 768) → (4, 12, 128, 64)
  └─ V: (4, 128, 768) → (4, 12, 128, 64)
  
  Attention scores:
     Q @ K^T: (4, 12, 128, 64) @ (4, 12, 64, 128) → (4, 12, 128, 128)
     # Each head: each token attends to all tokens
     
  Mask + Softmax:
     scores: (4, 12, 128, 128)  # Probabilities sum to 1 along last dim
     
  Weighted sum:
     scores @ V: (4, 12, 128, 128) @ (4, 12, 128, 64) → (4, 12, 128, 64)
  
  Concat heads:
     (4, 12, 128, 64) → (4, 128, 768)   # Reshape back
     
  Output projection:
     (4, 128, 768) @ (768, 768) → (4, 128, 768)

RESIDUAL CONNECTION:
  x = x + attention_output    # (4, 128, 768)

LAYER NORM 2:
  norm(x): (4, 128, 768)

FFN:
  x @ W1 + b1: (4, 128, 768) @ (768, 3072) → (4, 128, 3072)   # Expand 4×
  GELU activation: (4, 128, 3072)
  x @ W2 + b2: (4, 128, 3072) @ (3072, 768) → (4, 128, 768)   # Compress back

RESIDUAL CONNECTION:
  x = x + ffn_output         # (4, 128, 768)

OUTPUT: (4, 128, 768) — SAME SHAPE AS INPUT ✓

PARAMETER COUNT for this block:
  Attention: 4 × (768 × 768) = 4 × 589,824 = 2,359,296
  FFN: (768 × 3072) + (3072 × 768) = 4,718,592
  LayerNorms: 2 × (2 × 768) = 3,072
  Biases: attention(4×768) + FFN(3072+768) = 6,912
  TOTAL: ~7,087,872 ≈ 7M params per block
  
  GPT-2 Small: 12 blocks × 7M = ~84M + embeddings ≈ 124M total ✓
```

---

### Q4: What happens to attention when context length doubles? Can we fix it?

**A:**
```
ATTENTION COMPLEXITY: O(n²) in sequence length

  Context    Attention Matrix    Memory    Time
  ─────────────────────────────────────────────
  1K tokens   1K × 1K = 1M      ~4 MB     1×
  4K tokens   4K × 4K = 16M     ~64 MB    16×
  16K tokens  16K × 16K = 256M  ~1 GB     256×
  128K tokens 128K × 128K       ~64 GB    16,384×  ← 🔥

FIXES (in order of popularity):

1. FlashAttention (no quality loss)
   - Tiles computation to fit in SRAM
   - Doesn't store full N×N matrix
   - 2-4x speedup, O(N) memory instead of O(N²)
   - Used by everyone (PyTorch default now)

2. Sliding Window Attention (minor quality loss)
   - Each token only attends to last W tokens
   - O(N × W) instead of O(N²)
   - Mistral uses W=4096
   - Quality: 99% of full attention for most tasks

3. GQA — Grouped Query Attention (no quality loss*)
   - Reduces KV heads from 32 to 8
   - Doesn't fix attention compute, fixes KV cache memory
   - Llama 2 70B uses this

4. Ring Attention (no quality loss)
   - Distributes sequence across GPUs
   - Each GPU holds seq_len/num_gpus
   - Attention computed in a ring pattern
   - Enables 1M+ context on clusters

5. Multi-Scale Attention (slight quality difference)
   - Different layers attend at different scales
   - Layer 1-4: local (1K window)
   - Layer 5-8: medium (4K window)  
   - Layer 9-12: global (full context)
   - Used by some long-context architectures
```

---

### Q5: Why do we need residual connections? What happens without them?

**A:**
```
RESIDUAL CONNECTION:
  output = x + layer(x)    # Instead of: output = layer(x)

WITHOUT RESIDUALS (depth > 20 layers):
  Layer 1: gradient = 0.95
  Layer 10: gradient = 0.95^10 = 0.60
  Layer 30: gradient = 0.95^30 = 0.21
  Layer 96: gradient = 0.95^96 = 0.007  ← VANISHING!
  
  The model can't learn in early layers because gradients
  are too small by the time they propagate back.

WITH RESIDUALS:
  The gradient has a "highway" — it can skip directly to any layer.
  
  ∂output/∂x = ∂(x + layer(x))/∂x = 1 + ∂layer(x)/∂x
  
  Even if ∂layer(x)/∂x → 0, the gradient is at least 1!
  
VISUALIZATION (Residual Stream):
  Token embedding: [0.1, -0.3, 0.5, ...]
       ↓
  + Attention Layer 1 output: [0.02, 0.01, -0.03, ...]
       ↓
  + FFN Layer 1 output:       [0.05, -0.02, 0.01, ...]
       ↓
  + Attention Layer 2 output: [0.03, 0.04, -0.01, ...]
       ↓
  ...
  
  Each layer ADDS a small update to the "residual stream."
  The stream carries information from all previous layers.
  
  Think of it like an assembly line:
  - Each worker (layer) adds one small improvement to the product
  - No single worker needs to build the whole thing
  - If a worker does nothing (identity), product still passes through

PRACTICAL IMPACT:
  GPT-2 (12 layers): works without residuals, but much worse
  GPT-3 (96 layers): CANNOT train without residuals
  Llama 3 (80+ layers): physically impossible without residuals
```

---

### Q6: What is the feedforward network doing in each Transformer block?

**A:**
```
ATTENTION = Communication between tokens
FFN = Processing within each token (independently!)

WHAT FFN DOES:
  1. Expand: 768 → 3072 (4× wider)
  2. Apply non-linearity (GELU)
  3. Compress: 3072 → 768

  The expansion creates a high-dimensional space where the model
  can perform complex transformations on each token independently.

CONCRETE EXAMPLE:
  After attention, token "bank" has gathered context:
    "The river bank was..."
    
  FFN looks up: "bank" + "river" context → activate the 
  "nature/geography" neurons, suppress "finance" neurons.
  
  This is essentially a KEY-VALUE MEMORY:
    Keys = rows of W1 (patterns to match)
    Values = columns of W2 (what to output when matched)
    
    W1 row 42: detects "bank near water words" → GELU activates
    W2 col 42: outputs "shift meaning toward geography"

EVIDENCE:
  Researchers found individual neurons in FFN that:
  - Fire for specific languages (neuron 1234 = French)
  - Fire for specific topics (neuron 5678 = legal text)
  - Store factual knowledge ("Eiffel Tower" → "Paris")
  
  When you edit these neurons, you can change what the model "knows"!

PARAMETER COUNT:
  FFN is ~2/3 of all parameters in a Transformer!
  Attention: 4 × d² = 4 × 768² = 2.36M
  FFN:       2 × d × 4d = 2 × 768 × 3072 = 4.72M  ← DOUBLE!
  
  Most of the model's "knowledge" is in the FFN weights.
```

---

### Q7: How does layer normalization work and why is Pre-LN better than Post-LN?

**A:**
```
LAYER NORM — Normalize across features for each token:
  Input: x = [3.0, -1.0, 0.5, 2.5]  (4 features for one token)
  Mean: μ = 1.25
  Std:  σ = 1.60
  Normalized: (x - μ) / σ = [1.09, -1.41, -0.47, 0.78]
  Scaled: γ * normalized + β  (learnable parameters)

WHY NORMALIZE?
  Without LN, activations grow or shrink as they pass through layers.
  Layer 1 output: [-0.1, 0.3]
  Layer 50 output: [-1500, 4200]  ← exploding!
  
  LN keeps values in a stable range → stable training.

POST-LN (Original Transformer):
  x → Attention → Add → LayerNorm → FFN → Add → LayerNorm
  
  Problem: gradients must flow THROUGH the LayerNorm to reach attention.
  At initialization, LayerNorm can distort gradients → unstable training.
  Requires learning rate warmup (waste of training time).

PRE-LN (GPT-2, Llama, all modern models):
  x → LayerNorm → Attention → Add → LayerNorm → FFN → Add
  
  Advantage: residual connection is OUTSIDE the LayerNorm.
  Gradient flows directly through the residual stream.
  More stable training, no warmup needed!

RMS-NORM (Llama):
  Even simpler — don't subtract mean, just divide by RMS:
  RMS = sqrt(mean(x²))
  output = x / RMS * γ
  
  Why? Subtracting mean adds no value in practice.
  RMSNorm is 10-15% faster than LayerNorm.
  Llama, Mistral, Gemma all use RMSNorm.
```

---

### Q8: What are the differences between encoder-only, decoder-only, and encoder-decoder architectures?

**A:**
```
┌──────────────┬─────────────┬──────────────┬────────────────┐
│ Feature      │ Encoder-only│ Decoder-only │ Encoder-Decoder│
├──────────────┼─────────────┼──────────────┼────────────────┤
│ Attention    │ Bidirectional│ Causal (left)│ Both           │
│ Examples     │ BERT, RoBERTa│ GPT, Llama  │ T5, BART       │
│ Training     │ Masked LM    │ Next-token  │ Seq-to-seq     │
│ Best for     │ Understanding│ Generation  │ Translation    │
│ Output       │ Embeddings   │ Text        │ Text           │
│ Used in 2024 │ Mostly for   │ DOMINANT    │ Niche (T5 for  │
│              │ embeddings   │ (ChatGPT etc)│ specific tasks)│
└──────────────┴─────────────┴──────────────┴────────────────┘

WHY DECODER-ONLY WON:
  1. Simpler: one architecture for all tasks
  2. Scales better: more params → better at everything
  3. Emergent abilities: reasoning, code, etc. appear at scale
  4. Can do understanding TOO (just phrase as generation)
  
  "Is this email spam?" 
    BERT: → [0.95, 0.05] (classification head)
    GPT:  → "Yes, this is spam because..." (more useful!)
```

---

### Q9: Your team is building a custom Transformer from scratch. What are the key hyperparameters and how do you choose them?

**A:**
```
HYPERPARAMETER SELECTION GUIDE:

┌────────────────────┬─────────────┬─────────────┬──────────────┐
│ Hyperparameter     │ Small (125M)│ Medium (1.3B)│ Large (70B)  │
├────────────────────┼─────────────┼─────────────┼──────────────┤
│ d_model           │ 768          │ 2048        │ 8192         │
│ n_layers          │ 12           │ 24          │ 80           │
│ n_heads           │ 12           │ 16          │ 64           │
│ d_ff (FFN width)  │ 3072 (4×d)  │ 8192 (4×d)  │ 28672(3.5×d)│
│ d_k (head dim)    │ 64           │ 128         │ 128          │
│ vocab_size        │ 50K          │ 50K         │ 128K         │
│ max_seq_len       │ 2048         │ 4096        │ 128K         │
│ GQA groups        │ no GQA       │ 4 groups    │ 8 groups     │
│ Activation        │ GELU         │ SwiGLU      │ SwiGLU       │
│ Norm              │ LayerNorm    │ RMSNorm     │ RMSNorm      │
│ Pos encoding      │ Learned      │ RoPE        │ RoPE         │
│ Learning rate     │ 6e-4         │ 2e-4        │ 1.5e-5       │
│ Batch size (tok)  │ 500K         │ 2M          │ 4M           │
│ Training tokens   │ 30B          │ 300B        │ 15T          │
│ GPUs              │ 8× A100     │ 64× A100    │ 16K× H100   │
│ Training time     │ ~1 day      │ ~1 week     │ ~3 months    │
└────────────────────┴─────────────┴─────────────┴──────────────┘

KEY RULES:
1. d_model should be divisible by n_heads
2. d_ff ≈ 4× d_model (or 8/3× with SwiGLU for same param count)
3. More layers with smaller d_model > fewer layers with bigger d_model
4. Head dimension 64 or 128 (optimized in hardware)
5. Vocab size: 32K-128K (Llama 3 uses 128K for multilingual)
6. Training tokens ≈ 20 × parameter count (Chinchilla scaling)
```

---

### Q10: Explain the "residual stream" view of Transformers.

**A:**
```
TRADITIONAL VIEW: Data flows through layers sequentially
  Input → Layer1 → Layer2 → ... → LayerN → Output

RESIDUAL STREAM VIEW: Layers write to a shared stream
  ┌─────────────────────────────────────────────────┐
  │            RESIDUAL STREAM                      │
  │  x₀ ──────────────────────────────────────→ out │
  │   ↑ write  ↑ write  ↑ write  ↑ write           │
  │   Attn1    FFN1     Attn2    FFN2     ...       │
  │   ↓ read   ↓ read   ↓ read   ↓ read            │
  └─────────────────────────────────────────────────┘
  
  x_final = x_0 + attn_1(x_0) + ffn_1(x_1) + attn_2(x_2) + ...

WHY THIS VIEW IS POWERFUL:
  1. Any layer can directly influence the output
     (just write to the residual stream)
  
  2. Early layers can communicate with late layers
     (via the shared stream, skipping intermediate layers)
  
  3. Layers can be "disabled" without breaking the model
     (if a layer outputs zeros, the stream flows unchanged)

EMPIRICAL EVIDENCE:
  - Removing random layers from GPT-2: <5% quality drop per layer
  - Some layers barely change the residual stream at all
  - Layer importance varies: layers 0-2 and last 2 are most important
  - Middle layers can often be pruned (depth pruning)

This view also explains why LORA fine-tuning works:
  Each LoRA adapter adds a tiny delta to the stream
  It doesn't need to change the whole layer, just nudge the stream
```

---

## Production Scenario: Debugging a Custom Transformer

```python
class TransformerDebugger:
    """
    Scenario: You trained a custom 1.3B Transformer from scratch.
    It generates plausible text but has specific failure modes.
    
    SYMPTOM 1: Model repeats itself after ~200 tokens
    SYMPTOM 2: Model ignores instructions in middle of long prompts
    SYMPTOM 3: Model outputs gibberish for non-English text
    """
    
    DIAGNOSIS_1 = """
    SYMPTOM: Repetition after ~200 tokens
    
    ROOT CAUSE CANDIDATES:
    ┌─────────────────────────┬──────────┬─────────────────────────┐
    │ Cause                   │ Likelihood│ How to check            │
    ├─────────────────────────┼──────────┼─────────────────────────┤
    │ Training data too short │ HIGH     │ Check avg doc length    │
    │ Positional encoding bug │ MEDIUM   │ Check RoPE max_position │
    │ Attention pattern issue │ MEDIUM   │ Visualize attention maps │
    │ Temperature too low     │ LOW      │ Try temp=0.8            │
    │ Repetition in training  │ LOW      │ Check dedup of data     │
    └─────────────────────────┴──────────┴─────────────────────────┘
    
    INVESTIGATION:
    
    1. Check training data:
       $ python -c "
       import json
       lengths = [len(doc.split()) for doc in load_training_data()]
       print(f'Median: {np.median(lengths)}, P95: {np.percentile(lengths, 95)}')
       "
       Result: Median=180 words, P95=400 words
       AHA! 50% of training data is <200 words!
       Model learned: "after ~200 tokens, start wrapping up"
    
    2. FIX: Add long-form documents to training data
       - Include books, papers, long articles
       - Ensure 20% of data is >2000 tokens
       - Fine-tune on long-context examples
    
    3. Quick fix for deployment:
       - Apply frequency penalty = 1.2 (penalize repeated tokens)
       - Apply presence penalty = 0.8 (encourage new topics)
       - Use sliding window repetition check:
    """
    
    REPETITION_FIX = """
    def detect_and_fix_repetition(tokens, window=50, threshold=0.6):
        '''Detect if recent tokens are repeating a pattern.'''
        recent = tokens[-window:]
        earlier = tokens[-2*window:-window]
        
        # Check n-gram overlap
        recent_ngrams = set(zip(recent, recent[1:], recent[2:]))
        earlier_ngrams = set(zip(earlier, earlier[1:], earlier[2:]))
        
        overlap = len(recent_ngrams & earlier_ngrams) / max(len(recent_ngrams), 1)
        
        if overlap > threshold:
            # Boost temperature and add penalties
            return {
                "temperature": 1.2,
                "frequency_penalty": 2.0,
                "presence_penalty": 1.5,
            }
        return {}
    """
    
    DIAGNOSIS_2 = """
    SYMPTOM: Model ignores instructions in middle of long prompts
    
    ROOT CAUSE: "Lost in the Middle" problem
    
    ┌────────────────────────────────────────────────┐
    │ Attention heatmap for 4K context:              │
    │                                                │
    │ Position:  0    1K   2K   3K   4K              │
    │ Attention: ████ ██   █    ██   ████            │
    │                                                │
    │ Model pays attention to START and END,         │
    │ but IGNORES the middle!                        │
    └────────────────────────────────────────────────┘
    
    This is a KNOWN problem with causal attention.
    Recent tokens have direct access (close proximity).
    First tokens set the context (high attention by convention).
    Middle tokens are neither special nor recent → ignored.
    
    FIXES:
    1. Restructure prompts: put key info at START or END
    2. Use explicit markers: "IMPORTANT: The following is critical..."
    3. Repeat key instructions at the end
    4. Fine-tune with "needle in haystack" examples
    5. Architectural: use sliding window + global attention tokens
    """
    
    DIAGNOSIS_3 = """
    SYMPTOM: Gibberish for non-English text
    
    ROOT CAUSE: Tokenizer vocabulary
    
    Investigation:
      English:  "Hello world"  → [15496, 995]         # 2 tokens
      Japanese: "こんにちは世界" → [2515, 232, 98, 163, # 12 tokens!
                                   11839, 99, 119, 29,
                                   22174, 236, 30266, 249]
    
    Problem: BPE tokenizer was trained mostly on English text.
    Non-English characters get broken into individual bytes.
    12 tokens for 7 characters = very inefficient!
    Model runs out of context much faster for non-English.
    
    FIXES:
    1. Retrain tokenizer with multilingual corpus
       - Include 30%+ non-English text
       - Increase vocab size from 50K → 128K (like Llama 3)
    
    2. Quick fix: Use a multilingual tokenizer (SentencePiece)
       - But requires retraining the model with new tokenizer
    
    3. Cheapest fix: Add a translation layer
       - Translate input to English → process → translate back
       - Quality loss but works without retraining
    """
```

---

## Production Scenario: Migrating from GPT to Self-Hosted Transformer

```python
class GPTToSelfHostedMigration:
    """
    Scenario: Your company wants to migrate from GPT-4 API to
    a self-hosted open-source Transformer for data privacy.
    
    Current: GPT-4 API, 10K queries/day, $3K/month
    Goal: Same quality, full data control, lower cost long-term
    """
    
    PHASE_1_EVALUATION = """
    Step 1: Benchmark open-source models against GPT-4
    
    ┌─────────────────┬──────────┬──────────┬──────────┬─────────┐
    │ Task            │ GPT-4    │ Llama 70B│ Llama 8B │ Mistral │
    │                 │ (baseline)│ (AWQ)   │ (FP16)   │ 7B      │
    ├─────────────────┼──────────┼──────────┼──────────┼─────────┤
    │ Classification  │ 94%      │ 91%      │ 87%      │ 88%     │
    │ Summarization   │ 4.2/5    │ 3.9/5    │ 3.5/5    │ 3.6/5   │
    │ Code generation │ 89%      │ 82%      │ 70%      │ 72%     │
    │ Reasoning       │ 91%      │ 84%      │ 68%      │ 71%     │
    │ Instruction     │ 95%      │ 88%      │ 80%      │ 82%     │
    ├─────────────────┼──────────┼──────────┼──────────┼─────────┤
    │ Avg Quality     │ 100%     │ ~90%     │ ~75%     │ ~77%    │
    │ Monthly cost    │ $3,000   │ $9,000   │ $800     │ $800    │
    │ (self-hosted)   │ (API)    │ (2×H100) │ (1×L4)   │ (1×L4)  │
    └─────────────────┴──────────┴──────────┴──────────┴─────────┘
    
    DECISION: Llama 70B for complex tasks + Llama 8B for simple ones
    """
    
    PHASE_2_DEPLOYMENT = """
    Step 2: Set up inference infrastructure
    
    ARCHITECTURE:
    ┌──────────┐     ┌──────────────┐     ┌───────────┐
    │ API      │────→│ Model Router │────→│ Llama 70B │ (complex)
    │ Gateway  │     │ (classify    │     │ 2× H100   │
    │          │     │  complexity) │     └───────────┘
    │          │     │              │     ┌───────────┐
    │          │     │              │────→│ Llama 8B  │ (simple)
    │          │     │              │     │ 1× L4     │
    │          │     │              │     └───────────┘
    │          │     │              │     ┌───────────┐
    │          │     │              │────→│ GPT-4 API │ (fallback)
    └──────────┘     └──────────────┘     └───────────┘
    
    ROUTING LOGIC:
    1. Simple queries (60%): classification, FAQ → Llama 8B
    2. Complex queries (35%): reasoning, code → Llama 70B
    3. Critical/edge cases (5%): fall back to GPT-4 API
    
    COST:
    Llama 8B:  1× L4 = $800/month
    Llama 70B: 2× H100 = $9,000/month
    GPT-4 API: 5% × $3,000 = $150/month
    Infra:     $500/month
    ──────────────────────
    Total:     $10,450/month
    
    Wait — that's MORE than $3K/month on GPT-4!
    
    OPTIMIZATION:
    - Use AWQ quantization: 70B fits on 1× H100 → $4,500/month
    - Use spot instances for 70B: $2,000/month
    - Semantic cache (40% hit rate): reduce GPU load
    
    FINAL COST: ~$4,000/month
    vs GPT-4 API: $3,000/month
    
    Premium: $1,000/month for FULL DATA PRIVACY
    At 10K queries/day, breakeven at ~50K queries/day on self-hosted.
    """
    
    PHASE_3_FINE_TUNING = """
    Step 3: Close the quality gap with fine-tuning
    
    Use your historical GPT-4 query/response pairs as training data!
    
    1. Collect 10K high-quality GPT-4 responses (manually verified)
    2. Fine-tune Llama 70B with LoRA (8-bit, rank=16)
       Training: 4 hours on 2× A100
       Cost: ~$30 (cloud GPU rental)
    
    3. Result after fine-tuning:
       ┌─────────────────┬──────────┬──────────────┐
       │ Task            │ GPT-4    │ Llama 70B FT │
       ├─────────────────┼──────────┼──────────────┤
       │ Classification  │ 94%      │ 93% (+2%)    │
       │ Summarization   │ 4.2/5    │ 4.1/5        │
       │ Your specific   │ 95%      │ 94% (!!!)    │
       │ use case        │          │              │
       └─────────────────┴──────────┴──────────────┘
       
       Fine-tuned model nearly matches GPT-4 ON YOUR DATA
       because it learned your specific domain patterns.
    """
```

---

## Quick Reference: Transformer Component Cheat Sheet

```
┌──────────────────────────────────────────────────────────────────┐
│                  TRANSFORMER QUICK REFERENCE                     │
├────────────────┬─────────────────────────────────────────────────┤
│ Component      │ Purpose & Key Facts                             │
├────────────────┼─────────────────────────────────────────────────┤
│ Token Embedding│ Converts token IDs → dense vectors              │
│                │ Size: vocab_size × d_model                      │
│                │ Llama 3: 128K × 8192 = 1B params just here!    │
├────────────────┼─────────────────────────────────────────────────┤
│ Pos Encoding   │ Gives model sense of position/order             │
│                │ RoPE: rotates Q/K by position angle             │
│                │ Enables length extrapolation                    │
├────────────────┼─────────────────────────────────────────────────┤
│ Causal Mask    │ Prevents tokens seeing future during training   │
│                │ Upper triangle = -∞ → softmax → 0              │
│                │ Enables parallel training of all positions      │
├────────────────┼─────────────────────────────────────────────────┤
│ Multi-Head Attn│ Tokens communicate, share information           │
│                │ Each head learns different relationship types   │
│                │ O(n²) complexity, ~1/3 of layer params          │
├────────────────┼─────────────────────────────────────────────────┤
│ FFN            │ Per-token processing, "knowledge storage"       │
│                │ Expand 4× then compress back                   │
│                │ ~2/3 of layer params, stores factual knowledge  │
├────────────────┼─────────────────────────────────────────────────┤
│ Layer Norm     │ Stabilizes activations between layers           │
│                │ Pre-LN: norm before attention (modern default)  │
│                │ RMSNorm: faster variant used by Llama           │
├────────────────┼─────────────────────────────────────────────────┤
│ Residual Conn  │ Skip connections for gradient flow              │
│                │ output = x + layer(x)                           │
│                │ Enables training of 100+ layer networks         │
├────────────────┼─────────────────────────────────────────────────┤
│ LM Head        │ Final linear layer → logits over vocabulary     │
│                │ Size: d_model × vocab_size                      │
│                │ Often shares weights with token embedding       │
└────────────────┴─────────────────────────────────────────────────┘
```

---

*Continue to [Module 07 QA](../07-model-tradeoffs/QA-production-scenarios.md)*
