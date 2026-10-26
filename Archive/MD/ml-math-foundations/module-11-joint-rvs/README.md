# Module 11 — Joint Random Variables

## When Variables Dance Together

> **Why Joint RVs Matter in ML:** Features in real data are almost never independent. Understanding how variables relate to each other — through joint distributions, covariance, and correlation — is fundamental to multivariate models, GANs, diffusion models, and any model that handles multiple inputs.

```
 MODULE 11 ROADMAP
 ═══════════════════════════════════════
 11.01 Two Discrete Variables
 11.02 Two Continuous Variables
 11.03 Moments of Joint Distributions
 11.04 Covariance & Correlation
 11.05 Gaussian Combinations
 ═══════════════════════════════════════
```

---

## 11.01 — Two Discrete Variables (6 Lessons)

### Lesson 1: Joint PMF

The **joint PMF** gives the probability that X = x AND Y = y simultaneously:

```
P(X = x, Y = y) = P(X = x ∩ Y = y)
```

📊 **Joint PMF Table:**
```
          Y = 0    Y = 1    Y = 2    P(X=x)
X = 0      0.10     0.15     0.05     0.30
X = 1      0.20     0.25     0.25     0.70
────────────────────────────────────────────
P(Y=y)     0.30     0.40     0.30     1.00
           └──────────────────────┘
                  marginals
```

```python
import numpy as np

# Joint PMF as a matrix
joint_pmf = np.array([
    [0.10, 0.15, 0.05],   # X=0
    [0.20, 0.25, 0.25],   # X=1
])

print(f"Joint PMF:\n{joint_pmf}")
print(f"Sum (must be 1): {joint_pmf.sum():.2f}")

# Marginal distributions
p_x = joint_pmf.sum(axis=1)  # Sum over Y
p_y = joint_pmf.sum(axis=0)  # Sum over X
print(f"\nP(X): {p_x}")  # [0.30, 0.70]
print(f"P(Y): {p_y}")    # [0.30, 0.40, 0.30]

# Conditional: P(Y|X=1) = P(X=1, Y) / P(X=1)
p_y_given_x1 = joint_pmf[1, :] / p_x[1]
print(f"\nP(Y|X=1): {np.round(p_y_given_x1, 3)}")
print(f"Sum: {p_y_given_x1.sum():.2f}")  # Must be 1

# Check independence: P(X,Y) = P(X)P(Y)?
independent_pmf = np.outer(p_x, p_y)
print(f"\nIf independent, joint would be:\n{np.round(independent_pmf, 3)}")
print(f"Actually independent? {np.allclose(joint_pmf, independent_pmf)}")
```

### Lesson 2: Marginal Distributions — "Summing Out" Variables

💡 **Key Intuition:** To get the distribution of just X (ignoring Y), sum over all possible Y values:

```
P(X = x) = Σ_y P(X = x, Y = y)
```

⚡ **ML Connection:** Marginalization is used everywhere:
- **Mixture models:** P(x) = Σ_k P(x|k)P(k)
- **Variational inference:** Evidence lower bound (ELBO)
- **Attention:** Marginalizing over possible alignments

### Lesson 3: Conditional Distributions

```
P(Y = y | X = x) = P(X = x, Y = y) / P(X = x)
```

💡 **Key Insight:** Conditioning is like "slicing" the joint distribution at a particular value.

```python
# Conditional distributions in ML: P(label | features)
# This is literally what classifiers compute!

# Simple example: weather and activity
# P(Activity | Weather)
joint = {
    ("sunny", "beach"):   0.20,
    ("sunny", "park"):    0.15,
    ("sunny", "indoor"):  0.05,
    ("rainy", "beach"):   0.02,
    ("rainy", "park"):    0.03,
    ("rainy", "indoor"):  0.35,
    ("cloudy", "beach"):  0.05,
    ("cloudy", "park"):   0.10,
    ("cloudy", "indoor"): 0.05,
}

# Compute P(Activity | Weather = "rainy")
p_rainy = sum(p for (w, a), p in joint.items() if w == "rainy")
print(f"P(rainy) = {p_rainy:.2f}")

print("P(Activity | rainy):")
for activity in ["beach", "park", "indoor"]:
    p = joint[("rainy", activity)] / p_rainy
    print(f"  {activity}: {p:.3f}")
```

### Lessons 4-6: Independence, Conditional Independence, and Chain Rule

**Chain Rule of Probability:**
```
P(X₁, X₂, ..., Xₙ) = P(X₁) × P(X₂|X₁) × P(X₃|X₁,X₂) × ... × P(Xₙ|X₁,...,Xₙ₋₁)
```

⚡ **ML Connection:** This is exactly how autoregressive models (GPT, language models) generate text!

```python
# Autoregressive generation = chain rule of probability
# P(w₁, w₂, w₃, ...) = P(w₁) × P(w₂|w₁) × P(w₃|w₁,w₂) × ...

# Simplified language model
vocab = ["the", "cat", "sat", "on", "mat", "dog"]

# Conditional probabilities (simplified)
transitions = {
    "<start>": {"the": 0.6, "cat": 0.1, "sat": 0.05, "on": 0.05, "mat": 0.1, "dog": 0.1},
    "the": {"cat": 0.3, "dog": 0.3, "mat": 0.2, "the": 0.05, "sat": 0.05, "on": 0.1},
    "cat": {"sat": 0.5, "on": 0.2, "the": 0.1, "cat": 0.05, "mat": 0.05, "dog": 0.1},
    "sat": {"on": 0.6, "the": 0.2, "cat": 0.05, "sat": 0.05, "mat": 0.05, "dog": 0.05},
    "on": {"the": 0.7, "cat": 0.05, "sat": 0.05, "on": 0.05, "mat": 0.1, "dog": 0.05},
    "mat": {"the": 0.3, "cat": 0.1, "sat": 0.1, "on": 0.1, "mat": 0.1, "dog": 0.3},
    "dog": {"sat": 0.4, "on": 0.2, "the": 0.2, "cat": 0.1, "mat": 0.05, "dog": 0.05},
}

def generate_sentence(transitions, max_len=6):
    """Generate a sentence using the chain rule."""
    sentence = []
    current = "<start>"
    total_log_prob = 0
    
    for _ in range(max_len):
        probs = transitions.get(current, transitions["<start>"])
        words = list(probs.keys())
        p = list(probs.values())
        next_word = np.random.choice(words, p=p)
        sentence.append(next_word)
        total_log_prob += np.log(probs[next_word])
        current = next_word
    
    return " ".join(sentence), total_log_prob

for _ in range(5):
    sent, logp = generate_sentence(transitions)
    print(f"  '{sent}' (log-prob: {logp:.2f})")
```

---

## 11.02 — Two Continuous Variables (6 Lessons)

### Lesson 1: Joint PDF

For continuous variables, the joint PDF f(x, y) defines probability as volume:

```
P(a ≤ X ≤ b, c ≤ Y ≤ d) = ∫∫ f(x, y) dy dx
```

```python
import numpy as np
from scipy import integrate

# Example: Joint PDF f(x,y) = 24xy for 0 ≤ x ≤ 1, 0 ≤ y ≤ 1-x
def joint_pdf(y, x):
    if 0 <= x <= 1 and 0 <= y <= 1 - x:
        return 24 * x * y
    return 0.0

# Verify it integrates to 1
total, _ = integrate.dblquad(joint_pdf, 0, 1, 0, lambda x: 1 - x)
print(f"∫∫ f(x,y) dA = {total:.4f} (should be 1.0)")

# P(X ≤ 0.5, Y ≤ 0.3)
prob, _ = integrate.dblquad(joint_pdf, 0, 0.5, 0, lambda x: min(0.3, 1 - x))
print(f"P(X ≤ 0.5, Y ≤ 0.3) = {prob:.4f}")

# Marginal PDF of X: f_X(x) = ∫ f(x,y) dy
x_val = 0.3
marginal_x, _ = integrate.quad(lambda y: joint_pdf(y, x_val), 0, 1 - x_val)
print(f"f_X({x_val}) = {marginal_x:.4f}")
# Analytical: f_X(x) = 12x(1-x)² — integrating 24xy over y from 0 to 1-x
print(f"Analytical:  {12 * x_val * (1 - x_val)**2:.4f}")
```

### Lesson 2: Bivariate Normal Distribution ⭐

The most important joint distribution in ML:

```
f(x, y) = (1/2πσ₁σ₂√(1-ρ²)) × exp[-z/2(1-ρ²)]

where z = (x-μ₁)²/σ₁² - 2ρ(x-μ₁)(y-μ₂)/σ₁σ₂ + (y-μ₂)²/σ₂²
```

📊 **The Shape of Bivariate Normal (contours):**
```
ρ = 0 (independent):    ρ = 0.8 (correlated):    ρ = -0.8:
     ┌──┐                    ╱╱                     ╲╲
    ╱    ╲                  ╱╱                       ╲╲
   │  ●   │                ╱╱  ●                   ●  ╲╲
    ╲    ╱                 ╱╱                         ╲╲
     └──┘                 ╱╱                           ╲╲
  Circular                Tilted ellipse              Tilted other way
```

```python
import numpy as np

def sample_bivariate_normal(mu, cov, n=1000):
    """Sample from a bivariate normal distribution."""
    return np.random.multivariate_normal(mu, cov, n)

# Different correlation strengths
mu = [0, 0]

for rho in [0, 0.5, 0.9, -0.9]:
    cov = [[1, rho], [rho, 1]]
    samples = sample_bivariate_normal(mu, cov, 10000)
    
    empirical_corr = np.corrcoef(samples.T)[0, 1]
    print(f"ρ = {rho:>5.1f}: empirical correlation = {empirical_corr:.3f}")
```

---

## 11.03 — Moments of Joint Distributions (8 Lessons)

### Key Formulas

```
E[XY] = Σ_x Σ_y xy × P(X=x, Y=y)       (discrete)
      = ∫∫ xy × f(x,y) dx dy             (continuous)

E[g(X,Y)] = ∫∫ g(x,y) × f(x,y) dx dy   (LOTUS — Law of the Unconscious Statistician)
```

```python
import numpy as np

# Compute joint moments from a joint PMF table
joint_pmf = np.array([
    [0.10, 0.15, 0.05],   # X=0, Y=0,1,2
    [0.20, 0.25, 0.25],   # X=1, Y=0,1,2
])

x_vals = np.array([0, 1])
y_vals = np.array([0, 1, 2])

# E[X]
E_X = sum(x * joint_pmf[i, :].sum() for i, x in enumerate(x_vals))
print(f"E[X] = {E_X:.3f}")

# E[Y]
E_Y = sum(y * joint_pmf[:, j].sum() for j, y in enumerate(y_vals))
print(f"E[Y] = {E_Y:.3f}")

# E[XY] — the joint moment
E_XY = 0
for i, x in enumerate(x_vals):
    for j, y in enumerate(y_vals):
        E_XY += x * y * joint_pmf[i, j]
print(f"E[XY] = {E_XY:.3f}")

# Cov(X,Y) = E[XY] - E[X]E[Y]
Cov_XY = E_XY - E_X * E_Y
print(f"Cov(X,Y) = {Cov_XY:.4f}")
print(f"  (Positive → X and Y tend to increase together)")

# Verify with simulation
n = 1000000
samples = []
for _ in range(n):
    flat_idx = np.random.choice(6, p=joint_pmf.flatten())
    i, j = divmod(flat_idx, 3)
    samples.append((x_vals[i], y_vals[j]))
samples = np.array(samples)

print(f"\nSimulation verification (n={n:,}):")
print(f"  E[X] ≈ {samples[:, 0].mean():.3f}")
print(f"  E[Y] ≈ {samples[:, 1].mean():.3f}")
print(f"  E[XY] ≈ {(samples[:, 0] * samples[:, 1]).mean():.3f}")
print(f"  Cov(X,Y) ≈ {np.cov(samples.T)[0, 1]:.4f}")
```

### LOTUS: Law of the Unconscious Statistician

💡 **Key Insight:** To find E[g(X,Y)], you don't need the distribution of g(X,Y) — just apply g inside the expectation:

```python
# E[X² + Y²] — expected squared distance from origin
E_X2_Y2 = 0
for i, x in enumerate(x_vals):
    for j, y in enumerate(y_vals):
        E_X2_Y2 += (x**2 + y**2) * joint_pmf[i, j]
print(f"E[X² + Y²] = {E_X2_Y2:.3f}")

# E[max(X,Y)] — expected maximum
E_max = 0
for i, x in enumerate(x_vals):
    for j, y in enumerate(y_vals):
        E_max += max(x, y) * joint_pmf[i, j]
print(f"E[max(X,Y)] = {E_max:.3f}")
```

---

## 11.04 — Covariance and Correlation (4 Lessons)

### Lesson 1: Covariance

**Covariance** measures how two variables move together:

```
Cov(X, Y) = E[(X - μₓ)(Y - μᵧ)] = E[XY] - E[X]E[Y]
```

```
Cov > 0:  X↑ when Y↑  (move together)
Cov = 0:  no linear relationship
Cov < 0:  X↑ when Y↓  (move opposite)
```

### Lesson 2: Correlation (Pearson's r)

**Correlation** is covariance normalized to [-1, 1]:

```
ρ(X, Y) = Cov(X, Y) / (σₓ × σᵧ)

ρ = +1:  perfect positive linear relationship
ρ = 0:   no linear relationship (could still be nonlinearly related!)
ρ = -1:  perfect negative linear relationship
```

```python
import numpy as np

# Covariance and correlation in practice
np.random.seed(42)

# Generate correlated features (like real-world data)
n = 1000
age = np.random.normal(40, 10, n)
income = 1000 * age + 5000 + np.random.normal(0, 10000, n)  # Correlated!
height = np.random.normal(170, 10, n)  # Independent of age

# Covariance matrix
data = np.column_stack([age, income, height])
cov_matrix = np.cov(data.T)
corr_matrix = np.corrcoef(data.T)

print("Correlation Matrix:")
labels = ["age", "income", "height"]
print(f"{'':>10}", end="")
for l in labels:
    print(f"{l:>10}", end="")
print()
for i, l in enumerate(labels):
    print(f"{l:>10}", end="")
    for j in range(3):
        print(f"{corr_matrix[i,j]:>10.3f}", end="")
    print()

# Notice: age-income highly correlated, height independent
```

### Lesson 3: The Covariance Matrix ⭐

For a random vector X = [X₁, X₂, ..., Xₙ]:

```
       ┌                                        ┐
       │ Var(X₁)      Cov(X₁,X₂)  ···  Cov(X₁,Xₙ) │
Σ =    │ Cov(X₂,X₁)  Var(X₂)     ···  Cov(X₂,Xₙ) │
       │ ⋮            ⋮            ⋱    ⋮            │
       │ Cov(Xₙ,X₁)  Cov(Xₙ,X₂) ···  Var(Xₙ)     │
       └                                        ┘

Properties:
  ✓ Symmetric (Σ = Σᵀ)
  ✓ Positive semidefinite
  ✓ Diagonal = variances
  ✓ Off-diagonal = covariances
```

⚡ **ML Connection:** The covariance matrix appears in:
- PCA (eigenvectors of covariance)
- Gaussian Mixture Models (each cluster has its own Σ)
- Mahalanobis distance (accounts for correlation)
- Kalman filters (state uncertainty)

```python
# The covariance matrix IS the shape of data clusters
import numpy as np

def mahalanobis_distance(x, mu, cov):
    """
    Distance that accounts for covariance structure.
    Used in anomaly detection, Gaussian mixture models.
    """
    diff = x - mu
    cov_inv = np.linalg.inv(cov)
    return np.sqrt(diff @ cov_inv @ diff)

# Example: anomaly detection
np.random.seed(42)
mu = np.array([0, 0])
cov = np.array([[1, 0.8], [0.8, 1]])  # Correlated features

# Normal point (inside the ellipse)
x_normal = np.array([0.5, 0.3])
# Anomalous point (outside the ellipse)
x_anomaly = np.array([2.0, -1.0])

d_normal = mahalanobis_distance(x_normal, mu, cov)
d_anomaly = mahalanobis_distance(x_anomaly, mu, cov)

print(f"Normal point:  Mahalanobis distance = {d_normal:.3f}")
print(f"Anomaly point: Mahalanobis distance = {d_anomaly:.3f}")
print(f"(Larger distance → more anomalous)")
```

### Lesson 4: Correlation ≠ Causation (But It's Still Useful)

```python
# Famous example: ice cream sales and drowning deaths are correlated
# But eating ice cream doesn't cause drowning!
# Hidden variable: temperature (summer → more of both)

# In ML, we must be careful:
# 1. Confounders can create spurious correlations
# 2. Feature selection based on correlation alone can be misleading
# 3. Always consider causal reasoning when interpreting model features

# Anscombe's quartet: same correlation, very different data!
datasets = {
    "I":   (np.array([10,8,13,9,11,14,6,4,12,7,5]),
             np.array([8.04,6.95,7.58,8.81,8.33,9.96,7.24,4.26,10.84,4.82,5.68])),
    "II":  (np.array([10,8,13,9,11,14,6,4,12,7,5]),
             np.array([9.14,8.14,8.74,8.77,9.26,8.10,6.13,3.10,9.13,7.26,4.74])),
    "III": (np.array([10,8,13,9,11,14,6,4,12,7,5]),
             np.array([7.46,6.77,12.74,7.11,7.81,8.84,6.08,5.39,8.15,6.42,5.73])),
    "IV":  (np.array([8,8,8,8,8,8,8,19,8,8,8]),
             np.array([6.58,5.76,7.71,8.84,8.47,7.04,5.25,12.50,5.56,7.91,6.89])),
}

print("Anscombe's Quartet — same stats, different data:")
for name, (x, y) in datasets.items():
    r = np.corrcoef(x, y)[0, 1]
    print(f"  Dataset {name}: r = {r:.3f}, mean_x = {x.mean():.1f}, mean_y = {y.mean():.2f}")
```

---

## 11.05 — Gaussian Combinations (5 Lessons)

### Lesson 1: Sum of Independent Normals

```
If X ~ N(μ₁, σ₁²) and Y ~ N(μ₂, σ₂²) are independent:
Then X + Y ~ N(μ₁ + μ₂, σ₁² + σ₂²)
```

💡 **Key Insight:** Normal distributions are "closed under addition" — this is why they're so useful!

### Lesson 2: The Multivariate Normal Distribution ⭐

```
X ~ N(μ, Σ)

Where:
  μ = mean vector (n × 1)
  Σ = covariance matrix (n × n, symmetric, positive semidefinite)

PDF: f(x) = (2π)^(-n/2) |Σ|^(-1/2) exp[-½(x-μ)ᵀΣ⁻¹(x-μ)]
```

⚡ **ML Connection:** The multivariate normal is the basis for:
- Gaussian Mixture Models (GMMs)
- Variational Autoencoders (VAE) — the latent space is Gaussian
- Gaussian Processes (GP)
- Linear Discriminant Analysis (LDA)

```python
import numpy as np

class GaussianMixtureModel:
    """GMM from scratch — combining joint distributions."""
    
    def __init__(self, k=2, max_iter=100):
        self.k = k
        self.max_iter = max_iter
    
    def fit(self, X):
        n, d = X.shape
        
        # Initialize
        self.means = X[np.random.choice(n, self.k, replace=False)]
        self.covs = [np.eye(d) for _ in range(self.k)]
        self.weights = np.ones(self.k) / self.k
        
        for iteration in range(self.max_iter):
            # E-step: compute responsibilities
            resp = self._compute_responsibilities(X)
            
            # M-step: update parameters
            for j in range(self.k):
                r_j = resp[:, j]
                N_j = r_j.sum()
                self.means[j] = (r_j[:, None] * X).sum(axis=0) / N_j
                diff = X - self.means[j]
                self.covs[j] = (r_j[:, None, None] * (diff[:, :, None] @ diff[:, None, :])).sum(axis=0) / N_j
                self.covs[j] += 1e-6 * np.eye(d)  # Regularization
                self.weights[j] = N_j / n
        
        return self
    
    def _gaussian_pdf(self, X, mean, cov):
        d = len(mean)
        diff = X - mean
        cov_inv = np.linalg.inv(cov)
        exponent = -0.5 * np.sum(diff @ cov_inv * diff, axis=1)
        normalization = np.sqrt((2*np.pi)**d * np.linalg.det(cov))
        return np.exp(exponent) / normalization
    
    def _compute_responsibilities(self, X):
        resp = np.zeros((X.shape[0], self.k))
        for j in range(self.k):
            resp[:, j] = self.weights[j] * self._gaussian_pdf(X, self.means[j], self.covs[j])
        resp /= resp.sum(axis=1, keepdims=True)
        return resp
    
    def predict(self, X):
        resp = self._compute_responsibilities(X)
        return resp.argmax(axis=1)

# Demo
np.random.seed(42)
# Generate data from 2 Gaussians
X1 = np.random.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], 200)
X2 = np.random.multivariate_normal([4, 4], [[1, -0.3], [-0.3, 1]], 200)
X = np.vstack([X1, X2])

gmm = GaussianMixtureModel(k=2)
gmm.fit(X)
labels = gmm.predict(X)

print("GMM Results:")
for j in range(2):
    print(f"  Cluster {j}: mean = {np.round(gmm.means[j], 2)}, "
          f"weight = {gmm.weights[j]:.3f}, "
          f"size = {(labels == j).sum()}")
```

### Lessons 3-5: Conditional Gaussians and Bayesian Linear Regression

```python
import numpy as np

def bayesian_linear_regression(X_train, y_train, X_test, alpha=1.0, beta=1.0):
    """
    Bayesian linear regression:
    Prior:      w ~ N(0, α⁻¹I)
    Likelihood: y|x,w ~ N(wᵀx, β⁻¹)
    Posterior:  w|X,y ~ N(m_N, S_N)
    
    Returns predictions WITH uncertainty!
    """
    n_features = X_train.shape[1]
    
    # Posterior covariance
    S_N_inv = alpha * np.eye(n_features) + beta * X_train.T @ X_train
    S_N = np.linalg.inv(S_N_inv)
    
    # Posterior mean
    m_N = beta * S_N @ X_train.T @ y_train
    
    # Predictions
    y_pred = X_test @ m_N
    
    # Prediction uncertainty (variance at each test point)
    y_var = 1/beta + np.sum(X_test @ S_N * X_test, axis=1)
    y_std = np.sqrt(y_var)
    
    return y_pred, y_std, m_N, S_N

# Demo
np.random.seed(42)
X_train = np.random.randn(20, 1)
X_train = np.column_stack([X_train, np.ones(20)])  # Add bias
y_train = 2 * X_train[:, 0] + 1 + 0.3 * np.random.randn(20)

X_test = np.column_stack([np.linspace(-3, 3, 100), np.ones(100)])

y_pred, y_std, w_mean, w_cov = bayesian_linear_regression(X_train, y_train, X_test)

print("Bayesian Linear Regression:")
print(f"  Weight posterior mean: {np.round(w_mean, 3)}")
print(f"  Weight posterior std:  {np.round(np.sqrt(np.diag(w_cov)), 3)}")
print(f"  Average prediction std: {y_std.mean():.3f}")
print(f"  (Uncertainty grows away from training data!)")
```

---

## 🔥 FAANG Deep Dive — Joint RVs

### Interview Problem 1: Google — "Multivariate Anomaly Detection"

```python
def multivariate_anomaly_detection(X_train, X_test, threshold=0.05):
    """
    Detect anomalies using multivariate Gaussian.
    Fit a Gaussian to normal data, flag low-probability points.
    """
    mu = X_train.mean(axis=0)
    cov = np.cov(X_train.T)
    cov_inv = np.linalg.inv(cov)
    
    # Mahalanobis distance for each test point
    diff = X_test - mu
    distances = np.sqrt(np.sum(diff @ cov_inv * diff, axis=1))
    
    # Flag points beyond threshold (using chi-squared distribution)
    from scipy.stats import chi2
    d = X_train.shape[1]
    critical_value = np.sqrt(chi2.ppf(1 - threshold, d))
    
    anomalies = distances > critical_value
    return anomalies, distances

np.random.seed(42)
X_train = np.random.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], 500)
X_test = np.vstack([
    np.random.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], 90),
    np.random.multivariate_normal([5, 5], [[0.1, 0], [0, 0.1]], 10),  # Anomalies!
])

anomalies, distances = multivariate_anomaly_detection(X_train, X_test)
print(f"Anomalies detected: {anomalies.sum()} out of {len(X_test)}")
print(f"Anomaly distances: {np.round(distances[anomalies][:5], 2)}")
```

---

## ✅ Module 11 Checkpoint

- [ ] Construct and interpret joint probability tables
- [ ] Compute marginal and conditional distributions
- [ ] Apply the chain rule of probability
- [ ] Calculate covariance and correlation
- [ ] Build and interpret covariance matrices
- [ ] Understand the multivariate normal distribution
- [ ] Implement a Gaussian Mixture Model
- [ ] Perform Bayesian linear regression with uncertainty

**Next →** [Module 12: Inference](../module-12-inference/README.md)
