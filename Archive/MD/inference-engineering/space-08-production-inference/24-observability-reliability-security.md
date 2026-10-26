# Module 24 — Observability, Reliability & Security

> **9 lessons**
> Monitor, protect, and recover your inference service.

---

## 24.01 — Inference Metrics Dashboard

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Key inference metrics
REQUEST_COUNT = Counter('inference_requests_total', 'Total requests', ['status'])
TTFT_HISTOGRAM = Histogram('inference_ttft_seconds', 'Time to first token',
                           buckets=[0.1, 0.2, 0.5, 1.0, 2.0, 5.0])
TPOT_HISTOGRAM = Histogram('inference_tpot_seconds', 'Time per output token',
                           buckets=[0.01, 0.02, 0.05, 0.1, 0.2])
GPU_MEMORY = Gauge('gpu_memory_used_bytes', 'GPU memory used', ['gpu_id'])
KV_UTILIZATION = Gauge('kv_cache_utilization', 'KV cache utilization percent')
QUEUE_DEPTH = Gauge('inference_queue_depth', 'Requests waiting in queue')
BATCH_SIZE = Histogram('inference_batch_size', 'Current batch size',
                       buckets=[1, 4, 8, 16, 32, 64, 128])
TOKENS_GENERATED = Counter('inference_tokens_generated_total', 'Total tokens generated')

# Grafana dashboard panels:
# 1. TTFT P50/P95/P99 (line chart)
# 2. TPOT P50/P95/P99 (line chart)
# 3. Throughput tokens/sec (line chart)
# 4. GPU memory utilization (gauge)
# 5. KV cache utilization (gauge)
# 6. Queue depth (line chart)
# 7. Error rate (line chart)
# 8. Request rate (line chart)
```

---

## 24.02 — GPU & System Metrics

```python
# Essential GPU metrics to monitor:
gpu_metrics = {
    "utilization_gpu":     "GPU compute utilization (%)",
    "utilization_memory":  "Memory controller utilization (%)",
    "memory_used":         "GPU memory used (MB)",
    "memory_total":        "GPU memory total (MB)",
    "temperature_gpu":     "GPU temperature (°C)",
    "power_draw":          "Current power draw (W)",
    "clocks_sm":           "SM clock speed (MHz)",
    "ecc_errors_corrected": "ECC errors (thermal/memory issues)",
}

# Alert thresholds:
alerts = {
    "gpu_temperature > 85°C":        "WARNING: Thermal throttling imminent",
    "memory_used > 95%":             "CRITICAL: OOM risk",
    "kv_utilization > 90%":          "WARNING: Preemption likely",
    "queue_depth > 50":              "WARNING: Requests piling up",
    "error_rate > 1%":               "CRITICAL: High error rate",
    "ttft_p95 > slo * 1.2":         "WARNING: SLO at risk",
    "ecc_errors > 0":               "WARNING: Hardware issue",
}
```

---

## 24.03 — Distributed Tracing

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

tracer = trace.get_tracer("inference-service")

async def handle_request(request):
    with tracer.start_as_current_span("inference_request") as span:
        span.set_attribute("input_tokens", len(request.prompt_tokens))
        span.set_attribute("max_output_tokens", request.max_tokens)

        with tracer.start_as_current_span("scheduling"):
            scheduled_batch = await scheduler.schedule(request)

        with tracer.start_as_current_span("prefill"):
            kv_cache = await model.prefill(request.prompt_tokens)
            span.set_attribute("prefill_time_ms", prefill_time)

        with tracer.start_as_current_span("decode"):
            tokens = await model.decode(kv_cache, request.max_tokens)
            span.set_attribute("tokens_generated", len(tokens))

        span.set_attribute("total_time_ms", total_time)
```

---

## 24.04-24.06 — Admission Control, Retries & Recovery

### Admission Control

```python
class AdmissionController:
    """Reject requests when the system is overloaded."""

    def __init__(self, max_queue_depth=100, max_kv_utilization=0.95):
        self.max_queue = max_queue_depth
        self.max_kv = max_kv_utilization

    def should_admit(self, request, current_queue, current_kv_util):
        if current_queue >= self.max_queue:
            return False, "Queue full (429)"
        if current_kv_util >= self.max_kv:
            return False, "KV cache full (503)"
        return True, "Admitted"
```

### OOM Recovery

```python
async def safe_generate(model, request):
    """Generate with OOM recovery."""
    try:
        return await model.generate(request)
    except torch.cuda.OutOfMemoryError:
        # 1. Cancel the largest running request
        largest = scheduler.get_largest_request()
        scheduler.abort(largest.id)

        # 2. Clear CUDA cache
        torch.cuda.empty_cache()

        # 3. Retry
        return await model.generate(request)
```

## 24.07 — Chaos Testing

```python
chaos_tests = [
    "Kill 1 of 4 workers during peak load",
    "Exhaust GPU memory (send max-length requests)",
    "Spike traffic 10× for 30 seconds",
    "Inject 100ms network latency",
    "Corrupt one GPU (nvidia-smi drain)",
    "Fill disk (model weight cache full)",
    "Send malformed requests at high rate",
]
# For each test: measure recovery time, data loss, SLO impact
```

## 24.08 — Security

```python
# API Security Checklist:
security = {
    "Authentication":     "API keys, JWT tokens, OAuth2",
    "Rate limiting":      "Per-user, per-API-key token budgets",
    "Input validation":   "Max prompt length, block prompt injection",
    "Output filtering":   "Safety classifiers, PII detection",
    "Tenant isolation":   "Separate GPU pools or strict fairness",
    "Network":            "TLS, VPC, no public GPU access",
    "Audit logging":      "Log all requests with user ID (not content)",
}
```

> **🏢 FAANG Deep Dive:** Google SREs monitor Gemini infrastructure with 1000+ metrics, automated anomaly detection, and PagerDuty integration. Their SLO: 99.9% of requests meet latency targets. A single SLO breach triggers automated investigation and potential rollback.

---

**Next Module:** [25 — Inference Economics & Capacity Planning](./25-inference-economics.md) →
