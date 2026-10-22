# LeetCode Learning Project

## Overall Observations

You are already thinking at a strong intermediate/advanced level in algorithms.

Most of your mistakes are NOT:

* wrong algorithm choice
* lack of DS/Algo knowledge
* brute force thinking

Instead, your mistakes are usually:

* missing one optimization causing TLE
* implementation inefficiency
* repeated processing in BFS/graphs
* edge-case state management
* queue/visited timing issues

This is actually a good progression stage.

---

# Your Thinking Pattern

## Strengths

### 1. You naturally think in graph transformations

You often convert problems into:

* BFS
* implicit graph
* mapping relationships
* preprocessing for fast traversal

This is advanced thinking.

Examples:

* Prime jump problem
* Event scheduling
* Rotation/gravity problem

---

### 2. You avoid brute force early

You usually try to:

* preprocess
* build maps
* use sieve/hashmaps/prefix ideas
* reduce nested loops

Good competitive programming instinct.

---

### 3. You try to optimize before finishing

You often ask:

* “what is optimal?”
* “is my approach optimized?”
* “why TLE?”

This is very useful for improving.

---

# Repeated Mistake Patterns

## Pattern 1: Reprocessing adjacency repeatedly

### Seen In

* Prime jump BFS problem

### Mistake

You processed the same adjacency/group many times.

Example:

```python
for i in jumpNonPrime[nums[ind]]:
```

repeated for every node with same prime.

### Learning

In BFS problems with:

* teleport groups
* same-value groups
* buses/routes
* word transformations

usually:

```python
after processing a group once:
clear/delete it
```

This converts:

```text
O(n^2) -> O(n)
```

### Future Reminder

Whenever you see:

* hashmap → list of nodes
* repeated traversal possibility

ask:

> “Can this adjacency be consumed only once?”

---

# Pattern 2: Marking visited too late

### Seen In

Multiple BFS implementations.

### Mistake

Sometimes visited was marked during pop instead of push.

### Problem

Same node can enter queue multiple times.

### Correct Pattern

```python
visited[nxt] = True
q.append(nxt)
```

mark immediately during enqueue.

---

# Pattern 3: Correct idea, slightly inefficient implementation

### Seen In

* sieve construction
* loops
* repeated prime checks

### Example

```python
len(factors[i]) == 1
```

called many times.

### Learning

Once algorithm is correct:

next stage is:

* reducing repeated work
* reducing repeated function calls
* reducing repeated iterations

---

# Pattern 4: Good intuition for preprocessing

You frequently use:

* sieve
* factorization
* maps
* prefix-style preprocessing
* implicit graphs

This is one of your strongest areas.

You should continue strengthening:

* graph optimization
* state compression
* DP transitions
* monotonic structures

---

# Question-Specific Notes

# 1. Prime Jump / Minimum Jumps Problem

## Your Core Idea

Very strong.

You realized:

* graph should not be explicitly built
* use prime factor mapping
* BFS shortest path

That is advanced modeling.

## Main Mistake

Repeated traversal of same prime group.

## Important Learning

For grouped BFS transitions:

```python
graph[group].clear()
```

is often critical.

## Your Growth Signal

This was not a beginner mistake.
This is optimization-level debugging.

---

# 2. Rotate The Box

## Your Strength

You focused on:

* simulation
* transformation
* gravity mechanics

## Learning Direction

For matrix simulation problems:

Always ask:

1. Can operation order be reversed?
2. Can rotation + gravity be separated?
3. Can two passes become one?

You are good at getting correct solutions.
Next level:

* cleaner state transitions
* in-place optimization
* reducing auxiliary memory

---

# 3. Two Non-Overlapping Events

## Your Strength

You naturally moved toward:

* interval reasoning
* optimization
* event ordering

Good sign for:

* binary search on intervals
* sweep line
* DP + sorting problems

## Learning Direction

Strengthen:

* interval DP
* weighted interval scheduling
* prefix/suffix maximum patterns

These will unlock many hard problems.

---

# Current Algorithm Profile

## Strong Areas

### Good

* BFS
* Graph modeling
* Hashmaps
* Preprocessing
* Simulation
* Sieve/factorization
* Optimization intuition

### Improving

* DP
* Greedy proof reasoning
* Advanced graph pruning
* Complexity analysis precision
* State deduplication

---

# Biggest Improvement Opportunity

## Before coding BFS/Graph

Always ask:

### 1.

> Can same state enter queue multiple times?

### 2.

> Can same adjacency list be processed multiple times?

### 3.

> Is there repeated work hidden inside loops?

### 4.

> Am I revisiting groups instead of nodes?

These four questions alone will remove many TLEs.

---

# Recommended Learning Path

## Phase 1 — Master BFS Optimizations

Focus on:

* Jump Game IV
* Bus Routes
* Word Ladder
* Multi-source BFS
* 0-1 BFS
* State BFS

Goal:
recognize repeated adjacency problems instantly.

---

## Phase 2 — Interval + DP

Focus on:

* weighted interval scheduling
* LIS variations
* prefix/suffix DP
* memoization → tabulation conversion

---

## Phase 3 — Advanced Graph Thinking

Focus on:

* implicit graph reduction
* pruning
* shortest path variants
* DSU
* topological optimization

---

# 4. Jump Game IX (LeetCode 3660)

## Your Initial Thought Process

You correctly identified:

* prefix maximum matters
* suffix minimum matters
* answers propagate across ranges

These are the hardest observations in the problem.

You were already thinking in terms of:

* connectivity
* propagation
* interval influence

which is strong algorithmic intuition.

---

## Where Your Logic Went Wrong

You tracked:

```python
prefixMinInd[i]
```

meaning:

```text
where is the minimum on the right?
```

But the real problem only needs:

```text
Does ANY smaller value exist on the right?
```

This is an important pattern:

```text
existence condition
!=
exact position tracking
```

You added extra complexity by storing the exact minimum index.

---

## Core Insight

For an index i:

If:

```text
bigger value exists on left
AND
smaller value exists on right
```

then current index connects both sides.

This merges connected components.

Equivalent condition:

```python
prefixMax[i] > suffixMin
```

because:

* prefixMax[i] means bigger exists on left
* suffixMin means smaller exists on right

---

## Important Mental Model

This problem is secretly:

```text
connected component merging
```

not greedy.

Once an index bridges left and right:

```text
left component <-> current index <-> right component
```

all become one connected component.

Then the answer propagates.

---

## Editorial Difficulty Observation

The editorial explanations were much more complicated than necessary for first understanding.

They used:

* interval divide and conquer
* connected component proofs
* monotonic stack component merging
* interval transfer reasoning

These are proof-oriented explanations.

Your simpler understanding:

```text
left bigger + right smaller
=> merge components
```

is actually the correct intuition-first approach.

---

## Important Learning Pattern

You often try to:

```text
track exact structure/index
```

when problem only needs:

```text
existence of condition
```

Future optimization question to ask:

> “Do I need the exact index/value/path,
> or only whether the condition exists?”

This will simplify many:

* greedy
* interval
* graph
* DP problems

---

## Growth Observation

You are already doing something strong:

```text
trying to deeply understand editorials
instead of memorizing solutions
```

That is exactly how advanced problem-solving intuition develops.

# Final Assessment

You are already beyond the “brute-force beginner” stage.

Your current stage is:

```text
Correct algorithm
   ↓
Missed optimization
   ↓
TLE/debugging
```

That is a strong stage to be in.

The next jump in your growth will come from:

* recognizing repeated processing instantly
* understanding amortized complexity deeply
* cleaner BFS/graph implementations
* stronger DP structure recognition

Your thought process is already competitive-programming oriented.
