# Multi-Path DP Pattern (Two Simultaneous Walks)

## When to Use

- Problem says "go from A to B, then return from B to A" on the same grid
- Two agents collecting resources on the same grid
- Two paths that share/interact with the same state (picking items, blocking cells)
- Greedy (solve one path, then the other) does NOT work because paths affect each other

## Core Idea

**"Go and return" = "Two people walking forward simultaneously"**

A return path (left/up) is just a forward path (right/down) in reverse.
So instead of solving two separate problems, simulate both walkers at the same time.

## Dimension Reduction Trick

If both walkers can only move **right or down**, every step increases (row + col) by 1.

```
row + col = t   (where t = number of steps taken)
```

So `col = t - row`. You don't need to store the column.

### State: `dp(t, r1, r2)`

- `t` = steps taken (same for both walkers)
- `r1` = row of person 1 → column is `t - r1`
- `r2` = row of person 2 → column is `t - r2`

This reduces 4D `(r1, c1, r2, c2)` → 3D `(t, r1, r2)`

## Recurrence

Each person independently moves right or down → 4 combinations:

```
dp(t, r1, r2) = current_cherries + max(
    dp(t+1, r1+1, r2+1),   # both down
    dp(t+1, r1+1, r2),     # person1 down, person2 right
    dp(t+1, r1,   r2+1),   # person1 right, person2 down
    dp(t+1, r1,   r2),     # both right
)
```

**Double-counting rule:** If `r1 == r2` (same cell), count the cherry only once.

## Template Code

```python
def twoPathDP(grid):
    n = len(grid)
    memo = {}

    def dp(t, r1, r2):
        c1, c2 = t - r1, t - r2

        # out of bounds or blocked
        if r1 >= n or r2 >= n or c1 >= n or c2 >= n:
            return float('-inf')
        if grid[r1][c1] == -1 or grid[r2][c2] == -1:
            return float('-inf')

        # reached destination
        if r1 == n - 1 and c1 == n - 1:
            return grid[r1][c1]

        if (t, r1, r2) in memo:
            return memo[(t, r1, r2)]

        # collect cherries (avoid double-counting)
        cherries = grid[r1][c1]
        if r1 != r2:
            cherries += grid[r2][c2]

        # 4 next states
        best = max(
            dp(t + 1, r1 + 1, r2 + 1),
            dp(t + 1, r1 + 1, r2),
            dp(t + 1, r1, r2 + 1),
            dp(t + 1, r1, r2),
        )

        memo[(t, r1, r2)] = cherries + best
        return memo[(t, r1, r2)]

    return max(0, dp(0, 0, 0))
```

## Complexity

- Time: O(n^3) — t goes to 2n, r1 and r2 each go to n
- Space: O(n^3) for memoization

## Why Greedy Fails

Finding the best path first, clearing it, then finding the second best path does NOT
give the global optimum. The first path might "steal" cherries that would have allowed
a much better pair of paths overall. The two paths must be optimized jointly.

## Key Recognition Signals

| You see...                          | Think...                                  |
|-------------------------------------|-------------------------------------------|
| Go then return on same grid         | Two simultaneous forward walks             |
| Two paths sharing resources         | Joint DP, not two separate DPs             |
| Only move right/down                | row + col = steps, reduce dimensions       |
| "Max collection" with interactions  | Can't be greedy, must be DP                |
| Two agents on grid, same start/end  | Synchronize by step count t                |

## Variations

### Variation 1: Two walkers, different starting columns (Cherry Pickup II)

Walkers start at top row in different columns, move down one row each step.
State: `dp(row, c1, c2)` — row is shared (both move down together).

### Variation 2: Single path

When there's only one path, it simplifies to standard 2D grid DP.

---

## Practice Problems

### Direct Pattern (Two Paths on Grid)

1. **Cherry Pickup** (Hard)
   https://leetcode.com/problems/cherry-pickup/
   Go (0,0)→(n-1,n-1) and return. Classic two-walker problem.

2. **Cherry Pickup II** (Hard)
   https://leetcode.com/problems/cherry-pickup-ii/
   Two robots start at top corners, move down. State: dp(row, c1, c2).

### Prerequisites (Single Path Grid DP)

3. **Minimum Path Sum** (Medium)
   https://leetcode.com/problems/minimum-path-sum/
   Single path, right/down only. Foundation for multi-path.

4. **Unique Paths** (Medium)
   https://leetcode.com/problems/unique-paths/
   Count paths in grid. Builds intuition for right/down movement.

5. **Unique Paths II** (Medium)
   https://leetcode.com/problems/unique-paths-ii/
   Same as above but with obstacles (like thorns in cherry pickup).

6. **Dungeon Game** (Hard)
   https://leetcode.com/problems/dungeon-game/
   Single path, reverse DP. Good practice for grid DP direction.

### Related Multi-Agent / Multi-Path DP

7. **Maximum Number of Points with Cost** (Medium)
   https://leetcode.com/problems/maximum-number-of-points-with-cost/
   Row-by-row DP with transition cost. Similar state design.

8. **Triangle** (Medium)
   https://leetcode.com/problems/triangle/
   Top-down path in triangle. Good warmup for path DP.

9. **Minimum Falling Path Sum** (Medium)
   https://leetcode.com/problems/minimum-falling-path-sum/
   Single agent moving down a grid. Simpler version of Cherry Pickup II.

10. **Minimum Falling Path Sum II** (Hard)
    https://leetcode.com/problems/minimum-falling-path-sum-ii/
    Harder variant with non-adjacent column constraint.

### Suggested Order

```
Unique Paths → Unique Paths II → Minimum Path Sum → Triangle
→ Minimum Falling Path Sum → Dungeon Game
→ Cherry Pickup → Cherry Pickup II
→ Minimum Falling Path Sum II → Maximum Number of Points with Cost
```
