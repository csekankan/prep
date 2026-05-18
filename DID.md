# Designing Data-Intensive Applications — Key Concepts

> Martin Kleppmann's comprehensive guide to the principles, trade-offs, and practical considerations behind modern data systems.

---

## Part I: Foundations of Data Systems

---

### Chapter 1: Reliable, Scalable, and Maintainable Applications

#### Three Core Concerns

| Concern | Definition |
|---------|-----------|
| **Reliability** | System continues to work correctly even when things go wrong (faults) |
| **Scalability** | System can handle growth (data volume, traffic, complexity) |
| **Maintainability** | People can work on the system productively over time |

#### Reliability

**Faults vs. Failures:**
- **Fault**: One component deviating from spec (partial)
- **Failure**: System as a whole stops providing required service (total)

**Types of Faults:**

```
1. Hardware Faults
   - Disk failure (MTTF ~10-50 years)
   - RAM errors, power grid blackouts
   - Solution: Redundancy (RAID, dual power, hot-swap CPUs)
   - Modern trend: Software fault-tolerance over hardware redundancy

2. Software Errors
   - Systematic faults (bugs triggered by unusual inputs)
   - Runaway processes consuming shared resources
   - Cascading failures
   - Solution: Careful thinking about assumptions, thorough testing,
     process isolation, crash-and-restart, monitoring

3. Human Errors
   - Configuration errors are the leading cause of outages
   - Solutions:
     • Design systems that minimize opportunities for error
     • Decouple places where mistakes are made from places that cause failures (sandbox environments)
     • Test thoroughly at all levels (unit, integration, E2E)
     • Allow quick rollback
     • Set up detailed monitoring (telemetry)
```

#### Scalability

**Describing Load — Load Parameters:**
- Requests per second (web server)
- Read/write ratio (database)
- Simultaneously active users (chat)
- Cache hit rate

**Twitter Fan-out Example:**
```
Approach 1: Pull model (query on read)
  - Post tweet → insert into global tweets table
  - Home timeline → JOIN tweets with follows at read time
  - Problem: Heavy reads (300k reads/sec vs 4.6k writes/sec)

Approach 2: Push model (fan-out on write)
  - Post tweet → write to each follower's cached timeline
  - Home timeline → simple cache read
  - Problem: Celebrities with 30M+ followers = huge fan-out

Approach 3: Hybrid
  - Regular users → fan-out on write
  - Celebrities → pulled at read time and merged
```

**Describing Performance:**
- **Throughput**: Number of records processed per second (batch)
- **Response time**: Time between client sending request and receiving response (online)

**Latency vs. Response Time:**
- Response time = service time + network delays + queueing delays
- Latency = time request is waiting to be handled

**Percentiles (more useful than averages):**
```
p50 (median)  — Half the requests are faster than this
p95           — 95% of requests are faster
p99           — 99% of requests are faster
p999          — 99.9% of requests are faster (tail latency)

Why tail latencies matter:
- Often the customers with most data (most valuable) experience the worst latencies
- Amazon: 100ms increase in response time → 1% drop in sales
- Amazon internal: p999 response time requirement
```

**Approaches to Scaling:**
```
Vertical Scaling (Scale Up):
  - More powerful machine
  - Simpler but has limits and is expensive

Horizontal Scaling (Scale Out):
  - Distribute across multiple machines (shared-nothing architecture)
  - More complex but necessary at scale

Elastic Scaling:
  - Automatically add resources when load increases
  - Useful for unpredictable load patterns
```

#### Maintainability

Three design principles:

1. **Operability** — Make it easy for ops teams to keep the system running
   - Good monitoring, automation support, documentation
   - Avoid dependency on individual machines
   - Good default behavior with override ability

2. **Simplicity** — Make it easy for new engineers to understand
   - Remove accidental complexity (not essential complexity)
   - Good abstractions hide implementation details
   - Clean interfaces between components

3. **Evolvability** — Make it easy to make changes (extensibility/plasticity)
   - Requirements always change
   - Agile working patterns, TDD, refactoring
   - Simple and well-abstracted systems are easier to modify

---

### Chapter 2: Data Models and Query Languages

#### Relational Model vs. Document Model

**Relational Model (SQL):**
- Data organized in relations (tables), each is a collection of tuples (rows)
- Schema-on-write (enforced at write time)
- Strong at joins, many-to-many relationships
- Good for: financial transactions, highly interconnected data

**Document Model (NoSQL):**
- Data stored as self-contained documents (JSON/BSON)
- Schema-on-read (interpreted at read time)
- Better locality (entire document fetched at once)
- Good for: one-to-many relationships, data that comes as a document

**Key Differences:**

```
                    Relational              Document
Schema             Schema-on-write         Schema-on-read
Joins              Excellent               Poor (denormalize or app-level)
Many-to-many       Natural                 Awkward
Data locality      Scattered (multiple     Good (single document)
                   tables, needs joins)
Flexibility        Rigid schema            Flexible structure
Access pattern     Arbitrary queries       Known access patterns
```

**The Object-Relational Mismatch (Impedance Mismatch):**
- Application code is in objects, but relational DB is in rows/columns
- ORMs reduce but don't eliminate the mismatch
- Document model is closer to application data structures

**When Document Model Wins:**
- Tree-structured data (one-to-many)
- Entire document loaded at once
- Schema flexibility needed
- Data locality matters for performance

**When Relational Model Wins:**
- Many-to-many relationships
- Need for joins
- Need to access parts of a document frequently
- Need for strong consistency guarantees

#### Graph-Like Data Models

Best for data with complex many-to-many relationships.

**Property Graph Model (Neo4j, etc.):**
```
Vertex (node):
  - Unique ID
  - Set of outgoing edges
  - Set of incoming edges
  - Collection of properties (key-value pairs)

Edge (relationship):
  - Unique ID
  - Start vertex (tail)
  - End vertex (head)
  - Label (type of relationship)
  - Collection of properties
```

**Triple-Store Model (subject, predicate, object):**
```
(Jim, likes, bananas)
(Jim, worksAt, Google)
(Google, locatedIn, California)
```

#### Query Languages

**Declarative vs. Imperative:**
```
Imperative (how to get data):
  function getSharks() {
    var sharks = [];
    for (var i = 0; i < animals.length; i++) {
      if (animals[i].family === "Sharks") {
        sharks.push(animals[i]);
      }
    }
    return sharks;
  }

Declarative (what data you want):
  SELECT * FROM animals WHERE family = 'Sharks';

Advantages of Declarative:
  - Concise, easier to work with
  - Hides implementation details
  - Database can optimize execution
  - Lends itself to parallel execution
```

**MapReduce:**
- Neither fully declarative nor fully imperative
- Logic expressed with snippets of code called repeatedly by the framework
- Used in MongoDB for aggregation (but aggregation pipeline is more common now)

---

### Chapter 3: Storage and Retrieval

#### Log-Structured Storage Engines

**Hash Indexes:**
```
- In-memory hash map: key → byte offset in data file
- Writes: append to file, update hash map
- Reads: look up offset in hash map, read from file
- Compaction: merge segment files, discard old values

Limitations:
  - Hash table must fit in memory
  - Range queries are not efficient
  
Used by: Bitcask (Riak's default storage engine)
```

**SSTables and LSM-Trees:**

```
SSTable (Sorted String Table):
  - Key-value pairs sorted by key within each segment
  - Advantages over hash-indexed segments:
    • Merging is efficient (like merge sort)
    • No need to keep all keys in memory (sparse index)
    • Range queries are efficient

LSM-Tree (Log-Structured Merge-Tree):
  1. Write comes in → add to in-memory balanced tree (memtable)
  2. When memtable exceeds threshold → flush to disk as SSTable
  3. Read request → check memtable → check most recent SSTable → older SSTables
  4. Background: merge and compact SSTables periodically

Optimizations:
  - Bloom filters: quickly tell if key does NOT exist (avoid unnecessary disk reads)
  - Size-tiered compaction: newer SSTables merged into older, larger ones
  - Leveled compaction: key range split into smaller SSTables, moved level-by-level

Used by: LevelDB, RocksDB, Cassandra, HBase, Lucene (term dictionary)
```

**LSM-Tree Advantages:**
- Higher write throughput (sequential writes)
- Can be compressed better (lower storage overhead)
- Lower write amplification than B-trees (sometimes)

**LSM-Tree Disadvantages:**
- Compaction can interfere with reads/writes (resource contention)
- Multiple copies of same key across levels
- Response time less predictable (compaction spikes)

#### Page-Oriented Storage Engines (B-Trees)

```
B-Tree Structure:
  - Fixed-size blocks/pages (typically 4KB)
  - Each page identified by address (like a pointer)
  - One page is the root
  - Pages contain keys and references to child pages
  - Leaf pages contain values (or references to values)
  - Branching factor: typically several hundred

Write Operation:
  1. Find the leaf page containing the key
  2. Update value in place (overwrite the page on disk)
  3. If page is full → split into two half-full pages, update parent

Crash Recovery:
  - Write-ahead log (WAL/redo log): every modification written to append-only log before page modification
  - Used for recovery after crash

Optimizations:
  - Copy-on-write instead of WAL (LMDB)
  - Abbreviated keys in internal pages (higher branching factor)
  - Leaf pages stored in sequential order on disk
  - Sibling page pointers
  - Fractal trees (borrowing LSM ideas)
```

**B-Tree vs. LSM-Tree:**

```
                    B-Tree                  LSM-Tree
Write pattern      Random I/O              Sequential I/O
Read performance   Predictable             May need multiple lookups
Write              Overwrite in place       Append-only
amplification      
Space              Some fragmentation       No fragmentation (compaction)
Concurrency        Latches (fine-grained    Simpler (immutable segments)
                   locks)
Predictability     More predictable         Compaction can cause spikes
Maturity           Decades of production    Newer, still evolving
                   use
```

#### Other Indexing Structures

**Secondary Indexes:**
- Not unique (multiple rows can have same key)
- Solutions: make value a list of row IDs, or append row ID to key

**Storing Values within the Index:**
```
Clustered Index:
  - Stores the actual row within the index
  - Only one per table (defines physical storage order)
  - Example: InnoDB primary key

Non-clustered Index:
  - Stores reference (heap file location) in the index
  - Multiple per table

Covering Index (index with included columns):
  - Stores some columns within the index
  - Can answer some queries from index alone (index-only scan)
```

**Multi-column Indexes:**
```
Concatenated Index:
  - Combines multiple fields into one key (in defined order)
  - (lastname, firstname) → good for (lastname) or (lastname, firstname)
  - NOT good for (firstname) alone

Multi-dimensional Index:
  - R-trees for geospatial data
  - Needed for: "find all restaurants within 2km"
  - Standard B-tree can't efficiently answer multi-dimensional range queries
```

**Full-Text Search and Fuzzy Indexes:**
- Lucene: in-memory index is a finite state automaton (similar to trie)
- Supports edit distance searches
- SSTable-like structure for the term dictionary

#### Transaction Processing vs. Analytics (OLTP vs. OLAP)

```
                    OLTP                    OLAP
Main read          Small number of          Aggregate over large
pattern            records per query        number of records
Main write         Random-access, low-      Bulk import (ETL) or
pattern            latency writes           event stream
Used by            End user via web app     Internal analyst for
                                            decision support
Data represents    Latest state of data     History of events
Dataset size       GB to TB                 TB to PB
Bottleneck         Disk seek time           Disk bandwidth
```

#### Column-Oriented Storage

```
Why column storage for analytics:
  - Queries often access few columns but many rows
  - Row storage: must read entire row even if you need 3 out of 100 columns
  - Column storage: only read the columns you need

How it works:
  - Store all values from each column together
  - Each column file contains values in the same row order
  - To reconstruct row: take nth entry from each column file

Column Compression:
  - Bitmap encoding: one bitmap per distinct value
    • Column with n distinct values → n bitmaps
    • Bitmap i has 1 where value equals i
    • Very effective when n is small relative to row count
  
  - Run-length encoding on bitmaps:
    • Many zeros in a row → compress efficiently
    
  - Vectorized processing:
    • Compressed column data fits in CPU L1 cache
    • AND/OR operations on bitmaps = efficient filtering

Sort Order in Column Storage:
  - Can't sort each column independently (would lose row correspondence)
  - Choose a sort key (e.g., date_key, product_key)
  - First sort column has excellent compression (run-length encoding)
  - Multiple sort orders: store data redundantly sorted different ways (like multiple indexes)

Materialized Views and Data Cubes:
  - Precomputed aggregates
  - Data cube: grid of aggregates by combinations of dimensions
  - Trade-off: faster queries vs. less flexibility (only predefined aggregates)
```

#### Data Warehousing

```
ETL (Extract-Transform-Load):
  - Extract data from OLTP databases
  - Transform into analysis-friendly schema
  - Load into data warehouse

Star Schema (Dimensional Modeling):
  - Fact table: central table with events (one row per event)
    • Contains foreign keys to dimension tables
    • Contains measures (numeric values for analysis)
  - Dimension tables: who, what, where, when, how, why
    • Relatively small, wide tables
    • Human-readable attributes

  Example:
    fact_sales: date_key, product_key, store_key, qty, revenue
    dim_date: date_key, day, month, year, holiday_flag
    dim_product: product_key, name, category, brand
    dim_store: store_key, name, city, state

Snowflake Schema:
  - Dimensions further normalized into sub-dimensions
  - More normalized but harder to work with
  - Star schema generally preferred by analysts
```

---

### Chapter 4: Encoding and Evolution

#### Formats for Encoding Data

**Language-Specific Formats:**
```
Java: java.io.Serializable
Python: pickle
Ruby: Marshal

Problems:
  - Tied to one language
  - Security issues (arbitrary object instantiation)
  - Versioning/compatibility often an afterthought
  - Efficiency often poor

Verdict: Avoid for anything beyond transient purposes
```

**JSON, XML, CSV:**
```
Advantages:
  - Human-readable
  - Widely supported
  - Good for interchange

Problems:
  - JSON: no distinction between integers and floats
  - JSON: no binary strings (must base64 encode)
  - XML: verbose, complex
  - CSV: no schema, ambiguous escaping
  - No schema enforcement (JSON Schema / XML Schema are optional)
  - Large encoding size (field names repeated)
```

**Binary Encoding (Thrift, Protocol Buffers, Avro):**

```
Protocol Buffers / Thrift:
  - Schema definition with numbered field tags
  - Binary encoding uses field tag numbers (not names)
  - Very compact
  
  message Person {
    required string user_name = 1;
    optional int64 favorite_number = 2;
    repeated string interests = 3;
  }

  Schema Evolution Rules:
    - Can add new fields (with new tag numbers) — old code ignores unknown tags
    - Can't rename field tags (would break compatibility)
    - Can remove optional fields (can't reuse their tag number)
    - Can't change required → optional (breaks old readers)

Avro:
  - Schema included or referenced in data
  - No field tag numbers — uses field position matching
  - Writer's schema and reader's schema don't have to be identical
  - Schema resolution: match fields by name
  
  Schema Evolution:
    - Add/remove fields with defaults
    - Writer's schema included with every record (or schema registry)
    - Very good for Hadoop (schema stored once in file header)
    - Dynamic schema generation (e.g., dump database to file — schema generated from DB schema)
```

**Comparison of Binary Encodings:**
```
                    Protobuf/Thrift     Avro
Field identification Tag numbers        Field names (matched at read)
Schema in data      No (just tags)      Yes (or registry reference)
Dynamic schemas     Harder              Natural fit
Code generation     Required            Optional
Compact             Yes                 Slightly more compact
Hadoop ecosystem    Less common         Standard
```

#### Modes of Dataflow

**1. Dataflow Through Databases:**
```
- Writing to database = encoding (future self is the reader)
- Multiple app versions may write/read same database
- Forward compatibility needed: old code must not destroy new fields
- Data outlives code: database may contain values written by very old code

Migration concern:
  - Schema changes (ALTER TABLE) may rewrite entire table (expensive)
  - Or: add column with NULL default, fill on read (schema-on-read)
  - Most relational DBs allow adding nullable columns without rewrite
```

**2. Dataflow Through Services (REST and RPC):**
```
REST:
  - Based on HTTP, uses URLs for resources
  - Simple, widely supported, good for public APIs
  - OpenAPI/Swagger for documentation

RPC (Remote Procedure Call):
  - Tries to make network call look like local function call
  - Fundamental problems with this abstraction:
    • Network requests can fail (timeout, packet loss)
    • Network requests may not get response (did it succeed or not?)
    • Retries may cause duplicate execution (need idempotency)
    • Network latency is variable and unpredictable
    • Parameters must be encoded (can't pass pointers)
    • Client and server may be in different languages

  Modern RPC Frameworks:
    - gRPC (Protocol Buffers)
    - Thrift
    - Avro RPC
    - Finagle (Thrift)

  Advantages over REST:
    - Binary encoding (more compact, faster)
    - Built-in schema evolution
    - Bidirectional streaming (gRPC)
    - Code generation

Service Compatibility:
  - Servers updated first, then clients
  - Need backward compatibility (new server, old client)
  - Need forward compatibility (old server, new client) — only if clients are other services
```

**3. Message-Passing Dataflow:**
```
Advantages over direct RPC:
  - Buffer messages if recipient is unavailable/overloaded
  - Redeliver messages if process crashes
  - Sender doesn't need to know IP/port of recipient
  - One message can be sent to multiple recipients
  - Decouples sender from recipient

Message Brokers (RabbitMQ, Kafka, etc.):
  - Producer sends message to named queue/topic
  - Broker delivers message to one or more consumers
  - One-way: sender doesn't wait for response (fire-and-forget)
  - Consumer may publish to another queue (chain of processing)

Actor Model (Akka, Orleans, Erlang OTP):
  - Concurrency model: actors communicate via async messages
  - Each actor processes one message at a time (no thread safety issues)
  - Location transparency: actor may be on same or different node
  - Three challenges for distributed actors:
    • Message delivery semantics (at-most-once, at-least-once, exactly-once)
    • Message ordering guarantees
    • Handling node failures
```

---

## Part II: Distributed Data

### Why Distribute Data?

```
Reasons:
  1. Scalability — data volume, read/write load exceeds single machine
  2. Fault tolerance/High availability — redundancy allows continued operation
  3. Latency — place data geographically close to users

Two main approaches:
  - Replication: same data on multiple nodes (redundancy)
  - Partitioning: split data into subsets (sharding)
  (Usually used together)
```

---

### Chapter 5: Replication

#### Leaders and Followers (Master-Slave)

```
How it works:
  1. One replica is the leader (master/primary)
  2. Other replicas are followers (slaves/secondaries)
  3. Writes go to leader only
  4. Leader sends replication stream to followers
  5. Reads can go to any replica

Synchronous vs. Asynchronous Replication:

  Synchronous:
    - Leader waits for follower to confirm write
    - Follower guaranteed to have up-to-date copy
    - If follower is down/slow → leader blocked
    - Impractical to make ALL followers synchronous
  
  Semi-synchronous:
    - ONE follower is synchronous, others asynchronous
    - Guarantees up-to-date copy on at least 2 nodes
  
  Asynchronous (most common):
    - Leader doesn't wait for followers
    - Fast writes, but data can be lost if leader fails
    - Followers may be behind (replication lag)
```

**Setting Up New Followers:**
```
1. Take consistent snapshot of leader's database
2. Copy snapshot to new follower
3. Follower connects to leader, requests changes since snapshot
   (using log sequence number / binlog coordinates)
4. Follower processes backlog, then continues streaming
```

**Handling Node Outages:**

```
Follower Failure (Catch-up Recovery):
  - Follower knows last transaction processed
  - Reconnects to leader, requests all changes since then
  - Applies changes until caught up

Leader Failure (Failover):
  1. Determine leader has failed (timeout-based detection)
  2. Choose new leader (most up-to-date replica, or election)
  3. Reconfigure system to use new leader
  
  Failover Pitfalls:
    - Asynchronous: new leader may be behind → data loss
    - Discarding writes is dangerous if other systems (e.g., Redis, MySQL) 
      have coordinated with old leader (GitHub incident: auto-increment 
      conflict exposed private data)
    - Split brain: two nodes both believe they are leader
    - What timeout? Too short → unnecessary failovers; too long → longer recovery
```

#### Replication Logs Implementation

```
1. Statement-based: replicate SQL statements
   - Problems: NOW(), RAND(), auto-increment, triggers, side effects
   
2. Write-ahead log (WAL) shipping: send storage engine's WAL
   - Byte-level changes → tightly coupled to storage engine version
   - Can't run different versions on leader/follower (no zero-downtime upgrade)

3. Logical (row-based) log replication:
   - Sequence of records describing writes at row granularity
   - Decoupled from storage engine internals
   - Easier for external systems to parse (CDC - Change Data Capture)
   - MySQL binlog (row-based), PostgreSQL logical decoding

4. Trigger-based replication:
   - Application-level: triggers/stored procedures on write → replicate
   - Most flexible, most overhead, most fragile
```

#### Problems with Replication Lag

```
Read-after-write Consistency (Read-your-writes):
  Problem: User writes, then reads from stale follower → thinks write was lost
  
  Solutions:
    - Read user's own data from leader (e.g., profile → always read own profile from leader)
    - Track time of last write; for 1 min after write, read from leader
    - Client remembers timestamp of last write; replica must be at least that fresh
    - Cross-device: centralize metadata about last write

Monotonic Reads:
  Problem: User reads from fresh replica, then stale one → sees time "go backward"
  
  Solution: Each user always reads from the same replica (e.g., hash of user ID → replica)

Consistent Prefix Reads:
  Problem: Causally related writes appear in wrong order to reader
  
  Example: Question appears after answer if partitions have different lag
  Solution: Causally related writes go to same partition, or use causal ordering mechanisms
```

#### Multi-Leader Replication

```
Use Cases:
  - Multi-datacenter operation (leader in each DC)
  - Clients with offline operation (each device is a "leader")
  - Collaborative editing (each user's edits are like writes to a leader)

Advantages:
  - Performance: writes processed in local DC (lower latency)
  - Tolerance of datacenter outages: each DC operates independently
  - Tolerance of network problems: async replication between DCs

The BIG Problem — Write Conflicts:
  
  Example: User A changes title to "B", User B changes title to "C" simultaneously
           at different leaders. Each leader accepts locally, then conflict on replication.

  Conflict Resolution Strategies:
    1. Conflict avoidance: route all writes for a record to same leader
    2. Converging to consistent state:
       - Last write wins (LWW): timestamp-based, prone to data loss
       - Higher replica ID wins: also data loss
       - Merge values: concatenate, create set
       - Record conflict in data structure, resolve later (application code)
    3. Custom resolution logic:
       - On write: handler called when conflict detected (background)
       - On read: store all versions, present to user/app on next read (CouchDB)

  Topologies:
    - All-to-all: every leader replicates to every other (most common)
    - Circular: each leader replicates to the next in a ring
    - Star: one central leader relays to others
    - Problem with circular/star: single point of failure
    - Problem with all-to-all: causality violations (overtaking)
```

#### Leaderless Replication (Dynamo-style)

```
How it works:
  - Client writes to multiple replicas directly (or via coordinator)
  - Client reads from multiple replicas and takes most recent value
  - No failover needed (remaining replicas accept writes when one is down)

Quorum Reads and Writes:
  n = total replicas
  w = write quorum (number of confirmations needed for write)
  r = read quorum (number of replicas to query for read)
  
  Rule: w + r > n  →  guaranteed to read at least one up-to-date value
  
  Common: n=3, w=2, r=2
  Read-heavy: n=3, w=3, r=1 (reads from single node, writes must hit all)
  Write-heavy: n=3, w=1, r=3 (fast writes, reads query all)

  Limitations of Quorum:
    - w + r > n does NOT guarantee reading the latest value in all cases:
      • Sloppy quorum (writes go to different nodes than reads)
      • Concurrent writes (unclear ordering)
      • Write concurrent with read (may or may not be reflected)
      • Write succeeded on some but failed on others (< w), not rolled back
      • Node carrying new value fails, restored from stale replica

Anti-entropy and Read Repair:
  Read Repair:
    - Client reads from multiple replicas, detects stale value
    - Client writes newer value back to stale replicas
    
  Anti-entropy Process:
    - Background process looks for differences between replicas
    - Copies missing data (no ordering guarantee, may be significant delay)

Sloppy Quorums and Hinted Handoff:
  - When designated nodes are unreachable, write to other nodes temporarily
  - "Sloppy quorum": w writes to ANY w nodes (not necessarily the designated ones)
  - Hinted handoff: when designated node is back, temporary node sends the writes
  - Increases write availability but no guarantee of reading latest value

Detecting Concurrent Writes:
  Problem: multiple clients write to same key concurrently → conflicts
  
  Last Write Wins (LWW):
    - Attach timestamp to each write, keep only highest
    - Achieves convergence at the cost of durability (lost writes)
    - Only safe if keys are immutable (write once)
  
  Version Vectors:
    - Track version number per replica per key
    - Client sends version with every write
    - Server can tell if writes are concurrent or causally ordered
    - Version vector: collection of version numbers from all replicas
    - Allows correct merging without data loss
```

---

### Chapter 6: Partitioning (Sharding)

#### Partitioning Strategies

```
Goal: Spread data and query load evenly across nodes

Partitioning by Key Range:
  - Keys sorted, each partition owns a contiguous range
  - Advantages: efficient range queries
  - Disadvantages: risk of hot spots (e.g., timestamps → all writes to today's partition)
  - Solution: prefix key with something that distributes (e.g., sensor_name + timestamp)
  - Used by: HBase, Bigtable, RethinkDB

Partitioning by Hash of Key:
  - Hash function distributes keys uniformly across partitions
  - Advantages: even distribution, no hot spots (for uniform access)
  - Disadvantages: lose range query ability (adjacent keys scattered)
  - Consistent hashing: minimize redistribution when partition count changes
  - Used by: Cassandra, MongoDB, Voldemort
  
  Cassandra Compromise:
    - Compound primary key: first part hashed (partition key), rest sorted within partition
    - Can do range queries within a partition but not across

Hot Spot Mitigation:
  - Even hash-based partitioning can't prevent hot spots entirely
  - Celebrity problem: one key accessed extremely frequently
  - Application-level solution: append random number to hot keys (split across partitions)
    → Requires bookkeeping for reads (must query all split keys)
    → Only apply to known hot keys
```

#### Secondary Indexes and Partitioning

```
Document-Partitioned Index (Local Index):
  - Each partition maintains its own secondary index
  - Index covers only data in that partition
  - Write: only update one partition's index
  - Read: must query ALL partitions (scatter/gather) — expensive
  - Used by: MongoDB, Riak, Cassandra, Elasticsearch, VoltDB

Term-Partitioned Index (Global Index):
  - Index itself is partitioned (different from data partitions)
  - e.g., colors a-r on partition 0, s-z on partition 1
  - Write: may need to update multiple index partitions (cross-partition, often async)
  - Read: single partition for a given term — efficient
  - Trade-off: writes slower/more complex, reads faster
  - Used by: DynamoDB global secondary indexes, Riak search
```

#### Rebalancing Partitions

```
Strategies:

DON'T: hash mod N (changing N requires moving almost all data)

Fixed Number of Partitions:
  - Create many more partitions than nodes upfront
  - When node added: steal partitions from existing nodes
  - Partition count never changes, only assignment to nodes
  - Must choose partition count at start (hard to get right)
  - Used by: Riak, Elasticsearch, Couchbase, Voldemort

Dynamic Partitioning:
  - Partition splits when it exceeds a size threshold
  - Partition merges when it shrinks below threshold
  - Number of partitions adapts to data volume
  - Used by: HBase, RethinkDB, MongoDB (with range partitioning)

Partitioning Proportional to Nodes:
  - Fixed number of partitions per node
  - When new node added: randomly split existing partitions
  - Used by: Cassandra, Ketama

Automatic vs. Manual Rebalancing:
  - Fully automatic: convenient but risky (cascading failures)
  - Manual with automation assist: human approves rebalancing plan
  - Human in the loop prevents unexpected load shifts
```

#### Request Routing (Service Discovery)

```
Three approaches:
  1. Client contacts any node; node forwards if needed (gossip protocol)
     - Used by: Cassandra, Riak (gossip among nodes)
  
  2. Routing tier (partition-aware load balancer)
     - Used by: MongoDB mongos
  
  3. Client is partition-aware (knows which node has which partition)
     - Used by: client libraries with partition map

Coordination service (ZooKeeper):
  - Maintains authoritative partition-to-node mapping
  - Nodes register in ZooKeeper
  - Routing tier / clients subscribe to ZooKeeper notifications
  - Used by: HBase, SolrCloud, Kafka
```

---

### Chapter 7: Transactions

#### ACID Properties

```
Atomicity:
  - All or nothing — if transaction fails partway, all changes are rolled back
  - NOT about concurrency (that's Isolation)
  - About fault recovery: if error occurs, transaction is aborted and DB is unchanged
  - "Abortability" would be a better name

Consistency:
  - Application-level property, not really a database guarantee
  - Invariants about your data (e.g., credits and debits must balance)
  - Application must define correct transactions; DB can't guarantee this alone
  - "C" doesn't really belong in ACID (it's the application's responsibility)

Isolation:
  - Concurrent transactions don't interfere with each other
  - Ideally: serializability (result as if transactions ran serially)
  - In practice: weaker levels used for performance

Durability:
  - Once committed, data won't be lost (even if hardware fault/crash)
  - Means: written to non-volatile storage (and/or replicated)
  - No absolute guarantee (all disks can fail simultaneously)
  - Techniques: WAL, B-tree write-ahead logging, replication
```

#### Weak Isolation Levels

```
Read Committed:
  - No dirty reads: only see committed data
  - No dirty writes: only overwrite committed data
  - Implementation: row-level locks for writes; for reads, DB remembers old + new value
  - DEFAULT in many databases (PostgreSQL, Oracle, SQL Server)
  
  What it DOESN'T prevent:
    - Read skew (non-repeatable read)
    - Write skew

Snapshot Isolation (Repeatable Read):
  - Each transaction sees a consistent snapshot of the database
  - Transaction sees all data committed before it started, none committed after
  - Implementation: MVCC (Multi-Version Concurrency Control)
    • Each row has a created_by and deleted_by transaction ID
    • Transaction only sees rows created by earlier committed transactions
    • Never sees rows deleted by earlier committed transactions
  
  Visibility Rules:
    1. At transaction start, list all in-progress transactions — ignore their writes
    2. Ignore writes by aborted transactions
    3. Ignore writes by transactions with later transaction ID
    4. All other writes are visible
  
  Used for: long-running read-only queries (analytics, backups)
  Prevents: read skew / non-repeatable reads
  
  What it DOESN'T prevent:
    - Write skew
    - Phantoms
```

#### Preventing Lost Updates

```
The Lost Update Problem:
  - Two transactions read a value, modify it, write it back
  - Second write clobbers the first (read-modify-write cycle)
  - Example: two users incrementing a counter simultaneously

Solutions:
  1. Atomic operations: UPDATE counters SET value = value + 1
     - Database provides atomic read-modify-write
     - Usually implemented with exclusive lock on the row
  
  2. Explicit locking: SELECT ... FOR UPDATE
     - Application locks rows it intends to update
     - Other transactions must wait
  
  3. Automatically detecting lost updates:
     - DB detects concurrent modifications, aborts one
     - Transaction retries
     - PostgreSQL repeatable read, Oracle serializable
  
  4. Compare-and-set:
     - UPDATE ... SET ... WHERE value = old_value
     - Only succeeds if value hasn't changed since read
     - Not safe if DB reads from stale snapshot

  5. Conflict resolution (replicated databases):
     - Locks and compare-and-set won't work across replicas
     - Allow concurrent writes, resolve later
     - Commutative operations (e.g., increment) can be applied in any order
```

#### Write Skew and Phantoms

```
Write Skew:
  - Two transactions read the same data, make decisions based on it,
    then write DIFFERENT objects
  - Neither individual write conflicts, but together they violate an invariant
  
  Example (hospital on-call):
    - Invariant: at least one doctor must be on call
    - Alice and Bob are both on call
    - Alice checks: 2 on call → removes herself
    - Bob checks: 2 on call → removes himself
    - Result: 0 on call (invariant violated!)
  
  More examples:
    - Meeting room booking (double booking)
    - Multiplayer game (two players moving to same position)
    - Claiming a username (two users register same name)
    - Financial: double-spending / bank account going negative

Phantom:
  - Transaction checks for absence of rows matching a condition
  - Another transaction inserts a row matching that condition
  - First transaction's decision was based on stale information
  
  Problem: can't lock rows that don't exist yet!
  
  Solution — Materializing Conflicts:
    - Create a table of all possible items that could be locked
    - e.g., table of all (room, time_slot) combinations
    - Transaction locks the relevant row in this table
    - Ugly but effective last resort (prefer serializable isolation)
```

#### Serializable Isolation

```
Three implementations:

1. Actual Serial Execution:
   - Execute transactions one at a time, on a single thread
   - No concurrency at all → no concurrency bugs
   - Feasible because: RAM is cheap (data fits in memory), OLTP transactions are short
   
   Requirements:
     - Transactions must be short and fast
     - Dataset must fit in memory
     - Write throughput must be low enough for single CPU
     - Cross-partition transactions are possible but much slower
   
   Stored Procedures:
     - Entire transaction submitted as a single request
     - No interactive back-and-forth (would waste single thread's time)
     - Written in general-purpose language (Redis: Lua, VoltDB: Java)
   
   Partitioning:
     - Each partition has its own single thread
     - Cross-partition transactions require coordination (slower)
   
   Used by: VoltDB, Redis, Datomic

2. Two-Phase Locking (2PL):
   - Readers don't block readers
   - Writers block readers AND other writers
   - Readers block writers
   - → Much stricter than snapshot isolation
   
   Lock Modes:
     - Shared lock: multiple readers can hold simultaneously
     - Exclusive lock: only one writer, blocks all others
   
   How it works:
     - Acquire shared lock to read, exclusive lock to write
     - Must hold all locks until END of transaction (that's the "two phase")
     - Phase 1: acquiring locks; Phase 2: releasing all locks at commit
   
   Performance:
     - Significantly worse than weak isolation (high contention)
     - Deadlocks are frequent → detection and abort
     - Unstable latencies (one slow transaction blocks many)
   
   Predicate Locks:
     - Lock not just existing rows but ALL rows matching a condition (including future ones)
     - Prevents phantoms
     - Example: lock all bookings for room 123 between 12:00-13:00
   
   Index-Range Locks (Next-Key Locking):
     - Approximation of predicate locks (coarser granularity)
     - Lock a range on an index (e.g., lock all of room 123, or all bookings at noon)
     - Less precise but much lower overhead than predicate locks
   
   Used by: MySQL InnoDB (serializable), SQL Server

3. Serializable Snapshot Isolation (SSI):
   - Optimistic concurrency control
   - Allow transactions to proceed without blocking
   - At commit time: check for conflicts, abort if needed
   
   How it detects conflicts:
     a. Detecting stale MVCC reads:
        - At commit time, check if any data read has since been modified
        - If so: abort and retry
     b. Detecting writes that affect prior reads:
        - Track which transactions have read which data
        - When transaction writes, notify all transactions that read affected data
        - Those transactions must abort at commit time
   
   Performance:
     - Better than 2PL for read-heavy workloads (reads don't block writes)
     - Aborts higher under contention (but no deadlocks)
     - Predictable latency
     - Works well with distributed systems (no need for distributed locks)
   
   Used by: PostgreSQL (serializable since 9.1), FoundationDB
```

---

### Chapter 8: The Trouble with Distributed Systems

#### Unreliable Networks

```
Shared-Nothing Architecture:
  - Nodes communicate only via network (no shared memory/disk)
  - Dominant approach for building internet services
  - Network is the only way nodes communicate → network problems are fundamental

Types of Network Faults:
  - Request lost
  - Request queued (delivered later)
  - Remote node failed
  - Remote node temporarily stopped responding (long GC pause)
  - Response lost
  - Response queued

The sender CANNOT distinguish these cases!
  → Must use timeouts, but timeout ≠ node dead

Network Partitions (netsplits):
  - Part of the network is cut off from the rest
  - Must be tolerated in any distributed system (can't be prevented)
  - Choice: either stop serving (consistent) or continue with stale data (available)

Detecting Faults:
  - Load balancer needs to know if node is dead → stop sending requests
  - Leader-based replication: followers need to know if leader is dead → failover
  - Feedback signals: TCP RST, ICMP unreachable, process death notification
  - But: silence (no response) is the most common case → must rely on timeouts

Timeouts:
  - Too short: premature declarations of death, unnecessary failovers
  - Too long: long wait until a failed node is declared dead
  
  Network congestion and queueing:
    - Network switch queue
    - OS receive buffer (TCP flow control)
    - VM monitor queuing (virtualization)
    - TCP retransmission timeout
  
  → Response time is not constant; variability makes timeout choice hard
  → Phi Accrual failure detector: adaptive timeout based on observed response times
```

#### Unreliable Clocks

```
Types of Clocks:

Time-of-Day Clocks:
  - Return wall-clock time (e.g., seconds since epoch)
  - Synchronized with NTP (Network Time Protocol)
  - Can jump forward or backward (NTP step adjustment)
  - NOT suitable for measuring elapsed time
  - Coarse resolution in some systems

Monotonic Clocks:
  - Always move forward (never jump back)
  - Good for measuring elapsed time (durations)
  - No meaning across different machines (only relative within one machine)
  - Rate may be adjusted (NTP slewing) but never jumps

Clock Synchronization Problems:
  - Quartz clock drift: ~200 ppm (6 ms drift per 30 seconds, 17 seconds per day)
  - NTP accuracy: limited by network round-trip time
  - NTP can jump clock backward/forward
  - Firewall may block NTP traffic
  - Virtualization: VM pause doesn't advance clock
  - Leap seconds: NTP servers may lie (smear)

Timestamp Ordering Issues:
  - LWW depends on timestamps → if clocks are skewed, newer writes may be discarded
  - Clock skew of even a few milliseconds can cause data loss with LWW
  
  Example:
    Node 1 (clock slightly ahead): write x=1 at t=42.004
    Node 2 (clock slightly behind): write x=2 at t=42.003
    LWW picks x=1 (higher timestamp) even though x=2 happened later in reality

Confidence Intervals:
  - Clock readings should be treated as a range [earliest, latest]
  - Google Spanner: TrueTime API returns [earliest, latest]
    • Uses GPS receivers and atomic clocks in each datacenter
    • Uncertainty usually < 7ms
    • Spanner waits out the uncertainty before committing (commit wait)
    • If [A.earliest, A.latest] and [B.earliest, B.latest] don't overlap → definite ordering
```

#### Process Pauses

```
A node may pause for extended periods:
  - Garbage collection (GC) "stop the world" — can be seconds
  - VM suspended (live migration), laptop lid closed
  - OS context switching under load
  - Synchronous disk I/O (even on SSDs)
  - Memory swapping (thrashing)
  - Unix SIGSTOP signal

Impact:
  - A leader may pause, other nodes elect new leader
  - Original leader resumes, thinks it's still leader
  - → Two leaders! (split brain)

Solutions:
  - Fencing tokens: each lock/lease has a monotonically increasing token
    • Resource (storage) rejects writes with token older than what it's already seen
  - Treat GC pauses like brief outages: notify other nodes before GC
  - Limit impact of GC: only use short-lived objects, or restart periodically
```

#### Knowledge, Truth, and Lies

```
The Truth is Defined by the Majority:
  - A node cannot trust its own judgment about whether it's alive
  - Must rely on a quorum of nodes to make decisions
  - Example: a node may think it holds a lease, but if it was paused for 15 seconds, the lease expired

Byzantine Faults:
  - Nodes that LIE (send corrupted or intentionally wrong messages)
  - Byzantine fault tolerance: system works even if some nodes are malicious
  - Most systems DO NOT handle Byzantine faults (too expensive)
  - Assumed: nodes may be faulty but are honest (crash-stop or crash-recovery model)
  
  When it matters:
    - Aerospace (radiation-induced corruption)
    - Cryptocurrency / blockchain (untrusted participants)
    - Multi-organization systems (participants may cheat)

System Models:

  Timing assumptions:
    - Synchronous: bounded network delay and process pauses (unrealistic)
    - Partially synchronous: usually behaves synchronous but sometimes exceeds bounds (realistic)
    - Asynchronous: no timing assumptions at all (very restrictive, can't use timeouts)
  
  Node failure assumptions:
    - Crash-stop: node fails by stopping permanently
    - Crash-recovery: node may stop, then resume later (with durable storage)
    - Byzantine: node may do anything, including lying
  
  Most real systems assume: partially synchronous + crash-recovery
```

---

### Chapter 9: Consistency and Consensus

#### Consistency Guarantees

```
Spectrum from weakest to strongest:
  1. Eventual consistency: if you stop writing, eventually all reads return same value
  2. Read-after-write consistency
  3. Monotonic reads
  4. Consistent prefix reads
  5. Causal consistency
  6. Linearizability (strongest)
```

#### Linearizability

```
Definition:
  - System appears as if there is only a single copy of the data
  - All operations are atomic (take effect at a single point in time)
  - Once a write completes, all subsequent reads must see that write (or a later one)
  - Real-time ordering is respected

Linearizable vs. Serializable:
  - Serializable: transactions appear to execute in SOME serial order (not necessarily real-time order)
  - Linearizable: single-object, real-time ordering guarantee
  - Strict serializability = serializable + linearizable (strongest guarantee)

Use Cases Requiring Linearizability:
  1. Leader election: exactly one leader (lock)
  2. Constraints and uniqueness: one user per username
  3. Cross-channel timing: if I post photo and notify friend, friend must see photo
     (photo write must be visible before notification is received)

Cost of Linearizability:
  - CAP Theorem: in presence of network partition, choose Consistency or Availability
    • CP: linearizable but may be unavailable during partition
    • AP: always available but may return stale data during partition
    • Not really a choice: partitions WILL happen, so it's really "C or A when partitioned"
  
  - Even without partitions: linearizability has performance cost
    • Requires coordination between nodes
    • RAM on modern multi-core CPUs is not even linearizable (CPU caches)!
  
  - Few systems are actually linearizable:
    • Single-leader replication: potentially linearizable (if reads go to leader)
    • Consensus algorithms (Paxos, Raft): linearizable
    • Multi-leader: NOT linearizable
    • Leaderless (Dynamo-style): NOT linearizable (even with quorum)
```

#### Ordering Guarantees

```
Causal Ordering:
  - Weaker than linearizability but still useful
  - If event A caused event B, then A must appear before B everywhere
  - Concurrent events can be in any order (no causal relationship)
  - "Causal consistency is the strongest consistency model that doesn't sacrifice availability"

Lamport Timestamps:
  - (counter, nodeID) pair
  - Each node increments counter on each operation
  - On receiving message: counter = max(local, received) + 1
  - Gives total order consistent with causality
  
  Limitations:
    - Total order only known after the fact
    - Can't use for real-time decisions (e.g., "is this username taken?")
    - Need to collect all timestamps to determine order

Total Order Broadcast:
  - Protocol for exchanging messages between nodes
  - Guarantees:
    1. Reliable delivery: message delivered to all nodes (or none)
    2. Totally ordered: all nodes deliver messages in the same order
  
  - Equivalent to consensus (can implement one from the other)
  - Used for: database replication (state machine replication)
  - If every replica processes messages in same order → replicas stay consistent
```

#### Distributed Transactions and Consensus

```
Consensus Problem:
  - Multiple nodes must agree on a value
  - Properties required:
    1. Uniform agreement: no two nodes decide differently
    2. Integrity: no node decides twice
    3. Validity: if a node decides value v, then v was proposed by some node
    4. Termination: every non-crashed node eventually decides
  
  FLP Result: in an asynchronous system, no consensus algorithm can guarantee 
  termination if even one node may crash (theoretical impossibility)
  → In practice: use timeouts (partially synchronous model)

Two-Phase Commit (2PC):
  - Used for distributed transactions (across multiple databases/services)
  
  Phase 1 (Prepare):
    - Coordinator sends "prepare" to all participants
    - Each participant responds "yes" (promise to commit) or "no" (abort)
    - Once participant says "yes" → it MUST commit if coordinator says so
    
  Phase 2 (Commit/Abort):
    - If ALL participants said "yes" → coordinator sends "commit"
    - If ANY participant said "no" → coordinator sends "abort"
    - Participants carry out coordinator's decision
  
  The Problem — Coordinator Failure:
    - Participants have said "yes" and are now IN DOUBT (uncertain)
    - Cannot proceed until coordinator recovers
    - Holding locks while waiting → blocking other transactions
    - This is why 2PC is called a "blocking" protocol
    - The coordinator is a single point of failure
  
  Three-Phase Commit (3PC):
    - Adds a "pre-commit" phase to avoid blocking
    - But: only works with bounded network delays (not realistic)
    - Generally not used in practice

Consensus Algorithms (Paxos, Raft, Zab, VSR):
  - Non-blocking: progress even if some nodes fail (as long as majority alive)
  - Total order broadcast + consensus are equivalent problems
  
  How they work (simplified):
    - Elect a leader (using voting/election algorithm)
    - Leader proposes values, followers accept
    - Decision requires majority (quorum)
    - If leader fails → elect new leader
    
  Raft (most understandable):
    - Leader election with randomized timeouts
    - Log replication: leader appends entries, followers replicate
    - Safety: committed entry won't be lost (majority acknowledges)
    - Leader completeness: elected leader must have all committed entries
  
  Limitations of Consensus:
    - Performance cost of voting (synchronous replication)
    - Requires strict majority (can't operate with too many failures)
    - Most use fixed membership (adding/removing nodes is complex)
    - Leader election relies on timeouts (sensitive to network issues)
    - Static membership assumptions

Membership and Coordination Services (ZooKeeper, etcd):
  - Implement consensus internally
  - Provide useful features built on consensus:
    • Linearizable atomic operations (compare-and-swap)
    • Total ordering of operations (Zxid / fencing tokens)
    • Failure detection (ephemeral nodes / heartbeats)
    • Change notifications (watches)
  
  Use cases:
    - Leader election (acquire ephemeral lock)
    - Service discovery (nodes register themselves)
    - Configuration management
    - Distributed locks and coordination
  
  NOT intended for general-purpose data storage (small metadata only)
```

---

## Part III: Derived Data

---

### Chapter 10: Batch Processing

#### Unix Philosophy

```
Key Principles:
  1. Each program does one thing well
  2. Output of one program → input of another
  3. Design for early trying (build quickly, don't hesitate to rebuild)
  4. Use tools over manual labor

Applied to Data:
  - stdin/stdout as uniform interface
  - Immutable inputs, append-only outputs
  - Programs don't care about each other's internals
  - Loose coupling enables composition
```

#### MapReduce

```
How it works:
  1. Map: extract key-value pairs from input records
     - Processes one record at a time
     - Outputs zero or more key-value pairs
  
  2. Shuffle: group all values by key (distributed sort)
     - Handled by framework
     
  3. Reduce: process all values for a given key
     - Produces output records
     - One reducer per distinct key (or key range)

Example (word count):
  Map: for each document, emit (word, 1) for each word
  Reduce: for each word, sum all the 1s

Distributed Execution:
  - Input split into chunks (HDFS blocks, typically 128MB)
  - Map tasks: one per input chunk, run on node storing that chunk (data locality)
  - Map output sorted by key, written to local disk
  - Reduce tasks: pull sorted map output, merge-sort, process
  
Key Properties:
  - Inputs are immutable, outputs are new files
  - No side effects (pure functions)
  - Fault tolerance: re-run failed tasks (output deterministic)
  - Can retry any task without affecting rest of computation

MapReduce Joins:

  Sort-Merge Join:
    - Both datasets have same key (e.g., user_id)
    - Mappers extract key from both datasets, tag with source
    - Reducer sees all records for a key → join them
    - All network communication is in shuffle (not random access)
  
  Broadcast Hash Join:
    - Small dataset fits in memory of each mapper
    - Large dataset is the input, small dataset loaded as hash table
    - Each mapper joins independently (no reduce phase needed)
  
  Partitioned Hash Join:
    - Both datasets partitioned by the same key
    - Each mapper only needs the corresponding partition of the small dataset

Output of MapReduce:
  - Write to new files in distributed filesystem
  - Can then be loaded into a database (bulk load)
  - Or used as input to another MapReduce job
  
  Building indexes: map/reduce produces index files, then bulk-load into serving system
  (e.g., build search index → deploy to read-only serving nodes)
```

#### Beyond MapReduce

```
Problems with MapReduce:
  - Materializes intermediate state to files (expensive I/O)
  - Must wait for previous job to fully complete
  - Mappers are often redundant (just reading back what previous reducer wrote)
  - No support for iterative algorithms (must re-read entire dataset each time)

Dataflow Engines (Spark, Flink, Tez):
  - Model computation as a DAG (directed acyclic graph) of operators
  - Operators can be map, reduce, join, filter, etc.
  - Don't materialize intermediate state (pipe between operators)
  - Can pipeline operations in memory
  
  Advantages over MapReduce:
    - No unnecessary sorting (sort only when needed)
    - No unnecessary map tasks
    - Scheduler has overview of entire dataflow → better optimization
    - Operators can start as soon as input is ready (no barrier)
    - JVM can stay warm (reuse across operators)
  
  Fault Tolerance:
    - If intermediate data is lost → recompute from last materialized checkpoint
    - Trade-off: less disk I/O vs. more recomputation on failure
    - Spark RDDs: track lineage (computation graph) for recomputation
    - Flink: periodic checkpoints to durable storage

Graph Processing (Pregel / BSP model):
  - For algorithms like PageRank, shortest paths, connected components
  - "Think like a vertex": each vertex processes messages from neighbors
  - Bulk Synchronous Parallel: iterations (supersteps)
    1. Each vertex processes all incoming messages
    2. Each vertex sends messages to neighbors
    3. Barrier: wait for all vertices to finish
    4. Repeat until convergence (no more messages)
  - Fault tolerance: checkpoint state after each superstep
```

---

### Chapter 11: Stream Processing

#### Messaging Systems

```
Direct Messaging (UDP multicast, ZeroMQ, HTTP webhooks):
  - Application code handles message loss / retry
  - No durability guarantee

Message Brokers / Message Queues:

  Traditional (RabbitMQ, ActiveMQ):
    - Messages deleted after successful consumer acknowledgment
    - Consumers are destructive (message can't be re-read)
    - Ordering guarantee within a queue
    - Fan-out: multiple queues for same message
    - No historical replay

  Log-Based (Kafka, Amazon Kinesis):
    - Append-only log partitioned across brokers
    - Messages are immutable and persist for configured retention
    - Consumer maintains offset (position in log)
    - Can replay from any point (re-read old messages)
    - Ordering guaranteed within a partition
    - Throughput: millions of messages/sec
    
    Consumer Groups:
      - Each partition → one consumer in group (no sharing within partition)
      - Multiple groups can independently consume same topic
      - Number of consumers in group ≤ number of partitions
    
    Offset Management:
      - Consumer periodically checkpoints its offset
      - On restart: resume from last checkpoint
      - At-least-once delivery: may reprocess messages since last checkpoint
      - Exactly-once: combine with transactional output or idempotent writes
```

#### Change Data Capture (CDC)

```
Concept:
  - Observe all changes to a database, replicate to other systems
  - Database is the leader (source of truth)
  - Derived systems (search index, cache, warehouse) are followers
  
  Implementation:
    - Parse replication log (WAL/binlog)
    - Example: Debezium (MySQL binlog → Kafka), PostgreSQL logical decoding
    
  Benefits:
    - Keep derived systems in sync without dual writes
    - Derived systems can be rebuilt from scratch (replay entire log)
    - Event sourcing lite (but stores current state, not events)
  
  Initial Snapshot:
    - Log has finite retention (can't replay from the beginning of time)
    - New consumer: take snapshot of current state + subscribe to changes from that point
    - Log compaction: keep only latest value per key (like a snapshot)

Log Compaction:
  - For every key, keep only the most recent value (discard older)
  - Tombstone: message with null value → key has been deleted
  - Compacted log can reconstruct the full current state
  - Consumer can start from beginning of compacted log instead of snapshot
```

#### Event Sourcing

```
Core Idea:
  - Store all changes as a sequence of immutable events
  - Current state = replay all events from the beginning
  - Events represent what happened, not current state
  
  Differences from CDC:
    - CDC: extracts changes from mutable database, events are low-level (row changes)
    - Event sourcing: events are domain-level, designed from application perspective
      e.g., "student enrolled in course" vs "INSERT INTO enrollments..."
  
  Benefits:
    - Complete audit trail
    - Can derive new views from old events
    - Debugging: replay events to reproduce any past state
    - Modeling: events capture intent, not just effect
  
  Challenges:
    - Event log grows forever (snapshotting for performance)
    - Schema evolution of events (must handle all historical event formats)
    - Eventual consistency between event log and derived views
    - Immutability vs. GDPR/right-to-be-forgotten (crypto-shredding as solution)

CQRS (Command Query Responsibility Segregation):
  - Separate write path (commands → events) from read path (query optimized views)
  - Write: validate command, append event
  - Read: pre-computed views (materialized from events)
  - Can have multiple read models optimized for different query patterns
```

#### Stream Processing Patterns

```
Complex Event Processing (CEP):
  - Detect patterns in event streams
  - Define patterns (like regex over events)
  - When pattern matched → emit complex event
  - Used for: fraud detection, monitoring, business rules

Stream Analytics:
  - Aggregations over time windows
  - Rates, averages, histograms, percentiles
  - Less about specific events, more about aggregate measurements

Windowing:
  - Tumbling window: fixed-size, non-overlapping (e.g., every 5 minutes)
  - Hopping window: fixed-size, overlapping (5-min window, every 1 minute)
  - Sliding window: all events within some interval of each other
  - Session window: group events by activity sessions (gap-based)

Stream Joins:

  Stream-Stream Join (window join):
    - Join events from two streams within a time window
    - Example: match ad click with ad impression within 1 hour
    - Must buffer events from both streams
  
  Stream-Table Join (enrichment):
    - Join stream event with current state of a table
    - Example: enrich order event with customer profile
    - Options: query database per event (slow) or maintain local copy of table
    - CDC to keep local table copy up-to-date
  
  Table-Table Join (materialized view maintenance):
    - Both inputs are CDC streams (representing tables)
    - Output: materialized join that stays up-to-date
    - Example: maintain a view of "user's timeline" from follows + tweets tables

Fault Tolerance in Stream Processing:
  
  Microbatching (Spark Streaming):
    - Break stream into small batches (e.g., 1 second)
    - Process each batch like a mini batch job
    - Tumbling window = batch interval
    - Provides exactly-once semantics within the batch
  
  Checkpointing (Flink):
    - Periodically checkpoint operator state
    - On failure: restore from checkpoint, replay from last checkpoint
    - Barrier messages flow through the DAG (Chandy-Lamport algorithm)
  
  Idempotent Writes:
    - Make operations idempotent (safe to retry)
    - Include offset/sequence number in output
    - On replay: check if already written (deduplication)
  
  Transactional Output:
    - Atomically commit output and checkpoint offset together
    - Exactly-once end-to-end (but only within the system boundary)
```

---

### Chapter 12: The Future of Data Systems

#### Data Integration

```
The Problem:
  - No single tool does everything well
  - Need specialized systems for OLTP, analytics, search, caching, etc.
  - Must keep all systems consistent with each other

Derived Data vs. System of Record:
  - System of record (source of truth): authoritative copy, writes go here first
  - Derived data: result of transforming/processing the source data
    • Search index, materialized view, cache, ML model
    • Can always be rebuilt from source (in theory)
    • If lost: re-derive from source (no data loss)

Approaches to Data Integration:
  
  Dual Writes (naïve approach):
    - Application writes to all systems (e.g., DB + search index + cache)
    - Problems:
      • Race conditions (no total ordering between writes to different systems)
      • Partial failure (one write succeeds, another fails)
    - Result: systems can permanently diverge

  Log-Based Integration (better):
    - Total order broadcast (e.g., Kafka) as backbone
    - One system (or the log) is the leader
    - All others derive their state from the log
    - Ordering is guaranteed → systems converge
    - Can rebuild any derived system by replaying the log
  
  Lambda Architecture:
    - Batch layer: MapReduce over entire dataset (slow but complete)
    - Speed layer: stream processing of recent events (fast but approximate)
    - Merge results of both layers to answer queries
    - Problems: maintaining two codepaths, complex merging
  
  Kappa Architecture:
    - Stream processing only (no batch layer)
    - Replay events from log to rebuild state
    - Simpler, but log must have long retention (or compaction)
```

#### Unbundling Databases

```
A database provides:
  - Secondary indexes
  - Materialized views
  - Replication (full-text search = replicated inverted index)
  - Transaction log (WAL = source of truth, tables = derived)

These concepts map to data infrastructure:
  - Secondary index → search system (Elasticsearch)
  - Materialized view → precomputed cache/view
  - Replication → CDC to other systems
  - Transaction log → Kafka

"Unbundling" = building these features across specialized systems rather than within one monolithic database

Benefits:
  - Each component uses the best tool for its job
  - Loose coupling (systems can be replaced independently)
  - New views can be added without changing the source

Challenge:
  - Maintaining consistency across all these systems
  - Ordering guarantees (total order broadcast helps)
  - Exactly-once semantics end-to-end
```

#### Designing Applications Around Dataflow

```
Dataflow Approach:
  - Think of application state as derived from an ordered log of immutable events
  - Read path: serve queries from precomputed views (fast, cached)
  - Write path: validate, append event to log
  - Derived views maintained by stream processors
  
  Application writes as stream processors:
    - Instead of: app → DB → read back
    - Think: app → append event → derived views update asynchronously
    
  Advantages:
    - Separation of concerns: write logic vs. read optimization
    - Can evolve read views independently (add new ones, drop old)
    - Audit trail built in
    - Can reason about entire dataflow holistically

Exactly-Once Semantics:
  - Hard to achieve end-to-end
  - Within one system: transactions or idempotency
  - Across system boundaries: need idempotent operations or distributed transactions
  - Practical approach: unique request ID for deduplication

End-to-End Argument:
  - Reliability features only work if implemented end-to-end
  - Example: TCP guarantees delivery between two nodes, but not end-to-end through your application
  - Duplicate suppression: even if stream processor deduplicates, user might click button twice
  - Must handle at the application level (unique operation ID, client-generated)
```

#### Correctness, Ethics, and the Future

```
Correctness Guarantees:
  
  Constraints and Uniqueness:
    - Unique constraints: can be enforced via consensus (slow) or probabilistically
    - Alternative: claim unique ID optimistically, check asynchronously, apologize if conflict
    - Many systems can tolerate temporary violation → correct later
  
  Timeliness vs. Integrity:
    - Timeliness: users see up-to-date state (freshness)
    - Integrity: data is correct (no corruption, no contradictions)
    - Integrity is MORE important than timeliness
      • Eventual consistency sacrifices timeliness but maintains integrity
      • Losing data (integrity violation) is much worse than showing stale data
    - ACID = strong timeliness + strong integrity
    - Event-based systems: strong integrity (via log ordering) + eventual timeliness

Trust but Verify:
  - We usually trust hardware to work correctly, software to be bug-free
  - But failures happen: bit flips, bugs, operator errors
  - Auditability: maintain immutable, append-only logs
    • Can check derived data against source events
    • Can detect corruption or bugs after the fact
  - End-to-end integrity checks (checksums, data lineage)
```

---

## Summary of Key Trade-offs

| Decision | Option A | Option B | Consideration |
|----------|----------|----------|---------------|
| Storage engine | B-tree (reads) | LSM-tree (writes) | Read vs. write heavy workload |
| Replication | Sync (strong consistency) | Async (availability) | Latency tolerance vs. data safety |
| Partitioning | Key range (range queries) | Hash (even distribution) | Access patterns |
| Consistency | Linearizable (correct) | Eventual (available) | CAP: what to sacrifice during partition |
| Isolation | Serializable (safe) | Weaker (fast) | Correctness vs. performance |
| Schema | Schema-on-write (rigid) | Schema-on-read (flexible) | Data quality vs. agility |
| Processing | Batch (thorough) | Stream (timely) | Latency requirements |
| Data model | Relational (joins) | Document (locality) | Relationships vs. self-contained access |

---

## Mental Models and Principles

1. **No perfect system** — every choice is a trade-off; understand what you're giving up
2. **Faults are inevitable** — design for resilience (retry, replicate, detect, recover)
3. **Distributed ≠ just "more machines"** — fundamentally different failure modes (network partitions, clock skew, partial failures)
4. **Data outlives code** — schema evolution and backward/forward compatibility matter
5. **Derived data is powerful** — system of record + derived views is more flexible than one monolithic store
6. **Immutability simplifies** — append-only logs, event sourcing, immutable inputs eliminate many concurrency issues
7. **End-to-end matters** — reliability at one layer doesn't guarantee end-to-end correctness
8. **Understand your SLAs** — do you need linearizability? Exactly-once? Or is eventual/at-least-once good enough?
9. **Simple systems are better** — accidental complexity is the enemy of reliability
10. **Measure, don't guess** — use percentiles, load testing, and monitoring to understand real behavior
