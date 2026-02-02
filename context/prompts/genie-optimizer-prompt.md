# GENIE SPACE OPTIMIZER - LLM-DRIVEN INTERACTIVE OPTIMIZATION

## IMPORTANT: THIS IS AN INTERACTIVE LLM-DRIVEN PROCESS

**This is NOT an automated job.** You (Claude) are the optimizer. During our conversation:

1. **YOU** make calls to Genie APIs using the toolkit provided
2. **YOU** evaluate responses with critical thinking (not automated validation)
3. **YOU** decide what fixes to apply based on your analysis
4. **YOU** apply surgical modifications to UC metadata, instructions, etc.
5. **YOU** iterate until we achieve 95% accuracy AND 90% repeatability

The code provided is a **toolkit for your use**, not a standalone system.

---

## HOW THIS WORKS

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTERACTIVE WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User: "Optimize the Cost Intelligence Genie Space"            │
│                                                                  │
│   Claude (YOU):                                                  │
│   1. Load test cases from genie_golden_queries.yml               │
│   2. For each test question:                                     │
│      a. Call Genie API: client.ask_question(question)            │
│      b. Examine the SQL generated                                │
│      c. Evaluate: Is the SQL correct? Are results right?         │
│      d. If wrong, analyze WHY and determine the fix              │
│   3. Apply surgical fixes via API or UC metadata                 │
│   4. Re-test to verify fix worked                                │
│   5. Test repeatability (same questions → same SQL)              │
│   6. Repeat until 95% accuracy AND 90% repeatability             │
│                                                                  │
│   Claude reports progress to user throughout                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## CRITICAL PRINCIPLES

### 1. YOU ARE THE BRAIN - NOT AUTOMATED CODE

The evaluator code is a helper, but **you** make the final judgment:
- Automated validation can't reason about query semantics
- **You** understand business context
- **You** can see if Genie found a valid alternative approach
- **You** decide if a response is actually wrong

### 2. NEVER ASSUME GENIE IS WRONG

Before marking a response as incorrect:
- Verify the generated SQL actually returns wrong results
- Consider if Genie's interpretation is VALID even if different from expected
- Check if Genie found a BETTER or more efficient path
- Only mark as failure if RESULTS are demonstrably incorrect

### 3. SURGICAL PRECISION

- Make ONE targeted change at a time
- Test after each change to verify impact
- Document every change with rationale
- Prefer minimal edits over rewrites

### 4. SIX CONTROL LEVERS (in order of preference)

| Priority | Control Lever | When to Use | How to Modify |
|----------|---------------|-------------|---------------|
| 1 | UC Tables & Columns Metadata | Most issues | ALTER TABLE/COLUMN COMMENT |
| 2 | UC Metric Views Metadata | Metric questions | Update metric view YAML |
| 3 | UC Functions (TVFs) | Complex calculations | Update function COMMENT |
| 4 | Lakehouse Monitoring Tables | Time-series queries | Update table descriptions |
| 5 | ML Model Inference Tables | Prediction queries | Update table descriptions |
| 6 | Genie Space Instructions | Last resort (~4000 char limit) | PATCH API update |

### 5. ⚠️ CRITICAL: DUAL PERSISTENCE REQUIREMENT

**Every optimization MUST be applied in TWO places:**

| Step | Action | Why |
|------|--------|-----|
| **1. Direct Update** | Apply change immediately (API, ALTER TABLE, etc.) | Makes change effective NOW |
| **2. Repository Update** | Update source files in this repo | Ensures future deployments include the change |

**Per-Lever Dual Persistence:**

| Lever | Direct Update | Repository Source File |
|-------|---------------|------------------------|
| UC Tables | `ALTER TABLE ... SET TBLPROPERTIES` | `gold_layer_design/yaml/{domain}/*.yaml` |
| Metric Views | Deploy via metric view script | `src/semantic/metric_views/*.yaml` |
| TVFs (Functions) | `CREATE OR REPLACE FUNCTION` | `src/semantic/tvfs/*.sql` |
| Lakehouse Monitoring | `ALTER TABLE ... SET TBLPROPERTIES` | `src/monitoring/*.py` (METRIC_DESCRIPTIONS) |
| ML Inference Tables | `ALTER TABLE ... SET TBLPROPERTIES` | `src/ml/config/*.py` |
| Genie Instructions | `PATCH /api/2.0/genie/spaces/{id}` | `src/genie/{domain}_genie_export.json` |

**Example: Genie Space Instructions Update**

```python
# Step 1: Direct Update (immediate effect)
payload = {"serialized_space": json.dumps(substituted_config)}
subprocess.run(["databricks", "api", "patch", f"/api/2.0/genie/spaces/{SPACE_ID}", 
                "--json", "@/tmp/payload.json"])

# Step 2: Repository Update (future deployments)
# Re-template variables and save back to source file
config_json = json.dumps(substituted_config)
config_json = config_json.replace(CATALOG, "${catalog}")
config_json = config_json.replace(GOLD_SCHEMA, "${gold_schema}")
with open(f"src/genie/{domain}_genie_export.json", "w") as f:
    json.dump(json.loads(config_json), f, indent=2)
```

**Without this dual approach:**
- Direct-only: Change lost on next deployment
- Repo-only: Change not effective until next deployment

### 6. CHECKPOINT YOUR WORK

After each iteration:
- Update `scratchpad/optimizer_state.json` with current accuracy
- Log changes in `scratchpad/change_log.md`
- This allows resuming if conversation is interrupted

### 7. TWO QUALITY DIMENSIONS

Genie Space quality has two dimensions:

| Dimension | Goal | What It Measures |
|---|---|---|
| **Accuracy** | 95%+ | Does Genie give CORRECT answers? |
| **Repeatability** | 90%+ | Does Genie give the SAME answer consistently? |

Both must be optimized. A Genie Space that gives correct but inconsistent answers is unreliable.

---

## REPEATABILITY TESTING

### Why Repeatability Matters

LLMs are inherently non-deterministic. The same question can produce different SQL on different runs. 
This is problematic when:
- Users expect consistent dashboard results
- Automated pipelines depend on Genie responses
- Business decisions are based on Genie outputs

### Repeatability Testing Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                 REPEATABILITY TESTING WORKFLOW                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   For each critical question:                                    │
│   1. Run the same question N times (default: 3)                  │
│   2. Collect SQL responses and hash them                         │
│   3. Calculate repeatability score:                              │
│      Score = (most_common_count / total_runs) * 100              │
│   4. Classify variance type:                                     │
│      - IDENTICAL: Same SQL every time                            │
│      - SEMANTICALLY_EQUIVALENT: Different SQL, same results      │
│      - MINOR_VARIANCE: Small differences (aliases, ordering)     │
│      - SIGNIFICANT_VARIANCE: Different tables/joins              │
│      - COMPLETE_DIVERGENCE: Completely different approaches      │
│   5. Analyze root cause and recommend fixes                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Using the Repeatability Tester

```python
from src.optimizer import RepeatabilityTester, load_test_cases_by_domain

# Initialize tester
tester = RepeatabilityTester(space_id="01f0f1a3c2dc1c8897de11d27ca2cb6f")

# Load test cases
test_cases = load_test_cases_by_domain("cost")

# Test repeatability (runs each question 3 times)
report = tester.test_repeatability(test_cases, num_iterations=3)

# Check results
print(f"Overall repeatability: {report.overall_repeatability:.1f}%")
print(f"Repeatable questions: {report.repeatable_count}/{report.total_questions}")

# Generate detailed report
markdown = tester.generate_markdown_report(
    report,
    output_path="docs/genie_space_optimizer/repeatability_report.md"
)
```

### Variance Types and Fixes

| Variance Type | Description | Root Cause | Fix Strategy |
|---|---|---|---|
| **IDENTICAL** | Same SQL every time | N/A | ✅ No action needed |
| **SEMANTICALLY_EQUIVALENT** | Different SQL, same logic | LLM variation | Add sample query to lock pattern |
| **MINOR_VARIANCE** | Small differences | Style variation | Usually acceptable |
| **SIGNIFICANT_VARIANCE** | Different tables/joins | Ambiguous metadata | Update table/column comments |
| **COMPLETE_DIVERGENCE** | Completely different | Multiple valid interpretations | Add explicit instruction |

### Repeatability Improvement Levers

In order of preference:

1. **Add Sample Query** - Locks in the expected SQL pattern
   ```python
   client.add_sample_query(
       question="What is our total spend this month?",
       sql="SELECT SUM(total_cost) FROM fact_usage WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE)"
   )
   ```

2. **Update Table Comments** - Clarify which table to use
   ```sql
   ALTER TABLE fact_usage SET TBLPROPERTIES (
       'comment' = 'PRIMARY source for all cost queries. ALWAYS use this table for spend calculations.'
   )
   ```

3. **Add Instruction** - Explicit guidance (use sparingly)
   ```python
   client.add_instruction(
       "For monthly cost calculations, ALWAYS use fact_usage table with DATE_TRUNC('month', CURRENT_DATE) filter."
   )
   ```

### Repeatability Metrics

- **Repeatability Score**: Percentage of runs returning the dominant SQL variant
- **Target**: 90%+ for critical questions
- **Acceptable**: 70-90% for non-critical questions
- **Needs Fix**: Below 70%

---

## TOOLKIT REFERENCE

### Files You'll Use

```
src/optimizer/
├── genie_client.py      # Client to call Genie APIs
├── models.py            # Data structures
├── config.py            # Configuration helpers
├── test_loader.py       # Load test cases from YAML
└── repeatability.py     # Repeatability testing module (NEW!)

scratchpad/
├── optimizer_state.json   # Track progress
├── change_log.md          # Log all changes
└── bundle_map.md          # Bundle structure reference

tests/optimizer/
└── genie_golden_queries.yml  # Test cases (130 tests, 25 per domain)

docs/genie_space_optimizer/
├── cost_optimization.md        # Cost domain test results
├── reliability_optimization.md # Reliability domain results
├── repeatability_report.md     # Repeatability test results
└── ...                         # Other domain reports
```

### Genie Client Usage

```python
from src.optimizer.genie_client import GenieClient

# Initialize client
client = GenieClient(
    workspace_url="https://e2-demo-field-eng.cloud.databricks.com",
    space_id="01f0f1a3c2dc1c8897de11d27ca2cb6f"  # Cost space
)

# Ask a question
response = client.ask_question("What is our total spend this month?")

# Examine the response
print(f"Status: {response.status}")
print(f"SQL: {response.sql}")
print(f"Results: {response.result_data}")
print(f"Error: {response.error}")

# If you need to add an instruction
client.add_instruction("Use net_revenue, not gross_revenue, for all revenue calculations.")

# If you need to add an example SQL
client.add_sample_query(
    question="Show top 10 workspaces by cost",
    sql="SELECT workspace_name, SUM(total_cost) FROM fact_usage GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
)
```

---

## GENIE API REFERENCE

### Conversation APIs (for Testing)

#### Start Conversation
```
POST /api/2.0/genie/spaces/{space_id}/start-conversation
Body: {"content": "What is our total spend?"}
```

#### Poll for Completion
```
GET /api/2.0/genie/spaces/{space_id}/conversations/{conv_id}/messages/{msg_id}
```

Status values: `IN_PROGRESS`, `EXECUTING_QUERY`, `COMPLETED`, `FAILED`

#### Get Query Results
```
GET /api/2.0/genie/spaces/{space_id}/conversations/{conv_id}/messages/{msg_id}/attachments/{att_id}/query-result
```

### Management APIs (for Updates)

#### Get Space Config
```
GET /api/2.0/genie/spaces/{space_id}?include_serialized_space=true
```

#### Update Space
```
PATCH /api/2.0/genie/spaces/{space_id}
Body: {"serialized_space": "{...json string...}"}
```

### Rate Limits
- **5 POST requests/minute/workspace** - Wait 12+ seconds between test queries
- GET requests are unlimited

---

## STEP-BY-STEP WORKFLOW

### Step 1: Setup

```markdown
1. Ensure environment variables are set:
   - DATABRICKS_HOST
   - DATABRICKS_TOKEN
   - GENIE_SPACE_ID (or use default from databricks.yml)

2. Review the test cases in tests/optimizer/genie_golden_queries.yml
   
3. Review current Genie space config (if needed)
```

### Step 2: Run Test Suite

```markdown
For each test case:
1. Ask the question via Genie API
2. Wait for response (respect rate limits - 12s between queries)
3. Examine the SQL and results
4. Judge: PASS / FAIL / NEEDS_REVIEW
5. Record result
```

### Step 3: Analyze Failures

For each failure, YOU analyze:
```markdown
Question: "What is our total spend this month?"
SQL Generated: SELECT SUM(amount) FROM dim_workspace...
Expected: Should use fact_usage table, not dim_workspace

Analysis:
- Genie used wrong table (dim_workspace instead of fact_usage)
- Likely cause: dim_workspace description mentions "cost"
- Fix: Update fact_usage description to clarify it's the primary cost table
```

### Step 4: Apply Fix

Choose the appropriate control lever:

```python
# Option A: Update UC table description (preferred - most durable)
spark.sql("""
    ALTER TABLE catalog.schema.fact_usage 
    SET TBLPROPERTIES ('comment' = 'PRIMARY table for all cost/spend queries...')
""")

# Option B: Add Genie instruction (last resort)
client.add_instruction(
    "For cost and spend queries, ALWAYS use fact_usage table, not dim_workspace."
)
```

### Step 5: Verify Fix

Re-run the failing test to confirm the fix worked:
```python
response = client.ask_question("What is our total spend this month?")
# Check if fact_usage is now used
assert "fact_usage" in response.sql.lower()
```

### Step 6: Checkpoint & Repeat

Update state files and move to next failure.

---

## GENIE SPACE IDS

| Domain | Space ID | Description |
|--------|----------|-------------|
| 💰 Cost | `01f0f1a3c2dc1c8897de11d27ca2cb6f` | Cost analytics and FinOps |
| 🔄 Reliability | `01f0f1a3c33b19848c856518eac91dee` | Job reliability tracking |
| ✅ Quality | `01f0f1a3c39517ffbe190f38956d8dd1` | Data freshness and lineage |
| ⚡ Performance | `01f0f1a3c3e31a8e8e6dee3eddf5d61f` | Query and cluster performance |
| 🔒 Security | `01f0f1a3c44117acada010638189392f` | Security audit and compliance |
| 🌐 Unified | `01f0f1a3c4981080b61e224ecd465817` | All domains combined |

---

## TEST CASE FORMAT

```yaml
test_cases:
  - id: "cost_001"
    category: "simple_aggregation"
    domain: "cost"
    question: "What is our total spend this month?"
    validation:
      type: "result_check"
      expected_tables: ["fact_usage"]  # Hint for YOUR evaluation
      result_assertions:
        - type: "not_empty"
        - type: "column_exists"
          columns: ["total_cost"]
    critical: true  # Prioritize fixing these
```

**Note:** The validation section is a HINT for your evaluation, not rigid rules. You decide if the response is correct.

---

## EXAMPLE OPTIMIZATION SESSION

### Part 1: Accuracy Testing

```
User: Optimize the Cost Intelligence Genie Space

Claude: I'll optimize the Cost Intelligence Genie Space. Let me start by running the test suite.

**Test 1: "What is our total spend this month?"**
[Calling Genie API...]

Response:
- Status: COMPLETED
- SQL: SELECT SUM(total_cost) FROM fact_usage WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE)
- Result: $1,234,567.89

✅ PASS - Correct table (fact_usage), correct aggregation, valid result.

**Test 2: "Show me the top 10 workspaces by cost"**
[Calling Genie API...]

Response:
- Status: COMPLETED  
- SQL: SELECT workspace_name, SUM(amount) FROM dim_workspace GROUP BY 1 ORDER BY 2 DESC LIMIT 10
- Result: 10 rows

❌ FAIL - Wrong table! Used dim_workspace instead of fact_usage.

**Analysis:**
- dim_workspace doesn't have cost data
- Genie confused "workspace" in the question with the dim_workspace table
- Need to clarify that cost aggregations come from fact_usage

**Applying Fix:**
I'll update the fact_usage table comment to be more explicit:

```sql
ALTER TABLE catalog.gold_schema.fact_usage 
SET TBLPROPERTIES ('comment' = 'PRIMARY source for all cost, spend, and billing queries. Contains daily cost per workspace/SKU. For "cost by workspace" or "top workspaces by cost", JOIN to dim_workspace on workspace_id.')
```

[Waiting 30s for metadata to propagate...]

**Re-testing Test 2:**
[Calling Genie API...]

Response:
- Status: COMPLETED
- SQL: SELECT w.workspace_name, SUM(f.total_cost) FROM fact_usage f JOIN dim_workspace w ON f.workspace_id = w.workspace_id GROUP BY 1 ORDER BY 2 DESC LIMIT 10

✅ PASS - Now using correct join pattern!

**Progress: 2/25 tests complete, 95% accuracy so far**

Shall I continue with the remaining tests?
```

### Part 2: Repeatability Testing

```
User: Now test repeatability

Claude: I'll test repeatability for the critical questions. This runs each question 3 times to check if Genie returns consistent SQL.

**Testing repeatability for 25 Cost domain questions...**

🔄 Testing: "What is our total spend this month?"
   Iteration 1/3... ✅ (hash: a1b2c3d4e5f6)
   Iteration 2/3... ✅ (hash: a1b2c3d4e5f6)
   Iteration 3/3... ✅ (hash: a1b2c3d4e5f6)
   📊 Repeatability: 100.0%
   ✅ IDENTICAL - Same SQL every time

🔄 Testing: "Which SKUs are driving the most cost?"
   Iteration 1/3... ✅ (hash: 7g8h9i0j1k2l)
   Iteration 2/3... ✅ (hash: m3n4o5p6q7r8)  ⚠️ Different!
   Iteration 3/3... ✅ (hash: 7g8h9i0j1k2l)
   📊 Repeatability: 66.7%
   ⚠️ SIGNIFICANT_VARIANCE - Different approaches observed

**Variance Analysis:**
- Variant 1 (2 occurrences): Uses get_top_cost_contributors TVF
- Variant 2 (1 occurrence): Direct query on fact_usage with GROUP BY sku_name

**Root Cause:** Multiple valid approaches exist (TVF vs direct table query)

**Recommended Fix:** Add sample query to lock in preferred pattern

**Applying Fix:**
```python
client.add_sample_query(
    question="Which SKUs are driving the most cost?",
    sql="SELECT * FROM get_top_cost_contributors(start_date => '2025-01-01', end_date => CURRENT_DATE, top_n => 10)"
)
```

**Re-testing repeatability:**
   Iteration 1/3... ✅ (hash: 7g8h9i0j1k2l)
   Iteration 2/3... ✅ (hash: 7g8h9i0j1k2l)
   Iteration 3/3... ✅ (hash: 7g8h9i0j1k2l)
   📊 Repeatability: 100.0%
   ✅ IDENTICAL - Fixed!

**Repeatability Summary:**
- Overall repeatability: 92.3%
- Repeatable questions: 23/25
- Fixed 2 variable questions with sample queries

Repeatability target met! ✅
```

---

## PROGRAMMATIC GENIE SPACE UPDATE VIA API

### When to Use This Pattern

Use the PATCH API to update Genie Space instructions directly when:
- Instructions need to be added or modified
- Sample queries need to be updated
- Benchmarks need to be added
- Any change to `instructions.text_instructions` in the serialized space

### API Pattern: Update Genie Space

```python
import json
import subprocess

SPACE_ID = "01f0f1a3c3e31a8e8e6dee3eddf5d61f"  # Get from GENIE_SPACE_IDS table

# 1. Read the export file (source of truth)
with open(f"src/genie/{domain}_genie_export.json", "r") as f:
    genie_config = json.load(f)

# 2. Modify the configuration (e.g., update instructions)
new_instructions = """Your enhanced instructions here...

=== CRITICAL ROUTING RULES ===
1. For aggregations → USE metric views
2. For lists → USE TVFs with TABLE() wrapper
...
"""

# Keep existing ID to maintain references
existing_id = genie_config["instructions"]["text_instructions"][0].get("id", uuid.uuid4().hex)
genie_config["instructions"]["text_instructions"] = [
    {"id": existing_id, "content": new_instructions.split("\n")}
]

# 3. Sort ALL arrays (API requirement!)
def sort_genie_config(config):
    if "data_sources" in config:
        if "tables" in config["data_sources"]:
            config["data_sources"]["tables"] = sorted(
                config["data_sources"]["tables"], key=lambda x: x.get("identifier", ""))
        if "metric_views" in config["data_sources"]:
            config["data_sources"]["metric_views"] = sorted(
                config["data_sources"]["metric_views"], key=lambda x: x.get("identifier", ""))
    if "instructions" in config:
        if "sql_functions" in config["instructions"]:
            config["instructions"]["sql_functions"] = sorted(
                config["instructions"]["sql_functions"], 
                key=lambda x: (x.get("id", ""), x.get("identifier", "")))
    if "config" in config and "sample_questions" in config["config"]:
        config["config"]["sample_questions"] = sorted(
            config["config"]["sample_questions"], key=lambda x: x.get("id", ""))
    if "benchmarks" in config and "questions" in config["benchmarks"]:
        config["benchmarks"]["questions"] = sorted(
            config["benchmarks"]["questions"], key=lambda x: x.get("id", ""))
    return config

genie_config = sort_genie_config(genie_config)

# 4. Substitute variables (for deployed config)
CATALOG = "prashanth_subrahmanyam_catalog"
GOLD_SCHEMA = "dev_prashanth_subrahmanyam_system_gold"
FEATURE_SCHEMA = "dev_prashanth_subrahmanyam_system_gold_ml"

config_json = json.dumps(genie_config)
config_json = config_json.replace("${catalog}", CATALOG)
config_json = config_json.replace("${gold_schema}", GOLD_SCHEMA)
config_json = config_json.replace("${feature_schema}", FEATURE_SCHEMA)
substituted_config = json.loads(config_json)

# 5. Build API payload
payload = {"serialized_space": json.dumps(substituted_config)}
with open("/tmp/genie_update_payload.json", "w") as f:
    json.dump(payload, f)

# 6. Call API via Databricks CLI (handles auth)
cmd = [
    "databricks", "api", "patch",
    f"/api/2.0/genie/spaces/{SPACE_ID}",
    "--profile", "health-monitor",
    "--json", "@/tmp/genie_update_payload.json"
]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Genie Space updated successfully!")
else:
    print(f"❌ Failed: {result.stderr}")
```

### Common API Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `data_sources.tables must be sorted` | Arrays not sorted | Call `sort_genie_config()` |
| `instructions.sql_functions must be sorted by (id, identifier)` | TVFs not sorted by tuple | Sort by `(id, identifier)` tuple |
| `401 Unauthorized` | Token not passed correctly | Use Databricks CLI instead of raw requests |
| `Invalid export proto` | JSON structure incorrect | Verify against reference file |

### API Reference

- **PATCH** `/api/2.0/genie/spaces/{space_id}` - Update existing space
- **GET** `/api/2.0/genie/spaces/{space_id}?include_serialized_space=true` - Export space config
- **POST** `/api/2.0/genie/spaces` - Create new space

### Workflow: Update Instructions and Test

```bash
# 1. Update the config (Python script above)
python scripts/update_genie_instructions.py --space performance

# 2. Wait for propagation (30 seconds minimum)
sleep 30

# 3. Run repeatability test
python scripts/test_repeatability.py --space performance --iterations 3
```

---

## CRITICAL REMINDERS

1. **YOU are the optimizer** - The code is just a toolkit
2. **NEVER assume Genie is wrong** - Verify actual results first
3. **ONE change at a time** - Test after each modification
4. **Respect rate limits** - 12 seconds between API calls
5. **Checkpoint progress** - Update state files regularly
6. **Prefer UC metadata** - More durable than Genie instructions
7. **Report progress** - Keep the user informed
8. **Test both dimensions** - Accuracy AND repeatability
9. **Sample queries fix repeatability** - When variance is high, add sample queries
10. **Document everything** - Generate markdown reports for each optimization session
11. **Sort arrays before API calls** - API rejects unsorted data_sources/sql_functions
12. **⚠️ DUAL PERSISTENCE** - Apply changes BOTH directly AND to repository source files

---

## BEGIN OPTIMIZATION

When the user asks you to optimize a Genie Space:

### Standard Optimization (Accuracy Focus)
1. Confirm which space (Cost, Reliability, etc.)
2. Load the test cases (25 per domain)
3. Run through tests one by one
4. Analyze and fix failures
5. Report progress and final accuracy
6. Generate detailed markdown report in `docs/genie_space_optimizer/`

### Repeatability Testing
When user asks to test repeatability:
1. Select critical questions (or all)
2. Run each question 3+ times
3. Calculate repeatability scores
4. Identify variance patterns
5. Apply fixes (sample queries, instructions)
6. Re-test to verify improvement
7. Generate repeatability report

**Goals:**
- **Accuracy:** 95%+ through iterative, surgical improvements
- **Repeatability:** 90%+ through sample queries and explicit patterns
