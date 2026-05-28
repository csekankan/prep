# LeetCode Interview Roadmap (Sorted by ROI)

Problems within each topic: first one teaches the core pattern, rest sorted by interview frequency.
Topics sorted by how likely they appear in a real interview loop.

---

## TIER 1 — Do These First (appear in 80%+ of interviews)

---

### 1. Two Pointers

**Pattern:** Two indices scanning from opposite ends or same direction to reduce O(n^2) to O(n).

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Container With Most Water | Medium | https://leetcode.com/problems/container-with-most-water/ |
| - [ ] | 3Sum | Medium | https://leetcode.com/problems/3sum/ |
| - [ ] | Trapping Rain Water | Hard | https://leetcode.com/problems/trapping-rain-water/ |
| - [ ] | Two Sum II - Input Array Is Sorted | Medium | https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/ |
| - [ ] | Merge Sorted Array | Easy | https://leetcode.com/problems/merge-sorted-array/ |

---

### 2. Arrays

**Pattern:** In-place manipulation, prefix/suffix tricks, index-as-hash.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Product of Array Except Self | Medium | https://leetcode.com/problems/product-of-array-except-self/ |
| - [ ] | Best Time to Buy and Sell Stock | Easy | https://leetcode.com/problems/best-time-to-buy-and-sell-stock/ |
| - [ ] | First Missing Positive | Hard | https://leetcode.com/problems/first-missing-positive/ |
| - [ ] | Rotate Array | Medium | https://leetcode.com/problems/rotate-array/ |
| - [ ] | Majority Element | Easy | https://leetcode.com/problems/majority-element/ |
| - [ ] | Move Zeroes | Easy | https://leetcode.com/problems/move-zeroes/ |
| - [ ] | Remove Duplicates from Sorted Array | Easy | https://leetcode.com/problems/remove-duplicates-from-sorted-array/ |
| - [ ] | Best Time to Buy and Sell Stock II | Medium | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/ |
| - [ ] | Increasing Triplet Subsequence | Medium | https://leetcode.com/problems/increasing-triplet-subsequence/ |
| - [ ] | Number of Zero-Filled Subarrays | Medium | https://leetcode.com/problems/number-of-zero-filled-subarrays/ |

---

### 3. Hash Tables

**Pattern:** O(1) lookup to trade space for time. Frequency maps, grouping, two-sum pattern.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Group Anagrams | Medium | https://leetcode.com/problems/group-anagrams/ |
| - [ ] | Longest Consecutive Sequence | Medium | https://leetcode.com/problems/longest-consecutive-sequence/ |
| - [ ] | Ransom Note | Easy | https://leetcode.com/problems/ransom-note/ |
| - [ ] | Isomorphic Strings | Easy | https://leetcode.com/problems/isomorphic-strings/ |
| - [ ] | Contains Duplicate II | Easy | https://leetcode.com/problems/contains-duplicate-ii/ |
| - [ ] | Reorganize String | Medium | https://leetcode.com/problems/reorganize-string/ |
| - [ ] | Encode and Decode TinyURL | Medium | https://leetcode.com/problems/encode-and-decode-tinyurl/ |
| - [ ] | Number of Matching Subsequences | Medium | https://leetcode.com/problems/number-of-matching-subsequences/ |
| - [ ] | Split Array into Consecutive Subsequences | Medium | https://leetcode.com/problems/split-array-into-consecutive-subsequences/ |
| - [ ] | Number of Good Ways to Split a String | Medium | https://leetcode.com/problems/number-of-good-ways-to-split-a-string/ |
| - [ ] | Design HashMap | Easy | https://leetcode.com/problems/design-hashmap/ |
| - [ ] | Maximum Number of Balloons | Easy | https://leetcode.com/problems/maximum-number-of-balloons/ |
| - [ ] | Number of Good Pairs | Easy | https://leetcode.com/problems/number-of-good-pairs/ |

---

### 4. Sliding Window (Dynamic Size)

**Pattern:** Expand right, shrink left to maintain a valid window. Track state with a map/counter.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Longest Substring Without Repeating Characters | Medium | https://leetcode.com/problems/longest-substring-without-repeating-characters/ |
| - [ ] | Minimum Window Substring | Hard | https://leetcode.com/problems/minimum-window-substring/ |
| - [ ] | Longest Repeating Character Replacement | Medium | https://leetcode.com/problems/longest-repeating-character-replacement/ |
| - [ ] | Minimum Size Subarray Sum | Medium | https://leetcode.com/problems/minimum-size-subarray-sum/ |
| - [ ] | Max Consecutive Ones III | Medium | https://leetcode.com/problems/max-consecutive-ones-iii/ |

---

### 5. Sliding Window (Fixed Size)

**Pattern:** Fixed-size window slides across array. Add new element, remove old, update answer.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Find All Anagrams in a String | Medium | https://leetcode.com/problems/find-all-anagrams-in-a-string/ |
| - [ ] | Permutation in String | Medium | https://leetcode.com/problems/permutation-in-string/ |
| - [ ] | Substring with Concatenation of All Words | Hard | https://leetcode.com/problems/substring-with-concatenation-of-all-words/ |
| - [ ] | Maximum Sum of Distinct Subarrays With Length K | Medium | https://leetcode.com/problems/maximum-sum-of-distinct-subarrays-with-length-k/ |
| - [ ] | Maximum Average Subarray I | Easy | https://leetcode.com/problems/maximum-average-subarray-i/ |

---

### 6. Binary Search

**Pattern:** Search on sorted data OR search on answer space. Halve the problem each step.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Search in Rotated Sorted Array | Medium | https://leetcode.com/problems/search-in-rotated-sorted-array/ |
| - [ ] | Find First and Last Position of Element in Sorted Array | Medium | https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/ |
| - [ ] | Koko Eating Bananas | Medium | https://leetcode.com/problems/koko-eating-bananas/ |
| - [ ] | Find Peak Element | Medium | https://leetcode.com/problems/find-peak-element/ |
| - [ ] | Search a 2D Matrix | Medium | https://leetcode.com/problems/search-a-2d-matrix/ |
| - [ ] | Find Minimum in Rotated Sorted Array | Medium | https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/ |
| - [ ] | Median of Two Sorted Arrays | Hard | https://leetcode.com/problems/median-of-two-sorted-arrays/ |
| - [ ] | Random Pick with Weight | Medium | https://leetcode.com/problems/random-pick-with-weight/ |
| - [ ] | Find in Mountain Array | Hard | https://leetcode.com/problems/find-in-mountain-array/ |
| - [ ] | Search Insert Position | Easy | https://leetcode.com/problems/search-insert-position/ |

---

### 7. Stacks

**Pattern:** LIFO for matching pairs, nested structures, nearest smaller/greater tracking.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Valid Parentheses | Easy | https://leetcode.com/problems/valid-parentheses/ |
| - [ ] | Min Stack | Medium | https://leetcode.com/problems/min-stack/ |
| - [ ] | Evaluate Reverse Polish Notation | Medium | https://leetcode.com/problems/evaluate-reverse-polish-notation/ |
| - [ ] | Basic Calculator II | Medium | https://leetcode.com/problems/basic-calculator-ii/ |
| - [ ] | Longest Valid Parentheses | Hard | https://leetcode.com/problems/longest-valid-parentheses/ |
| - [ ] | Remove Duplicate Letters | Medium | https://leetcode.com/problems/remove-duplicate-letters/ |
| - [ ] | Removing Stars From a String | Medium | https://leetcode.com/problems/removing-stars-from-a-string/ |
| - [ ] | Remove All Adjacent Duplicates In String | Easy | https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/ |

---

### 8. Tree Traversal — DFS (Pre/In/Post Order combined)

**Pattern:** Recursion on tree structure. Pre=process before children, In=BST sorted, Post=process after children.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Lowest Common Ancestor of a Binary Tree | Medium | https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/ |
| - [ ] | Validate Binary Search Tree | Medium | https://leetcode.com/problems/validate-binary-search-tree/ |
| - [ ] | Binary Tree Maximum Path Sum | Hard | https://leetcode.com/problems/binary-tree-maximum-path-sum/ |
| - [ ] | Serialize and Deserialize Binary Tree | Hard | https://leetcode.com/problems/serialize-and-deserialize-binary-tree/ |
| - [ ] | Construct Binary Tree from Preorder and Inorder Traversal | Medium | https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/ |
| - [ ] | Kth Smallest Element in a BST | Medium | https://leetcode.com/problems/kth-smallest-element-in-a-bst/ |
| - [ ] | Diameter of Binary Tree | Easy | https://leetcode.com/problems/diameter-of-binary-tree/ |
| - [ ] | Invert Binary Tree | Easy | https://leetcode.com/problems/invert-binary-tree/ |
| - [ ] | Flatten Binary Tree to Linked List | Medium | https://leetcode.com/problems/flatten-binary-tree-to-linked-list/ |
| - [ ] | Path Sum III | Medium | https://leetcode.com/problems/path-sum-iii/ |
| - [ ] | Symmetric Tree | Easy | https://leetcode.com/problems/symmetric-tree/ |
| - [ ] | Same Tree | Easy | https://leetcode.com/problems/same-tree/ |
| - [ ] | Maximum Difference Between Node and Ancestor | Medium | https://leetcode.com/problems/maximum-difference-between-node-and-ancestor/ |
| - [ ] | Find Duplicate Subtrees | Medium | https://leetcode.com/problems/find-duplicate-subtrees/ |
| - [ ] | Delete Nodes And Return Forest | Medium | https://leetcode.com/problems/delete-nodes-and-return-forest/ |
| - [ ] | Distribute Coins in Binary Tree | Medium | https://leetcode.com/problems/distribute-coins-in-binary-tree/ |
| - [ ] | Binary Search Tree Iterator | Medium | https://leetcode.com/problems/binary-search-tree-iterator/ |
| - [ ] | Construct Binary Tree from Inorder and Postorder Traversal | Medium | https://leetcode.com/problems/construct-binary-tree-from-inorder-and-postorder-traversal/ |
| - [ ] | Convert Sorted Array to Binary Search Tree | Easy | https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/ |
| - [ ] | Count Complete Tree Nodes | Easy | https://leetcode.com/problems/count-complete-tree-nodes/ |
| - [ ] | Minimum Distance Between BST Nodes | Easy | https://leetcode.com/problems/minimum-distance-between-bst-nodes/ |
| - [ ] | Minimum Absolute Difference in BST | Easy | https://leetcode.com/problems/minimum-absolute-difference-in-bst/ |
| - [ ] | Binary Tree Paths | Easy | https://leetcode.com/problems/binary-tree-paths/ |
| - [ ] | Binary Tree Preorder Traversal | Easy | https://leetcode.com/problems/binary-tree-preorder-traversal/ |
| - [ ] | Binary Tree Inorder Traversal | Easy | https://leetcode.com/problems/binary-tree-inorder-traversal/ |
| - [ ] | Binary Tree Postorder Traversal | Easy | https://leetcode.com/problems/binary-tree-postorder-traversal/ |

---

### 9. Tree Traversal — BFS (Level Order)

**Pattern:** Queue-based level-by-level processing. Used for width, right-side view, zigzag.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Binary Tree Level Order Traversal | Medium | https://leetcode.com/problems/binary-tree-level-order-traversal/ |
| - [ ] | Binary Tree Right Side View | Medium | https://leetcode.com/problems/binary-tree-right-side-view/ |
| - [ ] | Binary Tree Zigzag Level Order Traversal | Medium | https://leetcode.com/problems/binary-tree-zigzag-level-order-traversal/ |
| - [ ] | Maximum Width of Binary Tree | Medium | https://leetcode.com/problems/maximum-width-of-binary-tree/ |
| - [ ] | Populating Next Right Pointers in Each Node II | Medium | https://leetcode.com/problems/populating-next-right-pointers-in-each-node-ii/ |

---

### 10. Graph — DFS

**Pattern:** Explore as deep as possible, backtrack. Used for connected components, cycle detection, path finding.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Number of Islands | Medium | https://leetcode.com/problems/number-of-islands/ |
| - [ ] | Clone Graph | Medium | https://leetcode.com/problems/clone-graph/ |
| - [ ] | Pacific Atlantic Water Flow | Medium | https://leetcode.com/problems/pacific-atlantic-water-flow/ |
| - [ ] | All Nodes Distance K in Binary Tree | Medium | https://leetcode.com/problems/all-nodes-distance-k-in-binary-tree/ |
| - [ ] | Surrounded Regions | Medium | https://leetcode.com/problems/surrounded-regions/ |
| - [ ] | Is Graph Bipartite? | Medium | https://leetcode.com/problems/is-graph-bipartite/ |
| - [ ] | Making A Large Island | Hard | https://leetcode.com/problems/making-a-large-island/ |
| - [ ] | Time Needed to Inform All Employees | Medium | https://leetcode.com/problems/time-needed-to-inform-all-employees/ |
| - [ ] | All Paths From Source to Target | Medium | https://leetcode.com/problems/all-paths-from-source-to-target/ |
| - [ ] | Employee Importance | Medium | https://leetcode.com/problems/employee-importance/ |

---

### 11. Graph — BFS

**Pattern:** Level-by-level exploration. Guarantees shortest path in unweighted graphs.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Rotting Oranges | Medium | https://leetcode.com/problems/rotting-oranges/ |
| - [ ] | 01 Matrix | Medium | https://leetcode.com/problems/01-matrix/ |
| - [ ] | Word Ladder | Hard | https://leetcode.com/problems/word-ladder/ |
| - [ ] | Open the Lock | Medium | https://leetcode.com/problems/open-the-lock/ |
| - [ ] | Shortest Path in a Grid with Obstacles Elimination | Hard | https://leetcode.com/problems/shortest-path-in-a-grid-with-obstacles-elimination/ |
| - [ ] | Bus Routes | Hard | https://leetcode.com/problems/bus-routes/ |

---

### 12. Linked Lists (Core + In-place Reversal)

**Pattern:** Pointer manipulation. Reversal uses prev/curr/next. Dummy head simplifies edge cases.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Reverse Linked List | Easy | https://leetcode.com/problems/reverse-linked-list/ |
| - [ ] | Add Two Numbers | Medium | https://leetcode.com/problems/add-two-numbers/ |
| - [ ] | Remove Nth Node From End of List | Medium | https://leetcode.com/problems/remove-nth-node-from-end-of-list/ |
| - [ ] | Copy List with Random Pointer | Medium | https://leetcode.com/problems/copy-list-with-random-pointer/ |
| - [ ] | Reverse Linked List II | Medium | https://leetcode.com/problems/reverse-linked-list-ii/ |
| - [ ] | Reverse Nodes in k-Group | Hard | https://leetcode.com/problems/reverse-nodes-in-k-group/ |
| - [ ] | Merge Two Sorted Lists | Easy | https://leetcode.com/problems/merge-two-sorted-lists/ |
| - [ ] | Swap Nodes in Pairs | Medium | https://leetcode.com/problems/swap-nodes-in-pairs/ |
| - [ ] | Intersection of Two Linked Lists | Easy | https://leetcode.com/problems/intersection-of-two-linked-lists/ |
| - [ ] | Palindrome Linked List | Easy | https://leetcode.com/problems/palindrome-linked-list/ |
| - [ ] | Remove Duplicates from Sorted List II | Medium | https://leetcode.com/problems/remove-duplicates-from-sorted-list-ii/ |
| - [ ] | Partition List | Medium | https://leetcode.com/problems/partition-list/ |
| - [ ] | Rotate List | Medium | https://leetcode.com/problems/rotate-list/ |
| - [ ] | Flatten a Multilevel Doubly Linked List | Medium | https://leetcode.com/problems/flatten-a-multilevel-doubly-linked-list/ |
| - [ ] | Design Linked List | Medium | https://leetcode.com/problems/design-linked-list/ |

---

### 13. Fast and Slow Pointers

**Pattern:** Two pointers at different speeds detect cycles, find midpoints, identify patterns.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Linked List Cycle II | Medium | https://leetcode.com/problems/linked-list-cycle-ii/ |
| - [ ] | Middle of the Linked List | Easy | https://leetcode.com/problems/middle-of-the-linked-list/ |
| - [ ] | Happy Number | Easy | https://leetcode.com/problems/happy-number/ |

---

### 14. Heap / Priority Queue — Top K Elements

**Pattern:** Maintain a heap of size k for running top-k / kth-largest problems.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Top K Frequent Elements | Medium | https://leetcode.com/problems/top-k-frequent-elements/ |
| - [ ] | K Closest Points to Origin | Medium | https://leetcode.com/problems/k-closest-points-to-origin/ |
| - [ ] | Kth Largest Element in a Stream | Easy | https://leetcode.com/problems/kth-largest-element-in-a-stream/ |

---

### 15. 1-D Dynamic Programming

**Pattern:** Current state depends on previous states. Build answer bottom-up or top-down with memo.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | House Robber | Medium | https://leetcode.com/problems/house-robber/ |
| - [ ] | House Robber II | Medium | https://leetcode.com/problems/house-robber-ii/ |
| - [ ] | Climbing Stairs | Easy | https://leetcode.com/problems/climbing-stairs/ |
| - [ ] | Min Cost Climbing Stairs | Easy | https://leetcode.com/problems/min-cost-climbing-stairs/ |

---

## TIER 2 — High ROI (appear in 50-80% of loops)

---

### 16. Backtracking

**Pattern:** Build solution incrementally, abandon (backtrack) when constraints are violated.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Permutations | Medium | https://leetcode.com/problems/permutations/ |
| - [ ] | Subsets | Medium | https://leetcode.com/problems/subsets/ |
| - [ ] | Combination Sum | Medium | https://leetcode.com/problems/combination-sum/ |
| - [ ] | Generate Parentheses | Medium | https://leetcode.com/problems/generate-parentheses/ |
| - [ ] | Letter Combinations of a Phone Number | Medium | https://leetcode.com/problems/letter-combinations-of-a-phone-number/ |
| - [ ] | N-Queens | Hard | https://leetcode.com/problems/n-queens/ |
| - [ ] | Combination Sum II | Medium | https://leetcode.com/problems/combination-sum-ii/ |
| - [ ] | Palindrome Partitioning | Medium | https://leetcode.com/problems/palindrome-partitioning/ |

---

### 17. Intervals

**Pattern:** Sort by start/end, then merge/compare adjacent. Greedy on sorted intervals.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Merge Intervals | Medium | https://leetcode.com/problems/merge-intervals/ |
| - [ ] | Insert Interval | Medium | https://leetcode.com/problems/insert-interval/ |
| - [ ] | Non-overlapping Intervals | Medium | https://leetcode.com/problems/non-overlapping-intervals/ |
| - [ ] | Minimum Number of Arrows to Burst Balloons | Medium | https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/ |
| - [ ] | Maximum Number of Events That Can Be Attended | Medium | https://leetcode.com/problems/maximum-number-of-events-that-can-be-attended/ |

---

### 18. Prefix Sum

**Pattern:** Precompute cumulative sums. Subarray sum = prefix[j] - prefix[i]. Hash map for target sum.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Subarray Sum Equals K | Medium | https://leetcode.com/problems/subarray-sum-equals-k/ |
| - [ ] | Continuous Subarray Sum | Medium | https://leetcode.com/problems/continuous-subarray-sum/ |
| - [ ] | Contiguous Array | Medium | https://leetcode.com/problems/contiguous-array/ |
| - [ ] | Subarray Sums Divisible by K | Medium | https://leetcode.com/problems/subarray-sums-divisible-by-k/ |
| - [ ] | Range Sum Query - Immutable | Easy | https://leetcode.com/problems/range-sum-query-immutable/ |

---

### 19. Monotonic Stack

**Pattern:** Stack maintaining increasing/decreasing order. Finds next greater/smaller element in O(n).

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Daily Temperatures | Medium | https://leetcode.com/problems/daily-temperatures/ |
| - [ ] | Largest Rectangle in Histogram | Hard | https://leetcode.com/problems/largest-rectangle-in-histogram/ |
| - [ ] | 132 Pattern | Medium | https://leetcode.com/problems/132-pattern/ |
| - [ ] | Number of Visible People in a Queue | Hard | https://leetcode.com/problems/number-of-visible-people-in-a-queue/ |
| - [ ] | Online Stock Span | Medium | https://leetcode.com/problems/online-stock-span/ |
| - [ ] | Next Greater Element I | Easy | https://leetcode.com/problems/next-greater-element-i/ |

---

### 20. Greedy

**Pattern:** Make locally optimal choice at each step. Prove it leads to global optimum (exchange argument).

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Task Scheduler | Medium | https://leetcode.com/problems/task-scheduler/ |
| - [ ] | Jump Game II | Medium | https://leetcode.com/problems/jump-game-ii/ |
| - [ ] | Gas Station | Medium | https://leetcode.com/problems/gas-station/ |
| - [ ] | Candy | Hard | https://leetcode.com/problems/candy/ |
| - [ ] | Minimum Add to Make Parentheses Valid | Medium | https://leetcode.com/problems/minimum-add-to-make-parentheses-valid/ |
| - [ ] | Minimum Cost to Hire K Workers | Hard | https://leetcode.com/problems/minimum-cost-to-hire-k-workers/ |
| - [ ] | Minimum Number of Refueling Stops | Hard | https://leetcode.com/problems/minimum-number-of-refueling-stops/ |

---

### 21. String DP

**Pattern:** 2D table on two strings or one string's subranges. LCS, edit distance, palindrome patterns.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Longest Common Subsequence | Medium | https://leetcode.com/problems/longest-common-subsequence/ |
| - [ ] | Edit Distance | Medium | https://leetcode.com/problems/edit-distance/ |
| - [ ] | Word Break | Medium | https://leetcode.com/problems/word-break/ |
| - [ ] | Decode Ways | Medium | https://leetcode.com/problems/decode-ways/ |
| - [ ] | Longest Palindromic Subsequence | Medium | https://leetcode.com/problems/longest-palindromic-subsequence/ |
| - [ ] | Wildcard Matching | Hard | https://leetcode.com/problems/wildcard-matching/ |
| - [ ] | Interleaving String | Medium | https://leetcode.com/problems/interleaving-string/ |
| - [ ] | Distinct Subsequences | Hard | https://leetcode.com/problems/distinct-subsequences/ |
| - [ ] | Palindrome Partitioning II | Hard | https://leetcode.com/problems/palindrome-partitioning-ii/ |

---

### 22. Topological Sort

**Pattern:** Process nodes with no incoming edges first (BFS/Kahn's). Detects cycles in DAGs.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Course Schedule II | Medium | https://leetcode.com/problems/course-schedule-ii/ |
| - [ ] | Find Eventual Safe States | Medium | https://leetcode.com/problems/find-eventual-safe-states/ |
| - [ ] | Minimum Height Trees | Medium | https://leetcode.com/problems/minimum-height-trees/ |
| - [ ] | Sort Items by Groups Respecting Dependencies | Hard | https://leetcode.com/problems/sort-items-by-groups-respecting-dependencies/ |

---

### 23. Data Structure Design

**Pattern:** Combine multiple data structures (hash map + linked list, etc.) for O(1) operations.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | LRU Cache | Medium | https://leetcode.com/problems/lru-cache/ |
| - [ ] | Insert Delete GetRandom O(1) | Medium | https://leetcode.com/problems/insert-delete-getrandom-o1/ |
| - [ ] | Time Based Key-Value Store | Medium | https://leetcode.com/problems/time-based-key-value-store/ |
| - [ ] | Design Twitter | Medium | https://leetcode.com/problems/design-twitter/ |
| - [ ] | Maximum Frequency Stack | Hard | https://leetcode.com/problems/maximum-frequency-stack/ |
| - [ ] | Snapshot Array | Medium | https://leetcode.com/problems/snapshot-array/ |
| - [ ] | Design Browser History | Medium | https://leetcode.com/problems/design-browser-history/ |
| - [ ] | Design a Food Rating System | Medium | https://leetcode.com/problems/design-a-food-rating-system/ |

---

### 24. Trie

**Pattern:** Tree of characters for prefix-based search. Each node has up to 26 children.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Implement Trie (Prefix Tree) | Medium | https://leetcode.com/problems/implement-trie-prefix-tree/ |
| - [ ] | Design Add and Search Words Data Structure | Medium | https://leetcode.com/problems/design-add-and-search-words-data-structure/ |
| - [ ] | Word Search II | Hard | https://leetcode.com/problems/word-search-ii/ |
| - [ ] | Search Suggestions System | Medium | https://leetcode.com/problems/search-suggestions-system/ |
| - [ ] | Maximum XOR of Two Numbers in an Array | Medium | https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/ |
| - [ ] | Longest Word in Dictionary | Medium | https://leetcode.com/problems/longest-word-in-dictionary/ |

---

### 25. Union Find

**Pattern:** Disjoint set with union-by-rank + path compression. O(α(n)) per operation. Connected components.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Number of Provinces | Medium | https://leetcode.com/problems/number-of-provinces/ |
| - [ ] | Accounts Merge | Medium | https://leetcode.com/problems/accounts-merge/ |
| - [ ] | Redundant Connection | Medium | https://leetcode.com/problems/redundant-connection/ |
| - [ ] | Minimize Malware Spread | Hard | https://leetcode.com/problems/minimize-malware-spread/ |

---

### 26. Kadane's Algorithm

**Pattern:** Track running max/min subarray sum ending at current index. Reset when sum goes negative.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Maximum Subarray | Medium | https://leetcode.com/problems/maximum-subarray/ |
| - [ ] | Maximum Product Subarray | Medium | https://leetcode.com/problems/maximum-product-subarray/ |
| - [ ] | Maximum Sum Circular Subarray | Medium | https://leetcode.com/problems/maximum-sum-circular-subarray/ |
| - [ ] | Best Sightseeing Pair | Medium | https://leetcode.com/problems/best-sightseeing-pair/ |

---

### 27. Two Heaps

**Pattern:** Max-heap for lower half, min-heap for upper half. Maintains running median.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Find Median from Data Stream | Hard | https://leetcode.com/problems/find-median-from-data-stream/ |
| - [ ] | IPO | Hard | https://leetcode.com/problems/ipo/ |
| - [ ] | Sliding Window Median | Hard | https://leetcode.com/problems/sliding-window-median/ |

---

## TIER 3 — Medium ROI (appear in 20-50% of loops)

---

### 28. 2D Grid DP

**Pattern:** DP on grid with right/down moves. Multi-path = simultaneous walkers (see Cherry Pickup notes).

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Unique Paths II | Medium | https://leetcode.com/problems/unique-paths-ii/ |
| - [ ] | Minimum Path Sum | Medium | https://leetcode.com/problems/minimum-path-sum/ |
| - [ ] | Longest Increasing Path in a Matrix | Hard | https://leetcode.com/problems/longest-increasing-path-in-a-matrix/ |
| - [ ] | Cherry Pickup | Hard | https://leetcode.com/problems/cherry-pickup/ |
| - [ ] | Maximum Profit in Job Scheduling | Hard | https://leetcode.com/problems/maximum-profit-in-job-scheduling/ |
| - [ ] | Triangle | Medium | https://leetcode.com/problems/triangle/ |
| - [ ] | Count Square Submatrices with All Ones | Medium | https://leetcode.com/problems/count-square-submatrices-with-all-ones/ |
| - [ ] | Maximum Number of Points with Cost | Medium | https://leetcode.com/problems/maximum-number-of-points-with-cost/ |
| - [ ] | Burst Balloons | Hard | https://leetcode.com/problems/burst-balloons/ |

---

### 29. LIS (Longest Increasing Subsequence)

**Pattern:** O(n log n) with patience sort (binary search on tails array).

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Longest Increasing Subsequence | Medium | https://leetcode.com/problems/longest-increasing-subsequence/ |
| - [ ] | Russian Doll Envelopes | Hard | https://leetcode.com/problems/russian-doll-envelopes/ |
| - [ ] | Number of Longest Increasing Subsequence | Medium | https://leetcode.com/problems/number-of-longest-increasing-subsequence/ |

---

### 30. 0/1 Knapsack

**Pattern:** Pick or skip each item. dp[i][w] = best value using first i items with capacity w.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Partition Equal Subset Sum | Medium | https://leetcode.com/problems/partition-equal-subset-sum/ |
| - [ ] | Target Sum | Medium | https://leetcode.com/problems/target-sum/ |
| - [ ] | Last Stone Weight II | Medium | https://leetcode.com/problems/last-stone-weight-ii/ |

---

### 31. Unbounded Knapsack

**Pattern:** Same as 0/1 but items can be reused. Inner loop goes forward instead of backward.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Coin Change | Medium | https://leetcode.com/problems/coin-change/ |
| - [ ] | Coin Change II | Medium | https://leetcode.com/problems/coin-change-ii/ |
| - [ ] | Perfect Squares | Medium | https://leetcode.com/problems/perfect-squares/ |

---

### 32. Matrix (2D Array)

**Pattern:** Simulation and in-place tricks on 2D grids. Layer-by-layer, direction arrays.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Spiral Matrix | Medium | https://leetcode.com/problems/spiral-matrix/ |
| - [ ] | Rotate Image | Medium | https://leetcode.com/problems/rotate-image/ |
| - [ ] | Set Matrix Zeroes | Medium | https://leetcode.com/problems/set-matrix-zeroes/ |
| - [ ] | Valid Sudoku | Medium | https://leetcode.com/problems/valid-sudoku/ |
| - [ ] | Game of Life | Medium | https://leetcode.com/problems/game-of-life/ |

---

### 33. K-Way Merge

**Pattern:** Min-heap of k pointers, each pointing into a sorted list. Pop smallest, push its next.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Merge k Sorted Lists | Hard | https://leetcode.com/problems/merge-k-sorted-lists/ |
| - [ ] | Kth Smallest Element in a Sorted Matrix | Medium | https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/ |
| - [ ] | Find K Pairs with Smallest Sums | Medium | https://leetcode.com/problems/find-k-pairs-with-smallest-sums/ |
| - [ ] | Smallest Range Covering Elements from K Lists | Hard | https://leetcode.com/problems/smallest-range-covering-elements-from-k-lists/ |

---

### 34. Strings

**Pattern:** Character manipulation, palindrome checks, prefix tricks.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Valid Palindrome | Easy | https://leetcode.com/problems/valid-palindrome/ |
| - [ ] | Reverse Words in a String | Medium | https://leetcode.com/problems/reverse-words-in-a-string/ |
| - [ ] | Longest Common Prefix | Easy | https://leetcode.com/problems/longest-common-prefix/ |
| - [ ] | Zigzag Conversion | Medium | https://leetcode.com/problems/zigzag-conversion/ |
| - [ ] | Is Subsequence | Easy | https://leetcode.com/problems/is-subsequence/ |
| - [ ] | Guess the Word | Hard | https://leetcode.com/problems/guess-the-word/ |

---

### 35. Shortest Path

**Pattern:** Dijkstra (weighted, no negative), Bellman-Ford (negative edges), BFS (unweighted).

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Network Delay Time | Medium | https://leetcode.com/problems/network-delay-time/ |
| - [ ] | Cheapest Flights Within K Stops | Medium | https://leetcode.com/problems/cheapest-flights-within-k-stops/ |
| - [ ] | Path With Minimum Effort | Medium | https://leetcode.com/problems/path-with-minimum-effort/ |
| - [ ] | Path with Maximum Probability | Medium | https://leetcode.com/problems/path-with-maximum-probability/ |
| - [ ] | Swim in Rising Water | Hard | https://leetcode.com/problems/swim-in-rising-water/ |

---

### 36. Tree / Graph DP

**Pattern:** DP on tree using post-order DFS. State at node depends on children's states.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | House Robber III | Medium | https://leetcode.com/problems/house-robber-iii/ |
| - [ ] | Binary Tree Cameras | Hard | https://leetcode.com/problems/binary-tree-cameras/ |
| - [ ] | Sum of Distances in Tree | Hard | https://leetcode.com/problems/sum-of-distances-in-tree/ |
| - [ ] | Number of Ways to Arrive at Destination | Medium | https://leetcode.com/problems/number-of-ways-to-arrive-at-destination/ |
| - [ ] | Unique Binary Search Trees II | Medium | https://leetcode.com/problems/unique-binary-search-trees-ii/ |

---

### 37. Heaps (General)

**Pattern:** Priority queue for scheduling, simulation problems. Process by priority.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Furthest Building You Can Reach | Medium | https://leetcode.com/problems/furthest-building-you-can-reach/ |
| - [ ] | Single-Threaded CPU | Medium | https://leetcode.com/problems/single-threaded-cpu/ |
| - [ ] | Process Tasks Using Servers | Medium | https://leetcode.com/problems/process-tasks-using-servers/ |

---

### 38. Bit Manipulation

**Pattern:** XOR cancels pairs, AND/OR for masks, bit shifts for powers of 2.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Single Number | Easy | https://leetcode.com/problems/single-number/ |
| - [ ] | Single Number III | Medium | https://leetcode.com/problems/single-number-iii/ |
| - [ ] | Sum of Two Integers | Medium | https://leetcode.com/problems/sum-of-two-integers/ |
| - [ ] | Counting Bits | Easy | https://leetcode.com/problems/counting-bits/ |
| - [ ] | Bitwise AND of Numbers Range | Medium | https://leetcode.com/problems/bitwise-and-of-numbers-range/ |
| - [ ] | Number of 1 Bits | Easy | https://leetcode.com/problems/number-of-1-bits/ |
| - [ ] | Reverse Bits | Easy | https://leetcode.com/problems/reverse-bits/ |

---

### 39. State Machine DP

**Pattern:** Define states (holding, not holding, cooldown) and transitions between them.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Best Time to Buy and Sell Stock with Cooldown | Medium | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/ |
| - [ ] | Best Time to Buy and Sell Stock III | Hard | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/ |

---

### 40. BST / Ordered Set

**Pattern:** Self-balancing BST or sorted container for range queries, floor/ceiling.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Stock Price Fluctuation | Medium | https://leetcode.com/problems/stock-price-fluctuation/ |
| - [ ] | My Calendar I | Medium | https://leetcode.com/problems/my-calendar-i/ |
| - [ ] | My Calendar II | Medium | https://leetcode.com/problems/my-calendar-ii/ |
| - [ ] | Trim a Binary Search Tree | Medium | https://leetcode.com/problems/trim-a-binary-search-tree/ |

---

## TIER 4 — Niche (rarely asked, do last)

---

### 41. Monotonic Queue

**Pattern:** Deque maintaining max/min over sliding window in O(1) amortized.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Sliding Window Maximum | Hard | https://leetcode.com/problems/sliding-window-maximum/ |
| - [ ] | Jump Game VI | Medium | https://leetcode.com/problems/jump-game-vi/ |
| - [ ] | Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit | Medium | https://leetcode.com/problems/longest-continuous-subarray-with-absolute-diff-less-than-or-equal-to-limit/ |
| - [ ] | Max Value of Equation | Hard | https://leetcode.com/problems/max-value-of-equation/ |

---

### 42. Recursion / Divide and Conquer

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Pow(x, n) | Medium | https://leetcode.com/problems/powx-n/ |
| - [ ] | Decode String | Medium | https://leetcode.com/problems/decode-string/ |
| - [ ] | Convert Sorted List to Binary Search Tree | Medium | https://leetcode.com/problems/convert-sorted-list-to-binary-search-tree/ |
| - [ ] | Construct Quad Tree | Medium | https://leetcode.com/problems/construct-quad-tree/ |
| - [ ] | Maximum Binary Tree | Medium | https://leetcode.com/problems/maximum-binary-tree/ |

---

### 43. Sorting (Merge Sort / QuickSelect)

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Kth Largest Element in an Array | Medium | https://leetcode.com/problems/kth-largest-element-in-an-array/ |
| - [ ] | Sort Colors | Medium | https://leetcode.com/problems/sort-colors/ |
| - [ ] | Sort List | Medium | https://leetcode.com/problems/sort-list/ |
| - [ ] | Reverse Pairs | Hard | https://leetcode.com/problems/reverse-pairs/ |

---

### 44. Bucket Sort

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Top K Frequent Words | Medium | https://leetcode.com/problems/top-k-frequent-words/ |
| - [ ] | Sort Characters By Frequency | Medium | https://leetcode.com/problems/sort-characters-by-frequency/ |
| - [ ] | Maximum Gap | Medium | https://leetcode.com/problems/maximum-gap/ |

---

### 45. Queues

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Reveal Cards In Increasing Order | Medium | https://leetcode.com/problems/reveal-cards-in-increasing-order/ |
| - [ ] | Number of Recent Calls | Easy | https://leetcode.com/problems/number-of-recent-calls/ |
| - [ ] | Time Needed to Buy Tickets | Easy | https://leetcode.com/problems/time-needed-to-buy-tickets/ |

---

### 46. Maths / Geometry

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Reverse Integer | Medium | https://leetcode.com/problems/reverse-integer/ |
| - [ ] | Max Points on a Line | Hard | https://leetcode.com/problems/max-points-on-a-line/ |
| - [ ] | Factorial Trailing Zeroes | Medium | https://leetcode.com/problems/factorial-trailing-zeroes/ |
| - [ ] | Palindrome Number | Easy | https://leetcode.com/problems/palindrome-number/ |
| - [ ] | Valid Square | Medium | https://leetcode.com/problems/valid-square/ |
| - [ ] | Minimum Area Rectangle II | Medium | https://leetcode.com/problems/minimum-area-rectangle-ii/ |

---

### 47. Bitmask DP

**Pattern:** Use bitmask to represent subset of items. dp[mask] = best answer using items in mask.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Shortest Path Visiting All Nodes | Hard | https://leetcode.com/problems/shortest-path-visiting-all-nodes/ |
| - [ ] | Minimum Number of Work Sessions to Finish the Tasks | Medium | https://leetcode.com/problems/minimum-number-of-work-sessions-to-finish-the-tasks/ |
| - [ ] | Fair Distribution of Cookies | Medium | https://leetcode.com/problems/fair-distribution-of-cookies/ |

---

### 48. Digit DP

**Pattern:** Count numbers up to N with digit constraints. State: position, tight, started.

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Number of Digit One | Hard | https://leetcode.com/problems/number-of-digit-one/ |
| - [ ] | Numbers At Most N Given Digit Set | Hard | https://leetcode.com/problems/numbers-at-most-n-given-digit-set/ |
| - [ ] | Count Numbers with Unique Digits | Medium | https://leetcode.com/problems/count-numbers-with-unique-digits/ |

---

### 49. Probability DP

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Knight Probability in Chessboard | Medium | https://leetcode.com/problems/knight-probability-in-chessboard/ |
| - [ ] | New 21 Game | Medium | https://leetcode.com/problems/new-21-game/ |
| - [ ] | Soup Servings | Medium | https://leetcode.com/problems/soup-servings/ |

---

### 50. String Matching

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Shortest Palindrome | Hard | https://leetcode.com/problems/shortest-palindrome/ |
| - [ ] | Repeated String Match | Medium | https://leetcode.com/problems/repeated-string-match/ |
| - [ ] | Longest Duplicate Substring | Hard | https://leetcode.com/problems/longest-duplicate-substring/ |

---

### 51. BIT / Segment Tree

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Range Sum Query - Mutable | Medium | https://leetcode.com/problems/range-sum-query-mutable/ |
| - [ ] | Count of Smaller Numbers After Self | Hard | https://leetcode.com/problems/count-of-smaller-numbers-after-self/ |

---

### 52. Line Sweep

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | The Skyline Problem | Hard | https://leetcode.com/problems/the-skyline-problem/ |
| - [ ] | Minimum Interval to Include Each Query | Hard | https://leetcode.com/problems/minimum-interval-to-include-each-query/ |

---

### 53. Minimum Spanning Tree

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Min Cost to Connect All Points | Medium | https://leetcode.com/problems/min-cost-to-connect-all-points/ |

---

### 54. Eulerian Circuit

| # | Problem | Difficulty | Link |
|---|---------|-----------|------|
| - [ ] | Reconstruct Itinerary | Hard | https://leetcode.com/problems/reconstruct-itinerary/ |
| - [ ] | Cracking the Safe | Hard | https://leetcode.com/problems/cracking-the-safe/ |

---

## Quick Stats

| Tier | Topics | Problems | Time Estimate |
|------|--------|----------|---------------|
| Tier 1 | 15 topics | ~115 problems | 4-6 weeks |
| Tier 2 | 12 topics | ~75 problems | 3-4 weeks |
| Tier 3 | 12 topics | ~55 problems | 2-3 weeks |
| Tier 4 | 14 topics | ~35 problems | 1-2 weeks |
| **Total** | **53 topics** | **~280 problems** | **10-15 weeks** |

If short on time, finish all of Tier 1 and top half of Tier 2. That covers 90% of what you'll see.
