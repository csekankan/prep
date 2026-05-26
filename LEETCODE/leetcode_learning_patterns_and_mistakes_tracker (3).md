# LeetCode 3629 — Minimum Jumps to Reach End via Prime Teleportation

# Problem Type

* BFS
* Implicit Graph
* Prime Factorization
* Graph Optimization
* Teleport BFS

---

# Your Original Thought Process

You correctly identified:

* this is a shortest path problem
* BFS should be used
* explicit graph construction would be too expensive
* prime preprocessing is important
* mapping prime -> indices is useful

This is already strong graph intuition.

---

# Your Original Code

```python
MAX=1000001
factors=[[i] for i in range(MAX)]
factors[0].pop()
factors[1].pop()

for i in range(2,MAX):
    if len(factors[i])==1 :

        for val in range(2*i,MAX,i):
            factors[val].append(i)

class Solution:

    def isPrime(self,i):
        return len(factors[i])==1

    def minJumps(self, nums: List[int]) -> int:

        start=0
        q=deque()
        q.append([start,0])

        end=len(nums)-1

        jumpNonPrime=defaultdict(list)

        for i,val in enumerate(nums):

            if not self.isPrime(val):

                for p in factors[val]:
                    jumpNonPrime[p].append(i)

            if self.isPrime(val):
                jumpNonPrime[val].append(i)

        visited=[False for _ in range(len(nums))]

        while len(q)>0:

            ind,jumpCount=q.popleft()

            if ind==end:
                return jumpCount

            visited[ind]=True

            if self.isPrime(nums[ind]):

                for i in jumpNonPrime[nums[ind]]:

                    if not visited[i]:
                        visited[i]=True
                        q.append([i,jumpCount+1])

            if ind-1>=0 and not visited[ind-1]:
                visited[ind-1]=True
                q.append([ind-1,jumpCount+1])

            if ind+1<len(nums) and not visited[ind+1]:
                visited[ind+1]=True
                q.append([ind+1,jumpCount+1])

        return len(nums)-1
```

---

# Main Mistake

## Problematic Part

```python
if self.isPrime(nums[ind]):

    for i in jumpNonPrime[nums[ind]]:
```

You repeatedly processed the same adjacency list.

---

# Why This Causes TLE

Example:

```python
nums = [2,2,2,2,2,2,2....]
```

Suppose:

```text
prime 2 appears 50,000 times
```

Then:

```text
visit first 2  -> iterate 50k indices
visit second 2 -> iterate 50k again
visit third 2  -> iterate 50k again
```

Complexity becomes near:

```text
O(n²)
```

---

# Important BFS Optimization Pattern

This is a VERY common optimization:

```text
process teleport/group adjacency only once
```

After processing:

```python
graph[val].clear()
```

Seen in:

* Jump Game IV
* Word Ladder
* Bus Routes
* Teleport graph problems

---

# Another Mistake

You sometimes marked visited too late.

Example:

```python
visited[ind]=True
```

inside pop-processing.

Correct BFS pattern:

```python
visited[nxt]=True
q.append(nxt)
```

Mark visited immediately during enqueue.

Otherwise same node may enter queue multiple times.

---

# Core Algorithm

## Step 1 — Precompute prime factors

```python
factors = [[] for _ in range(MAX)]

for i in range(2, MAX):

    if not factors[i]:

        for j in range(i, MAX, i):
            factors[j].append(i)
```

Meaning:

```text
factors[x] stores all prime divisors of x
```

---

## Step 2 — Build prime -> indices map

```python
for i, val in enumerate(nums):

    if val is prime:
        graph[val].append(i)

    else:
        for p in factors[val]:
            graph[p].append(i)
```

Meaning:

```text
For every prime p,
store all indices connected through p.
```

---

## Step 3 — BFS

From index i:

```text
1. move left
2. move right
3. if nums[i] is prime:
      jump to all indices connected to that prime
```

---

## Step 4 — IMPORTANT optimization

After processing adjacency:

```python
graph[val].clear()
```

Mental shortcut:

```text
consume adjacency only once
```

---

# Easy Interview Recall Version

```text
Precompute factors
-> build prime -> indices mapping
-> BFS
-> consume teleport adjacency once
```

---

# Correct Optimized Code

```python
from collections import defaultdict, deque

MAX = 10**6 + 1

# factors[x] = prime divisors of x
factors = [[] for _ in range(MAX)]

for i in range(2, MAX):

    # if empty => prime
    if not factors[i]:

        for j in range(i, MAX, i):
            factors[j].append(i)


class Solution:

    def isPrime(self, x):

        # prime numbers have exactly one prime divisor: themselves
        return len(factors[x]) == 1 and factors[x][0] == x


    def minJumps(self, nums: List[int]) -> int:

        n = len(nums)

        # prime -> connected indices
        graph = defaultdict(list)

        # build implicit graph
        for i, val in enumerate(nums):

            if self.isPrime(val):

                graph[val].append(i)

            else:

                for p in factors[val]:
                    graph[p].append(i)

        q = deque([(0, 0)])

        visited = [False] * n

        # IMPORTANT
        # mark visited during enqueue
        visited[0] = True

        while q:

            ind, dist = q.popleft()

            # reached end
            if ind == n - 1:
                return dist

            val = nums[ind]

            # teleport jump
            if self.isPrime(val):

                for nxt in graph[val]:

                    if not visited[nxt]:

                        visited[nxt] = True
                        q.append((nxt, dist + 1))

                # VERY IMPORTANT OPTIMIZATION
                # consume adjacency once
                graph[val].clear()

            # left move
            if ind - 1 >= 0 and not visited[ind - 1]:

                visited[ind - 1] = True
                q.append((ind - 1, dist + 1))

            # right move
            if ind + 1 < n and not visited[ind + 1]:

                visited[ind + 1] = True
                q.append((ind + 1, dist + 1))

        return -1
```

---

# Biggest Learning From This Problem

Whenever you see:

```text
value/group -> list of nodes
```

always ask:

> “Can this adjacency/group be consumed only once?”

This prevents many hidden BFS TLEs.
