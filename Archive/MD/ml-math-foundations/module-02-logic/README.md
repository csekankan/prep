# Module 02 — Logic

## The Reasoning Framework Behind Every Algorithm

> **Why Logic Matters in ML:** Decision trees split on logical conditions. Loss functions evaluate truth. Attention masks use Boolean logic. Every `if` statement in your code is formal logic in disguise.

```
 MODULE 02 ROADMAP
 ═══════════════════════════════════════
 02.01 Statements, Predicates & Truth
 02.02 Conditional Logic
 02.03 Boolean Algebra
 ═══════════════════════════════════════
```

---

## 02.01 — Statements, Predicates and Truth (9 Lessons)

### Lesson 1: Propositions

💡 **Key Intuition:** A **proposition** is any statement that is either TRUE or FALSE — nothing in between.

| Statement | Proposition? | Value |
|-----------|:------:|-------|
| "2 + 3 = 5" | ✅ | TRUE |
| "The sky is green" | ✅ | FALSE |
| "What time is it?" | ❌ | Not a proposition (it's a question) |
| "x > 5" | ❌ | Depends on x (it's a predicate) |

### Lesson 2: Logical Connectives

These are the building blocks of ALL logical reasoning:

| Connective | Symbol | Python | Plain English |
|-----------|--------|--------|---------------|
| **NOT** (negation) | ¬p | `not p` | "It is NOT the case that p" |
| **AND** (conjunction) | p ∧ q | `p and q` | "Both p AND q are true" |
| **OR** (disjunction) | p ∨ q | `p or q` | "At least one of p, q is true" |
| **IMPLIES** | p → q | `(not p) or q` | "If p then q" |
| **IFF** (biconditional) | p ↔ q | `p == q` | "p if and only if q" |

### Lesson 3: Truth Tables — The Complete Story

📊 **NOT:**
```
 p  │ ¬p
────┼────
 T  │  F
 F  │  T
```

📊 **AND, OR, XOR:**
```
 p  │ q  │ p∧q │ p∨q │ p⊕q
────┼────┼─────┼─────┼─────
 T  │ T  │  T  │  T  │  F
 T  │ F  │  F  │  T  │  T
 F  │ T  │  F  │  T  │  T
 F  │ F  │  F  │  F  │  F
```

🐍 **Build Truth Tables in Python:**
```python
import itertools

def truth_table(variables, expression, expr_name="Result"):
    """Generate a truth table for any logical expression."""
    headers = variables + [expr_name]
    print(" | ".join(f"{h:>5}" for h in headers))
    print("-" * (8 * len(headers)))
    
    for values in itertools.product([True, False], repeat=len(variables)):
        env = dict(zip(variables, values))
        result = expression(env)
        row = list(values) + [result]
        print(" | ".join(f"{str(v):>5}" for v in row))

# Example: p AND (q OR r)
truth_table(
    ["p", "q", "r"],
    lambda e: e["p"] and (e["q"] or e["r"]),
    "p∧(q∨r)"
)
```

### Lesson 4: Predicates — Propositions with Variables

A **predicate** is a statement containing variables that becomes a proposition when you plug in values.

```
P(x) = "x is greater than 5"

P(3) → FALSE   (3 > 5 is false)
P(7) → TRUE    (7 > 5 is true)
P(5) → FALSE   (5 > 5 is false)
```

⚡ **ML Connection:** A decision tree split is a predicate!
```
P(x) = "feature_age > 30"   ← predicate on input x
If P(x) is TRUE  → go left
If P(x) is FALSE → go right
```

```python
# Decision tree as predicates
def simple_decision_tree(x):
    """Each node is a predicate."""
    age, income, score = x
    
    if age > 30:                    # Predicate P1
        if income > 50000:          # Predicate P2
            return "approved"
        else:
            return "review"
    else:
        if score > 700:             # Predicate P3
            return "approved"
        else:
            return "denied"

# Test
print(simple_decision_tree([35, 60000, 650]))  # approved
print(simple_decision_tree([25, 30000, 650]))  # denied
```

### Lesson 5: Quantifiers — "For All" and "There Exists"

| Quantifier | Symbol | Meaning | Example |
|-----------|--------|---------|---------|
| **Universal** | ∀ | "For ALL" | ∀x ∈ ℝ: x² ≥ 0 ("every real number squared is non-negative") |
| **Existential** | ∃ | "There EXISTS at least one" | ∃x ∈ ℤ: x² = 4 ("some integer squared equals 4") |

```python
# Universal quantifier: ∀x in data, loss(x) < threshold
data = [0.1, 0.05, 0.2, 0.15, 0.08]
threshold = 0.3

all_below = all(loss < threshold for loss in data)  # ∀
print(f"All losses below {threshold}: {all_below}")  # True

# Existential quantifier: ∃x in data, loss(x) > threshold
any_above = any(loss > threshold for loss in data)   # ∃
print(f"Any loss above {threshold}: {any_above}")     # False
```

### Lesson 6: Negating Quantifiers ⭐

This trips up 90% of candidates:

```
¬(∀x: P(x))  ≡  ∃x: ¬P(x)
"NOT everything is true" = "there exists something false"

¬(∃x: P(x))  ≡  ∀x: ¬P(x)  
"nothing exists that is true" = "everything is false"
```

💡 **Example:** "Not all students passed" = "There exists at least one student who failed."

### Lesson 7-9: Logical Equivalences, Tautologies, and Contradictions

**Tautology:** Always TRUE regardless of inputs → p ∨ ¬p

**Contradiction:** Always FALSE → p ∧ ¬p

**Contingency:** Sometimes TRUE, sometimes FALSE → p ∧ q

```python
# Check if an expression is a tautology
def is_tautology(n_vars, expression):
    for values in itertools.product([True, False], repeat=n_vars):
        if not expression(*values):
            return False
    return True

# p ∨ ¬p is a tautology
print(is_tautology(1, lambda p: p or not p))          # True

# p → (q → p) is a tautology
print(is_tautology(2, lambda p, q: (not p) or ((not q) or p)))  # True

# p ∧ q is NOT a tautology
print(is_tautology(2, lambda p, q: p and q))           # False
```

---

## 02.02 — Conditional Logic (8 Lessons)

### Lesson 1: The Implication (→)

**p → q** reads "if p then q"

📊 **The Most Counter-Intuitive Truth Table:**
```
  p  │  q  │ p→q │ Why?
─────┼─────┼─────┼──────────────────────────────────
  T  │  T  │  T  │ Promise kept: "if rain, umbrella" — it rained, I had umbrella ✓
  T  │  F  │  F  │ Promise broken: it rained, no umbrella ✗
  F  │  T  │  T  │ Promise not tested: no rain, had umbrella anyway — still valid!
  F  │  F  │  T  │ Promise not tested: no rain, no umbrella — still valid!
```

💡 **Key Insight:** An implication is only FALSE when the hypothesis is TRUE but the conclusion is FALSE. A promise can only be broken when the condition is met.

⚡ **ML Connection:** "If model predicts positive, then sample IS positive" — this is **precision**. When p→q is FALSE (predicted positive but actually negative), that's a **false positive**.

### Lesson 2: Converse, Inverse, Contrapositive

Given: p → q ("if it rains, the ground is wet")

| Form | Statement | Equivalent to original? |
|------|----------|:-----------------------:|
| **Converse** | q → p ("if ground is wet, it rained") | ❌ |
| **Inverse** | ¬p → ¬q ("if no rain, ground not wet") | ❌ |
| **Contrapositive** | ¬q → ¬p ("if ground NOT wet, it did NOT rain") | ✅ |

💡 **Critical:** The **contrapositive** is ALWAYS logically equivalent to the original. FAANG loves this!

```python
def implication(p, q):
    return (not p) or q

# Verify: p→q ≡ ¬q→¬p (contrapositive)
for p in [True, False]:
    for q in [True, False]:
        original = implication(p, q)
        contrapositive = implication(not q, not p)
        assert original == contrapositive, "Should never fail!"
        
print("✓ Implication ≡ Contrapositive (always)")
```

### Lesson 3: Biconditional (↔)

**p ↔ q** means "p if and only if q" (p is true exactly when q is true)

```
 p  │ q  │ p↔q
────┼────┼─────
 T  │ T  │  T
 T  │ F  │  F
 F  │ T  │  F
 F  │ F  │  T
```

⚡ **ML Connection:** "The model is accurate ↔ loss is below threshold" — these conditions are equivalent.

### Lessons 4-8: Proof Techniques

**Why Care?** Because understanding proofs helps you verify algorithm correctness.

**Direct Proof:** Assume p, derive q.
```
Claim: If n is even, then n² is even.
Proof: n = 2k (definition of even)
       n² = (2k)² = 4k² = 2(2k²)
       This is 2 × (integer), so n² is even. ∎
```

**Proof by Contradiction:** Assume the opposite, find a contradiction.
```
Claim: √2 is irrational.
Proof: Assume √2 = p/q (lowest terms)
       2 = p²/q²  →  p² = 2q²
       So p² is even → p is even → p = 2k
       (2k)² = 2q² → 4k² = 2q² → q² = 2k²
       So q is also even — contradicts "lowest terms"! ∎
```

**Proof by Induction:** Base case + inductive step.
```
Claim: 1 + 2 + ... + n = n(n+1)/2
Base:  n=1 → 1 = 1(2)/2 = 1 ✓
Step:  Assume true for n=k:  1+2+...+k = k(k+1)/2
       For n=k+1: k(k+1)/2 + (k+1) = (k+1)(k+2)/2 ✓ ∎
```

---

## 02.03 — Boolean Algebra (2 Lessons)

### Lesson 1: Boolean Algebra Identities

Boolean algebra is set theory with {0, 1} instead of sets:

| Set Operation | Boolean Operation | Symbol |
|:---:|:---:|:---:|
| A ∪ B | a OR b | a + b |
| A ∩ B | a AND b | a · b |
| Aᶜ | NOT a | ā |

**All the same laws apply:**

```
Commutative:   a + b = b + a          a · b = b · a
Associative:   (a+b)+c = a+(b+c)      (a·b)·c = a·(b·c)
Distributive:  a·(b+c) = a·b + a·c    a+(b·c) = (a+b)·(a+c)
Identity:      a + 0 = a              a · 1 = a
Complement:    a + ā = 1              a · ā = 0
De Morgan:     (a+b)' = ā·b̄          (a·b)' = ā+b̄
```

### Lesson 2: Boolean Algebra in Neural Networks

⚡ **ML Connection — Attention Masks are Boolean!**

```python
import numpy as np

# Transformer attention mask — Boolean algebra in action!
seq_len = 5

# Causal mask: token i can only attend to tokens 0..i
causal_mask = np.tril(np.ones((seq_len, seq_len), dtype=bool))
print("Causal mask (lower triangle):")
print(causal_mask.astype(int))
# [[1, 0, 0, 0, 0],
#  [1, 1, 0, 0, 0],
#  [1, 1, 1, 0, 0],
#  [1, 1, 1, 1, 0],
#  [1, 1, 1, 1, 1]]

# Padding mask: positions 3,4 are padding (not real tokens)
padding_mask = np.array([True, True, True, False, False])

# Combined mask: causal AND not-padding (Boolean AND)
combined = causal_mask & padding_mask[np.newaxis, :]
print("\nCombined mask:")
print(combined.astype(int))
# [[1, 0, 0, 0, 0],
#  [1, 1, 0, 0, 0],
#  [1, 1, 1, 0, 0],
#  [1, 1, 1, 0, 0],
#  [1, 1, 1, 0, 0]]
```

📊 **Logic Gates as Neural Network Neurons:**
```
        x₁ ─┐
             ├──[w₁·x₁ + w₂·x₂ + b]──▶ σ(z) ──▶ output
        x₂ ─┘

AND gate: w₁=1, w₂=1, b=-1.5  → only fires when BOTH inputs ≈ 1
OR gate:  w₁=1, w₂=1, b=-0.5  → fires when EITHER input ≈ 1
NOT gate: w₁=-1, b=0.5        → flips the input
XOR gate: CANNOT be done with single neuron! (Minsky & Papert, 1969)
          → This is why we need HIDDEN LAYERS
```

```python
import numpy as np

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

# AND gate as a single neuron
def AND_neuron(x1, x2):
    w1, w2, b = 20, 20, -30  # large weights for sharp boundary
    return sigmoid(w1*x1 + w2*x2 + b)

# OR gate as a single neuron
def OR_neuron(x1, x2):
    w1, w2, b = 20, 20, -10
    return sigmoid(w1*x1 + w2*x2 + b)

# Test
for x1, x2 in [(0,0), (0,1), (1,0), (1,1)]:
    print(f"AND({x1},{x2})={AND_neuron(x1,x2):.3f}  "
          f"OR({x1},{x2})={OR_neuron(x1,x2):.3f}")
# AND(0,0)=0.000  OR(0,0)=0.000
# AND(0,1)=0.000  OR(0,1)=1.000
# AND(1,0)=0.000  OR(1,0)=1.000
# AND(1,1)=1.000  OR(1,1)=1.000
```

---

## 🔥 FAANG Deep Dive — Logic

### Interview Problem 1: Google — "Satisfiability"
> Given n boolean variables and a list of clauses (each a disjunction of literals), determine if there exists an assignment that makes all clauses true.

```python
from itertools import product

def is_satisfiable(n_vars, clauses):
    """
    Brute force SAT solver.
    clauses: list of lists. Each inner list has integers.
             Positive i means variable i is true.
             Negative -i means variable i is false.
    """
    for assignment in product([False, True], repeat=n_vars):
        all_satisfied = True
        for clause in clauses:
            clause_satisfied = False
            for literal in clause:
                var_idx = abs(literal) - 1
                val = assignment[var_idx]
                if literal > 0 and val:
                    clause_satisfied = True
                elif literal < 0 and not val:
                    clause_satisfied = True
            if not clause_satisfied:
                all_satisfied = False
                break
        if all_satisfied:
            return True, assignment
    return False, None

# (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ ¬x3)
result, assignment = is_satisfiable(3, [[1, 2], [-1, 3], [-2, -3]])
print(f"Satisfiable: {result}, Assignment: {assignment}")
```

### Interview Problem 2: Amazon — "Evaluate Boolean Expression"

```python
def eval_bool_expr(expression):
    """
    Evaluate: "T AND (F OR T)" → True
    Simple recursive descent parser.
    """
    tokens = expression.replace("(", " ( ").replace(")", " ) ").split()
    pos = [0]
    
    def parse():
        if tokens[pos[0]] == "(":
            pos[0] += 1  # skip (
            left = parse()
            op = tokens[pos[0]]
            pos[0] += 1
            right = parse()
            pos[0] += 1  # skip )
            if op == "AND":
                return left and right
            elif op == "OR":
                return left or right
        elif tokens[pos[0]] == "NOT":
            pos[0] += 1
            return not parse()
        else:
            val = tokens[pos[0]] == "T"
            pos[0] += 1
            return val
    
    return parse()

print(eval_bool_expr("(T AND (F OR T))"))  # True
print(eval_bool_expr("(T AND F)"))          # False
```

---

## ✅ Module 02 Checkpoint

- [ ] Build truth tables for any logical expression
- [ ] Distinguish between converse, inverse, and contrapositive
- [ ] Negate quantified statements correctly
- [ ] Understand how decision trees use predicates
- [ ] Map Boolean algebra to neural network neurons
- [ ] Explain why XOR requires a hidden layer

**Next →** [Module 03: Linear Systems](../module-03-linear-systems/README.md)
