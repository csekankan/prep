# 06.04 — Work Through a KV-Cache Allocation

> **One sentence:** This is a hands-on exercise where you calculate memory requirements for KV caches across different model sizes, batch sizes, and context lengths — the kind of back-of-envelope math FAANG interviewers expect.

---

## The Formula

```
KV Cache Memory = 2 × L × H_kv × d_k × S × B × bytes_per_element

Where:
  2        = Keys + Values (two tensors)
  L        = Number of transformer layers
  H_kv     = Number of KV heads (may differ from Q heads with GQA)
  d_k      = Dimension per head
  S        = Sequence length (how many tokens cached)
  B        = Batch size (concurrent requests)
  bytes    = 2 for float16, 1 for int8
```

---

## Exercise 1: Llama 3.1 8B

```python
# Llama 3.1 8B specs
L = 32          # layers
H_kv = 8        # GQA with 8 KV heads (32 query heads / 4 groups)
d_k = 128       # head dimension (4096 / 32)
bytes = 2       # float16

# Scenario A: Single request, 4K context
S = 4096
B = 1
memory_A = 2 * L * H_kv * d_k * S * B * bytes
print(f"Scenario A: {memory_A / 1e9:.2f} GB")  # ~0.54 GB

# Scenario B: 16 concurrent requests, 4K context
B = 16
memory_B = 2 * L * H_kv * d_k * S * B * bytes
print(f"Scenario B: {memory_B / 1e9:.2f} GB")  # ~8.59 GB

# Scenario C: Single request, 128K context
S = 128_000
B = 1
memory_C = 2 * L * H_kv * d_k * S * B * bytes
print(f"Scenario C: {memory_C / 1e9:.2f} GB")  # ~16.78 GB

# Model weights: ~16 GB in float16
# So KV cache for 128K context ≈ model weights!
```

---

## Exercise 2: Llama 3.1 70B

```python
L = 80          # layers
H_kv = 8        # GQA: still 8 KV heads
d_k = 128       # head dimension
bytes = 2       # float16

# How many concurrent 4K requests can we serve on a single A100 (80GB)?
model_weights = 70e9 * 2  # ~140 GB (need 2 GPUs minimum)
# On 2x A100 (160GB total), after model: 160 - 140 = 20 GB for KV cache

per_request_4k = 2 * L * H_kv * d_k * 4096 * 1 * bytes
print(f"KV cache per request (4K): {per_request_4k / 1e9:.2f} GB")  # ~1.34 GB

available = 20e9  # 20 GB free
max_concurrent = int(available / per_request_4k)
print(f"Max concurrent requests: {max_concurrent}")  # ~14

# With int8 quantized KV cache:
per_request_4k_int8 = 2 * L * H_kv * d_k * 4096 * 1 * 1  # 1 byte
max_concurrent_int8 = int(available / per_request_4k_int8)
print(f"Max with int8 KV cache: {max_concurrent_int8}")  # ~29 (2x more!)
```

---

## Exercise 3: Total GPU Memory Budget

```python
def total_memory_budget(
    model_params_B: float,    # Billion parameters
    num_layers: int,
    num_kv_heads: int,
    head_dim: int,
    seq_len: int,
    batch_size: int,
    model_dtype_bytes: int = 2,  # float16
    kv_dtype_bytes: int = 2,     # float16
) -> dict:
    """Complete GPU memory calculation."""
    
    # Model weights
    model_memory = model_params_B * 1e9 * model_dtype_bytes
    
    # KV cache
    kv_memory = 2 * num_layers * num_kv_heads * head_dim * seq_len * batch_size * kv_dtype_bytes
    
    # Activation memory (rough estimate: ~2x one layer's activations)
    activation_memory = batch_size * seq_len * (model_params_B * 1e9 / num_layers) * 0.01 * 2
    
    total = model_memory + kv_memory + activation_memory
    
    return {
        "model_weights_GB": model_memory / 1e9,
        "kv_cache_GB": kv_memory / 1e9,
        "activations_GB": activation_memory / 1e9,
        "total_GB": total / 1e9,
        "kv_fraction": kv_memory / total * 100,
    }

# Scenario: Serving Llama 70B with batch of 32, 8K context
budget = total_memory_budget(
    model_params_B=70, num_layers=80, num_kv_heads=8,
    head_dim=128, seq_len=8192, batch_size=32
)
for k, v in budget.items():
    print(f"  {k}: {v:.2f}")

# How many A100 GPUs needed?
gpus_needed = budget["total_GB"] / 80  # 80GB per A100
print(f"  A100s needed: {gpus_needed:.0f}")
```

---

## Quick Reference: Memory Rules of Thumb

```
Rule 1: Model weights (float16) ≈ 2 × params_in_billions GB
  7B model  ≈ 14 GB
  13B model ≈ 26 GB
  70B model ≈ 140 GB

Rule 2: KV cache per token per layer ≈ 2 × H_kv × d_k × 2 bytes
  With GQA (8 KV heads, d_k=128): 2 × 8 × 128 × 2 = 4,096 bytes per token per layer
  
Rule 3: To serve N concurrent requests of length S:
  KV memory = N × S × per_token_per_layer × num_layers

Rule 4: KV cache often exceeds model weights for long contexts
  70B model + 128K context = 140 GB weights + 160 GB KV cache
```

---

## Key Takeaways

1. **KV cache grows linearly** with sequence length and batch size
2. **GQA reduces KV memory** by 4-8x (fewer KV heads than query heads)
3. **For long contexts, KV cache dominates memory** — can exceed model weights
4. **Int8 KV quantization** doubles your serving capacity with minimal quality loss
5. **Back-of-envelope calculations** are essential for capacity planning

---

## 💼 FAANG Interview Questions

1. *"You have 4x A100 GPUs (320GB total). How many concurrent 32K-context requests can you serve with Llama 70B?"*
2. *"Your LLM service needs to handle 100 concurrent users with 8K context. Size the GPU cluster."*
3. *"What optimizations can you apply to serve 3x more requests on the same hardware?"*
