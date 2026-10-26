# Module 10 — Probability

## Quantifying Uncertainty — The Soul of ML

> **Why Probability Matters in ML:** ML models don't output truth — they output probabilities. Classification is probability. Generative AI is probability. Bayesian inference is probability. Understanding probability isn't optional — it's the entire point.

```
 MODULE 10 ROADMAP
 ═══════════════════════════════════════════════════
 10.01 Probability Rules & Bayesian Updating
 10.02 Continuous Random Variables
 10.03 Transforming Random Variables
 10.04 Moments, Means & Variability
 10.05 Discrete Probability Distributions
 10.06 Continuous Probability Distributions
 ═══════════════════════════════════════════════════
```

---

## 10.01 — Probability Rules and Bayesian Updating (3 Lessons)

### Lesson 1: Probability Basics

💡 **Key Intuition:** Probability measures how likely something is. It's a number between 0 (impossible) and 1 (certain).

**Three interpretations:**

| View | Meaning | Example |
|------|---------|---------|
| **Frequentist** | Long-run frequency | "60% of emails are spam" |
| **Bayesian** | Degree of belief | "I'm 60% sure this is spam" |
| **Axiomatic** | Mathematical framework | P satisfies the axioms below |

**Kolmogorov's Axioms:**
```
1. P(A) ≥ 0                    (non-negative)
2. P(Ω) = 1                    (total probability = 1)
3. P(A ∪ B) = P(A) + P(B)      if A ∩ B = ∅ (mutually exclusive)
```

```python
import numpy as np

# Simulating probability with random experiments
np.random.seed(42)
n_trials = 1000000

# Roll a fair die
rolls = np.random.randint(1, 7, n_trials)

# P(rolling a 6) ≈ 1/6
p_six = np.mean(rolls == 6)
print(f"P(roll=6) = {p_six:.4f} (theory: {1/6:.4f})")

# P(roll > 4) = P(5) + P(6) = 2/6
p_gt4 = np.mean(rolls > 4)
print(f"P(roll>4) = {p_gt4:.4f} (theory: {2/6:.4f})")
```

### Lesson 2: Conditional Probability and Independence

**Conditional Probability:** P(A|B) = "probability of A given B happened"

```
P(A|B) = P(A ∩ B) / P(B)
```

📊 **Visual:**
```
    ┌──────────────────────┐
    │       Ω              │
    │   ┌─────────┐        │
    │   │    B    │        │   P(A|B) = (A∩B area) / (B area)
    │   │  ┌──┐  │        │
    │   │  │A∩B│  │        │   = "zoom into B, what fraction is A?"
    │   │  └──┘  │        │
    │   └─────────┘        │
    └──────────────────────┘
```

**Independence:** A and B are independent if knowing B doesn't change P(A):

```
P(A|B) = P(A)  ⟺  P(A ∩ B) = P(A) × P(B)
```

```python
# Conditional probability example
# Medical test: P(Disease) = 0.01, P(Positive|Disease) = 0.95, P(Positive|No Disease) = 0.05
p_disease = 0.01
p_pos_given_disease = 0.95    # Sensitivity (true positive rate)
p_pos_given_no_disease = 0.05  # False positive rate

# Simulate
n = 1000000
has_disease = np.random.random(n) < p_disease
test_positive = np.where(
    has_disease,
    np.random.random(n) < p_pos_given_disease,
    np.random.random(n) < p_pos_given_no_disease
)

# P(Disease | Positive) — THE key question!
p_disease_given_pos = np.mean(has_disease[test_positive]) 
print(f"P(Disease|Positive) = {p_disease_given_pos:.3f}")
# Surprisingly low! (~16%) despite 95% test accuracy
```

### Lesson 3: Bayes' Theorem ⭐

```
                P(B|A) × P(A)
P(A|B) = ─────────────────────
                  P(B)

       posterior    likelihood × prior
       ────────── = ──────────────────
                        evidence
```

💡 **Plain English:** To update your belief about A after seeing B, multiply your prior belief by how well B matches A, then normalize.

⚡ **ML Connection:** Bayes' theorem is the foundation of:
- Naive Bayes classifiers
- Bayesian neural networks
- Bayesian optimization (hyperparameter tuning)
- Posterior inference in generative models

```python
def bayes_theorem(prior, likelihood, evidence):
    """P(A|B) = P(B|A) × P(A) / P(B)"""
    return likelihood * prior / evidence

# Medical test example with Bayes
p_disease = 0.01                    # Prior: 1% have the disease
p_pos_given_disease = 0.95          # Likelihood
p_pos_given_healthy = 0.05          # False positive rate

# Evidence: P(Positive) = P(Pos|D)×P(D) + P(Pos|¬D)×P(¬D)
p_positive = p_pos_given_disease * p_disease + p_pos_given_healthy * (1 - p_disease)

p_disease_given_pos = bayes_theorem(p_disease, p_pos_given_disease, p_positive)
print(f"P(Disease|Positive) = {p_disease_given_pos:.4f}")  # ~0.161

# Bayesian updating: if we test AGAIN and it's positive
p_disease_updated = bayes_theorem(
    p_disease_given_pos,  # New prior = old posterior
    p_pos_given_disease,  # Same likelihood
    p_pos_given_disease * p_disease_given_pos + p_pos_given_healthy * (1 - p_disease_given_pos)
)
print(f"After 2nd positive test: P(Disease) = {p_disease_updated:.4f}")  # ~0.785

# NAIVE BAYES CLASSIFIER
def naive_bayes_classify(features, class_priors, feature_likelihoods):
    """
    Classify using Naive Bayes assumption: features are independent.
    P(class|features) ∝ P(class) × ∏P(feature_i|class)
    """
    scores = {}
    for cls in class_priors:
        log_prob = np.log(class_priors[cls])
        for i, f in enumerate(features):
            log_prob += np.log(feature_likelihoods[cls][i][f])
        scores[cls] = log_prob
    return max(scores, key=scores.get)

# Spam classifier
class_priors = {"spam": 0.3, "ham": 0.7}
feature_likelihoods = {
    "spam": [{"free": 0.8, "meeting": 0.1, "hello": 0.1},    # Word 1
             {"click": 0.7, "please": 0.2, "dear": 0.1}],    # Word 2
    "ham":  [{"free": 0.1, "meeting": 0.5, "hello": 0.4},
             {"click": 0.05, "please": 0.45, "dear": 0.5}]
}

email = ["free", "click"]
result = naive_bayes_classify(email, class_priors, feature_likelihoods)
print(f"\nEmail with words {email} → classified as: {result}")
```

---

## 10.02 — Continuous Random Variables (6 Lessons)

### Lesson 1: PDF and CDF

**PDF (Probability Density Function):** f(x) — the "shape" of the distribution.

```
Important: f(x) is NOT a probability! It's a density.
P(a ≤ X ≤ b) = ∫ₐᵇ f(x)dx    ← area under the curve IS probability
```

**CDF (Cumulative Distribution Function):** F(x) = P(X ≤ x) — probability up to x.

```
CDF properties:
  F(-∞) = 0        (starts at 0)
  F(+∞) = 1        (ends at 1)
  F is non-decreasing
  f(x) = F'(x)     (PDF is derivative of CDF)
```

📊 **PDF vs CDF:**
```
PDF f(x):                       CDF F(x):
    ╱╲                          ──────── 1.0
   ╱  ╲                        ╱
  ╱    ╲                      ╱
 ╱      ╲                   ╱
╱________╲___              ╱___________ 0.0
              x                        x

Area under curve = 1        S-shaped, monotonically increasing
```

```python
import numpy as np
from scipy import stats

# Normal distribution
mu, sigma = 0, 1
x = np.linspace(-4, 4, 1000)

normal = stats.norm(mu, sigma)

pdf = normal.pdf(x)
cdf = normal.cdf(x)

# Key probabilities
print("Normal Distribution N(0,1):")
print(f"  P(X ≤ 0)     = {normal.cdf(0):.4f}")      # 0.5
print(f"  P(-1 ≤ X ≤ 1) = {normal.cdf(1) - normal.cdf(-1):.4f}")  # 0.6827
print(f"  P(-2 ≤ X ≤ 2) = {normal.cdf(2) - normal.cdf(-2):.4f}")  # 0.9545
print(f"  P(-3 ≤ X ≤ 3) = {normal.cdf(3) - normal.cdf(-3):.4f}")  # 0.9973
```

### Lesson 3-6: Working with PDFs and CDFs in Practice

```python
import numpy as np
from scipy import stats

# EXAMPLE: Using the CDF to answer probability questions
# "What fraction of adults are taller than 180cm?"
# Height ~ N(170, 8²)  (mean 170cm, std 8cm)
height_dist = stats.norm(170, 8)

p_above_180 = 1 - height_dist.cdf(180)
print(f"P(height > 180cm) = {p_above_180:.4f} = {p_above_180*100:.1f}%")

# "Between what heights do 90% of people fall?"
lower = height_dist.ppf(0.05)   # 5th percentile
upper = height_dist.ppf(0.95)   # 95th percentile
print(f"90% of people: {lower:.1f}cm to {upper:.1f}cm")

# EXAMPLE: Comparing distributions visually via quantiles
quantiles = [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]
normal = stats.norm(0, 1)
t_dist = stats.t(df=3)  # heavy-tailed

print(f"\n{'Quantile':>10} {'Normal':>10} {'t(df=3)':>10} {'Ratio':>10}")
print("-" * 44)
for q in quantiles:
    n_val = normal.ppf(q)
    t_val = t_dist.ppf(q)
    ratio = abs(t_val / n_val) if n_val != 0 else float('inf')
    print(f"{q:>10.2f} {n_val:>10.3f} {t_val:>10.3f} {ratio:>10.2f}")
# Notice: t-distribution has MUCH heavier tails (larger extreme quantiles)
```

---

## 10.03 — Transforming Random Variables (5 Lessons)

### Key Concept: Change of Variables

If Y = g(X) and X has PDF fₓ(x), what is the PDF of Y?

```
f_Y(y) = f_X(g⁻¹(y)) × |dg⁻¹/dy|
```

⚡ **ML Connection:** This is the foundation of **normalizing flows** — a family of generative models!

```python
import numpy as np

# Normalizing Flow: transform simple distribution → complex distribution

# Start with standard normal z ~ N(0,1)
z = np.random.randn(10000)

# Apply transformation: x = exp(z)  (makes it log-normal)
x = np.exp(z)

print(f"z (standard normal): mean={z.mean():.3f}, std={z.std():.3f}")
print(f"x (log-normal): mean={x.mean():.3f}, median={np.median(x):.3f}")
print(f"  Theoretical mean: {np.exp(0.5):.3f}")
```

### Common Transformations in ML

```python
import numpy as np

np.random.seed(42)
n = 100000

# 1. STANDARDIZATION: Z = (X - μ) / σ → always N(0,1) if X is normal
X = np.random.normal(50, 10, n)  # N(50, 100)
Z = (X - X.mean()) / X.std()
print(f"After standardization: mean={Z.mean():.4f}, std={Z.std():.4f}")

# 2. SIGMOID TRANSFORM: σ(x) = 1/(1+e^-x) maps ℝ → (0,1)
# This is why logistic regression outputs probabilities!
logits = np.random.normal(0, 2, n)
probabilities = 1 / (1 + np.exp(-logits))
print(f"Logits range: [{logits.min():.1f}, {logits.max():.1f}]")
print(f"After sigmoid: [{probabilities.min():.4f}, {probabilities.max():.4f}]")

# 3. SOFTMAX: maps ℝⁿ → probability simplex
# Used as the final layer of classifiers
def softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)

logits_batch = np.random.randn(5, 3)  # 5 samples, 3 classes
probs_batch = softmax(logits_batch)
print(f"\nSoftmax outputs (each row sums to 1):")
for i in range(3):
    print(f"  Sample {i}: {np.round(probs_batch[i], 3)} → sum = {probs_batch[i].sum():.4f}")

# 4. BOX-COX TRANSFORM: makes skewed data more normal
from scipy import stats
skewed_data = np.random.exponential(2, n)
transformed, lam = stats.boxcox(skewed_data)
print(f"\nBox-Cox transform (λ={lam:.3f}):")
print(f"  Before: skewness = {stats.skew(skewed_data):.3f}")
print(f"  After:  skewness = {stats.skew(transformed):.3f}")
```

---

## 10.04 — Moments, Means and Variability (10 Lessons)

### Lesson 1: Expected Value (Mean)

```
Discrete:   E[X] = Σ xᵢ × P(X = xᵢ)
Continuous: E[X] = ∫ x × f(x) dx
```

💡 **Key Intuition:** The expected value is the "center of mass" of the distribution.

### Lesson 2: Variance and Standard Deviation

```
Var(X) = E[(X - μ)²] = E[X²] - (E[X])²
σ = √Var(X)
```

💡 **Key Intuition:** Variance measures spread — how far values typically deviate from the mean.

### Lesson 3: Key Properties

```
E[aX + b] = aE[X] + b              (linearity of expectation)
Var(aX + b) = a²Var(X)             (variance scales quadratically)
E[X + Y] = E[X] + E[Y]            (ALWAYS — even if dependent!)
Var(X + Y) = Var(X) + Var(Y)       (only if independent!)
```

```python
import numpy as np

# Verify properties via simulation
np.random.seed(42)
n = 1000000

X = np.random.randn(n) * 2 + 3     # N(3, 4)
Y = np.random.randn(n) * 1 + 1     # N(1, 1)

print("Verification of moment properties:")
print(f"  E[X] = {X.mean():.3f} (theory: 3)")
print(f"  Var(X) = {X.var():.3f} (theory: 4)")
print(f"  E[2X+5] = {(2*X+5).mean():.3f} (theory: {2*3+5})")
print(f"  Var(2X+5) = {(2*X+5).var():.3f} (theory: {4*4})")
print(f"  E[X+Y] = {(X+Y).mean():.3f} (theory: {3+1})")
print(f"  Var(X+Y) = {(X+Y).var():.3f} (theory: {4+1}) [independent]")
```

### Lessons 4-10: Higher Moments, Skewness, Kurtosis

| Moment | Formula | What It Measures |
|--------|---------|-----------------|
| Mean (1st) | E[X] | Center |
| Variance (2nd) | E[(X-μ)²] | Spread |
| Skewness (3rd) | E[(X-μ)³]/σ³ | Asymmetry |
| Kurtosis (4th) | E[(X-μ)⁴]/σ⁴ - 3 | Tail heaviness |

```python
from scipy import stats
import numpy as np

# Compare distributions by their moments
distributions = {
    "Normal":     np.random.randn(100000),
    "Exponential": np.random.exponential(1, 100000),
    "Uniform":    np.random.uniform(0, 1, 100000),
    "Student-t":  np.random.standard_t(3, 100000),
}

print(f"{'Distribution':>15} {'Mean':>8} {'Var':>8} {'Skew':>8} {'Kurt':>8}")
print("-" * 52)
for name, data in distributions.items():
    print(f"{name:>15} {data.mean():>8.3f} {data.var():>8.3f} "
          f"{stats.skew(data):>8.3f} {stats.kurtosis(data):>8.3f}")
```

---

## 10.05 — Discrete Probability Distributions (10 Lessons)

### The Big Five Discrete Distributions

```python
import numpy as np
from scipy import stats

# 1. BERNOULLI: single coin flip
# P(X=1) = p, P(X=0) = 1-p
p = 0.7
bernoulli = stats.bernoulli(p)
print(f"Bernoulli(p={p}): mean={bernoulli.mean():.1f}, var={bernoulli.var():.2f}")
# ML: Binary classification output

# 2. BINOMIAL: number of successes in n trials
# X ~ Bin(n, p)
n, p = 10, 0.3
binomial = stats.binom(n, p)
print(f"Binomial(n={n}, p={p}): mean={binomial.mean():.1f}, var={binomial.var():.2f}")
# ML: Number of correct predictions in a batch

# 3. MULTINOMIAL: generalization to k categories
# Used in: multi-class classification (softmax output)
probs = [0.2, 0.3, 0.5]  # 3 classes
samples = np.random.multinomial(100, probs, size=5)
print(f"Multinomial(n=100, p={probs}):")
for s in samples[:3]:
    print(f"  {s}")

# 4. POISSON: count of rare events
# X ~ Poisson(λ)
lam = 5
poisson = stats.poisson(lam)
print(f"Poisson(λ={lam}): mean={poisson.mean():.1f}, var={poisson.var():.2f}")
# ML: Modeling count data (page views, clicks, arrivals)

# 5. GEOMETRIC: trials until first success
# X ~ Geom(p)
p = 0.3
geometric = stats.geom(p)
print(f"Geometric(p={p}): mean={geometric.mean():.2f}, var={geometric.var():.2f}")
# ML: "How many attempts until we find a relevant document?"
```

### Key: Softmax as Categorical Distribution

```python
def softmax(logits):
    """Convert raw scores to probabilities (categorical distribution)."""
    e = np.exp(logits - logits.max())
    return e / e.sum()

# Classifier output
logits = np.array([2.0, 1.0, 0.5])
probs = softmax(logits)
classes = ["cat", "dog", "bird"]

print("Classification probabilities:")
for cls, p in zip(classes, probs):
    print(f"  {cls}: {p:.3f}")

# Cross-entropy loss = -log(P(correct class))
true_class = 0  # cat
loss = -np.log(probs[true_class])
print(f"\nCross-entropy loss: {loss:.4f}")
```

---

## 10.06 — Continuous Probability Distributions (7 Lessons)

### The Essential Continuous Distributions

```python
import numpy as np
from scipy import stats

# 1. UNIFORM: equal probability everywhere
# X ~ U(a, b)
uniform = stats.uniform(0, 1)
print(f"Uniform(0,1): mean={uniform.mean():.2f}, var={uniform.var():.4f}")
# ML: Random initialization, random search

# 2. NORMAL (GAUSSIAN): the bell curve ← MOST IMPORTANT
# X ~ N(μ, σ²)
normal = stats.norm(0, 1)
print(f"Normal(0,1): mean={normal.mean():.2f}, var={normal.var():.2f}")
# ML: Weight initialization, noise modeling, batch norm

# 3. EXPONENTIAL: time between events
# X ~ Exp(λ)
exponential = stats.expon(scale=1/2)  # λ=2
print(f"Exponential(λ=2): mean={exponential.mean():.2f}")
# ML: Modeling waiting times, survival analysis

# 4. BETA: distribution on [0, 1]
# X ~ Beta(α, β)
beta = stats.beta(2, 5)
print(f"Beta(2,5): mean={beta.mean():.3f}, var={beta.var():.4f}")
# ML: Bayesian prior for probabilities, Thompson sampling

# 5. GAMMA: generalization of exponential
# X ~ Gamma(α, β)
gamma = stats.gamma(2, scale=1)
print(f"Gamma(2,1): mean={gamma.mean():.2f}")
# ML: Bayesian priors, modeling positive values
```

### The Normal Distribution — Why It Rules ML ⭐

```
            ┌──────── 68.3% ────────┐
       ┌────┤                        ├────┐
       │    │   ┌────── 95.4% ─────┐│    │
       │    │   │                   ││    │
     ──┴────┴───┴─┬───┬───┬───┬───┬┴┴────┴──
     -3σ  -2σ  -σ │ μ │  σ  2σ  3σ
                   └───┘
```

**Central Limit Theorem (CLT):** No matter the original distribution, the average of many samples approaches a normal distribution!

```python
import numpy as np

# CLT in action: average of ANYTHING becomes normal
np.random.seed(42)

# Start with very non-normal distributions
distributions = {
    "Uniform": lambda n: np.random.uniform(0, 1, n),
    "Exponential": lambda n: np.random.exponential(1, n),
    "Bernoulli": lambda n: np.random.binomial(1, 0.3, n),
}

n_averages = 10000
sample_sizes = [1, 5, 30]

print("Central Limit Theorem Demonstration:")
print(f"{'Distribution':>15} {'n':>5} {'Mean of avgs':>15} {'Std of avgs':>15}")
print("-" * 55)

for name, sampler in distributions.items():
    for n in sample_sizes:
        averages = [sampler(n).mean() for _ in range(n_averages)]
        print(f"{name:>15} {n:>5} {np.mean(averages):>15.4f} {np.std(averages):>15.4f}")
    print()
```

---

## 🔥 FAANG Deep Dive — Probability

### Interview Problem 1: Google — "Random Variable Simulation"

```python
def simulate_birthday_problem(n_people, n_simulations=100000):
    """
    What's the probability that at least 2 people share a birthday?
    Famous result: for 23 people, P > 50%!
    """
    count = 0
    for _ in range(n_simulations):
        birthdays = np.random.randint(0, 365, n_people)
        if len(set(birthdays)) < n_people:  # Duplicate found
            count += 1
    return count / n_simulations

for n in [10, 20, 23, 30, 50, 70]:
    p = simulate_birthday_problem(n)
    print(f"  {n:>2} people: P(shared birthday) = {p:.3f}")
```

### Interview Problem 2: Meta — "A/B Testing"

```python
import numpy as np
from scipy import stats

def ab_test(control, treatment, alpha=0.05):
    """
    Perform an A/B test using a two-proportion z-test.
    Returns whether the difference is statistically significant.
    """
    n_c, conv_c = len(control), sum(control)
    n_t, conv_t = len(treatment), sum(treatment)
    
    p_c = conv_c / n_c    # Control conversion rate
    p_t = conv_t / n_t    # Treatment conversion rate
    
    # Pooled proportion under H0
    p_pool = (conv_c + conv_t) / (n_c + n_t)
    
    # Standard error
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n_c + 1/n_t))
    
    # Z-statistic
    z = (p_t - p_c) / se
    
    # P-value (two-tailed)
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    return {
        "control_rate": p_c,
        "treatment_rate": p_t,
        "lift": (p_t - p_c) / p_c * 100,
        "z_statistic": z,
        "p_value": p_value,
        "significant": p_value < alpha
    }

# Simulate A/B test data
np.random.seed(42)
control   = np.random.binomial(1, 0.10, 5000)  # 10% conversion
treatment = np.random.binomial(1, 0.12, 5000)  # 12% conversion

result = ab_test(control, treatment)
for key, val in result.items():
    if isinstance(val, float):
        print(f"  {key}: {val:.4f}")
    else:
        print(f"  {key}: {val}")
```

---

## ✅ Module 10 Checkpoint

- [ ] Apply Bayes' Theorem to update beliefs
- [ ] Distinguish PDF, PMF, and CDF
- [ ] Calculate expected value and variance
- [ ] Name the key discrete distributions and their ML uses
- [ ] Name the key continuous distributions and their ML uses
- [ ] Explain the Central Limit Theorem and why it matters
- [ ] Implement a Naive Bayes classifier
- [ ] Perform an A/B test

**Next →** [Module 11: Joint RVs](../module-11-joint-rvs/README.md)
