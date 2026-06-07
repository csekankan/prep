# Digit DP

---

## Part 1: Concept

### What Is It?

Technique to count or sum over integers in **[L, R]** whose digits satisfy some property, without iterating every number.

**Build the number digit by digit (left → right), tracking a compact state via memoized DFS.**

### When to Use

- Range is huge (up to 10^18), brute force impossible
- Property depends on individual digits: digit sum, adjacent digits, specific digit counts, divisibility, peaks/valleys

### Three Pillars

**1. Tight Constraint**

If every digit so far exactly matches the upper limit, the next digit is capped at `limit[pos]`. Otherwise 0–9.

```
Counting ≤ 3456:
  Pick 3 at pos 0 → pos 1 capped at 4 (tight)
  Pick 2 at pos 0 → pos 1 free 0–9 (not tight)
```

Once you go below the limit at any position, all future digits are unconstrained.

**2. Leading Zeros**

`007` is just `7`. Track with a `started` flag or `-1` sentinel so leading zeros don't corrupt state.

**Rule: During leading zeros, store `-1` not `0`.**

**3. Range Decomposition**

```
answer = solve(R) - solve(L - 1)
```

`solve(N)` = answer for `[0, N]`. Off-by-one trap: it's `L-1`, not `L`.

### Complexity

```
O(D × 2 × 2 × S × 10)
   pos tight started state digits_per_pos
```

D ≤ 18 for numbers up to 10^18. Almost always fast enough.

---

## Part 2: Templates

### Template A — Counting numbers with a property

Use when: count how many numbers in [0, N] satisfy a condition.

```python
from functools import lru_cache

def solve(N):
    if N < 0:
        return 0
    digits = list(map(int, str(N)))
    n = len(digits)

    @lru_cache(None)
    def dfs(pos, tight, started, state):
        if pos == n:
            if not started:
                return 0          # don't count "empty" number
            return 1 if valid(state) else 0

        limit = digits[pos] if tight else 9
        res = 0
        for d in range(limit + 1):
            nTight  = tight and (d == limit)
            nStart  = started or (d != 0)
            nState  = state             # update based on problem
            if not started and d == 0:
                nState = initial_state  # leading zero — don't update state
            else:
                nState = transition(state, d)
            res += dfs(pos + 1, nTight, nStart, nState)
        return res

    return dfs(0, True, False, initial_state)

answer = solve(R) - solve(L - 1)
```

### Template B — Summing a value across all numbers (contribution counting)

Use when: sum some per-number value (like waviness, digit count) across [0, N].

Return **(count, total_sum)** from each state. When a digit contributes +X to the value, add `X × subCnt` (every completion gets that contribution).

```python
from functools import lru_cache

def solve(N):
    if N < 0:
        return 0
    digits = list(map(int, str(N)))
    n = len(digits)

    @lru_cache(None)
    def dfs(pos, tight, started, state):
        if pos == n:
            return (1, 0)  # (count=1, sum=0)

        limit = digits[pos] if tight else 9
        cnt = total = 0
        for d in range(limit + 1):
            nTight  = tight and (d == limit)
            nStart  = started or (d != 0)
            nState  = transition(state, d, nStart)
            c, s = dfs(pos + 1, nTight, nStart, nState)

            contribution = compute_contribution(state, d)
            total += contribution * c  # this digit adds to ALL completions
            cnt   += c
            total += s                 # plus sum from future positions
        return (cnt, total)

    return dfs(0, True, False, initial_state)[1]
```

### Common State Variables

| Problem | State | Template |
|---------|-------|----------|
| Digit sum = K | `cur_sum` | A |
| No adjacent equal digits | `last_digit` | A |
| Contains digit X | `bool seen_x` | A |
| All digits unique | `bitmask` (10 bits) | A |
| Divisible by M | `remainder % M` | A |
| Sum of waviness | `prev, cur` (two trailing) | B |
| Total count of digit X | `(nothing extra)` | B |

---

## Part 3: Worked Examples

### Example 1: Count numbers in [0, N] with digit sum = S

State = `cur_sum`. Template A.

```python
from functools import lru_cache

def count_digit_sum(N, S):
    if N < 0:
        return 0
    digits = list(map(int, str(N)))
    n = len(digits)

    @lru_cache(None)
    def dfs(pos, tight, cur_sum):
        if cur_sum > S:
            return 0
        if pos == n:
            return 1 if cur_sum == S else 0
        limit = digits[pos] if tight else 9
        res = 0
        for d in range(limit + 1):
            res += dfs(pos + 1, tight and (d == limit), cur_sum + d)
        return res

    return dfs(0, True, 0)
```

### Example 2: Count numbers in [0, N] with no adjacent equal digits

State = `last_digit`. Template A. Needs leading zero handling.

```python
from functools import lru_cache

def count_no_adjacent(N):
    if N <= 0:
        return 0
    digits = list(map(int, str(N)))
    n = len(digits)

    @lru_cache(None)
    def dfs(pos, tight, last, started):
        if pos == n:
            return 1 if started else 0
        limit = digits[pos] if tight else 9
        res = 0
        for d in range(limit + 1):
            if not started and d == 0:
                res += dfs(pos + 1, tight and (d == limit), -1, False)
            elif d != last:
                res += dfs(pos + 1, tight and (d == limit), d, True)
        return res

    return dfs(0, True, -1, False)
```

---

## Part 4: Total Waviness Problem (Hard — Template B)

### Problem

Given [num1, num2], return the **sum of waviness** of all integers in the range.

Waviness = count of peaks + valleys in the digit sequence.
- Peak: `prev < cur > next`
- Valley: `prev > cur < next`

```
1 3 2 4
  ↑ ↑
  P V     → waviness = 2
```

### Why Template B?

We're summing waviness across all numbers, not just counting. Need `(count, total_waviness)`.

### State Design

Need **two trailing digits** to detect peak/valley:

```
... prev  cur  [digit being placed]
         ↑
   Can now check: is cur a peak or valley?
```

State = `(pos, tight, start, prev, cur)` where prev and cur are `-1` during leading zeros.

### Contribution Logic

```
When cur IS a peak/valley:
    waive += subCnt     ← +1 for every number completable from here

Always:
    waive += subWaive   ← waviness from positions further right
```

### Solution

```python
from functools import lru_cache

class Solution:
    def totalWaviness(self, num1: int, num2: int) -> int:
        def solve(num):
            digits = list(map(int, str(num)))
            n = len(digits)
            if n < 3:
                return 0

            @lru_cache(None)
            def dfs(pos, tight, start, prev, cur):
                if pos == n:
                    return (1, 0)

                limit = digits[pos] if tight else 9
                cnt = waive = 0
                for d in range(limit + 1):
                    nTight = tight and (d == limit)
                    nStart = start and (d == 0)
                    nCur   = -1 if nStart else d       # KEY: -1 during leading zeros
                    c, w   = dfs(pos + 1, nTight, nStart, cur, nCur)

                    if not nStart and prev >= 0 and cur >= 0:
                        if (d > cur and prev > cur) or (d < cur and prev < cur):
                            waive += c                 # contribution counting

                    cnt   += c
                    waive += w
                return (cnt, waive)

            return dfs(0, True, True, -1, -1)[1]

        return solve(num2) - solve(num1 - 1)
```

### Trace: number 91 (in 3-digit context)

| pos | digit | start | prev | cur | check? |
|-----|-------|-------|------|-----|--------|
| 0 | 0 | True | -1 | **-1** (not 0!) | — |
| 1 | 9 | False | -1 | 9 | prev=-1 → skip |
| 2 | 1 | False | -1 | 9 | prev=-1 → skip |

Waviness = 0. Correct — 91 is 2 digits, no interior digit.

### Trace: number 1324

| pos | digit | prev | cur | check? |
|-----|-------|------|-----|--------|
| 0 | 1 | -1 | 1 | — |
| 1 | 3 | -1 | 3 | prev=-1 → skip |
| 2 | 2 | 1 | 3 | 1<3>2 → peak! waive += c |
| 3 | 4 | 3 | 2 | 3>2<4 → valley! waive += c |

Waviness = 2. Correct.

### States: ~77K

```
pos(18) × tight(2) × start(2) × prev(11: -1..9) × cur(11: -1..9) ≈ 77K
```

---

## Part 5: Mistakes & Pitfalls

### Mistake 1 — Leading zeros leak as digit 0

**Bug:** `dfs(..., cur, digit)` — a leading zero `0` gets stored, later looks like a real digit.

```
Number 91 in 3-digit context:
  WRONG: 0, 9, 1 → sees "0<9>1" → false peak!
  RIGHT: -1, 9, 1 → prev=-1 → guard blocks
```

**Fix:** `nCur = -1 if nStart else d`

### Mistake 2 — @lru_cache without (None) → TLE

```python
@lru_cache         # maxsize=128 (default!) — evicts constantly on 77K states
@lru_cache(None)   # unlimited — what you need
```

**#1 cause of TLE in digit DP.**

### Mistake 3 — Return list instead of tuple

```python
return [cnt, waive]   # list — not hashable, can cause subtle caching bugs
return (cnt, waive)   # tuple — hashable, safe
```

### Mistake 4 — Range off-by-one

```python
solve(R) - solve(L - 1)   # correct
solve(R) - solve(L)       # WRONG — excludes L itself
```

### Mistake 5 — Missing guard for peak/valley check

Must verify **both** `prev >= 0` and `cur >= 0` before comparing. Otherwise `-1` (sentinel) participates in comparisons and `-1 < anything` is always true → false peaks.

---

## Part 6: Quick Revision Card

```
WHAT:  Count/sum over [L,R] by building number digit-by-digit
RANGE: solve(R) - solve(L-1)
TIGHT: limit = digits[pos] if tight else 9
ZEROS: nCur = -1 if nStart else d   (never store 0 for leading zeros)
CACHE: @lru_cache(None)             (not @lru_cache!)
RETURN: tuples, not lists

TEMPLATE A (counting):  return count
TEMPLATE B (summing):   return (count, total_sum)
  contribution: total += X * subCnt  (X added to every completion)

WAVINESS STATE: dfs(pos, tight, start, prev, cur)
  CHECK:  prev < cur > d (peak) or prev > cur < d (valley)
  GUARD:  only when prev ≥ 0 AND cur ≥ 0 AND not leading
  BASE:   pos==n → (1,0);  num<100 → 0
```

---

## Part 7: Practice Problems

| Problem | Pattern | Key Idea |
|---------|---------|----------|
| LC 233 — Number of Digit One | Template B | Contribution counting for digit 1 |
| LC 902 — Numbers At Most N Given Digit Set | Template A | Restricted digit set |
| LC 1012 — Numbers With Repeated Digits | Template A | Bitmask of used digits |
| LC 2719 — Count of Integers (digit sum in range) | Template A | Digit sum bounds |
| LC 2999 — Count the Number of Powerful Integers | Template A | Suffix constraint + tight |
| Total Waviness | Template B | Two trailing digits, peak/valley |
| CSES — Counting Numbers | Template A | No adjacent equal digits |
| CF 628D — Magic Numbers | Template A | Divisibility + positional digit |
