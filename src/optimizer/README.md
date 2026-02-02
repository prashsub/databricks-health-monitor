# Genie Space Optimizer Toolkit

An **LLM-driven interactive optimization toolkit** for improving Genie Space accuracy to 95%+.

## Overview

This toolkit provides Claude (or other LLMs) with the tools needed to:

1. **Test** Genie Spaces with golden queries
2. **Analyze** failures and determine root causes
3. **Apply** surgical fixes to UC metadata, Genie instructions, etc.
4. **Track** progress and checkpoint state

> **⚠️ IMPORTANT:** This is NOT automated code. **You (the LLM) are the optimizer.** The code here is a toolkit for your use.

## Quick Start

### 1. Set Environment Variables

```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"
```

### 2. Ask Claude to Optimize

```
User: Optimize the Cost Intelligence Genie Space

Claude will:
1. Load test cases from tests/optimizer/genie_golden_queries.yml
2. For each test:
   a. Call Genie API
   b. Examine SQL generated
   c. Evaluate correctness
   d. If wrong, analyze WHY and fix
3. Apply fixes via UC metadata or Genie instructions
4. Verify fixes work
5. Report final accuracy
```

## Files

```
src/optimizer/
├── __init__.py           # Main exports
├── genie_client.py       # Client to call Genie APIs
├── models.py             # Data structures (TestCase, GenieResponse, etc.)
├── config.py             # Configuration and Genie Space IDs
├── test_loader.py        # Load golden queries from YAML
└── README.md             # This file

scratchpad/
├── optimizer_state.json  # Track progress (survives conversation breaks)
├── change_log.md         # Log all changes made
└── bundle_map.md         # Quick reference for project structure

tests/optimizer/
├── genie_golden_queries.yml  # 35 test cases across all domains
└── test_optimizer.py         # Unit tests for the toolkit
```

## Genie Space IDs

| Domain | Space ID | Description |
|--------|----------|-------------|
| 💰 Cost | `01f0f1a3c2dc1c8897de11d27ca2cb6f` | Cost analytics and FinOps |
| 🔄 Reliability | `01f0f1a3c33b19848c856518eac91dee` | Job reliability tracking |
| ✅ Quality | `01f0f1a3c39517ffbe190f38956d8dd1` | Data freshness and lineage |
| ⚡ Performance | `01f0f1a3c3e31a8e8e6dee3eddf5d61f` | Query and cluster performance |
| 🔒 Security | `01f0f1a3c44117acada010638189392f` | Security audit and compliance |
| 🌐 Unified | `01f0f1a3c4981080b61e224ecd465817` | All domains combined |

## Control Levers (Priority Order)

When fixing issues, use these in order of preference:

| Priority | Control Lever | When to Use | How to Modify |
|----------|---------------|-------------|---------------|
| 1 | UC Tables Metadata | Most issues | `ALTER TABLE ... SET TBLPROPERTIES` |
| 2 | UC Column Metadata | Column confusion | `ALTER TABLE ... ALTER COLUMN ... COMMENT` |
| 3 | UC Metric Views | Metric questions | Update metric view YAML |
| 4 | UC Functions (TVFs) | Calculation queries | Update function COMMENT |
| 5 | Lakehouse Monitoring | Time-series queries | Update table descriptions |
| 6 | ML Inference Tables | Prediction queries | Update table descriptions |
| 7 | Genie Instructions | Last resort | `client.add_instruction()` |

## API Reference

### GenieClient

```python
from src.optimizer import GenieClient

# Initialize
client = GenieClient(
    workspace_url="https://your-workspace.cloud.databricks.com",
    space_id="01f0f1a3c2dc1c8897de11d27ca2cb6f"  # Cost space
)

# Ask a question
response = client.ask_question("What is our total spend this month?")

# Examine response
print(f"Status: {response.status}")
print(f"SQL: {response.sql}")
print(f"Results: {response.result_data}")
print(f"Error: {response.error}")

# Add instruction (use sparingly - ~4000 char limit)
client.add_instruction("Use net_revenue, not gross_revenue, for revenue calculations.")

# Add sample query
client.add_sample_query(
    question="Show top 10 workspaces by cost",
    sql="SELECT workspace_name, SUM(total_cost) FROM fact_usage GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
)
```

### Test Loader

```python
from src.optimizer import load_test_cases, print_test_summary

# Load all test cases
tests = load_test_cases()

# Load by domain
cost_tests = load_test_cases(domain="cost")

# Load critical only
critical_tests = load_test_cases(critical_only=True)

# Print summary
print_test_summary()
```

### Create Client for Domain

```python
from src.optimizer import create_client_for_domain

# Automatically looks up space ID for domain
client = create_client_for_domain("cost")
response = client.ask_question("What is our total spend?")
```

## Test Case Format

```yaml
- id: cost_001
  category: simple_aggregation
  domain: cost
  question: "What is our total spend this month?"
  validation:
    type: result_check
    expected_tables: ["fact_usage"]
    result_assertions:
      - type: not_empty
      - type: column_exists
        columns: ["total_cost"]
  critical: true
  notes: |
    Should use fact_usage table with date filter for current month.
```

## Rate Limits

- **5 POST requests/minute/workspace** - Wait 12+ seconds between test queries
- GET requests are unlimited

The client automatically enforces rate limits.

## Workflow

### Step 1: Run Tests

```python
# Load test cases for a domain
from src.optimizer import load_test_cases, create_client_for_domain

tests = load_test_cases(domain="cost")
client = create_client_for_domain("cost")

# Run each test (Claude does this interactively)
for test in tests:
    response = client.ask_question(test.question)
    # Claude evaluates the response
    # Claude decides PASS/FAIL/NEEDS_REVIEW
```

### Step 2: Analyze Failures

For each failure, Claude analyzes:
- What SQL was generated?
- What tables/columns were used?
- Why did Genie choose this path?
- What's the root cause?

### Step 3: Apply Fix

Claude chooses the appropriate control lever:

```sql
-- Option A: Update UC table description (preferred)
ALTER TABLE catalog.schema.fact_usage 
SET TBLPROPERTIES ('comment' = 'PRIMARY table for all cost/spend queries...');

-- Option B: Add Genie instruction (last resort)
-- client.add_instruction("For cost queries, ALWAYS use fact_usage, not dim_workspace.")
```

### Step 4: Verify

Re-run the failing test to confirm the fix worked.

### Step 5: Checkpoint

Update `scratchpad/optimizer_state.json` and `scratchpad/change_log.md`.

## Critical Principles

1. **YOU are the brain** - The code is just a toolkit
2. **NEVER assume Genie is wrong** - Verify actual results first
3. **ONE change at a time** - Test after each modification
4. **Respect rate limits** - 12 seconds between API calls
5. **Checkpoint progress** - Update state files regularly
6. **Prefer UC metadata** - More durable than Genie instructions
7. **Report progress** - Keep the user informed

## Example Session

```
User: Optimize the Cost Intelligence Genie Space

Claude: I'll optimize the Cost Intelligence Genie Space. Let me start.

**Test 1: "What is our total spend this month?"**
[Calling Genie API...]

Response:
- Status: COMPLETED
- SQL: SELECT SUM(total_cost) FROM fact_usage WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE)
- Result: $1,234,567.89

✅ PASS - Correct table, correct aggregation, valid result.

**Test 2: "Show me the top 10 workspaces by cost"**
[Calling Genie API...]

Response:
- Status: COMPLETED  
- SQL: SELECT workspace_name, SUM(amount) FROM dim_workspace GROUP BY 1 ORDER BY 2 DESC LIMIT 10

❌ FAIL - Wrong table! Used dim_workspace instead of fact_usage.

**Applying Fix:**
I'll update the fact_usage table comment:

```sql
ALTER TABLE catalog.gold_schema.fact_usage 
SET TBLPROPERTIES ('comment' = 'PRIMARY source for all cost, spend, and billing queries. For "cost by workspace", JOIN to dim_workspace on workspace_id.')
```

[Waiting for metadata to propagate...]

**Re-testing:**
✅ PASS - Now using correct join pattern!

**Progress: 2/13 cost tests, 100% accuracy so far**
```

## References

- [Genie Space Patterns](../../.cursor/rules/semantic-layer/16-genie-space-patterns.mdc)
- [Genie Spaces Inventory](../genie/GENIE_SPACES_INVENTORY.md)
- [Original Prompt](../../context/prompts/genie-optimizer-prompt.md)
