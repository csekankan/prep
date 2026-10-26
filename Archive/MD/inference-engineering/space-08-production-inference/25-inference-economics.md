# Module 25 — Inference Economics & Capacity Planning

> **6 lessons**
> Calculate costs, compare GPUs, plan capacity, and build the cheapest system that meets your SLO.

---

## 25.01 — Cost per Request & Cost per Million Tokens

```python
def cost_per_million_tokens(gpu_cost_per_hour, throughput_tokens_per_sec):
    """Calculate the cost to generate 1 million tokens."""
    tokens_per_hour = throughput_tokens_per_sec * 3600
    cost_per_token = gpu_cost_per_hour / tokens_per_hour
    cost_per_million = cost_per_token * 1_000_000
    return cost_per_million

# Example configurations
configs = [
    {"name": "H100 + Llama 70B FP8", "gpu_cost": 3.50, "throughput": 2000},
    {"name": "A100 + Llama 70B INT4", "gpu_cost": 2.00, "throughput": 800},
    {"name": "H100 + Llama 8B BF16", "gpu_cost": 3.50, "throughput": 5000},
    {"name": "L40S + Llama 8B INT4", "gpu_cost": 1.20, "throughput": 3000},
]

print(f"{'Configuration':<30} {'$/hr':>6} {'tok/s':>8} {'$/1M tokens':>12}")
print("-" * 60)
for c in configs:
    cpm = cost_per_million_tokens(c['gpu_cost'], c['throughput'])
    print(f"{c['name']:<30} ${c['gpu_cost']:>5.2f} {c['throughput']:>7,} ${cpm:>10.2f}")
```

### Compare with API Providers (2026 pricing)

| Provider | Model | Input $/1M | Output $/1M |
|----------|-------|-----------|-------------|
| OpenAI | GPT-4o | $2.50 | $10.00 |
| Anthropic | Claude 3.5 Sonnet | $3.00 | $15.00 |
| Google | Gemini Pro | $1.25 | $5.00 |
| **Self-hosted** | **Llama 70B (H100)** | **$0.30** | **$0.50** |

**Self-hosting break-even:** ~10M tokens/day

---

## 25.02 — GPU Price/Performance Comparison

```python
gpus = [
    {"name": "A100 80GB",  "price_hr": 2.00, "mem_gb": 80,  "bw_tb": 2.0,  "flops_tf": 312},
    {"name": "H100 80GB",  "price_hr": 3.50, "mem_gb": 80,  "bw_tb": 3.35, "flops_tf": 990},
    {"name": "H200 141GB", "price_hr": 4.50, "mem_gb": 141, "bw_tb": 4.8,  "flops_tf": 990},
    {"name": "L40S 48GB",  "price_hr": 1.20, "mem_gb": 48,  "bw_tb": 0.86, "flops_tf": 362},
    {"name": "MI300X 192GB", "price_hr": 3.00, "mem_gb": 192, "bw_tb": 5.3, "flops_tf": 1300},
]

print(f"{'GPU':<16} {'$/hr':>6} {'Mem':>6} {'BW':>7} {'FLOPS':>7} {'BW/$':>7} {'Mem/$':>7}")
print("-" * 65)
for g in gpus:
    bw_per_dollar = g['bw_tb'] / g['price_hr']
    mem_per_dollar = g['mem_gb'] / g['price_hr']
    print(f"{g['name']:<16} ${g['price_hr']:>5.2f} {g['mem_gb']:>4}GB "
          f"{g['bw_tb']:>5.1f}TB/s {g['flops_tf']:>5}TF "
          f"{bw_per_dollar:>5.2f} {mem_per_dollar:>6.1f}")
```

---

## 25.03 — Capacity Planning

```python
def plan_capacity(
    peak_requests_per_sec: float,
    avg_input_tokens: int,
    avg_output_tokens: int,
    slo_ttft_ms: float,
    slo_tpot_ms: float,
    throughput_per_gpu: float,  # tokens/sec from benchmarks
    failure_headroom: float = 0.2,  # N+1 redundancy
    burst_factor: float = 1.5,  # Handle 1.5× peak
):
    """Calculate required GPUs for a production deployment."""

    total_tokens_per_sec = peak_requests_per_sec * (avg_input_tokens + avg_output_tokens)
    total_with_burst = total_tokens_per_sec * burst_factor

    gpus_for_throughput = total_with_burst / throughput_per_gpu
    gpus_with_headroom = gpus_for_throughput * (1 + failure_headroom)
    gpus_needed = int(gpus_with_headroom) + 1

    print(f"=== CAPACITY PLAN ===")
    print(f"Peak traffic:      {peak_requests_per_sec} req/s")
    print(f"Token throughput:   {total_tokens_per_sec:,.0f} tok/s")
    print(f"With burst (×{burst_factor}): {total_with_burst:,.0f} tok/s")
    print(f"Per-GPU throughput: {throughput_per_gpu:,.0f} tok/s")
    print(f"GPUs needed:        {gpus_needed} (incl. {failure_headroom:.0%} headroom)")

    return gpus_needed

# Example: medium-size chat application
gpus = plan_capacity(
    peak_requests_per_sec=100,
    avg_input_tokens=500,
    avg_output_tokens=300,
    slo_ttft_ms=500,
    slo_tpot_ms=50,
    throughput_per_gpu=2000,
)
```

---

## 25.04-25.05 — Build vs Buy Decision

```python
def build_vs_buy(
    monthly_tokens_millions: float,
    api_cost_per_million: float,  # $/1M tokens from API provider
    gpu_cost_per_month: float,    # $/month per GPU
    tokens_per_gpu_per_month: float,  # From benchmarks
    engineering_cost_per_month: float = 25000,  # 1 inference engineer
    num_gpus_needed: int = None,
):
    """Compare self-hosted vs API provider costs."""
    # API provider cost
    api_monthly = monthly_tokens_millions * api_cost_per_million

    # Self-hosted cost
    if num_gpus_needed is None:
        tokens_per_gpu = tokens_per_gpu_per_month
        num_gpus_needed = int(monthly_tokens_millions * 1e6 / tokens_per_gpu) + 1

    self_hosted_gpu = num_gpus_needed * gpu_cost_per_month
    self_hosted_total = self_hosted_gpu + engineering_cost_per_month

    print(f"Monthly tokens: {monthly_tokens_millions:.0f}M")
    print(f"API cost:       ${api_monthly:>10,.0f}/month")
    print(f"Self-hosted:    ${self_hosted_total:>10,.0f}/month ({num_gpus_needed} GPUs + eng)")
    print(f"Savings:        ${api_monthly - self_hosted_total:>10,.0f}/month")

    if self_hosted_total < api_monthly:
        roi_months = engineering_cost_per_month / (api_monthly - self_hosted_total)
        print(f"Break-even:     {roi_months:.1f} months")
        print(f"✅ Self-hosting is cheaper!")
    else:
        print(f"❌ API is cheaper at this scale")

build_vs_buy(
    monthly_tokens_millions=5000,
    api_cost_per_million=5.0,
    gpu_cost_per_month=2500,  # H100 reserved
    tokens_per_gpu_per_month=5e9,  # ~2000 tok/s sustained
)
```

> **🏢 FAANG Deep Dive:** OpenAI's pricing tiers reflect their inference cost structure: input tokens are 2-4× cheaper than output tokens because prefill is more efficient (compute-bound, high GPU utilization) while decode is expensive (memory-bound, low utilization). This is why every inference provider charges differently for input vs output.

---

**Next Module:** [26 — Specialized Inference Workloads](../space-09-specializations-engine-building/26-specialized-workloads.md) →
