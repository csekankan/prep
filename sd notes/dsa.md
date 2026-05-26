# DSA Patterns — Complete Reference Guide

A comprehensive guide to all major Data Structures & Algorithms patterns needed for technical interviews and competitive programming.

---

## Table of Contents

1. [Arrays & Strings](#1-arrays--strings)
2. [Two Pointers](#2-two-pointers)
3. [Sliding Window](#3-sliding-window)
4. [Binary Search](#4-binary-search)
5. [Prefix Sum](#5-prefix-sum)
6. [Hashing](#6-hashing)
7. [Stack](#7-stack)
8. [Queue & Deque](#8-queue--deque)
9. [Linked List](#9-linked-list)
10. [Trees](#10-trees)
11. [Tries](#11-tries)
12. [Heaps / Priority Queue](#12-heaps--priority-queue)
13. [Graphs](#13-graphs)
14. [Backtracking](#14-backtracking)
15. [Dynamic Programming](#15-dynamic-programming)
16. [Greedy](#16-greedy)
17. [Intervals](#17-intervals)
18. [Math & Bit Manipulation](#18-math--bit-manipulation)
19. [Sorting](#19-sorting)
20. [Union Find (Disjoint Set)](#20-union-find-disjoint-set)
21. [Monotonic Stack / Queue](#21-monotonic-stack--queue)
22. [Segment Tree & BIT](#22-segment-tree--bit)

---

## 1. Arrays & Strings

### Pattern: In-place Modification
Modify an array without using extra space by overwriting elements.

```
Use when: removing duplicates, moving zeros, filtering in-place
Key idea: maintain a "write pointer" separate from the "read pointer"
```

**Template:**
```python
write = 0
for read in range(len(nums)):
    if condition(nums[read]):
        nums[write] = nums[read]
        write += 1
return write
```

**Problems:** Remove Duplicates from Sorted Array, Move Zeroes, Remove Element

---

### Pattern: Kadane's Algorithm (Maximum Subarray)
Track the maximum sum ending at the current position.

```
Use when: maximum/minimum subarray sum
Key idea: max_ending_here = max(num, max_ending_here + num)
```

**Template:**
```python
max_sum = curr_sum = nums[0]
for num in nums[1:]:
    curr_sum = max(num, curr_sum + num)
    max_sum = max(max_sum, curr_sum)
return max_sum
```

**Problems:** Maximum Subarray, Maximum Product Subarray

---

### Pattern: Cyclic Sort
Place each number at its correct index (works when numbers are 1 to N).

```
Use when: array contains numbers in range [1, N] or [0, N-1]
Key idea: swap nums[i] to its correct position until correct
```

**Template:**
```python
i = 0
while i < len(nums):
    correct = nums[i] - 1
    if nums[i] != nums[correct]:
        nums[i], nums[correct] = nums[correct], nums[i]
    else:
        i += 1
```

**Problems:** Find Missing Number, Find All Duplicates, First Missing Positive

---

## 2. Two Pointers

### Pattern: Opposite Direction Pointers
Start one pointer at the beginning and one at the end, move toward each other.

```
Use when: sorted array, pair/triplet problems, palindrome check
Key idea: shrink the search space from both ends
```

**Template:**
```python
left, right = 0, len(arr) - 1
while left < right:
    if condition_met(arr[left], arr[right]):
        # process answer
        left += 1
        right -= 1
    elif need_larger:
        left += 1
    else:
        right -= 1
```

**Problems:** Two Sum II, 3Sum, Container With Most Water, Valid Palindrome, Trapping Rain Water

---

### Pattern: Same Direction (Fast & Slow)
Two pointers moving in the same direction at different speeds.

```
Use when: cycle detection, finding middle of list, nth from end
Key idea: slow moves 1 step, fast moves 2 steps
```

**Template:**
```python
slow = fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
    if slow == fast:  # cycle detected
        break
```

**Problems:** Linked List Cycle, Find Middle, Happy Number, Palindrome Linked List

---

## 3. Sliding Window

### Pattern: Fixed Size Window
Maintain a window of exactly K elements.

```
Use when: subarray/substring of fixed length K
Key idea: add new element, remove oldest element, track window state
```

**Template:**
```python
window_sum = sum(nums[:k])
max_sum = window_sum
for i in range(k, len(nums)):
    window_sum += nums[i] - nums[i - k]
    max_sum = max(max_sum, window_sum)
return max_sum
```

**Problems:** Maximum Average Subarray, Sliding Window Maximum

---

### Pattern: Variable Size Window (Shrinkable)
Expand window to the right, shrink from the left when a condition is violated.

```
Use when: longest/shortest subarray/substring satisfying a condition
Key idea: grow right pointer, shrink left pointer when invalid
```

**Template:**
```python
left = 0
result = 0
window_state = {}  # or counter, sum, etc.

for right in range(len(s)):
    # add s[right] to window
    window_state[s[right]] = window_state.get(s[right], 0) + 1

    while window_is_invalid(window_state):
        # remove s[left] from window
        window_state[s[left]] -= 1
        left += 1

    result = max(result, right - left + 1)

return result
```

**Problems:** Longest Substring Without Repeating, Minimum Window Substring, Longest Repeating Character Replacement, Fruit Into Baskets

---

## 4. Binary Search

### Pattern: Standard Binary Search
Search in a sorted array.

```
Use when: sorted data, O(log n) required
Key idea: eliminate half the search space each iteration
```

**Template:**
```python
left, right = 0, len(nums) - 1
while left <= right:
    mid = left + (right - left) // 2
    if nums[mid] == target:
        return mid
    elif nums[mid] < target:
        left = mid + 1
    else:
        right = mid - 1
return -1
```

---

### Pattern: Binary Search on Answer
Binary search on the answer space rather than the array.

```
Use when: "find minimum/maximum X such that condition holds"
Key idea: the answer space is monotonic — valid/invalid has a boundary
```

**Template:**
```python
def feasible(mid):
    # check if mid is a valid answer
    return True / False

left, right = min_possible, max_possible
while left < right:
    mid = left + (right - left) // 2
    if feasible(mid):
        right = mid       # look for smaller valid answer
    else:
        left = mid + 1    # mid too small, increase
return left
```

**Problems:** Koko Eating Bananas, Capacity To Ship Packages, Split Array Largest Sum, Minimum Days to Make Bouquets

---

### Pattern: Binary Search in Rotated Array
Find the inflection point, then determine which half is sorted.

```
Use when: rotated sorted array problems
Key idea: one half is always sorted — figure out which one
```

**Template:**
```python
left, right = 0, len(nums) - 1
while left <= right:
    mid = left + (right - left) // 2
    if nums[mid] == target:
        return mid
    if nums[left] <= nums[mid]:  # left half sorted
        if nums[left] <= target < nums[mid]:
            right = mid - 1
        else:
            left = mid + 1
    else:                        # right half sorted
        if nums[mid] < target <= nums[right]:
            left = mid + 1
        else:
            right = mid - 1
return -1
```

**Problems:** Search in Rotated Sorted Array, Find Minimum in Rotated Sorted Array

---

## 5. Prefix Sum

### Pattern: Prefix Sum Array
Precompute cumulative sums to answer range queries in O(1).

```
Use when: multiple range sum queries, subarray sum equals K
Key idea: sum(i, j) = prefix[j+1] - prefix[i]
```

**Template:**
```python
prefix = [0] * (len(nums) + 1)
for i, num in enumerate(nums):
    prefix[i + 1] = prefix[i] + num

# range sum [l, r]
range_sum = prefix[r + 1] - prefix[l]
```

---

### Pattern: Prefix Sum + HashMap (Subarray Sum = K)
Track seen prefix sums to find subarrays with a target sum.

```
Use when: count subarrays with exact sum K
Key idea: if prefix[j] - prefix[i] == k, then subarray [i,j] sums to k
```

**Template:**
```python
count = 0
prefix_sum = 0
seen = {0: 1}  # sum -> frequency

for num in nums:
    prefix_sum += num
    count += seen.get(prefix_sum - k, 0)
    seen[prefix_sum] = seen.get(prefix_sum, 0) + 1

return count
```

**Problems:** Subarray Sum Equals K, Continuous Subarray Sum, Path Sum III

---

## 6. Hashing

### Pattern: Frequency Count
Use a hash map to count occurrences.

```
Use when: anagrams, duplicates, majority element, most frequent
Key idea: Counter or defaultdict to track frequencies
```

**Template:**
```python
from collections import Counter
freq = Counter(nums)
# or
freq = {}
for x in nums:
    freq[x] = freq.get(x, 0) + 1
```

**Problems:** Valid Anagram, Group Anagrams, Top K Frequent Elements, First Unique Character

---

### Pattern: Two Sum / Complement Lookup
Store visited elements and check for complements.

```
Use when: pair that sums to target
Key idea: for each x, check if (target - x) already seen
```

**Template:**
```python
seen = {}
for i, num in enumerate(nums):
    complement = target - num
    if complement in seen:
        return [seen[complement], i]
    seen[num] = i
```

**Problems:** Two Sum, Four Sum II, Pairs with Given Difference

---

## 7. Stack

### Pattern: Balanced Parentheses / Matching
Use a stack to match opening and closing brackets.

```
Use when: valid parentheses, matching tags, nested structures
Key idea: push on open, pop and verify on close
```

**Template:**
```python
stack = []
mapping = {')': '(', '}': '{', ']': '['}
for char in s:
    if char in mapping:
        top = stack.pop() if stack else '#'
        if mapping[char] != top:
            return False
    else:
        stack.push(char)
return not stack
```

**Problems:** Valid Parentheses, Minimum Remove to Make Valid, Longest Valid Parentheses

---

### Pattern: Next Greater / Smaller Element
Use a stack to find the next greater or smaller element for each index.

```
Use when: next greater element, daily temperatures, stock span
Key idea: pop when current element resolves the "pending" stack elements
```

**Template:**
```python
result = [-1] * len(nums)
stack = []  # stores indices

for i, num in enumerate(nums):
    while stack and nums[stack[-1]] < num:  # found next greater
        idx = stack.pop()
        result[idx] = num
    stack.append(i)

return result
```

**Problems:** Next Greater Element, Daily Temperatures, Largest Rectangle in Histogram

---

## 8. Queue & Deque

### Pattern: BFS Level Order
Process nodes level by level using a queue.

```
Use when: shortest path in unweighted graph, level-order traversal
Key idea: enqueue neighbors, process level by level
```

**Template:**
```python
from collections import deque
queue = deque([start])
visited = {start}
level = 0

while queue:
    for _ in range(len(queue)):  # process entire level
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    level += 1
```

---

### Pattern: Sliding Window Maximum (Monotonic Deque)
Maintain a deque of useful indices in decreasing order of values.

```
Use when: maximum/minimum in a sliding window
Key idea: deque front = current window max, pop back if smaller than current
```

**Template:**
```python
from collections import deque
dq = deque()  # stores indices
result = []

for i, num in enumerate(nums):
    while dq and dq[0] < i - k + 1:  # out of window
        dq.popleft()
    while dq and nums[dq[-1]] < num:  # smaller, useless
        dq.pop()
    dq.append(i)
    if i >= k - 1:
        result.append(nums[dq[0]])

return result
```

**Problems:** Sliding Window Maximum, Jump Game VI

---

## 9. Linked List

### Pattern: Dummy Head Node
Use a dummy node to simplify edge cases (empty list, head removal).

```
Use when: merging lists, removing nodes, complex pointer manipulation
Key idea: dummy.next = head avoids special-casing head deletion
```

**Template:**
```python
dummy = ListNode(0)
dummy.next = head
curr = dummy

# ... manipulate list ...

return dummy.next
```

**Problems:** Merge Two Sorted Lists, Remove Nth From End, Reverse Linked List II

---

### Pattern: Reverse a Linked List
Iteratively reverse pointers.

```
Use when: reverse entire list or a portion
Key idea: prev, curr, next — redirect curr.next to prev
```

**Template:**
```python
prev = None
curr = head
while curr:
    next_node = curr.next
    curr.next = prev
    prev = curr
    curr = next_node
return prev
```

**Problems:** Reverse Linked List, Reverse Nodes in k-Group, Palindrome Linked List

---

## 10. Trees

### Pattern: DFS — Recursive Tree Traversal
Traverse a tree using recursion (pre/in/post order).

```
Use when: path problems, subtree comparisons, tree height/depth
Key idea: base case = null node, combine left + right results
```

**Template:**
```python
def dfs(node):
    if not node:
        return base_value

    left = dfs(node.left)
    right = dfs(node.right)

    return combine(left, right, node.val)
```

**Problems:** Max Depth, Diameter of Tree, Same Tree, Invert Binary Tree, Path Sum

---

### Pattern: Path Sum (Root to Leaf)
Track path sum from root to every leaf.

```
Use when: root-to-leaf path problems
Key idea: pass running sum down, check at leaves
```

**Template:**
```python
def hasPathSum(node, remaining):
    if not node:
        return False
    remaining -= node.val
    if not node.left and not node.right:  # leaf
        return remaining == 0
    return hasPathSum(node.left, remaining) or hasPathSum(node.right, remaining)
```

---

### Pattern: Level Order / BFS on Tree
Process nodes level by level.

```
Use when: level averages, zigzag traversal, right side view
Key idea: use a queue, process all nodes at current level
```

**Template:**
```python
from collections import deque
result = []
if not root:
    return result

queue = deque([root])
while queue:
    level = []
    for _ in range(len(queue)):
        node = queue.popleft()
        level.append(node.val)
        if node.left: queue.append(node.left)
        if node.right: queue.append(node.right)
    result.append(level)

return result
```

---

### Pattern: Lowest Common Ancestor (LCA)
Find the deepest node that is an ancestor of both targets.

```
Use when: LCA in BST or general binary tree
Key idea: if node == p or q, return it; LCA is where left and right both return non-null
```

**Template:**
```python
def lca(node, p, q):
    if not node or node == p or node == q:
        return node
    left = lca(node.left, p, q)
    right = lca(node.right, p, q)
    if left and right:
        return node  # p and q on different sides
    return left or right
```

---

### Pattern: BST Properties
Exploit BST ordering for efficient search/insertion.

```
Use when: validate BST, search, kth smallest, inorder traversal
Key idea: inorder traversal of BST gives sorted order
```

**Template (Validate BST):**
```python
def isValid(node, min_val=float('-inf'), max_val=float('inf')):
    if not node:
        return True
    if not (min_val < node.val < max_val):
        return False
    return isValid(node.left, min_val, node.val) and \
           isValid(node.right, node.val, max_val)
```

---

## 11. Tries

### Pattern: Trie (Prefix Tree)
A tree where each path from root represents a prefix/word.

```
Use when: autocomplete, word search, prefix matching, IP routing
Key idea: each node has children[26] and a flag for end of word
```

**Template:**
```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

    def starts_with(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True
```

**Problems:** Implement Trie, Word Search II, Replace Words, Design Add and Search Words

---

## 12. Heaps / Priority Queue

### Pattern: Top K Elements
Use a min-heap of size K to maintain K largest elements.

```
Use when: top K frequent, K closest, K largest/smallest
Key idea: min-heap of size K — pop when size exceeds K
```

**Template:**
```python
import heapq

heap = []
for num in nums:
    heapq.heappush(heap, num)
    if len(heap) > k:
        heapq.heappop(heap)  # remove smallest

return list(heap)
```

---

### Pattern: K-way Merge
Merge K sorted lists using a min-heap tracking (value, list_index, element_index).

```
Use when: merge K sorted lists/arrays, smallest range covering K lists
Key idea: always extract minimum across all lists, push next element from same list
```

**Template:**
```python
import heapq

heap = []
for i, lst in enumerate(lists):
    if lst:
        heapq.heappush(heap, (lst[0].val, i, lst[0]))

dummy = ListNode(0)
curr = dummy

while heap:
    val, i, node = heapq.heappop(heap)
    curr.next = node
    curr = curr.next
    if node.next:
        heapq.heappush(heap, (node.next.val, i, node.next))

return dummy.next
```

**Problems:** Merge K Sorted Lists, Find K Pairs with Smallest Sums, Kth Smallest in Matrix

---

### Pattern: Two Heaps (Median Finding)
Maintain a max-heap for the lower half and a min-heap for the upper half.

```
Use when: find median from data stream, sliding window median
Key idea: max_heap size == min_heap size (or +1) at all times
```

**Template:**
```python
import heapq

max_heap = []  # lower half (negate for max-heap behavior)
min_heap = []  # upper half

def add_num(num):
    heapq.heappush(max_heap, -num)
    heapq.heappush(min_heap, -heapq.heappop(max_heap))
    if len(min_heap) > len(max_heap):
        heapq.heappush(max_heap, -heapq.heappop(min_heap))

def find_median():
    if len(max_heap) == len(min_heap):
        return (-max_heap[0] + min_heap[0]) / 2.0
    return -max_heap[0]
```

**Problems:** Find Median from Data Stream, Sliding Window Median

---

## 13. Graphs

### Pattern: DFS on Graph
Explore as far as possible before backtracking.

```
Use when: connected components, cycle detection, topological sort, island problems
Key idea: mark visited, explore all neighbors recursively
```

**Template:**
```python
def dfs(node, visited, graph):
    visited.add(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs(neighbor, visited, graph)

visited = set()
for node in graph:
    if node not in visited:
        dfs(node, visited, graph)
```

---

### Pattern: BFS on Graph (Shortest Path)
Find the shortest path in an unweighted graph.

```
Use when: shortest path, minimum steps, word ladder
Key idea: BFS guarantees shortest path in unweighted graphs
```

**Template:**
```python
from collections import deque

def bfs(start, end, graph):
    queue = deque([(start, 0)])
    visited = {start}

    while queue:
        node, dist = queue.popleft()
        if node == end:
            return dist
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    return -1
```

**Problems:** Word Ladder, Shortest Path in Binary Matrix, 01 Matrix, Rotting Oranges

---

### Pattern: Topological Sort (Kahn's Algorithm)
Process nodes with no incoming edges first; detect cycles.

```
Use when: task scheduling, course prerequisites, build order
Key idea: in-degree array + queue, process zero-in-degree nodes
```

**Template:**
```python
from collections import deque

in_degree = [0] * n
graph = [[] for _ in range(n)]

for u, v in prerequisites:
    graph[u].append(v)
    in_degree[v] += 1

queue = deque([i for i in range(n) if in_degree[i] == 0])
order = []

while queue:
    node = queue.popleft()
    order.append(node)
    for neighbor in graph[node]:
        in_degree[neighbor] -= 1
        if in_degree[neighbor] == 0:
            queue.append(neighbor)

return order if len(order) == n else []  # empty = cycle exists
```

**Problems:** Course Schedule I & II, Alien Dictionary, Sequence Reconstruction

---

### Pattern: Dijkstra's Algorithm (Weighted Shortest Path)
Greedy shortest path using a min-heap.

```
Use when: weighted graph, minimum cost path
Key idea: always process the node with smallest current distance
```

**Template:**
```python
import heapq

def dijkstra(graph, start):
    dist = {node: float('inf') for node in graph}
    dist[start] = 0
    heap = [(0, start)]

    while heap:
        cost, node = heapq.heappop(heap)
        if cost > dist[node]:
            continue
        for neighbor, weight in graph[node]:
            new_cost = cost + weight
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                heapq.heappush(heap, (new_cost, neighbor))

    return dist
```

**Problems:** Network Delay Time, Cheapest Flights Within K Stops, Path With Minimum Effort

---

### Pattern: Union Find (see section 20 for details)

### Pattern: Flood Fill / Island DFS
Explore connected regions in a grid.

```
Use when: number of islands, max area island, surrounded regions
Key idea: DFS/BFS from each unvisited cell, mark visited inline
```

**Template:**
```python
def dfs(grid, r, c):
    if r < 0 or r >= len(grid) or c < 0 or c >= len(grid[0]):
        return
    if grid[r][c] != '1':
        return
    grid[r][c] = '#'  # mark visited
    dfs(grid, r+1, c)
    dfs(grid, r-1, c)
    dfs(grid, r, c+1)
    dfs(grid, r, c-1)

count = 0
for r in range(len(grid)):
    for c in range(len(grid[0])):
        if grid[r][c] == '1':
            dfs(grid, r, c)
            count += 1
return count
```

---

## 14. Backtracking

### Pattern: Subsets / Combinations
Generate all subsets or combinations recursively.

```
Use when: all subsets, combinations, combination sum
Key idea: include or exclude each element; start from current index to avoid duplicates
```

**Template:**
```python
def backtrack(start, current, result):
    result.append(list(current))
    for i in range(start, len(nums)):
        current.append(nums[i])
        backtrack(i + 1, current, result)
        current.pop()  # undo choice

result = []
backtrack(0, [], result)
return result
```

**Problems:** Subsets, Subsets II, Combination Sum, Combination Sum II

---

### Pattern: Permutations
Generate all permutations by choosing from remaining elements.

```
Use when: all permutations, next permutation
Key idea: swap element into current position, recurse, swap back
```

**Template:**
```python
def backtrack(start):
    if start == len(nums):
        result.append(list(nums))
        return
    for i in range(start, len(nums)):
        nums[start], nums[i] = nums[i], nums[start]
        backtrack(start + 1)
        nums[start], nums[i] = nums[i], nums[start]  # undo

result = []
backtrack(0)
return result
```

**Problems:** Permutations I & II, Letter Combinations of a Phone Number

---

### Pattern: Constraint Satisfaction (N-Queens style)
Place elements one by one, check constraints, backtrack if violated.

```
Use when: N-Queens, Sudoku Solver, word search in grid
Key idea: validate before placing, undo after backtracking
```

**Template:**
```python
def backtrack(row):
    if row == n:
        result.append(board_state())
        return
    for col in range(n):
        if is_valid(row, col):
            place(row, col)
            backtrack(row + 1)
            remove(row, col)  # undo

backtrack(0)
```

---

## 15. Dynamic Programming

### Pattern: 1D DP (Linear)
Build solution bottom-up using a 1D array.

```
Use when: Fibonacci-like, house robber, climbing stairs, coin change
Key idea: dp[i] = f(dp[i-1], dp[i-2], ...)
```

**Template:**
```python
dp = [0] * (n + 1)
dp[0] = base_case_0
dp[1] = base_case_1

for i in range(2, n + 1):
    dp[i] = dp[i-1] + dp[i-2]  # or other recurrence

return dp[n]
```

**Problems:** Climbing Stairs, House Robber, Coin Change, Decode Ways

---

### Pattern: 2D DP (Grid / Two Sequences)
Fill a 2D table for problems involving two sequences or a grid.

```
Use when: LCS, edit distance, unique paths, knapsack, string matching
Key idea: dp[i][j] depends on dp[i-1][j], dp[i][j-1], dp[i-1][j-1]
```

**Template:**
```python
m, n = len(text1), len(text2)
dp = [[0] * (n + 1) for _ in range(m + 1)]

for i in range(1, m + 1):
    for j in range(1, n + 1):
        if text1[i-1] == text2[j-1]:
            dp[i][j] = dp[i-1][j-1] + 1
        else:
            dp[i][j] = max(dp[i-1][j], dp[i][j-1])

return dp[m][n]
```

**Problems:** LCS, Edit Distance, Unique Paths, Minimum Path Sum, Interleaving String

---

### Pattern: 0/1 Knapsack
For each item, decide include or exclude.

```
Use when: subset sum, partition equal subset, target sum
Key idea: dp[i][w] = max profit using first i items with capacity w
Optimization: iterate capacity in reverse for 1D space optimization
```

**Template:**
```python
dp = [0] * (capacity + 1)
for weight, value in items:
    for w in range(capacity, weight - 1, -1):  # reverse!
        dp[w] = max(dp[w], dp[w - weight] + value)
return dp[capacity]
```

**Problems:** 0/1 Knapsack, Subset Sum, Partition Equal Subset Sum, Last Stone Weight II

---

### Pattern: Unbounded Knapsack
Each item can be used unlimited times.

```
Use when: coin change (min coins), coin change II (ways), rod cutting
Key idea: same as 0/1 but iterate forward (allow reuse)
```

**Template:**
```python
dp = [float('inf')] * (amount + 1)
dp[0] = 0
for coin in coins:
    for w in range(coin, amount + 1):  # forward!
        dp[w] = min(dp[w], dp[w - coin] + 1)
return dp[amount] if dp[amount] != float('inf') else -1
```

---

### Pattern: DP on Strings
Match characters, find subsequences, or transform strings.

```
Use when: palindrome problems, regex matching, wildcard matching
Key idea: expand from center for palindromes, row-by-row for matching
```

**Template (Longest Palindromic Substring):**
```python
def expand(s, l, r):
    while l >= 0 and r < len(s) and s[l] == s[r]:
        l -= 1
        r += 1
    return s[l+1:r]

result = ""
for i in range(len(s)):
    odd = expand(s, i, i)
    even = expand(s, i, i + 1)
    result = max(result, odd, even, key=len)
return result
```

**Problems:** Palindromic Substrings, Longest Palindromic Subsequence, Regular Expression Matching

---

### Pattern: DP on Trees
Compute values bottom-up on a tree.

```
Use when: house robber on tree, diameter, maximum path sum
Key idea: post-order DFS, return (with_node, without_node) from each subtree
```

**Template:**
```python
def dp(node):
    if not node:
        return 0, 0  # (include, exclude)
    l_inc, l_exc = dp(node.left)
    r_inc, r_exc = dp(node.right)

    include = node.val + l_exc + r_exc
    exclude = max(l_inc, l_exc) + max(r_inc, r_exc)
    return include, exclude

return max(dp(root))
```

---

### Pattern: DP with Bitmask
Track subsets of elements using bitmasks.

```
Use when: TSP, assign K workers to N tasks, covering problems, small N (≤ 20)
Key idea: state = (current_node, visited_bitmask)
```

**Template:**
```python
from functools import lru_cache

@lru_cache(None)
def dp(pos, visited):
    if visited == (1 << n) - 1:  # all visited
        return 0
    best = float('inf')
    for next_pos in range(n):
        if not (visited >> next_pos & 1):
            best = min(best, cost[pos][next_pos] + dp(next_pos, visited | (1 << next_pos)))
    return best

return dp(0, 1)  # start at 0, with 0 visited
```

---

## 16. Greedy

### Pattern: Interval Scheduling / Activity Selection
Always pick the activity that ends earliest.

```
Use when: non-overlapping intervals, maximum events
Key idea: sort by end time, greedily pick non-overlapping
```

**Template:**
```python
intervals.sort(key=lambda x: x[1])
count = 0
end = float('-inf')

for start, finish in intervals:
    if start >= end:
        count += 1
        end = finish

return count
```

**Problems:** Non-overlapping Intervals, Minimum Number of Arrows to Burst Balloons

---

### Pattern: Jump Game
Track the maximum reachable index.

```
Use when: can you reach end, minimum jumps
Key idea: at each index, update the farthest reachable position
```

**Template:**
```python
max_reach = 0
for i, jump in enumerate(nums):
    if i > max_reach:
        return False
    max_reach = max(max_reach, i + jump)
return True
```

**Problems:** Jump Game I & II, Video Stitching

---

### Pattern: Task Scheduling with Cooldown
Use a priority queue or math to schedule tasks optimally.

```
Use when: CPU scheduling, task cooldown
Key idea: always execute the most frequent available task
```

**Problems:** Task Scheduler, Reorganize String

---

## 17. Intervals

### Pattern: Merge Intervals
Sort by start, merge overlapping intervals.

```
Use when: merge overlapping intervals, meeting rooms
Key idea: sort by start, merge if current.start <= last.end
```

**Template:**
```python
intervals.sort(key=lambda x: x[0])
merged = [intervals[0]]

for start, end in intervals[1:]:
    if start <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], end)
    else:
        merged.append([start, end])

return merged
```

**Problems:** Merge Intervals, Insert Interval, Meeting Rooms I & II

---

### Pattern: Sweep Line
Process events (start/end points) in sorted order.

```
Use when: meeting rooms (min conference rooms), event overlap count
Key idea: +1 for start events, -1 for end events, track running max
```

**Template:**
```python
events = []
for start, end in intervals:
    events.append((start, 1))
    events.append((end, -1))

events.sort()
max_rooms = curr_rooms = 0
for time, change in events:
    curr_rooms += change
    max_rooms = max(max_rooms, curr_rooms)

return max_rooms
```

---

## 18. Math & Bit Manipulation

### Pattern: Bit Tricks
Common bit manipulation operations.

```
x & (x-1)     → clears the lowest set bit
x & (-x)      → isolates the lowest set bit
x ^ x = 0     → XOR of same number is 0
x ^ 0 = x     → XOR with 0 is identity
n & 1          → check if odd
n >> 1         → divide by 2
n << 1         → multiply by 2
```

**Pattern: Single Number (XOR)**
```python
result = 0
for num in nums:
    result ^= num
return result  # all pairs cancel out
```

**Pattern: Count Set Bits (Brian Kernighan)**
```python
count = 0
while n:
    n &= n - 1  # clear lowest set bit
    count += 1
return count
```

**Problems:** Single Number, Number of 1 Bits, Reverse Bits, Power of Two, Missing Number

---

### Pattern: Fast Power (Exponentiation by Squaring)
Compute x^n in O(log n).

```python
def pow(x, n):
    if n < 0:
        x, n = 1/x, -n
    result = 1
    while n:
        if n & 1:
            result *= x
        x *= x
        n >>= 1
    return result
```

---

### Pattern: GCD / LCM

```python
import math
gcd = math.gcd(a, b)
lcm = a * b // gcd
```

---

## 19. Sorting

### Pattern: Custom Sort
Sort by a custom comparator.

```python
# Sort by multiple keys
nums.sort(key=lambda x: (x[0], -x[1]))

# Sort by frequency then value
from collections import Counter
freq = Counter(nums)
nums.sort(key=lambda x: (-freq[x], x))
```

---

### Pattern: Counting Sort / Bucket Sort
Sort in O(n) when range is known.

```python
count = [0] * (max_val + 1)
for num in nums:
    count[num] += 1
result = []
for val, cnt in enumerate(count):
    result.extend([val] * cnt)
```

**Problems:** Sort Colors (Dutch National Flag), Top K Frequent Elements (bucket sort)

---

### Pattern: Dutch National Flag (3-way Partition)
Partition into 3 groups in one pass.

```python
low = mid = 0
high = len(nums) - 1

while mid <= high:
    if nums[mid] == 0:
        nums[low], nums[mid] = nums[mid], nums[low]
        low += 1; mid += 1
    elif nums[mid] == 1:
        mid += 1
    else:
        nums[mid], nums[high] = nums[high], nums[mid]
        high -= 1
```

---

## 20. Union Find (Disjoint Set)

### Pattern: Union Find with Path Compression + Rank
Efficiently track connected components.

```
Use when: connected components, cycle detection in undirected graph, dynamic connectivity
Key idea: find with path compression, union by rank
```

**Template:**
```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False  # already connected
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        self.components -= 1
        return True

    def connected(self, x, y):
        return self.find(x) == self.find(y)
```

**Problems:** Number of Connected Components, Redundant Connection, Accounts Merge, Graph Valid Tree

---

## 21. Monotonic Stack / Queue

### Pattern: Monotonic Increasing Stack
Maintain a stack where elements are in increasing order.

```
Use when: next smaller element, largest rectangle, trapping rain water
Key idea: pop when current element is smaller than top (breaks monotonicity)
```

**Template (Largest Rectangle in Histogram):**
```python
stack = []  # index stack
max_area = 0

for i, h in enumerate(heights + [0]):  # sentinel 0 at end
    while stack and heights[stack[-1]] >= h:
        height = heights[stack.pop()]
        width = i if not stack else i - stack[-1] - 1
        max_area = max(max_area, height * width)
    stack.append(i)

return max_area
```

**Problems:** Largest Rectangle in Histogram, Maximal Rectangle, Trapping Rain Water, Sum of Subarray Minimums

---

## 22. Segment Tree & BIT

### Pattern: Binary Indexed Tree (Fenwick Tree)
Efficient prefix sum updates and queries in O(log n).

```
Use when: range sum queries with point updates
Key idea: each index stores sum of a range determined by lowest set bit
```

**Template:**
```python
class BIT:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def update(self, i, delta):  # 1-indexed
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)  # move to parent

    def query(self, i):  # prefix sum [1, i]
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & (-i)  # move to responsible parent
        return total

    def range_query(self, l, r):
        return self.query(r) - self.query(l - 1)
```

**Problems:** Range Sum Query (Mutable), Count of Smaller Numbers After Self, Reverse Pairs

---

### Pattern: Segment Tree
Range queries and range updates in O(log n).

```
Use when: range min/max/sum queries with updates
Key idea: divide array into segments, store aggregate in each node
```

**Template:**
```python
class SegmentTree:
    def __init__(self, nums):
        self.n = len(nums)
        self.tree = [0] * (4 * self.n)
        self.build(nums, 0, 0, self.n - 1)

    def build(self, nums, node, start, end):
        if start == end:
            self.tree[node] = nums[start]
        else:
            mid = (start + end) // 2
            self.build(nums, 2*node+1, start, mid)
            self.build(nums, 2*node+2, mid+1, end)
            self.tree[node] = self.tree[2*node+1] + self.tree[2*node+2]

    def query(self, node, start, end, l, r):
        if r < start or end < l:
            return 0
        if l <= start and end <= r:
            return self.tree[node]
        mid = (start + end) // 2
        return self.query(2*node+1, start, mid, l, r) + \
               self.query(2*node+2, mid+1, end, l, r)
```

---

## Quick Reference: Pattern → Problem Mapping

| Pattern | Key Problems |
|---|---|
| Two Pointers | Two Sum II, 3Sum, Container With Most Water |
| Sliding Window | Longest Substring Without Repeating, Min Window Substring |
| Binary Search on Answer | Koko Eating Bananas, Capacity to Ship Packages |
| Prefix Sum + HashMap | Subarray Sum Equals K, Path Sum III |
| Monotonic Stack | Daily Temperatures, Largest Rectangle in Histogram |
| BFS | Word Ladder, Rotting Oranges, Shortest Path |
| Topological Sort | Course Schedule, Alien Dictionary |
| Dijkstra | Network Delay Time, Cheapest Flights |
| Union Find | Number of Connected Components, Redundant Connection |
| 0/1 Knapsack | Subset Sum, Partition Equal Subset |
| Unbounded Knapsack | Coin Change, Coin Change II |
| DP on Grid | Unique Paths, Minimum Path Sum |
| Backtracking | Subsets, Permutations, Combination Sum |
| Two Heaps | Find Median from Data Stream |
| Trie | Word Search II, Replace Words |
| Bitmask DP | TSP, Minimum Cost to Connect All Points |

---

## Problem Difficulty Roadmap

### Easy — Build Foundations
- Two Sum, Valid Parentheses, Reverse Linked List
- Maximum Subarray, Climbing Stairs, Best Time to Buy Stock
- Binary Search, Merge Two Sorted Lists, Number of 1 Bits

### Medium — Core Patterns
- 3Sum, Longest Substring Without Repeating Characters
- LRU Cache, Word Search, Coin Change
- Number of Islands, Course Schedule, Jump Game
- Subarray Sum Equals K, Partition Equal Subset Sum

### Hard — Advanced Combinations
- Trapping Rain Water, Sliding Window Maximum
- Largest Rectangle in Histogram, Serialize/Deserialize Tree
- Word Ladder II, Alien Dictionary, Edit Distance
- Median of Two Sorted Arrays, Regular Expression Matching
- Minimum Window Substring, Word Search II

---

*Tip: Most interview problems are combinations of 2-3 patterns. Practice recognizing the patterns first, then the implementation becomes natural.*

---

# Hard Problem Patterns — Advanced Reference

The sections below cover patterns that appear almost exclusively in Hard problems. Mastering these separates top candidates from the rest.

---

## H1. Interval DP

**Core idea:** The answer for a range `[i, j]` depends on splitting it at every possible midpoint `k`.

```
Use when: burst balloons, matrix chain multiplication, strange printer,
          removing boxes, palindrome partitioning II, optimal game strategy
Key idea: dp[i][j] = best answer for the subarray/substring [i..j]
          Try every split point k inside [i, j]
Order:    iterate by LENGTH of interval, not left endpoint
```

**Template:**
```python
n = len(arr)
dp = [[0] * n for _ in range(n)]

# Base case: length 1
for i in range(n):
    dp[i][i] = base_case(arr[i])

# Fill by increasing length
for length in range(2, n + 1):
    for i in range(n - length + 1):
        j = i + length - 1
        dp[i][j] = float('inf')  # or -inf
        for k in range(i, j):    # try all split points
            dp[i][j] = min(dp[i][j], dp[i][k] + dp[k+1][j] + cost(i, k, j))

return dp[0][n-1]
```

**Hard problems:** Burst Balloons (312), Remove Boxes (546), Strange Printer (664),
Minimum Cost to Merge Stones (1000), Zuma Game (488)

---

## H2. DP on Subsequences with States

**Core idea:** Add extra state dimensions to standard subsequence DP when more context is needed.

```
Use when: best time to buy/sell with cooldown or fee, painting fence,
          stock trading with at most K transactions
Key idea: states encode "what mode are we in" — holding, sold, rest, etc.
```

**Template (Stock with K transactions):**
```python
# dp[k][0] = max profit on day i, k transactions used, not holding
# dp[k][1] = max profit on day i, k transactions used, holding
dp = [[[-inf, -inf] for _ in range(K + 1)] for _ in range(n)]
dp[0][0][0] = 0
dp[0][0][1] = -prices[0]

for i in range(1, n):
    for k in range(K + 1):
        dp[i][k][0] = max(dp[i-1][k][0], dp[i-1][k][1] + prices[i])
        if k > 0:
            dp[i][k][1] = max(dp[i-1][k][1], dp[i-1][k-1][0] - prices[i])

return max(dp[n-1][k][0] for k in range(K + 1))
```

**Hard problems:** Best Time to Buy and Sell Stock III (123), IV (188),
with Cooldown (309), with Transaction Fee (714)

---

## H3. DP Optimization — Convex Hull Trick (CHT)

**Core idea:** When the DP recurrence has the form `dp[i] = min over j (dp[j] + cost(i, j))` where `cost` is linear in `i`, use a deque of lines to answer queries in O(1) amortized.

```
Use when: dp[i] = min{ dp[j] + b[j] * a[i] } — "line" form
          The naive O(n²) DP can be optimized to O(n)
Key signal: cost function factors into a product of two terms
```

**Template:**
```python
# Each j defines a line: y = b[j] * x + dp[j]
# Query at x = a[i]: find minimum y over all lines

from collections import deque

def bad(l1, l2, l3):
    # Is line l2 ever useful between l1 and l3?
    # l2 is redundant if the intersection of l1,l3 is left of l1,l2
    return (l3[1] - l1[1]) * (l1[0] - l2[0]) <= (l2[1] - l1[1]) * (l1[0] - l3[0])

hull = deque()  # stores (slope, intercept) pairs

for i in range(n):
    # Query: find min line value at x = a[i]
    while len(hull) >= 2 and hull[0][0] * a[i] + hull[0][1] >= hull[1][0] * a[i] + hull[1][1]:
        hull.popleft()
    dp[i] = hull[0][0] * a[i] + hull[0][1] + something

    # Add new line for this i
    new_line = (b[i], dp[i])
    while len(hull) >= 2 and bad(hull[-2], hull[-1], new_line):
        hull.pop()
    hull.append(new_line)
```

**Hard problems:** Minimum Cost to Cut a Stick (1547), Divide Array in Sets (1296 variant),
Maximize the Profit as the Salesman, some competitive programming geometry problems

---

## H4. Divide & Conquer DP Optimization

**Core idea:** When `opt(i, j)` (the optimal split point for state `(i, j)`) is monotone — `opt(i, j) ≤ opt(i, j+1)` — reduce O(n³) to O(n² log n) or O(n²).

```
Use when: dp[i][j] = min over k { dp[i-1][k] + cost(k+1, j) }
          AND the opt() function is monotone
```

**Template:**
```python
def solve(i, lo, hi, opt_lo, opt_hi):
    if lo > hi:
        return
    mid = (lo + hi) // 2
    best_cost = float('inf')
    best_k = opt_lo
    for k in range(opt_lo, min(opt_hi, mid) + 1):
        cost = dp[i-1][k] + C[k+1][mid]
        if cost < best_cost:
            best_cost = cost
            best_k = k
    dp[i][mid] = best_cost
    solve(i, lo, mid - 1, opt_lo, best_k)
    solve(i, mid + 1, hi, best_k, opt_hi)
```

**Hard problems:** Minimum Cost to Merge Stones variants, Optimal BST

---

## H5. Advanced Graph — Tarjan's Algorithm

### Bridges (Cut Edges)
An edge is a bridge if removing it disconnects the graph.

```
Use when: find critical connections, network reliability
Key idea: DFS with discovery time and low-link values
          Edge (u,v) is bridge if low[v] > disc[u]
```

**Template:**
```python
def find_bridges(n, edges):
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)

    disc = [-1] * n
    low = [0] * n
    bridges = []
    timer = [0]

    def dfs(u, parent):
        disc[u] = low[u] = timer[0]
        timer[0] += 1
        for v in graph[u]:
            if disc[v] == -1:
                dfs(v, u)
                low[u] = min(low[u], low[v])
                if low[v] > disc[u]:
                    bridges.append((u, v))  # bridge found
            elif v != parent:
                low[u] = min(low[u], disc[v])

    for i in range(n):
        if disc[i] == -1:
            dfs(i, -1)
    return bridges
```

**Hard problems:** Critical Connections in a Network (1192), Minimum Number of Days to Disconnect Island

---

### Strongly Connected Components (Tarjan's SCC)
Find groups where every node can reach every other node.

```
Use when: SCC in directed graphs, condensation DAG
Key idea: DFS + stack, node pops off when it's the root of an SCC
```

**Template:**
```python
def tarjan_scc(n, graph):
    disc = [-1] * n
    low = [0] * n
    on_stack = [False] * n
    stack = []
    sccs = []
    timer = [0]

    def dfs(u):
        disc[u] = low[u] = timer[0]
        timer[0] += 1
        stack.append(u)
        on_stack[u] = True

        for v in graph[u]:
            if disc[v] == -1:
                dfs(v)
                low[u] = min(low[u], low[v])
            elif on_stack[v]:
                low[u] = min(low[u], disc[v])

        if low[u] == disc[u]:  # root of SCC
            scc = []
            while True:
                v = stack.pop()
                on_stack[v] = False
                scc.append(v)
                if v == u:
                    break
            sccs.append(scc)

    for i in range(n):
        if disc[i] == -1:
            dfs(i)
    return sccs
```

**Hard problems:** Loud and Rich (851), Minimum Number of Vertices to Reach All Nodes (1557)

---

## H6. Minimum Spanning Tree (MST)

### Kruskal's Algorithm
Sort edges by weight, add if it doesn't form a cycle (use Union Find).

```
Use when: connect all nodes with minimum total edge weight
Key idea: greedy — always add cheapest safe edge
Time: O(E log E)
```

**Template:**
```python
def kruskal(n, edges):
    edges.sort(key=lambda x: x[2])  # sort by weight
    uf = UnionFind(n)
    mst_cost = 0
    mst_edges = []

    for u, v, w in edges:
        if uf.union(u, v):
            mst_cost += w
            mst_edges.append((u, v, w))
            if len(mst_edges) == n - 1:
                break

    return mst_cost, mst_edges
```

### Prim's Algorithm
Greedily grow the MST by adding the cheapest edge connecting tree to non-tree.

```
Use when: dense graphs (better than Kruskal for E >> V)
Key idea: use a min-heap tracking (cost, node)
Time: O(E log V)
```

**Template:**
```python
import heapq

def prim(n, graph):
    visited = set()
    heap = [(0, 0)]  # (cost, node), start from node 0
    total = 0

    while heap and len(visited) < n:
        cost, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        total += cost
        for v, w in graph[u]:
            if v not in visited:
                heapq.heappush(heap, (w, v))

    return total if len(visited) == n else -1
```

**Hard problems:** Min Cost to Connect All Points (1584), Optimize Water Distribution (1168)

---

## H7. Shortest Path — Bellman-Ford & Floyd-Warshall

### Bellman-Ford
Handles negative weights; detects negative cycles.

```
Use when: negative weight edges, detect negative cycles
Key idea: relax ALL edges V-1 times; if still improving → negative cycle
Time: O(V * E)
```

**Template:**
```python
def bellman_ford(n, edges, src):
    dist = [float('inf')] * n
    dist[src] = 0

    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] != float('inf') and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w

    # Check for negative cycles
    for u, v, w in edges:
        if dist[u] + w < dist[v]:
            return None  # negative cycle exists

    return dist
```

**Hard problems:** Cheapest Flights Within K Stops (787) — modified Bellman-Ford with K relaxation rounds

---

### Floyd-Warshall
All-pairs shortest path.

```
Use when: shortest path between ALL pairs of nodes
Key idea: dp[i][j] = min over all intermediate nodes k
Time: O(V³) — only use for small graphs (V ≤ ~400)
```

**Template:**
```python
def floyd_warshall(n, edges):
    dist = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for u, v, w in edges:
        dist[u][v] = w

    for k in range(n):        # intermediate node
        for i in range(n):    # source
            for j in range(n):  # destination
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    return dist
```

**Hard problems:** Find the City With Smallest Number of Neighbors (1334), Network Delay Time (743)

---

## H8. Advanced String — KMP Algorithm

**Core idea:** Precompute a failure function to avoid redundant comparisons during pattern matching.

```
Use when: find all occurrences of pattern in text, repeated string detection
Key idea: failure[i] = length of longest proper prefix of pattern[0..i]
          that is also a suffix
Time: O(n + m) vs O(n*m) naive
```

**Template:**
```python
def kmp_search(text, pattern):
    # Build failure function
    m = len(pattern)
    fail = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = fail[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        fail[i] = j

    # Search
    matches = []
    j = 0
    for i in range(len(text)):
        while j > 0 and text[i] != pattern[j]:
            j = fail[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            matches.append(i - m + 1)
            j = fail[j - 1]
    return matches
```

**Hard problems:** Repeated Substring Pattern (459), Shortest Palindrome (214),
Find the Index of the First Occurrence (28)

---

## H9. Rolling Hash (Rabin-Karp)

**Core idea:** Compute a hash for a window that can be updated in O(1) by sliding.

```
Use when: find all occurrences of pattern, duplicate substrings, longest duplicate substring
Key idea: hash(window) = (hash * base + new_char - old_char * base^k) % mod
          Use double hashing to avoid collisions
```

**Template:**
```python
def rabin_karp(text, pattern):
    BASE = 31
    MOD = 10**9 + 7
    n, m = len(text), len(pattern)

    def char_val(c):
        return ord(c) - ord('a') + 1

    # Compute pattern hash and first window hash
    p_hash = 0
    t_hash = 0
    power = 1

    for i in range(m):
        p_hash = (p_hash * BASE + char_val(pattern[i])) % MOD
        t_hash = (t_hash * BASE + char_val(text[i])) % MOD
        if i > 0:
            power = power * BASE % MOD

    results = []
    if p_hash == t_hash and text[:m] == pattern:
        results.append(0)

    for i in range(1, n - m + 1):
        t_hash = (t_hash - char_val(text[i-1]) * power) % MOD
        t_hash = (t_hash * BASE + char_val(text[i + m - 1])) % MOD
        t_hash %= MOD
        if t_hash == p_hash and text[i:i+m] == pattern:
            results.append(i)

    return results
```

**Hard problems:** Longest Duplicate Substring (1044), Distinct Echo Substrings (1316),
Longest Repeating Substring (1062)

---

## H10. Meet in the Middle

**Core idea:** Split the problem in half, enumerate all possibilities for each half separately (2^(n/2) each), then combine.

```
Use when: brute force is 2^n but 2^(n/2) is feasible (n ≤ 40)
          subset sum with large n, 4-sum, partition into equal subsets
Key idea: enumerate left half, sort, binary search for complement in right half
```

**Template (Subset Sum = Target):**
```python
from itertools import combinations
import bisect

def meet_in_middle(nums, target):
    n = len(nums)
    left, right = nums[:n//2], nums[n//2:]

    def get_all_sums(arr):
        sums = []
        for r in range(len(arr) + 1):
            for combo in combinations(arr, r):
                sums.append(sum(combo))
        return sorted(sums)

    left_sums = get_all_sums(left)
    right_sums = get_all_sums(right)

    count = 0
    for s in left_sums:
        complement = target - s
        lo = bisect.bisect_left(right_sums, complement)
        hi = bisect.bisect_right(right_sums, complement)
        count += hi - lo

    return count
```

**Hard problems:** Partition Array Into Two Arrays to Minimize Sum Difference (2035),
Closest Subsequence Sum (1755), 4Sum II (454)

---

## H11. Monotonic Stack — Hard Variants

### Sum of Subarray Minimums / Maximums
For each element, find how many subarrays it is the minimum of.

```
Use when: sum of subarray min/max, contribution technique
Key idea: for each element, find left boundary (prev smaller) and right boundary (next smaller)
          contribution = arr[i] * left_count * right_count
```

**Template:**
```python
def sum_subarray_mins(arr):
    MOD = 10**9 + 7
    n = len(arr)
    left = [0] * n   # distance to previous smaller (or equal)
    right = [0] * n  # distance to next smaller

    stack = []
    for i in range(n):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        left[i] = i - stack[-1] if stack else i + 1
        stack.append(i)

    stack = []
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] > arr[i]:  # strict for right to avoid double count
            stack.pop()
        right[i] = stack[-1] - i if stack else n - i
        stack.append(i)

    return sum(arr[i] * left[i] * right[i] for i in range(n)) % MOD
```

**Hard problems:** Sum of Subarray Minimums (907), Maximum of Subarray Minimums,
Sum of Subarray Ranges (2104)

---

## H12. Line Sweep for Geometry / Intervals

### Skyline Problem
Find the outline profile of buildings.

```
Use when: skyline, rectangle union area, max overlap at any point
Key idea: events at each x-coordinate (building start/end),
          use a max-heap to track active building heights
```

**Template:**
```python
import heapq

def get_skyline(buildings):
    events = []
    for l, r, h in buildings:
        events.append((l, -h, r))  # start: negative height (max-heap)
        events.append((r, 0, 0))   # end: height 0

    events.sort()
    result = []
    heap = [(0, float('inf'))]  # (neg_height, end_x)

    for x, neg_h, end in events:
        # Remove expired buildings
        while heap[0][1] <= x:
            heapq.heappop(heap)
        if neg_h != 0:
            heapq.heappush(heap, (neg_h, end))
        curr_max = -heap[0][0]
        if not result or result[-1][1] != curr_max:
            result.append([x, curr_max])

    return result
```

**Hard problems:** The Skyline Problem (218), Rectangle Area II (850)

---

## H13. Advanced BFS — Multi-source, Bidirectional, A*

### Bidirectional BFS
Search from both start and end simultaneously; meet in the middle.

```
Use when: word ladder, shortest path when start AND end are known
Key idea: always expand the smaller frontier — dramatically reduces search space
Time: O(b^(d/2)) vs O(b^d) for standard BFS
```

**Template:**
```python
from collections import deque

def bidirectional_bfs(start, end, get_neighbors):
    if start == end:
        return 0

    front = {start}
    back = {end}
    visited_front = {start}
    visited_back = {end}
    steps = 0

    while front and back:
        steps += 1
        # Always expand smaller frontier
        if len(front) > len(back):
            front, back = back, front
            visited_front, visited_back = visited_back, visited_front

        next_front = set()
        for node in front:
            for neighbor in get_neighbors(node):
                if neighbor in back:
                    return steps
                if neighbor not in visited_front:
                    visited_front.add(neighbor)
                    next_front.add(neighbor)
        front = next_front

    return -1
```

**Hard problems:** Word Ladder II (126), Minimum Genetic Mutation (433)

---

### 0-1 BFS
BFS on a graph where edges have weight 0 or 1 — use deque, push weight-0 to front.

```
Use when: grid/graph where moves cost 0 or 1
Key idea: deque appendleft for 0-cost, append for 1-cost edges
Time: O(V + E) — faster than Dijkstra for 0-1 weights
```

**Template:**
```python
from collections import deque

def zero_one_bfs(grid, start, end):
    n, m = len(grid), len(grid[0])
    dist = [[float('inf')] * m for _ in range(n)]
    dist[start[0]][start[1]] = 0
    dq = deque([start])

    while dq:
        r, c = dq.popleft()
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m:
                cost = 0 if grid[nr][nc] == '.' else 1
                if dist[r][c] + cost < dist[nr][nc]:
                    dist[nr][nc] = dist[r][c] + cost
                    if cost == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))

    return dist[end[0]][end[1]]
```

**Hard problems:** Minimum Obstacle Removal to Reach Corner (2290), Minimum Cost to Make at Least One Valid Path in a Grid (1368)

---

## H14. Segment Tree with Lazy Propagation

**Core idea:** Defer range updates — store pending updates at each node, push down when needed.

```
Use when: range updates (add to range, set range) + range queries
Key idea: "lazy" tag at each node means "this update hasn't been applied to children yet"
Time: O(log n) per update and query
```

**Template:**
```python
class LazySegTree:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (4 * n)
        self.lazy = [0] * (4 * n)

    def push_down(self, node, start, end):
        if self.lazy[node]:
            mid = (start + end) // 2
            self.tree[2*node+1] += self.lazy[node] * (mid - start + 1)
            self.tree[2*node+2] += self.lazy[node] * (end - mid)
            self.lazy[2*node+1] += self.lazy[node]
            self.lazy[2*node+2] += self.lazy[node]
            self.lazy[node] = 0

    def update(self, node, start, end, l, r, val):
        if r < start or end < l:
            return
        if l <= start and end <= r:
            self.tree[node] += val * (end - start + 1)
            self.lazy[node] += val
            return
        self.push_down(node, start, end)
        mid = (start + end) // 2
        self.update(2*node+1, start, mid, l, r, val)
        self.update(2*node+2, mid+1, end, l, r, val)
        self.tree[node] = self.tree[2*node+1] + self.tree[2*node+2]

    def query(self, node, start, end, l, r):
        if r < start or end < l:
            return 0
        if l <= start and end <= r:
            return self.tree[node]
        self.push_down(node, start, end)
        mid = (start + end) // 2
        return self.query(2*node+1, start, mid, l, r) + \
               self.query(2*node+2, mid+1, end, l, r)
```

**Hard problems:** Range Sum Query with Updates, My Calendar III (732), Count of Range Sum (327)

---

## H15. Persistent Data Structures

**Core idea:** Each update creates a new version by sharing unchanged nodes with the old version.

```
Use when: range kth smallest, historical queries, offline queries
Key idea: persistent segment tree — each update creates O(log n) new nodes
```

**Persistent Segment Tree (Range Kth Smallest):**
```python
class Node:
    def __init__(self, left=None, right=None, count=0):
        self.left = left
        self.right = right
        self.count = count

def update(prev, lo, hi, val):
    node = Node(prev.left, prev.right, prev.count + 1)
    if lo == hi:
        return node
    mid = (lo + hi) // 2
    if val <= mid:
        node.left = update(prev.left, lo, mid, val)
    else:
        node.right = update(prev.right, mid+1, hi, val)
    return node

def kth(left_root, right_root, lo, hi, k):
    if lo == hi:
        return lo
    mid = (lo + hi) // 2
    left_count = right_root.left.count - left_root.left.count
    if k <= left_count:
        return kth(left_root.left, right_root.left, lo, mid, k)
    else:
        return kth(left_root.right, right_root.right, mid+1, hi, k - left_count)
```

**Hard problems:** Count of Range Sum (327), Kth Smallest Element in a Sorted Matrix (378)

---

## H16. Hard DP Patterns — State Machine

**Core idea:** Model a problem as transitions between discrete states.

```
Use when: problems with "modes" or "phases" — with/without item, normal/boosted,
          buy/sell/hold/cooldown
Key idea: define all possible states explicitly, write transition rules
```

**Template (Generic 3-state machine):**
```python
# States: A, B, C
# Transitions depend on problem

state_A = state_B = state_C = initial_values

for x in input_sequence:
    new_A = max(state_A + cost_stay_A(x),
                state_B + cost_B_to_A(x),
                state_C + cost_C_to_A(x))
    new_B = max(state_A + cost_A_to_B(x),
                state_B + cost_stay_B(x))
    new_C = max(state_B + cost_B_to_C(x),
                state_C + cost_stay_C(x))
    state_A, state_B, state_C = new_A, new_B, new_C

return max(state_A, state_B, state_C)
```

**Hard problems:** Best Time to Buy Stock with Cooldown (309), Paint House II (265),
Frog Jump (403 — unbounded states)

---

## H17. Hard Backtracking — Pruning Strategies

The difference between TLE and AC on hard backtracking is aggressive pruning.

```
Key pruning techniques:
1. Sort + Skip duplicates early (avoid duplicate branches)
2. Forward checking — if remaining elements can't satisfy constraint, prune
3. Constraint propagation — reduce domain before recursing (Sudoku)
4. Symmetry breaking — avoid exploring symmetric states
```

**Template (Combination Sum with Pruning):**
```python
def backtrack(start, remaining, current):
    if remaining == 0:
        result.append(list(current))
        return
    for i in range(start, len(candidates)):
        if candidates[i] > remaining:
            break   # sorted — no point continuing
        if i > start and candidates[i] == candidates[i-1]:
            continue  # skip duplicates at same level
        current.append(candidates[i])
        backtrack(i + 1, remaining - candidates[i], current)
        current.pop()

candidates.sort()
result = []
backtrack(0, target, [])
```

**Template (Sudoku — Constraint Propagation):**
```python
def solve(board, rows, cols, boxes):
    empty = find_empty(board)
    if not empty:
        return True
    r, c = empty
    box_id = (r // 3) * 3 + c // 3

    for num in '123456789':
        if num not in rows[r] and num not in cols[c] and num not in boxes[box_id]:
            board[r][c] = num
            rows[r].add(num); cols[c].add(num); boxes[box_id].add(num)
            if solve(board, rows, cols, boxes):
                return True
            board[r][c] = '.'
            rows[r].remove(num); cols[c].remove(num); boxes[box_id].remove(num)
    return False
```

**Hard problems:** Sudoku Solver (37), N-Queens (51), Expression Add Operators (282),
Remove Invalid Parentheses (301), Palindrome Partitioning II (132)

---

## H18. Key Hard Problem Recognition Guide

| If you see... | Think... |
|---|---|
| Subarray min/max sum, contribution | Monotonic Stack + left/right boundaries |
| Intervals splitting into optimal groups | Interval DP |
| Subset/combination, n ≤ 40 | Meet in the Middle |
| Graph with negative weights | Bellman-Ford |
| All-pairs shortest path | Floyd-Warshall |
| Critical edges/nodes in graph | Tarjan's Bridges / Articulation Points |
| Connect all nodes min cost | Kruskal's / Prim's MST |
| Pattern in text, O(n+m) | KMP |
| Duplicate/longest substring, large n | Rolling Hash (Rabin-Karp) |
| Range updates + range queries | Lazy Segment Tree |
| Kth element over range of indices | Persistent Segment Tree |
| dp[i] = min{ dp[j] + m*b[j] } form | Convex Hull Trick |
| Shortest path, 0 or 1 cost | 0-1 BFS (Deque) |
| Shortest path, start AND end known | Bidirectional BFS |
| Building heights / skyline events | Line Sweep + Max-Heap |
| "Modes" (hold/sell/rest/cooldown) | DP State Machine |

---

## H19. Complexity Cheat Sheet for Hard Problems

```
O(log n)      Binary search, BIT/Fenwick query
O(n)          Two pointers, sliding window, KMP, 0-1 BFS
O(n log n)    Sorting, segment tree, Dijkstra (E log V)
O(n²)         2D DP, Floyd-Warshall (small n only)
O(n³)         Interval DP naive, matrix multiplication
O(n · 2^n)    Bitmask DP (n ≤ 20)
O(2^(n/2))    Meet in the middle (n ≤ 40)
O(E · V)      Bellman-Ford
```

**When to use which approach by constraint:**

| Constraint | Approach |
|---|---|
| n ≤ 10 | Brute force, full backtracking |
| n ≤ 20 | Bitmask DP, meet-in-middle |
| n ≤ 100 | O(n³) DP, Floyd-Warshall |
| n ≤ 1,000 | O(n²) DP, O(n² log n) |
| n ≤ 10,000 | O(n log² n) |
| n ≤ 100,000 | O(n log n) — segment tree, Dijkstra, sorting |
| n ≤ 1,000,000 | O(n) or O(n log n) — two pointers, BFS, KMP |

---

*For hard problems: first identify the bottleneck constraint → pick the complexity class → match to the pattern. The combination of pattern recognition + constraint analysis is what makes hard problems solvable.*
