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
3. [0-1 BFS — The Deque Trick (Beginner-Friendly)](#3-0-1-bfs)
   - [The Simplest Way to Think About It](#the-simplest-way-to-think-about-it)
   - [Building Up from Regular BFS](#building-up-from-regular-bfs)
   - [The Deque Rule (Just Two Rules)](#the-deque-rule)
   - [Full Walkthrough with Pictures](#full-walkthrough-with-pictures)
   - [When to Use 0-1 BFS — Cheat Sheet](#when-to-use-0-1-bfs)
   - [Implementation](#0-1-bfs-implementation)
4. [Bellman-Ford Algorithm — Handling Negative Edges](#4-bellman-ford)
   - [Why Dijkstra Breaks with Negative Edges](#why-dijkstra-breaks-with-negative-edges)
   - [The Bellman-Ford Idea](#the-bellman-ford-idea)
   - [Step-by-Step Trace](#bellman-ford-trace)
   - [Detecting Negative Cycles](#detecting-negative-cycles)
   - [Implementation](#bellman-ford-implementation)
   - [SPFA — The Optimized Version](#spfa)
5. [Dijkstra vs 0-1 BFS vs BFS vs Bellman-Ford — Decision Framework](#5-decision-framework)
6. [Variant: Bottleneck Shortest Path (Max-Min / Min-Max)](#6-bottleneck-shortest-path)
7. [Variant: Dijkstra with State (r, c, extra)](#7-dijkstra-with-state)
8. [Case Study: LC 3286 — Find a Safe Walk Through a Grid](#8-case-study-safe-walk)
9. [Common Bugs & Pitfalls](#9-common-bugs)
10. [Practice Problems — Graded by Pattern](#10-practice-problems)
11. [Mental Checklist Before Coding](#11-mental-checklist)

---

## 1. The Core Idea

**Single-source shortest path (SSSP):** Given a graph with edge weights and a source node, find the minimum-cost path from source to every other node.

Four algorithms solve this, each optimized for different weight constraints:

```
                           Edge weights
                               │
            ┌──────────────┬───┴───┬──────────────┐
            │              │       │              │
       All equal      Only {0,1}  Arbitrary ≥ 0  Can be negative
            │              │       │              │
          BFS          0-1 BFS   Dijkstra     Bellman-Ford
        O(V + E)       O(V + E)  O((V+E)logV)   O(V × E)
        (queue)        (deque)   (min-heap)     (relax all edges V-1 times)
```

The key insight: **BFS, 0-1 BFS, and Dijkstra all process nodes in non-decreasing order of distance.** They differ only in the data structure that maintains this order. Bellman-Ford takes a completely different approach — it doesn't care about processing order, it just keeps relaxing edges until nothing changes.

| Algorithm | Data Structure | Why It Works |
|-----------|---------------|-------------|
| BFS | Queue (FIFO) | All edges weight 1, so distance = depth = FIFO order |
| 0-1 BFS | Deque | 0-cost goes front (same level), 1-cost goes back (next level) |
| Dijkstra | Min-heap | Arbitrary weights need explicit sorting by cost |
| Bellman-Ford | Plain array | Brute-force: relax every edge V-1 times; works with negatives |

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

## 3. 0-1 BFS — The Deque Trick (Beginner-Friendly)

### The Simplest Way to Think About It

Forget algorithms for a moment. Imagine you're in a building:
- Some doors are **open** (cost 0 to walk through)
- Some doors are **locked** (cost 1 to break open)

You want to reach the exit breaking the **fewest doors possible.**

**Regular BFS** assumes every step costs the same — it can't tell open doors from locked ones.  
**Dijkstra** works but is overkill — it uses a full priority queue for just two possible costs.  
**0-1 BFS** is the sweet spot — it handles exactly this "free or costs 1" situation perfectly.

### Building Up from Regular BFS

Let's start from what you already know and build up.

**Regular BFS** uses a queue. It works because every edge costs the same (1), so nodes in the queue are naturally sorted by distance:

```
Queue: [dist=1, dist=1, dist=1, dist=2, dist=2, dist=2, dist=3, ...]
        ^^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^^    ^^^^^^^^
        all same cost           all same cost           same cost
```

Now what if some edges cost 0? A neighbor reached via a 0-cost edge has the **same distance** as the current node. It should be processed **before** the nodes at the next distance level.

```
Queue: [dist=1, dist=1, dist=2, dist=2]
                                         
Now we pop dist=1 node and find a 0-cost neighbor (also dist=1).
Where does it go?

Queue: [dist=1, dist=2, dist=2]   ← we need dist=1 node HERE, at the front!
        ^^^
        new 0-cost neighbor should be here, not at the back
```

A regular queue only adds to the back. But we need to add to the **front** sometimes. That's a **deque** (double-ended queue).

### The Deque Rule (Just Two Rules)

```
When you discover a neighbor:

  Edge cost = 0  →  appendleft (front of deque)    "same distance, process soon"
  Edge cost = 1  →  append     (back of deque)     "next distance, process later"
```

That's it. That's the entire algorithm. Everything else is identical to BFS.

**Why does this work?** Because the deque always stays sorted:

```
Step 1: Start with [A₀]                     (subscript = distance)

Step 2: Pop A₀, find 0-cost neighbor B and 1-cost neighbor C
         B has dist 0 → front
         C has dist 1 → back
         Deque: [B₀, C₁]     ← sorted! ✓

Step 3: Pop B₀, find 0-cost neighbor D and 1-cost neighbor E
         D has dist 0 → front
         E has dist 1 → back
         Deque: [D₀, C₁, E₁]  ← sorted! ✓

Step 4: Pop D₀, find 1-cost neighbor F
         F has dist 1 → back
         Deque: [C₁, E₁, F₁]  ← sorted! ✓

Step 5: Pop C₁, find 0-cost neighbor G
         G has dist 1 → front
         Deque: [G₁, E₁, F₁]  ← sorted! ✓
```

At any moment, the deque contains **at most 2 distance levels** (current `d` and next `d+1`). 0-cost neighbors stay at level `d` (front), 1-cost neighbors go to level `d+1` (back). When all level-`d` nodes are done, level `d+1` becomes the new front.

### Full Walkthrough with Pictures

```
Grid (0 = free path, 1 = wall to break):

     col0  col1  col2
row0:  0     1     0
row1:  0     0     1
row2:  1     0     0

Start: (0,0)    End: (2,2)
Question: What's the minimum number of walls to break?
```

**Initial state:**

```
dist:    0    ∞    ∞         Deque: [(0,0)]
         ∞    ∞    ∞
         ∞    ∞    ∞
```

**Step 1:** Pop (0,0) with dist=0. Neighbors:
- (1,0): grid=0, new_cost = 0+0 = 0 → **front**
- (0,1): grid=1, new_cost = 0+1 = 1 → **back**

```
dist:    0    1    ∞         Deque: [(1,0), (0,1)]
         0    ∞    ∞                  ↑front   ↑back
         ∞    ∞    ∞
```

**Step 2:** Pop (1,0) with dist=0. Neighbors:
- (0,0): already dist=0, skip (0 < 0 is false)
- (2,0): grid=1, new_cost = 0+1 = 1 → **back**
- (1,1): grid=0, new_cost = 0+0 = 0 → **front**

```
dist:    0    1    ∞         Deque: [(1,1), (0,1), (2,0)]
         0    0    ∞
         ∞    ∞    ∞
```

**Step 3:** Pop (1,1) with dist=0. Neighbors:
- (0,1): already dist=1, new_cost=0+1=1, not better, skip
- (2,1): grid=0, new_cost = 0+0 = 0 → **front**
- (1,0): already dist=0, skip
- (1,2): grid=1, new_cost = 0+1 = 1 → **back**

```
dist:    0    1    ∞         Deque: [(2,1), (0,1), (2,0), (1,2)]
         0    0    ∞
         ∞    0    ∞
```

**Step 4:** Pop (2,1) with dist=0. Neighbors:
- (1,1): already 0, skip
- (2,0): new_cost=0+1=1, same as current 1, skip (not strictly less)
- (2,2): grid=0, new_cost = 0+0 = 0 → **front**

```
dist:    0    1    ∞         Deque: [(2,2), (0,1), (2,0), (1,2)]
         0    0    ∞
         ∞    0    0    ← destination reached with cost 0!
```

**Step 5:** Pop (2,2) with dist=0. This is the destination! **Answer: 0 walls broken.**

```
The path: (0,0) → (1,0) → (1,1) → (2,1) → (2,2)
All cells on this path are 0, so no walls needed!

     0  1  0
     ↓
     0→ 0  1
        ↓
     1  0→ 0  ← exit
```

### When to Use 0-1 BFS — Cheat Sheet

**Trigger words in the problem:**
- "minimum number of **removals/changes/flips**"
- "free to move one way, costs 1 to go another way"
- Grid with exactly **two cell types** (0 and 1, or arrows and redirections)
- Any shortest path where edges cost either 0 or 1

**Real examples:**
| Problem says... | Edge cost 0 | Edge cost 1 |
|---|---|---|
| "Remove obstacles" | Move through empty cell | Remove an obstacle |
| "Follow arrows" | Move in arrow direction | Change arrow direction |
| "Safe walk" | Step on safe cell (0) | Step on dangerous cell (1) |
| "Flip switches" | Walk through open door | Flip a switch |

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
                        dq.appendleft((nr, nc))   # free move → front
                    else:
                        dq.append((nr, nc))        # costly move → back

    return dist[end[0]][end[1]]
```

**Line-by-line for beginners:**

```python
dist[start[0]][start[1]] = grid[start[0]][start[1]]
# Start cell might cost 0 or 1. Include that cost.

new_cost = dist[r][c] + grid[nr][nc]
# Total cost to reach neighbor = cost to reach current + neighbor's cost

if new_cost < dist[nr][nc]:
# Only update if we found a CHEAPER path to this neighbor

if grid[nr][nc] == 0:
    dq.appendleft((nr, nc))   # Cost 0: same priority level → front
else:
    dq.append((nr, nc))       # Cost 1: next priority level → back
```

### 0-1 BFS vs BFS vs Dijkstra — Side by Side

```python
# ── Regular BFS (all edges cost 1) ──
queue = deque([start])
while queue:
    node = queue.popleft()
    for neighbor in get_neighbors(node):
        if dist[neighbor] > dist[node] + 1:
            dist[neighbor] = dist[node] + 1
            queue.append(neighbor)              # always back

# ── 0-1 BFS (edges cost 0 or 1) ──
dq = deque([start])
while dq:
    node = dq.popleft()
    for neighbor, edge_cost in get_neighbors(node):   # edge_cost is 0 or 1
        if dist[neighbor] > dist[node] + edge_cost:
            dist[neighbor] = dist[node] + edge_cost
            if edge_cost == 0:
                dq.appendleft(neighbor)         # ← only difference: front
            else:
                dq.append(neighbor)             # ← back (same as BFS)

# ── Dijkstra (edges cost anything ≥ 0) ──
heap = [(0, start)]
while heap:
    cost, node = heapq.heappop(heap)            # ← always pops minimum
    for neighbor, edge_cost in get_neighbors(node):
        if dist[neighbor] > cost + edge_cost:
            dist[neighbor] = cost + edge_cost
            heapq.heappush(heap, (dist[neighbor], neighbor))
```

Notice: **0-1 BFS is literally BFS with one extra if-else.** That's why it's so easy once you get the intuition.

---

## 4. Bellman-Ford Algorithm

### Why Dijkstra Breaks with Negative Edges

Dijkstra's correctness relies on: "once I pop a node, its distance is final." This works because adding more edges can only increase cost (all edges ≥ 0).

With negative edges, this breaks completely:

```
Graph:
  A ──1──▶ B ──(-5)──▶ C
  │                     ▲
  └────────3───────────▶

Dijkstra pops B (cost 1), then C via B (cost 1 + (-5) = -4).
But it already finalized A→C = 3 in the heap.

Dijkstra says: shortest to C = -4  ← happens to be right here
But in general, Dijkstra might finalize C = 3 BEFORE discovering the -4 path.
```

**The deeper issue:** Dijkstra pops node C with cost 3 and marks it done. It never reconsiders C even though B→C gives cost -4. The greedy assumption ("popped = final") is violated.

### The Bellman-Ford Idea

**Forget being clever. Just brute-force it.**

The key insight: the shortest path from source to any node uses **at most V-1 edges** (V = number of vertices). If it used V or more edges, it would visit some node twice, meaning there's a cycle — and if the cycle is negative, the shortest path is -infinity.

So the algorithm is dead simple:

```
Repeat V-1 times:
    For every edge (u, v, weight) in the graph:
        If dist[u] + weight < dist[v]:
            dist[v] = dist[u] + weight
```

**That's it.** No heap, no visited set, no clever data structure. Just keep relaxing edges until convergence.

**Why V-1 iterations?**

```
After iteration 1:  shortest paths using ≤ 1 edge are correct
After iteration 2:  shortest paths using ≤ 2 edges are correct
...
After iteration k:  shortest paths using ≤ k edges are correct
After iteration V-1: ALL shortest paths are correct (max V-1 edges in any simple path)
```

Think of it like a **wave spreading one edge at a time:**

```
Iteration 1: Source's direct neighbors get correct distances
Iteration 2: Neighbors of neighbors get correct distances
...
Iteration V-1: The farthest reachable node gets its correct distance
```

### Bellman-Ford Trace

```
Graph:
  A ──4──▶ B ──(-2)──▶ C
  │         ▲           │
  │         3           5
  │         │           │
  └──2──▶ D ───(-1)───▶ E

Edges: (A,B,4), (A,D,2), (B,C,-2), (D,B,3), (D,E,-1), (C,E,5)
Source: A
```

| Node | Init | After iter 1 | After iter 2 | After iter 3 | After iter 4 |
|------|------|-------------|-------------|-------------|-------------|
| A | 0 | 0 | 0 | 0 | 0 |
| B | ∞ | 4 | 4→**5**? no, 4<5 → **4** | 4 | 4 |
| C | ∞ | ∞→**2** (via B) | **2** | 2 | 2 |
| D | ∞ | **2** (via A) | 2 | 2 | 2 |
| E | ∞ | ∞ | **1** (via D, 2+(-1)) | 1 | 1 |

Wait, let me redo more carefully. In each iteration we scan ALL edges:

**Init:** dist = {A:0, B:∞, C:∞, D:∞, E:∞}

**Iteration 1** (scan all 6 edges):
- (A,B,4): dist[A]+4 = 4 < ∞ → dist[B] = 4
- (A,D,2): dist[A]+2 = 2 < ∞ → dist[D] = 2
- (B,C,-2): dist[B]+(-2) = 2 < ∞ → dist[C] = 2
- (D,B,3): dist[D]+3 = 5 > 4 → no change
- (D,E,-1): dist[D]+(-1) = 1 < ∞ → dist[E] = 1
- (C,E,5): dist[C]+5 = 7 > 1 → no change

dist = {A:0, B:4, C:2, D:2, E:1}

**Iteration 2** (scan all 6 edges again):
- All edges: no improvements found. **Early termination!**

**Answer:** A→B=4, A→C=2 (via A→B→C), A→D=2, A→E=1 (via A→D→E)

### Detecting Negative Cycles

After V-1 iterations, do **one more pass** over all edges. If any distance can still be reduced, there's a negative cycle (a loop where total weight < 0, meaning you can decrease cost infinitely).

```
After V-1 iterations, do iteration V:
    For every edge (u, v, weight):
        If dist[u] + weight < dist[v]:
            → NEGATIVE CYCLE DETECTED!
```

**Why?** After V-1 iterations, all shortest paths are finalized. If an edge can still relax, it means going around a cycle one more time reduces cost → that cycle has negative total weight.

```
Example negative cycle:
  A ──1──▶ B ──(-3)──▶ C ──1──▶ A
  Total cycle weight: 1 + (-3) + 1 = -1

Every time you go around: cost decreases by 1
Go around 1000 times: cost decreases by 1000
Shortest path = -∞ (undefined)
```

### Bellman-Ford Implementation

```python
def bellman_ford(n: int, edges: list[tuple], source: int) -> tuple[list, bool]:
    """
    n: number of nodes (0 to n-1)
    edges: list of (u, v, weight)
    Returns: (dist array, has_negative_cycle)
    """
    dist = [float('inf')] * n
    dist[source] = 0

    # Relax all edges V-1 times
    for i in range(n - 1):
        updated = False
        for u, v, w in edges:
            if dist[u] != float('inf') and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                updated = True
        if not updated:       # early exit — no changes means we're done
            break

    # Check for negative cycles (one more pass)
    for u, v, w in edges:
        if dist[u] != float('inf') and dist[u] + w < dist[v]:
            return dist, True    # negative cycle exists

    return dist, False
```

**The `if not updated: break` optimization:** If a full pass over all edges makes no changes, all distances are final. This often reduces the number of iterations in practice.

### SPFA — The Optimized Bellman-Ford

**Shortest Path Faster Algorithm (SPFA)** is Bellman-Ford with a queue optimization. Instead of scanning ALL edges every iteration, only scan edges from nodes whose distances recently changed.

```python
from collections import deque

def spfa(n: int, graph: dict, source: int) -> tuple[list, bool]:
    """
    graph: adjacency list {node: [(neighbor, weight), ...]}
    Returns: (dist array, has_negative_cycle)
    """
    dist = [float('inf')] * n
    dist[source] = 0
    in_queue = [False] * n
    count = [0] * n              # times each node entered queue

    queue = deque([source])
    in_queue[source] = True

    while queue:
        u = queue.popleft()
        in_queue[u] = False
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                if not in_queue[v]:
                    queue.append(v)
                    in_queue[v] = True
                    count[v] += 1
                    if count[v] >= n:     # entered queue ≥ V times → negative cycle
                        return dist, True

    return dist, False
```

**SPFA vs Bellman-Ford:**
- Average case: SPFA is much faster (often O(E) in practice)
- Worst case: both are O(V×E) — SPFA can be forced into worst case by adversarial graphs
- LeetCode: SPFA usually passes, but some problems are designed to break it

### When to Use Bellman-Ford

| Situation | Use |
|---|---|
| Non-negative weights | Dijkstra (faster) |
| Negative weights, no negative cycles | Bellman-Ford or SPFA |
| Need to detect negative cycles | Bellman-Ford (V-th iteration check) |
| Limited number of edges/stops (like "at most K stops") | Bellman-Ford with K iterations instead of V-1 |
| Distributed system (each node only knows its neighbors) | Bellman-Ford (no global view needed) |

### Bellman-Ford for "At Most K Edges" Problems

A special trick: if you only run **K iterations** instead of V-1, you get shortest paths using **at most K edges**. This is perfect for "cheapest flight with at most K stops."

```python
def cheapest_flight_k_stops(n, flights, src, dst, k):
    """Shortest path from src to dst using at most k+1 edges (k stops)."""
    dist = [float('inf')] * n
    dist[src] = 0

    for _ in range(k + 1):                        # k stops = k+1 edges
        new_dist = dist[:]                         # copy! important!
        for u, v, w in flights:
            if dist[u] + w < new_dist[v]:
                new_dist[v] = dist[u] + w
        dist = new_dist

    return dist[dst] if dist[dst] != float('inf') else -1
```

**Critical: `new_dist = dist[:]`** — we must use the previous iteration's values, otherwise within a single iteration we might relax a chain of edges (using more edges than allowed).

---

## 5. Decision Framework

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
        └── NO →
            Q4: Negative edges present?
            │
            ├── Need negative cycle detection → Bellman-Ford, O(VE)
            │   Examples: arbitrage detection
            │
            ├── "At most K edges/stops" → Bellman-Ford with K iterations
            │   Examples: cheapest flights with K stops
            │
            └── General negative weights → SPFA (optimized Bellman-Ford)
                Examples: shortest path with toll rebates
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

### Recognizing Bellman-Ford Problems

- Problem has **negative edge weights** (discounts, rebates, refunds)
- **"At most K stops/edges"** constraint (Bellman-Ford with K iterations)
- Need to **detect negative cycles** (arbitrage, infinite discount loops)
- Dijkstra gives wrong answers (hint: negative edges exist)

---

## 6. Bottleneck Shortest Path

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

## 7. Dijkstra with State

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

## 8. Case Study: LC 3286 — Find a Safe Walk Through a Grid

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

## 9. Common Bugs & Pitfalls

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

## 10. Practice Problems

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

### Tier 6: Bellman-Ford / Negative Weights / K-Edge Constraints

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 787 | [Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) | Medium | Bellman-Ford with K+1 iterations (also solvable with Dijkstra+state) |
| 743 | [Network Delay Time](https://leetcode.com/problems/network-delay-time/) | Medium | Can be solved with Bellman-Ford as practice (Dijkstra is better here) |
| 1334 | [Find the City With the Smallest Number of Neighbors at a Threshold Distance](https://leetcode.com/problems/find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance/) | Medium | Bellman-Ford from each city, or Floyd-Warshall |
| 1865 | [Finding Pairs With a Certain Sum](https://leetcode.com/problems/finding-pairs-with-a-certain-sum/) | Medium | Not shortest path but uses similar relaxation logic |
| 2093 | [Minimum Cost to Reach City With Discounts](https://leetcode.com/problems/minimum-cost-to-reach-city-with-discounts/) | Medium | Bellman-Ford/Dijkstra with state (node, discounts_left) |

### Tier 7: Advanced / Combo

| # | Problem | Difficulty | Hint |
|---|---------|------------|------|
| 2258 | [Escape the Spreading Fire](https://leetcode.com/problems/escape-the-spreading-fire/) | Hard | Binary search on wait time + two BFS layers |
| 1928 | [Minimum Cost to Reach Destination in Time](https://leetcode.com/problems/minimum-cost-to-reach-destination-in-time/) | Hard | Dijkstra with state = (node, time_left) |
| 2577 | [Minimum Time to Visit a Cell In a Grid](https://leetcode.com/problems/minimum-time-to-visit-a-cell-in-a-grid/) | Hard | Dijkstra, parity trick for waiting |
| 1786 | [Number of Restricted Paths From First to Last Node](https://leetcode.com/problems/number-of-restricted-paths-from-first-to-last-node/) | Medium | Dijkstra from last node, then DP/DFS |
| 2045 | [Second Minimum Time to Reach Destination](https://leetcode.com/problems/second-minimum-time-to-reach-destination/) | Hard | Modified BFS tracking top-2 distances per node |

---

## 11. Mental Checklist Before Coding

```
□ What are the edge weights?
  → All 1?            Use BFS
  → Only 0 or 1?      Use 0-1 BFS
  → Variable ≥ 0?     Use Dijkstra
  → Can be negative?   Use Bellman-Ford / SPFA
  → "At most K edges"? Use Bellman-Ford with K iterations

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

□ Could there be negative cycles?
  → Run Bellman-Ford V-th iteration check
  → If negative cycle exists, shortest path is undefined (-∞)

□ Bellman-Ford: am I using previous iteration's values?
  → For K-edge problems, copy dist[] before each iteration
  → Without copy, a single iteration can relax multi-edge chains
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
