# Subarray Sum Problems — Interview Intuition Guide

> **Goal:** By the end of this guide, you will be able to look at a subarray problem in an interview and immediately know whether prefix sums apply, how to set up the transformation, and how to count pairs efficiently.

---

## Part 1 — What is a Subarray Sum Problem?

A **subarray** is a contiguous slice of an array.  
A **subarray sum** is the total of all elements in that slice.

Problems that ask you to **count** or **find** subarrays based on their sum are the target of this guide.

### Recognising the pattern in an interview

You are likely dealing with a subarray-sum problem when you see phrases like:

| Phrase in problem | What it really means |
|---|---|
| "subarrays with sum equal to k" | classic prefix sum |
| "subarrays with sum divisible by k" | prefix sum + modular arithmetic |
| "subarrays where element X appears more than half the time" | +1/-1 transform → sum > 0 |
| "subarrays with equal 0s and 1s" | recode 0→-1, find sum = 0 |
| "shortest subarray with sum ≥ k" | prefix sum + monotonic deque |
| "number of pairs (i, j) such that …" | almost always prefix sums |

The instant you see **"subarray"** + **"count"** + **some condition on values**, your first thought should be: *can I express this condition as a sum?*

---

## Part 2 — The Core Idea: Prefix Sums

### Definition

```
prefix[0] = 0
prefix[1] = nums[0]
prefix[2] = nums[0] + nums[1]
...
prefix[i] = nums[0] + nums[1] + ... + nums[i-1]
```

### Key formula

```
sum of subarray [l, r]  =  prefix[r+1] - prefix[l]
```

This is the single most important identity. Write it down, memorise it.

### Why does this help?

Instead of recomputing the sum of every subarray (O(n²)), you compute prefix sums once (O(n)) and then express any subarray sum as a **difference of two prefix values**.

---

## Part 3 — The Three Subarray Sum Patterns

### Pattern 1 — Count subarrays with sum exactly equal to `k`

**Example:** `nums = [1, 2, 3, -1, 2]`, `k = 4`

We want: `prefix[r+1] - prefix[l] = k`, i.e., `prefix[l] = prefix[r+1] - k`.

**Algorithm:**
1. Walk left to right, maintaining a running prefix sum `curr`.
2. At each step, check how many times `curr - k` has appeared before. That is the count of valid subarrays ending here.
3. Record `curr` in a frequency map.

```python
from collections import defaultdict

def count_subarrays_sum_k(nums, k):
    freq = defaultdict(int)
    freq[0] = 1       # empty prefix (sum 0) seen once
    curr = 0
    result = 0

    for x in nums:
        curr += x
        result += freq[curr - k]   # subarrays ending here with sum = k
        freq[curr] += 1

    return result
```

**Trace for `nums = [1, 2, 3, -1, 2]`, `k = 4`:**

| step | x  | curr | looking for curr-k = curr-4 | freq before update | result |
|------|----|------|-----------------------------|--------------------|--------|
| init | -  | 0    | -                           | {0:1}              | 0      |
| 0    | 1  | 1    | -3 → 0 matches              | {0:1}              | 0      |
| 1    | 2  | 3    | -1 → 0 matches              | {0:1, 1:1}         | 0      |
| 2    | 3  | 6    | 2 → 0 matches               | {0:1, 1:1, 3:1}    | 0      |
| 3    | -1 | 5    | 1 → 1 match                 | {…, 6:1}           | 1      |
| 4    | 2  | 7    | 3 → 1 match                 | {…, 5:1}           | 2      |

Answer = **2** (subarrays `[3, -1, 2]` and `[2, 3, -1]`... wait let's verify)

Subarrays with sum 4:
- `[1, 2, 3, -1, 2]` slices: `[1,2,3,-1,2]`? sum=7. No.
- Check: `[2,3,-1]`=4 ✓, `[-1,2]`=1, `[3,-1,2]`=4 ✓ → **2 subarrays**. Correct.

---

### Pattern 2 — Count subarrays with sum `> 0` (or `< 0`, `≥ k`, etc.)

**Example:** `nums = [1, -1, 1, 1, -1]` (after +1/-1 transform)

We want: `prefix[r+1] - prefix[l] > 0`, i.e., `prefix[l] < prefix[r+1]`.

This is now: **count pairs (l, r+1) where l < r+1 and prefix[l] < prefix[r+1]** — essentially a **count of inversions** variant, or a **rank query**.

**Algorithm:**
1. Walk left to right with running prefix sum `curr`.
2. At each step, count how many previously seen prefix sums are **strictly less than `curr`**.
3. Record `curr`.

For counting "how many stored values < curr" efficiently, use a **frequency array with a prefix trick** or a **Binary Indexed Tree (BIT/Fenwick Tree)**.

```python
def count_subarrays_positive_sum(nums):
    n = len(nums)
    # prefix sums range from -n to +n; offset by n so all indices are ≥ 0
    # index = curr + offset, so prefix sum 0 → index n
    freq = [0] * (2 * n + 2)

    offset = n
    freq[offset] = 1    # prefix sum 0 seen once (the empty prefix before any element)

    curr = 0
    result = 0
    for x in nums:
        curr += x
        # count stored prefix sums strictly < curr
        # = sum of freq[0 .. curr+offset-1]
        result += sum(freq[:curr + offset])   # O(n) per step → O(n²) total — replace with BIT for O(n log n)
        freq[curr + offset] += 1

    return result
```

---

### Pattern 3 — Count subarrays with sum divisible by `k`

We want: `(prefix[r+1] - prefix[l]) % k == 0`, i.e., `prefix[r+1] % k == prefix[l] % k`.

**Algorithm:** Same as Pattern 1 but store `curr % k` in the frequency map.

```python
from collections import defaultdict

def count_subarrays_divisible_by_k(nums, k):
    freq = defaultdict(int)
    freq[0] = 1
    curr = 0
    result = 0

    for x in nums:
        curr = (curr + x) % k
        result += freq[curr]
        freq[curr] += 1

    return result
```

---

## Part 4 — The +1/-1 Transform (for non-numeric conditions)

Many problems do not look like sum problems at first. The trick is to **recode** the array so that your condition becomes a sum condition.

### Classic transforms

| Original condition | Recode | Sum condition |
|---|---|---|
| Count of `target` > count of others | target→+1, others→-1 | sum > 0 |
| Equal number of 0s and 1s | 0→-1, 1→+1 | sum = 0 |
| Count of A > count of B | A→+1, B→-1 | sum > 0 |
| Count of A ≥ k × count of B | A→(k-1), B→-1... | sum ≥ 0 |

### Worked example — Equal 0s and 1s

`nums = [0, 1, 0, 0, 1, 1]`

Recode 0→-1: `[-1, +1, -1, -1, +1, +1]`

Want subarrays with sum = 0 → use Pattern 1 with k=0.

```python
from collections import defaultdict

def count_equal_01(nums):
    coded = [1 if x == 1 else -1 for x in nums]
    freq = defaultdict(int)
    freq[0] = 1
    curr = 0
    result = 0
    for x in coded:
        curr += x
        result += freq[curr]   # curr - 0 = curr, same prefix seen before
        freq[curr] += 1
    return result
```

---

## Part 5 — The Binary Indexed Tree (for "count values < x")

When you need to count "how many stored values are strictly less than `curr`", a frequency array alone forces you to scan O(n) elements. A BIT gives you a **prefix sum query in O(log n)**.

### How a BIT works (minimal mental model)

A BIT stores a frequency array and answers:
- `update(i)` — record that value `i` has appeared
- `query(i)` — how many values ≤ i have appeared so far?

Then "how many values < curr" = `query(curr - 1)`.

```python
class BIT:
    """Binary Indexed Tree for prefix sum queries."""

    def __init__(self, size):
        self.n = size
        self.tree = [0] * (size + 1)

    def update(self, i, delta=1):
        """Add delta at position i (1-indexed)."""
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)

    def query(self, i):
        """Return sum of positions 1..i."""
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & (-i)
        return total
```

### Full solution for "count subarrays with majority element"

```python
def countMajoritySubarrays(nums, target):
    n = len(nums)
    bit = BIT(2 * n + 1)

    # offset = n+1 so that prefix sum 0 maps to index n+1 (all indices ≥ 1)
    offset = n + 1
    bit.update(offset)    # record initial prefix sum 0

    curr = 0              # running prefix sum (in original -n..+n range)
    result = 0

    for x in nums:
        curr += 1 if x == target else -1
        # count stored prefix sums strictly < curr
        # in shifted coordinates that is index < curr + offset
        result += bit.query(curr + offset - 1)
        bit.update(curr + offset)

    return result
```

---

## Part 6 — Interview Decision Tree

```
You see a subarray counting problem
            │
            ▼
Does the condition involve a SUM or can you
RECODE elements to make it about a sum?
            │
     ┌──────┴──────┐
    YES             NO
     │              │
     ▼              ▼
Compute prefix   Think sliding window
sums as you go   or two pointers
     │
     ▼
What is the condition on prefix[r] - prefix[l]?
     │
     ├── = k    →  freq map, look up freq[curr - k]          O(n)
     │
     ├── = 0    →  freq map, look up freq[curr]              O(n)
     │
     ├── % k=0  →  freq map with modular prefix sums        O(n)
     │
     └── > 0 /  →  BIT or sorted structure,
         < 0       query "how many stored values < curr"    O(n log n)
```

---

## Part 7 — The Majority Element Problem, Fully Revisited

Now with all the tools in hand:

**Problem:** Count subarrays where `target` appears strictly more than half the time.

**Step 1 — Identify it as a sum problem.**  
"More than half" → count(target) > count(others) → recode as +1/-1 → need sum > 0.

**Step 2 — Express as prefix sum condition.**  
sum > 0 → `prefix[r+1] > prefix[l]` → count pairs where later prefix > earlier prefix.

**Step 3 — Two ways to count "stored values < curr"**

Since every element is +1 or -1, `curr` only ever moves by **+1 or -1** each step. This lets us maintain the count incrementally in O(1) per step instead of querying a BIT.

---

### Approach A — BIT (O(n log n), works for any step size)

```python
def countMajoritySubarrays(nums, target):
    n = len(nums)
    bit = BIT(2 * n + 1)
    offset = n + 1
    bit.update(offset)          # prefix sum 0 → index n+1

    curr = 0
    result = 0
    for x in nums:
        curr += 1 if x == target else -1
        result += bit.query(curr + offset - 1)   # count stored values < curr
        bit.update(curr + offset)

    return result
```

---

### Approach B — Incremental (O(n), works because curr moves ±1 only)

Key insight: `presum` = count of stored prefix sums < curr, kept live.

- `curr` goes **+1**: new presum = old presum + freq[old curr] (add the boundary)
- `curr` goes **-1**: new presum = old presum - freq[new curr] (remove the boundary)

```python
def countMajoritySubarrays(nums, target):
    n = len(nums)
    pre = [0] * (2 * n + 1)    # pre[i] = freq of prefix sum (i - n)
    pre[n] = 1                  # prefix sum 0 seen once; offset = n

    cnt = n                     # cnt = curr + offset (shifted current prefix sum)
    presum = 0                  # count of stored prefix sums < curr
    result = 0

    for x in nums:
        if x == target:
            presum += pre[cnt]  # curr going +1: add freq of old curr (the new boundary)
            cnt += 1
            pre[cnt] += 1
        else:
            cnt -= 1
            presum -= pre[cnt]  # curr going -1: remove freq of new curr (lost boundary)
            pre[cnt] += 1
        result += presum

    return result
```

**Trace for `[1, 2, 1, 1]`, `target=1`, `n=4`, `offset=4`:**

| x | action | cnt | presum | result |
|---|--------|-----|--------|--------|
| 1 | presum+=pre[4]=1, cnt=5, pre[5]+=1 | 5 | 1 | 1 |
| 2 | cnt=4, presum-=pre[4]=1, pre[4]+=1 | 4 | 0 | 1 |
| 1 | presum+=pre[4]=2, cnt=5, pre[5]+=1 | 5 | 2 | 3 |
| 1 | presum+=pre[5]=2, cnt=6, pre[6]+=1 | 6 | 4 | 7 |

Answer = **7**.

---

### Complexity comparison

| Approach | Time | When to use |
|---|---|---|
| Naive `sum(freq[:])` | O(n²) | Never — teaching only |
| BIT | O(n log n) | When curr can jump by any amount |
| Incremental (official) | **O(n)** | When curr only moves ±1 (this problem) |

---

## Part 8 — Count of Inversions and Rank Queries

These two ideas are the engine behind Pattern 2 (sum > 0). They appear across many hard problems, so understanding them on their own pays off.

---

### 8a — Count of Inversions

#### Definition

An **inversion** in an array `A` is a pair of indices `(i, j)` such that:
```
i < j   and   A[i] > A[j]
```
In plain English: an earlier element is **larger** than a later one.

#### Why it matters here

When you want "count subarrays with sum > 0", you end up with an array of prefix sums `P` and you want:
```
count pairs (i, j) where i < j and P[i] < P[j]
```
This is the **complement** of inversions. Inversions ask for `P[i] > P[j]`; you want `P[i] < P[j]`. Same structure, opposite inequality.

#### Brute force — O(n²)

```python
def count_inversions_brute(arr):
    n = len(arr)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if arr[i] > arr[j]:
                count += 1
    return count
```

#### Why O(n²) is too slow and what to do instead

For n = 10⁵, O(n²) = 10¹⁰ operations — way too slow.

The insight: instead of comparing every pair, process elements **one by one left to right** and ask:

> "Of all elements I have already seen, how many are greater than the current one?"

That is a **rank query** — explained next.

#### Merge sort approach — O(n log n)

During merge sort, whenever you pick an element from the **right half** to place before elements remaining in the **left half**, all those remaining left-half elements form inversions with it.

```python
def count_inversions_merge(arr):
    """Returns (sorted_array, inversion_count)."""
    if len(arr) <= 1:
        return arr, 0

    mid = len(arr) // 2
    left, left_inv = count_inversions_merge(arr[:mid])
    right, right_inv = count_inversions_merge(arr[mid:])

    merged = []
    inversions = left_inv + right_inv
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            # left[i] > right[j]: every remaining element in left
            # is also > right[j], so they all form inversions with right[j]
            inversions += len(left) - i
            merged.append(right[j])
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged, inversions
```

**Trace for `[3, 1, 2]`:**

```
Inversions: (3,1), (3,2) → count = 2

Merge sort split:
  left  = [3]   right = [1, 2]
  Merge [3] and [1, 2]:
    3 > 1: inversions += 1 (just [3] remaining in left), pick 1
    3 > 2: inversions += 1, pick 2
    pick 3
  Result: [1, 2, 3], inversions = 2  ✓
```

---

### 8b — Rank Query

#### Definition

A **rank query** asks: given a set of numbers already inserted, how many of them are **less than (or less than or equal to) a given value `x`**?

```
rank(x) = count of inserted elements < x
```

This is exactly what you need for "count subarrays with sum > 0":

```
At each position, curr = current prefix sum
Query: how many previously stored prefix sums are < curr?
Answer: rank(curr) over the set of stored prefix sums
```

#### Three ways to answer rank queries

**Method 1 — Sorting + binary search (offline, static)**

If you have all queries in advance, sort the inserted values and use binary search.

```python
import bisect

stored = []
def insert(x):
    bisect.insort(stored, x)

def rank(x):
    return bisect.bisect_left(stored, x)   # count of elements < x
```

- Insert: O(n) per call (shifting in sorted list) — not great for large n
- Query: O(log n)

**Method 2 — Binary Indexed Tree (online, dynamic)**

When elements arrive one by one and you need to query immediately after each insertion.

Map values to indices (coordinate compression if needed), then:
- `bit.update(x)` — insert x
- `bit.query(x - 1)` — how many inserted values are < x

```python
class BIT:
    def __init__(self, size):
        self.n = size
        self.tree = [0] * (size + 1)

    def update(self, i, delta=1):
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)      # move to next responsible node (explained below)

    def query(self, i):
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & (-i)      # move to parent node (explained below)
        return total

# Usage:
# bit = BIT(max_value)
# bit.update(x)          → insert x
# bit.query(x - 1)       → rank(x): count of inserted values < x
```

- Insert: O(log n)
- Query: O(log n)

#### Why `i += i & (-i)` and `i -= i & (-i)`?

**What is `i & (-i)`?**

`-i` in binary is the two's complement of `i`: flip all bits of `i`, then add 1.

`i & (-i)` isolates the **lowest set bit** of `i`.

Examples:

```
i = 6  →  binary 0110  →  -i = 1010  →  6 & -6 = 0010 = 2
i = 4  →  binary 0100  →  -i = 1100  →  4 & -4 = 0100 = 4
i = 5  →  binary 0101  →  -i = 1011  →  5 & -5 = 0001 = 1
i = 12 →  binary 1100  →  -i = 0100  →  12 & -12 = 0100 = 4
```

**What does a BIT node store?**

Each node `tree[i]` is responsible for a range of `i & (-i)` elements ending at index `i`.

```
i=1 (001): responsible for 1 element  → tree[1] = freq[1]
i=2 (010): responsible for 2 elements → tree[2] = freq[1] + freq[2]
i=3 (011): responsible for 1 element  → tree[3] = freq[3]
i=4 (100): responsible for 4 elements → tree[4] = freq[1]+freq[2]+freq[3]+freq[4]
i=5 (101): responsible for 1 element  → tree[5] = freq[5]
i=6 (110): responsible for 2 elements → tree[6] = freq[5]+freq[6]
i=7 (111): responsible for 1 element  → tree[7] = freq[7]
i=8 (1000): responsible for 8 elements → tree[8] = freq[1]..freq[8]
```

**`update`: why `i += i & (-i)`?**

When you insert at index `i`, you need to update all nodes that **include index `i`** in their range.

`i += i & (-i)` jumps to the next node that covers index `i`.

```
Insert at i=3:
  update tree[3]  (covers index 3)
  3 + (3&-3) = 3 + 1 = 4 → update tree[4]  (covers indices 1-4)
  4 + (4&-4) = 4 + 4 = 8 → update tree[8]  (covers indices 1-8)
  8 > n → stop
```

**`query`: why `i -= i & (-i)`?**

When you query prefix sum up to index `i`, you collect non-overlapping ranges that together cover `[1, i]`.

`i -= i & (-i)` peels off the last range and moves to the next.

```
Query up to i=7:
  add tree[7]   covers [7,7]   →  7 - (7&-7) = 7 - 1 = 6
  add tree[6]   covers [5,6]   →  6 - (6&-6) = 6 - 2 = 4
  add tree[4]   covers [1,4]   →  4 - (4&-4) = 4 - 4 = 0
  stop
  total = tree[7] + tree[6] + tree[4] = freq[7] + freq[5..6] + freq[1..4] = freq[1..7] ✓
```

**One-line summary:**

```
i & (-i)   →   lowest set bit of i   →   the "range size" that node i is responsible for
update: go UP   by adding   the lowest set bit
query:  go DOWN by removing the lowest set bit
```

**Method 3 — Frequency array with running prefix (works when range is small)**

When all values fit in a small known range `[0, M]`:

```python
freq = [0] * (M + 1)
prefix = [0] * (M + 2)   # prefix[i] = sum of freq[0..i-1]

def insert(x):
    freq[x] += 1
    # update prefix from x+1 onwards (O(M) in naive form)
    # In practice, recompute lazily or use BIT

def rank(x):
    return prefix[x]   # count of inserted values < x
```

For the majority element problem, the range is `[-n, n]` which is O(n), so a frequency array works but needs O(n) to update naively. That's why the BIT is preferred.

---

### 8c — How Inversions and Rank Queries connect to subarray sums

Here is the complete chain of reasoning for "count subarrays with sum > 0":

```
Step 1: subarray [l, r] has sum > 0
            ↕
        prefix[r+1] - prefix[l] > 0
            ↕
        prefix[l] < prefix[r+1]                ← inequality on a pair

Step 2: for each r+1, count l < r+1 where prefix[l] < prefix[r+1]
            ↕
        rank query on the set of seen prefix sums

Step 3: process left to right
        - before seeing index r+1, insert prefix[r+1] into BIT
        - when at r+1, query rank(prefix[r+1]) = count of stored values < prefix[r+1]
        - add to answer

Step 4: this is equivalent to counting non-inversions
        (pairs where earlier value < later value in the prefix sum array)
```

---

### 8d — Putting it all together: Count Inversions in an array (LeetCode 315 style)

**Problem:** Given `nums`, for each index `i`, count how many `j > i` have `nums[j] < nums[i]`.

This is directly "count inversions per element".

```python
def count_smaller(nums):
    """
    Returns list where result[i] = count of nums[j] < nums[i] for all j > i.
    Uses BIT with coordinate compression.
    """
    # Coordinate compress: map actual values to ranks 1..n
    sorted_unique = sorted(set(nums))
    rank_map = {v: i + 1 for i, v in enumerate(sorted_unique)}
    m = len(sorted_unique)

    bit = BIT(m)
    result = []

    for x in reversed(nums):       # process right to left
        r = rank_map[x]
        # count of elements already seen (to the right) that are < x
        result.append(bit.query(r - 1))
        bit.update(r)

    return result[::-1]
```

**Trace for `nums = [5, 2, 6, 1]`:**

```
Process right to left:
  x=1, rank=1: query(0)=0, insert rank 1. result=[0]
  x=6, rank=4: query(3)=1 (the 1), insert rank 4. result=[0,1]
  x=2, rank=2: query(1)=1 (the 1), insert rank 2. result=[0,1,1]
  x=5, rank=3: query(2)=2 (the 1 and 2), insert rank 3. result=[0,1,1,2]

Reverse: [2, 1, 1, 0]
```

Meaning: 5 has 2 smaller to its right (2, 1), 2 has 1 (just 1), 6 has 1 (just 1), 1 has 0. Correct.

---

### 8e — Problem → Pattern mapping (extended)

| Problem | Key observation | Technique |
|---|---|---|
| Count inversions in array | pairs (i<j) where A[i]>A[j] | Merge sort or BIT |
| Count subarrays with sum > 0 | pairs (i<j) where P[i]<P[j] | BIT rank query |
| Count smaller to the right | for each i, count j>i with A[j]<A[i] | BIT right to left |
| Count range sum queries | multiple sum = k queries offline | prefix sum + hash map |
| Majority element subarrays | +1/-1 recode → sum > 0 | BIT rank query |
| Longest subarray with sum ≤ k | sliding window or deque | monotonic deque |

---

## Part 9 — Summary Cheat Sheet

```
PROBLEM SIGNAL          TRANSFORM                   ALGORITHM
─────────────────────────────────────────────────────────────────
sum = k                 none                        freq map: freq[curr - k]
sum = 0                 none                        freq map: freq[curr]
sum % k = 0             none                        freq map: freq[curr % k]
equal 0s and 1s         0 → -1                      sum = 0 above
majority element        target→+1, others→-1        sum > 0: incremental or BIT
A appears > B           A→+1, B→-1                  sum > 0: incremental or BIT
─────────────────────────────────────────────────────────────────
```

**Time complexities:**

| Pattern | Naive | Optimised |
|---|---|---|
| sum = k, sum = 0, sum % k = 0 | — | **O(n)** with freq map |
| sum > 0, sum < 0 (curr jumps freely) | O(n²) | **O(n log n)** with BIT |
| sum > 0, sum < 0 (curr moves ±1 only) | O(n²) | **O(n)** with incremental presum |

**In an interview, say:**
> "I recode elements so the condition becomes a subarray sum condition. Then prefix sums turn it into counting pairs of prefix values. For equality I use a hash map — O(n). For inequality, if the prefix sum only moves ±1 per step I maintain the count incrementally — O(n). For the general case I use a BIT — O(n log n)."

---

## Part 10 — Binary Indexed Tree (BIT) Deep Dive

### What problem does a BIT solve?

You have an array of frequencies. You need to repeatedly:
1. **Update** — increment a position
2. **Query** — get the sum of a prefix (positions 1 to i)

Naive array: update O(1), query O(n) → total O(n²) for n operations.  
BIT: update O(log n), query O(log n) → total O(n log n).

That's literally the only reason BIT exists. It's a frequency array with fast prefix sums.

---

### The internal structure

A BIT stores partial sums, not individual frequencies. Each node `tree[i]` is responsible for a range ending at `i` of length `i & (-i)`.

```
Index:   1    2    3    4    5    6    7    8
Binary: 001  010  011  100  101  110  111  1000
i&-i:    1    2    1    4    1    2    1    8

tree[1] = freq[1]
tree[2] = freq[1] + freq[2]
tree[3] = freq[3]
tree[4] = freq[1] + freq[2] + freq[3] + freq[4]
tree[5] = freq[5]
tree[6] = freq[5] + freq[6]
tree[7] = freq[7]
tree[8] = freq[1] + ... + freq[8]
```

Visual:
```
tree[8] ────────────────────────────── covers [1..8]
tree[4] ──────────                     covers [1..4]
tree[6]         ────                   covers [5..6]
tree[2]   ──                           covers [1..2]
tree[1] ─                              covers [1]
tree[3]     ─                          covers [3]
tree[5]         ─                      covers [5]
tree[7]             ─                  covers [7]
```

---

### Complete BIT implementation

```python
class BIT:
    """
    Binary Indexed Tree (Fenwick Tree).
    1-indexed. Supports point update and prefix sum query in O(log n).
    """

    def __init__(self, size):
        self.n = size
        self.tree = [0] * (size + 1)   # index 0 unused

    def update(self, i, delta=1):
        """Add delta at position i."""
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)              # jump to next responsible node

    def query(self, i):
        """Return sum of positions 1 to i."""
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & (-i)              # jump to previous independent range
        return total

    def range_query(self, l, r):
        """Return sum of positions l to r."""
        return self.query(r) - self.query(l - 1)
```

---

### Walkthrough — update(6) on empty BIT of size 8

```
i = 6  (binary 110)
  tree[6] += 1    →  6 + (6&-6) = 6 + 2 = 8
  tree[8] += 1    →  8 + (8&-8) = 8 + 8 = 16 > n → stop

Updated: tree[6] and tree[8]
```

### Walkthrough — query(7)

```
i = 7  (binary 111)
  add tree[7]     →  7 - (7&-7) = 7 - 1 = 6
  add tree[6]     →  6 - (6&-6) = 6 - 2 = 4
  add tree[4]     →  4 - (4&-4) = 4 - 4 = 0 → stop

total = tree[7] + tree[6] + tree[4]
      = freq[7]  + freq[5..6] + freq[1..4]
      = freq[1..7]  ✓
```

---

### Problems where BIT is the right tool

#### Category 1 — Count of elements satisfying a range condition (dynamic)

Elements arrive one by one. For each new element, count how many previous elements fall in a range.

| Problem | Query |
|---|---|
| Count inversions | how many previous elements > current |
| Count smaller to the right | how many previous elements < current |
| Count subarrays with sum > 0 | how many previous prefix sums < current |
| Count pairs (i,j) where A[i] > A[j] | same as inversions |

Template:
```python
bit = BIT(max_value)
for x in elements:
    result += bit.query(x - 1)    # count of previous elements < x
    bit.update(x)
```

#### Category 2 — Dynamic prefix sum with point updates

Array values change over time and you need prefix sums after each change.

| Problem | Operation |
|---|---|
| Range sum queries with updates | update single index, query prefix |
| Frequency rank of a stream | insert number, query rank |
| Count of elements in range [l, r] | range_query(l, r) |

Template:
```python
bit = BIT(n)
bit.update(i, value)              # set/update position i
bit.range_query(l, r)             # sum from l to r
```

#### Category 3 — 2D BIT (advanced)

For 2D grids: update a cell, query sum of a rectangle.

---

### When NOT to use BIT

| Situation | Use instead |
|---|---|
| Condition is equality (sum = k) | Hash map — O(n), simpler |
| Prefix sum moves ±1 only | Incremental — O(n), simpler |
| Need minimum/maximum in range | Segment tree |
| Offline queries, no updates | Merge sort or sorting + binary search |
| Values are too large to use as indices | Coordinate compress first, then BIT |

---

### Coordinate Compression (needed when values are large)

BIT needs values to be indices in range `[1, n]`. If values can be up to 10⁹, compress them first.

```python
def compress(arr):
    """Map values to ranks 1..len(unique values)."""
    sorted_unique = sorted(set(arr))
    rank = {v: i + 1 for i, v in enumerate(sorted_unique)}
    return [rank[x] for x in arr], len(sorted_unique)

# Example:
arr = [50, 10, 30, 10, 50]
compressed, m = compress(arr)
# compressed = [3, 1, 2, 1, 3]
# m = 3  (BIT size)
```

---

### Full worked example — Count Inversions (LeetCode 315)

**Problem:** For each index `i`, count how many `j > i` have `nums[j] < nums[i]`.

```python
def count_smaller(nums):
    # Step 1: coordinate compress
    sorted_unique = sorted(set(nums))
    rank = {v: i + 1 for i, v in enumerate(sorted_unique)}
    m = len(sorted_unique)

    bit = BIT(m)
    result = []

    # Step 2: process right to left
    # for each element, count already-seen (right side) elements smaller than it
    for x in reversed(nums):
        r = rank[x]
        result.append(bit.query(r - 1))   # count of inserted values < x
        bit.update(r)

    return result[::-1]


# Trace for [5, 2, 6, 1]:
# Process right to left: 1, 6, 2, 5
#   x=1, rank=1: query(0)=0, insert 1  → result=[0]
#   x=6, rank=4: query(3)=1,  insert 4  → result=[0,1]
#   x=2, rank=2: query(1)=1,  insert 2  → result=[0,1,1]
#   x=5, rank=3: query(2)=2,  insert 3  → result=[0,1,1,2]
# Reversed: [2, 1, 1, 0]
# Meaning: 5 has 2 smaller to its right, 2 has 1, 6 has 1, 1 has 0
```

---

### BIT vs Segment Tree — when to choose which

| Feature | BIT | Segment Tree |
|---|---|---|
| Code complexity | ~10 lines | ~30 lines |
| Prefix sum query | ✓ | ✓ |
| Range min / max query | ✗ | ✓ |
| Range update + query | needs extra BIT | ✓ |
| Constant factor | smaller | larger |
| **Use when** | point update + prefix sum | range update or min/max |

---

## Part 11 — LeetCode Problems by Pattern (with solutions)

---

### Group 1 — Hash Map (sum = k) — O(n)

---

#### LC 560 — Subarray Sum Equals K

**Problem:** Count subarrays with sum exactly equal to `k`.

**Brute force O(n²):**
```python
def subarraySum_brute(nums, k):
    count = 0
    for i in range(len(nums)):
        total = 0
        for j in range(i, len(nums)):
            total += nums[j]
            if total == k:
                count += 1
    return count
```

**Optimised O(n):**
```python
from collections import defaultdict

def subarraySum(nums, k):
    freq = defaultdict(int)
    freq[0] = 1      # empty prefix
    curr = 0
    result = 0
    for x in nums:
        curr += x
        result += freq[curr - k]   # subarrays ending here with sum k
        freq[curr] += 1
    return result
```

**Trace for `nums=[1,2,3]`, `k=3`:**
```
curr=1: look for -2 → 0. freq={0:1,1:1}
curr=3: look for  0 → 1. freq={0:1,1:1,3:1}  result=1  ([1,2])
curr=6: look for  3 → 1. freq={0:1,1:1,3:1,6:1} result=2  ([3])
```
Answer = **2** (subarrays `[1,2]` and `[3]`).

---

#### LC 974 — Subarray Sums Divisible by K

**Problem:** Count subarrays whose sum is divisible by `k`.

**Key insight:** `(prefix[r] - prefix[l]) % k == 0` → `prefix[r] % k == prefix[l] % k`.

```python
from collections import defaultdict

def subarraysDivByK(nums, k):
    freq = defaultdict(int)
    freq[0] = 1
    curr = 0
    result = 0
    for x in nums:
        curr = (curr + x) % k
        if curr < 0:
            curr += k          # Python handles negative mod, but be safe
        result += freq[curr]
        freq[curr] += 1
    return result
```

---

#### LC 525 — Contiguous Array

**Problem:** Find the max length subarray with equal number of 0s and 1s.

**Recode:** 0 → -1. Now find longest subarray with sum = 0.  
Store the **first index** where each prefix sum appeared (not count).

```python
def findMaxLength(nums):
    first_seen = {0: -1}   # prefix sum 0 seen before index 0
    curr = 0
    result = 0
    for i, x in enumerate(nums):
        curr += 1 if x == 1 else -1
        if curr in first_seen:
            result = max(result, i - first_seen[curr])
        else:
            first_seen[curr] = i
    return result
```

---

#### LC 1248 — Count Number of Nice Subarrays

**Problem:** Count subarrays with exactly `k` odd numbers.

**Recode:** odd → 1, even → 0. Now find subarrays with sum = `k`. Identical to LC 560.

```python
from collections import defaultdict

def numberOfSubarrays(nums, k):
    freq = defaultdict(int)
    freq[0] = 1
    curr = 0
    result = 0
    for x in nums:
        curr += x % 2          # 1 if odd, 0 if even
        result += freq[curr - k]
        freq[curr] += 1
    return result
```

---

#### LC 523 — Continuous Subarray Sum

**Problem:** Return true if there is a subarray of length ≥ 2 with sum divisible by `k`.

```python
def checkSubarraySum(nums, k):
    first_seen = {0: -1}   # store first index of each remainder
    curr = 0
    for i, x in enumerate(nums):
        curr = (curr + x) % k
        if curr in first_seen:
            if i - first_seen[curr] >= 2:   # length ≥ 2
                return True
        else:
            first_seen[curr] = i
    return False
```

---

### Group 2 — BIT / Incremental (sum > 0 or inequality) — O(n log n) or O(n)

---

#### LC 315 — Count of Smaller Numbers After Self

**Problem:** For each index `i`, count how many `nums[j] < nums[i]` where `j > i`.

**Approach:** Process right to left. For each element, query BIT for count of already-seen values smaller than it.

```python
def countSmaller(nums):
    # coordinate compress
    sorted_unique = sorted(set(nums))
    rank = {v: i + 1 for i, v in enumerate(sorted_unique)}
    m = len(sorted_unique)

    tree = [0] * (m + 1)

    def update(i):
        while i <= m:
            tree[i] += 1
            i += i & (-i)

    def query(i):
        total = 0
        while i > 0:
            total += tree[i]
            i -= i & (-i)
        return total

    result = []
    for x in reversed(nums):
        r = rank[x]
        result.append(query(r - 1))   # count of seen values < x
        update(r)

    return result[::-1]
```

**Trace for `[5,2,6,1]`:**
```
Process right to left:
  1 → query(0)=0, insert rank 1   result=[0]
  6 → query(3)=1, insert rank 4   result=[0,1]
  2 → query(1)=1, insert rank 2   result=[0,1,1]
  5 → query(2)=2, insert rank 3   result=[0,1,1,2]
Reversed: [2,1,1,0]
```

---

#### LC 493 — Reverse Pairs

**Problem:** Count pairs `(i,j)` where `i < j` and `nums[i] > 2 * nums[j]`.

**Key difference from LC 315:** condition is `nums[i] > 2 * nums[j]`, not just `nums[i] > nums[j]`. So query and update happen at different values — query for `> 2*x` before inserting `x`.

```python
def reversePairs(nums):
    sorted_unique = sorted(set(nums) | set(2 * x for x in nums))
    rank = {v: i + 1 for i, v in enumerate(sorted_unique)}
    m = len(sorted_unique)

    tree = [0] * (m + 1)

    def update(i):
        while i <= m:
            tree[i] += 1
            i += i & (-i)

    def query(i):      # count of values ≤ i
        total = 0
        while i > 0:
            total += tree[i]
            i -= i & (-i)
        return total

    result = 0
    total_inserted = 0
    for x in nums:
        # count of already-inserted values > 2*x
        result += total_inserted - query(rank[2 * x])
        update(rank[x])
        total_inserted += 1

    return result
```

---

#### LC 327 — Count of Range Sum

**Problem:** Count subarrays where the sum is in `[lower, upper]`.

**Approach:** For each prefix sum `curr`, count stored prefix sums in `[curr - upper, curr - lower]`. That's a BIT range query.

```python
def countRangeSum(nums, lower, upper):
    prefix = [0]
    for x in nums:
        prefix.append(prefix[-1] + x)

    # coordinate compress
    sorted_unique = sorted(set(prefix))
    rank = {v: i + 1 for i, v in enumerate(sorted_unique)}
    m = len(sorted_unique)

    tree = [0] * (m + 1)

    def update(i):
        while i <= m:
            tree[i] += 1
            i += i & (-i)

    def query(i):
        total = 0
        while i > 0:
            total += tree[i]
            i -= i & (-i)
        return total

    def rank_of(v):
        # largest rank with value ≤ v (bisect_right style)
        import bisect
        idx = bisect.bisect_right(sorted_unique, v)
        return idx   # 0 means nothing ≤ v exists

    result = 0
    for curr in prefix:
        # count stored values in [curr - upper, curr - lower]
        result += rank_of(curr - lower) - rank_of(curr - upper - 1)
        update(rank[curr])

    return result
```

---

#### LC 3739 — Count Subarrays With Majority Element II

**Problem:** Count subarrays where `target` appears strictly more than half the time.

All three approaches side by side:

```python
# Brute force — O(n²)
def countMajority_brute(nums, target):
    n = len(nums)
    result = 0
    for i in range(n):
        total = 0
        for j in range(i, n):
            total += 1 if nums[j] == target else -1
            if total > 0:
                result += 1
    return result


# BIT — O(n log n)
def countMajority_bit(nums, target):
    n = len(nums)
    tree = [0] * (2 * n + 2)
    offset = n + 1

    def update(i):
        while i < len(tree):
            tree[i] += 1
            i += i & (-i)

    def query(i):
        total = 0
        while i > 0:
            total += tree[i]
            i -= i & (-i)
        return total

    update(offset)
    curr = 0
    result = 0
    for x in nums:
        curr += 1 if x == target else -1
        result += query(curr + offset - 1)
        update(curr + offset)
    return result


# Incremental — O(n)  ← best for this problem
def countMajority_on(nums, target):
    n = len(nums)
    freq = [0] * (2 * n + 1)
    freq[n] = 1          # prefix sum 0 at offset n
    cnt = n
    presum = 0
    result = 0
    for x in nums:
        if x == target:
            presum += freq[cnt]
            cnt += 1
        else:
            cnt -= 1
            presum -= freq[cnt]
        freq[cnt] += 1
        result += presum
    return result
```

---

### Group 3 — BIT for Range Queries (not subarray sum)

---

#### LC 307 — Range Sum Query — Mutable

**Problem:** Given array, support `update(i, val)` and `sumRange(l, r)`.

```python
class NumArray:
    def __init__(self, nums):
        self.n = len(nums)
        self.tree = [0] * (self.n + 1)
        self.nums = [0] * self.n
        for i, v in enumerate(nums):
            self.update(i, v)

    def update(self, i, val):
        delta = val - self.nums[i]
        self.nums[i] = val
        i += 1                         # BIT is 1-indexed
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)

    def sumRange(self, l, r):
        def query(i):
            total = 0
            while i > 0:
                total += self.tree[i]
                i -= i & (-i)
            return total
        return query(r + 1) - query(l)
```

---

### Summary — which problem uses which pattern

| LC # | Problem | Pattern | Time |
|---|---|---|---|
| 560 | Subarray Sum Equals K | hash map: `freq[curr-k]` | O(n) |
| 974 | Subarray Sums Divisible by K | hash map: `freq[curr%k]` | O(n) |
| 525 | Contiguous Array | recode 0→-1, hash map for sum=0 | O(n) |
| 1248 | Count Nice Subarrays | recode odd→1, hash map for sum=k | O(n) |
| 523 | Continuous Subarray Sum | hash map: first index of `curr%k` | O(n) |
| 315 | Count Smaller After Self | BIT + coordinate compress | O(n log n) |
| 493 | Reverse Pairs | BIT + coordinate compress | O(n log n) |
| 327 | Count of Range Sum | BIT + coordinate compress | O(n log n) |
| 307 | Range Sum Query Mutable | BIT point update + prefix query | O(n log n) |
| 3739 | Majority Element Subarrays | incremental presum (±1 steps) | O(n) |

---

## Part 12 — Practice Problems (ordered by concept)

Work through these in order. Each group builds on the previous.

---

### Level 1 — Prefix Sum + Hash Map (master this first)

| # | Problem | Key idea | Link |
|---|---------|----------|------|
| 1 | LC 560 — Subarray Sum Equals K | `freq[curr - k]` | https://leetcode.com/problems/subarray-sum-equals-k |
| 2 | LC 974 — Subarray Sums Divisible by K | `freq[curr % k]` | https://leetcode.com/problems/subarray-sums-divisible-by-k |
| 3 | LC 525 — Contiguous Array | recode 0→-1, find sum=0 | https://leetcode.com/problems/contiguous-array |
| 4 | LC 1248 — Count Number of Nice Subarrays | recode odd→1, find sum=k | https://leetcode.com/problems/count-number-of-nice-subarrays |
| 5 | LC 523 — Continuous Subarray Sum | store first index of `curr%k` | https://leetcode.com/problems/continuous-subarray-sum |
| 6 | LC 325 — Maximum Size Subarray Sum Equals K | store first index of `curr-k` | https://leetcode.com/problems/maximum-size-subarray-sum-equals-k |

**Checkpoint:** Can you do LC 560 without looking at notes? If yes, move to Level 2.

---

### Level 2 — +1/-1 Recode (condition → sum)

| # | Problem | Recode | Sum condition |
|---|---------|--------|---------------|
| 7 | LC 525 — Contiguous Array | 0→-1 | sum = 0 |
| 8 | LC 1371 — Find the Longest Subarray with 0s and 1s | vowel→1, consonant→-1 | sum = 0 |
| 9 | LC 2155 — All Divisions With the Highest Score | recode by count | prefix compare |
| 10 | LC 3739 — Majority Element Subarrays | target→+1, others→-1 | sum > 0 |

**Checkpoint:** Given any problem with "count of X vs count of Y", can you immediately say what to recode and what sum condition to use?

---

### Level 3 — BIT (inequality condition)

| # | Problem | Query type | Direction |
|---|---------|-----------|-----------|
| 11 | LC 315 — Count of Smaller Numbers After Self | count < x | right to left |
| 12 | LC 493 — Reverse Pairs | count > 2x | right to left |
| 13 | LC 327 — Count of Range Sum | count in range [lo, hi] | left to right |
| 14 | LC 307 — Range Sum Query Mutable | prefix sum with updates | left to right |

**Checkpoint:** Can you write the BIT class from memory in under 2 minutes?

---

### Level 4 — Incremental presum (curr moves ±1)

| # | Problem | Why incremental works |
|---|---------|----------------------|
| 15 | LC 3739 — Majority Element Subarrays | +1/-1 recode → curr moves ±1 |
| 16 | LC 2488 — Count Subarrays With Median | median condition → +1/-1 recode |
| 17 | LC 169 — Majority Element (single) | Boyer-Moore = same ±1 idea |

**Checkpoint:** Can you explain in one sentence why curr moving ±1 allows O(n) instead of O(n log n)?

---

### Level 5 — Mixed / Hard

| # | Problem | Concepts combined |
|---|---------|------------------|
| 18 | LC 862 — Shortest Subarray with Sum at Least K | prefix sum + monotonic deque |
| 19 | LC 1074 — Number of Submatrices That Sum to Target | 2D prefix sum + hash map |
| 20 | LC 2302 — Count Subarrays With Score Less Than K | sliding window + prefix sum |
| 21 | LC 2092 — Find All People With Secret | union find + sorting |

---

### How to practice each problem

For every problem above, do it in this order:

```
Step 1 — Read the problem. Ask yourself:
  - Does it say "count subarrays"?
  - Can I express the condition as a SUM condition?
  - What do I recode each element to?

Step 2 — Write brute force first (nested loop).
  Verify it gives correct answers on the examples.

Step 3 — Identify which pattern applies:
  - sum = k       → hash map
  - sum = 0       → hash map
  - sum % k = 0   → hash map with modulo
  - sum > 0       → incremental (if ±1) or BIT (if any jump)
  - count < x     → BIT right to left

Step 4 — Write optimised solution.
  Test against your brute force on 3-4 small examples.

Step 5 — Ask: what is time complexity and why?
```

---

### Quick self-test questions

1. What is `freq[0] = 1` for in LC 560?
2. Why does query go right-to-left in LC 315 but left-to-right in LC 327?
3. When does `presum += freq[cnt]` happen BEFORE `cnt += 1` vs after?
4. Why can't you use a hash map for LC 315?
5. What is `i & (-i)` in BIT? What does it represent?
6. Why do we need coordinate compression in LC 315 but not in LC 560?
7. In the incremental approach, what does `presum` represent at each step?
8. If curr can jump by 5 in one step, can you still use incremental? Why not?

**Answers are all in this file. Go back and re-read the relevant section if stuck.**

---
