# Module 08 — Q&A + Production Scenarios: Reasoning & Verification

---

## Top 20 Interview Questions & Answers

### Q1: What is Chain of Thought (CoT) prompting and why does it work?

**A:**
```
WITHOUT CoT:
  Q: "Roger has 5 tennis balls. He buys 2 cans of 3 balls each. 
      How many does he have now?"
  A: "11" ← CORRECT, but the model might get it wrong at scale

WITH CoT:
  Q: Same question
  A: "Roger starts with 5 balls.
      He buys 2 cans, each with 3 balls.
      2 cans × 3 balls = 6 new balls.
      5 + 6 = 11 balls."
  
  By SHOWING ITS WORK, the model:
  1. Breaks complex problems into simple sub-steps
  2. Uses intermediate results (like scratch paper)
  3. Can catch its own mistakes mid-reasoning
  4. Accuracy on math/logic: 60% → 90%+ improvement!

WHY IT WORKS (mechanistically):
  Transformers process ALL tokens in parallel.
  Each generated token is one "step" of computation.
  
  Without CoT: model must solve in 1 step (1 forward pass for answer)
  With CoT: model gets N steps (N tokens of reasoning)
  
  Each reasoning token adds one more layer of "serial computation."
  The model literally gets more compute by writing more.
  
  It's like the difference between:
  - Mental math: 847 × 293 = ??? (hard in your head)
  - Written math: 847 × 293 = 7 × 293 + 40 × 293 + 800 × 293 = ... (easy!)

THREE VARIANTS:
  1. Zero-shot CoT: Add "Let's think step by step" to prompt
  2. Few-shot CoT: Show examples with reasoning chains
  3. Self-consistency: Generate 5 CoT paths, take majority vote
     Accuracy: zero-shot < few-shot < self-consistency
```

---

### Q2: When should you use a reasoning model (o1, o3) vs. a standard model (GPT-4o)?

**A:**
```
REASONING MODEL (o1/o3/DeepSeek-R1):
  - Internally generates a long "thinking" chain
  - Uses 10-100x more tokens (most are hidden)
  - Slower and more expensive
  - Better at: math, logic, coding, science, planning
  
STANDARD MODEL (GPT-4o, Claude 3.5):
  - Generates response directly
  - Fast, cheap
  - Better at: writing, translation, simple Q&A, creativity

DECISION MATRIX:
┌────────────────────────┬──────────┬──────────────┬────────────┐
│ Task                   │ Standard │ Reasoning    │ Winner     │
├────────────────────────┼──────────┼──────────────┼────────────┤
│ "Write a blog post"   │ ✓ 95%    │ ✓ 95%        │ Standard   │
│                        │ $0.01    │ $0.15        │ (cheaper)  │
├────────────────────────┼──────────┼──────────────┼────────────┤
│ "Fix this bug" (easy) │ ✓ 90%    │ ✓ 95%        │ Standard   │
│                        │ $0.02    │ $0.20        │ (fast)     │
├────────────────────────┼──────────┼──────────────┼────────────┤
│ "Solve this math proof"│ ✗ 40%   │ ✓ 85%        │ Reasoning  │
│                        │ $0.01    │ $0.30        │ (accuracy) │
├────────────────────────┼──────────┼──────────────┼────────────┤
│ "Design a system"     │ ~ 70%    │ ✓ 90%        │ Reasoning  │
│ (complex architecture)│ $0.05    │ $0.50        │            │
├────────────────────────┼──────────┼──────────────┼────────────┤
│ "Classify this email" │ ✓ 94%    │ ✓ 95%        │ Standard   │
│                        │ $0.001   │ $0.05        │ (50x cost!)│
├────────────────────────┼──────────┼──────────────┼────────────┤
│ "Multi-step planning" │ ~ 60%    │ ✓ 88%        │ Reasoning  │
│                        │ $0.03    │ $0.40        │            │
└────────────────────────┴──────────┴──────────────┴────────────┘

RULE OF THUMB:
  If the task needs "thinking" → reasoning model
  If the task needs "doing" → standard model
  If unsure → try standard first, escalate if quality is low
```

---

### Q3: What is Tree of Thought (ToT)? How is it different from Chain of Thought?

**A:**
```
CHAIN OF THOUGHT (CoT):
  One linear chain of reasoning steps
  
  Problem → Step 1 → Step 2 → Step 3 → Answer
  
  If Step 2 is wrong, the whole chain fails.
  No way to explore alternatives.

TREE OF THOUGHT (ToT):
  Multiple branches explored in parallel
  
  Problem ─┬─ Idea A ─┬─ A1 → Score: 7/10
            │          └─ A2 → Score: 3/10 ← prune
            ├─ Idea B ─┬─ B1 → Score: 9/10 ← BEST
            │          └─ B2 → Score: 6/10
            └─ Idea C ─── C1 → Score: 2/10 ← prune
  
  ToT uses the LLM itself to:
  1. GENERATE multiple reasoning paths
  2. EVALUATE which paths are promising
  3. PRUNE bad paths early
  4. EXPLORE deeper on good paths
  
  Like BFS/DFS on a tree of ideas!

WHEN ToT >> CoT:
  - Puzzle solving (24 game, crosswords): 4% → 74% accuracy
  - Creative writing (explore different angles)
  - Planning (consider multiple strategies)
  - Debugging (try multiple hypotheses)

WHEN CoT is enough:
  - Straightforward math
  - Step-by-step procedures
  - Most everyday reasoning

COST:
  CoT: 1 chain × ~500 tokens = 500 tokens
  ToT: 3 branches × 3 depths × 500 tokens = 4,500 tokens
  ToT is ~10x more expensive but dramatically better for hard problems.
```

---

### Q4: How does function calling / tool use work in LLMs?

**A:**
```
CONCEPT:
  LLMs can't do math, access databases, or browse the web.
  But they CAN decide WHEN and HOW to call external tools.
  
FLOW:
  ┌───────┐    ┌─────────┐    ┌────────┐    ┌───────┐
  │ User  │───→│  LLM    │───→│ Tool   │───→│ LLM   │
  │ query │    │ decides │    │ runs   │    │ final │
  │       │    │ to call │    │ returns│    │ answer│
  └───────┘    └─────────┘    └────────┘    └───────┘

EXAMPLE:
  User: "What's the weather in Tokyo?"
  
  LLM output (not shown to user):
  {
    "tool": "get_weather",
    "arguments": { "city": "Tokyo" }
  }
  
  System executes: get_weather("Tokyo") → "22°C, partly cloudy"
  
  LLM receives result, generates final answer:
  "It's currently 22°C and partly cloudy in Tokyo."

HOW THE LLM LEARNS THIS:
  1. Tool definitions in system prompt:
     "You have access to: get_weather(city: string) → weather info"
  
  2. Model was fine-tuned on tool-calling examples
     (OpenAI, Anthropic train their models on thousands of tool patterns)
  
  3. Model outputs structured JSON when it needs a tool
     (instead of natural language)

PARALLEL TOOL CALLS:
  User: "Compare weather in Tokyo, NYC, and London"
  
  LLM: [
    {"tool": "get_weather", "args": {"city": "Tokyo"}},
    {"tool": "get_weather", "args": {"city": "New York"}},
    {"tool": "get_weather", "args": {"city": "London"}}
  ]
  
  All three execute in parallel → faster response!

PRODUCTION GOTCHAS:
  1. Model might hallucinate tool names that don't exist
  2. Model might call tools with wrong argument types
  3. Tool execution might fail → need error handling
  4. Recursive tool calls → need depth limits
  5. Expensive tools → need confirmation before execution
```

---

### Q5: How do you diagnose when an LLM agent gets stuck in a loop?

**A:**
```
COMMON LOOP PATTERNS:

1. REPETITIVE ACTION LOOP:
   Agent: search("python error handling")
   Agent: search("python error handling")   ← same query!
   Agent: search("python error handling")   ← stuck!
   
   CAUSE: Model doesn't process tool results properly
   FIX: Track action history, reject duplicate actions
   
2. PLANNING LOOP:
   Agent: "Let me think about the approach..."
   Agent: "Actually, let me reconsider..."
   Agent: "On second thought, let me think again..."
   
   CAUSE: Insufficient decision-making confidence
   FIX: Add "You MUST take an action. Do not just think." to prompt
   
3. CORRECTION LOOP:
   Agent: write_file("app.py", code_v1)
   Agent: write_file("app.py", code_v2)    ← fixes v1 bug, introduces v2 bug
   Agent: write_file("app.py", code_v3)    ← fixes v2 bug, reintroduces v1 bug
   
   CAUSE: Tunnel vision — fixing one thing breaks another
   FIX: Show full file context, not just the error

4. PERMISSION LOOP:
   Agent: access_database() → Error: unauthorized
   Agent: access_database() → Error: unauthorized
   Agent: access_database() → Error: unauthorized
   
   CAUSE: Model doesn't understand the error is permanent
   FIX: Classify errors as retryable vs. permanent

DETECTION SYSTEM:
  class LoopDetector:
      def __init__(self, max_similar=3, max_total=20):
          self.actions = []
          self.max_similar = max_similar
          self.max_total = max_total
      
      def check(self, action):
          self.actions.append(action)
          
          # Check total iterations
          if len(self.actions) > self.max_total:
              return "STOP: Too many iterations"
          
          # Check repeated actions
          recent = self.actions[-self.max_similar:]
          if len(set(str(a) for a in recent)) == 1 and len(recent) == self.max_similar:
              return "STOP: Repeated same action 3 times"
          
          # Check oscillation (A→B→A→B)
          if len(self.actions) >= 4:
              if (self.actions[-1] == self.actions[-3] and 
                  self.actions[-2] == self.actions[-4]):
                  return "STOP: Oscillating between two actions"
          
          return "OK"
```

---

### Q6: What is self-consistency in CoT? When does it help most?

**A:**
```
SELF-CONSISTENCY: Generate multiple CoT paths, take majority vote.

EXAMPLE:
  Q: "A store has 48 items. 1/3 are books, 1/4 of the rest are pens. 
      How many pens?"

  Path 1 (temperature=0.7):
    "48 items. 1/3 are books = 16 books. Rest = 32. 
     1/4 of 32 = 8 pens." → 8 ✓

  Path 2 (temperature=0.7):
    "48 items. 1/3 = 16 books. Remaining = 48-16 = 32.
     1/4 pens = 32/4 = 8 pens." → 8 ✓

  Path 3 (temperature=0.7):
    "48 items. 1/3 books, 1/4 pens. 48/3 = 16 books.
     48/4 = 12 pens." → 12 ✗ (wrong: applied 1/4 to total)

  Path 4: → 8 ✓
  Path 5: → 8 ✓

  MAJORITY VOTE: 8 (4 out of 5 paths agree) → CORRECT ✓
  
  Without self-consistency: 80% chance of correct (1 sample)
  With self-consistency (5 samples): 97% chance (majority vote)

WHEN IT HELPS MOST:
  ✅ Math problems (different valid approaches)
  ✅ Logic puzzles (multiple reasoning paths)
  ✅ When accuracy > speed/cost
  
WHEN IT DOESN'T HELP:
  ❌ Creative tasks (no "right answer" to vote on)
  ❌ Simple tasks (model already 95%+ accurate)
  ❌ Budget-constrained (5× cost for 5 paths)

COST: N × single_query_cost
  N=5: 5× cost for ~3-5% accuracy boost
  N=10: 10× cost for ~5-8% accuracy boost
  N=20: diminishing returns
```

---

### Q7: How do you evaluate if an LLM's reasoning is correct?

**A:**
```
CHALLENGE: How do you verify free-form reasoning chains?

METHOD 1: PROCESS REWARD MODEL (PRM)
  Score EACH step of reasoning, not just the final answer.
  
  Step 1: "There are 48 items" → Score: 0.99 ✓
  Step 2: "1/3 are books = 16" → Score: 0.98 ✓
  Step 3: "Remaining = 30"     → Score: 0.15 ✗ (should be 32!)
  
  PRM catches errors at the step level.
  Training data: human annotators mark each step right/wrong.

METHOD 2: OUTCOME REWARD MODEL (ORM)
  Only check the final answer.
  
  Reasoning → Final answer → Compare to ground truth
  
  Cheaper to build but can't identify WHERE reasoning fails.

METHOD 3: SELF-VERIFICATION
  Ask the model to check its own work!
  
  Prompt 1: "Solve: [problem]"
  Answer: "The answer is 42."
  
  Prompt 2: "Check this solution step by step. 
             Is every step logically valid?"
  Verification: "Step 3 has an error: 5 × 8 = 40, not 45."
  
  Surprisingly effective! Catches ~60% of errors.

METHOD 4: CODE VERIFICATION (for math/logic)
  Convert reasoning to executable code:
  
  Reasoning: "48 items, 1/3 books, 1/4 of rest are pens"
  Code: total=48; books=total//3; rest=total-books; pens=rest//4
  Execute: pens = 8 ✓
  
  If code output ≠ reasoning output → flag for review.

PRODUCTION SETUP: Combine methods
  Low-risk: Self-verification only (cheapest)
  Medium-risk: Self-verification + code execution
  High-risk: PRM + human review for flagged cases
```

---

### Q8: Your agent needs to book a flight. Design the reasoning and tool-use flow.

**A:**
```
TASK: "Book the cheapest direct flight from SFO to NYC on Dec 15"

APPROACH 1: ReAct (Reasoning + Acting)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Thought: I need to search for flights from SFO to NYC on Dec 15.
Action: search_flights(from="SFO", to="NYC", date="2025-12-15", 
                        nonstop=true)
Observation: [
  {flight: "UA123", price: $289, depart: "8am", arrive: "4:30pm"},
  {flight: "DL456", price: $312, depart: "10am", arrive: "6:30pm"},
  {flight: "AA789", price: $275, depart: "6am", arrive: "2:30pm"},
]

Thought: AA789 is cheapest at $275. Before booking, I should 
         check seat availability and user preferences.
Action: check_availability(flight="AA789", class="economy")
Observation: {available: true, seats_left: 12}

Thought: Seats available. Let me check user's past preferences.
Action: get_user_preferences(user_id="user_123")
Observation: {prefers_aisle: true, loyalty: "United MileagePlus"}

Thought: User has United loyalty. UA123 is $14 more but earns miles.
         I should present both options and let user decide.
Action: present_options(options=[
  {"rec": "AA789", "price": "$275", "note": "Cheapest"},
  {"alt": "UA123", "price": "$289", "note": "Earns United miles"}
])

KEY DESIGN DECISIONS:
  1. Agent does NOT auto-book — presents options for confirmation
  2. Agent considers user context (loyalty program)
  3. Each step has clear reasoning before action
  4. Agent handles edge cases (sold out → search alternatives)

APPROACH 2: Plan-and-Execute
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plan:
  1. Search direct flights SFO→NYC on Dec 15
  2. Filter by price (ascending)
  3. Check availability of top 3
  4. Check user preferences
  5. Present options with recommendation
  
Execute: [runs each step, re-plans if something fails]

ADVANTAGE over ReAct: plan is explicit, easier to debug and audit.
DISADVANTAGE: less flexible if unexpected things happen mid-execution.
```

---

## Production Scenario: Building a Multi-Step Reasoning Agent

```python
class ProductionReasoningAgent:
    """
    Scenario: Build an agent that handles complex customer support 
    queries requiring multi-step reasoning and tool use.
    
    Example: "I was charged twice for order #12345. I want a refund 
    for the duplicate and a 20% discount on my next order."
    """
    
    ARCHITECTURE = """
    ┌───────────────────────────────────────────────────────┐
    │                  REASONING AGENT                      │
    │                                                       │
    │  ┌─────────┐   ┌──────────┐   ┌────────────────────┐│
    │  │ Planner │──→│ Executor │──→│ Verifier           ││
    │  │ (o3)    │   │ (GPT-4o) │   │ (rules + GPT-4o)  ││
    │  └─────────┘   └──────────┘   └────────────────────┘│
    │       │              │                │              │
    │       ▼              ▼                ▼              │
    │  ┌──────────────────────────────────────────────┐   │
    │  │              TOOL LAYER                       │   │
    │  │  order_lookup │ payment_check │ refund_issue  │   │
    │  │  discount_add │ email_send    │ escalate      │   │
    │  └──────────────────────────────────────────────┘   │
    └───────────────────────────────────────────────────────┘
    """
    
    EXECUTION_TRACE = """
    User: "I was charged twice for order #12345. I want a refund 
           for the duplicate and a 20% discount on my next order."
    
    ━━━ PLANNER (reasoning model) ━━━
    Plan:
      1. Look up order #12345 and verify it exists
      2. Check payment records for duplicate charges
      3. If duplicate confirmed: issue refund for extra charge
      4. Check if we can offer 20% discount (policy check)
      5. If yes: add discount code to account
      6. Send confirmation email
    
    ━━━ EXECUTOR (standard model + tools) ━━━
    
    Step 1: order_lookup(order_id="12345")
    Result: {
      "order_id": "12345",
      "user": "jane@example.com",
      "amount": "$89.99",
      "date": "2025-10-20",
      "status": "delivered"
    }
    
    Step 2: payment_check(order_id="12345")
    Result: {
      "charges": [
        {"amount": "$89.99", "date": "2025-10-20", "status": "settled"},
        {"amount": "$89.99", "date": "2025-10-20", "status": "settled"}
      ],
      "duplicate_detected": true  ← CONFIRMED
    }
    
    Step 3: refund_issue(order_id="12345", amount="$89.99", 
                         reason="duplicate_charge")
    Result: {"refund_id": "RF-98765", "status": "processing", 
             "eta": "3-5 business days"}
    
    Step 4: policy_check(action="discount", percent=20, 
                         reason="duplicate_charge_compensation")
    Result: {"allowed": true, "max_discount": 25%, 
             "requires_approval": false}
    
    Step 5: discount_add(user="jane@example.com", percent=20, 
                         valid_until="2026-01-20")
    Result: {"code": "SORRY20", "applied": true}
    
    Step 6: email_send(
      to="jane@example.com",
      subject="Refund processed + 20% discount",
      body="..."
    )
    
    ━━━ VERIFIER ━━━
    Checks:
      ✓ Refund amount matches duplicate charge ($89.99)
      ✓ Discount within policy limits (20% ≤ 25% max)
      ✓ All requested actions completed
      ✓ Email sent with correct details
      ✓ No unauthorized actions taken
    
    ━━━ FINAL RESPONSE TO USER ━━━
    "I've confirmed the duplicate charge on order #12345. Here's 
     what I've done:
     
     1. ✅ Refund of $89.99 initiated (Ref: RF-98765)
        Expected in 3-5 business days
     2. ✅ 20% discount code: SORRY20
        Valid until January 20, 2026
     
     I apologize for the inconvenience. Is there anything else 
     I can help with?"
    """
    
    ERROR_HANDLING = """
    WHAT IF things go wrong:
    
    Scenario A: Order not found
      → "I couldn't find order #12345. Could you double-check 
         the order number? You can find it in your confirmation email."
    
    Scenario B: No duplicate charge found
      → "I checked the payment records for order #12345 and only 
         see one charge of $89.99. Could you share a screenshot 
         of the duplicate charge from your bank statement?"
    
    Scenario C: Refund system is down
      → "I've confirmed the duplicate charge but our refund system 
         is temporarily unavailable. I've escalated this to our 
         finance team with priority. You'll receive a refund within 
         24 hours. Reference: ESC-54321."
    
    Scenario D: 20% discount exceeds policy
      → "I can offer a 15% discount (our maximum for this situation). 
         Would you like me to apply that, or would you prefer to 
         speak with a manager about the 20% request?"
    """
```

---

## Production Scenario: Reasoning Failure Post-Mortem

```python
class ReasoningFailurePostMortem:
    """
    Scenario: Your reasoning agent made a costly mistake. 
    Conduct a post-mortem and implement fixes.
    
    INCIDENT: Agent approved a $50,000 refund instead of $500.
    The customer's order was $500, but agent misread "$500.00" 
    as "$50,000" due to a formatting issue in the tool response.
    """
    
    ROOT_CAUSE_ANALYSIS = """
    TIMELINE:
    14:23 - Customer requests refund for order #98765 ($500.00)
    14:23 - Agent calls order_lookup → returns amount="$500.00"
    14:23 - Agent calls refund_issue(amount="$50000")  ← BUG!
    14:23 - Refund system processes $50,000 refund
    14:24 - Verification check passes (amount > 0: ✓)   ← WEAK CHECK
    16:45 - Finance team notices anomaly in daily report
    16:50 - Refund reversed, incident declared
    
    ROOT CAUSE:
    The tool returned amount as a string "$500.00"
    The LLM parsed "500.00" as "50000" (dropped the decimal)
    The verification only checked "amount > 0", not "amount matches order"
    
    CONTRIBUTING FACTORS:
    1. No maximum refund limit in the agent's tool permissions
    2. No sanity check: "refund amount should equal order amount"
    3. Amount was a string, not a number (parsing ambiguity)
    4. No human-in-the-loop for amounts above threshold
    """
    
    FIXES = """
    FIX 1: GUARDRAILS ON TOOL PARAMETERS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Before: refund_issue(amount: string)  # Any amount!
      After:  refund_issue(order_id: string) # Amount auto-fetched
      
      The tool itself looks up the correct amount.
      Agent never specifies dollar amounts directly.
    
    FIX 2: AMOUNT VERIFICATION
    ━━━━━━━━━━━━━━━━━━━━━━━━━━
      def verify_refund(order_id, requested_amount):
          order = lookup_order(order_id)
          if abs(requested_amount - order.amount) > 0.01:
              raise ValueError(
                  f"Refund ${requested_amount} doesn't match "
                  f"order amount ${order.amount}"
              )
    
    FIX 3: TIERED APPROVAL
    ━━━━━━━━━━━━━━━━━━━━━━
      Refund < $100:    → Auto-approve
      $100 - $1,000:    → Agent verifier checks
      $1,000 - $10,000: → Human approval required
      > $10,000:        → Senior manager approval
    
    FIX 4: USE STRUCTURED DATA, NOT STRINGS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Before: amount = "$500.00"  (string, ambiguous)
      After:  amount = 500.00     (float, unambiguous)
              currency = "USD"    (explicit)
    
    FIX 5: REAL-TIME ANOMALY DETECTION
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      Flag any refund where:
      - Amount > 2× order value
      - Amount > $5,000 (unusual for our business)
      - Multiple refunds in 1 hour for same user
      - Refund amount is a round number (common LLM hallucination)
    """
    
    PREVENTION_CHECKLIST = """
    AGENT SAFETY CHECKLIST (use for any production agent):
    
    □ All financial operations have amount limits
    □ Destructive operations require confirmation
    □ Tool inputs are validated (type, range, format)
    □ Tool outputs are structured (JSON, not free text)
    □ Human-in-the-loop for high-risk actions
    □ Agent actions are logged with full reasoning trace
    □ Anomaly detection on agent behavior patterns
    □ Rate limiting on sensitive operations
    □ Rollback capability for all operations
    □ Regular audit of agent decisions (sample 5% daily)
    """
```

---

## Quick Reference: Reasoning Techniques Comparison

```
┌─────────────────────┬──────────┬──────────┬─────────┬──────────┐
│ Technique           │ Cost     │ Accuracy │ Latency │ Best for │
├─────────────────────┼──────────┼──────────┼─────────┼──────────┤
│ Direct prompting    │ 1×       │ Baseline │ Fast    │ Simple Q │
│ Zero-shot CoT       │ 1.5×     │ +15-30%  │ Medium  │ Math     │
│ Few-shot CoT        │ 2×       │ +20-40%  │ Medium  │ Complex  │
│ Self-consistency    │ 5-10×    │ +5-15%   │ Slow    │ Critical │
│                     │          │ (on CoT) │         │ accuracy │
│ Tree of Thought     │ 10-50×   │ +40-70%  │ V.Slow  │ Puzzles, │
│                     │          │ (on hard)│         │ planning │
│ Reasoning model     │ 10-100×  │ Best     │ Slow    │ STEM,    │
│ (o1/o3)             │          │          │         │ code     │
│ ReAct (tool use)    │ 2-5×     │ N/A      │ Medium  │ Actions  │
│ Plan-and-Execute    │ 3-10×    │ N/A      │ Slow    │ Complex  │
│                     │          │          │         │ workflows│
└─────────────────────┴──────────┴──────────┴─────────┴──────────┘

RULE OF THUMB:
  Start with the cheapest technique that meets your accuracy bar.
  Escalate only when you have evidence the simpler approach fails.
```

---

*Continue to [Module 09 QA](../09-mcp-and-agents/QA-production-scenarios.md)*
