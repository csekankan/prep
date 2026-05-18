# Agoda's Image Platform — Expert Guide

> **Who is this for?** ML engineers, data platform architects, and senior backend engineers who want to understand the technical depth — model architectures, graph algorithms, data modeling, partition strategies, and system design trade-offs.

---

## Table of Contents

1. [End-to-End Data Flow](#1-end-to-end-data-flow)
2. [Image Deduplication: Embedding → Graph → SCC](#2-image-deduplication)
3. [Quality Scoring: Architecture & Training](#3-quality-scoring)
4. [Super Resolution: RealESRGAN Pipeline](#4-super-resolution)
5. [Image Tagging: Vision Transformers](#5-image-tagging)
6. [Couchbase Data Model & Access Patterns](#6-couchbase-data-model)
7. [Config-Driven ML: Versioning & A/B Strategy](#7-config-driven-ml)
8. [Monorepo CI/CD: Dependency-Aware Testing](#8-monorepo-cicd)
9. [Bottleneck Analysis & Optimization](#9-bottleneck-analysis)
10. [System Design Trade-offs](#10-system-design-trade-offs)

---

## 1. End-to-End Data Flow

```
 INGESTION LAYER                    PROCESSING LAYER                     SERVING LAYER
 ─────────────────                  ─────────────────                     ─────────────

 ┌─────────────┐                    ┌──────────────────────────────────┐
 │ Supplier A  │──┐                 │        SPARK MONOREPO            │
 │ Supplier B  │──┤  ┌──────────┐  │                                  │
 │ Supplier C  │──┼─►│ Unified  │  │  ┌────────┐ ┌────────┐          │
 │ YCS (owned) │──┤  │ Metadata │─►│  │Dedup   │ │Quality │          │
 │ ...         │──┘  │ Table    │  │  │Pipeline│ │Pipeline│          │
 └─────────────┘     │ (daily   │  │  └───┬────┘ └───┬────┘          │
                     │  refresh)│  │      │          │               │
                     └──────────┘  │  ┌───┴────┐ ┌───┴────┐          │
                                   │  │Tag     │ │SuperRes│          │   ┌──────────┐
                     ┌──────────┐  │  │Pipeline│ │Pipeline│          │   │Couchbase │
                     │ VAST     │  │  └───┬────┘ └───┬────┘          │──►│          │
                     │ Bucket   │─►│      │          │               │   │ hotel_id │
                     │ (binaries│  │      ▼          ▼               │   │ → {doc}  │
                     │  at ML   │  │  ┌──────────────────────┐       │   └────┬─────┘
                     │  sizes)  │  │  │ Versioned Spark      │       │        │
                     └──────────┘  │  │ Managed Tables       │       │    20 min
                                   │  │ partition_by(date,   │       │   ingestion
                                   │  │              version)│       │        │
                                   │  └──────────────────────┘       │        ▼
                                   └──────────────────────────────────┘  ┌──────────┐
                                                                        │Content   │
                                                                        │API       │
                                                                        │(serves   │
                                                                        │ frontend)│
                                                                        └──────────┘
```

**Key data flow properties:**
- Metadata table is the **single source of truth** — all suppliers normalized into one schema
- Binaries stored at **scaled sizes** in VAST — ML jobs request only the resolution they need, saving bandwidth
- All enrichment outputs are **versioned** via `partition_columns('data_date', 'version')`
- Couchbase ingestion is a **batch upsert** keyed on `hotel_id`, replacing the 365-day MSSQL ETL

---

## 2. Image Deduplication

### The Math

Given a set of N images for a hotel, the deduplication pipeline:

**Step 1 — Embedding generation:**

Each image `I_i` is passed through DenseNet169 (pretrained on ImageNet, final classification layer removed) to produce a feature vector:

```
f(I_i) = DenseNet169(I_i) ∈ ℝ^1664
```

DenseNet169 was chosen over lighter models (ResNet50, MobileNet) for its **dense connectivity pattern** — each layer receives feature maps from all preceding layers, producing richer representations for similarity comparison.

**Step 2 — Pairwise cosine similarity:**

For every pair `(I_i, I_j)`:

```
                    f(I_i) · f(I_j)
sim(I_i, I_j) = ─────────────────────
                 ‖f(I_i)‖ × ‖f(I_j)‖
```

This produces a similarity matrix `S ∈ ℝ^(N×N)` where `S[i][j] ∈ [-1, 1]`.

**Step 3 — Graph construction:**

Build a directed graph `G = (V, E)` where:
- `V` = set of all images
- `E` = `{(I_i, I_j) | sim(I_i, I_j) ≥ threshold}`

The threshold is tuned empirically — too low catches false positives (different images that look vaguely similar), too high misses true duplicates with slight variations (cropping, compression artifacts).

**Step 4 — Strongly Connected Components (SCC):**

```
  ┌─────┐  0.98  ┌─────┐
  │ I_1 │───────►│ I_2 │
  │     │◄───────│     │
  └──┬──┘  0.97  └──┬──┘
     │               │
     │ 0.95    0.96  │
     │               │
     ▼               ▼
  ┌─────┐  0.99  ┌─────┐
  │ I_3 │───────►│ I_4 │
  │     │◄───────│     │
  └─────┘  0.98  └─────┘

  SCC: {I_1, I_2, I_3, I_4} → Dedup Group 42
```

**Why SCC over simple clustering (e.g., k-means)?**
- SCC naturally handles **transitive similarity**: if A≈B and B≈C, then {A,B,C} form a group even if A and C are slightly below threshold
- No need to predefine cluster count
- Runs efficiently via Tarjan's or Kosaraju's algorithm in `O(V + E)`

**Spark implementation consideration:**
- For a hotel with 1000 images, pairwise comparison = `1000 * 999 / 2 = ~500K` pairs
- Embarrassingly parallel: partition by hotel_id, compute within each partition
- Large hotels may need broadcast joins for the embedding vectors

---

## 3. Quality Scoring

### Model Architecture

```
┌─────────────────────────────────────────────────────┐
│                    INPUT IMAGE                       │
│                   (224 × 224 × 3)                    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              DenseNet169 BACKBONE                     │
│                                                      │
│  Dense Block 1 ──► Transition 1 ──► Dense Block 2    │
│  ──► Transition 2 ──► Dense Block 3 ──► Transition 3 │
│  ──► Dense Block 4 ──► Global Avg Pooling             │
│                                                      │
│  Output: 1664-dimensional feature vector             │
│  (pretrained on ImageNet, frozen or fine-tuned)      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│         CUSTOM HEAD (2 Dense Layers)                 │
│                                                      │
│  FC Layer 1: 1664 → 512 (ReLU + Dropout)             │
│  FC Layer 2: 512 → 1   (Linear activation)           │
│                                                      │
│  Output: Single scalar ∈ [-4, +4]                    │
└─────────────────────────────────────────────────────┘
```

### Training Data

- **Human-labeled dataset**: assessors rated images on multiple axes:
  - Clarity (sharpness, noise)
  - Composition (framing, rule of thirds)
  - Lighting (exposure, color balance)
  - Overall appeal (would this make you want to book?)
- Labels aggregated into a continuous score `[-4, +4]`
- Loss function: likely **MSE** or **smooth L1** for regression
- Training: transfer learning — DenseNet169 backbone pretrained, custom head trained on Agoda's labeled data

### Score Distribution Interpretation

```
  -4         -2          0          +2         +4
   │──────────│──────────│──────────│──────────│
   Reject     Poor       Average    Good       Featured
   (blurry,   (dark,     (adequate  (well-lit, (professional
    corrupt)   noisy)     quality)   sharp)     quality)
```

Images scoring below a threshold can be:
- Suppressed from display
- Sent to the super-resolution pipeline
- Deprioritized in ranking

---

## 4. Super Resolution

### RealESRGAN Pipeline

```
  ┌─────────────────┐
  │ Filter: images  │
  │ ≤ 800 × 600    │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────────────────────────────────┐
  │            RealESRGAN Model                  │
  │                                              │
  │  Generator: U-Net with Residual-in-Residual  │
  │             Dense Blocks (RRDB)              │
  │                                              │
  │  Discriminator: U-Net discriminator          │
  │                 (used only during training)  │
  │                                              │
  │  Enhancement: GFPGAN for face restoration    │
  │               (handles portraits/selfies)    │
  │                                              │
  │  Scale factor: typically 4×                  │
  └────────┬────────────────────────────────────┘
           │
           ▼
  ┌─────────────────┐
  │  Output:         │
  │  800×600 → 3200×2400 (at 4× scale)         │
  │  or capped at target resolution              │
  └─────────────────┘
```

**Why RealESRGAN over ESRGAN/SRGAN?**
- Trained with **second-order degradation model** — handles real-world artifacts (JPEG compression, blur, noise) better than synthetic-only training
- **GFPGAN integration** handles face enhancement — critical for property images showing staff, guests in common areas
- Better generalization to "in-the-wild" hotel images vs. lab-quality test sets

**Spark execution:**
- GPU-accelerated inference via Spark + GPU cluster
- Images partitioned and processed in parallel
- Output stored back to VAST bucket alongside originals (separate path/key)

---

## 5. Image Tagging

### Vision Transformer (ViT-Base-Patch16-224)

```
  Input Image (224 × 224)
         │
         ▼
  ┌──────────────────────────────────┐
  │  Split into 16×16 patches        │
  │  → 196 patches (14 × 14 grid)   │
  │  Each patch: 16 × 16 × 3 = 768  │
  └──────────┬───────────────────────┘
             │
             ▼
  ┌──────────────────────────────────┐
  │  Linear projection + position    │
  │  embeddings                      │
  │  [CLS] + 196 patch tokens       │
  │  → 197 tokens × 768 dims        │
  └──────────┬───────────────────────┘
             │
             ▼
  ┌──────────────────────────────────┐
  │  12 Transformer Encoder Layers   │
  │  (Multi-Head Self-Attention      │
  │   + MLP, 12 heads each)         │
  └──────────┬───────────────────────┘
             │
             ▼
  ┌──────────────────────────────────┐
  │  [CLS] token → Classification    │
  │  head → Category integer tag     │
  └──────────────────────────────────┘
```

**Why ViT over CNN-based classifiers (ResNet, EfficientNet)?**
- **Global receptive field from layer 1**: self-attention sees all patches simultaneously vs. CNNs building up gradually
- Better at capturing **scene-level semantics** ("this is a pool area" vs. "there is water and tiles")
- Pretrained on ImageNet-21k (14M images, 21K classes) → strong transfer to property image categories
- Patch-based approach handles varying compositions well (wide-angle room shots, close-up amenities)

**Category taxonomy** (example):
```
Tag ID │ Category
───────┼──────────────────
  1    │ Bedroom / Suite
  2    │ Bathroom
  3    │ Living area
  4    │ Swimming pool
  5    │ Restaurant / Dining
  6    │ Exterior / Building
  7    │ Lobby / Reception
  8    │ Gym / Fitness
  9    │ Spa / Wellness
 10    │ View / Scenery
 11    │ Meeting room
 12    │ Beach / Waterfront
 ...   │ ...
```

---

## 6. Couchbase Data Model

### Document Structure

```json
{
  "hotel_id": "H_12345",
  "last_updated": "2025-01-15T00:00:00Z",
  "images": [
    {
      "image_id": "IMG_001",
      "source": "supplier_A",
      "dimensions": { "width": 1920, "height": 1080 },
      "enrichment": {
        "version": "2.0",
        "quality_score": 3.2,
        "tags": [1, 4],
        "dedup_group_id": 42,
        "is_dedup_primary": true,
        "super_res_available": false,
        "blurhash": "LKO2?U%2Tw=w]~RBVZRi};RPxuwH"
      }
    },
    {
      "image_id": "IMG_002",
      "source": "YCS",
      "dimensions": { "width": 640, "height": 480 },
      "enrichment": {
        "version": "2.0",
        "quality_score": -1.5,
        "tags": [6],
        "dedup_group_id": 43,
        "is_dedup_primary": true,
        "super_res_available": true,
        "super_res_path": "vast://enhanced/H_12345/IMG_002_4x.jpg",
        "blurhash": "L6PZfSi_.AyE_3t7t7R**0o#DgR4"
      }
    }
  ]
}
```

### Access Patterns

```
                    ┌──────────────────────────────────┐
                    │           COUCHBASE               │
                    │                                    │
  Content API ──►   │  Bucket: "image_features"          │
  GET hotel_id      │                                    │
       │            │  Key: "H_12345"                    │
       │            │  Value: { full JSON doc above }    │
       │            │                                    │
       └──────────► │  Index: primary on hotel_id        │
                    │  (key-value lookup, O(1))          │
                    │                                    │
                    └──────────────────────────────────┘
```

**Why this document model works:**
- **One read per hotel** — all image metadata in a single document
- Frontend typically loads one hotel at a time → perfect match
- No JOINs, no secondary queries
- Couchbase's **memory-first architecture** keeps hot documents in RAM
- Sub-millisecond reads for key-value gets

**Ingestion strategy:**
- Spark job writes enriched metadata to versioned Spark tables
- A downstream job reads the latest partition, transforms into Couchbase document schema, and performs **batch upserts**
- Full 450M image metadata ingested in ~20 minutes (bulk loader)

---

## 7. Config-Driven ML

### Configuration Schema

```yaml
pipeline:
  name: "image_quality_scoring"
  schedule: "daily"
  
model:
  name: "densenet169_quality"
  framework: "pytorch"
  model_path: "vast://models/quality/densenet169_v2.pth"
  version: "2.0"
  input_size: 224
  batch_size: 256
  device: "gpu"

preprocessing:
  resize: [224, 224]
  normalize:
    mean: [0.485, 0.456, 0.406]
    std: [0.229, 0.224, 0.225]

output:
  table: "image_features.quality_scores"
  partition_columns: ["data_date", "version"]
  mode: "overwrite_partition"

resources:
  executors: 50
  executor_memory: "16g"
  executor_gpus: 1
```

### Versioned Partition Strategy

```
image_features.quality_scores/
├── data_date=2025-01-14/
│   ├── version=1.0/          ← Old model (ResNet50-based)
│   │   └── part-00000.parquet
│   └── version=2.0/          ← Current model (DenseNet169)
│       └── part-00000.parquet
├── data_date=2025-01-15/
│   ├── version=2.0/          ← Current model
│   │   └── part-00000.parquet
│   └── version=3.0/          ← New model (EfficientNet, A/B test)
│       └── part-00000.parquet
```

**A/B testing flow:**
1. Deploy new model config with `version: "3.0"`
2. Run pipeline — writes to new version partition alongside existing
3. Couchbase ingestion job can read **either** version or **both**
4. Content API serves version based on experiment assignment
5. Measure engagement metrics per version
6. Promote winner, deprecate loser

### Model Loading Abstraction

```python
def load_model(config):
    """Lightweight function — the ONLY code change needed for new frameworks."""
    if config["framework"] == "pytorch":
        model = torch.load(config["model_path"])
    elif config["framework"] == "tensorflow":
        model = tf.saved_model.load(config["model_path"])
    elif config["framework"] == "onnx":
        model = ort.InferenceSession(config["model_path"])
    model.eval()
    return model
```

The rest of the pipeline (data loading, preprocessing, partitioned writes, monitoring) remains **completely unchanged**.

---

## 8. Monorepo CI/CD

### Dependency Graph for Test Triggering

```
                    ┌──────────────┐
                    │   commons/   │
                    │ (global)     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            │            ▼
     ┌────────────┐        │     ┌────────────┐
     │  images/   │        │     │   text/     │
     │  commons/  │        │     │   commons/  │
     └──────┬─────┘        │     └──────┬──────┘
            │              │            │
    ┌───────┼───────┐      │     ┌──────┼──────┐
    ▼       ▼       ▼      │     ▼      ▼      ▼
 ┌─────┐┌─────┐┌──────┐   │  ┌─────┐┌─────┐┌─────┐
 │Dedup││Qual.││Tag   │   │  │Sent.││Meta ││...  │
 │     ││Score││      │   │  │     ││Ext. ││     │
 └─────┘└─────┘└──────┘   │  └─────┘└─────┘└─────┘
 ┌──────┐                  │
 │SRes. │                  │
 └──────┘                  │
```

**Trigger rules (GitLab CI):**

```yaml
# .gitlab-ci.yml (simplified)

.test_template:
  stage: test
  script:
    - python -m pytest ${TEST_PATH} -v

test_dedup:
  extends: .test_template
  variables:
    TEST_PATH: "images/deduplication/tests/"
  rules:
    - changes:
        - "commons/**/*"
        - "images/commons/**/*"
        - "images/deduplication/**/*"

test_quality:
  extends: .test_template
  variables:
    TEST_PATH: "images/quality_scoring/tests/"
  rules:
    - changes:
        - "commons/**/*"
        - "images/commons/**/*"
        - "images/quality_scoring/**/*"

test_text_sentiment:
  extends: .test_template
  variables:
    TEST_PATH: "text/sentiment/tests/"
  rules:
    - changes:
        - "commons/**/*"
        - "text/commons/**/*"
        - "text/sentiment/**/*"
```

### Localized Spark Testing

```python
def get_test_session():
    """Creates a local Spark session — no cluster required."""
    return (SparkSession.builder
            .master("local[2]")
            .appName("unit-tests")
            .config("spark.sql.warehouse.dir", "/tmp/test-warehouse")
            .config("spark.driver.memory", "2g")
            .config("spark.sql.shuffle.partitions", "2")
            .enableHiveSupport()
            .getOrCreate())

def create_test_table(spark, db_name, table_name, schema, data, 
                      partition_cols=None):
    """Creates a temp Hive table with test data for unit tests."""
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    df = spark.createDataFrame(data, schema)
    writer = df.write.mode("overwrite")
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    writer.saveAsTable(f"{db_name}.{table_name}")
```

**Benefits:**
- Tests run in **< 30 seconds** on a laptop (vs. minutes on a cluster)
- No infrastructure dependencies for development
- Deterministic — same data, same results every time
- Partition simulation catches partition-related bugs locally

---

## 9. Bottleneck Analysis

### Why MSSQL Replication Took 365 Days

```
  450M images × ~20 enrichment fields each
  = ~9 billion field values

  MSSQL bulk insert throughput: ~50K rows/sec (optimistic, with indexes)
  
  450M rows ÷ 50K rows/sec = 9,000 sec = 2.5 hours (raw insert)

  BUT: multiple tables with foreign keys, index rebuilds, 
       constraint checks, transaction log growth,
       network transfer from Hadoop cluster → MSSQL servers,
       ETL transformation overhead,
       incremental sync complexity (change detection),
       schema mismatch resolution per supplier

  Actual observed: ~365 days for full backfill
  (incremental daily updates were faster but always chasing a moving target)
```

### Why Couchbase Does It in 20 Minutes

```
  Document count: ~5M (one per hotel, not per image)
  Average document size: ~50KB (all images for one hotel)
  
  Couchbase bulk loader throughput: ~100K docs/sec
  
  5M docs ÷ 100K docs/sec = 50 sec (raw insert)
  
  With overhead (serialization, network, validation): ~20 minutes
  
  Key insight: restructuring from 450M rows (per-image) to 
  5M documents (per-hotel) reduced the unit count by 90×
```

### VAST Bucket Optimization

```
  OLD: Image binaries in HDFS
  ─────────────────────────────
  - 3× replication overhead
  - Block size mismatch (128MB blocks for small images)
  - High latency for random reads
  - Network hop: compute cluster → HDFS namenode → datanode
  
  NEW: Image binaries in VAST (object storage)
  ─────────────────────────────
  - Stored at ML-optimized sizes (not original resolution)
  - Bandwidth savings: 4000×3000 original → 224×224 for model input
  - Object storage optimized for parallel reads
  - Co-located with Spark GPU cluster for low latency
```

---

## 10. System Design Trade-offs

### Decisions Made and Why

| Decision | Alternative Considered | Why This Choice |
|---|---|---|
| DenseNet169 for embeddings | ResNet50, EfficientNet | Richer features from dense connections; acceptable compute cost at batch scale |
| Cosine similarity + SCC | k-means clustering, LSH | No need to predefine k; handles transitive similarity; LSH is approximate |
| Couchbase over MSSQL | Elasticsearch, MongoDB, Redis | High-throughput KV reads, document model fits access pattern, built-in clustering |
| Monorepo | Polyrepo per pipeline | Shared code reuse, atomic cross-pipeline changes, unified CI |
| Config-driven models | Plugin architecture, microservices | Simpler operational model; same Spark infra; no service mesh overhead |
| VAST for binaries | S3, HDFS, MinIO | Performance characteristics matched ML workload; co-location with GPU cluster |
| ViT for tagging | ResNet + FC, CLIP | Superior scene-level understanding; ImageNet-21k pretraining breadth |
| RealESRGAN for super-res | ESRGAN, SwinIR | Better real-world degradation handling; face enhancement built-in |
| Batch processing (daily) | Stream processing (real-time) | 450M images don't change frequently; daily refresh is sufficient; simpler ops |

### What's NOT Covered (Open Questions)

- **How are similarity thresholds tuned?** Likely a precision-recall trade-off curve evaluated on a labeled duplicate set
- **How are GPU resources allocated across pipelines?** Cluster scheduling (YARN, K8s) not discussed
- **How is the quality scoring model retrained?** Active learning loop from user engagement signals?
- **What's the cold-start strategy for new hotels?** How long until images are enriched after onboarding?
- **Couchbase document size limits?** Hotels with 10K+ images — is the document split?
- **Cache invalidation?** When enrichment updates, how quickly does Content API reflect changes?

---

*Previous: [02-intermediate.md](./02-intermediate.md) — Architecture and ML overview*
*Previous: [01-beginner.md](./01-beginner.md) — Simple explanation with analogies*
