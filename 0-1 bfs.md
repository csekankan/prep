# Dijkstra & 0-1 BFS — Deep Dive

> From "why does Dijkstra work?" to "when do I reach for a deque instead of a heap?"  
> Includes intuition, correctness proofs, step-by-step traces, common bugs, and 30+ practice problems.

---

## Table of Contents

1. [The Core Idea — Shortest Path in Weighted Graphs](#1-the-core-idea)
2. [Dijkstra's Algorithm — Full Breakdown](#2-dijkstras-algorithm)
   - [Intuition](#intuition)
   - [Why Dijkstra is Greedy (and Why It Works)](#why-dijkstra-is-greedy)
   - [Step-by-Step Trace](#step-by-step-trace)
   - [Implementation — Adjacency List](#implementation-adjacency-list)
   - [Implementation — Grid](#implementation-grid)
   - [Complexity Analysis](#complexity-analysis)
3. [0-1 BFS — The Deque Trick](#3-0-1-bfs)
   - [Why Not Just Use Dijkstra?](#why-not-just-use-dijkstra)
   - [How the Deque Maintains Sorted Order](#how-the-deque-maintains-sorted-order)
   - [Step-by-Step Trace](#0-1-bfs-trace)
   - [Implementation](#0-1-bfs-implementation)
4. [Dijkstra vs 0-1 BFS vs BFS — Decision Framework](#4-decision-framework)
5. [Variant: Bottleneck Shortest Path (Max-Min / Min-Max)](#5-bottleneck-shortest-path)
6. [Variant: Dijkstra with State (r, c, extra)](#6-dijkstra-with-state)
7. [Case Study: LC 3286 — Find a Safe Walk Through a Grid](#7-case-study-safe-walk)
8. [Common Bugs & Pitfalls](#8-common-bugs)
9. [Practice Problems — Graded by Pattern](#9-practice-problems)
10. [Mental Checklist Before Coding](#10-mental-checklist)

---

## 1. The Core Idea

**Single-source shortest path (SSSP):** Given a graph with non-negative edge weights and a source node, find the minimum-cost path from source to every other node.

Three algorithms solve this, each optimized for different weight constraints:

```
                        Edge weights
                            │
            ┌───────────────┼───────────────┐
            │               │               │
       All equal        Only {0, 1}     Arbitrary ≥ 0
            │               │               │
          BFS           0-1 BFS         Dijkstra
        O(V + E)        O(V + E)      O((V+E) log V)
        (queue)         (deque)         (min-heap)
```

The key insight: **all three algorithms process nodes in non-decreasing order of distance.** They differ only in the data structure that maintains this order.

| Algorithm | Data Structure | Why It Maintains Order |
|-----------|---------------|----------------------|
| BFS | Queue (FIFO) | All edges weight 1, so distance = depth = FIFO order |
| 0-1 BFS | Deque | 0-cost goes front (same level), 1-cost goes back (next level) |
| Dijkstra | Min-heap | Arbitrary weights need explicit sorting by cost |

---

## 2. Dijkstra's Algorithm

### Intuition

Imagine pouring water at the source node. Water flows along edges, moving slower on heavier edges. **The order in which nodes get wet is the order Dijkstra processes them.** The first time a node gets wet, that's its shortest distance — water can't arrive faster via a longer detour.

```
Source: A
        A ──2──▶ B ──1──▶ D
        │                  ▲
        3                  1
        │                  │
        ▼                  │
        C ───────1────────▶

Water reaches: A(0) → B(2) → C(3) → D(3)
               └ via A   └ via A   └ via B (cost 2+1=3, beats C→D = 3+1=4)
```

### Why Dijkstra is Greedy

**Claim:** When Dijkstra pops a node `u` from the min-heap, `dist[u]` is already optimal.

**Proof by contradiction:**
1. Suppose Dijkstra pops `u` with distance `d`, but there exists a shorter path of cost `d' < d`.
2. That shorter path must go through some node `v` that hasn't been popped yet (otherwise `u`'s distance would have been updated).
3. But `v` is still in the heap with `dist[v] ≥ d` (since the heap popped `u` first).
4. Since all edge weights are ≥ 0, the path through `v` costs at least `dist[v] ≥ d > d'` — contradiction.

**This is why Dijkstra fails with negative edges:** step 4 breaks. A node behind `u` in the heap could have a shortcut through a negative edge, making the total less than `d`.

### Step-by-Step Trace

```
Graph:
  A ──1──▶ B
  │        │
  4        2
  │        │
  ▼        ▼
  C ──3──▶ D ──1──▶ E

Start: A, Target: E
```

| Step | Pop from heap | dist[] updated | Heap state |
|------|--------------|----------------|------------|
| init | — | A=0 | [(0,A)] |
| 1 | A (cost 0) | B=1, C=4 | [(1,B), (4,C)] |
| 2 | B (cost 1) | D=3 | [(3,D), (4,C)] |
| 3 | D (cost 3) | E=4 | [(4,C), (4,E)] |
| 4 | C (cost 4) | D already 3 ≤ 7, skip | [(4,E)] |
| 5 | E (cost 4) | done | [] |

**Answer:** shortest path A→E = 4 (A→B→D→E)

**Notice:** C was popped but couldn't improve D. That's fine — the `if new_cost < dist[nr]` check rejects stale updates.

### Implementation — Adjacency List

```python
import heapq
from collections import defaultdict

def dijkstra(graph: dict[int, list[tuple[int, int]]], source: int, target: int) -> int:
    """
    graph: adjacency list {node: [(neighbor, weight), ...]}
    Returns shortest distance from source to target, or -1 if unreachable.
    """
    dist = defaultdict(lambda: float('inf'))
    dist[source] = 0
    heap = [(0, source)]

    while heap:
        cost, node = heapq.heappop(heap)
        if node == target:
            return cost
        if cost > dist[node]:          # stale entry — skip
            continue
        for neighbor, weight in graph[node]:
            new_cost = cost + weight
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                heapq.heappush(heap, (new_cost, neighbor))

    return -1
```

**Why `if cost > dist[node]: continue`?**  
The heap may contain multiple entries for the same node (we push without removing old entries — "lazy deletion"). When we pop a stale entry where `cost > dist[node]`, the node was already finalized via a cheaper path. Skipping avoids redundant work.

### Implementation — Grid

```python
import heapq

def dijkstra_grid(grid: list[list[int]], start: tuple, end: tuple) -> int:
    """Find minimum-cost path in a weighted grid."""
    m, n = len(grid), len(grid[0])
    dist = [[float('inf')] * n for _ in range(m)]
    dist[start[0]][start[1]] = grid[start[0]][start[1]]
    heap = [(dist[start[0]][start[1]], start[0], start[1])]
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while heap:
        cost, r, c = heapq.heappop(heap)
        if (r, c) == end:
            return cost
        if cost > dist[r][c]:
            continue
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                new_cost = cost + grid[nr][nc]
                if new_cost < dist[nr][nc]:
                    dist[nr][nc] = new_cost
                    heapq.heappush(heap, (new_cost, nr, nc))

    return dist[end[0]][end[1]]
```

### Complexity Analysis

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Min-heap (standard) | O((V + E) log V) | O(V + E) | Most common |
| Fibonacci heap | O(V log V + E) | O(V + E) | Theoretical, rarely used |
| Dense graph (array scan) | O(V²) | O(V) | Better when E ≈ V² |

**For grids:** V = m×n, E = 4×m×n → O(m×n × log(m×n))

---

## 3. 0-1 BFS

### Why Not Just Use Dijkstra?

You can — it's correct. But when edge weights are only 0 or 1, **a deque achieves the same correctness in O(V + E) instead of O((V+E) log V).**

The log factor comes from the heap maintaining sorted order among arbitrary weights. With only two possible weights (0 and 1), we can maintain sorted order for free using a deque.

### How the Deque Maintains Sorted Order

**Invariant:** The deque always contains nodes in non-decreasing order of distance.

**Why this holds:**
- At any moment, the deque has nodes at distance `d` (current front) and `d+1` (back region).
- When we pop a node at distance `d`:
  - A 0-cost neighbor also has distance `d` → push to **front** (same level)
  - A 1-cost neighbor has distance `d+1` → push to **back** (next level)
- The deque never has more than 2 distinct distance levels at any time.

```
Deque state during processing:

  FRONT                                    BACK
  ┌──────────────────┬──────────────────────┐
  │  cost = d nodes  │  cost = d+1 nodes    │
  └──────────────────┴──────────────────────┘
       ▲ pop here         push 1-cost here ▲
       │                                    │
       └── push 0-cost here (appendleft)

After all cost-d nodes are processed:
  ┌──────────────────┬──────────────────────┐
  │  cost = d+1      │  cost = d+2          │
  └──────────────────┴──────────────────────┘
  (the old d+1 nodes are now at the front)
```

This is essentially **BFS with two buckets** — the deque partitions nodes into "current distance" and "next distance."

### 0-1 BFS Trace

```
Grid (0 = free, 1 = wall to remove):
  0  1  0
  0  0  1
  1  0  0

Start: (0,0), End: (2,2)
Goal: minimum walls to remove
```

| Step | Pop | dist value | Action | Deque |
|------|-----|-----------|--------|-------|
| init | — | (0,0)=0 | seed | [(0,0)] |
| 1 | (0,0) d=0 | (1,0)=0, (0,1)=1 | (1,0) front, (0,1) back | [(1,0), (0,1)] |
| 2 | (1,0) d=0 | (1,1)=0, (2,0)=1 | (1,1) front, (2,0) back | [(1,1), (0,1), (2,0)] |
| 3 | (1,1) d=0 | (1,2)=1, (2,1)=0 | (2,1) front, (1,2) back | [(2,1), (0,1), (2,0), (1,2)] |
| 4 | (2,1) d=0 | (2,2)=0 | (2,2) front | [(2,2), (0,1), (2,0), (1,2)] |
| 5 | (2,2) d=0 | **done** | — | — |

**Answer:** 0 walls removed (path: (0,0)→(1,0)→(1,1)→(2,1)→(2,2), all 0-cost cells)

### 0-1 BFS Implementation

```python
from collections import deque

def zero_one_bfs(grid: list[list[int]], start: tuple, end: tuple) -> int:
    """Minimum cost path where each cell costs 0 or 1."""
    m, n = len(grid), len(grid[0])
    dist = [[float('inf')] * n for _ in range(m)]
    dist[start[0]][start[1]] = grid[start[0]][start[1]]
    dq = deque([(start[0], start[1])])
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while dq:
        r, c = dq.popleft()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                new_cost = dist[r][c] + grid[nr][nc]
                if new_cost < dist[nr][nc]:
                    dist[nr][nc] = new_cost
                    if grid[nr][nc] == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))

    return dist[end[0]][end[1]]
```

**Important subtle point:** Unlike Dijkstra, we do NOT need the `if cost > dist[r][c]: continue` guard here because the deque processes nodes in order. However, adding it doesn't hurt and can be a minor optimization:

```python
while dq:
    r, c = dq.popleft()
    if dist[r][c] < current_stored_cost:   # optional optimization
        continue
```

Some competitive programmers include it anyway for safety. Both versions are correct.

---

## 4. Decision Framework

```
Q1: Are all edge weights equal?
│
├── YES → plain BFS (queue), O(V+E)
│         Examples: shortest path in unweighted grid, word ladder
│
└── NO →
    Q2: Are edge weights only 0 and 1?
    │
    ├── YES → 0-1 BFS (deque), O(V+E)
    │         Examples: minimum obstacle removal, minimum flips
    │
    └── NO →
        Q3: Are all weights non-negative?
        │
        ├── YES → Dijkstra (min-heap), O((V+E) log V)
        │         Examples: network delay, minimum effort path
        │
        └── NO → Bellman-Ford, O(VE)
                  Examples: cheapest flights with negative rebates
```

### Recognizing 0-1 BFS Problems

Look for these patterns:
- Grid with **two types of cells** (free/blocked, arrow-following/redirecting)
- "Minimum number of X to change/remove/flip"
- Moving in one direction is free, changing direction costs 1
- Binary cost: either you pay 0 or you pay 1

### Recognizing Dijkstra Problems

- Grid/graph with **variable positive costs** (elevation differences, toll costs)
- "Minimum cost to reach destination" with non-uniform weights
- "Maximum probability path" (negate log for Dijkstra)
- Any shortest path where BFS/0-1 BFS doesn't apply

---

## 5. Bottleneck Shortest Path

Sometimes you don't want to minimize the **sum** — you want to:
- **Maximize the minimum** edge on the path (safest path)
- **Minimize the maximum** edge on the path (minimum effort)

**The only change from standard Dijkstra is the relaxation formula:**

```python
# Standard Dijkstra — minimize sum
new_cost = cost + edge_weight

# Max-min bottleneck — maximize the minimum edge
new_val = min(current_bottleneck, edge_weight)
# Use max-heap (negate values in Python)

# Min-max bottleneck — minimize the maximum edge
new_val = max(current_bottleneck, edge_weight)
# Use min-heap directly
```

### Example: Minimize Maximum Edge (LC 1631)

```python
import heapq

def minimum_effort_path(heights: list[list[int]]) -> int:
    """Minimize the maximum absolute difference along any path."""
    m, n = len(heights), len(heights[0])
    effort = [[float('inf')] * n for _ in range(m)]
    effort[0][0] = 0
    heap = [(0, 0, 0)]  # (max_diff_so_far, row, col)
    dirs = [(0,1),(0,-1),(1,0),(-1,0)]

    while heap:
        max_diff, r, c = heapq.heappop(heap)
        if r == m - 1 and c == n - 1:
            return max_diff
        if max_diff > effort[r][c]:
            continue
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                new_diff = max(max_diff, abs(heights[r][c] - heights[nr][nc]))
                if new_diff < effort[nr][nc]:
                    effort[nr][nc] = new_diff
                    heapq.heappush(heap, (new_diff, nr, nc))

    return effort[m-1][n-1]
```

**Why Dijkstra still works here:** The greedy property still holds — once we pop a node, no future path can improve its bottleneck because the heap gives us the smallest bottleneck first, and extending a path can only make the bottleneck worse (or equal).

---

## 6. Dijkstra with State

When the cost depends on more than just position — e.g., remaining fuel, keys held, turns taken — extend the state.

```python
# State: (cost, row, col, extra_state)
# dist key: (row, col, extra_state)

heap = [(0, sr, sc, initial_state)]
dist = {}
dist[(sr, sc, initial_state)] = 0
```

### Example: Cheapest Flights Within K Stops (LC 787)

```python
import heapq
from collections import defaultdict

def find_cheapest_price(
    n: int,
    flights: list[list[int]],
    src: int,
    dst: int,
    k: int
) -> int:
    graph = defaultdict(list)
    for u, v, w in flights:
        graph[u].append((v, w))

    # State: (cost, node, stops_remaining)
    dist = defaultdict(lambda: float('inf'))
    dist[(src, k + 1)] = 0
    heap = [(0, src, k + 1)]

    while heap:
        cost, node, stops = heapq.heappop(heap)
        if node == dst:
            return cost
        if stops == 0:
            continue
        if cost > dist[(node, stops)]:
            continue
        for neighbor, weight in graph[node]:
            new_cost = cost + weight
            if new_cost < dist[(neighbor, stops - 1)]:
                dist[(neighbor, stops - 1)] = new_cost
                heapq.heappush(heap, (new_cost, neighbor, stops - 1))

    return -1
```

**Caution:** State-space Dijkstra can explode the number of "nodes." For K stops and N cities, you have O(N×K) states. Make sure the state space is bounded.

---

## 7. Case Study: LC 3286 — Find a Safe Walk Through a Grid

**Problem:** Grid of 0s and 1s. Start at (0,0), reach (m-1,n-1). Each cell costs `grid[i][j]` health. You need `health > 0` at all times. Can you make it?

### Approach 1: DFS with Pruning (Your Solution — Works but Slow)

```python
def findSafeWalk(self, grid, health):
    m, n = len(grid), len(grid[0])
    visited = {}
    is_reached = [False]

    def dfs(i, j, health):
        if is_reached[0] or ((i, j) in visited and visited[(i, j)] >= health):
            return
        if health - grid[i][j] <= 0:
            return
        if i == m - 1 and j == n - 1:
            is_reached[0] = True
            return
        visited[(i, j)] = health
        health -= grid[i][j]
        for di, dj in [(0,1),(0,-1),(1,0),(-1,0)]:
            ni, nj = i + di, j + dj
            if not is_reached[0] and 0 <= ni < m and 0 <= nj < n:
                dfs(ni, nj, health)

    dfs(0, 0, health)
    return is_reached[0]
```

**Why it's slow:**
- DFS explores paths in arbitrary order
- Same cell can be visited with many different health values (health, health-1, health-2, ...)
- Worst case: O(m × n × health) — each cell visited once per health level
- Recursion stack depth can hit Python's limit on large grids

### Approach 2: 0-1 BFS (Optimal)

**Key reframe:** Each cell costs 0 or 1. Find the minimum total cost path. If `health > min_cost`, return True.

```python
from collections import deque

def findSafeWalk(self, grid, health):
    m, n = len(grid), len(grid[0])
    dist = [[float('inf')] * n for _ in range(m)]
    dist[0][0] = grid[0][0]
    dq = deque([(0, 0)])

    while dq:
        r, c = dq.popleft()
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                new_cost = dist[r][c] + grid[nr][nc]
                if new_cost < dist[nr][nc]:
                    dist[nr][nc] = new_cost
                    if grid[nr][nc] == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))

    return health - dist[m-1][n-1] > 0
```

**Why it's fast:**
- Each cell processed at most twice (once per distance level in the deque)
- O(m × n) time regardless of health value
- No recursion — no stack overflow

### Comparison

| | DFS + Pruning | 0-1 BFS |
|---|---|---|
| **Time** | O(m × n × health) | O(m × n) |
| **Space** | O(m × n) + recursion stack | O(m × n) |
| **Health = 100, grid = 1000×1000** | ~100 billion ops 💀 | ~4 million ops ✅ |
| **Stack overflow risk?** | Yes (deep grids) | No |

---

## 8. Common Bugs & Pitfalls

### Bug 1: Marking visited on push, not on pop

```python
# WRONG — can reject better paths that arrive at the heap later
visited.add((nr, nc))
heapq.heappush(heap, (new_cost, nr, nc))

# CORRECT — finalize only when popped (cheapest arrival)
cost, r, c = heapq.heappop(heap)
if (r, c) in visited:
    continue
visited.add((r, c))
```

**Alternative (also correct):** Skip visited set entirely, use `dist` array:
```python
cost, r, c = heapq.heappop(heap)
if cost > dist[r][c]:
    continue    # stale entry
```

### Bug 2: Not handling the start cell's cost

```python
# WRONG — start cell's cost not included
dist[0][0] = 0

# CORRECT — if the start cell has a cost, include it
dist[0][0] = grid[0][0]
```

### Bug 3: Comparing tuples with incomparable elements in the heap

```python
# WRONG — if costs tie, Python compares (r, c) which may not be comparable
heapq.heappush(heap, (cost, node_object))

# FIX — add a tiebreaker (counter) or ensure all elements are comparable
heapq.heappush(heap, (cost, counter, node_object))
```

For grids with integer coordinates, `(cost, r, c)` is fine since ints are always comparable.

### Bug 4: Using DFS for shortest path

DFS does NOT find shortest paths. Period. Even with memoization/pruning, DFS explores paths in arbitrary order, leading to:
- Revisiting cells with suboptimal values
- Exponential blowup in the number of states explored
- Potential stack overflow

**Only use DFS for:** connectivity, cycle detection, topological sort, exhaustive enumeration, tree traversal.

### Bug 5: 0-1 BFS — deciding front/back by the wrong cost

```python
# WRONG — deciding based on the CURRENT cell's cost
if grid[r][c] == 0:
    dq.appendleft(...)

# CORRECT — deciding based on the EDGE cost (the cell you're moving TO)
if grid[nr][nc] == 0:
    dq.appendleft((nr, nc))
else:
    dq.append((nr, nc))
```

The edge weight is the cost of ENTERING the neighbor, not the cost of the current cell.

### Bug 6: Forgetting that 0-1 BFS needs the `new_cost < dist` check

Without this, the same cell gets pushed repeatedly:

```python
# WRONG — infinite loop possible
dq.appendleft((nr, nc))

# CORRECT — only push if we found a better path
if new_cost < dist[nr][nc]:
    dist[nr][nc] = new_cost
    dq.appendleft((nr, nc)) if edge == 0 else dq.append((nr, nc))
```

### Bug 7: Python max-heap — forgetting to negate

Python's `heapq` is min-heap only. For max-heap behavior:

```python
# Push negated values
heapq.heappush(heap, (-value, node))

# Pop and negate back
neg_val, node = heapq.heappop(heap)
value = -neg_val
```

---

## 9. Practice Problems

### Tier 1: Standard BFS (Warm-Up)

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 1091 | [Shortest Path in Binary Matrix](https://leetcode.com/problems/shortest-path-in-binary-matrix/) | Medium | Plain BFS, 8-directional |
| 542 | [01 Matrix](https://leetcode.com/problems/01-matrix/) | Medium | Multi-source BFS from all 0s |
| 994 | [Rotting Oranges](https://leetcode.com/problems/rotting-oranges/) | Medium | Multi-source BFS, track waves |
| 1162 | [As Far from Land as Possible](https://leetcode.com/problems/as-far-from-land-as-possible/) | Medium | Multi-source BFS from all 1s |

### Tier 2: 0-1 BFS

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 2290 | [Minimum Obstacle Removal to Reach Corner](https://leetcode.com/problems/minimum-obstacle-removal-to-reach-corner/) | Hard | Cell 0 = free (cost 0), cell 1 = obstacle to remove (cost 1) |
| 1368 | [Minimum Cost to Make at Least One Valid Path](https://leetcode.com/problems/minimum-cost-to-make-at-least-one-valid-path-in-a-grid/) | Hard | Following arrow = 0, redirecting = 1 |
| 3286 | [Find a Safe Walk Through a Grid](https://leetcode.com/problems/find-a-safe-walk-through-a-grid/) | Medium | Min cost path, compare with health |
| 2699 | [Modify Graph Edge Weights](https://leetcode.com/problems/modify-graph-edge-weights/) | Hard | Dijkstra twice with modified weights |

### Tier 3: Standard Dijkstra

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 743 | [Network Delay Time](https://leetcode.com/problems/network-delay-time/) | Medium | Classic SSSP, return max dist |
| 1514 | [Path with Maximum Probability](https://leetcode.com/problems/path-with-maximum-probability/) | Medium | Max-heap, multiply probabilities |
| 1976 | [Number of Ways to Arrive at Destination](https://leetcode.com/problems/number-of-ways-to-arrive-at-destination/) | Medium | Dijkstra + count paths |
| 3341 | [Find Minimum Time to Reach Last Room I](https://leetcode.com/problems/find-minimum-time-to-reach-last-room-i/) | Medium | Must wait until grid[i][j] before entering |
| 3342 | [Find Minimum Time to Reach Last Room II](https://leetcode.com/problems/find-minimum-time-to-reach-last-room-ii/) | Medium | Same, but movement cost alternates 1/2 |

### Tier 4: Bottleneck Path (Max-Min / Min-Max Dijkstra)

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 1631 | [Path With Minimum Effort](https://leetcode.com/problems/path-with-minimum-effort/) | Medium | Minimize max(abs difference), min-heap |
| 778 | [Swim in Rising Water](https://leetcode.com/problems/swim-in-rising-water/) | Hard | Minimize max cell value on path |
| 1102 | [Path With Maximum Minimum Value](https://leetcode.com/problems/path-with-maximum-minimum-value/) | Medium | Maximize min cell (max-heap, negate) |
| 2812 | [Find the Safest Path in a Grid](https://leetcode.com/problems/find-the-safest-path-in-a-grid/) | Medium | Multi-source BFS for distances, then max-min Dijkstra |

### Tier 5: Dijkstra with State

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 787 | [Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) | Medium | State = (node, stops_left) |
| 1293 | [Shortest Path in Grid with Obstacles Elimination](https://leetcode.com/problems/shortest-path-in-a-grid-with-obstacles-elimination/) | Hard | State = (r, c, obstacles_left), BFS since unweighted |
| 864 | [Shortest Path to Get All Keys](https://leetcode.com/problems/shortest-path-to-get-all-keys/) | Hard | State = (r, c, keys_bitmask) |
| 847 | [Shortest Path Visiting All Nodes](https://leetcode.com/problems/shortest-path-visiting-all-nodes/) | Hard | State = (node, visited_bitmask) |
| 882 | [Reachable Nodes In Subdivided Graph](https://leetcode.com/problems/reachable-nodes-in-subdivided-graph/) | Hard | Dijkstra, edges have subdivided nodes |

### Tier 6: Advanced / Combo

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 2258 | [Escape the Spreading Fire](https://leetcode.com/problems/escape-the-spreading-fire/) | Hard | Binary search on wait time + two BFS layers |
| 1928 | [Minimum Cost to Reach Destination in Time](https://leetcode.com/problems/minimum-cost-to-reach-destination-in-time/) | Hard | Dijkstra with state = (node, time_left) |
| 2577 | [Minimum Time to Visit a Cell In a Grid](https://leetcode.com/problems/minimum-time-to-visit-a-cell-in-a-grid/) | Hard | Dijkstra, parity trick for waiting |
| 1786 | [Number of Restricted Paths From First to Last Node](https://leetcode.com/problems/number-of-restricted-paths-from-first-to-last-node/) | Medium | Dijkstra from last node, then DP/DFS |
| 2045 | [Second Minimum Time to Reach Destination](https://leetcode.com/problems/second-minimum-time-to-reach-destination/) | Hard | Modified BFS tracking top-2 distances per node |

---

## 10. Mental Checklist Before Coding

```
□ What are the edge weights?
  → All 1?           Use BFS
  → Only 0 or 1?     Use 0-1 BFS
  → Variable ≥ 0?    Use Dijkstra
  → Can be negative?  Use Bellman-Ford

□ What am I optimizing?
  → Minimize total cost?    Standard relaxation: new = old + edge
  → Maximize min edge?      Bottleneck: new = min(old, edge), max-heap
  → Minimize max edge?      Bottleneck: new = max(old, edge), min-heap

□ Does the answer depend on more than position?
  → YES: Add state to (row, col, state), expand dist to include state key

□ Am I including the start cell's cost?
  → dist[start] = grid[start], not 0 (if start cell has weight)

□ Am I doing lazy deletion correctly?
  → Check `if cost > dist[node]: continue` after popping from heap

□ Is the problem asking for reachability, not shortest path?
  → Consider if a simple BFS/DFS suffices before pulling out Dijkstra
```

---

## Appendix: Why DFS Fails for Shortest Path (Formal)

Consider this 3×3 grid where cell value = cost:

```
0 1 0
0 0 1
1 0 0
```

**Optimal path:** (0,0)→(1,0)→(1,1)→(2,1)→(2,2), total cost = 0.

**DFS might explore:** (0,0)→(0,1)→(0,2)→(1,2)→(2,2), total cost = 2.

DFS has no mechanism to guarantee it finds the cheaper path first. It processes based on **stack order** (depth), not **cost order**. The `visited` dictionary with health pruning helps, but in the worst case DFS still explores O(cells × health_levels) states because:

1. It visits (1,1) with health = 8 via one path
2. Later finds a path to (1,1) with health = 9 — must revisit
3. Then health = 10, 11, ... each triggering new exploration

BFS/0-1 BFS/Dijkstra avoid this by always processing the cheapest unfinished node first, guaranteeing each node is finalized in one visit.
