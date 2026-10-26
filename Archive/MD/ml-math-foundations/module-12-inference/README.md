# Module 12 — Inference

## From Data to Knowledge

> **Why Inference Matters in ML:** Every time you train a model, you're doing statistical inference. You're using a finite sample to learn something about the entire population. Understanding estimators, maximum likelihood, and confidence intervals tells you how much to trust your model's results.

```
 MODULE 12 ROADMAP
 ═══════════════════════════════════════
 12.01 Sampling Behavior & Estimators
 12.02 Likelihood-Based Estimation
 12.03 Interval Estimation
 ═══════════════════════════════════════
```

---

## 12.01 — Sampling Behavior and Estimators (9 Lessons)

### Lesson 1: Population vs Sample

```
POPULATION (θ):                    SAMPLE (θ̂):
All possible data                  What we actually have
├─────────────────────┤            ├────────┤
│ ? ? ? ? ? ? ? ? ? ? │            │ x₁ x₂ │
│ ? ? ? ? ? ? ? ? ? ? │            │ x₃ x₄ │
│ ? ? ? ? ? ? ? ? ? ? │            │ x₅    │
├─────────────────────┤            ├────────┤
Parameters: μ, σ, ...              Estimates: x̄, s, ...
(UNKNOWN, FIXED)                   (Computed, RANDOM)
```

💡 **Key Insight:** We never know the true population parameters. We can only estimate them from samples. The question is: *how good are our estimates?*

### Lesson 2: Estimators and Their Properties

An **estimator** θ̂ is a function of the data that estimates a population parameter θ.

**Desirable properties:**

| Property | Definition | Plain English |
|---------|-----------|---------------|
| **Unbiased** | E[θ̂] = θ | On average, hits the target |
| **Consistent** | θ̂ → θ as n → ∞ | Gets better with more data |
| **Efficient** | Minimum variance among unbiased | Tightest possible estimate |

```python
import numpy as np

# Demonstrate bias and consistency
np.random.seed(42)
true_mean = 5.0
true_var = 4.0  # σ² = 4, σ = 2

# Sample mean is unbiased for μ
# Sample variance (dividing by n) is BIASED
# Sample variance (dividing by n-1) is UNBIASED

sample_sizes = [5, 10, 50, 100, 1000, 10000]
n_experiments = 10000

print(f"{'n':>8} {'Mean of x̄':>12} {'Biased s²':>12} {'Unbiased s²':>12}")
print("-" * 48)

for n in sample_sizes:
    means = []
    vars_biased = []
    vars_unbiased = []
    
    for _ in range(n_experiments):
        sample = np.random.normal(true_mean, np.sqrt(true_var), n)
        means.append(sample.mean())
        vars_biased.append(sample.var())         # divides by n (biased!)
        vars_unbiased.append(sample.var(ddof=1)) # divides by n-1 (unbiased)
    
    print(f"{n:>8} {np.mean(means):>12.4f} {np.mean(vars_biased):>12.4f} {np.mean(vars_unbiased):>12.4f}")

print(f"\n{'True':>8} {true_mean:>12.4f} {true_var:>12.4f} {true_var:>12.4f}")
```

### Lesson 3: Sampling Distribution

The **sampling distribution** is the distribution of an estimator over all possible samples.

```
    Population
    ┌──────────┐
    │          │ ──── Sample 1 → x̄₁ = 4.8
    │          │ ──── Sample 2 → x̄₂ = 5.1
    │  μ = 5   │ ──── Sample 3 → x̄₃ = 4.9    → Distribution of x̄
    │          │ ──── Sample 4 → x̄₄ = 5.3       is approximately
    │          │ ──── Sample 5 → x̄₅ = 4.7       N(μ, σ²/n)
    └──────────┘       ...
```

⚡ **ML Connection:** This is why we run multiple training runs and report mean ± std!

### Lesson 4: The Standard Error

```
Standard Error of the Mean: SE(x̄) = σ / √n

This tells you:
  • How much x̄ varies between different samples
  • SE decreases as √n → need 4× data for 2× precision!
```

```python
# Standard error demonstration
import numpy as np

true_sigma = 2.0
print(f"{'n':>8} {'Theoretical SE':>15} {'Empirical SE':>15}")
print("-" * 40)

for n in [10, 100, 1000, 10000]:
    theoretical_se = true_sigma / np.sqrt(n)
    
    # Empirical: compute many sample means
    sample_means = [np.random.normal(5, true_sigma, n).mean() for _ in range(5000)]
    empirical_se = np.std(sample_means)
    
    print(f"{n:>8} {theoretical_se:>15.4f} {empirical_se:>15.4f}")
```

### Lessons 5-9: Law of Large Numbers and CLT in Practice

**Law of Large Numbers:** x̄ → μ as n → ∞ (the sample mean converges to the true mean)

**Central Limit Theorem:** x̄ is approximately N(μ, σ²/n) for large n, regardless of the population distribution.

```python
import numpy as np

# CLT for non-normal distributions
def demonstrate_clt(distribution_name, sampler, n_values=[1, 5, 30, 100]):
    """Show how sample means become normal as n increases."""
    n_experiments = 10000
    
    print(f"\n{distribution_name}:")
    for n in n_values:
        means = [sampler(n).mean() for _ in range(n_experiments)]
        from scipy.stats import normaltest
        _, p_value = normaltest(means)
        normal = "Yes" if p_value > 0.05 else "No"
        print(f"  n={n:>4}: skewness={np.mean(means):.3f}±{np.std(means):.3f}, "
              f"Normal? {normal} (p={p_value:.3f})")

demonstrate_clt("Exponential(λ=1)", lambda n: np.random.exponential(1, n))
demonstrate_clt("Bernoulli(p=0.3)", lambda n: np.random.binomial(1, 0.3, n))
```

---

## 12.02 — Likelihood-Based Estimation (7 Lessons)

### Lesson 1: The Likelihood Function

💡 **Key Intuition:** Given observed data, the **likelihood** tells you how plausible different parameter values are. It flips the question from "what data would these parameters produce?" to "what parameters best explain this data?"

```
Given: data D = {x₁, x₂, ..., xₙ}
Likelihood: L(θ) = P(D | θ) = ∏ P(xᵢ | θ)
Log-likelihood: ℓ(θ) = Σ log P(xᵢ | θ)    ← easier to work with
```

📊 **Probability vs Likelihood:**
```
PROBABILITY (fixed θ, varying data):    LIKELIHOOD (fixed data, varying θ):
"Given these parameters,                "Given this data,
 how likely is this data?"               how plausible are these parameters?"

P(data | θ=5) = ?                        L(θ) = P(data | θ) as a function of θ
```

### Lesson 2: Maximum Likelihood Estimation (MLE) ⭐

**The Big Idea:** Choose the parameter θ that makes the observed data MOST probable.

```
θ̂_MLE = argmax_θ L(θ) = argmax_θ ℓ(θ)
```

```python
import numpy as np
from scipy.optimize import minimize_scalar

# MLE for the mean of a normal distribution
def neg_log_likelihood_normal(mu, data, sigma=1):
    """Negative log-likelihood for N(μ, σ²)."""
    n = len(data)
    return 0.5 * n * np.log(2 * np.pi * sigma**2) + \
           0.5 * np.sum((data - mu)**2) / sigma**2

# Generate data
np.random.seed(42)
true_mu = 3.0
data = np.random.normal(true_mu, 1, 50)

# Find MLE
result = minimize_scalar(neg_log_likelihood_normal, args=(data,))
mle_mu = result.x

print(f"True μ: {true_mu}")
print(f"Sample mean: {data.mean():.4f}")
print(f"MLE μ: {mle_mu:.4f}")
print("(For normal distribution, MLE = sample mean!)")
```

### Lesson 3: MLE for Common Distributions

```python
import numpy as np

class MLEEstimator:
    """MLE for common distributions — what every ML engineer should know."""
    
    @staticmethod
    def normal(data):
        """MLE for Normal: μ̂ = x̄, σ̂² = Σ(xᵢ-x̄)²/n"""
        mu = data.mean()
        sigma2 = data.var(ddof=0)  # ddof=0 for MLE (biased)
        return mu, sigma2
    
    @staticmethod
    def bernoulli(data):
        """MLE for Bernoulli: p̂ = x̄"""
        return data.mean()
    
    @staticmethod
    def poisson(data):
        """MLE for Poisson: λ̂ = x̄"""
        return data.mean()
    
    @staticmethod
    def exponential(data):
        """MLE for Exponential: λ̂ = 1/x̄"""
        return 1 / data.mean()

# Test
np.random.seed(42)

# Normal
data_norm = np.random.normal(5, 2, 1000)
mu, sigma2 = MLEEstimator.normal(data_norm)
print(f"Normal MLE: μ̂={mu:.3f} (true: 5), σ̂²={sigma2:.3f} (true: 4)")

# Bernoulli
data_bern = np.random.binomial(1, 0.7, 1000)
p = MLEEstimator.bernoulli(data_bern)
print(f"Bernoulli MLE: p̂={p:.3f} (true: 0.7)")

# Poisson
data_pois = np.random.poisson(3.5, 1000)
lam = MLEEstimator.poisson(data_pois)
print(f"Poisson MLE: λ̂={lam:.3f} (true: 3.5)")
```

### Lesson 4: MLE and Cross-Entropy Loss ⭐

💡 **The Connection:** Minimizing cross-entropy loss IS doing MLE!

```
Cross-entropy loss: L = -Σ yᵢ log(ŷᵢ)

This is exactly the negative log-likelihood of a Bernoulli/Categorical distribution!
So training a classifier with cross-entropy = finding MLE of the model parameters.
```

```python
import numpy as np

def cross_entropy_is_mle():
    """Show that cross-entropy loss = negative log-likelihood."""
    
    # Binary classification
    y_true = np.array([1, 0, 1, 1, 0])
    y_pred = np.array([0.9, 0.1, 0.8, 0.7, 0.3])
    
    # Cross-entropy loss
    ce_loss = -np.mean(y_true * np.log(y_pred) + (1-y_true) * np.log(1-y_pred))
    
    # Negative log-likelihood of Bernoulli
    nll = -np.mean(np.log(np.where(y_true == 1, y_pred, 1 - y_pred)))
    
    print(f"Cross-entropy loss: {ce_loss:.6f}")
    print(f"Negative log-likelihood: {nll:.6f}")
    print(f"They are the same! {np.isclose(ce_loss, nll)}")

cross_entropy_is_mle()
```

### Lesson 5: MAP Estimation (Bayesian MLE)

**Maximum A Posteriori** adds a prior to MLE:

```
θ̂_MAP = argmax_θ P(θ|D) = argmax_θ [P(D|θ) × P(θ)]
                         = argmax_θ [ℓ(θ) + log P(θ)]
```

💡 **Key Insight:** MAP estimation = MLE + regularization!
- Gaussian prior P(θ) = N(0, σ²) → L2 regularization (Ridge)
- Laplace prior P(θ) = Laplace(0, b) → L1 regularization (Lasso)

```python
import numpy as np

def mle_vs_map(data, prior_mean=0, prior_var=1):
    """Compare MLE and MAP for normal mean estimation."""
    n = len(data)
    data_var = 1.0  # Known variance
    
    # MLE: just the sample mean
    mle = data.mean()
    
    # MAP with Gaussian prior N(prior_mean, prior_var)
    # Posterior mean = weighted average of prior and data
    precision_prior = 1 / prior_var
    precision_data = n / data_var
    
    map_estimate = (precision_prior * prior_mean + precision_data * data.mean()) / \
                   (precision_prior + precision_data)
    
    return mle, map_estimate

np.random.seed(42)

# With lots of data: MLE ≈ MAP
data_large = np.random.normal(3, 1, 1000)
mle_l, map_l = mle_vs_map(data_large, prior_mean=0, prior_var=1)
print(f"n=1000: MLE={mle_l:.4f}, MAP={map_l:.4f} (nearly identical)")

# With little data: MAP pulls toward prior
data_small = np.random.normal(3, 1, 3)
mle_s, map_s = mle_vs_map(data_small, prior_mean=0, prior_var=1)
print(f"n=3:    MLE={mle_s:.4f}, MAP={map_s:.4f} (MAP pulled toward prior=0)")
```

### Lessons 6-7: Fisher Information and Cramér-Rao Bound

The **Fisher Information** measures how much information data carries about a parameter:

```
I(θ) = -E[∂²ℓ/∂θ²]    (curvature of the log-likelihood)

Cramér-Rao Lower Bound:
  Var(θ̂) ≥ 1 / (n × I(θ))

This is the BEST any unbiased estimator can do!
```

```python
def fisher_information_normal(sigma):
    """Fisher information for mean of N(μ, σ²) is 1/σ²."""
    return 1 / sigma**2

# Example: precision of mean estimate
sigma = 2.0
I = fisher_information_normal(sigma)

for n in [10, 100, 1000]:
    cramer_rao_bound = 1 / (n * I)
    print(f"n={n:>5}: Minimum variance of μ̂ ≥ {cramer_rao_bound:.6f}, "
          f"SE ≥ {np.sqrt(cramer_rao_bound):.4f}")
```

---

## 12.03 — Interval Estimation (6 Lessons)

### Lesson 1: Confidence Intervals

💡 **Key Intuition:** A 95% confidence interval means: "If we repeated this experiment many times, 95% of the intervals we construct would contain the true parameter."

```
95% CI for the mean:
  x̄ ± z₀.₀₂₅ × (σ/√n)
  x̄ ± 1.96 × SE

  ├──────────────[─────x̄─────]──────────────┤
                  ↑               ↑
              x̄ - 1.96·SE    x̄ + 1.96·SE
```

```python
import numpy as np
from scipy import stats

def confidence_interval(data, confidence=0.95):
    """Compute confidence interval for the mean."""
    n = len(data)
    mean = data.mean()
    se = data.std(ddof=1) / np.sqrt(n)
    
    # Use t-distribution for small samples
    t_critical = stats.t.ppf((1 + confidence) / 2, n - 1)
    margin = t_critical * se
    
    return mean, mean - margin, mean + margin

# Demo
np.random.seed(42)
data = np.random.normal(100, 15, 50)  # IQ scores

mean, lower, upper = confidence_interval(data)
print(f"Sample mean: {mean:.2f}")
print(f"95% CI: ({lower:.2f}, {upper:.2f})")
print(f"True mean: 100")
print(f"Contains true mean? {lower <= 100 <= upper}")
```

### Lesson 2: CI for Model Performance

⚡ **ML Connection:** Always report model accuracy with confidence intervals!

```python
import numpy as np
from scipy import stats

def accuracy_confidence_interval(y_true, y_pred, confidence=0.95):
    """
    Confidence interval for classification accuracy.
    Uses the Wilson score interval (better than naive method for proportions).
    """
    n = len(y_true)
    p_hat = np.mean(y_true == y_pred)
    
    z = stats.norm.ppf((1 + confidence) / 2)
    
    # Wilson score interval
    denominator = 1 + z**2/n
    center = (p_hat + z**2/(2*n)) / denominator
    margin = z * np.sqrt((p_hat*(1-p_hat) + z**2/(4*n))/n) / denominator
    
    return p_hat, center - margin, center + margin

# Simulate model predictions
np.random.seed(42)
n_test = 200
y_true = np.random.binomial(1, 0.5, n_test)
y_pred = y_true.copy()
# Introduce 15% error rate
errors = np.random.choice(n_test, int(0.15 * n_test), replace=False)
y_pred[errors] = 1 - y_pred[errors]

acc, lower, upper = accuracy_confidence_interval(y_true, y_pred)
print(f"Accuracy: {acc:.3f}")
print(f"95% CI: ({lower:.3f}, {upper:.3f})")
print(f"Width: {upper - lower:.3f}")

# Compare with more test data
n_test_large = 10000
y_true_l = np.random.binomial(1, 0.5, n_test_large)
y_pred_l = y_true_l.copy()
errors_l = np.random.choice(n_test_large, int(0.15 * n_test_large), replace=False)
y_pred_l[errors_l] = 1 - y_pred_l[errors_l]

acc_l, lower_l, upper_l = accuracy_confidence_interval(y_true_l, y_pred_l)
print(f"\nWith 10K samples:")
print(f"Accuracy: {acc_l:.3f}")
print(f"95% CI: ({lower_l:.3f}, {upper_l:.3f})")
print(f"Width: {upper_l - lower_l:.3f} (much tighter!)")
```

### Lesson 3: Bootstrap Confidence Intervals ⭐

When you can't derive a formula, use the **bootstrap**:

```
1. Resample your data WITH replacement, same size
2. Compute your statistic on each resample
3. The middle 95% of your statistics = 95% CI
```

```python
import numpy as np

def bootstrap_ci(data, statistic_fn, confidence=0.95, n_bootstrap=10000):
    """
    Bootstrap confidence interval — works for ANY statistic!
    No assumptions about the distribution needed.
    """
    n = len(data)
    bootstrap_stats = []
    
    for _ in range(n_bootstrap):
        resample = data[np.random.randint(0, n, n)]
        bootstrap_stats.append(statistic_fn(resample))
    
    bootstrap_stats = np.sort(bootstrap_stats)
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, 100 * alpha/2)
    upper = np.percentile(bootstrap_stats, 100 * (1 - alpha/2))
    
    return statistic_fn(data), lower, upper

# Bootstrap CI for mean (should match t-interval)
np.random.seed(42)
data = np.random.normal(100, 15, 50)

mean, lower, upper = bootstrap_ci(data, np.mean)
print(f"Bootstrap CI for mean: {mean:.2f} ({lower:.2f}, {upper:.2f})")

# Bootstrap CI for MEDIAN (no closed-form formula exists!)
median, lower, upper = bootstrap_ci(data, np.median)
print(f"Bootstrap CI for median: {median:.2f} ({lower:.2f}, {upper:.2f})")

# Bootstrap CI for model performance metric (e.g., F1 score)
from sklearn.metrics import f1_score
y_true = np.random.binomial(1, 0.3, 200)
y_pred = np.random.binomial(1, 0.35, 200)

paired_data = np.column_stack([y_true, y_pred])
f1_stat = lambda d: f1_score(d[:, 0], d[:, 1], zero_division=0)
f1, lower, upper = bootstrap_ci(paired_data, f1_stat)
print(f"Bootstrap CI for F1: {f1:.3f} ({lower:.3f}, {upper:.3f})")
```

### Lesson 4: Hypothesis Testing Fundamentals

```
H₀: Null hypothesis (no effect, no difference)
H₁: Alternative hypothesis (there IS an effect)

Procedure:
1. Assume H₀ is true
2. Compute test statistic
3. Calculate p-value = P(data this extreme | H₀)
4. If p-value < α (significance level), reject H₀
```

```python
import numpy as np
from scipy import stats

def hypothesis_test_two_models(scores_A, scores_B, alpha=0.05):
    """
    Paired t-test: Is model A significantly better than model B?
    (Using paired test because both run on the same test set.)
    """
    differences = scores_A - scores_B
    t_stat, p_value = stats.ttest_rel(scores_A, scores_B)
    
    return {
        "mean_A": scores_A.mean(),
        "mean_B": scores_B.mean(),
        "mean_diff": differences.mean(),
        "t_statistic": t_stat,
        "p_value": p_value,
        "significant": p_value < alpha,
        "better_model": "A" if differences.mean() > 0 else "B"
    }

# Compare two models on 5-fold CV
np.random.seed(42)
model_A_scores = np.array([0.85, 0.87, 0.84, 0.86, 0.88])  # Accuracy per fold
model_B_scores = np.array([0.82, 0.84, 0.81, 0.83, 0.85])

result = hypothesis_test_two_models(model_A_scores, model_B_scores)
for k, v in result.items():
    if isinstance(v, float):
        print(f"  {k}: {v:.4f}")
    else:
        print(f"  {k}: {v}")
```

### Lessons 5-6: Multiple Testing and Practical Significance

```python
import numpy as np
from scipy import stats

def bonferroni_correction(p_values, alpha=0.05):
    """
    When running multiple tests, correct for multiple comparisons.
    Bonferroni: divide α by number of tests.
    """
    m = len(p_values)
    corrected_alpha = alpha / m
    
    print(f"Number of tests: {m}")
    print(f"Original α: {alpha}")
    print(f"Corrected α (Bonferroni): {corrected_alpha:.6f}")
    print()
    
    for i, p in enumerate(p_values):
        sig_original = p < alpha
        sig_corrected = p < corrected_alpha
        print(f"  Test {i+1}: p={p:.4f}  "
              f"Original: {'✓' if sig_original else '✗'}  "
              f"Corrected: {'✓' if sig_corrected else '✗'}")

# Example: testing 20 features for significance
np.random.seed(42)
p_values = np.random.uniform(0, 1, 20)
p_values[0] = 0.001  # One truly significant result
p_values[5] = 0.03   # Marginal

bonferroni_correction(p_values)
```

---

## 🔥 FAANG Deep Dive — Inference

### Interview Problem 1: Google — "Design an A/B Test"

```python
import numpy as np
from scipy import stats

def design_ab_test(baseline_rate, min_detectable_effect, alpha=0.05, power=0.80):
    """
    Calculate required sample size for an A/B test.
    
    baseline_rate: current conversion rate
    min_detectable_effect: minimum relative improvement to detect
    alpha: significance level (Type I error)
    power: 1 - Type II error
    """
    p1 = baseline_rate
    p2 = baseline_rate * (1 + min_detectable_effect)
    
    # Z-values
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula
    p_avg = (p1 + p2) / 2
    n = ((z_alpha * np.sqrt(2 * p_avg * (1-p_avg)) + 
          z_beta * np.sqrt(p1*(1-p1) + p2*(1-p2))) / (p2-p1))**2
    
    return int(np.ceil(n))

# Scenario: 5% click rate, want to detect 10% relative improvement
n_per_group = design_ab_test(
    baseline_rate=0.05,
    min_detectable_effect=0.10,  # 10% lift (5% → 5.5%)
    alpha=0.05,
    power=0.80
)
print(f"Required sample size per group: {n_per_group:,}")
print(f"Total participants needed: {2*n_per_group:,}")
print(f"At 10K daily users, need ~{2*n_per_group/10000:.0f} days")
```

### Interview Problem 2: Meta — "Cross-Validation with Proper Statistics"

```python
import numpy as np
from scipy import stats

def nested_cross_validation(X, y, model_configs, k_outer=5, k_inner=3):
    """
    Proper model selection AND evaluation with nested CV.
    Inner loop: select best hyperparameters
    Outer loop: estimate generalization performance
    """
    n = len(y)
    indices = np.random.permutation(n)
    fold_size = n // k_outer
    outer_scores = []
    
    for i in range(k_outer):
        # Outer split
        test_idx = indices[i*fold_size:(i+1)*fold_size]
        train_idx = np.setdiff1d(indices, test_idx)
        
        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]
        
        # Inner loop: find best config
        best_config = None
        best_inner_score = -np.inf
        
        inner_fold_size = len(train_idx) // k_inner
        inner_indices = np.random.permutation(len(train_idx))
        
        for config in model_configs:
            inner_scores = []
            for j in range(k_inner):
                val_idx = inner_indices[j*inner_fold_size:(j+1)*inner_fold_size]
                train_inner_idx = np.setdiff1d(inner_indices, val_idx)
                
                # Simplified: just use correlation as "score"
                # In practice, train a model with this config
                score = np.random.uniform(0.7, 0.95)  # Placeholder
                inner_scores.append(score)
            
            mean_score = np.mean(inner_scores)
            if mean_score > best_inner_score:
                best_inner_score = mean_score
                best_config = config
        
        # Evaluate best config on outer test set
        outer_score = np.random.uniform(0.75, 0.90)  # Placeholder
        outer_scores.append(outer_score)
        print(f"Fold {i+1}: best config = {best_config}, score = {outer_score:.3f}")
    
    mean_score = np.mean(outer_scores)
    ci = stats.t.interval(0.95, k_outer-1, 
                          loc=mean_score, 
                          scale=stats.sem(outer_scores))
    
    print(f"\nOverall: {mean_score:.3f} ± {stats.sem(outer_scores):.3f}")
    print(f"95% CI: ({ci[0]:.3f}, {ci[1]:.3f})")

# Run
np.random.seed(42)
X = np.random.randn(500, 10)
y = np.random.binomial(1, 0.5, 500)
configs = ["lr=0.001", "lr=0.01", "lr=0.1"]

nested_cross_validation(X, y, configs)
```

### Interview Problem 3: Amazon — "Bayesian A/B Testing with Thompson Sampling"

```python
import numpy as np

def thompson_sampling_ab_test(true_rates, n_rounds=1000):
    """
    Bayesian A/B testing: no fixed sample size needed!
    Uses Thompson Sampling to adaptively allocate traffic.
    """
    k = len(true_rates)
    # Beta prior parameters
    alpha = np.ones(k)  # successes + 1
    beta_param = np.ones(k)   # failures + 1
    
    choices = np.zeros(k, dtype=int)
    rewards = np.zeros(k, dtype=int)
    
    for t in range(n_rounds):
        # Sample from posterior (Beta distribution)
        samples = [np.random.beta(alpha[i], beta_param[i]) for i in range(k)]
        
        # Choose the arm with highest sample
        choice = np.argmax(samples)
        choices[choice] += 1
        
        # Observe reward
        reward = np.random.binomial(1, true_rates[choice])
        rewards[choice] += reward
        
        # Update posterior
        alpha[choice] += reward
        beta_param[choice] += 1 - reward
    
    print("Thompson Sampling Results:")
    print(f"{'Variant':>10} {'True Rate':>10} {'Observed':>10} {'Pulls':>8} {'Traffic%':>10}")
    for i in range(k):
        obs_rate = rewards[i] / max(choices[i], 1)
        traffic = choices[i] / n_rounds * 100
        print(f"{'ABCD'[i]:>10} {true_rates[i]:>10.3f} {obs_rate:>10.3f} "
              f"{choices[i]:>8} {traffic:>9.1f}%")

# 4 variants: B is the winner
thompson_sampling_ab_test([0.05, 0.07, 0.04, 0.05], n_rounds=10000)
```

---

## ✅ Module 12 Checkpoint

- [ ] Distinguish population parameters from sample estimates
- [ ] Evaluate estimators: bias, consistency, efficiency
- [ ] Derive MLE for common distributions
- [ ] Connect cross-entropy loss to maximum likelihood
- [ ] Compute confidence intervals (analytical and bootstrap)
- [ ] Design and analyze A/B tests
- [ ] Apply Bonferroni correction for multiple testing
- [ ] Explain the difference between MLE and MAP

---

## 🎓 Congratulations!

You've completed the full ML Math Foundations curriculum. Here's what you've mastered:

```
 ┌─────────────────────────────────────────────────────────┐
 │              YOUR MATHEMATICAL TOOLKIT                  │
 │                                                         │
 │  ✅ Sets & Logic          → Data structures, decisions  │
 │  ✅ Linear Systems        → The backbone of ML          │
 │  ✅ Vector Spaces         → Where embeddings live       │
 │  ✅ Spectral Theory       → PCA, PageRank, stability    │
 │  ✅ Projection            → Least squares, attention    │
 │  ✅ SVD & Low Rank        → Compression, recommenders   │
 │  ✅ Applications          → Regression, PCA             │
 │  ✅ Multivariable Calculus→ Backpropagation, gradients  │
 │  ✅ Probability           → Bayes, distributions        │
 │  ✅ Joint Distributions   → Multivariate models, GMMs   │
 │  ✅ Statistical Inference → MLE, confidence, testing    │
 └─────────────────────────────────────────────────────────┘
```

**Next Steps:**
1. Practice the FAANG problems — do them without looking at solutions
2. Implement everything from scratch in Python
3. Read ML papers and identify the math concepts in each
4. Apply these foundations to specific ML topics: deep learning, NLP, computer vision

**Back to →** [Main Index](../README.md)
