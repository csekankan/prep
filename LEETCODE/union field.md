# Union-Find (Disjoint Set Union) — Deep Dive

> From "what does Union-Find actually do?" to "how do I pick it over BFS/DFS?"  
> Includes intuition, correctness, optimizations, step-by-step traces, common bugs, and 30+ practice problems.

---

## Table of Contents

1. [The Core Idea](#1-the-core-idea)
2. [Naive Union-Find — And Why It's Slow](#2-naive-union-find)
3. [Optimization 1: Union by Rank/Size](#3-union-by-ranksize)
4. [Optimization 2: Path Compression](#4-path-compression)
5. [Combined: Near-Constant Time Operations](#5-combined-near-constant-time)
6. [Step-by-Step Trace](#6-step-by-step-trace)
7. [Template Code (Copy-Paste Ready)](#7-template-code)
8. [When Union-Find vs BFS/DFS — Decision Framework](#8-decision-framework)
9. [Pattern 1: Connected Components — Count / Size / Check](#9-pattern-1-connected-components)
10. [Pattern 2: Complete Components](#10-pattern-2-complete-components)
11. [Pattern 3: Dynamic Connectivity — Process Edges Online](#11-pattern-3-dynamic-connectivity)
12. [Pattern 4: MST — Kruskal's Algorithm](#12-pattern-4-mst-kruskals)
13. [Pattern 5: Union-Find on Grid](#13-pattern-5-union-find-on-grid)
14. [Pattern 6: Accounts Merge / Grouping by Equivalence](#14-pattern-6-accounts-merge)
15. [Pattern 7: Redundant Connection — Cycle Detection](#15-pattern-7-redundant-connection)
16. [Pattern 8: Union-Find with Extra State](#16-pattern-8-extra-state)
17. [Case Study: LC 2685 — Count Complete Components (My Mistakes)](#17-case-study-lc-2685)
18. [Common Bugs & Pitfalls](#18-common-bugs)
19. [Practice Problems — Graded by Pattern](#19-practice-problems)
20. [Mental Checklist Before Coding](#20-mental-checklist)

---

## 1. The Core Idea

**Union-Find** answers one question efficiently: **are two elements in the same group?**

It supports two operations:
- **Find(x):** which group does x belong to? (returns the group's representative / root)
- **Union(x, y):** merge x's group and y's group into one

```
Before: {A, B, C}  {D, E}  {F}      ← 3 groups
Union(C, D)
After:  {A, B, C, D, E}  {F}        ← 2 groups
Find(A) == Find(E)?  → YES (same group)
Find(A) == Find(F)?  → NO  (different groups)
```

**Why not just use BFS/DFS?** You can — but Union-Find is better when:
- Edges arrive **one at a time** (online / streaming)
- You need to **merge groups** and **query connectivity** interleaved
- You want near-O(1) per operation instead of O(V+E) per BFS

---

## 2. Naive Union-Find

### The Array Representation

Each element points to a **parent**. The root of each tree is the group's representative (it points to itself).

```python
parent = [0, 1, 2, 3, 4]   # everyone is their own root initially
#          0  1  2  3  4
```

### Naive Find — Walk Up to Root

```python
def find(i):
    while parent[i] != i:
        i = parent[i]
    return i
```

### Naive Union — Attach One Root to Another

```python
def union(i, j):
    root_i = find(i)
    root_j = find(j)
    if root_i != root_j:
        parent[root_i] = root_j
```

### Why It's Slow

Without any optimization, `union` can create a **chain** (degenerate tree):

```
union(0,1), union(1,2), union(2,3), union(3,4):

0 → 1 → 2 → 3 → 4

find(0) walks 4 steps!
```

**Worst case:** O(n) per `find`, O(n) per `union`.  
After n unions and n finds: **O(n²) total.** TLE on n ≥ 10⁵.

---

## 3. Union by Rank/Size

### The Idea

Always attach the **smaller tree under the larger tree.** This keeps trees short.

```
BAD:  Tall tree under short tree → chain grows
      5                             5
      |         attach 1→2→3       |
      4          under 5           4
      |             ↓              |
      3                            3
      |                            |
      2                            2
      |                            |
      1                            1
                                   |
                                   6→7→8     ← height increased!

GOOD: Short tree under tall tree → height stays same
      5
      |
      4
      |
      3
      |
      2
      |
      1     6→7→8 goes under 5
     ↕ ↕
     result:
           5
         / |
        4  6
        |  |
        3  7
        |  |
        2  8
        |
        1
```

### Two Flavors

| Strategy | Track | Rule |
|----------|-------|------|
| **Union by rank** | Upper bound on height | Attach shorter tree under taller |
| **Union by size** | Number of nodes | Attach smaller tree under larger |

Both guarantee tree height ≤ O(log n). **Union by size is simpler and what I recommend.**

### Implementation (Union by Size)

```python
def union(i, j):
    pi, pj = find(i), find(j)
    if pi == pj:
        return  # already same group!
    if size[pi] >= size[pj]:
        parent[pj] = pi        # attach pj's tree under pi
        size[pi] += size[pj]
    else:
        parent[pi] = pj        # attach pi's tree under pj
        size[pj] += size[pi]
```

**Find is now O(log n)** because tree height ≤ log₂(n).

---

## 4. Path Compression

### The Idea

When you call `find(x)`, you walk from x up to the root. **Point every node on that path directly to the root.** Future finds from those nodes are O(1).

```
Before find(0):         After find(0):
    4                       4
    |                     / | \
    3                    0  1  3
    |                       |
    2                       2
    |
    1
    |
    0

find(0) walked 0→1→2→3→4, then set parent[0]=4, parent[1]=4, parent[2]=4, parent[3]=4
```

### Implementation (Recursive)

```python
def find(i):
    if parent[i] != i:
        parent[i] = find(parent[i])   # ASSIGNMENT, not comparison!
    return parent[i]
```

### Implementation (Iterative — No Recursion Limit)

```python
def find(i):
    root = i
    while parent[root] != root:
        root = parent[root]
    while parent[i] != root:       # second pass: compress
        parent[i], i = root, parent[i]
    return root
```

### ⚠️ The Classic Typo Bug

```python
# WRONG — == is comparison, not assignment
self.parent[i] == self.find(self.parent[i])   # does NOTHING, returns bool

# RIGHT — = is assignment
self.parent[i] = self.find(self.parent[i])    # actually compresses path
```

Python won't warn you. The `==` silently evaluates to `True` or `False` and discards the result. Your find "works" (returns the correct root via recursion) but **never compresses**, so every future find re-walks the chain. On large inputs → **TLE**.

---

## 5. Combined: Near-Constant Time

With **both** union by size/rank **and** path compression:

| Operation | Amortized Time |
|-----------|---------------|
| `find(x)` | O(α(n)) ≈ O(1) |
| `union(x,y)` | O(α(n)) ≈ O(1) |

α(n) is the **inverse Ackermann function.** For all practical inputs (n < 10⁸⁰), α(n) ≤ 4. It's effectively constant.

**Always use both optimizations together.** There's no reason not to.

---

## 6. Step-by-Step Trace

Let's trace through `n=6, edges = [(0,1), (1,2), (3,4), (2,4), (5,5)]`:

```
Initial:
parent: [0, 1, 2, 3, 4, 5]
size:   [1, 1, 1, 1, 1, 1]
Groups: {0} {1} {2} {3} {4} {5}

union(0, 1):
  find(0)=0, find(1)=1, sizes equal → parent[1]=0, size[0]=2
  parent: [0, 0, 2, 3, 4, 5]
  size:   [2, 1, 1, 1, 1, 1]
  Groups: {0,1} {2} {3} {4} {5}

union(1, 2):
  find(1): parent[1]=0, parent[0]=0 → root=0  (path compress: parent[1]=0, already done)
  find(2)=2, size[0]=2 > size[2]=1 → parent[2]=0, size[0]=3
  parent: [0, 0, 0, 3, 4, 5]
  size:   [3, 1, 1, 1, 1, 1]
  Groups: {0,1,2} {3} {4} {5}

union(3, 4):
  find(3)=3, find(4)=4, sizes equal → parent[4]=3, size[3]=2
  parent: [0, 0, 0, 3, 3, 5]
  size:   [3, 1, 1, 2, 1, 1]
  Groups: {0,1,2} {3,4} {5}

union(2, 4):
  find(2): parent[2]=0, parent[0]=0 → root=0
  find(4): parent[4]=3, parent[3]=3 → root=3  (path compress: parent[4]=3, already done)
  size[0]=3 > size[3]=2 → parent[3]=0, size[0]=5
  parent: [0, 0, 0, 0, 3, 5]
  size:   [5, 1, 1, 2, 1, 1]
  Groups: {0,1,2,3,4} {5}

find(4) later:
  parent[4]=3 → parent[3]=0 → parent[0]=0 → root=0
  path compress: parent[4]=0, parent[3]=0 (already 0)
  parent: [0, 0, 0, 0, 0, 5]   ← now 4 points directly to root
```

---

## 7. Template Code

### Standard Template (Use This)

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False  # already connected
        if self.size[px] < self.size[py]:
            px, py = py, px  # ensure px is the larger root
        self.parent[py] = px
        self.size[px] += self.size[py]
        self.components -= 1
        return True  # merged two different groups

    def connected(self, x, y):
        return self.find(x) == self.find(y)
```

### Iterative Find (For n > 10⁵ to Avoid Python Recursion Limit)

```python
import sys
sys.setrecursionlimit(200001)  # option A: raise the limit

# option B: iterative find (recommended for Python)
def find(self, x):
    root = x
    while self.parent[root] != root:
        root = self.parent[root]
    while self.parent[x] != root:
        self.parent[x], x = root, self.parent[x]
    return root
```

### Weighted Union-Find (Track Edge Weights / Offsets)

Used when you need relative values between nodes (e.g., LC 399 Evaluate Division):

```python
class WeightedUnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.weight = [1.0] * n  # weight[i] = ratio from i to parent[i]

    def find(self, x):
        if self.parent[x] != x:
            root = self.find(self.parent[x])
            self.weight[x] *= self.weight[self.parent[x]]
            self.parent[x] = root
        return self.parent[x]

    def union(self, x, y, w):
        """Set weight[x] / weight[y] = w"""
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        # w * weight[y] / weight[x] = ratio from px to py
        self.weight[px] = w * self.weight[y] / self.weight[x]
        self.parent[px] = py
```

---

## 8. When Union-Find vs BFS/DFS — Decision Framework

```
Question: Do I need to GROUP elements by connectivity?
│
├── Edges given upfront, query once?
│   └── BFS/DFS is simpler (one traversal, mark components)
│
├── Edges arrive one-by-one, queries interleaved?
│   └── ✅ UNION-FIND (BFS/DFS would recompute from scratch each time)
│
├── Need to detect a CYCLE in undirected graph?
│   └── ✅ UNION-FIND (union returns false → cycle found)
│   └── DFS also works, but UF is cleaner for "which edge causes the cycle?"
│
├── Need minimum spanning tree?
│   └── ✅ UNION-FIND + Kruskal's (sort edges, union greedily)
│
├── Need shortest path / distances?
│   └── ❌ NOT Union-Find. Use BFS/Dijkstra/Bellman-Ford.
│
├── Need to SPLIT groups (disconnect)?
│   └── ❌ Union-Find only supports merge, not split.
│   └── Trick: process in reverse order (removals become additions)
│
└── Grid with "expand region" / "merge islands"?
    └── ✅ UNION-FIND on (r*cols + c) coordinates
```

### Quick Comparison

| Feature | Union-Find | BFS/DFS |
|---------|-----------|---------|
| Build components from edge list | O(E · α(N)) ≈ O(E) | O(V + E) |
| Query "same component?" | O(α(N)) ≈ O(1) | O(V + E) per query |
| Add edge dynamically | O(α(N)) ≈ O(1) | Rebuild: O(V + E) |
| Count components | O(1) (track counter) | O(V + E) |
| Remove edge | ❌ Not supported | Rebuild |
| Find shortest path | ❌ Not supported | ✅ BFS/Dijkstra |

**Rule of thumb:** If the problem only cares about **which component** (not distances or paths), Union-Find is likely optimal.

---

## 9. Pattern 1: Connected Components — Count / Size / Check

### The Pattern

> "How many connected components?" or "What's the size of each component?"

This is the bread-and-butter use case.

### Template

```python
uf = UnionFind(n)
for u, v in edges:
    uf.union(u, v)

# Number of components
print(uf.components)

# Size of each component
from collections import Counter
roots = [uf.find(i) for i in range(n)]
component_sizes = Counter(roots)
```

### Key Problems

| # | Problem | Difficulty | Twist |
|---|---------|------------|-------|
| 323 | [Number of Connected Components](https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/) | Medium | Pure component counting |
| 547 | [Number of Provinces](https://leetcode.com/problems/number-of-provinces/) | Medium | Adjacency matrix input |
| 2316 | [Count Unreachable Pairs](https://leetcode.com/problems/count-unreachable-pairs-of-nodes-in-an-undirected-graph/) | Medium | Pairs across components = Σ(sᵢ × remaining) |

---

## 10. Pattern 2: Complete Components

### The Pattern

> "Is every node in a component connected to every other node in that component?"

A component of size k is **complete** if it has exactly k × (k-1) / 2 edges, or equivalently, every node has degree k-1.

### Strategy

1. Build Union-Find from edges
2. For each component, collect its size and edge count
3. Check: edge_count == size × (size - 1) / 2

```python
def countCompleteComponents(n, edges):
    uf = UnionFind(n)
    for u, v in edges:
        uf.union(u, v)

    comp_size = Counter()
    comp_edges = Counter()

    for i in range(n):
        comp_size[uf.find(i)] += 1

    for u, v in edges:
        comp_edges[uf.find(u)] += 1

    count = 0
    for root in comp_size:
        s = comp_size[root]
        e = comp_edges[root]
        if e == s * (s - 1) // 2:
            count += 1
    return count
```

### Key Problems

| # | Problem | Difficulty | Twist |
|---|---------|------------|-------|
| 2685 | [Count Complete Components](https://leetcode.com/problems/count-the-number-of-complete-components/) | Medium | Check edge count per component |

---

## 11. Pattern 3: Dynamic Connectivity — Process Edges Online

### The Pattern

> Edges arrive one at a time. After each edge, answer a query (component count, "are X and Y connected?", etc.)

Union-Find handles this in O(α(n)) per edge. BFS/DFS would need O(V+E) per query.

### Key Problems

| # | Problem | Difficulty | Twist |
|---|---------|------------|-------|
| 305 | [Number of Islands II](https://leetcode.com/problems/number-of-islands-ii/) | Hard | Grid cells added one by one, count islands after each |
| 1319 | [Number of Operations to Make Network Connected](https://leetcode.com/problems/number-of-operations-to-make-network-connected/) | Medium | Each failed union = redundant cable; need (components-1) cables |
| 2076 | [Process Restricted Friend Requests](https://leetcode.com/problems/process-restricted-friend-requests/) | Hard | Union only if no restriction violated; rollback on failure |

---

## 12. Pattern 4: MST — Kruskal's Algorithm

### The Pattern

> "Find the minimum spanning tree" or "minimum cost to connect all nodes."

**Kruskal's:** Sort edges by weight. Greedily add the lightest edge that connects two different components (i.e., union returns True).

```python
edges.sort(key=lambda e: e[2])  # sort by weight
uf = UnionFind(n)
mst_cost = 0
for u, v, w in edges:
    if uf.union(u, v):
        mst_cost += w
# If uf.components > 1, graph is disconnected (no MST exists)
```

### Key Problems

| # | Problem | Difficulty | Twist |
|---|---------|------------|-------|
| 1135 | [Connecting Cities With Minimum Cost](https://leetcode.com/problems/connecting-cities-with-minimum-cost/) | Medium | Pure Kruskal's |
| 1584 | [Min Cost to Connect All Points](https://leetcode.com/problems/min-cost-to-connect-all-points/) | Medium | Generate all O(n²) edges, then Kruskal's |
| 1168 | [Optimize Water Distribution in a Village](https://leetcode.com/problems/optimize-water-distribution-in-a-village/) | Hard | Add virtual node 0, well[i] = edge (0, i, cost) |
| 1489 | [Find Critical and Pseudo-Critical Edges in MST](https://leetcode.com/problems/find-critical-and-pseudo-critical-edges-in-minimum-spanning-tree/) | Hard | For each edge: try MST without it (critical?), try MST forcing it (pseudo-critical?) |

---

## 13. Pattern 5: Union-Find on Grid

### The Pattern

> Grid problems where you merge adjacent cells — "number of islands", "largest island", etc.

**Key trick:** Flatten 2D coordinates to 1D: `id = row * cols + col`.

```python
uf = UnionFind(rows * cols)
for r in range(rows):
    for c in range(cols):
        if grid[r][c] == 1:
            for dr, dc in [(0,1),(1,0)]:  # only right and down to avoid double-counting
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    uf.union(r * cols + c, nr * cols + nc)
```

### Key Problems

| # | Problem | Difficulty | Twist |
|---|---------|------------|-------|
| 200 | [Number of Islands](https://leetcode.com/problems/number-of-islands/) | Medium | Classic; BFS also works |
| 305 | [Number of Islands II](https://leetcode.com/problems/number-of-islands-ii/) | Hard | Cells added online → UF shines over BFS |
| 827 | [Making A Large Island](https://leetcode.com/problems/making-a-large-island/) | Hard | Find components, then try flipping each 0 |
| 1061 | [Lexicographically Smallest Equivalent String](https://leetcode.com/problems/lexicographically-smallest-equivalent-string/) | Medium | Union characters, root = smallest in group |
| 130 | [Surrounded Regions](https://leetcode.com/problems/surrounded-regions/) | Medium | Union border O's to a virtual node |

---

## 14. Pattern 6: Accounts Merge / Grouping by Equivalence

### The Pattern

> "Group items where any shared attribute means they're the same entity."

Union-Find is natural here because transitivity is built in: if A shares email with B, and B shares email with C, then A, B, C are all one person.

```python
# Accounts Merge (LC 721)
email_to_id = {}
uf = UnionFind(len(accounts))

for i, account in enumerate(accounts):
    for email in account[1:]:
        if email in email_to_id:
            uf.union(i, email_to_id[email])
        email_to_id[email] = i

# Group emails by root account
groups = defaultdict(list)
for email, idx in email_to_id.items():
    groups[uf.find(idx)].append(email)
```

### Key Problems

| # | Problem | Difficulty | Twist |
|---|---------|------------|-------|
| 721 | [Accounts Merge](https://leetcode.com/problems/accounts-merge/) | Medium | Shared email = same person |
| 737 | [Sentence Similarity II](https://leetcode.com/problems/sentence-similarity-ii/) | Medium | Transitive word similarity |
| 990 | [Satisfiability of Equality Equations](https://leetcode.com/problems/satisfiability-of-equality-equations/) | Medium | Process `==` first (union), then check `!=` |
| 399 | [Evaluate Division](https://leetcode.com/problems/evaluate-division/) | Medium | Weighted Union-Find (ratios along edges) |

---

## 15. Pattern 7: Redundant Connection — Cycle Detection

### The Pattern

> "Which edge, if removed, breaks a cycle?" or "Find the extra edge in a tree."

A tree with n nodes has exactly n-1 edges. If you have n edges, exactly one creates a cycle. Process edges one by one — the first edge where `union` returns False (both endpoints already connected) is the redundant one.

```python
uf = UnionFind(n + 1)  # 1-indexed nodes
for u, v in edges:
    if not uf.union(u, v):
        return [u, v]   # this edge created a cycle
```

### Key Problems

| # | Problem | Difficulty | Twist |
|---|---------|------------|-------|
| 684 | [Redundant Connection](https://leetcode.com/problems/redundant-connection/) | Medium | Undirected graph, find the cycle-creating edge |
| 685 | [Redundant Connection II](https://leetcode.com/problems/redundant-connection-ii/) | Hard | Directed graph; handle double-parent + cycle |
| 1579 | [Remove Max Number of Edges](https://leetcode.com/problems/remove-max-number-of-edges-to-keep-graph-fully-traversable/) | Hard | Two UFs (Alice/Bob), process type-3 edges first |

---

## 16. Pattern 8: Union-Find with Extra State

### The Pattern

Sometimes you need to track more than just connectivity:
- **Edge count per component** (complete component check)
- **Weight/ratio between nodes** (evaluate division)
- **Bipartiteness** (same or different partition)

Add extra arrays alongside `parent` and `size`:

```python
class UnionFindWithEdges:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.edges = [0] * n  # edge count per component

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            self.edges[px] += 1  # edge within same component
            return False
        if self.size[px] < self.size[py]:
            px, py = py, px
        self.parent[py] = px
        self.size[px] += self.size[py]
        self.edges[px] += self.edges[py] + 1  # merge edges + this new edge
        return True
```

---

## 17. Case Study: LC 2685 — Count Complete Components (My Mistakes)

### Problem

Given n nodes and edges, count connected components where **every pair of nodes is directly connected** (the component is a complete subgraph).

### Mistake 1: `==` vs `=` in Path Compression (SILENT BUG → TLE)

```python
# WRONG — comparison, not assignment. Python doesn't warn you!
def find(self, i):
    if self.parent[i] == i:
        return i
    self.parent[i] == self.find(self.parent[i])   # ← BUG: == does nothing
    return self.parent[i]

# RIGHT — assignment with single =
def find(self, i):
    if self.parent[i] == i:
        return i
    self.parent[i] = self.find(self.parent[i])    # ← actually compresses path
    return self.parent[i]
```

**Why it causes TLE:**
The `find` still returns the correct root (the recursion reaches the root and returns it). But `self.parent[i]` is never updated — so next time `find(i)` is called, it walks the entire chain again. With n = 50 and many queries, this doesn't TLE. But on n = 10⁵, each find is O(n) instead of O(α(n)), turning the whole algorithm from O(n) to O(n²).

**How to catch it:** Test with a long chain: `union(0,1), union(1,2), ..., union(n-2, n-1)`, then call `find(0)` twice. With compression, the second call is O(1). Without, it's O(n).

### Mistake 2: Re-parenting the Node Instead of the Root

```python
# WRONG — attaches node i, not root pi
def union(self, i, j):
    pi = self.find(i)
    pj = self.find(j)
    if self.len[pi] >= self.len[pj]:
        self.parent[i] = self.find(pj)    # ← BUG: should be parent[pj] = pi
        self.len[pi] += self.len[pj]

# RIGHT — always re-parent the ROOT
def union(self, i, j):
    pi = self.find(i)
    pj = self.find(j)
    if pi == pj:
        return
    if self.size[pi] >= self.size[pj]:
        self.parent[pj] = pi              # ← root pj goes under root pi
        self.size[pi] += self.size[pj]
    else:
        self.parent[pi] = pj
        self.size[pj] += self.size[pi]
```

**What goes wrong:**
Setting `self.parent[i] = pj` detaches node `i` from its original tree, but the rest of the tree (rooted at `pi`) still exists separately. You've split the tree instead of merging it.

```
Before: Tree A:  pi ← ... ← i       Tree B: pj ← ...

WRONG union: only move i under pj
  Tree A becomes: pi ← ... (without i)    pj ← ... ← i
  Nodes between pi and i are ORPHANED from i's new tree!

RIGHT union: move root pi under pj (or vice versa)
  pj ← pi ← ... ← i     All of Tree A is now under pj
```

### Mistake 3: Missing `pi == pj` Guard (CAUSES TLE)

```python
# WRONG — no guard
def union(self, i, j):
    pi = self.find(i)
    pj = self.find(j)
    self.parent[pj] = pi
    self.size[pi] += self.size[pj]   # doubles the size even though nothing merged!

# RIGHT — guard against same-component union
def union(self, i, j):
    pi = self.find(i)
    pj = self.find(j)
    if pi == pj:
        return                        # already in same group, nothing to do
    self.parent[pj] = pi
    self.size[pi] += self.size[pj]
```

**Why it causes TLE:**

Without the guard, unioning two nodes in the **same** component:
1. **Corrupts `size`:** `size[pi] += size[pj]` doubles the size since `pi == pj`, and `self.parent[pj] = pi` is a no-op. Every redundant edge inflates the size counter.
2. **Inflated sizes break union-by-size:** The invariant "size tracks actual node count" is destroyed. The tree that got inflated always "wins" future unions, creating a long chain.
3. **Long chains → O(n) finds:** Without union-by-size working correctly, tree height can reach O(n), and path compression alone can't save you from O(n log n) worst case.

On a complete graph with n nodes, there are n(n-1)/2 edges but only n-1 productive unions. The remaining ~n²/2 redundant union calls each corrupt the size. This cascades into O(n²) time.

### Mistake 4: Reading `self.parent` Directly Without Compressing

```python
# WRONG — parent[i] might not point to root
def getParents(self):
    return Counter(self.parent), self.parent

# RIGHT — call find(i) for every node first
def getParents(self):
    parents = [self.find(i) for i in range(self.n)]
    return Counter(parents), parents
```

After unions, the parent array looks like a forest of trees. `parent[i]` points to i's **immediate** parent, not necessarily the root. Only `find(i)` (with path compression) guarantees you get the root.

### My Corrected Solution

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.size[px] < self.size[py]:
            px, py = py, px
        self.parent[py] = px
        self.size[px] += self.size[py]

class Solution:
    def countCompleteComponents(self, n: int, edges: List[List[int]]) -> int:
        uf = UnionFind(n)
        for u, v in edges:
            uf.union(u, v)

        comp_size = Counter()
        comp_edges = Counter()

        for i in range(n):
            comp_size[uf.find(i)] += 1

        for u, v in edges:
            comp_edges[uf.find(u)] += 1

        return sum(
            1 for root in comp_size
            if comp_edges[root] == comp_size[root] * (comp_size[root] - 1) // 2
        )
```

---

## 18. Common Bugs & Pitfalls

### Bug 1: `==` vs `=` in Path Compression

```python
self.parent[i] == self.find(self.parent[i])   # WRONG: comparison
self.parent[i] = self.find(self.parent[i])    # RIGHT: assignment
```

Symptoms: correct answers on small inputs, TLE on large inputs. Python gives zero warnings.

### Bug 2: Re-parenting the Node, Not the Root

```python
self.parent[i] = pj    # WRONG: moves node i, orphans the rest of its tree
self.parent[pi] = pj   # RIGHT: moves entire tree rooted at pi
```

Symptoms: components fragment unexpectedly. Some nodes report wrong roots.

### Bug 3: Missing `pi == pj` Guard

```python
# Without guard, same-component unions corrupt size[]
if pi == pj:
    return  # ALWAYS check this before merging
```

Symptoms: size array inflates → union-by-size degenerates → O(n) finds → TLE.

### Bug 4: Using 0-Indexed vs 1-Indexed Nodes

Many problems use 1-indexed nodes. If you create `UnionFind(n)` but nodes go from 1 to n, you'll get index out of bounds or mix up node 0.

```python
uf = UnionFind(n + 1)  # for 1-indexed problems
```

### Bug 5: Forgetting to Call find() Before Reading parent[]

```python
# parent[i] is NOT the root — it's just the immediate parent
# Always use find(i) to get the actual root
```

### Bug 6: Python Recursion Limit

Recursive `find` on a chain of 10⁵ nodes hits Python's default recursion limit (1000).

```python
import sys
sys.setrecursionlimit(200001)  # or use iterative find
```

### Bug 7: Union-Find Doesn't Support Deletion

If you need to **remove** edges or **split** components, Union-Find can't do it directly. Common trick: **process in reverse** (removals become additions).

---

## 19. Practice Problems — Graded by Pattern

### Tier 1: Pure Component Counting (Warm-Up)

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 323 | [Number of Connected Components](https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/) | Medium | Track component count, decrement on each successful union |
| 547 | [Number of Provinces](https://leetcode.com/problems/number-of-provinces/) | Medium | Adjacency matrix; union i,j if `isConnected[i][j]==1` |
| 200 | [Number of Islands](https://leetcode.com/problems/number-of-islands/) | Medium | Grid UF: `id = r * cols + c` |

### Tier 2: Redundant Edge / Cycle Detection

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 684 | [Redundant Connection](https://leetcode.com/problems/redundant-connection/) | Medium | First edge where union fails = the answer |
| 685 | [Redundant Connection II](https://leetcode.com/problems/redundant-connection-ii/) | Hard | Directed: handle double-parent + cycle |
| 261 | [Graph Valid Tree](https://leetcode.com/problems/graph-valid-tree/) | Medium | Tree = n-1 edges + fully connected |

### Tier 3: MST / Minimum Cost Connectivity

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 1135 | [Connecting Cities With Min Cost](https://leetcode.com/problems/connecting-cities-with-minimum-cost/) | Medium | Sort edges by weight, Kruskal's |
| 1584 | [Min Cost to Connect All Points](https://leetcode.com/problems/min-cost-to-connect-all-points/) | Medium | Generate all edges (Manhattan dist), Kruskal's |
| 1168 | [Optimize Water Distribution](https://leetcode.com/problems/optimize-water-distribution-in-a-village/) | Hard | Virtual node trick: well cost = edge to node 0 |
| 1489 | [Critical and Pseudo-Critical Edges in MST](https://leetcode.com/problems/find-critical-and-pseudo-critical-edges-in-minimum-spanning-tree/) | Hard | Try excluding / forcing each edge |

### Tier 4: Grid Union-Find

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 305 | [Number of Islands II](https://leetcode.com/problems/number-of-islands-ii/) | Hard | Online cell additions; union with 4 neighbors |
| 827 | [Making A Large Island](https://leetcode.com/problems/making-a-large-island/) | Hard | UF to find components, then try flipping each 0 |
| 130 | [Surrounded Regions](https://leetcode.com/problems/surrounded-regions/) | Medium | Union border O's to a virtual node |
| 1391 | [Check if Path Exists in Grid](https://leetcode.com/problems/check-if-there-is-a-valid-path-in-a-grid/) | Medium | Union cells by street type connections |

### Tier 5: Equivalence Grouping / Merging

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 721 | [Accounts Merge](https://leetcode.com/problems/accounts-merge/) | Medium | Shared email = same person (union by email) |
| 990 | [Satisfiability of Equality Equations](https://leetcode.com/problems/satisfiability-of-equality-equations/) | Medium | Process `==` first, then check `!=` |
| 399 | [Evaluate Division](https://leetcode.com/problems/evaluate-division/) | Medium | Weighted UF: edges carry ratio values |
| 737 | [Sentence Similarity II](https://leetcode.com/problems/sentence-similarity-ii/) | Medium | Transitive similarity = UF |
| 1061 | [Lexicographically Smallest Equivalent String](https://leetcode.com/problems/lexicographically-smallest-equivalent-string/) | Medium | Union chars, root = smallest in group |

### Tier 6: Advanced / Dynamic / Trick

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 2685 | [Count Complete Components](https://leetcode.com/problems/count-the-number-of-complete-components/) | Medium | Track edge count per component |
| 1579 | [Remove Max Edges](https://leetcode.com/problems/remove-max-number-of-edges-to-keep-graph-fully-traversable/) | Hard | Two UFs (Alice/Bob), process type-3 first |
| 2076 | [Process Restricted Friend Requests](https://leetcode.com/problems/process-restricted-friend-requests/) | Hard | Tentative union + rollback |
| 2316 | [Count Unreachable Pairs](https://leetcode.com/problems/count-unreachable-pairs-of-nodes-in-an-undirected-graph/) | Medium | Pairs = Σ(sᵢ × remaining) |
| 1632 | [Rank Transform of a Matrix](https://leetcode.com/problems/rank-transform-of-a-matrix/) | Hard | UF groups same-value cells sharing row/col |
| 928 | [Minimize Malware Spread II](https://leetcode.com/problems/minimize-malware-spread-ii/) | Hard | UF on non-infected nodes, check infected neighbors |
| 803 | [Bricks Falling When Hit](https://leetcode.com/problems/bricks-falling-when-hit/) | Hard | Reverse time trick: removals become additions |

### Tier 7: Contest / Expert

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 2421 | [Number of Good Paths](https://leetcode.com/problems/number-of-good-paths/) | Hard | Process nodes by value, union with smaller neighbors |
| 1697 | [Checking Existence of Edge Length Limited Paths](https://leetcode.com/problems/checking-existence-of-edge-length-limited-paths/) | Hard | Offline: sort queries + edges by weight, union incrementally |
| 2503 | [Maximum Number of Points From Grid Queries](https://leetcode.com/problems/maximum-number-of-points-from-grid-queries/) | Hard | Sort queries, BFS/UF expanding grid cells by value |
| 1724 | [Checking Existence of Edge Length Limited Paths II](https://leetcode.com/problems/checking-existence-of-edge-length-limited-paths-ii/) | Hard | Online version: persistent UF / Kruskal's tree |

---

## 20. Mental Checklist Before Coding

```
□ What are the elements? What gets grouped?
  → Nodes? Grid cells? Emails? Characters?

□ Do I need Union-Find or is BFS/DFS enough?
  → Edges arrive online / interleaved with queries? → UF
  → Process all edges first, query once? → BFS/DFS is simpler

□ What's my index space?
  → Nodes 0 to n-1? → UnionFind(n)
  → Nodes 1 to n? → UnionFind(n+1)
  → Grid? → UnionFind(rows * cols), id = r * cols + c

□ Do I need extra state per component?
  → Edge count (complete check): track edges[] alongside size[]
  → Weight/ratio: weighted UF
  → Just connectivity: standard template is enough

□ Did I include BOTH optimizations?
  → Path compression in find()  (parent[x] = find(parent[x]))
  → Union by size in union()     (attach smaller under larger)

□ Did I guard against same-component union?
  → if px == py: return  (ALWAYS check this)

□ Am I reading find(x) for roots, not parent[x]?
  → parent[x] is immediate parent, NOT the root

□ Will n > 1000?
  → Use iterative find, or set sys.setrecursionlimit

□ Does the problem require deletion/splitting?
  → UF can't split. Process in reverse (removals → additions).
```

---

## Appendix: Union-Find vs DFS for "Number of Islands"

Both work for LC 200. Here's the trade-off:

| Approach | Time | Space | When Better |
|----------|------|-------|-------------|
| DFS/BFS | O(mn) | O(mn) visited array | Simpler; one-shot query |
| Union-Find | O(mn · α(mn)) ≈ O(mn) | O(mn) parent array | Cells added incrementally (LC 305) |

For the static version (all cells given upfront), DFS is simpler and slightly faster. For the dynamic version (cells added one at a time), Union-Find is the only efficient choice.
