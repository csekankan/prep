# Machine Learning Mastery — Staff Engineer Interview Guide
> From fundamentals to system design. Every concept that separates senior from staff.

---

## Table of Contents
1. [Math Foundations You Must Own](#1-math-foundations-you-must-own)
2. [Bias-Variance & The Generalization Problem](#2-bias-variance--the-generalization-problem)
3. [Linear Models — Deeper Than You Think](#3-linear-models--deeper-than-you-think)
4. [Regularization — The Full Picture](#4-regularization--the-full-picture)
5. [Tree-Based Models & Ensembles](#5-tree-based-models--ensembles)
6. [Gradient Boosting — How It Actually Works](#6-gradient-boosting--how-it-actually-works)
7. [Neural Networks — First Principles](#7-neural-networks--first-principles)
8. [Optimizers — From SGD to AdamW](#8-optimizers--from-sgd-to-adamw)
9. [CNNs, RNNs, LSTMs](#9-cnns-rnns-lstms)
10. [Attention & Transformers](#10-attention--transformers)
11. [Embeddings & Representation Learning](#11-embeddings--representation-learning)
12. [Unsupervised Learning](#12-unsupervised-learning)
13. [Probability & Statistics for ML](#13-probability--statistics-for-ml)
14. [Feature Engineering & Selection](#14-feature-engineering--selection)
15. [Model Evaluation — Beyond Accuracy](#15-model-evaluation--beyond-accuracy)
16. [Calibration & Uncertainty](#16-calibration--uncertainty)
17. [Recommendation Systems](#17-recommendation-systems)
18. [Large Language Models — Production Knowledge](#18-large-language-models--production-knowledge)
19. [ML System Design](#19-ml-system-design)
20. [MLOps & Production Failures](#20-mlops--production-failures)
21. [Staff-Level Interview Patterns](#21-staff-level-interview-patterns)

---

## 1. Math Foundations You Must Own

### 1.1 Linear Algebra

```
Vector dot product:   a · b = Σ aᵢbᵢ = |a||b|cos(θ)
Matrix multiply:      (AB)ᵢⱼ = Σₖ Aᵢₖ Bₖⱼ
Transpose:            (AB)ᵀ = BᵀAᵀ
Inverse:              AA⁻¹ = I   (only square, full-rank matrices)
```

**Eigendecomposition:**
```
Av = λv
A = QΛQᵀ    (symmetric A, Q = eigenvectors, Λ = diagonal eigenvalues)

Key insight: PCA finds eigenvectors of covariance matrix.
Largest eigenvalue → direction of maximum variance.
```

**SVD (most important in ML):**
```
A = UΣVᵀ
U: left singular vectors (m×m)  — output space
Σ: singular values (m×n diagonal) — importance
V: right singular vectors (n×n) — input space

Used in: PCA, matrix factorization (RecSys), LSA, pseudoinverse
Truncated SVD: keep top-k → dimensionality reduction
```

**Norms:**
```
L0: number of non-zero elements
L1: Σ|xᵢ|              → sparsity, Lasso
L2: √(Σxᵢ²)           → Euclidean distance, Ridge
L∞: max|xᵢ|

Frobenius norm (matrices): √(Σᵢⱼ Aᵢⱼ²) = √(Σ σᵢ²)
```

### 1.2 Calculus

**Chain rule (the heart of backprop):**
```
∂L/∂w = ∂L/∂y · ∂y/∂w

Computational graph:  x → [w] → z → [σ] → a → [loss] → L
Backward:             ∂L/∂w = ∂L/∂a · ∂a/∂z · ∂z/∂w
```

**Key derivatives:**
```python
# Sigmoid:  σ(x) = 1/(1+e^-x)
# σ'(x) = σ(x)(1 - σ(x))   ← vanishes for large |x|

# ReLU:  max(0, x)
# ReLU'(x) = 1 if x>0 else 0   ← dead neuron problem

# Softmax: σ(z)ᵢ = e^zᵢ / Σⱼ e^zⱼ
# ∂σᵢ/∂zⱼ = σᵢ(δᵢⱼ - σⱼ)    ← Jacobian

# Cross-entropy loss with softmax:
# L = -Σ yᵢ log(ŷᵢ)
# ∂L/∂zᵢ = ŷᵢ - yᵢ           ← beautifully simple gradient
```

**Gradient, Jacobian, Hessian:**
```
Gradient ∇f: vector of first derivatives (direction of steepest ascent)
Jacobian J:  matrix of first derivatives for vector→vector functions
Hessian H:   matrix of second derivatives (curvature)

If H is PSD (all eigenvalues ≥ 0): local minimum
If H is NSD: local maximum
If mixed: saddle point
```

### 1.3 Probability

```
Bayes' Theorem:  P(A|B) = P(B|A)·P(A) / P(B)

In ML:  P(params|data) ∝ P(data|params) · P(params)
         posterior      ∝ likelihood    · prior

MLE: maximize P(data|params)       → no regularization
MAP: maximize P(params|data)       → L2 reg (Gaussian prior), L1 reg (Laplace prior)

Expectation:   E[X] = Σ x·P(X=x)
Variance:      Var[X] = E[X²] - (E[X])²
Covariance:    Cov[X,Y] = E[XY] - E[X]E[Y]
```

**Information Theory:**
```
Entropy:          H(X) = -Σ p(x) log p(x)       (average surprise)
Cross-entropy:    H(p,q) = -Σ p(x) log q(x)     (cost of using q to encode p)
KL Divergence:    KL(p||q) = Σ p(x) log(p(x)/q(x))  (asymmetric "distance")
Mutual Info:      I(X;Y) = H(X) - H(X|Y) = KL(p(x,y)||p(x)p(y))

H(p,q) = H(p) + KL(p||q)     ← minimizing cross-entropy = minimizing KL divergence
```

---

## 2. Bias-Variance & The Generalization Problem

### The Decomposition

```
Expected Test Error = Bias² + Variance + Irreducible Noise

Bias:      error from wrong assumptions (underfitting)
Variance:  error from sensitivity to training data (overfitting)
Noise:     inherent randomness in data (irreducible)

E[(y - ŷ)²] = (E[ŷ] - f(x))² + E[(ŷ - E[ŷ])²] + σ²
               ───────────────   ─────────────────   ──
                   Bias²              Variance        Noise
```

```
High Bias:
  Train error: HIGH
  Test error:  HIGH (similar to train)
  Gap:         Small
  Fix:         More complex model, more features, less regularization

High Variance:
  Train error: LOW
  Test error:  HIGH
  Gap:         Large
  Fix:         More data, regularization, simpler model, dropout

The Tradeoff:
  Simple model  → High bias, low variance
  Complex model → Low bias, high variance
  Optimal:       Minimize total error
```

### Double Descent Phenomenon

```
Modern discovery: error curve is NOT monotonically increasing after interpolation threshold

Error
  │     ╲         ╱──╲
  │      ╲       ╱    ╲___________
  │       ╲_____╱
  └────────────────────────────────→ Model complexity
     classical   interpolation    overparameterized
      regime      threshold           regime

Deep neural networks operate in overparameterized regime —
they interpolate training data yet generalize well.
Implicit regularization from SGD is key.
```

### Practical Diagnosis

```python
import numpy as np
from sklearn.model_selection import learning_curve

# Learning curve: plot train/val error vs training set size
train_sizes, train_scores, val_scores = learning_curve(
    estimator, X, y,
    train_sizes=np.linspace(0.1, 1.0, 10),
    cv=5, scoring='neg_mean_squared_error'
)

# High bias:     both curves plateau at high error, close together
# High variance: large gap between train and val curves
# Good fit:      low error on both, gap narrows with more data
```

---

## 3. Linear Models — Deeper Than You Think

### 3.1 Linear Regression

```
Model:  ŷ = Xβ + ε,  ε ~ N(0, σ²I)

OLS solution:  β̂ = (XᵀX)⁻¹Xᵀy

Assumptions (BLUE — Gauss-Markov):
  1. Linearity:        E[y|X] = Xβ
  2. Full rank:        rank(X) = p (no multicollinearity)
  3. Exogeneity:       E[ε|X] = 0
  4. Homoscedasticity: Var[ε|X] = σ²I (constant variance)
  5. No autocorrelation: Cov[εᵢ, εⱼ] = 0 for i≠j

Why OLS works: BLUE (Best Linear Unbiased Estimator) by Gauss-Markov
When it fails: heteroscedasticity → WLS; autocorrelation → GLS; multicollinearity → Ridge
```

```python
# Geometric interpretation of OLS
# ŷ = Xβ̂ is the projection of y onto the column space of X
# Residuals e = y - ŷ are orthogonal to column space of X
# Xᵀ(y - Xβ̂) = 0  ← normal equations

# Computing without matrix inverse (numerically stable via QR)
import numpy as np
Q, R = np.linalg.qr(X)
beta = np.linalg.solve(R, Q.T @ y)  # more stable than (XᵀX)⁻¹Xᵀy

# Condition number of XᵀX = (condition of X)²  → amplifies numerical errors
np.linalg.cond(X)  # if > 1e10, worried about multicollinearity
```

### 3.2 Logistic Regression

```
P(y=1|x) = σ(wᵀx + b) = 1 / (1 + e^-(wᵀx+b))

Loss: Binary cross-entropy (= negative log-likelihood)
L = -[y log(p) + (1-y) log(1-p)]

Gradient: ∂L/∂w = (p - y)x    ← same form as linear regression!

Multi-class: softmax
P(y=k|x) = e^(wₖᵀx) / Σⱼ e^(wⱼᵀx)

Decision boundary: wᵀx + b = 0  (linear hyperplane)
```

**Why log loss not MSE for classification:**
```python
# MSE with sigmoid creates flat gradients (saturation)
# When p ≈ 0 and y=1: MSE gradient ≈ 0 (very slow learning)
# Log loss gradient = (p - y) × x: large gradient when prediction is wrong

# Probabilistic interpretation:
# Logistic regression = MLE under Bernoulli likelihood
# Ridge logistic = MAP with Gaussian prior on weights
```

### 3.3 Generalized Linear Models

```
GLM unifies linear, logistic, Poisson regression:

Component            | Linear    | Logistic        | Poisson
Distribution         | Gaussian  | Bernoulli       | Poisson
Link function g(μ)   | identity  | logit log(p/1-p)| log
Inverse link (μ)     | η         | sigmoid(η)      | exp(η)
Use case             | continuous| binary          | count data
```

---

## 4. Regularization — The Full Picture

### Ridge (L2)

```
L(w) = ||y - Xw||² + λ||w||²

Solution: w = (XᵀX + λI)⁻¹Xᵀy

Effects:
  - Shrinks all weights toward 0 (not to 0)
  - Handles multicollinearity (λI makes XᵀX invertible)
  - MAP with Gaussian prior: w ~ N(0, σ²/λ · I)
  - Closed-form solution (unlike Lasso)
  - ALL features kept (no sparsity)
```

### Lasso (L1)

```
L(w) = ||y - Xw||² + λ||w||₁

No closed-form! Solved via coordinate descent or proximal gradient.

Effects:
  - Drives some weights EXACTLY to 0 → feature selection
  - MAP with Laplace prior: w ~ Laplace(0, 1/λ)
  - When features correlated: arbitrarily picks one
  - Not differentiable at 0 → subgradient methods

Geometric intuition:
  Ridge constraint:  sphere (smooth) — optimal point on surface, not corner
  Lasso constraint:  diamond (corners) — optimal often at corner (zero coefficient)
```

### Elastic Net

```
L(w) = ||y - Xw||² + λ₁||w||₁ + λ₂||w||²

Best of both: sparsity + handles correlated features
Used in: high-dimensional genomics, text classification
```

### Dropout (Neural Networks)

```python
# Training: randomly zero each activation with probability p
# Inference: multiply all weights by (1-p) — or scale during training

# Intuition: trains 2^n different "thinned" networks, averages at test time
# Prevents co-adaptation of neurons (neurons can't rely on specific other neurons)
# Equivalent to: L2 regularization for linear networks

class Dropout(nn.Module):
    def __init__(self, p=0.5):
        super().__init__()
        self.p = p

    def forward(self, x):
        if not self.training:
            return x  # no dropout at inference
        mask = (torch.rand_like(x) > self.p).float()
        return x * mask / (1 - self.p)  # inverted dropout — keeps expected value same
```

### Batch Normalization

```python
# Normalize each feature across the batch, then learn scale/shift
# y = γ · (x - μ_batch) / σ_batch + β

# Effects:
#  - Reduces internal covariate shift
#  - Allows higher learning rates
#  - Mild regularization (noise from batch statistics)
#  - Problematic for: small batches, RNNs, online learning

# Inference: use running mean/var (not batch stats)
# Layer Norm (better for Transformers): normalize across features, not batch
```

### Weight Decay vs L2

```python
# Standard Adam + L2 loss: L2 is scaled by adaptive learning rate
# Weight decay (AdamW): weight decay applied separately from gradient update
# w ← w - lr·grad - lr·λ·w    ← decoupled

# They're equivalent for SGD but NOT for Adam — AdamW is preferred
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
```

---

## 5. Tree-Based Models & Ensembles

### 5.1 Decision Trees

```
Split criterion:
  Classification: Gini = 1 - Σ pᵢ²   OR   Entropy = -Σ pᵢ log pᵢ
  Regression:     MSE = 1/n Σ(yᵢ - ȳ)²

Information Gain = H(parent) - weighted_avg(H(children))

Gini vs Entropy: nearly identical in practice; Gini is faster to compute.

Pruning:
  Pre-pruning:  max_depth, min_samples_split, min_samples_leaf
  Post-pruning: cost-complexity pruning (Cp parameter)

Key insight: trees have high variance — small data change → very different tree
Solution: averaging (bagging) reduces variance without increasing bias
```

### 5.2 Random Forests

```
Algorithm:
  For each tree t = 1..T:
    1. Bootstrap sample n data points (with replacement)
    2. At each split, consider random subset of √p features
    3. Grow tree to max depth (no pruning)
  Predict: majority vote (classification) or mean (regression)

Why it works:
  Bagging:     reduces variance by averaging uncorrelated predictions
  Feature sub-sampling: decorrelates trees (key! without this → correlated trees)

Var(mean of N correlated vars) = σ²/N + (N-1)/N · ρ · σ²
  → decorrelation (low ρ) is critical for variance reduction

OOB Error: ~1/3 of data not in each bootstrap → free validation estimate

Feature Importance: mean decrease in impurity (MDI)
  Caveat: biased toward high-cardinality features → prefer permutation importance
```

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

rf = RandomForestClassifier(
    n_estimators=200,
    max_features='sqrt',    # key: feature subsampling
    min_samples_leaf=5,     # regularization
    n_jobs=-1,
    oob_score=True          # free validation error
)
rf.fit(X_train, y_train)
print("OOB score:", rf.oob_score_)

# Permutation importance (more reliable than MDI)
result = permutation_importance(rf, X_val, y_val, n_repeats=10)
importance = result.importances_mean
```

---

## 6. Gradient Boosting — How It Actually Works

### The Algorithm

```
Initialize: F₀(x) = argmin_γ Σ L(yᵢ, γ)   (e.g., mean for MSE, log-odds for log loss)

For m = 1 to M:
  1. Compute pseudo-residuals:
     rᵢₘ = -[∂L(yᵢ, F(xᵢ)) / ∂F(xᵢ)]   ← negative gradient of loss w.r.t. predictions

  2. Fit weak learner hₘ to residuals (rᵢₘ, xᵢ)

  3. Find optimal step size:
     γₘ = argmin_γ Σ L(yᵢ, Fₘ₋₁(xᵢ) + γ·hₘ(xᵢ))

  4. Update: Fₘ(x) = Fₘ₋₁(x) + η·γₘ·hₘ(x)   (η = learning rate / shrinkage)

Output: F_M(x)

Key insight: we're doing gradient descent in FUNCTION SPACE.
Each tree corrects the residual errors of the previous ensemble.
```

**For MSE loss:**
```
L(y, F) = ½(y - F)²
∂L/∂F = -(y - F) = F - y

Pseudo-residuals = y - F(x)   ← actual residuals!
So: gradient boosting with MSE fits trees to residuals (intuitive)
```

**For log loss:**
```
L(y, F) = -[y log p + (1-y) log(1-p)]  where p = sigmoid(F)
∂L/∂F = p - y

Pseudo-residuals = y - p   ← not actual residuals, but probability error
```

### XGBoost vs LightGBM vs CatBoost

```
XGBoost:
  - Level-wise tree growth (all leaves at same depth grown)
  - Second-order Taylor expansion of loss (uses Hessian)
  - Exact and approximate split finding
  - L1 + L2 regularization on leaf weights + tree complexity
  - Objective: L = Σ[lᵢ + l'ᵢhₘ(xᵢ) + ½l''ᵢhₘ(xᵢ)²] + Ω(hₘ)

LightGBM:
  - Leaf-wise tree growth (grow leaf with max gain → deeper, more asymmetric)
  - Gradient-based One-Side Sampling (GOSS): keeps large-gradient instances + sample small
  - Exclusive Feature Bundling (EFB): bundle mutually exclusive sparse features
  - Histogram-based split finding (faster than exact)
  - Better for large datasets, usually faster than XGBoost
  - Risk: can overfit with small data (use min_child_samples)

CatBoost:
  - Symmetric trees (balanced, like a lookup table)
  - Ordered boosting: target statistics computed without leakage
  - Native categorical feature handling (ordered target encoding)
  - Slower to train, competitive accuracy especially with categoricals
```

```python
import xgboost as xgb
import lightgbm as lgb

# XGBoost
model = xgb.XGBClassifier(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,           # row subsampling (reduces variance)
    colsample_bytree=0.8,    # feature subsampling per tree
    reg_alpha=0.1,           # L1
    reg_lambda=1.0,          # L2
    tree_method='hist',      # fast histogram method
    early_stopping_rounds=50,
    eval_metric='logloss',
)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=100)

# LightGBM
model = lgb.LGBMClassifier(
    n_estimators=1000,
    learning_rate=0.05,
    num_leaves=31,           # key param: 2^max_depth for symmetric, but leaf-wise can be more
    min_child_samples=20,    # regularization for small datasets
    subsample=0.8,
    colsample_bytree=0.8,
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
)
```

### SHAP Values — Explaining Boosted Trees

```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Global importance
shap.summary_plot(shap_values, X_test)

# Local explanation for one prediction
shap.waterfall_plot(explainer(X_test)[0])

# SHAP = Shapley values from game theory
# φᵢ = Σ [|S|!(p-|S|-1)!/p!] · [f(S∪{i}) - f(S)]  over all subsets S not containing i
# Satisfies: efficiency, symmetry, dummy, additivity
# Only method satisfying all four properties
```

---

## 7. Neural Networks — First Principles

### 7.1 Forward Pass

```python
import torch
import torch.nn as nn

class MLP(nn.Module):
    def __init__(self, dims):
        super().__init__()
        layers = []
        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i+1]))
            if i < len(dims) - 2:
                layers.append(nn.ReLU())
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)

# Universal Approximation Theorem:
# A single hidden layer with enough neurons can approximate any continuous function.
# BUT: depth is exponentially more efficient than width for many functions.
# Depth allows composing features hierarchically.
```

### 7.2 Backpropagation from Scratch

```python
import numpy as np

def sigmoid(z): return 1 / (1 + np.exp(-z))
def relu(z): return np.maximum(0, z)

class NeuralNet:
    def __init__(self, layer_sizes):
        self.W = []
        self.b = []
        for i in range(len(layer_sizes) - 1):
            # He initialization for ReLU
            self.W.append(np.random.randn(layer_sizes[i], layer_sizes[i+1]) *
                          np.sqrt(2.0 / layer_sizes[i]))
            self.b.append(np.zeros(layer_sizes[i+1]))

    def forward(self, X):
        self.cache = {'A': [X]}
        self.cache['Z'] = []
        A = X
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            Z = A @ W + b
            self.cache['Z'].append(Z)
            A = relu(Z) if i < len(self.W) - 1 else sigmoid(Z)
            self.cache['A'].append(A)
        return A

    def backward(self, y):
        m = y.shape[0]
        grads = {'dW': [], 'db': []}

        # Output layer gradient (sigmoid + cross-entropy = elegant)
        dA = self.cache['A'][-1] - y  # dL/dA for last layer

        for i in reversed(range(len(self.W))):
            A_prev = self.cache['A'][i]
            Z = self.cache['Z'][i]

            if i == len(self.W) - 1:
                dZ = dA  # already (p - y) for sigmoid + cross-entropy
            else:
                # ReLU derivative: 1 where Z > 0, 0 otherwise
                dZ = dA * (Z > 0)

            dW = A_prev.T @ dZ / m
            db = dZ.mean(axis=0)
            dA = dZ @ self.W[i].T  # propagate to previous layer

            grads['dW'].insert(0, dW)
            grads['db'].insert(0, db)

        return grads
```

### 7.3 Activation Functions

```
Function    | Formula              | Range     | Problems           | Use when
────────────┼──────────────────────┼───────────┼────────────────────┼──────────────────
Sigmoid     | 1/(1+e^-x)           | (0,1)     | Vanishing gradient | Output (binary)
Tanh        | (e^x-e^-x)/(e^x+e^-x)| (-1,1)   | Vanishing gradient | RNN hidden states
ReLU        | max(0,x)             | [0,∞)     | Dead neurons       | Default hidden
Leaky ReLU  | max(αx, x)           | (-∞,∞)   | —                  | Replace dead ReLU
ELU         | x if x>0, α(e^x-1)   | (-α,∞)   | Slower compute     | Deep nets
GELU        | x·Φ(x)               | (-∞,∞)   | —                  | Transformers
Swish       | x·sigmoid(x)         | (-∞,∞)   | —                  | EfficientNet
Softmax     | e^xᵢ/Σe^xⱼ          | (0,1)     | —                  | Multi-class output

Dead ReLU: neuron always gets negative input → gradient always 0 → never updates
Fix: use smaller learning rate, Leaky ReLU, careful initialization

GELU is preferred in modern transformers (BERT, GPT) — smooth, non-monotonic
```

### 7.4 Weight Initialization

```python
# Why initialization matters: controls initial signal magnitude through layers

# Xavier/Glorot (sigmoid/tanh):
# W ~ U[-√(6/(nᵢₙ+nₒᵤₜ)), +√(6/(nᵢₙ+nₒᵤₜ))]
# Var[W] = 2 / (nᵢₙ + nₒᵤₜ)
nn.init.xavier_uniform_(layer.weight)

# He/Kaiming (ReLU):
# Var[W] = 2/nᵢₙ  (accounts for ReLU halving the variance)
nn.init.kaiming_normal_(layer.weight, mode='fan_in', nonlinearity='relu')

# Why: want Var[output] ≈ Var[input] through each layer
# If var shrinks → vanishing gradients
# If var grows  → exploding gradients

# Residual networks help: output = input + small_perturbation
# Gradient flows through skip connection unchanged
```

---

## 8. Optimizers — From SGD to AdamW

### 8.1 SGD and Momentum

```python
# Pure SGD: noisy, slow convergence in ravines
# w ← w - α · ∇L(w; xᵢ, yᵢ)

# SGD with Momentum: accumulate velocity
# v ← β·v + (1-β)·∇L      (or v ← β·v + ∇L)
# w ← w - α·v

# Nesterov Momentum (better): gradient at lookahead position
# v ← β·v + ∇L(w - β·v)   (gradient at where we're going)
# w ← w - α·v

optimizer = torch.optim.SGD(
    model.parameters(),
    lr=0.01,
    momentum=0.9,      # typical
    nesterov=True,
    weight_decay=1e-4
)
```

### 8.2 Adam

```python
# Adaptive learning rates per parameter + momentum
# m ← β₁·m + (1-β₁)·g        (first moment — mean)
# v ← β₂·v + (1-β₂)·g²       (second moment — uncentered variance)
# m̂ = m/(1-β₁ᵗ)              (bias correction)
# v̂ = v/(1-β₂ᵗ)              (bias correction)
# w ← w - α · m̂/(√v̂ + ε)

# Defaults: β₁=0.9, β₂=0.999, ε=1e-8, α=1e-3
# Intuition: parameters with consistent gradients get larger effective lr
#            parameters with noisy gradients get smaller effective lr

# Adam vs SGD:
# Adam:  faster convergence, less sensitive to lr, worse generalization
# SGD+M: slower convergence, better generalization, needs lr tuning
# Rule: Adam for transformers/research; SGD+M for computer vision production

optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, betas=(0.9, 0.999))
```

### 8.3 AdamW

```python
# Problem with Adam + L2 loss: L2 gets scaled by 1/√v̂ (adaptive lr)
# Large gradient params → large v̂ → small L2 effect → unfair regularization

# AdamW fix: decouple weight decay from gradient update
# m̂ = ...; v̂ = ...
# w ← w - α · m̂/(√v̂ + ε) - α·λ·w    ← weight decay added separately

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-3,
    weight_decay=0.01  # typical for transformers
)
```

### 8.4 Learning Rate Schedules

```python
# Warmup + Cosine decay (standard for transformers)
from torch.optim.lr_scheduler import OneCycleLR, CosineAnnealingLR

# OneCycleLR: warmup then cosine decay (trains fast, good generalization)
scheduler = OneCycleLR(optimizer, max_lr=0.01, epochs=100, steps_per_epoch=len(loader))

# Cosine annealing
scheduler = CosineAnnealingLR(optimizer, T_max=100, eta_min=1e-6)

# Linear warmup + cosine decay (GPT-style)
def lr_lambda(step):
    warmup_steps = 1000
    if step < warmup_steps:
        return step / warmup_steps
    progress = (step - warmup_steps) / (total_steps - warmup_steps)
    return 0.5 * (1 + math.cos(math.pi * progress))

scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

# Why warmup? Adam's second moment (v) starts at 0 → large initial steps → instability
# Warmup lets v estimates stabilize before full learning rate
```

### 8.5 Gradient Clipping

```python
# Exploding gradients: especially in RNNs
# Clip by global norm: scale gradients so total norm ≤ threshold

torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

# Why by norm (not value): preserves gradient direction
# Typical: max_norm=1.0 for Transformers, 5.0 for RNNs
```

---

## 9. CNNs, RNNs, LSTMs

### 9.1 CNN Fundamentals

```python
# Convolution: slide filter over input, compute dot product + bias
# Output size: (W - F + 2P) / S + 1  (W=input, F=filter, P=padding, S=stride)

# Properties:
#   Local connectivity: each neuron sees only local region (receptive field)
#   Weight sharing:     same filter applied everywhere → fewer parameters
#   Translation equivariance: shifted input → shifted output (not invariant)
#   Translation invariance: achieved by pooling

# Receptive field with L layers of F×F kernels:
# RF = 1 + L(F-1)   (without strides)

# Dilated convolutions: insert gaps in filter → larger RF without more params
# Stride 2 convolution: downsample + extract features (preferred over max pool in modern CNNs)

import torch.nn as nn

class ConvBlock(nn.Module):
    def __init__(self, in_c, out_c, kernel=3, stride=1):
        super().__init__()
        self.conv = nn.Conv2d(in_c, out_c, kernel, stride, padding=kernel//2, bias=False)
        self.bn   = nn.BatchNorm2d(out_c)
        self.act  = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.act(self.bn(self.conv(x)))

# ResNet skip connection (key to training deep nets)
class ResBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = ConvBlock(channels, channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn2   = nn.BatchNorm2d(channels)

    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.bn2(self.conv2(out))
        return torch.relu(out + identity)  # residual connection
```

### 9.2 RNNs and Vanishing Gradients

```
RNN: hₜ = tanh(Wₕhₜ₋₁ + Wₓxₜ + b)
     yₜ = Wyₕhₜ

Backprop through time (BPTT):
∂L/∂h₀ = ∂L/∂hₙ · ∏ₜ₌₁ⁿ ∂hₜ/∂hₜ₋₁

Each ∂hₜ/∂hₜ₋₁ = Wₕᵀ · diag(tanh'(hₜ))

If ||Wₕ|| < 1: gradients → 0 exponentially    (vanishing)
If ||Wₕ|| > 1: gradients → ∞ exponentially    (exploding)

Result: can't learn long-range dependencies
Fix for exploding: gradient clipping
Fix for vanishing: LSTM (gated memory), skip connections, Transformers
```

### 9.3 LSTM

```python
# LSTM: cell state (c) carries long-range information
# Gates control what to remember/forget/output

# Forget gate:  fₜ = σ(Wf·[hₜ₋₁, xₜ] + bf)    — what to forget from cell
# Input gate:   iₜ = σ(Wi·[hₜ₋₁, xₜ] + bi)    — what new info to add
# Cell update:  c̃ₜ = tanh(Wc·[hₜ₋₁, xₜ] + bc) — candidate cell state
# Cell state:   cₜ = fₜ ⊙ cₜ₋₁ + iₜ ⊙ c̃ₜ      — additive update (not multiplicative!)
# Output gate:  oₜ = σ(Wo·[hₜ₋₁, xₜ] + bo)    — what to expose from cell
# Hidden state: hₜ = oₜ ⊙ tanh(cₜ)

# Why additive cell state update solves vanishing gradients:
# ∂cₜ/∂cₜ₋₁ = fₜ   (just the forget gate, not multiplicative chain)
# Gradient flows through cell state relatively unchanged

# GRU (simpler, often competitive):
# zₜ = σ(Wz·[hₜ₋₁, xₜ])    — update gate
# rₜ = σ(Wr·[hₜ₋₁, xₜ])    — reset gate
# h̃ₜ = tanh(W·[rₜ⊙hₜ₋₁, xₜ])
# hₜ = (1-zₜ)⊙hₜ₋₁ + zₜ⊙h̃ₜ
# Merges cell and hidden state → fewer parameters than LSTM

lstm = nn.LSTM(input_size=128, hidden_size=256, num_layers=2, 
               dropout=0.3, bidirectional=True, batch_first=True)
output, (hn, cn) = lstm(x)
```

---

## 10. Attention & Transformers

### 10.1 Scaled Dot-Product Attention

```python
import torch
import torch.nn.functional as F
import math

def attention(Q, K, V, mask=None):
    """
    Q, K, V: (batch, heads, seq_len, d_k)

    Attention(Q,K,V) = softmax(QKᵀ / √d_k) · V
    """
    d_k = Q.shape[-1]
    scores = Q @ K.transpose(-2, -1) / math.sqrt(d_k)

    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)  # -inf before softmax

    weights = F.softmax(scores, dim=-1)  # attention distribution
    return weights @ V, weights

# Why scale by √d_k?
# Q·K dot products grow with d_k
# Large values → softmax saturation → near-zero gradients
# Scaling keeps variance at 1: Var[q·k] = d_k → Var[q·k/√d_k] = 1
```

### 10.2 Multi-Head Attention

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        assert d_model % num_heads == 0
        self.d_k = d_model // num_heads
        self.h   = num_heads
        self.Wq  = nn.Linear(d_model, d_model)
        self.Wk  = nn.Linear(d_model, d_model)
        self.Wv  = nn.Linear(d_model, d_model)
        self.Wo  = nn.Linear(d_model, d_model)

    def forward(self, q, k, v, mask=None):
        B, T, _ = q.shape
        Q = self.Wq(q).view(B, T, self.h, self.d_k).transpose(1, 2)  # (B,H,T,dk)
        K = self.Wk(k).view(B, -1, self.h, self.d_k).transpose(1, 2)
        V = self.Wv(v).view(B, -1, self.h, self.d_k).transpose(1, 2)

        out, weights = attention(Q, K, V, mask)
        out = out.transpose(1, 2).contiguous().view(B, T, -1)  # concat heads
        return self.Wo(out)

# Why multiple heads?
# Different heads learn different types of attention:
# head 1: syntactic dependencies
# head 2: coreference
# head 3: positional relationships
# etc.
```

### 10.3 Transformer Architecture

```
Encoder block:
  x → LayerNorm → MultiHeadAttn → + x (residual) → LayerNorm → FFN → + x

Decoder block:
  x → LayerNorm → Masked MultiHeadAttn → + x
    → LayerNorm → Cross-Attn(Q=dec, K=V=enc) → + x
    → LayerNorm → FFN → + x

FFN: two linear layers with GELU/ReLU: FFN(x) = max(0, xW₁+b₁)W₂+b₂
     d_model → 4·d_model → d_model  (4x expansion typical)

Positional Encoding (sinusoidal):
PE(pos, 2i)   = sin(pos/10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos/10000^(2i/d_model))

Why: encodes relative positions via dot products
     PE(pos+k) can be expressed as linear function of PE(pos)
     Learned PE often better in practice (BERT, GPT use learned)
```

### 10.4 Attention Complexity & Efficient Variants

```
Standard attention: O(n²d) time, O(n²) space (n = sequence length)
Bottleneck for long sequences

Efficient Attention Variants:
─────────────────────────────────────────────────────────
Sparse Attention   | O(n√n) | attend to fixed sparse pattern
Longformer         | O(n)   | local window + global tokens
BigBird            | O(n)   | random + local + global
Linformer          | O(n)   | low-rank approximation of K,V
Performer          | O(n)   | kernel trick, unbiased estimator of softmax
FlashAttention     | O(n²)  | same complexity, IO-aware (tiling), 2-4x faster in practice
FlashAttention-2   | O(n²)  | better parallelism, ~2x faster than FA-1
Ring Attention     | O(n²)  | distributed attention across devices

FlashAttention key insight:
  Fuses attention into single CUDA kernel
  Avoids materializing full n×n attention matrix in HBM
  Uses SRAM for tiling → memory bandwidth bound → massive speedup
```

### 10.5 KV Cache (Inference Optimization)

```python
# During autoregressive decoding, each new token attends to all previous tokens
# Naive: recompute K,V for all previous tokens at each step → O(n²) per generation

# KV Cache: store computed K,V for past tokens, only compute for new token
# K_cache: [B, H, past_len, dk]  → append new K at each step
# Memory: 2 × B × H × L × dk × precision_bytes per layer

# For GPT-3 (175B): KV cache per token ≈ 0.8MB
# 1000 token context, batch=1: ~0.8GB for KV cache

# Optimizations:
# Multi-Query Attention (MQA): share K,V across heads → H× memory reduction
# Grouped-Query Attention (GQA): G groups of heads share K,V (between MHA and MQA)
# → LLaMA 2, Mistral use GQA for efficient long-context inference
```

---

## 11. Embeddings & Representation Learning

### 11.1 Word2Vec

```python
# Skip-gram: predict context words from center word
# CBOW: predict center word from context words

# Objective (skip-gram with negative sampling):
# L = Σ [log σ(vₒ·vᵥ) + Σₖ Eᵥₙₑ₉[log σ(-vₙ·vᵥ)]]

# Properties of learned embeddings:
# king - man + woman ≈ queen  (linear analogy)
# Cosine similarity captures semantic relatedness

# Why it works: co-occurrence → similar contexts → similar vectors
# Dimensionality: 100-300d typical, diminishing returns beyond 300d

from gensim.models import Word2Vec

model = Word2Vec(
    sentences,          # list of tokenized sentences
    vector_size=100,
    window=5,           # context window size
    min_count=5,        # ignore words with freq < min_count
    sg=1,               # 1=skip-gram, 0=CBOW
    negative=5,         # negative samples
    workers=4
)

model.wv.most_similar("king")
model.wv.similarity("cat", "dog")
```

### 11.2 Contrastive Learning (SimCLR, CLIP)

```python
# Self-supervised: learn representations by pulling augmented views together

# InfoNCE loss (NT-Xent):
# L = -log[exp(sim(zᵢ,zⱼ)/τ) / Σₖ exp(sim(zᵢ,zₖ)/τ)]
# τ = temperature (smaller → sharper distribution)

def nt_xent_loss(z1, z2, temperature=0.5):
    """z1, z2: (batch, d) normalized embeddings of two views"""
    B = z1.shape[0]
    z = torch.cat([z1, z2], dim=0)  # (2B, d)
    sim = F.cosine_similarity(z.unsqueeze(1), z.unsqueeze(0), dim=2)  # (2B, 2B)

    # Labels: positive pairs are (i, i+B) and (i+B, i)
    labels = torch.arange(B, device=z.device)
    labels = torch.cat([labels + B, labels])  # (2B,)

    # Remove self-similarities
    mask = torch.eye(2*B, dtype=bool, device=z.device)
    sim = sim.masked_fill(mask, -1e9)

    return F.cross_entropy(sim / temperature, labels)

# CLIP: cross-modal contrastive (image + text)
# Match image embedding with its text description
# Enables zero-shot classification: compare image to text "a photo of a {class}"
```

### 11.3 Embedding for Retrieval (ANN)

```python
# Approximate Nearest Neighbor (ANN) at scale
# Exact KNN: O(Nd) per query — too slow for large N

# FAISS (Facebook AI Similarity Search)
import faiss
import numpy as np

d = 128    # embedding dimension
N = 10**6  # number of vectors

# Flat (exact, slow): O(N·d) per query
index = faiss.IndexFlatL2(d)
index.add(embeddings.astype('float32'))
D, I = index.search(query.astype('float32'), k=10)

# IVF (inverted file, ~100x faster): quantize into clusters, search subset
nlist = 1000  # number of Voronoi cells
quantizer = faiss.IndexFlatL2(d)
index = faiss.IndexIVFFlat(quantizer, d, nlist)
index.train(embeddings)
index.add(embeddings)
index.nprobe = 10  # search 10 nearest cells (accuracy vs speed tradeoff)

# HNSW (hierarchical navigable small world): graph-based, no training needed
index = faiss.IndexHNSWFlat(d, 32)  # 32 = num neighbors in graph
index.add(embeddings)

# ScaNN, Annoy, hnswlib are alternatives
# For production: Pinecone, Weaviate, Milvus, pgvector
```

---

## 12. Unsupervised Learning

### 12.1 K-Means

```python
# Algorithm:
# 1. Initialize k centroids (random, K-means++, etc.)
# 2. Assign each point to nearest centroid
# 3. Recompute centroids as mean of assigned points
# 4. Repeat until convergence

# Objective: minimize within-cluster sum of squares (WCSS)
# Σᵢ Σₓ∈Cᵢ ||x - μᵢ||²

# K-means++: initialize centroids with probability ∝ d(x, nearest centroid)²
# → better initialization, faster convergence, better final solution

from sklearn.cluster import KMeans

model = KMeans(n_clusters=5, init='k-means++', n_init=10)
labels = model.fit_predict(X)

# Choosing k:
# Elbow method: plot WCSS vs k, look for "elbow"
# Silhouette score: s(i) = (b - a) / max(a, b), range [-1, 1], higher is better
from sklearn.metrics import silhouette_score
score = silhouette_score(X, labels)

# Limitations: assumes spherical clusters, sensitive to outliers, needs k
# Use DBSCAN for arbitrary shapes; GMM for soft assignments
```

### 12.2 PCA

```python
# Principal Component Analysis: find directions of maximum variance
# 1. Standardize: X_centered = X - mean(X)
# 2. Covariance matrix: C = X_centered.T @ X_centered / (n-1)
# 3. Eigendecomposition: C = QΛQᵀ
# 4. Sort eigenvectors by eigenvalue (descending)
# 5. Project: X_reduced = X_centered @ Q[:, :k]

# Equivalently via SVD: X = UΣVᵀ, principal components = right singular vectors V

from sklearn.decomposition import PCA

pca = PCA(n_components=0.95)  # keep 95% of variance
X_reduced = pca.fit_transform(X)
print(pca.explained_variance_ratio_)

# PCA limitations:
# Linear only → use UMAP/t-SNE for nonlinear structure
# Global structure: PCA preserves, t-SNE does NOT, UMAP partially does

# When to use what:
# PCA: preprocessing, feature extraction, remove noise, multicollinearity
# t-SNE: visualization only (2D/3D), not for distance interpretation
# UMAP: visualization + preserves more global structure, faster than t-SNE
```

### 12.3 Gaussian Mixture Models

```python
# Soft clustering: each point has probability of belonging to each cluster
# Assumes data from K Gaussians: p(x) = Σₖ πₖ N(x; μₖ, Σₖ)

# EM Algorithm:
# E-step: γᵢₖ = πₖN(xᵢ;μₖ,Σₖ) / Σⱼπⱼ N(xᵢ;μⱼ,Σⱼ)  (responsibilities)
# M-step: μₖ = Σᵢγᵢₖxᵢ / Nₖ,   Σₖ = Σᵢγᵢₖ(xᵢ-μₖ)(xᵢ-μₖ)ᵀ/Nₖ,  πₖ = Nₖ/N

from sklearn.mixture import GaussianMixture

gmm = GaussianMixture(n_components=3, covariance_type='full')
gmm.fit(X)
labels = gmm.predict(X)
probs  = gmm.predict_proba(X)  # soft assignments

# GMM vs K-means:
# GMM: soft assignments, elliptical clusters, probabilistic
# K-means: special case of GMM with Σ = σ²I, hard assignments

# Model selection: BIC = -2·log(L) + k·log(n)  (lower is better)
bic_scores = [GaussianMixture(n).fit(X).bic(X) for n in range(2, 10)]
```

---

## 13. Probability & Statistics for ML

### 13.1 Distributions You Must Know

```
Distribution   | Use in ML
───────────────┼────────────────────────────────────────────────
Gaussian       | Noise model, weight prior (Ridge), PCA
Bernoulli      | Binary labels → logistic regression
Categorical    | Multi-class labels → softmax
Beta           | Prior on probabilities (conjugate to Bernoulli)
Dirichlet      | Prior on categorical distributions (topic models)
Poisson        | Count data (clicks, events)
Exponential    | Time between events
Laplace        | Prior on weights → L1/Lasso
Gamma          | Bayesian deep learning, prior on precision
Log-Normal     | When log(X) is Gaussian (income, file sizes)

CLT: sum of n iid rvs → Gaussian as n→∞ (regardless of distribution)
LLN: sample mean → population mean as n→∞
```

### 13.2 Hypothesis Testing

```python
# Type I error (α): false positive (reject H₀ when true) — "significance level"
# Type II error (β): false negative (fail to reject H₀ when false)
# Power = 1 - β: probability of correctly detecting true effect

# p-value: probability of observing test statistic at least as extreme as observed,
#          ASSUMING H₀ is true. NOT P(H₀ is true | data).

# A/B test (z-test for proportions):
from scipy import stats

control = (1000, 50)    # (n, conversions)
treatment = (1000, 65)

p1 = control[1] / control[0]
p2 = treatment[1] / treatment[0]
p_pooled = (control[1] + treatment[1]) / (control[0] + treatment[0])

se = (p_pooled * (1 - p_pooled) * (1/control[0] + 1/treatment[0])) ** 0.5
z = (p2 - p1) / se
p_value = 2 * (1 - stats.norm.cdf(abs(z)))  # two-tailed

# Multiple comparison problem:
# If testing 20 metrics with α=0.05, expect ~1 false positive
# Bonferroni: α_corrected = α / m   (conservative)
# Benjamini-Hochberg: FDR control   (less conservative, preferred)
```

### 13.3 Bayesian Inference

```python
# Prior → Likelihood → Posterior → Posterior Predictive

# Conjugate priors: posterior has same distribution as prior
# Beta-Binomial: Beta prior on p + Binomial likelihood → Beta posterior
# Prior: p ~ Beta(α, β)
# Likelihood: X | p ~ Binomial(n, p)
# Posterior: p | X ~ Beta(α + X, β + n - X)

from scipy.stats import beta

# Click-through rate estimation
# Prior: 1 click, 1 no-click (weak uniform prior = Beta(1,1))
# Data: 40 clicks, 60 no-clicks
posterior = beta(a=1+40, b=1+60)
print(f"Mean CTR: {posterior.mean():.3f}")
print(f"95% CI: {posterior.ppf([0.025, 0.975])}")

# Bayesian vs Frequentist for ML:
# Frequentist MLE: fast, no prior needed, point estimate
# Bayesian MAP: includes prior knowledge, still point estimate
# Full Bayesian: posterior distribution → uncertainty quantification, more expensive
```

---

## 14. Feature Engineering & Selection

### 14.1 Numerical Features

```python
import numpy as np
from sklearn.preprocessing import (StandardScaler, MinMaxScaler,
                                   PowerTransformer, QuantileTransformer)

# Standardization: mean=0, std=1 (required for SVM, PCA, logistic regression)
scaler = StandardScaler()
X_std = scaler.fit_transform(X_train)   # fit on TRAIN only, transform both

# Min-Max: [0,1] range (required for neural networks with sigmoid/tanh output)
scaler = MinMaxScaler()

# Log transform: for right-skewed features (income, clicks)
X_log = np.log1p(X)  # log(1+x) handles zeros

# Box-Cox / Yeo-Johnson: parametric power transformation
pt = PowerTransformer(method='yeo-johnson')  # handles negatives too

# Quantile transform: maps to uniform or Gaussian (robust to outliers)
qt = QuantileTransformer(output_distribution='normal')

# Outlier handling:
# Clip to percentile
X_clipped = np.clip(X, X.quantile(0.01), X.quantile(0.99))

# Robust scaling: uses IQR (robust to outliers)
from sklearn.preprocessing import RobustScaler
scaler = RobustScaler()  # (x - median) / IQR

# Binning (discretization): capture non-linear relationships for linear models
from sklearn.preprocessing import KBinsDiscretizer
est = KBinsDiscretizer(n_bins=5, encode='onehot', strategy='quantile')
```

### 14.2 Categorical Features

```python
# One-hot encoding: k categories → k binary features (or k-1 to avoid multicollinearity)
pd.get_dummies(df['color'], drop_first=True)

# Label encoding: ordered categories only (not for tree models — implies order)
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder

# Target encoding: replace category with mean target (risk: leakage!)
from category_encoders import TargetEncoder
enc = TargetEncoder(smoothing=10)  # smoothing avoids overfitting rare categories
# Target encoding = (count × category_mean + smooth × global_mean) / (count + smooth)

# Frequency/count encoding: replace with frequency in training set
freq = df['category'].value_counts() / len(df)
df['cat_enc'] = df['category'].map(freq)

# High-cardinality (user IDs, item IDs):
# Option 1: Entity embeddings (learn in neural network)
# Option 2: Hashing trick (hash to fixed-size feature vector — may collide)
from sklearn.feature_extraction import FeatureHasher

# Handling new categories at inference:
# OHE: column of zeros (or separate 'unknown' category)
# Target encoding: use global mean
# Embeddings: random init or global average embedding
```

### 14.3 Feature Selection

```python
from sklearn.feature_selection import (SelectKBest, mutual_info_classif,
                                        RFE, SelectFromModel)

# Filter methods: score each feature independently
selector = SelectKBest(mutual_info_classif, k=20)
X_sel = selector.fit_transform(X, y)

# Wrapper methods: use model to score feature subsets
# Recursive Feature Elimination (RFE)
from sklearn.linear_model import LogisticRegression
rfe = RFE(LogisticRegression(), n_features_to_select=20)
X_sel = rfe.fit_transform(X, y)

# Embedded methods: model learns feature importance during training
# L1 regularization (Lasso): automatically zeros out uninformative features
# Tree-based feature importance (but biased toward high-cardinality!)
from sklearn.ensemble import RandomForestClassifier
sel = SelectFromModel(RandomForestClassifier(), threshold='mean')
X_sel = sel.fit_transform(X, y)

# Variance Inflation Factor (VIF): detect multicollinearity
from statsmodels.stats.outliers_influence import variance_inflation_factor
vif = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
# VIF > 5-10: consider removing or combining collinear features
```

---

## 15. Model Evaluation — Beyond Accuracy

### 15.1 Classification Metrics

```python
from sklearn.metrics import (classification_report, roc_auc_score,
                              average_precision_score, confusion_matrix)
import numpy as np

# Confusion Matrix:
#                Predicted Positive  Predicted Negative
# Actual Positive      TP                  FN
# Actual Negative      FP                  TN

# Core metrics:
# Precision = TP / (TP + FP)   ← of all predicted positive, how many are?
# Recall    = TP / (TP + FN)   ← of all actual positive, how many caught?
# F1        = 2·P·R / (P+R)   ← harmonic mean (penalizes extreme imbalance)
# F-beta    = (1+β²)·P·R / (β²·P + R)  ← β>1 weights recall more

# ROC-AUC: probability that a random positive ranks higher than random negative
# → threshold-independent
# → insensitive to class imbalance? NO — use PR-AUC for imbalanced data

y_prob = model.predict_proba(X_test)[:, 1]
print("ROC-AUC:", roc_auc_score(y_test, y_prob))
print("PR-AUC:",  average_precision_score(y_test, y_prob))

# When to use what:
# Accuracy: balanced classes, equal cost for FP/FN
# Precision: FP is costly (spam filter — don't block legitimate email)
# Recall:    FN is costly (cancer detection — don't miss actual cancer)
# F1:        imbalanced classes, similar FP/FN cost
# ROC-AUC:   overall ranking ability, balanced classes
# PR-AUC:    imbalanced classes, focus on positive class

# Cohen's Kappa: agreement above chance (useful for multi-class)
from sklearn.metrics import cohen_kappa_score
```

### 15.2 Regression Metrics

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

mse  = mean_squared_error(y_true, y_pred)
rmse = np.sqrt(mse)
mae  = mean_absolute_error(y_true, y_pred)   # robust to outliers
r2   = r2_score(y_true, y_pred)              # proportion of variance explained

# MAPE: percentage error (bad when y_true ≈ 0)
mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

# SMAPE: symmetric MAPE
smape = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred))) * 100

# Quantile loss (for prediction intervals):
def quantile_loss(y_true, y_pred, q):
    e = y_true - y_pred
    return np.mean(np.where(e >= 0, q * e, (q - 1) * e))
# q=0.5 → MAE; q=0.9 → penalizes underprediction 9x more
```

### 15.3 Cross-Validation Strategies

```python
from sklearn.model_selection import (KFold, StratifiedKFold, GroupKFold,
                                      TimeSeriesSplit, cross_val_score)

# Standard k-fold (no time structure, no groups)
cv = KFold(n_splits=5, shuffle=True, random_state=42)

# Stratified k-fold: maintain class proportions in each fold
cv = StratifiedKFold(n_splits=5, shuffle=True)

# Group k-fold: ensure all samples from a group are in same fold
# Use when: same user appears multiple times (prevent data leakage)
cv = GroupKFold(n_splits=5)
scores = cross_val_score(model, X, y, cv=cv, groups=user_ids)

# Time series: always train on past, test on future (no shuffle!)
tscv = TimeSeriesSplit(n_splits=5)
# Fold 1: train=[0:200],  test=[200:240]
# Fold 2: train=[0:240],  test=[240:280]
# Fold 3: train=[0:280],  test=[280:320] ...

# Nested CV: unbiased hyperparameter tuning + model evaluation
from sklearn.model_selection import GridSearchCV, cross_val_score
inner_cv = StratifiedKFold(n_splits=3)
outer_cv = StratifiedKFold(n_splits=5)

clf = GridSearchCV(model, param_grid, cv=inner_cv)
nested_scores = cross_val_score(clf, X, y, cv=outer_cv)
# Outer CV estimates generalization; inner CV selects hyperparams
```

---

## 16. Calibration & Uncertainty

### 16.1 Model Calibration

```python
# Well-calibrated model: predicted probability 0.8 → event occurs 80% of time
# Overconfident: predicted 0.9 → actual 0.7
# Underconfident: predicted 0.6 → actual 0.8

from sklearn.calibration import calibration_curve, CalibratedClassifierCV

# Check calibration
prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=10)
# Perfect calibration: diagonal line

# Fix calibration:
# Platt scaling (sigmoid): fit logistic regression on cv probs and true labels
# Isotonic regression: non-parametric, more flexible, needs more data
calibrated = CalibratedClassifierCV(base_estimator=model, method='sigmoid', cv=5)
calibrated.fit(X_train, y_train)

# Expected Calibration Error (ECE):
# ECE = Σ |Bₘ|/n · |acc(Bₘ) - conf(Bₘ)|
# Group predictions into bins, measure gap between confidence and accuracy

# Brier Score: MSE for probability predictions
from sklearn.metrics import brier_score_loss
brier = brier_score_loss(y_test, y_prob)
# Range [0,1], lower is better, 0.25 = random classifier on balanced data
```

### 16.2 Uncertainty Quantification

```python
# Epistemic uncertainty: model uncertainty (reducible with more data)
# Aleatoric uncertainty: data uncertainty (irreducible noise)

# MC Dropout: approximate Bayesian uncertainty
class MCDropoutModel(nn.Module):
    def __init__(self, dropout_rate=0.2):
        super().__init__()
        self.dropout = nn.Dropout(dropout_rate)
        self.fc = nn.Linear(128, 1)

    def forward(self, x):
        return self.fc(self.dropout(x))  # dropout active even at inference

def predict_with_uncertainty(model, x, n_samples=100):
    model.train()  # keep dropout active
    preds = torch.stack([model(x) for _ in range(n_samples)])
    return preds.mean(dim=0), preds.std(dim=0)  # mean, epistemic std

# Conformal Prediction: distribution-free prediction intervals
# Coverage guarantee: P(y ∈ Ĉ(x)) ≥ 1 - α for any data distribution
from mapie.regression import MapieRegressor
mapie = MapieRegressor(estimator=model, method='plus', cv=5)
mapie.fit(X_train, y_train)
y_pred, y_pis = mapie.predict(X_test, alpha=0.1)  # 90% prediction intervals
```

---

## 17. Recommendation Systems

### 17.1 Collaborative Filtering

```python
# User-based CF: similar users like similar items
# Item-based CF: similar items liked by similar users

# Matrix Factorization: decompose R(users×items) = U·Vᵀ
# Minimize: Σ(r,u,i) [rᵤᵢ - uᵤ·vᵢᵀ]² + λ(||U||² + ||V||²)

# ALS (Alternating Least Squares):
# Fix V, solve for U (closed-form): uᵤ = (VᵀV + λI)⁻¹ Vᵀrᵤ
# Fix U, solve for V (closed-form): vᵢ = (UᵀU + λI)⁻¹ Uᵀrᵢ

import implicit  # ALS for implicit feedback

model = implicit.als.AlternatingLeastSquares(
    factors=50,
    regularization=0.1,
    iterations=20,
    use_gpu=False
)
model.fit(item_user_matrix)  # sparse matrix: items × users
recommendations = model.recommend(user_id, user_items, N=10)

# Implicit vs Explicit feedback:
# Explicit: ratings (1-5 stars) — sparse, noisy, biased
# Implicit: clicks, purchases, view time — dense, but noisy (clicked ≠ liked)
```

### 17.2 Neural Collaborative Filtering

```python
class NCF(nn.Module):
    def __init__(self, n_users, n_items, emb_dim=32, layers=[64, 32, 16]):
        super().__init__()
        # GMF path
        self.user_emb_gmf = nn.Embedding(n_users, emb_dim)
        self.item_emb_gmf = nn.Embedding(n_items, emb_dim)

        # MLP path
        self.user_emb_mlp = nn.Embedding(n_users, emb_dim)
        self.item_emb_mlp = nn.Embedding(n_items, emb_dim)
        mlp_input = emb_dim * 2
        mlp_layers = []
        for out in layers:
            mlp_layers.extend([nn.Linear(mlp_input, out), nn.ReLU()])
            mlp_input = out
        self.mlp = nn.Sequential(*mlp_layers)

        # Output
        self.output = nn.Linear(emb_dim + layers[-1], 1)

    def forward(self, user_ids, item_ids):
        gmf = self.user_emb_gmf(user_ids) * self.item_emb_gmf(item_ids)  # element-wise product
        mlp_in = torch.cat([self.user_emb_mlp(user_ids), self.item_emb_mlp(item_ids)], dim=1)
        mlp_out = self.mlp(mlp_in)
        out = torch.cat([gmf, mlp_out], dim=1)
        return torch.sigmoid(self.output(out))
```

### 17.3 Two-Tower Models (Industry Scale)

```
Architecture:
  User Tower: user features → user embedding
  Item Tower: item features → item embedding
  Score: dot product of user_emb · item_emb

Training: contrastive loss — match user to positive items, push away from negatives

Serving:
  Offline: precompute all item embeddings
  ANN index: build FAISS/ScaNN index of item embeddings
  Online: compute user embedding → query ANN → retrieve top-K candidates
  → Re-ranking with expensive model (cross-encoder style)

Negative sampling strategies (critical for quality):
  In-batch negatives: treat other positives in batch as negatives (fast, biased)
  Random negatives: sample random items (too easy)
  Hard negatives: items similar to positive but not clicked (harder, better)
  Mixed: combine random + hard

Production stack:
  Candidate generation (two-tower) → Filtering (business rules) →
  Scoring (expensive features, cross-encoder) → Re-ranking (diversity, freshness)
```

---

## 18. Large Language Models — Production Knowledge

### 18.1 Pre-training, Fine-tuning, RLHF

```
Pre-training: predict next token on massive corpus (self-supervised)
  Loss: L = -Σₜ log P(xₜ | x₁...xₜ₋₁)
  Scale: tokens processed ≈ 100B-10T; compute ≈ petaflop-days

Fine-tuning approaches:
  Full fine-tuning:   update all weights (expensive, catastrophic forgetting risk)
  LoRA:              inject low-rank adapters (B·A where rank r << d)
  Prefix tuning:     prepend learnable tokens to input
  Prompt tuning:     learn soft prompt tokens only (fewest params)
  QLoRA:             4-bit quantized base model + LoRA

RLHF (Reinforcement Learning from Human Feedback):
  Step 1: Supervised Fine-Tuning (SFT) on human demonstrations
  Step 2: Train Reward Model (RM) on human comparisons of outputs
  Step 3: PPO: optimize LLM to maximize reward - KL(LLM || SFT)
  
  KL penalty prevents LLM from gaming reward model (reward hacking)
  
DPO (Direct Preference Optimization):
  Skip reward model — directly optimize on preference pairs
  Simpler, stable, competitive with RLHF
```

### 18.2 LoRA in Detail

```python
# Problem: fine-tuning 70B model → 70B gradient states → too expensive
# LoRA: weight change ΔW = A·B, where A∈R^(d×r), B∈R^(r×k), r << min(d,k)
# Freeze original weights, train only A and B

# Parameters saved: instead of d×k, train d×r + r×k = r(d+k)
# r=16, d=k=4096: 16×4096×2 = 131K vs 4096²=16M → 120x fewer params

class LoRALayer(nn.Module):
    def __init__(self, original_layer, rank=4, alpha=16):
        super().__init__()
        d, k = original_layer.weight.shape
        self.original = original_layer
        self.original.weight.requires_grad = False   # freeze base

        # Initialize: A ~ N(0,1), B = 0 (so ΔW=0 at start)
        self.A = nn.Parameter(torch.randn(d, rank) * 0.01)
        self.B = nn.Parameter(torch.zeros(rank, k))
        self.scale = alpha / rank   # alpha controls LoRA contribution magnitude

    def forward(self, x):
        base = self.original(x)
        lora = x @ self.A @ self.B * self.scale
        return base + lora
```

### 18.3 Quantization

```
FP32: 4 bytes/param  → 70B model = 280GB
FP16/BF16: 2 bytes   → 140GB
INT8: 1 byte         → 70GB
INT4: 0.5 bytes      → 35GB

Post-Training Quantization (PTQ):
  GPTQ: weight-only quantization using second-order information (Hessian)
  AWQ:  activation-aware weight quantization (protect salient weights)
  GGUF: format for CPU inference (llama.cpp)

Quantization-Aware Training (QAT):
  Simulate quantization during training → better accuracy
  Straight-Through Estimator: pass gradients through rounding operation

BF16 vs FP16:
  BF16: same exponent bits as FP32 (8) → same dynamic range, less precision
  FP16: more precision, smaller range → NaN issues with large values
  Use BF16 for training (stable), FP16 for inference (supported on more hardware)
```

### 18.4 Inference Optimization

```
Throughput vs Latency:
  Throughput: tokens/second across all requests (batching helps)
  Latency: time-to-first-token + time-per-output-token (user-facing)

KV Cache Management:
  PagedAttention (vLLM): manage KV cache like OS virtual memory
  - KV cache in non-contiguous blocks
  - Copy-on-write for shared prefixes (speculative decoding, beam search)
  - Near-zero memory waste
  - Enables higher batch sizes → higher GPU utilization

Speculative Decoding:
  Small "draft" model generates k tokens → large model verifies in parallel
  Accepted tokens: O(k) speedup when draft is often correct
  Rejected: fall back to large model's token
  Speedup: 2-3x for large models

Continuous Batching:
  Dynamic batching: don't wait for slowest request to finish
  Swap completed requests out, add new ones mid-generation
  → dramatically improves throughput (used in vLLM, TGI)

Flash Attention:
  Tiling to avoid materializing full attention matrix
  2-4x speedup, O(n) memory vs O(n²)
  Industry standard for LLM training
```

---

## 19. ML System Design

### 19.1 Design Framework

```
1. Clarify requirements
   → Functional: What does it do?
   → Non-functional: latency SLA, scale (QPS, users), freshness requirements
   → Success metrics: online (revenue, CTR) + offline (AUC, NDCG)

2. Problem formulation
   → Supervised/unsupervised? Regression/classification/ranking?
   → Single model or pipeline?
   → What's the label? How is training data collected?

3. Data collection & pipeline
   → Sources, volume, freshness, labeling strategy
   → Feature store: online (Redis) + offline (S3/Hive)
   → Data validation (schema, distribution drift)

4. Feature engineering
   → User features, item features, context features, cross features
   → Handling: missing values, new categories, data leakage

5. Model selection & training
   → Simple baseline first
   → Offline evaluation strategy (cross-val, temporal split)
   → Training infrastructure (distributed training)

6. Serving & deployment
   → Batch vs real-time inference
   → Model serving: TorchServe, Triton, SageMaker
   → Canary deployment, shadow mode, A/B testing

7. Monitoring
   → Data drift (feature distributions)
   → Concept drift (model performance degrades)
   → Alerting, retraining triggers
```

### 19.2 Designing a Recommendation System (Instagram Feed)

```
Scale: 1B users, 100M content pieces/day, <100ms latency

Pipeline:
  Candidate Generation (fast, recall-focused):
    - Two-tower model: user_emb · item_emb
    - ANN retrieval: top 1000 candidates per user
    - Multiple towers: interest model, social graph, trending

  Ranking (slow, precision-focused):
    - Gradient boosted trees or deep model
    - Features: user-item interaction, temporal, social, content
    - Outputs: P(like), P(comment), P(share), P(time_spent)
    - Combine: value = w₁P(like) + w₂P(comment) + ... (weighted sum)

  Re-ranking (business rules):
    - Diversity: not 5 posts from same creator
    - Freshness: boost new content
    - Safety: down-rank flagged content
    - Ads: inject at specific positions

Feature Store:
  Offline (Spark + S3): user historical features, computed daily
  Online (Redis): real-time features, sub-ms lookup
  Feature server: join offline + online at request time

Training:
  Label: engagement (1), no engagement (0), delayed reward (long-form video)
  Frequency: retrain daily; lightweight online updates hourly
  Freshness: separate recency tower for new items (cold start)

Evaluation:
  Offline: AUC, NDCG, coverage
  Online: A/B test → CTR, session time, return rate
```

### 19.3 Designing a Fraud Detection System

```
Challenges:
  - Extreme class imbalance (fraud: 0.01-0.1%)
  - Concept drift (fraud patterns change constantly)
  - Low latency (<100ms for transaction approval)
  - Ground truth delay (chargebacks take weeks)
  - Adversarial: fraudsters adapt to model

Label strategy:
  - Chargeback data (gold labels, delayed)
  - Rule-based labels (weak supervision, immediate)
  - Human review labels (expensive, high quality)

Model architecture:
  - Real-time: gradient boosting (XGBoost) on transaction features
  - Graph: GNN on transaction graph (shared device/card/email)
  - Sequential: LSTM on user transaction history
  - Ensemble: combine scores

Features:
  - Transaction: amount, merchant category, time, location
  - User history: velocity (txn count last 1h/24h/7d), typical behavior
  - Device/session: IP, device fingerprint, session length
  - Graph: connected accounts, shared attributes

Imbalance handling:
  - Down-sample majority in training (keep all fraud, sample legit)
  - Class weights: class_weight = {0: 1, 1: 100}
  - SMOTE (synthetic minority oversampling)
  - Threshold tuning for business requirement (FPR vs FNR tradeoff)

Deployment:
  - Shadow mode: run new model alongside rules, compare alerts
  - Canary: route 5% traffic to new model
  - Champion-challenger: A/B test with rollback

Monitoring:
  - Score distribution shift → data drift
  - Alert rate change → model drift
  - Fraud rate change → concept drift
  - Retrain trigger: weekly or on drift detection
```

---

## 20. MLOps & Production Failures

### 20.1 Data Leakage — The Silent Killer

```python
# Type 1: Target leakage — future information in features
# Example: predicting loan default with "payment_status" (only known after default)
# Fix: think carefully about what's available at prediction time

# Type 2: Train-test leakage — test data influences training
# Example: standardizing with global stats (includes test)
# WRONG:
scaler = StandardScaler().fit(X)  # includes test data
X_train_scaled = scaler.transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# CORRECT:
scaler = StandardScaler().fit(X_train)  # fit on TRAIN only
X_train_scaled = scaler.transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# Type 3: Group leakage — same entity in train and test
# Example: same user's transactions in both (model learns user identity)
# Fix: GroupKFold, user-level splits

# Type 4: Temporal leakage — future time periods in training
# Fix: strict time-based splits, no shuffle for time series
```

### 20.2 Training-Serving Skew

```
Problem: model trained on one data distribution, serves another
  - Training: batch offline features; Serving: real-time features
  - Different preprocessing code paths
  - Stale features at serving time

Fix:
  - Feature Store: single source of truth for both training and serving
  - Training: retrieve features from same store used in serving
  - Log features + predictions at serving time → use as training data
  - Continuous validation: compare training distribution to serving distribution

Signs of skew:
  - Model performs well offline, poorly online
  - Feature distribution shift between logged data and batch data
  - Predictions cluster at unusual values at serving time
```

### 20.3 Concept Drift Detection

```python
# Population Stability Index (PSI): detect feature distribution shift
def psi(expected, actual, buckets=10):
    """PSI < 0.1: no shift; 0.1-0.2: slight; > 0.2: significant"""
    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets+1))
    exp_pct = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    act_pct = np.histogram(actual,   bins=breakpoints)[0] / len(actual)
    exp_pct = np.where(exp_pct == 0, 0.0001, exp_pct)
    act_pct = np.where(act_pct == 0, 0.0001, act_pct)
    return np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))

# Statistical tests for drift
from scipy.stats import ks_2samp, chi2_contingency

# Kolmogorov-Smirnov test (continuous features)
stat, p_value = ks_2samp(train_feature, serving_feature)
if p_value < 0.05:
    alert("Distribution shift detected!")

# Model performance monitoring (when labels available)
# Track: sliding window AUC, precision, recall
# Alert when rolling metric drops below threshold

# Evidently AI: production-ready drift detection library
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
report = Report(metrics=[DataDriftPreset()])
report.run(reference_data=train_df, current_data=serving_df)
```

### 20.4 Distributed Training

```python
# Data Parallelism: same model, different data shards per device
# DDP (DistributedDataParallel): gradient allreduce across GPUs

import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

def train(rank, world_size):
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    model = MyModel().to(rank)
    model = DDP(model, device_ids=[rank])

    sampler = DistributedSampler(dataset, num_replicas=world_size, rank=rank)
    loader  = DataLoader(dataset, sampler=sampler, batch_size=32)

    for batch in loader:
        out  = model(batch)
        loss = criterion(out, batch.labels)
        loss.backward()           # gradients averaged across all GPUs
        optimizer.step()

# Model Parallelism: model too large for one GPU → split across GPUs
# Tensor Parallelism (Megatron-LM): split individual operations (matrix multiply)
# Pipeline Parallelism: split layers across GPUs, pipeline micro-batches

# ZeRO (Zero Redundancy Optimizer):
# Stage 1: partition optimizer states   (8x memory reduction)
# Stage 2: + partition gradients        (additional reduction)
# Stage 3: + partition model weights    (full theoretical reduction)
# Used in DeepSpeed, now integrated in PyTorch FSDP

# Gradient accumulation: simulate large batch without memory overhead
optimizer.zero_grad()
for i, batch in enumerate(loader):
    out  = model(batch) / accumulation_steps
    loss = criterion(out, batch.labels)
    loss.backward()
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

---

## 21. Staff-Level Interview Patterns

### 21.1 Questions Only Staff Should Get Right

**Q: Why does the validation loss start increasing while training loss still decreases?**
> Overfitting. The model memorizes training noise. The gap indicates high variance. Solutions: regularization (dropout, weight decay, data augmentation), early stopping, more data. Staff answer also mentions: could also be learning rate too high causing oscillation, or train/val distribution mismatch.

**Q: You have 99% accuracy on a fraud detection model. Is it good?**
> No. If 1% of transactions are fraud, predicting "legit" always achieves 99% accuracy. Use precision, recall, F1, PR-AUC. Staff answer: ask about business cost of FP vs FN, set decision threshold accordingly, use imbalance-aware training.

**Q: Model works great in A/B test but not in production. What happened?**
> Multiple possibilities: (1) A/B test was on wrong population segment, (2) Network effect — test group affects control (e.g., in social feeds), (3) Launch effect — novelty bias, (4) Training-serving skew emerged at full scale, (5) Metrics definition mismatch. Staff answer: diagnose each systematically.

**Q: When would you use a neural network vs gradient boosting?**
> GBM: tabular data, smaller datasets, need interpretability, fast iteration. Neural: unstructured data (images, text, audio), very large datasets, feature learning from raw inputs, sequences, need transfer learning. Staff answer: start with GBM as baseline, justify NN with ablation study.

**Q: How do you handle class imbalance?**
> Level 1: class_weight parameter. Level 2: threshold tuning. Level 3: over/under sampling (SMOTE, RandomUnderSampler). Level 4: loss modification (focal loss: -α(1-p)^γ log p, penalizes easy examples). Level 5: reframe as anomaly detection. Staff answer: question whether imbalance is a problem at all — if AUC is good, it's not.

**Q: Explain the attention mechanism and why it works better than RNNs for long sequences.**
> RNN: sequential computation, O(n) path length between distant positions → vanishing gradients. Attention: any two positions connected in O(1) steps, parallel computation. Staff answer also mentions: downside is O(n²) memory/compute, contrast with efficient attention variants, explain when RNN still preferred (streaming, very long sequences).

**Q: What is gradient checkpointing and when would you use it?**
> Recompute activations during backward pass instead of storing them. Reduces memory from O(n layers) to O(√n) at cost of ~33% more compute. Use when: training large models, GPU OOM, enabling larger batch sizes. Implementation: `torch.utils.checkpoint.checkpoint(fn, inputs)`.

### 21.2 System Design Anti-Patterns

```
1. Jumping to complex model
   → Always start with a simple baseline (linear model, rule-based)
   → Complex model must beat baseline by enough to justify maintenance cost

2. Ignoring data quality
   → 80% of ML work is data; 20% is model
   → "Garbage in, garbage out" — no model fixes fundamental data problems

3. Leaking features
   → Common in competitions, devastating in production
   → Always ask: "would I have this feature at prediction time?"

4. Evaluating incorrectly
   → Single metric: always use multiple
   → Wrong split: use same split type as production scenario
   → Ignoring calibration: good AUC ≠ good probabilities

5. Not thinking about deployment
   → "Works on my machine" → model needs to serve at scale
   → Latency requirements drive architecture choices
   → Batch vs real-time determines feature freshness

6. Ignoring feedback loops
   → Model affects what data it sees next (explore vs exploit)
   → Recommendation: model recommends popular items → biases future training
   → Fix: off-policy learning, exploration strategies, debiasing

7. Premature optimization
   → Spending weeks on hyperparameter tuning vs collecting better data
   → More data almost always beats better algorithm
```

### 21.3 The Staff Engineer Mindset

```
Technical depth:
  ✓ Explain every design choice and trade-off
  ✓ Know when NOT to use ML (rules-based is often better)
  ✓ Think about edge cases: cold start, missing data, distribution shift

Business alignment:
  ✓ Connect ML metrics to business metrics
  ✓ Understand deployment constraints (latency, cost, compliance)
  ✓ Communicate uncertainty and risk to stakeholders

System thinking:
  ✓ End-to-end pipeline, not just model
  ✓ Data flywheel: better model → more data → better model
  ✓ Feedback loops: how does deployment change future training data?
  ✓ Monitoring and alerting from day 1

Team impact:
  ✓ ML platform decisions affect whole team velocity
  ✓ Documentation, reproducibility (MLflow, DVC)
  ✓ Model cards, bias audits, fairness evaluation
```

---

## Quick Reference

### Complexity Summary

```
Algorithm          | Train          | Predict  | Memory    | Parallelizable
───────────────────┼────────────────┼──────────┼───────────┼───────────────
Linear Regression  | O(nd²+d³)     | O(d)     | O(d)      | Yes
Logistic Reg       | O(ndi)        | O(d)     | O(d)      | Yes
Decision Tree      | O(nd log n)   | O(depth) | O(n)      | No
Random Forest      | O(T·nd log n) | O(T·d)   | O(T·n)    | Yes (per tree)
XGBoost            | O(T·nd log n) | O(T·d)   | O(T·n)    | Yes (per level)
KNN                | O(1)          | O(nd)    | O(nd)     | Yes (search)
SVM (kernel)       | O(n²d-n³d)   | O(n_sv)  | O(n_sv)   | Partial
k-Means (per iter) | O(nkd)        | O(kd)    | O(nkd)    | Yes
Neural Net (SGD)   | O(ndi per ep) | O(d)     | O(d)      | Yes (GPU)
Transformer attn   | O(n²d)        | O(n²d)   | O(n²)     | Yes
```

### Loss Function Reference

```
Task                 | Loss                    | Notes
─────────────────────┼─────────────────────────┼────────────────────────────
Binary classification| Binary cross-entropy    | -y log p - (1-y) log(1-p)
Multi-class          | Categorical cross-entropy| -Σ y log p
Regression           | MSE                     | robust: MAE, Huber
Imbalanced classif.  | Focal loss              | -α(1-p)^γ log p
Ranking              | Hinge loss              | max(0, 1 - y·ŷ)
Generation           | Cross-entropy           | next token prediction
Contrastive          | InfoNCE / NT-Xent       | -log(exp(pos)/Σexp(all))
VAE                  | ELBO = -KL + recon      | variational lower bound
GAN                  | minimax / Wasserstein   | generator vs discriminator
Reward modeling      | Pairwise preference     | log σ(rᵥᵢₙₙₑᵣ - rₗₒₛₑᵣ)
```

---

*Related: `DSA_PATTERNS.md` | `CONCEPTS.md` | `THREADING_CONCURRENCY.md` | `LLD_OOD.md`*
