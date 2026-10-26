# Module 09 — Q&A + Production Scenarios: MCP & Agents

---

## Top 20 Interview Questions & Answers

### Q1: What is the Model Context Protocol (MCP) and why does it matter?

**A:**
```
PROBLEM WITHOUT MCP:
  Every AI tool builds its own integration:
  
  ┌──────────┐    Custom API    ┌──────────┐
  │ ChatGPT  │────────────────→│ Slack    │
  │          │    Custom API    ├──────────┤
  │          │────────────────→│ GitHub   │
  │          │    Custom API    ├──────────┤
  │          │────────────────→│ Jira     │
  └──────────┘                 └──────────┘
  
  ┌──────────┐    Custom API    ┌──────────┐
  │ Claude   │────────────────→│ Slack    │  ← Duplicated work!
  │          │    Custom API    ├──────────┤
  │          │────────────────→│ GitHub   │  ← Different format!
  └──────────┘                 └──────────┘
  
  N AI apps × M tools = N×M integrations 😱

MCP SOLUTION (like USB for AI):
  ┌──────────┐                 ┌──────────────┐    ┌──────────┐
  │ ChatGPT  │──── MCP ──────→│ MCP Server:  │───→│ Slack    │
  ├──────────┤     Protocol    │ Slack        │    └──────────┘
  │ Claude   │──── MCP ──────→├──────────────┤    ┌──────────┐
  ├──────────┤                 │ MCP Server:  │───→│ GitHub   │
  │ Cursor   │──── MCP ──────→│ GitHub       │    └──────────┘
  └──────────┘                 └──────────────┘
  
  N AI apps + M tools = N+M integrations ✓
  
  Each tool builds ONE MCP server.
  Each AI app supports MCP protocol.
  Everything works with everything.

ANALOGY:
  Before USB: every device had a different cable
  After USB:  one cable works for everything
  
  Before MCP: every AI needs custom tool integration
  After MCP:  one protocol works for all tools

KEY COMPONENTS:
  1. MCP Server: wraps a tool/service (GitHub, DB, API)
  2. MCP Client: the AI application (Cursor, Claude)
  3. Tools: functions the server exposes (search, create, update)
  4. Resources: data the server can provide (files, docs)
  5. Prompts: pre-built prompt templates
```

---

### Q2: Explain the Agent Loop. What makes a good agent architecture?

**A:**
```
BASIC AGENT LOOP:
  
  while not done:
      1. OBSERVE: Read current state + tool results
      2. THINK:   Decide what to do next (LLM call)
      3. ACT:     Execute a tool/action
      4. CHECK:   Did we achieve the goal?
  
  This is the ReAct (Reasoning + Acting) pattern.

SIMPLE IMPLEMENTATION:
  class Agent:
      def run(self, goal):
          messages = [{"role": "user", "content": goal}]
          
          for step in range(MAX_STEPS):
              response = llm.generate(messages, tools=self.tools)
              
              if response.has_tool_call:
                  result = self.execute_tool(response.tool_call)
                  messages.append({"role": "tool", "content": result})
              else:
                  return response.content  # Final answer
          
          return "Max steps reached"

WHAT MAKES A GOOD AGENT:

  ┌───────────────────┬──────────────────────────────────────┐
  │ Feature           │ Why it matters                       │
  ├───────────────────┼──────────────────────────────────────┤
  │ Clear goal        │ Agent knows when it's "done"         │
  │ Right tools       │ Not too many (confusion), not too    │
  │                   │ few (can't complete task)            │
  │ Error recovery    │ Retries, fallbacks, escalation       │
  │ Memory            │ Remembers what it tried + results    │
  │ Budget limits     │ Max steps, max tokens, max cost      │
  │ Guardrails        │ Can't do dangerous things            │
  │ Observability     │ Logs every step for debugging        │
  │ Human escalation  │ Asks for help when stuck             │
  └───────────────────┴──────────────────────────────────────┘

ANTI-PATTERNS:
  ❌ Too many tools (>20): model gets confused choosing
  ❌ No step limit: agent runs forever burning money
  ❌ No error handling: one failure = total failure
  ❌ No memory management: context fills up, quality drops
  ❌ Autonomous dangerous actions: deleting data, spending money
```

---

### Q3: Compare ReAct vs Plan-and-Execute agent patterns.

**A:**
```
ReAct (REACTIVE):
━━━━━━━━━━━━━━━
  Think → Act → Observe → Think → Act → Observe → ...
  
  Each step decides what to do based on ALL prior observations.
  Flexible, adaptive, but can be inefficient.
  
  GOOD FOR:
  - Unpredictable tasks (debugging, exploration)
  - Tasks where next step depends on previous result
  - Short tasks (3-5 steps)
  
  BAD FOR:
  - Complex multi-step plans (loses track)
  - Tasks requiring coordination (step order matters)

Plan-and-Execute (PROACTIVE):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Plan (full plan upfront) → Execute step 1 → Execute step 2 → ...
  
  If a step fails → Re-plan from current state.
  
  GOOD FOR:
  - Complex workflows (10+ steps)
  - Tasks with clear subtasks
  - When you need to show the user what will happen
  
  BAD FOR:
  - Exploratory tasks (hard to plan upfront)
  - Highly dynamic environments

HYBRID (most production agents):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. High-level plan (reasoning model, e.g., o3)
  2. Execute each step with ReAct (standard model, e.g., GPT-4o)
  3. After each step, check if plan needs updating
  
  Uses two models:
    Planner: expensive, good at reasoning (called 2-3 times)
    Executor: cheap, good at tool use (called 10-20 times)
  
  COST: ~$0.50 per complex task
  vs. pure o3: ~$2.00 per task
  vs. pure GPT-4o: fails on complex tasks

COMPARISON:
  ┌─────────────┬──────────┬────────────────┬─────────┐
  │ Feature     │ ReAct    │ Plan-Execute   │ Hybrid  │
  ├─────────────┼──────────┼────────────────┼─────────┤
  │ Planning    │ None     │ Full upfront   │ High+low│
  │ Flexibility │ HIGH     │ LOW            │ MEDIUM  │
  │ Efficiency  │ LOW      │ HIGH           │ HIGH    │
  │ Debugging   │ HARD     │ EASY           │ MEDIUM  │
  │ Cost        │ Variable │ Predictable    │ Optimal │
  │ Complexity  │ Simple   │ Moderate       │ Complex │
  └─────────────┴──────────┴────────────────┴─────────┘
```

---

### Q4: How do you manage context in a long-running agent?

**A:**
```
PROBLEM:
  Agent runs for 20 steps.
  Each step: ~500 tokens (thought + action + observation).
  After 20 steps: 10,000+ tokens of conversation history.
  Model context: 128K tokens... but quality degrades long before!
  
  "Lost in the Middle" → model ignores info in middle of context.
  Cost grows linearly with context length.

CONTEXT MANAGEMENT STRATEGIES:

1. SLIDING WINDOW (simplest):
   Keep: system prompt + last 5 interactions
   Drop: older interactions
   
   Pro: Simple, bounded context
   Con: Loses important early information

2. SUMMARIZATION:
   After every 5 steps, summarize what happened:
   
   Original (2,500 tokens):
     Step 1: Searched for user → found user_id=123
     Step 2: Looked up orders → found 3 orders
     Step 3: Checked payments → duplicate charge on order #456
     Step 4: Calculated refund → $89.99
     Step 5: Issued refund → confirmation RF-789
   
   Summary (100 tokens):
     "Found user 123. Identified duplicate charge of $89.99 on 
      order #456. Refund RF-789 issued. Now need to apply discount."
   
   25× compression! Context stays small.

3. TIERED MEMORY:
   ┌─────────────────────────────────────────────┐
   │ HOT:  Last 3 messages (always in context)   │
   │ WARM: Key facts extracted from steps 1-N    │
   │       (user_id, amounts, decisions made)    │
   │ COLD: Full history stored in DB             │
   │       (retrieved only if needed)            │
   └─────────────────────────────────────────────┘
   
   Context = system_prompt + warm_facts + hot_messages
   Total: ~2000 tokens regardless of step count!

4. TOOL RESULT TRUNCATION:
   Many tool results are huge but agent needs only key info:
   
   Before: search_code("login") → 5000 lines of code (8K tokens!)
   After:  search_code("login") → top 5 results with line numbers 
           (500 tokens)
   
   Truncate or summarize tool outputs immediately.

5. STRUCTURED STATE:
   Maintain a JSON "scratchpad" instead of conversation:
   
   {
     "goal": "Refund duplicate charge + apply discount",
     "completed": ["found_user", "identified_duplicate", "issued_refund"],
     "remaining": ["apply_discount", "send_email"],
     "key_facts": {"user": "jane@...", "refund": "RF-789"},
     "current_step": "apply_discount"
   }
   
   This is always small and always up to date.
```

---

### Q5: Design an MCP server for a database. What tools should it expose?

**A:**
```
MCP SERVER: Database Access

TOOLS (carefully designed for safety + usability):

READ-ONLY TOOLS:
  1. query_table(table, filters, limit=100)
     "Get rows from a table with optional filters"
     Returns: JSON array of matching rows
     
  2. describe_table(table)
     "Get schema: column names, types, constraints"
     Returns: column definitions
     
  3. list_tables()
     "List all available tables"
     Returns: table names with descriptions
     
  4. run_sql(query)  — READ-ONLY!
     "Run a SELECT query (no INSERT/UPDATE/DELETE)"
     Validation: parse SQL, reject anything not SELECT
     Returns: query results

WRITE TOOLS (with guardrails):
  5. insert_row(table, data)
     "Insert a new row"
     Guardrails: validate schema, check required fields
     
  6. update_rows(table, filters, updates, dry_run=true)
     "Update rows matching filters"
     Default: dry_run=true (shows what WOULD change)
     Must call with dry_run=false to actually execute
     
  7. delete_rows(table, filters, dry_run=true)
     "Delete rows matching filters"
     HARD LIMIT: max 100 rows per call
     Requires explicit confirmation

SAFETY DESIGN:
  ┌──────────────────────────────────────────────────┐
  │ PRINCIPLE: Tools should be SAFE BY DEFAULT        │
  │                                                   │
  │ ✓ Read tools: unlimited, no confirmation needed  │
  │ ✓ Write tools: dry_run=true by default           │
  │ ✓ Delete tools: limited batch size + dry_run     │
  │ ✗ DROP TABLE: NOT EXPOSED (too dangerous)        │
  │ ✗ Raw write SQL: NOT EXPOSED (injection risk)    │
  │ ✗ Schema changes: NOT EXPOSED (infra concern)    │
  └──────────────────────────────────────────────────┘

IMPLEMENTATION PATTERN:
  @mcp.tool()
  async def query_table(table: str, filters: dict, limit: int = 100):
      # Validate table name (prevent injection)
      if table not in ALLOWED_TABLES:
          raise ValueError(f"Unknown table: {table}")
      
      # Build parameterized query (prevent SQL injection)
      query = f"SELECT * FROM {table} WHERE "
      conditions = []
      params = []
      for key, value in filters.items():
          if key not in get_columns(table):
              raise ValueError(f"Unknown column: {key}")
          conditions.append(f"{key} = %s")
          params.append(value)
      
      query += " AND ".join(conditions) if conditions else "1=1"
      query += f" LIMIT {min(limit, 1000)}"  # Hard cap
      
      return await db.execute(query, params)
```

---

### Q6: How do you handle agent failures gracefully?

**A:**
```
FAILURE MODES AND HANDLING:

1. TOOL FAILURE (API timeout, error):
   Strategy: Retry with backoff → fallback tool → escalate
   
   async def safe_tool_call(tool, args, retries=3):
       for attempt in range(retries):
           try:
               return await tool(**args)
           except TimeoutError:
               await asyncio.sleep(2 ** attempt)
           except PermissionError:
               return {"error": "Permission denied", "action": "escalate"}
           except Exception as e:
               if attempt == retries - 1:
                   return {"error": str(e), "action": "skip_or_escalate"}

2. LLM FAILURE (rate limit, content filter, hallucination):
   Strategy: Retry → fallback model → return partial result
   
   Models: [primary: "gpt-4o", fallback: "claude-3.5", emergency: "gpt-4o-mini"]

3. BUDGET EXCEEDED (too many steps/tokens):
   Strategy: Summarize progress → return partial result → offer to continue
   
   "I've completed 3 of 5 subtasks. Here's what's done:
    ✅ Found user account
    ✅ Identified the issue
    ✅ Calculated refund amount
    ⬜ Issue refund (budget limit reached)
    ⬜ Send confirmation
    Would you like me to continue?"

4. CONTEXT OVERFLOW (conversation too long):
   Strategy: Compress context → continue with summary
   
   When context > 80% of limit:
     1. Summarize all tool results to key findings
     2. Remove intermediate reasoning steps
     3. Keep: goal, key facts, remaining steps
     4. Continue with compressed context

5. STUCK/LOOP (no progress for 3+ steps):
   Strategy: Detect → try different approach → escalate
   
   if loop_detected:
       # Inject hint into context
       messages.append({
           "role": "system",
           "content": "You appear stuck. Try a completely different "
                      "approach or explain what's blocking you."
       })

GRACEFUL DEGRADATION HIERARCHY:
  Full success → Partial success → Graceful failure → Hard failure
  
  "Done! All tasks complete."
  "Done 3/5 tasks. Remaining need manual action because..."
  "I couldn't complete the task because X. Here's what I found..."
  "Error occurred. Task state saved. Resumable from step 3."
```

---

### Q7: How do you evaluate and monitor an agent in production?

**A:**
```
AGENT METRICS DASHBOARD:

RELIABILITY METRICS:
  ┌────────────────────────┬────────┬──────────┐
  │ Metric                 │ Target │ Alert at │
  ├────────────────────────┼────────┼──────────┤
  │ Task completion rate   │ >90%   │ <80%     │
  │ Tool call success rate │ >95%   │ <90%     │
  │ Loop detection rate    │ <5%    │ >10%     │
  │ Escalation rate        │ <15%   │ >25%     │
  │ Error rate             │ <2%    │ >5%      │
  └────────────────────────┴────────┴──────────┘

QUALITY METRICS:
  ┌────────────────────────┬────────┬──────────┐
  │ Metric                 │ Target │ Alert at │
  ├────────────────────────┼────────┼──────────┤
  │ User satisfaction      │ >4.0/5 │ <3.5     │
  │ Correct final answer   │ >85%   │ <75%     │
  │ Hallucination rate     │ <3%    │ >5%      │
  │ Unsafe action rate     │ 0%     │ >0%      │
  └────────────────────────┴────────┴──────────┘

EFFICIENCY METRICS:
  ┌────────────────────────┬────────┬──────────┐
  │ Metric                 │ Target │ Alert at │
  ├────────────────────────┼────────┼──────────┤
  │ Avg steps per task     │ <8     │ >15      │
  │ Avg tokens per task    │ <5K    │ >15K     │
  │ Avg cost per task      │ <$0.10 │ >$0.30   │
  │ Avg time per task      │ <30s   │ >60s     │
  │ Redundant tool calls   │ <10%   │ >20%     │
  └────────────────────────┴────────┴──────────┘

MONITORING IMPLEMENTATION:
  class AgentMonitor:
      def track_task(self, task_id, steps, result):
          metrics = {
              "task_id": task_id,
              "steps": len(steps),
              "tokens_used": sum(s.tokens for s in steps),
              "cost": sum(s.cost for s in steps),
              "duration_sec": (steps[-1].time - steps[0].time).seconds,
              "tool_calls": len([s for s in steps if s.tool_call]),
              "tool_errors": len([s for s in steps if s.tool_error]),
              "completed": result.success,
              "loop_detected": any(s.loop_flag for s in steps),
          }
          
          # Alert on anomalies
          if metrics["cost"] > 1.00:
              alert("High cost task", metrics)
          if metrics["steps"] > 20:
              alert("Long-running task", metrics)
          if metrics["tool_errors"] / max(metrics["tool_calls"], 1) > 0.3:
              alert("High tool failure rate", metrics)
          
          # Log for analysis
          self.log(metrics)
```

---

### Q8: Build a complete MCP-powered coding assistant agent.

**A:**
```
ARCHITECTURE:
  ┌──────────────────────────────────────────────────┐
  │              CODING ASSISTANT AGENT               │
  │                                                   │
  │  User: "Add pagination to the /users endpoint"   │
  │                                                   │
  │  ┌─────────────┐                                 │
  │  │  PLANNER    │ Understand task, create plan     │
  │  └──────┬──────┘                                 │
  │         ▼                                         │
  │  ┌─────────────┐    ┌────────────────────────┐   │
  │  │  EXECUTOR   │───→│ MCP Servers:           │   │
  │  │  (ReAct     │    │  📁 filesystem         │   │
  │  │   loop)     │    │  🔍 code-search        │   │
  │  │             │    │  🐙 github             │   │
  │  │             │    │  🧪 test-runner        │   │
  │  │             │    │  📖 docs               │   │
  │  └──────┬──────┘    └────────────────────────┘   │
  │         ▼                                         │
  │  ┌─────────────┐                                 │
  │  │  VERIFIER   │ Run tests, lint, review diff    │
  │  └─────────────┘                                 │
  └──────────────────────────────────────────────────┘

EXECUTION TRACE:
  
  PLAN:
  1. Find the /users endpoint code
  2. Understand current implementation
  3. Add pagination parameters (page, limit)
  4. Update database query with OFFSET/LIMIT
  5. Add pagination metadata to response
  6. Update tests
  7. Run tests and verify
  
  EXECUTION:
  
  Step 1: code_search("users endpoint route handler")
  → Found: src/routes/users.ts:45
  
  Step 2: read_file("src/routes/users.ts", lines=[40, 80])
  → Current code: simple GET /users returning all users
  
  Step 3: read_file("src/models/user.ts")
  → User model with Prisma ORM
  
  Step 4: edit_file("src/routes/users.ts", changes=[
    {
      "type": "modify",
      "description": "Add pagination to GET /users",
      "new_code": "..."  // page, limit params + OFFSET/LIMIT query
    }
  ])
  
  Step 5: read_file("tests/users.test.ts")
  → Existing tests for /users endpoint
  
  Step 6: edit_file("tests/users.test.ts", changes=[
    {
      "type": "add",
      "description": "Add pagination tests",
      "new_code": "..."  // test page=1&limit=10, defaults, edge cases
    }
  ])
  
  Step 7: run_tests("tests/users.test.ts")
  → Result: 8/8 passed ✅
  
  Step 8: create_pull_request(
    title="Add pagination to /users endpoint",
    body="Adds page and limit query params with cursor-based pagination...",
    branch="feature/users-pagination"
  )
  
  DONE! PR created.
```

---

## Production Scenario: Building an Enterprise AI Agent Platform

```python
class EnterpriseAgentPlatform:
    """
    Scenario: Your company wants to build an internal AI agent 
    platform that multiple teams can use to create custom agents.
    
    Requirements:
    - 10 teams, each with different agent needs
    - Shared MCP server infrastructure
    - Usage tracking and cost allocation
    - Security and access controls
    - 99.9% availability
    """
    
    PLATFORM_ARCHITECTURE = """
    ┌──────────────────────────────────────────────────────┐
    │                 AGENT PLATFORM                        │
    │                                                       │
    │  ┌─────────────────────────────────────────────────┐ │
    │  │              API GATEWAY                         │ │
    │  │  Auth │ Rate Limit │ Cost Track │ Route          │ │
    │  └─────────────────────────────────────────────────┘ │
    │                         │                             │
    │  ┌─────────────────────────────────────────────────┐ │
    │  │           AGENT RUNTIME                          │ │
    │  │                                                   │ │
    │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │ │
    │  │  │ Support  │ │ DevOps   │ │ Sales    │        │ │
    │  │  │ Agent    │ │ Agent    │ │ Agent    │  ...   │ │
    │  │  └──────────┘ └──────────┘ └──────────┘        │ │
    │  │                                                   │ │
    │  │  Shared: Context Manager, Loop Detector,         │ │
    │  │          Error Handler, Cost Controller           │ │
    │  └─────────────────────────────────────────────────┘ │
    │                         │                             │
    │  ┌─────────────────────────────────────────────────┐ │
    │  │           MCP SERVER REGISTRY                    │ │
    │  │                                                   │ │
    │  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │ │
    │  │  │Slack │ │Jira  │ │DB    │ │GitHub│ │PagerD│ │ │
    │  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ │ │
    │  │                                                   │ │
    │  │  Access control: each agent has a tool allowlist  │ │
    │  └─────────────────────────────────────────────────┘ │
    │                         │                             │
    │  ┌─────────────────────────────────────────────────┐ │
    │  │           LLM PROVIDER LAYER                     │ │
    │  │  OpenAI │ Anthropic │ Self-hosted │ Routing      │ │
    │  └─────────────────────────────────────────────────┘ │
    └──────────────────────────────────────────────────────┘
    """
    
    AGENT_DEFINITION = """
    Each team defines their agent with a YAML config:
    
    # support-agent.yaml
    name: customer-support-agent
    team: support
    model:
      primary: gpt-4o
      fallback: claude-3.5-sonnet
      reasoning: o3  # for complex cases
    
    tools:
      - mcp://slack/send_message        # Can send Slack messages
      - mcp://jira/create_ticket        # Can create Jira tickets
      - mcp://database/query_table      # Can read from DB
      - mcp://database/update_rows      # Can update DB (with approval)
      # NOT allowed: mcp://github/*     # No code access
      # NOT allowed: mcp://database/delete_rows  # No deletions
    
    limits:
      max_steps: 15
      max_tokens: 10000
      max_cost_per_task: $0.50
      max_daily_cost: $100
      require_approval_for:
        - mcp://database/update_rows
        - mcp://jira/create_ticket (priority=critical)
    
    system_prompt: |
      You are a customer support agent. 
      Your goal is to resolve customer issues quickly and accurately.
      Always verify information before making changes.
      Escalate to human if customer is upset or issue is complex.
    """
    
    COST_ALLOCATION = """
    COST TRACKING PER TEAM:
    
    ┌───────────────┬──────────┬──────────┬──────────┬──────────┐
    │ Team          │ Tasks    │ LLM Cost │ Tool Cost│ Total    │
    ├───────────────┼──────────┼──────────┼──────────┼──────────┤
    │ Support       │ 5,200    │ $420     │ $50      │ $470     │
    │ DevOps        │ 1,100    │ $890     │ $120     │ $1,010   │
    │ Sales         │ 3,400    │ $210     │ $30      │ $240     │
    │ Engineering   │ 2,800    │ $1,500   │ $200     │ $1,700   │
    │ Data Science  │ 600      │ $2,100   │ $340     │ $2,440   │
    ├───────────────┼──────────┼──────────┼──────────┼──────────┤
    │ TOTAL         │ 13,100   │ $5,120   │ $740     │ $5,860   │
    └───────────────┴──────────┴──────────┴──────────┴──────────┘
    
    Cost per task avg: $0.45
    vs. manual handling: ~$12/task (15 min × $48/hr)
    ROI: 26:1 ← each $1 on agents saves $26 in human time
    """
    
    SECURITY_MODEL = """
    MULTI-LAYER SECURITY:
    
    Layer 1: AUTHENTICATION
      - API key per team
      - JWT tokens per user
      - MCP server credentials managed centrally (vault)
    
    Layer 2: AUTHORIZATION (per agent)
      - Tool allowlist (only approved MCP tools)
      - Data access controls (which tables/columns)
      - Action limits (read vs. write vs. delete)
    
    Layer 3: RUNTIME GUARDRAILS
      - Prompt injection detection on every input
      - PII detection on every output
      - Sensitive data masking in logs
      - Cost limits per task and per day
    
    Layer 4: AUDIT
      - Every agent action logged to immutable audit log
      - Searchable by: team, user, agent, tool, timestamp
      - Weekly automated review of high-risk actions
      - 90-day retention for compliance
    
    Layer 5: INCIDENT RESPONSE
      - Kill switch: disable any agent instantly
      - Rollback: undo last N actions by an agent
      - Alert: anomaly detection on agent behavior
    """
```

---

## Production Scenario: Agent Orchestration — Multi-Agent System

```python
class MultiAgentOrchestrator:
    """
    Scenario: Complex tasks that require multiple specialized agents 
    working together.
    
    Example: "Investigate why response times increased 50% this week"
    """
    
    AGENT_TEAM = """
    ┌──────────────────────────────────────────────────────────┐
    │                   ORCHESTRATOR AGENT                      │
    │  Breaks down task, assigns to specialists, synthesizes   │
    │  Model: o3 (reasoning, planning)                         │
    └──────────────────────────┬───────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ METRICS      │  │ CODE         │  │ INFRA        │
    │ AGENT        │  │ AGENT        │  │ AGENT        │
    │              │  │              │  │              │
    │ Tools:       │  │ Tools:       │  │ Tools:       │
    │ - Datadog    │  │ - GitHub     │  │ - AWS/GCP    │
    │ - Grafana    │  │ - code-search│  │ - K8s        │
    │ - PagerDuty  │  │ - git-log    │  │ - Terraform  │
    │              │  │              │  │              │
    │ Model: GPT-4o│  │ Model: GPT-4o│  │ Model: GPT-4o│
    └──────────────┘  └──────────────┘  └──────────────┘
    """
    
    EXECUTION = """
    ORCHESTRATOR PLAN:
    1. Metrics Agent: Get response time data for the past 2 weeks
    2. Metrics Agent: Identify when exactly the increase started
    3. Code Agent: Check what code was deployed around that time
    4. Infra Agent: Check for infrastructure changes
    5. Synthesize findings into root cause report
    
    PARALLEL EXECUTION:
    
    [Metrics Agent] ──────────────────────────────────┐
    Query: "P95 response time, /api/*, last 14 days"  │
    Result: P95 jumped from 200ms to 320ms on Oct 22  │
                                                       │
    [Code Agent] ─────────────────────────────────────┤
    Query: "Deployments between Oct 21-23"             │
    Result: PR #4521 deployed Oct 22 — "Add user       │
            activity logging to all API endpoints"     │
                                                       │
    [Infra Agent] ────────────────────────────────────┤
    Query: "Resource changes, Oct 21-23"               │
    Result: No infrastructure changes. CPU/memory      │
            normal. DB connections increased 2x.        │
                                                       ▼
    
    ORCHESTRATOR SYNTHESIS:
    ┌──────────────────────────────────────────────────┐
    │ ROOT CAUSE ANALYSIS                              │
    │                                                   │
    │ Finding: PR #4521 added synchronous activity      │
    │ logging to ALL API endpoints. Each request now    │
    │ makes an extra DB write, doubling DB connections  │
    │ and adding ~120ms latency.                        │
    │                                                   │
    │ Evidence:                                         │
    │ - P95 jumped exactly when PR was deployed         │
    │ - DB connections doubled (correlates)             │
    │ - No infrastructure changes (rules out infra)    │
    │                                                   │
    │ Recommendations:                                  │
    │ 1. Make activity logging ASYNC (background queue) │
    │ 2. Batch DB writes (buffer 100 logs, write once) │
    │ 3. Expected improvement: -100ms latency          │
    │                                                   │
    │ Created: JIRA-5678 (P1, assigned to backend team)│
    └──────────────────────────────────────────────────┘
    
    Total cost: $0.85 (3 agents + orchestrator)
    Total time: 45 seconds (parallel execution)
    Human equivalent: 2-4 hours of investigation
    """
```

---

## Quick Reference: Agent & MCP Cheat Sheet

```
AGENT PATTERNS:
  Simple task (1-3 steps)     → ReAct with GPT-4o
  Complex task (5-15 steps)   → Plan-and-Execute with o3 planner
  Multi-domain task           → Multi-agent orchestration
  Ongoing task (monitoring)   → Event-driven agent loop
  Coding task                 → Agent + filesystem/git MCP servers

MCP SERVER DESIGN:
  ✓ DO: Expose focused, well-named tools
  ✓ DO: Make write operations require confirmation (dry_run)
  ✓ DO: Validate all inputs server-side
  ✓ DO: Return structured data (JSON)
  ✗ DON'T: Expose dangerous operations (DROP, DELETE ALL)
  ✗ DON'T: Trust the LLM to validate inputs
  ✗ DON'T: Return huge payloads (truncate/paginate)

CONTEXT ENGINEERING:
  1. System prompt: clear role, constraints, available tools
  2. User message: the task/goal
  3. Conversation: managed to stay under 50% of context window
  4. Tool results: truncated/summarized immediately
  5. Memory: structured state (JSON) > raw conversation

COST CONTROL:
  Set hard limits: max steps, max tokens, max $ per task
  Track: cost per task, per team, per model
  Optimize: route to cheapest model that works
  Cache: semantic cache for repeated queries
  Alert: when any limit is >80% consumed
```

---

*End of Module 09 — You've completed the full AI Engineering Deep Dive! 🎓*

*Return to [Curriculum Overview](../README.md)*
