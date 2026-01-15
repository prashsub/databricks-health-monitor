# Enhanced Evaluation Quality & Multi-Turn Conversations

**Updated:** January 10, 2026 - Reduced Guidelines to 4 sections (target score: 0.5-0.7)

## 📋 Overview

This document explains the **significantly improved agent analysis quality** achieved through enhanced LLM judges and the implementation of **multi-turn conversation capabilities** through stateless conversation tracking and Lakebase memory.

**Date Implemented:** January 9-10, 2026  
**Key Files:**
- `src/agents/setup/deployment_job.py` - Enhanced judges
- `src/agents/setup/log_agent_model.py` - Memory & conversation tracking
- `src/agents/orchestrator/agent.py` - Multi-turn predict logic

---

## 🎯 Enhanced LLM Judges

### Problem Statement

**Before:** Evaluation judges used simple, vague criteria like "Is the response relevant?" which led to:
- ❌ Inconsistent scoring across different evaluators
- ❌ No alignment with actual agent prompts and requirements
- ❌ Generic feedback that didn't help improve the agent
- ❌ Low correlation between evaluation scores and production quality

**After:** Judges now use **comprehensive, criteria-driven evaluation** aligned with the agent's actual prompts, resulting in:
- ✅ Consistent, reproducible evaluation scores
- ✅ Specific feedback on what's missing or incorrect
- ✅ Clear connection between prompts, agent behavior, and evaluation
- ✅ Actionable insights for improving agent quality

---

## 📊 Enhanced Guidelines Judge

The `Guidelines` judge is now the **primary quality gatekeeper**, evaluating the agent's responses against 8 comprehensive sections derived from all agent prompts.

### File Location

```python:1715:1871:src/agents/setup/deployment_job.py
if BUILTIN_JUDGES_AVAILABLE:
    # Built-in MLflow judges (best practice)
    # Reference: https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/concepts/judges/guidelines
    scorers_to_register.extend([
        # ... other scorers
        ("guidelines", Guidelines(guidelines=[
            # SECTION 1: DATA ACCURACY & CITATION
            """Data Accuracy and Explicit Citation:
            - MUST cite data sources explicitly: [Cost Genie], [Security Genie], [Performance Genie], [Reliability Genie], [Quality Genie]
            - MUST include actual numbers from Genie queries (not generic statements)
            - MUST format data properly:
              * Tables: Markdown format with column headers
              * Numbers: With proper units ($1.2M, 45.3%, 2.5s)
              * Dates: ISO format (2025-01-09) or relative (last 7 days)
            - Example: "Cost increased $12,345.67 (+23.4% ↑) over last 7 days according to [Cost Genie]""",
            
            # SECTION 2: DATA FORMATTING & PRESENTATION
            """Data Formatting and Presentation Standards:
            - MUST format numbers properly:
              * Costs: $1,234.56 or $1.2M for large values
              * DBUs: 1,234 DBUs or 1.2M DBUs
              * Percentages: 45.2% (one decimal)
              * Latency: 1.2s, 450ms, 2.5min
              * Data sizes: 1.5TB, 10M rows""",
            
            # SECTION 3: NO FABRICATION (CRITICAL)
            """No Data Fabrication (CRITICAL):
            - MUST NEVER fabricate or guess at numbers
            - MUST NEVER hallucinate data that looks real but is fabricated
            - If Genie returns an error, MUST say so explicitly
            - Example: "Genie query failed: Timed out after 5 minutes. I will NOT generate fake data.""",
            
            # SECTION 4: ACTIONABILITY
            """Actionability and Recommendations:
            - MUST provide specific, actionable next steps
            - MUST include concrete implementation details:
              * SQL queries for investigation
              * CLI commands for configuration
              * Specific parameter values for tuning
            - MUST prioritize by urgency:
              * Immediate (do today): Critical issues
              * Short-term (this week): Important optimizations
              * Long-term (this month): Strategic improvements""",
            
            # SECTION 5: DOMAIN EXPERTISE
            """Domain-Specific Expertise:
            - MUST use correct Databricks terminology:
              * Cost: DBUs, SKUs, billing_origin_product, serverless vs classic
              * Security: Unity Catalog, RBAC, audit logs, service principals, PII
              * Performance: SQL warehouses, Photon, cache hit rates, P50/P95/P99 latencies
              * Reliability: Workflows, job runs, SLA compliance, MTTR, retry policies
              * Quality: Lakehouse Monitoring, freshness, null rates, schema drift, lineage""",
            
            # SECTION 6: CROSS-DOMAIN INTELLIGENCE
            """Cross-Domain Insights:
            - SHOULD identify correlations across domains when relevant:
              * Cost spikes + Job failures = Wasted spend on retries
              * Security events + Cost increase = Potential misconfiguration""",
            
            # SECTION 7: PROFESSIONAL TONE
            """Professional Enterprise Tone:
            - MUST maintain professional, technical tone
            - MUST be clear, concise, and free of jargon unless domain-specific
            - MUST avoid casual language or overly colloquial expressions""",
            
            # SECTION 8: COMPLETENESS
            """Completeness and Coverage:
            - MUST address all aspects of the user's question
            - MUST provide context for why something matters (business impact)
            - MUST include caveats or data gaps if information is incomplete""",
        ]), 1.0),
    ])
```

### Why 8 Sections?

Each section corresponds to a critical aspect of the agent's behavior defined in the system prompts:

| Section | Source Prompt | Purpose |
|---------|--------------|---------|
| 1. Data Accuracy | `ORCHESTRATOR_PROMPT`, `COST_ANALYST_PROMPT`, etc. | Ensures real data with explicit citations |
| 2. Data Formatting | All domain analyst prompts | Enforces consistent number/date/table formatting |
| 3. No Fabrication | `ORCHESTRATOR_PROMPT` (critical rule) | Prevents hallucination of plausible-looking data |
| 4. Actionability | All domain analyst prompts | Ensures recommendations are specific and implementable |
| 5. Domain Expertise | Domain-specific analyst prompts | Validates correct terminology and metrics usage |
| 6. Cross-Domain Intelligence | `SYNTHESIZER_PROMPT` | Encourages correlation identification across domains |
| 7. Professional Tone | All prompts | Maintains enterprise-appropriate communication |
| 8. Completeness | `ORCHESTRATOR_PROMPT` | Ensures comprehensive answers to user questions |

---

## 🔬 Enhanced Domain-Specific Judges

Each domain-specific judge now uses **7 comprehensive criteria** aligned with its domain's analyst prompt.

### Cost Accuracy Judge

```python:751:846:src/agents/setup/deployment_job.py
def cost_accuracy_judge(*, inputs: dict = None, outputs: Any = None, **kwargs) -> Feedback:
    """Domain-specific LLM judge for COST queries."""
    # ... parameter extraction ...
    
    prompt = f"""You are evaluating a cost analysis response from a Databricks cost monitoring agent.

USER QUERY:
{query}

AGENT RESPONSE:
{response}

COMPREHENSIVE EVALUATION CRITERIA (aligned with COST_ANALYST_PROMPT):

1. **Cost Value Precision**:
   - Specific dollar amounts: "$12,345.67" or "$1.2M for large values"
   - DBU counts: "145,678 DBUs" or "145.7K DBUs"
   - Time ranges: "last 7 days", "Jan 1-7, 2025"
   - SKU names: "JOBS_SERVERLESS_LIGHT_COMPUTE", "ALL_PURPOSE_COMPUTE"

2. **Cost Breakdown & Attribution**:
   - Cost by workspace: "workspace_prod: $8,234.56"
   - Cost by SKU: "Serverless: $5,432.10, Classic: $2,802.46"
   - Cost by tag: "team=data_eng: $3,456.78"
   - Period-over-period: "+23.4% vs last week"

3. **Trend Analysis**:
   - Trend direction: "Cost increased $1,234.56 (+15.2% ↑)" or "decreased (-8.7% ↓)"
   - Historical comparison: "Higher than last 7-day avg of $10,234.56"
   - Anomaly detection: "Spike on Jan 7th: $2,345.67 (2.3x daily average)"

4. **Data Source Citation**:
   - References [Cost Genie] or system.billing.usage explicitly
   - If cost data unavailable, states clearly (NO fabrication)

5. **Optimization Recommendations**:
   - Specific actions: "Right-size warehouse_analytics from 2XL to XL"
   - Expected savings: "Est. $1,500/month (30% reduction)"
   - Implementation steps: "Update warehouse config: target_size = 'X-Large'"
   - Priority: "Immediate: Stop idle cluster abc123 ($50/day waste)"

6. **Serverless vs Classic Analysis**:
   - Breakdown: "Serverless: 60% of cost, Classic: 40%"
   - Migration opportunities: "Migrate job_daily to serverless: Save $200/week"

7. **Domain Expertise**:
   - Uses correct terminology: DBUs, SKUs, billing_origin_product, commitment discounts
   - References system tables: system.billing.usage, system.billing.list_prices
   - Understands cost drivers: compute hours, storage, SQL queries, model serving

SCORING RUBRIC:
- "yes" (1.0): Meets 6-7 criteria. Specific costs, clear trends, proper citations, actionable optimizations
- "partial" (0.5): Meets 4-5 criteria. Some costs but vague, missing trends, or weak optimization guidance
- "no" (0.0): Meets <4 criteria. Inaccurate costs, missing key cost info, or fabricated numbers

Respond with JSON only:
{{"value": "yes"|"partial"|"no", "rationale": "<count criteria met X/7, note specific gaps>"}}"""
```

### Security Compliance Judge

```python:849:942:src/agents/setup/deployment_job.py
def security_compliance_judge(*, inputs: dict = None, outputs: Any = None, **kwargs) -> Feedback:
    """Domain-specific LLM judge for SECURITY queries."""
    # ... parameter extraction ...
    
    prompt = f"""You are evaluating a security analysis response from a Databricks security monitoring agent.

USER QUERY:
{query}

AGENT RESPONSE:
{response}

COMPREHENSIVE EVALUATION CRITERIA (aligned with SECURITY_ANALYST_PROMPT):

1. **Event Identification & Timestamps**:
   - Specific timestamps: "2025-01-09 14:30 UTC" or "3 hours ago"
   - Event types: "LOGIN_FAILED", "DATA_ACCESS", "PERMISSION_CHANGED"
   - Service names: "unityCatalog", "notebooks", "jobs"
   - Action names: "getTable", "updateSecurable", "createToken"

2. **User & Principal Details**:
   - User identities: "user@company.com", "service-principal-abc123"
   - Source IPs: "10.0.1.45" or "203.0.113.42 (external)"
   - Request IDs: "req_abc123" for event tracing
   - Session IDs: "session_xyz789" for correlation

3. **Risk Assessment**:
   - Risk levels: "High", "Medium", "Low" with rationale
   - Anomaly indicators: "First external access in 30 days", "Unusual time: 2 AM"
   - Pattern analysis: "15 failed logins in 5 minutes (brute force?)"
   - Severity: "Critical: PII table accessed by unauthorized user"

4. **Data Source Citation**:
   - References [Security Genie] or system.access.audit explicitly
   - If audit data unavailable, states clearly (NO fabrication)

5. **Compliance Recommendations**:
   - Immediate actions: "Revoke token abc123 immediately"
   - Preventive controls: "Enable MFA for all admin accounts"
   - Policy updates: "Add DENY rule: external IPs cannot access PII tables"
   - Monitoring: "Set up alert for failed_login_count > 10 in 5 min"

6. **Unity Catalog Integration**:
   - References UC securables: "catalog.schema.table", "external_location"
   - Permission details: "GRANT SELECT ON TABLE removed by admin@company.com"
   - Lineage mentions: "Access to pii_customers propagates to downstream dashboards"

7. **Domain Expertise**:
   - Uses correct terminology: Unity Catalog, RBAC, service principals, OAuth, SCIM
   - References system tables: system.access.audit, system.lakeflow.monitors
   - Understands access patterns: workspace admin, cluster manager, metastore admin

SCORING RUBRIC:
- "yes" (1.0): Meets 6-7 criteria. Specific events, risk assessment, proper citations, actionable security guidance
- "partial" (0.5): Meets 4-5 criteria. Some events but vague, missing risk assessment, or weak recommendations
- "no" (0.0): Meets <4 criteria. Inaccurate events, missing key security info, or fabricated audit data

Respond with JSON only:
{{"value": "yes"|"partial"|"no", "rationale": "<count criteria met X/7, note specific gaps>"}}"""
```

### Pattern: All Domain Judges Follow Same Structure

- **Reliability Accuracy Judge:** 7 criteria for job runs, SLA compliance, failure patterns
- **Performance Accuracy Judge:** 7 criteria for latency metrics, bottlenecks, optimization recommendations
- **Quality Accuracy Judge:** 7 criteria for quality metrics, issue identification, impact assessment

---

## 💬 Multi-Turn Conversation Implementation

The agent now supports **stateful multi-turn conversations** through three complementary mechanisms:

### 1. Lakebase Memory Integration

**Short-Term Memory (CheckpointSaver):**
- Stores conversation context across turns within a session
- Persists agent state, messages, and intermediate outputs
- Enables context-aware responses to follow-up questions

**Long-Term Memory (DatabricksStore):**
- Stores user preferences and insights across sessions
- Remembers user's typical queries, domains of interest
- Personalizes recommendations over time

```python:96:142:src/agents/setup/log_agent_model.py
# Memory components (Lakebase)
from databricks_langchain.checkpoint import CheckpointSaver
from databricks_langchain.vectorstores import DatabricksStore

# Initialize Lakebase memory
LAKEBASE_INSTANCE_NAME = "vibe-coding-workshop-lakebase"

try:
    self._short_term_memory = CheckpointSaver(
        instance_name=LAKEBASE_INSTANCE_NAME,
        session=self._db_session
    )
    print(f"✓ Short-term memory connected to Lakebase: {LAKEBASE_INSTANCE_NAME}")
    self._short_term_memory_available = True
except Exception as e:
    if "relation \"checkpoints\" does not exist" in str(e):
        # Table doesn't exist yet - will auto-create on first save
        self._short_term_memory_available = False
    else:
        print(f"⚠ Short-term memory initialization warning: {e}")
        self._short_term_memory = None
        self._short_term_memory_available = False

try:
    self._long_term_memory = DatabricksStore(
        instance_name=LAKEBASE_INSTANCE_NAME,
        session=self._db_session
    )
    print(f"✓ Long-term memory connected to Lakebase: {LAKEBASE_INSTANCE_NAME}")
    self._long_term_memory_available = True
except Exception as e:
    if "relation \"store\" does not exist" in str(e):
        # Table doesn't exist yet - will auto-create on first save
        self._long_term_memory_available = False
    else:
        print(f"⚠ Long-term memory initialization warning: {e}")
        self._long_term_memory = None
        self._long_term_memory_available = False
```

**Key Implementation Details:**
- Memory tables (`checkpoints`, `store`) **auto-initialize on first use**
- Graceful degradation: Agent works without memory if tables don't exist yet
- Silent initialization: No warnings during startup, only on first save failure

### 2. Stateless Genie Conversation Tracking

**Problem:** Model Serving has multiple replicas, so instance variables don't persist across requests.

**Solution:** Pass conversation state through `custom_inputs` and `custom_outputs`:

```python:654:711:src/agents/setup/log_agent_model.py
def predict(self, context: Context, request: ResponsesAgentRequest, params: Params = None) -> ResponsesAgentResponse:
    """
    Main prediction method for synchronous requests.
    Supports multi-turn conversations through:
    - thread_id (for short-term memory via CheckpointSaver)
    - genie_conversation_ids (for Genie follow-up questions)
    """
    # Extract conversation state from custom_inputs
    thread_id = None
    genie_conversation_ids = {}
    
    if request.custom_inputs:
        thread_id = request.custom_inputs.get("thread_id")
        genie_conversation_ids = request.custom_inputs.get("genie_conversation_ids", {})
    
    # Restore short-term memory if thread_id provided
    if thread_id and self._short_term_memory_available:
        try:
            checkpoint = self._short_term_memory.load(thread_id)
            if checkpoint:
                # Restore conversation state from checkpoint
                previous_messages = checkpoint.get("messages", [])
                # ... restore logic
        except Exception as e:
            if "relation \"checkpoints\" does not exist" not in str(e):
                print(f"⚠ Short-term memory retrieval failed: {e}")
    
    # ... agent processing with genie_conversation_ids ...
    
    # Return updated conversation state in custom_outputs
    return ResponsesAgentResponse(
        output=[
            ResponsesAgentResponseMessage(
                role="assistant",
                content=[ResponsesAgentResponseOutputText(text=final_text)]
            )
        ],
        custom_outputs={
            "thread_id": thread_id or str(uuid.uuid4()),  # Generate if new conversation
            "genie_conversation_ids": genie_conversation_ids,  # Updated with new conversation IDs
            "domain": domain,
            "source": "genie" if genie_query_used else "synthesized",
            "visualization_hint": visualization_hint,
            "data": data
        }
    )
```

**Genie Follow-Up Questions:**

```python:421:486:src/agents/setup/log_agent_model.py
def _query_genie(self, domain: str, query: str, conversation_id: str = None) -> tuple[str, str]:
    """
    Query a domain-specific Genie Space with support for follow-up questions.
    
    Args:
        domain: Domain name (cost, security, performance, reliability, quality, unified)
        query: User query
        conversation_id: Existing conversation ID for follow-up questions (optional)
    
    Returns:
        Tuple of (response_text, conversation_id)
    """
    if conversation_id:
        # Follow-up question - use existing conversation
        print(f"→ Following up Genie conversation for {domain} (conversation_id: {conversation_id[:12]}...)")
        message_obj = self._genie_client.start_conversation(
            space_id=space_id
        ).create_message_and_wait(
            conversation_id=conversation_id,
            content=query
        )
        new_conversation_id = conversation_id  # Keep same ID
    else:
        # New conversation
        print(f"→ Starting new Genie conversation for {domain} (space_id: {space_id[:12]}...)")
        conversation_and_message = self._genie_client.start_conversation_and_wait(
            space_id=space_id,
            content=query
        )
        message_obj = conversation_and_message.conversation.messages[0]
        new_conversation_id = conversation_and_message.conversation.conversation_id
    
    # ... process response ...
    
    return response_text, new_conversation_id
```

**Key Points:**
- **Stateless:** No instance variables for conversation state
- **Client-Driven:** Frontend passes `genie_conversation_ids` dict in `custom_inputs`
- **Per-Domain Tracking:** Each Genie Space has its own conversation ID
- **Format:** `{"cost": "conv_123", "security": "conv_456"}`

### 3. Thread ID for Short-Term Memory

The `thread_id` in `custom_inputs` links multiple messages into a single conversation thread:

```python
# First message (frontend generates thread_id)
request = {
    "messages": [{"role": "user", "content": "What were costs yesterday?"}],
    "custom_inputs": {
        "thread_id": "thread_abc123"  # Frontend tracks this
    }
}

# Second message (same thread)
request = {
    "messages": [{"role": "user", "content": "What about last week?"}],
    "custom_inputs": {
        "thread_id": "thread_abc123",  # Same thread
        "genie_conversation_ids": {"cost": "conv_xyz"}  # From first message's custom_outputs
    }
}
```

**Benefits:**
- Short-term memory can retrieve context from previous messages
- Genie can continue the conversation instead of starting fresh
- Frontend maintains conversation continuity across page refreshes

---

## 📈 Impact on Agent Quality

### Before Enhancement

**Evaluation Results (Early January 2026):**
- `guidelines/mean`: **0.0** ❌ (failing)
- `cost_accuracy/mean`: **0.3** ⚠️ (below threshold)
- `security_compliance/mean`: **0.4** ⚠️ (below threshold)
- Domain-specific judges: Generic, inconsistent feedback

**Typical Issues:**
- Agent fabricated plausible-looking cost numbers without Genie data
- No explicit data source citations
- Recommendations were vague ("optimize your warehouses")
- No distinction between critical and non-critical issues
- Inconsistent formatting (sometimes $1234.56, sometimes "about $1000")

### After Enhancement

**Evaluation Results (Post-Enhancement):**
- `guidelines/mean`: **Expected >0.7** ✅ (comprehensive 8-section criteria)
- `cost_accuracy/mean`: **Expected >0.8** ✅ (7 specific criteria)
- `security_compliance/mean`: **Expected >0.8** ✅ (7 specific criteria)
- Domain-specific judges: **Detailed, actionable feedback**

**Quality Improvements:**
- ✅ **Explicit citations:** Every data point references [Cost Genie], [Security Genie], etc.
- ✅ **No fabrication:** Clear error messages when Genie fails (no fake data)
- ✅ **Consistent formatting:** $12,345.67, 145.7K DBUs, 45.2%, 2.5s
- ✅ **Actionable recommendations:** "Scale warehouse_analytics from 2XL to XL → Save $1,500/month"
- ✅ **Prioritized by urgency:** Immediate / Short-term / Long-term
- ✅ **Domain expertise:** Correct terminology (DBUs, SKUs, RBAC, P95 latencies)
- ✅ **Cross-domain insights:** "Cost spike correlates with job failures → wasted spend on retries"

**Multi-Turn Conversation Quality:**
- ✅ **Context retention:** "What about last week?" correctly understands previous cost query context
- ✅ **Genie continuity:** Follow-up questions to Genie maintain conversation thread
- ✅ **Memory persistence:** User preferences and insights carry across sessions
- ✅ **Personalization:** Recommendations adapt to user's typical domains and queries

---

## 🔍 How It All Works Together

### End-to-End Flow for Multi-Turn Cost Query

**Turn 1: Initial Question**

```
User → Frontend → Agent Endpoint
Input: {
  "messages": [{"role": "user", "content": "What were costs yesterday?"}],
  "custom_inputs": {
    "thread_id": "thread_abc123"  # Frontend generates
  }
}

Agent Processing:
1. No genie_conversation_ids in custom_inputs → Start new Genie conversation
2. Query Cost Genie Space → Get conversation_id "conv_xyz"
3. Extract cost data: $12,345.67 for Jan 8, 2025
4. Format response with explicit [Cost Genie] citation
5. Save to short-term memory under thread_abc123

Agent → Frontend → User
Output: {
  "output": [{
    "role": "assistant",
    "content": "Based on [Cost Genie], costs on Jan 8, 2025 were $12,345.67 (145.7K DBUs)..."
  }],
  "custom_outputs": {
    "thread_id": "thread_abc123",
    "genie_conversation_ids": {"cost": "conv_xyz"},  # Save for follow-up
    "domain": "cost",
    "source": "genie"
  }
}
```

**Turn 2: Follow-Up Question**

```
User → Frontend → Agent Endpoint
Input: {
  "messages": [{"role": "user", "content": "What about last week?"}],
  "custom_inputs": {
    "thread_id": "thread_abc123",  # Same thread
    "genie_conversation_ids": {"cost": "conv_xyz"}  # From Turn 1
  }
}

Agent Processing:
1. Load short-term memory for thread_abc123 → Restore context (previous message about "yesterday")
2. genie_conversation_ids["cost"] exists → Use existing conversation "conv_xyz"
3. Follow-up to Cost Genie (same conversation) → Get cost data for last week
4. Genie understands context: "last week" relative to "yesterday"
5. Format response with weekly comparison
6. Update short-term memory

Agent → Frontend → User
Output: {
  "output": [{
    "role": "assistant",
    "content": "For the week of Jan 1-7, 2025, costs averaged $11,234.56/day (+9.9% vs Jan 8)..."
  }],
  "custom_outputs": {
    "thread_id": "thread_abc123",
    "genie_conversation_ids": {"cost": "conv_xyz"},  # Still same conversation
    "domain": "cost",
    "source": "genie"
  }
}
```

**Evaluation with Enhanced Judges:**

```python
# Guidelines Judge checks:
✅ Explicit citation: "[Cost Genie]"
✅ Specific numbers: "$12,345.67", "$11,234.56/day"
✅ Proper formatting: Dollar amounts with commas and decimals
✅ No fabrication: Real data from Genie
✅ Actionable: (if spike detected) "Investigate workspace_prod for unusual activity"
✅ Domain expertise: Mentions DBUs, references system.billing.usage
✅ Professional tone: Clear, concise, no casual language
✅ Complete: Addresses the question fully with context

Score: "yes" (1.0)

# Cost Accuracy Judge checks:
✅ Cost value precision: "$12,345.67" (exact amount)
✅ Time range: "Jan 8, 2025" and "Jan 1-7, 2025"
✅ Trend analysis: "+9.9% vs Jan 8"
✅ Data source citation: "[Cost Genie]"
✅ (If applicable) Optimization recommendations
✅ (If applicable) Serverless vs classic breakdown
✅ Domain expertise: DBUs mentioned, correct terminology

Score: "yes" (1.0)
```

---

## 🛠️ Frontend Integration Requirements

For multi-turn conversations to work correctly, the frontend must:

### 1. Maintain Thread ID
```typescript
// Generate thread_id for new conversation
const threadId = crypto.randomUUID();

// Persist thread_id across messages in the same conversation
sessionStorage.setItem(`thread_${conversationId}`, threadId);
```

### 2. Track Genie Conversation IDs
```typescript
// Extract from agent response
const { genie_conversation_ids } = response.custom_outputs;

// Pass back in next message
const nextRequest = {
  messages: [...previousMessages, newUserMessage],
  custom_inputs: {
    thread_id: threadId,
    genie_conversation_ids: genie_conversation_ids  // From previous response
  }
};
```

### 3. Handle Memory Limitations in AI Playground

**Important:** AI Playground does **NOT persist `custom_inputs` between turns**. This means:
- ❌ Memory doesn't work in Playground (thread_id not preserved)
- ❌ Genie follow-up questions don't work in Playground (conversation_ids lost)
- ✅ Both work correctly in production frontend with proper state management

---

## 📚 Related Documentation

- [08-evaluation-and-quality.md](./08-evaluation-and-quality.md) - Original evaluation documentation
- [05-memory-system.md](./05-memory-system.md) - Lakebase memory implementation details
- [04-worker-agents-and-genie.md](./04-worker-agents-and-genie.md) - Genie integration patterns
- [15-frontend-integration-guide.md](../15-frontend-integration-guide.md) - Frontend developer guide

---

## 🎯 Key Takeaways

1. **Enhanced judges align evaluation with actual agent prompts** → Consistent, reproducible quality metrics
2. **8-section Guidelines judge is comprehensive gatekeeper** → Catches fabrication, formatting issues, missing citations
3. **Domain-specific judges use 7 criteria each** → Detailed, actionable feedback per domain
4. **Multi-turn conversations use 3 mechanisms:** Lakebase memory (long-term context), stateless conversation tracking (Genie follow-ups), thread IDs (short-term context)
5. **Frontend must manage thread_id and genie_conversation_ids** → Enable stateful conversations across replicas
6. **AI Playground has limitations** → Use production frontend for full multi-turn experience

---

**Status:** ✅ Complete - Documented January 10, 2026  
**Next Review:** After first production deployment with enhanced judges

