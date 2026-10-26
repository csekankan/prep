# Module 17 — Compare Inference Engines

> **6 lessons**
> vLLM, SGLang, TensorRT-LLM, llama.cpp — when to use which.

---

## 17.01 — Engine Comparison Matrix

| Feature | vLLM | SGLang | TensorRT-LLM | llama.cpp |
|---------|------|--------|-------------|-----------|
| **Language** | Python | Python | C++/Python | C++ |
| **KV Management** | PagedAttention | RadixAttention | Paged | Contiguous |
| **Batching** | Continuous | Continuous | In-flight | Limited |
| **Prefix Caching** | Hash-based | Radix tree | Manual | N/A |
| **Quantization** | AWQ, GPTQ, FP8 | AWQ, GPTQ, FP8 | INT4/8, FP8, all | GGUF (Q2-Q8) |
| **Multi-GPU** | TP, PP | TP | TP, PP | Limited TP |
| **Structured Output** | Outlines | Native FSM | Limited | Grammar |
| **Model Support** | Wide | Wide | NVIDIA only | GGUF only |
| **Ease of Use** | ★★★★★ | ★★★★☆ | ★★☆☆☆ | ★★★★★ |
| **Performance** | ★★★★☆ | ★★★★★ | ★★★★★ | ★★★☆☆ |
| **Best For** | General serving | High-perf serving | Max NVIDIA perf | CPU/edge |

---

## 17.02 — vLLM vs SGLang Architecture

```mermaid
graph TD
    subgraph "vLLM Architecture"
        V1["AsyncLLMEngine"]
        V2["Scheduler<br/>(FCFS, preemption)"]
        V3["BlockManager<br/>(PagedAttention)"]
        V4["ModelRunner<br/>(FlashAttention/FlashInfer)"]
        V1 --> V2 --> V3 --> V4
    end

    subgraph "SGLang Architecture"
        S1["Router + RadixCache"]
        S2["Scheduler<br/>(overlap prefill/decode)"]
        S3["RadixAttention<br/>(tree-based prefix cache)"]
        S4["ModelRunner<br/>(FlashInfer backend)"]
        S1 --> S2 --> S3 --> S4
    end
```

### Key Differences

- **SGLang's RadixAttention** manages prefix cache as a radix tree — better for complex prefix patterns (multi-turn, branching)
- **SGLang's constrained decoding** is native and fast (FSM-based)
- **vLLM has broader community** and more model support
- **SGLang typically wins** on throughput for high-concurrency workloads

---

## 17.03-17.04 — TensorRT-LLM & llama.cpp

### TensorRT-LLM

```bash
# Maximum performance on NVIDIA GPUs, but harder to set up
# Converts model to optimized TensorRT engine
trtllm-build --model_dir ./model --output_dir ./engine \
    --gemm_plugin auto --gpt_attention_plugin float16
```

### llama.cpp

```bash
# Run anywhere: CPU, Apple Silicon, small NVIDIA GPUs
# Best for: local development, edge devices, CPU inference
./llama-server -m model.gguf -c 4096 -ngl 99 --host 0.0.0.0 --port 8080
```

---

## 17.05 — Decision Flowchart

```mermaid
graph TD
    Start["Choose an Engine"] --> GPU{"NVIDIA GPU?"}
    GPU -->|No| LLAMA["llama.cpp<br/>(CPU, Apple, AMD)"]
    GPU -->|Yes| Perf{"Max performance<br/>needed?"}
    Perf -->|Yes, NVIDIA only OK| TRT["TensorRT-LLM"]
    Perf -->|Good perf + flexibility| Use{"Structured output<br/>or complex prefix?"}
    Use -->|Yes| SGL["SGLang"]
    Use -->|No, general purpose| VLLM["vLLM"]
```

> **🏢 FAANG Deep Dive:** Most companies don't pick just one engine. A typical setup:
> - **vLLM or SGLang** for general chat/API workloads (flexibility)
> - **TensorRT-LLM** for high-volume batch processing (max throughput)
> - **llama.cpp** for development, testing, and edge deployment

---

**Next Module:** [18 — Multi-GPU & Distributed Parallelism](../space-07-multi-gpu-distributed/18-multi-gpu-parallelism.md) →
