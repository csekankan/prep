# Grid & Graph Patterns — BFS / Dijkstra / DFS

> Focus: shortest distance, path optimization, and reachability in grids.
> Each section has the pattern rule, template code, and graded practice problems.

---

## Table of Contents

1. [Multi-Source BFS — Nearest Cell](#1-multi-source-bfs--nearest-cell)
2. [0-1 BFS — Weighted Grid with Two Costs](#2-0-1-bfs--weighted-grid-with-two-costs)
3. [Dijkstra on Grid — Weighted Shortest Path](#3-dijkstra-on-grid--weighted-shortest-path)
4. [Max-Min / Min-Max Path (Bottleneck Path)](#4-max-min--min-max-path-bottleneck-path)
5. [BFS on State Space — (row, col, state)](#5-bfs-on-state-space--row-col-state)
6. [DFS — When to Actually Use It](#6-dfs--when-to-actually-use-it)
7. [Pattern Decision Tree](#7-pattern-decision-tree)

---

## 1. Multi-Source BFS — Nearest Cell

### The Rule
> "Find minimum distance from **every cell** to its nearest source" → BFS from **all sources at once**.

Starting BFS simultaneously from all sources gives each cell the distance to its nearest source in a single O(m×n) pass.  
**Never use DFS here.** DFS does not process by distance order, so cells get incorrect or redundantly updated distances.

### Why Multi-Source Works

```
Sources: S        Grid distances computed:
S . . .           0 1 2 3
. . . .    →      1 2 3 4
. . . S           2 3 2 1
. . . .           3 4 3 2
```

BFS spreads out like ripples — all sources expand simultaneously, each cell is finalized the first time it's reached.

### Template

```python
from collections import deque

def multi_source_bfs(grid, m, n):
    dist = [[float('inf')] * n for _ in range(m)]
    queue = deque()

    # Seed all sources
    for i in range(m):
        for j in range(n):
            if is_source(grid[i][j]):
                dist[i][j] = 0
                queue.append((i, j))

    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    while queue:
        r, c = queue.popleft()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and dist[nr][nc] == float('inf'):
                dist[nr][nc] = dist[r][c] + 1
                queue.append((nr, nc))

    return dist
```

### Practice Problems

| # | Problem | Difficulty | Key Insight |
|---|---------|------------|-------------|
| 542 | [01 Matrix](https://leetcode.com/problems/01-matrix/) | Medium | BFS from all 0s simultaneously |
| 994 | [Rotting Oranges](https://leetcode.com/problems/rotting-oranges/) | Medium | BFS from all rotten oranges |
| 286 | [Walls and Gates](https://leetcode.com/problems/walls-and-gates/) | Medium | BFS from all gates |
| 1162 | [As Far from Land as Possible](https://leetcode.com/problems/as-far-from-land-as-possible/) | Medium | BFS from all land cells, maximize dist |
| 2812 | [Find the Safest Path in a Grid](https://leetcode.com/problems/find-the-safest-path-in-a-grid/) | Medium | Multi-source BFS → then Dijkstra |
| 1765 | [Map of Highest Peak](https://leetcode.com/problems/map-of-highest-peak/) | Medium | BFS from all water cells |
| 2258 | [Escape the Spreading Fire](https://leetcode.com/problems/escape-the-spreading-fire/) | Hard | BFS for fire spread + binary search on wait time |

---

## 2. 0-1 BFS — Weighted Grid with Two Costs

### The Rule
> Edge weights are **only 0 or 1** → use a **deque** (not a full heap).  
> Cost-0 edges go to the front; cost-1 edges go to the back.

This runs in O(m×n) vs O(m×n log(m×n)) for Dijkstra.

### Template

```python
from collections import deque

def zero_one_bfs(grid, m, n, start, end):
    dist = [[float('inf')] * n for _ in range(m)]
    dist[start[0]][start[1]] = 0
    dq = deque([(0, start[0], start[1])])
    dirs = [(1,0),(-1,0),(0,1),(0,-1)]

    while dq:
        cost, r, c = dq.popleft()
        if cost > dist[r][c]:
            continue
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                edge_cost = get_edge_cost(grid, r, c, nr, nc)  # 0 or 1
                new_cost = cost + edge_cost
                if new_cost < dist[nr][nc]:
                    dist[nr][nc] = new_cost
                    if edge_cost == 0:
                        dq.appendleft((new_cost, nr, nc))
                    else:
                        dq.append((new_cost, nr, nc))

    return dist[end[0]][end[1]]
```

### Practice Problems

| # | Problem | Difficulty | Key Insight |
|---|---------|------------|-------------|
| 1368 | [Minimum Cost to Make at Least One Valid Path in a Grid](https://leetcode.com/problems/minimum-cost-to-make-at-least-one-valid-path-in-a-grid/) | Hard | Following arrow = cost 0, redirecting = cost 1 |
| 2290 | [Minimum Obstacle Removal to Reach Corner](https://leetcode.com/problems/minimum-obstacle-removal-to-reach-corner/) | Hard | Moving through 0 = free, removing 1 = cost 1 |
| 1976 | [Number of Ways to Arrive at Destination](https://leetcode.com/problems/number-of-ways-to-arrive-at-destination/) | Medium | Dijkstra + count paths |

---

## 3. Dijkstra on Grid — Weighted Shortest Path

### The Rule
> Edge weights are **arbitrary positive integers** → use **Dijkstra** (min-heap).

Standard when you can't use BFS or 0-1 BFS.

### Template

```python
import heapq

def dijkstra_grid(grid, m, n, start, end):
    dist = [[float('inf')] * n for _ in range(m)]
    dist[start[0]][start[1]] = 0
    heap = [(0, start[0], start[1])]  # (cost, row, col)
    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    visited = set()

    while heap:
        cost, r, c = heapq.heappop(heap)
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if (r, c) == end:
            return cost
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and (nr, nc) not in visited:
                new_cost = cost + grid[nr][nc]  # or some weight function
                if new_cost < dist[nr][nc]:
                    dist[nr][nc] = new_cost
                    heapq.heappush(heap, (new_cost, nr, nc))

    return dist[end[0]][end[1]]
```

### Practice Problems

| # | Problem | Difficulty | Key Insight |
|---|---------|------------|-------------|
| 743 | [Network Delay Time](https://leetcode.com/problems/network-delay-time/) | Medium | Classic Dijkstra on graph |
| 1631 | [Path With Minimum Effort](https://leetcode.com/problems/path-with-minimum-effort/) | Medium | Edge weight = abs diff of heights |
| 778 | [Swim in Rising Water](https://leetcode.com/problems/swim-in-rising-water/) | Hard | Minimize max cell value on path |
| 787 | [Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) | Medium | Dijkstra with state (node, stops_left) |
| 1514 | [Path with Maximum Probability](https://leetcode.com/problems/path-with-maximum-probability/) | Medium | Max-heap Dijkstra, multiply probabilities |

---

## 4. Max-Min / Min-Max Path (Bottleneck Path)

### The Rule
> "Find a path that **maximizes the minimum** edge weight" (or minimizes the maximum) → **Dijkstra with max-heap**.

This is the pattern from the safeness factor problem. The heap key is the bottleneck so far, not the total cost.

```
Standard Dijkstra:  new_cost = cost + edge_weight      (sum)
Bottleneck Dijkstra: new_cost = min(cost, edge_weight) (bottleneck)
```

### Template

```python
import heapq

def max_bottleneck_path(weight, m, n, start, end):
    # Maximize the minimum weight along the path
    heap = [(-weight[start[0]][start[1]], start[0], start[1])]
    visited = set()
    dirs = [(1,0),(-1,0),(0,1),(0,-1)]

    while heap:
        val, r, c = heapq.heappop(heap)
        val = -val  # restore to positive
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if (r, c) == end:
            return val
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and (nr, nc) not in visited:
                new_val = min(val, weight[nr][nc])
                heapq.heappush(heap, (-new_val, nr, nc))

    return 0
```

**Key difference from standard Dijkstra:**
- Standard: `new_cost = cost + edge` → minimize total
- Bottleneck: `new_val = min(val, edge)` → maximize minimum

### Practice Problems

| # | Problem | Difficulty | Key Insight |
|---|---------|------------|-------------|
| 2812 | [Find the Safest Path in a Grid](https://leetcode.com/problems/find-the-safest-path-in-a-grid/) | Medium | Multi-source BFS → max-min Dijkstra |
| 778 | [Swim in Rising Water](https://leetcode.com/problems/swim-in-rising-water/) | Hard | Minimize max cell (min-max bottleneck) |
| 1631 | [Path With Minimum Effort](https://leetcode.com/problems/path-with-minimum-effort/) | Medium | Minimize max absolute difference |
| 1102 | [Path With Maximum Minimum Value](https://leetcode.com/problems/path-with-maximum-minimum-value/) | Medium | Classic max-min bottleneck |
| 3419 | [Minimize the Maximum Edge Weight of a Graph](https://leetcode.com/problems/minimize-the-maximum-edge-weight-of-a-graph/) | Medium | Binary search on answer + BFS/DFS check |

---

## 5. BFS on State Space — (row, col, state)

### The Rule
> When shortest path depends on **more than position** (keys collected, walls broken, steps remaining) → encode the extra state in the BFS node.

### Common State Encodings

```python
# Keys collected (bitmask)
(row, col, keys_bitmask)

# Walls you can still break
(row, col, walls_remaining)

# Visited special cells
(row, col, frozenset_of_visited)

# Steps or moves remaining
(row, col, moves_left)
```

### Template

```python
from collections import deque

def bfs_with_state(grid, m, n):
    start_state = (0, 0, initial_state)
    dist = {}
    dist[start_state] = 0
    queue = deque([start_state])

    while queue:
        r, c, state = queue.popleft()
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                new_state = transition(state, grid[nr][nc])
                key = (nr, nc, new_state)
                if key not in dist:
                    dist[key] = dist[(r, c, state)] + 1
                    queue.append(key)
    return dist
```

### Practice Problems

| # | Problem | Difficulty | Key Insight |
|---|---------|------------|-------------|
| 1293 | [Shortest Path in a Grid with Obstacles Elimination](https://leetcode.com/problems/shortest-path-in-a-grid-with-obstacles-elimination/) | Hard | State = (r, c, walls_remaining) |
| 864 | [Shortest Path to Get All Keys](https://leetcode.com/problems/shortest-path-to-get-all-keys/) | Hard | State = (r, c, keys_bitmask) |
| 1197 | [Minimum Knight Moves](https://leetcode.com/problems/minimum-knight-moves/) | Medium | BFS with knight movement, symmetry trick |
| 2258 | [Escape the Spreading Fire](https://leetcode.com/problems/escape-the-spreading-fire/) | Hard | Two BFS layers (fire spread + person) |
| 847 | [Shortest Path Visiting All Nodes](https://leetcode.com/problems/shortest-path-visiting-all-nodes/) | Hard | State = (node, visited_bitmask) |

---

## 6. DFS — When to Actually Use It

DFS is **not** for shortest distance. Use it for:

| Use Case | Example |
|---|---|
| Connectivity / island count | Number of Islands (200) |
| Cycle detection | Course Schedule (207) |
| Topological sort | Alien Dictionary (269) |
| Exhaustive path enumeration | All Paths Source Target (797) |
| Tree traversals | Any tree problem |
| Backtracking | Word Search (79), Sudoku Solver |

### DFS is WRONG for shortest path because:

```
Grid:         DFS might explore:    BFS explores:
S . . E       S→down→down→right...  S at dist 0
. . . .       (long path first)     neighbors at dist 1
. . . .                             ...shortest path found first
```

---

## 7. Pattern Decision Tree

```
Is the graph/grid unweighted?
├── YES → BFS
│         ├── One source → standard BFS
│         ├── Multiple sources → multi-source BFS
│         └── Extra state needed → BFS on (r, c, state)
│
└── NO → Are weights only 0 or 1?
          ├── YES → 0-1 BFS (deque)
          │
          └── NO → Are weights arbitrary positive?
                    ├── Minimize total cost → Dijkstra (min-heap)
                    ├── Maximize min edge / Minimize max edge → Dijkstra (max/min heap, bottleneck formula)
                    └── Negative weights → Bellman-Ford
```

---

## Quick Reference: Complexity

| Algorithm | Time | Space | Use When |
|---|---|---|---|
| BFS | O(V + E) | O(V) | Unweighted, shortest hops |
| Multi-source BFS | O(V + E) | O(V) | Nearest source for all cells |
| 0-1 BFS | O(V + E) | O(V) | Weights are only 0 or 1 |
| Dijkstra | O((V+E) log V) | O(V) | Non-negative weights |
| Bellman-Ford | O(VE) | O(V) | Negative weights |
| DFS | O(V + E) | O(V) | Connectivity, exhaustive search |

---

## Common Mistakes to Avoid

1. **DFS for shortest path** — DFS doesn't explore by distance. Always BFS/Dijkstra.
2. **Single-source BFS when multi-source is needed** — if you have multiple start points, seed them all at once.
3. **Not including state in visited** — in state-space BFS, `visited` must include the full state `(r, c, state)`, not just `(r, c)`.
4. **Forgetting to negate for max-heap in Python** — Python only has min-heap. Negate values for max-heap.
5. **Using Dijkstra visited-set wrong** — once a node is popped from the heap, its distance is final. Mark visited on pop, not on push.

---

## Study Order Recommendation

```
Week 1 — Foundation
  542 → 994 → 286 → 1162   (multi-source BFS, easy to medium)

Week 2 — Dijkstra
  743 → 1631 → 1514 → 1102  (Dijkstra variants)

Week 3 — Bottleneck + Combo
  778 → 2812 → 1368 → 2290  (bottleneck path + 0-1 BFS)

Week 4 — State Space (Hard)
  1293 → 864 → 847 → 2258   (BFS with state)
```
