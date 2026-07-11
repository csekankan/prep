# Grid DP — Max Score + Count Paths Pattern

## Problem: Number of Paths with Max Score (LC 1301)

Given a square board with digits, 'X' (blocked), 'S' (start, bottom-right), 'E' (end, top-left).  
Move only **up, left, or diagonal-up-left**. Find:
1. Maximum sum of digits along any path from S → E
2. Number of paths achieving that maximum (mod 10^9+7)

---

## How to Identify This Pattern

Ask yourself these questions:

1. **Is movement restricted to one general direction?**  
   → up/left only = DAG (no cycles) = DP works, no need for Dijkstra/BFS

2. **Are you optimizing a value AND counting optimal solutions?**  
   → Track both `dp` (optimal value) and `cnt` (number of ways) simultaneously

3. **Is the grid small (≤ 100)?**  
   → O(mn) DP is more than enough; no need for fancy data structures

4. **Can you define a clear subproblem?**  
   → "Best score from S to (i,j)" or "Best score from (i,j) to E"

**Red flags that it's NOT this pattern:**
- Movement in all 4 directions → BFS/DFS with visited set, not DP
- Negative weights or cycles → Bellman-Ford
- Unweighted shortest path → BFS

---

## Common Mistakes (What I Got Wrong)

### Mistake 1: Using Dijkstra on a DAG

```
WRONG THINKING: "I need the max score path → use Dijkstra with max-heap"
RIGHT THINKING: "Movement is only up/left → it's a DAG → simple DP in reverse order"
```

**Why it's wrong:**  
Dijkstra adds O(log n) overhead per cell for the heap. In a DAG, the topological order
(reverse loop) gives you the same result in O(1) per cell. Dijkstra is for graphs with
cycles where you don't know the processing order upfront.

**When you WOULD need Dijkstra:**  
Movement in all directions, weighted edges, no cycles guaranteed by structure.

### Mistake 2: Counting paths in a separate DFS pass without memoization

```
WRONG: Dijkstra for max score → unmemoized DFS for counting
       DFS explores 3^(m+n) paths → TLE even for m=10
```

**Why it's wrong:**  
Without memoization, the same cell is revisited exponentially many times.
The DFS branches 3 ways at each cell, and paths overlap massively.

**Fix options:**
- Add `@lru_cache` on `(i, j)` → O(mn) states
- Or better: compute count in the SAME DP loop as max score (no second pass)

### Mistake 3: DFS direction mismatch with DP values

```
WRONG:  dp[i][j] = score from S TO (i,j)     (increases toward E)
        DFS check: dp[r][c] == dp[i][j] - curBoard   (assumes score DECREASES)

RIGHT:  dp[r][c] == dp[i][j] + value(r,c)    (matches: score increases toward E)
```

**Why it's wrong:**  
If dp represents "score from S to cell", values INCREASE as you move toward E.
Subtracting `curBoard` assumes the reverse direction. Always make sure the DFS
traversal direction matches how dp values were computed.

### Mistake 4: Not considering the staleness check in Dijkstra

```python
# Without this, stale heap entries get processed → wasted work
val, i, j = heapq.heappop(q)
if dp[i][j] > val:    # ← this check is essential
    continue
```

---

## The Two DP Approaches

### Approach 1: Bottom-Up (Iterative)

**State:** `dp[i][j]` = max score from S(m-1,n-1) to (i,j)  
**Direction:** Loop from (m-1,n-1) → (0,0)  
**Neighbors:** Look at (i+1,j), (i,j+1), (i+1,j+1) — "who feeds into me"

```python
class Solution:
    def pathsWithMaxScore(self, board: List[str]) -> List[int]:
        MOD = 10**9 + 7
        m, n = len(board), len(board[0])

        dp  = [[-1] * n for _ in range(m)]
        cnt = [[0]  * n for _ in range(m)]
        dp[m-1][n-1] = 0
        cnt[m-1][n-1] = 1

        for i in range(m - 1, -1, -1):
            for j in range(n - 1, -1, -1):
                if (i == m-1 and j == n-1) or board[i][j] == 'X':
                    continue

                best = -1
                for di, dj in ((1, 0), (0, 1), (1, 1)):
                    ni, nj = i + di, j + dj
                    if ni < m and nj < n and dp[ni][nj] > best:
                        best = dp[ni][nj]

                if best < 0:
                    continue

                val = int(board[i][j]) if board[i][j].isdigit() else 0
                dp[i][j] = best + val

                for di, dj in ((1, 0), (0, 1), (1, 1)):
                    ni, nj = i + di, j + dj
                    if ni < m and nj < n and dp[ni][nj] == best:
                        cnt[i][j] = (cnt[i][j] + cnt[ni][nj]) % MOD

        return [max(dp[0][0], 0), cnt[0][0] % MOD]
```

### Approach 2: Top-Down (Recursive + Memoization)

**State:** `solve(i,j)` = (max score from (i,j) to E, path count)  
**Direction:** Recurse toward (0,0)  
**Neighbors:** Look at (i-1,j), (i,j-1), (i-1,j-1) — "where can I go"

```python
class Solution:
    def pathsWithMaxScore(self, board: List[str]) -> List[int]:
        MOD = 10**9 + 7
        m, n = len(board), len(board[0])

        @lru_cache(None)
        def solve(i, j):
            if board[i][j] == 'X':
                return (-1, 0)
            if i == 0 and j == 0:
                return (0, 1)

            val = int(board[i][j]) if board[i][j].isdigit() else 0
            best = -1
            ways = 0

            for di, dj in ((-1, 0), (0, -1), (-1, -1)):
                ni, nj = i + di, j + dj
                if not (0 <= ni < m and 0 <= nj < n):
                    continue
                sub_score, sub_cnt = solve(ni, nj)
                if sub_score < 0:
                    continue
                if sub_score > best:
                    best = sub_score
                    ways = sub_cnt
                elif sub_score == best:
                    ways += sub_cnt

            if best < 0:
                return (-1, 0)
            return (best + val, ways % MOD)

        score, paths = solve(m - 1, n - 1)
        return [max(score, 0), paths % MOD]
```

---

## DFS + Memoization Pattern (General Template)

This is a general pattern for grid DP problems using top-down recursion.

### When to use DFS + Memo vs Bottom-Up

| Use DFS + Memo when... | Use Bottom-Up when... |
|---|---|
| Only some cells are reachable (sparse) | All/most cells are visited |
| Subproblem depends on complex conditions | Dependencies follow a simple loop order |
| Easier to think recursively | Want maximum performance (no cache overhead) |
| State includes extra dimensions beyond (i,j) | State is just (i,j) |

### Template

```python
from functools import lru_cache

def grid_dp_memo(grid):
    m, n = len(grid), len(grid[0])
    
    @lru_cache(None)
    def solve(i, j):
        # 1. BASE CASE: destination reached
        if i == 0 and j == 0:
            return (base_value, 1)  # (score, 1 path)
        
        # 2. INVALID STATE: blocked or out of bounds
        if not valid(i, j):
            return (INVALID, 0)
        
        # 3. RECURSIVE CASE: try all valid moves
        best = INVALID
        ways = 0
        
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if in_bounds(ni, nj):
                sub_val, sub_cnt = solve(ni, nj)
                
                if sub_val == INVALID:
                    continue
                
                # MAXIMIZE (or MINIMIZE — change > to <)
                if sub_val > best:
                    best = sub_val
                    ways = sub_cnt
                elif sub_val == best:
                    ways += sub_cnt
        
        if best == INVALID:
            return (INVALID, 0)
        
        return (best + grid[i][j], ways % MOD)
    
    return solve(start_i, start_j)
```

### Key rules for DFS + Memo

1. **State must be hashable** — use tuples, not lists. `@lru_cache` needs immutable args.
2. **Return value encodes everything** — (score, count), not separate global variables.
3. **Mark INVALID distinctly** — use -1 or float('-inf'), never 0 (0 could be a valid score).
4. **Always check sub-result validity** — skip neighbors that returned INVALID.
5. **Mod only the count**, not the score (score is compared, count just accumulated).

### Common pitfalls

```
PITFALL 1: Forgetting @lru_cache
           → Exponential time, looks correct but TLEs

PITFALL 2: Mutable default args or global state
           → Cache returns stale results across test cases
           → Fix: put everything inside the function scope

PITFALL 3: Memo state too large
           → solve(i, j, val) where val has 1000 values = 100*100*1000 = 10M states
           → Fix: remove val, derive it from dp[i][j] instead

PITFALL 4: Direction mismatch
           → Top-down solve(i,j) means "from (i,j) to destination"
           → Neighbors must be TOWARD the destination
           → If destination is (0,0), move (-1,0), (0,-1), (-1,-1)
```

---

## Similar Problems for Practice

### Tier 1: Direct Pattern Match (Grid DP + Count Paths)

| # | Problem | Key Twist |
|---|---|---|
| **62** | Unique Paths | Count only (no score), basic grid DP |
| **63** | Unique Paths II | Add obstacles ('X' equivalent) |
| **64** | Minimum Path Sum | Min instead of max, no counting |
| **120** | Triangle | Non-rectangular grid, min path |
| **931** | Falling Squares / Minimum Falling Path Sum | 3 directions (down-left, down, down-right) |
| **1301** | Number of Paths with Max Score | **This problem** — max score + count |

### Tier 2: Grid DP with Counting (Moderate)

| # | Problem | Key Twist |
|---|---|---|
| **174** | Dungeon Game | DP from destination backward, min HP |
| **221** | Maximal Square | DP on grid, different state meaning |
| **329** | Longest Increasing Path in Matrix | 4-direction DFS + memo (DAG by value ordering) |
| **741** | Cherry Pickup | Two players simultaneously = 3D DP |
| **1463** | Cherry Pickup II | Two robots, 3D DP |
| **1594** | Maximum Non Negative Product in Matrix | Track both min and max (negative flips sign) |

### Tier 3: DFS + Memoization on Grids (Harder)

| # | Problem | Key Twist |
|---|---|---|
| **576** | Out of Boundary Paths | Count paths that leave grid, 4 directions |
| **1340** | Jump Game V | 1D but variable jump length |
| **1387** | Sort Integers by Power | Memo on non-grid recursive structure |
| **1444** | Number of Ways to Cut a Pizza | 3D DP (row, col, cuts remaining) |
| **2328** | Number of Increasing Paths in Grid | Count ALL increasing paths, not just longest |

### Tier 4: "Optimize + Count" Combo (Advanced)

| # | Problem | Key Twist |
|---|---|---|
| **1049** | Last Stone Weight II | Subset DP, optimize then count |
| **1155** | Number of Dice Rolls with Target Sum | DP with target value + counting |
| **1575** | Count All Possible Routes | DFS + memo with fuel state |
| **2435** | Paths in Matrix Whose Sum Is Divisible by K | DP with modular state |

---

## Decision Framework

```
START: Grid/path problem?
  │
  ├─ Movement in ONE general direction (up/left, down/right, etc.)?
  │   ├─ YES → It's a DAG → Use DP (no BFS/Dijkstra needed)
  │   │   ├─ Need just optimal value? → Single dp array
  │   │   ├─ Need optimal + count?   → dp + cnt arrays (this problem)
  │   │   ├─ Small grid, easy order? → Bottom-up (iterative)
  │   │   └─ Complex/sparse?         → Top-down (DFS + memo)
  │   │
  │   └─ NO → Movement in all directions?
  │       ├─ Unweighted? → BFS
  │       ├─ Weighted, no negative? → Dijkstra
  │       ├─ Values form a DAG (strictly increasing)? → DFS + memo (LC 329)
  │       └─ Negative weights? → Bellman-Ford
  │
  └─ NOT a grid?
      └─ Think about what forms the DAG / subproblem structure
```

---

## When NOT to Use DFS/Dijkstra — How to Pick DP

This is the most important section. The single question that decides everything:

**"Can I revisit a state?"**

```
Can I revisit a cell/state?
│
├─ NO  → It's a DAG → DP (loop or DFS+memo)
│
└─ YES → General graph → BFS / Dijkstra / Bellman-Ford
```

### How to Detect "No cycles" → Use DP

**Signal 1: Movement is restricted to one direction**

```
"move only right/down"          → can never go back → DAG → DP
"move only up/left/diag"        → can never go back → DAG → DP
"move only to larger indices"   → can never go back → DAG → DP

Examples:
  LC 62   Unique Paths           — only right/down
  LC 64   Minimum Path Sum       — only right/down
  LC 1301 Max Score Paths        — only up/left/diag
  LC 120  Triangle               — only down-left/down-right
```

**Signal 2: Values enforce an order**

Even with ALL 4 directions, if you can only move to strictly larger/smaller values,
there are no cycles.

```
"move to strictly increasing neighbors"   → DAG by value → DFS + memo
"move to cells with value > current"      → DAG by value → DFS + memo

Examples:
  LC 329  Longest Increasing Path  — 4 directions BUT strictly increasing = no cycles
  LC 2328 Increasing Paths Count   — same idea
```

**Signal 3: A dimension always decreases**

If one parameter of your state always shrinks, you can't cycle.

```
"fuel decreases each step"       → fuel = 0 is base case → DP
"cuts remaining decreases"       → cuts = 0 is base case → DP
"string gets shorter each step"  → empty = base case → DP

Examples:
  LC 1575 Count All Possible Routes — fuel decreases (4-dir BUT fuel is finite)
  LC 1444 Number of Ways to Cut a Pizza — cuts decrease
```

**Signal 4: Classic "choice at each step" problems**

```
"at step i, choose from options, move to step i+1" → linear DAG → DP

Examples:
  LC 198  House Robber          — rob or skip, move forward
  LC 322  Coin Change           — pick a coin, reduce amount
  LC 1335 Min Difficulty Job Schedule — assign jobs to days
```

### How to Detect "Yes cycles possible" → Use BFS/Dijkstra

**Signal 1: Free movement in all directions, no value ordering**

```
"move up/down/left/right freely"     → can revisit → NOT DP
"move to any neighbor"               → can revisit → NOT DP

Examples:
  LC 1091 Shortest Path in Binary Matrix — 8 directions, unweighted (BFS)
  LC 743  Network Delay Time             — general weighted graph (Dijkstra)
```

**Signal 2: "Shortest path" keyword**

```
"shortest path" + unweighted  → BFS
"shortest path" + weighted    → Dijkstra
"shortest path" + negative    → Bellman-Ford
```

**Signal 3: State can be reached from multiple directions without natural order**

```
"you can teleport back"    → cycles possible → BFS/Dijkstra
"edges go both ways"       → cycles possible → BFS/Dijkstra
```

### The Trap: "It LOOKS like Dijkstra but it's DP"

This is the exact trap LC 1301 sets:

```
WRONG:
  "I want max score along a path"
  "Max score = optimization"
  "Path optimization = Dijkstra"              ← WRONG JUMP

RIGHT:
  "I want max score along a path"
  "Can I revisit cells? No — moves are only up/left"
  "No revisits = DAG"
  "DAG optimization = DP"                     ← CORRECT
```

**The rule:** Dijkstra finds optimal paths when you DON'T know processing order.
DP finds optimal paths when you DO know the order (because it's a DAG).

### Quick Decision Table

| Ask yourself | Answer | Use |
|---|---|---|
| Can I only move in one direction (right/down, up/left)? | Yes | **DP** (loop) |
| All directions, but only to strictly larger/smaller values? | Yes | **DP** (DFS + memo) |
| Does a state parameter always decrease (fuel, cuts, length)? | Yes | **DP** (DFS + memo) |
| "Shortest path" on unweighted graph? | Yes | **BFS** |
| "Shortest/cheapest path" on weighted graph? | Yes | **Dijkstra** |
| Negative edge weights? | Yes | **Bellman-Ford** |

### Concrete Side-by-Side Comparisons

```
"Max score, move only up/left"
 → restricted direction → DAG → DP ✓

"Max score, move any direction, visit each cell once"
 → need visited set → DFS/backtracking (NP-hard in general)

"Shortest path, move any direction, weighted"
 → Dijkstra ✓

"Shortest path, move any direction, weights 0 or 1"
 → 0-1 BFS (deque trick) ✓

"Longest increasing path, move any direction"
 → strictly increasing = no cycles → DFS + memo ✓

"Count paths from A to B, move any direction, K steps"
 → state = (cell, steps_remaining), steps always decrease → DP ✓
```

### One-Liner Decision

> **If you can define a loop order where every dependency is already computed, use DP.
> If you can't, use BFS/Dijkstra.**

---

## Key Takeaways

1. **DAG = DP.** If movement is restricted (no cycles), you never need Dijkstra or BFS.
   Just loop in the right order (or use DFS + memo).

2. **Count in the same pass.** When neighbors tie for the best, SUM their counts.
   Never compute count in a separate pass if you can avoid it.

3. **Memoize or die.** Without caching, DFS on a grid is exponential.
   `@lru_cache(None)` on `(i, j)` = O(mn) states. Always add it.

4. **Direction consistency.** If dp means "S to cell", values increase toward E.
   If dp means "cell to E", values increase toward S.
   Make sure your neighbor checks match.

5. **Bottom-up > Top-down for simple grids.** No recursion stack, no cache dict,
   no function call overhead. Use top-down only when the recursion is more natural
   or when many cells are unreachable.
