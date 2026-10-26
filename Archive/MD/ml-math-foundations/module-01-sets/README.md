# Module 01 — Sets

## The Language Every ML Model Speaks

> **Why Sets Matter in ML:** Every dataset is a set of examples. Every feature space is a set of dimensions. Training/validation/test splits are set partitions. Understanding sets gives you the vocabulary to describe *what data is*.

```
 MODULE 01 ROADMAP
 ═══════════════════════════════════════
 01.01 Introduction to Set Theory ◀── YOU ARE HERE
 01.02 Set Operations
 01.03 Properties of Sets
 ═══════════════════════════════════════
```

---

## 01.01 — Introduction to Set Theory (8 Lessons)

### Lesson 1: What Is a Set?

💡 **Key Intuition:** A set is simply a *collection of distinct objects*. Think of it like a bag where duplicates don't count and order doesn't matter.

**Definition:** A **set** is an unordered collection of distinct elements.

```
Set A = {1, 2, 3}       ← A set of numbers
Set B = {"cat", "dog"}   ← A set of strings
Set C = {🍎, 🍌, 🍇}    ← A set of anything!
```

**Two ways to define a set:**

| Method | Example | Read As |
|--------|---------|---------|
| **Roster** (list them) | A = {2, 4, 6, 8} | "A is the set containing 2, 4, 6, 8" |
| **Set-builder** (describe them) | A = {x \| x is even, 0 < x < 10} | "A is all x such that x is even and between 0 and 10" |

🐍 **Python Code:**
```python
# Sets in Python — the direct translation
A = {1, 2, 3, 4, 5}
B = {3, 4, 5, 6, 7}

# Membership test: is 3 in A?
print(3 in A)      # True
print(10 in A)     # False

# Sets ignore duplicates
C = {1, 1, 2, 2, 3}
print(C)            # {1, 2, 3}

# Set-builder notation using comprehension
evens = {x for x in range(1, 20) if x % 2 == 0}
print(evens)        # {2, 4, 6, 8, 10, 12, 14, 16, 18}
```

### Lesson 2: Element Membership (∈)

The symbol **∈** means "is an element of" (think of it as "belongs to").

```
If A = {1, 2, 3}
Then:  1 ∈ A   ← "1 belongs to A" ✓
       5 ∉ A   ← "5 does NOT belong to A" ✗
```

⚡ **ML Connection:** When we say a data point x belongs to class C, we're saying x ∈ C.

```python
# In classification: which class does a sample belong to?
class_cat = {"img_01.jpg", "img_05.jpg", "img_09.jpg"}
class_dog = {"img_02.jpg", "img_03.jpg", "img_07.jpg"}

sample = "img_05.jpg"
print(sample in class_cat)  # True → classified as cat
print(sample in class_dog)  # False
```

### Lesson 3: Special Sets & The Number-System Ladder

📊 **The Number Ladder:**

```
ℕ ⊂ ℤ ⊂ ℚ ⊂ ℝ ⊂ ℂ

ℂ ─── Complex Numbers ────── {a + bi}      ← Signal processing, quantum
│
ℝ ─── Real Numbers ────────── {-∞ ... +∞}  ← ALL of ML lives here
│
ℚ ─── Rational Numbers ───── {p/q}         ← Fractions
│
ℤ ─── Integers ───────────── {...-2,-1,0,1,2...}  ← Counting, indices
│
ℕ ─── Natural Numbers ────── {0,1,2,3,...}  ← Class labels
```

💡 **Key Intuition:** ML models almost always work in ℝ (real numbers). Your input features, weights, and outputs are all real-valued. That's why "real-valued vector" appears everywhere in ML papers.

```python
import numpy as np

# ML models live in ℝⁿ (n-dimensional real space)
# A single data point in 3D feature space
x = np.array([1.5, -2.3, 0.7])  # x ∈ ℝ³

# A dataset is a collection of points in ℝⁿ
X = np.array([
    [1.5, -2.3, 0.7],   # sample 1
    [0.3,  1.1, -0.4],  # sample 2
    [2.1,  0.5,  1.8],  # sample 3
])
print(f"Dataset shape: {X.shape}")  # (3, 3) → 3 samples in ℝ³
```

### Lesson 4: Subsets (⊆)

**Definition:** A is a **subset** of B (written A ⊆ B) if *every* element of A is also in B.

```
A = {1, 2}
B = {1, 2, 3, 4}

A ⊆ B?  Check: 1 ∈ B ✓, 2 ∈ B ✓  →  YES, A ⊆ B
B ⊆ A?  Check: 3 ∈ A? ✗           →  NO, B ⊄ A
```

📊 **Visual Diagram:**
```
    ┌──────────────────────┐
    │  B = {1, 2, 3, 4}   │
    │    ┌──────────┐      │
    │    │ A = {1,2}│      │
    │    └──────────┘      │
    └──────────────────────┘
    
    A is completely inside B → A ⊆ B
```

⚡ **ML Connection:** Your training set should be a subset of your total data. Hyperparameter search spaces are subsets of all possible configurations.

```python
# Subset checking in Python
A = {1, 2}
B = {1, 2, 3, 4}

print(A.issubset(B))   # True  → A ⊆ B
print(A <= B)           # True  → shorthand
print(A < B)            # True  → proper subset (A ≠ B)

# ML example: checking if selected features are valid
all_features = {"age", "income", "education", "zip_code", "credit_score"}
selected_features = {"age", "income"}
print(selected_features <= all_features)  # True — valid selection!
```

### Lesson 5: Empty Set and Universal Set

| Set | Symbol | What It Is | ML Analogy |
|-----|--------|-----------|------------|
| **Empty Set** | ∅ or {} | A set with no elements | No data matches your filter |
| **Universal Set** | U | Set of ALL possible elements | The entire data universe |

```python
# Empty set — no samples match
filtered = {x for x in range(100) if x > 200}
print(filtered)         # set() — empty!
print(len(filtered))    # 0

# Universal set depends on context
U_colors = {"red", "green", "blue", "yellow", "purple"}
A_warm = {"red", "yellow"}
# Complement: everything in U not in A
A_complement = U_colors - A_warm
print(A_complement)     # {'green', 'blue', 'purple'}
```

### Lesson 6: Set Equality

Two sets are **equal** if they contain exactly the same elements.

```
A = {1, 2, 3}  and  B = {3, 1, 2}
A == B?  →  YES! (order doesn't matter in sets)

A = {1, 2, 3}  and  C = {1, 2, 3, 4}
A == C?  →  NO! (C has an extra element)
```

💡 **Key Insight:** A = B if and only if A ⊆ B AND B ⊆ A.

### Lesson 7: Power Set

The **power set** P(A) is the set of ALL possible subsets of A (including ∅ and A itself).

```
A = {1, 2, 3}
P(A) = {∅, {1}, {2}, {3}, {1,2}, {1,3}, {2,3}, {1,2,3}}
|P(A)| = 2³ = 8
```

**Formula:** If |A| = n, then |P(A)| = 2ⁿ

⚡ **ML Connection — Why This Is HUGE:**
If you have n features, the power set represents all possible feature combinations. With 20 features, that's 2²⁰ = 1,048,576 possible subsets to search through! This is why feature selection is NP-hard.

```python
from itertools import combinations

def power_set(s):
    """Generate all subsets of a set."""
    s = list(s)
    result = []
    for r in range(len(s) + 1):
        for combo in combinations(s, r):
            result.append(set(combo))
    return result

features = {"age", "income", "score"}
all_subsets = power_set(features)
print(f"Number of feature subsets: {len(all_subsets)}")  # 8
for subset in all_subsets:
    print(f"  {subset}")
```

### Lesson 8: Cardinality (Set Size)

**Cardinality** |A| is simply the number of elements in A.

| Set | Cardinality | Type |
|-----|------------|------|
| {1, 2, 3} | 3 | Finite |
| ℕ = {0,1,2,...} | ℵ₀ (aleph-null) | Countably Infinite |
| ℝ (real numbers) | 𝔠 (continuum) | Uncountably Infinite |

💡 **Mind-Blowing Fact:** There are "more" real numbers than natural numbers, even though both are infinite! This is Cantor's diagonal argument — and it explains why continuous probability distributions need density functions instead of simple counting.

---

## 01.02 — Set Operations (6 Lessons)

### Lesson 1: Union (∪) — "OR"

A ∪ B = elements in A **or** B (or both)

```
A = {1, 2, 3}
B = {3, 4, 5}
A ∪ B = {1, 2, 3, 4, 5}
```

📊 **Venn Diagram:**
```
    ┌───────┐   ┌───────┐
    │   A   │   │   B   │
    │  1  2 │ 3 │ 4  5  │
    │       │   │       │
    └───────┘   └───────┘
    ════════════════════════
    A ∪ B = {1, 2, 3, 4, 5}  ← everything shaded
```

```python
A = {1, 2, 3}
B = {3, 4, 5}
print(A | B)        # {1, 2, 3, 4, 5}
print(A.union(B))   # same thing

# ML: Combine predictions from two models (ensemble)
model1_positive = {"patient_A", "patient_C", "patient_E"}
model2_positive = {"patient_B", "patient_C", "patient_F"}
any_positive = model1_positive | model2_positive
print(f"Flagged by either model: {any_positive}")
```

### Lesson 2: Intersection (∩) — "AND"

A ∩ B = elements in A **and** B (both)

```
A = {1, 2, 3}
B = {3, 4, 5}
A ∩ B = {3}
```

📊 **Venn Diagram:**
```
    ┌───────┐   ┌───────┐
    │   A   │   │   B   │
    │  1  2 │▓3▓│ 4  5  │
    │       │   │       │
    └───────┘   └───────┘
    ════════════════════════
    A ∩ B = {3}  ← only the overlap
```

```python
A = {1, 2, 3}
B = {3, 4, 5}
print(A & B)              # {3}
print(A.intersection(B))  # same

# ML: Find features important to BOTH models
model1_important = {"age", "income", "education", "zip"}
model2_important = {"age", "credit_score", "income"}
both_important = model1_important & model2_important
print(f"Universally important: {both_important}")  # {'age', 'income'}
```

### Lesson 3: Difference (−) — "BUT NOT"

A − B = elements in A **but not** in B

```
A = {1, 2, 3, 4}
B = {3, 4, 5, 6}
A − B = {1, 2}       ← in A, remove anything also in B
B − A = {5, 6}       ← in B, remove anything also in A
```

```python
A = {1, 2, 3, 4}
B = {3, 4, 5, 6}
print(A - B)    # {1, 2}
print(B - A)    # {5, 6}

# ML: Find samples that model got wrong but should have gotten right
correct_answers = {"q1", "q2", "q3", "q4", "q5"}
model_correct = {"q1", "q3", "q5"}
mistakes = correct_answers - model_correct
print(f"Model got wrong: {mistakes}")  # {'q2', 'q4'}
```

### Lesson 4: Symmetric Difference (△)

A △ B = elements in A **or** B, **but not both** (XOR)

```
A = {1, 2, 3}
B = {3, 4, 5}
A △ B = {1, 2, 4, 5}   ← everything EXCEPT the overlap
```

```python
A = {1, 2, 3}
B = {3, 4, 5}
print(A ^ B)                        # {1, 2, 4, 5}
print(A.symmetric_difference(B))    # same

# ML: Find where two models DISAGREE
model1_pred = {"spam", "spam", "ham", "spam"}  # just labels for emails 1-4
model1_spam = {0, 1, 3}  # indices predicted as spam
model2_spam = {0, 2, 3}  # indices predicted as spam
disagreements = model1_spam ^ model2_spam
print(f"Models disagree on indices: {disagreements}")  # {1, 2}
```

### Lesson 5: Complement (Aᶜ)

Aᶜ = everything in the universal set U that is **not** in A

```
U = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
A = {2, 4, 6, 8, 10}
Aᶜ = {1, 3, 5, 7, 9}
```

⚡ **ML Connection:** In binary classification, if P(class=1) = 0.7, then P(class=0) = 1 − 0.7 = 0.3. The complement!

### Lesson 6: Cartesian Product (×)

A × B = all ordered pairs (a, b) where a ∈ A and b ∈ B

```
A = {1, 2}
B = {x, y, z}
A × B = {(1,x), (1,y), (1,z), (2,x), (2,y), (2,z)}
|A × B| = |A| · |B| = 2 × 3 = 6
```

⚡ **ML Connection — This is EVERYWHERE:**
- Feature space ℝⁿ = ℝ × ℝ × ... × ℝ (n times)
- Grid search: all combinations of hyperparameters
- Attention in transformers: Q × K (query-key pairs)

```python
from itertools import product

# Hyperparameter grid search is a Cartesian product!
learning_rates = [0.001, 0.01, 0.1]
batch_sizes = [32, 64, 128]
optimizers = ["adam", "sgd"]

search_space = list(product(learning_rates, batch_sizes, optimizers))
print(f"Total experiments: {len(search_space)}")  # 18
for config in search_space[:5]:
    print(f"  lr={config[0]}, batch={config[1]}, opt={config[2]}")
```

---

## 01.03 — Properties of Sets (11 Lessons)

### Lesson 1: Commutative Laws

```
A ∪ B = B ∪ A       ← Union is commutative
A ∩ B = B ∩ A       ← Intersection is commutative
```

💡 **Intuition:** The order you combine two datasets doesn't change the result.

### Lesson 2: Associative Laws

```
(A ∪ B) ∪ C = A ∪ (B ∪ C)
(A ∩ B) ∩ C = A ∩ (B ∩ C)
```

💡 **Intuition:** It doesn't matter which pair you combine first.

### Lesson 3: Distributive Laws

```
A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)
A ∪ (B ∩ C) = (A ∪ B) ∩ (A ∪ C)
```

📊 **Visual Proof:**
```
Step 1: B ∪ C                     Step 2: A ∩ (B ∪ C)
┌─────┐ ┌─────┐                  ┌───────────────┐
│  B  │ │  C  │                  │      A        │
│░░░░░│░│░░░░░│  = shaded        │   ┌─────┐─────┤
│░░░░░│░│░░░░░│                  │   │▓▓▓▓▓│▓▓▓▓▓│
└─────┘ └─────┘                  │   └─────┘─────┤
                                 └───────────────┘
                                 Only where A overlaps with B∪C
```

### Lesson 4: De Morgan's Laws ⭐

These are asked in **every** FAANG interview touching on logic/sets:

```
(A ∪ B)ᶜ = Aᶜ ∩ Bᶜ    ← "not (A or B)" = "not A AND not B"
(A ∩ B)ᶜ = Aᶜ ∪ Bᶜ    ← "not (A and B)" = "not A OR not B"
```

💡 **Plain English:**
- "People NOT in (engineers OR designers)" = "People NOT engineers AND NOT designers"
- "People NOT in (engineers AND designers)" = "People NOT engineers OR NOT designers"

```python
# Verify De Morgan's Laws
U = set(range(1, 11))
A = {1, 2, 3, 4, 5}
B = {4, 5, 6, 7, 8}

# Law 1: (A ∪ B)ᶜ = Aᶜ ∩ Bᶜ
lhs = U - (A | B)
rhs = (U - A) & (U - B)
print(f"Law 1: {lhs} == {rhs} → {lhs == rhs}")  # True

# Law 2: (A ∩ B)ᶜ = Aᶜ ∪ Bᶜ
lhs = U - (A & B)
rhs = (U - A) | (U - B)
print(f"Law 2: {lhs} == {rhs} → {lhs == rhs}")  # True
```

### Lesson 5: Identity Laws

```
A ∪ ∅ = A        ← Union with nothing = same set
A ∩ U = A        ← Intersection with everything = same set
```

### Lesson 6: Domination Laws

```
A ∪ U = U        ← Union with everything = everything
A ∩ ∅ = ∅        ← Intersection with nothing = nothing
```

### Lesson 7: Idempotent Laws

```
A ∪ A = A
A ∩ A = A
```

### Lesson 8: Absorption Laws

```
A ∪ (A ∩ B) = A
A ∩ (A ∪ B) = A
```

### Lesson 9: Complement Laws

```
A ∪ Aᶜ = U       ← Everything is either in A or not in A
A ∩ Aᶜ = ∅       ← Nothing is both in A and not in A
```

🐍 **Verify ALL Set Laws in Python:**
```python
# Verify every set law programmatically
U = set(range(1, 11))  # Universal set
A = {1, 2, 3, 4, 5}
B = {4, 5, 6, 7, 8}
C = {2, 4, 6, 8, 10}

print("=== Verifying Set Laws ===")

# Commutative
assert A | B == B | A,  "Union commutative failed"
assert A & B == B & A,  "Intersection commutative failed"
print("✓ Commutative laws")

# Associative
assert (A | B) | C == A | (B | C), "Union associative failed"
assert (A & B) & C == A & (B & C), "Intersection associative failed"
print("✓ Associative laws")

# Distributive
assert A & (B | C) == (A & B) | (A & C), "Distributive ∩ over ∪ failed"
assert A | (B & C) == (A | B) & (A | C), "Distributive ∪ over ∩ failed"
print("✓ Distributive laws")

# Identity
assert A | set() == A,  "Union identity failed"
assert A & U == A,      "Intersection identity failed"
print("✓ Identity laws")

# Domination
assert A | U == U,          "Union domination failed"
assert A & set() == set(),  "Intersection domination failed"
print("✓ Domination laws")

# Idempotent
assert A | A == A,  "Union idempotent failed"
assert A & A == A,  "Intersection idempotent failed"
print("✓ Idempotent laws")

# Absorption
assert A | (A & B) == A,  "Absorption 1 failed"
assert A & (A | B) == A,  "Absorption 2 failed"
print("✓ Absorption laws")

# Complement
A_comp = U - A
assert A | A_comp == U,      "Complement union failed"
assert A & A_comp == set(),  "Complement intersection failed"
print("✓ Complement laws")

# De Morgan
assert U - (A | B) == (U - A) & (U - B), "De Morgan 1 failed"
assert U - (A & B) == (U - A) | (U - B), "De Morgan 2 failed"
print("✓ De Morgan's laws")

print("\n✅ ALL SET LAWS VERIFIED!")
```

### Lesson 10: Inclusion-Exclusion Principle

**For counting elements in unions:**

```
|A ∪ B| = |A| + |B| − |A ∩ B|
|A ∪ B ∪ C| = |A| + |B| + |C| − |A∩B| − |A∩C| − |B∩C| + |A∩B∩C|
```

⚡ **ML Connection:** This is fundamental in probability — it becomes P(A ∪ B) = P(A) + P(B) − P(A ∩ B).

```python
# Inclusion-Exclusion in action
users_feature_A = set(range(0, 700))    # 700 users have feature A
users_feature_B = set(range(500, 1100)) # 600 users have feature B
# Overlap: 500-699 → 200 users

total_with_either = len(users_feature_A | users_feature_B)
by_formula = len(users_feature_A) + len(users_feature_B) - len(users_feature_A & users_feature_B)
print(f"Direct count: {total_with_either}")   # 1100
print(f"By formula:   {by_formula}")          # 1100 ✓
```

### Lesson 11: Partitions

A **partition** of set S divides it into non-overlapping subsets that together cover all of S.

```
S = {1, 2, 3, 4, 5, 6}
Partition: {1, 2}, {3, 4}, {5, 6}

Rules:
  ✓ No subset is empty
  ✓ Subsets don't overlap (pairwise disjoint)
  ✓ Union of all subsets = S
```

⚡ **ML Connection — Train/Val/Test Split IS a Partition!**

```python
import numpy as np

# The most important partition in ML
data = np.arange(1000)  # 1000 samples
np.random.shuffle(data)

train = set(data[:700])    # 70%
val   = set(data[700:850]) # 15%
test  = set(data[850:])    # 15%

# Verify it's a valid partition
print(f"No overlap train-val: {len(train & val) == 0}")     # True
print(f"No overlap train-test: {len(train & test) == 0}")   # True
print(f"No overlap val-test: {len(val & test) == 0}")       # True
print(f"Covers all data: {len(train | val | test) == 1000}")# True
print("✓ Valid partition!")
```

---

## 🔥 FAANG Deep Dive — Sets

### Interview Problem 1: Google — "Unique Email Addresses"
> Given a list of emails, determine the number of unique addresses (ignore dots and +suffix in local name).

```python
def num_unique_emails(emails):
    """Use SET to find unique emails after normalization."""
    unique = set()
    for email in emails:
        local, domain = email.split('@')
        local = local.split('+')[0]      # remove +suffix
        local = local.replace('.', '')    # remove dots
        unique.add(f"{local}@{domain}")
    return len(unique)

emails = [
    "test.email+alex@google.com",
    "test.e.mail+bob@google.com",
    "testemail+cd@google.com"
]
print(num_unique_emails(emails))  # 1 (all normalize to testemail@google.com)
```

### Interview Problem 2: Amazon — "Intersection of Two Arrays"
> Find common elements between two arrays (return unique values).

```python
def intersection(nums1, nums2):
    return list(set(nums1) & set(nums2))

print(intersection([1,2,2,1], [2,2]))       # [2]
print(intersection([4,9,5], [9,4,9,8,4]))   # [4, 9]
```

### Interview Problem 3: Meta — "K-fold Cross Validation as Partitions"

```python
def k_fold_partition(data, k=5):
    """Create k non-overlapping folds — a partition of the data."""
    n = len(data)
    indices = np.random.permutation(n)
    fold_size = n // k
    folds = []
    
    for i in range(k):
        start = i * fold_size
        end = start + fold_size if i < k - 1 else n
        folds.append(set(indices[start:end]))
    
    # Verify partition properties
    for i in range(k):
        for j in range(i + 1, k):
            assert len(folds[i] & folds[j]) == 0, "Folds overlap!"
    
    all_indices = set()
    for fold in folds:
        all_indices |= fold
    assert all_indices == set(range(n)), "Folds don't cover all data!"
    
    return folds

folds = k_fold_partition(np.arange(100), k=5)
for i, fold in enumerate(folds):
    print(f"Fold {i}: {len(fold)} samples")
```

---

## ✅ Module 01 Checkpoint

After completing this module, you should be able to:

- [ ] Define sets using roster and set-builder notation
- [ ] Perform union, intersection, difference, symmetric difference
- [ ] Apply De Morgan's Laws without hesitation
- [ ] Calculate power set size (2ⁿ) and explain its ML implications
- [ ] Understand why train/test splits are partitions
- [ ] Use the inclusion-exclusion principle
- [ ] Solve basic FAANG set problems in O(n) time using hash sets

**Next →** [Module 02: Logic](../module-02-logic/README.md)
