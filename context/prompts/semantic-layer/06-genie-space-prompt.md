# Genie Space Setup Prompt

## 🚀 Quick Start (1 hour)

**Goal:** Enable natural language queries for business users (no SQL required)

**Prerequisites:** ⚠️ Complete FIRST:
- ✅ Metric Views created (semantic layer)
- ✅ Table-Valued Functions created (common queries)
- ✅ Gold layer tables (with rich descriptions)

---

# ⚠️⚠️⚠️ MANDATORY DELIVERABLES - DO NOT SKIP ⚠️⚠️⚠️

## 🔴🔴🔴 REQUIRED OUTPUT: GENIE SPACE SETUP DOCUMENT 🔴🔴🔴

**You MUST produce a complete document containing ALL 7 sections below.**
**Each section is NON-NEGOTIABLE. Missing any section = INCOMPLETE deliverable.**

---

## ████████████████████████████████████████████████████████████████
## █                                                              █
## █  SECTION A: SPACE NAME                                       █
## █  ─────────────────────────────────────────────────────────── █
## █  REQUIRED: Provide the exact Genie Space name                █
## █                                                              █
## ████████████████████████████████████████████████████████████████

**Format:**
```
Space Name: {Project Name} {Domain} Analytics Space
```

**Example:**
```
Space Name: Wanderbricks Revenue Analytics Space
```

---

## ████████████████████████████████████████████████████████████████
## █                                                              █
## █  SECTION B: SPACE DESCRIPTION                                █
## █  ─────────────────────────────────────────────────────────── █
## █  REQUIRED: 2-3 sentence description of the space purpose     █
## █                                                              █
## ████████████████████████████████████████████████████████████████

**Format:**
```
Description: Natural language interface for {domain} analytics. 
Enables {user type} to query {data types} without SQL. 
Powered by {key data assets}.
```

**Example:**
```
Description: Natural language interface for vacation rental revenue and booking analytics. 
Enables business analysts and executives to query revenue, occupancy, and host performance metrics without SQL. 
Powered by Metric Views, Table-Valued Functions, and Gold layer dimensional model.
```

---

## ████████████████████████████████████████████████████████████████
## █                                                              █
## █  SECTION C: SAMPLE QUESTIONS                                 █
## █  ─────────────────────────────────────────────────────────── █
## █  REQUIRED: 10-15 example questions users can ask             █
## █  These appear in Genie UI to guide users                     █
## █                                                              █
## ████████████████████████████████████████████████████████████████

**Format:**
```markdown
## Sample Questions

### Revenue Questions
1. "What is the total revenue for the last 30 days?"
2. "Show me the top 10 {entities} by revenue"
3. "What was the revenue trend by month?"

### Performance Questions
4. "Which {entity} had the best performance last quarter?"
5. "Compare {entity A} vs {entity B}"

### Trend Questions
6. "Show me daily {metric} for the last 7 days"
7. "What is the month-over-month growth?"

### Drill-Down Questions
8. "Show {metric} by {dimension}"
9. "Which {entities} in {filter} had {metric} over {threshold}?"
10. "What is the average {metric} by {dimension}?"
```

---

## ████████████████████████████████████████████████████████████████
## █                                                              █
## █  SECTION D: DATA ASSETS (TABLES & METRIC VIEWS)              █
## █  ─────────────────────────────────────────────────────────── █
## █  REQUIRED: Complete list of all trusted assets               █
## █  Include: Metric Views, Dimension Tables, Fact Tables        █
## █                                                              █
## ████████████████████████████████████████████████████████████████

**Format:**
```markdown
## Data Assets

### Metric Views (PRIMARY - Use First)
| Metric View Name | Purpose | Key Measures |
|------------------|---------|--------------|
| {metric_view_1} | {purpose} | {measures} |
| {metric_view_2} | {purpose} | {measures} |

### Dimension Tables
| Table Name | Purpose | Key Columns |
|------------|---------|-------------|
| dim_{entity1} | {purpose} | {columns} |
| dim_{entity2} | {purpose} | {columns} |
| dim_date | Calendar lookups | year, quarter, month, day |

### Fact Tables (if needed beyond Metric Views)
| Table Name | Purpose | Grain |
|------------|---------|-------|
| fact_{entity} | {purpose} | {grain} |
```

---

## ████████████████████████████████████████████████████████████████
## █                                                              █
## █  SECTION E: GENERAL INSTRUCTIONS (20 LINES MAX)              █
## █  ─────────────────────────────────────────────────────────── █
## █  REQUIRED: Concise LLM behavior instructions                 █
## █  MUST BE EXACTLY 20 LINES OR LESS                            █
## █                                                              █
## ████████████████████████████████████████████████████████████████

**Format (COPY AND CUSTOMIZE):**
```markdown
## General Instructions

You are an expert {domain} analyst. Follow these rules:

1. **Primary Data Source:** Always use Metric Views first (e.g., {metric_view_name})
2. **Use TVFs:** For common queries, prefer Table-Valued Functions over raw SQL
3. **Date Defaults:** If no date specified, default to last 30 days
4. **Aggregations:** Use SUM for totals, AVG for averages, COUNT for volumes
5. **Sorting:** Sort results by primary metric DESC unless user specifies otherwise
6. **Limits:** Return top 10-20 rows for ranking queries unless user specifies
7. **Currency:** Format as USD with 2 decimal places
8. **Percentages:** Show as % with 1 decimal place
9. **Synonyms:** Handle these equivalents:
   - Revenue = sales, dollars, earnings
   - {Entity} = {synonyms}
10. **Context:** Always explain what the numbers mean in business terms
11. **Comparisons:** When comparing, show both absolute values and % difference
12. **Time Periods:** Support: today, yesterday, last week, last month, last quarter, YTD
13. **Null Handling:** Exclude nulls from calculations
14. **Performance:** Never scan raw Bronze/Silver tables
15. **Accuracy:** If unsure about a metric definition, state the assumption made
```

**⚠️ CONSTRAINT: MAXIMUM 20 LINES. Do not exceed.**

---

## ████████████████████████████████████████████████████████████████
## █                                                              █
## █  SECTION F: TABLE-VALUED FUNCTIONS (TVFs)                    █
## █  ─────────────────────────────────────────────────────────── █
## █  REQUIRED: List ALL TVFs with signatures and descriptions    █
## █                                                              █
## ████████████████████████████████████████████████████████████████

**Format:**
```markdown
## Table-Valued Functions

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| get_{query1} | `get_{query1}(param1 TYPE, param2 TYPE)` | {purpose} | {when to use} |
| get_{query2} | `get_{query2}(param1 TYPE, param2 TYPE)` | {purpose} | {when to use} |

### TVF Details

#### get_{query1}
- **Signature:** `get_{query1}(param1 STRING, start_date DATE, end_date DATE)`
- **Returns:** {description of output columns}
- **Use When:** User asks for {specific question pattern}
- **Example:** `SELECT * FROM get_{query1}('value', CURRENT_DATE - 30, CURRENT_DATE)`

#### get_{query2}
- **Signature:** `get_{query2}(limit INT, start_date DATE, end_date DATE)`
- **Returns:** {description of output columns}
- **Use When:** User asks for {specific question pattern}
- **Example:** `SELECT * FROM get_{query2}(10, CURRENT_DATE - 30, CURRENT_DATE)`
```

---

## ████████████████████████████████████████████████████████████████
## █                                                              █
## █  SECTION G: BENCHMARK QUESTIONS WITH SQL ANSWERS             █
## █  ─────────────────────────────────────────────────────────── █
## █  REQUIRED: 10-15 questions with EXACT SQL that should run    █
## █  These are for TESTING the Genie Space works correctly       █
## █                                                              █
## ████████████████████████████████████████████████████████████████

**Format:**
```markdown
## Benchmark Questions & Expected SQL

### Question 1: "{Natural language question}"
**Expected SQL:**
```sql
SELECT 
  {columns}
FROM {table_or_metric_view}
WHERE {conditions}
GROUP BY {grouping}
ORDER BY {ordering}
LIMIT {n};
```
**Expected Result:** {Description of what should return}

---

### Question 2: "{Natural language question using TVF}"
**Expected SQL:**
```sql
SELECT * FROM get_{function_name}({params});
```
**Expected Result:** {Description of what should return}

---

### Question 3: "{Aggregation question}"
**Expected SQL:**
```sql
SELECT 
  {dimension},
  MEASURE(`{Metric Name}`) as {alias}
FROM {metric_view}
GROUP BY {dimension}
ORDER BY {alias} DESC
LIMIT 10;
```
**Expected Result:** {Description of what should return}
```

**⚠️ REQUIREMENT: Provide 10-15 benchmark questions with EXACT working SQL.**

---

## ████████████████████████████████████████████████████████████████
## █                                                              █
## █  SECTION H: JSON EXPORT FOR API DEPLOYMENT                   █
## █  ─────────────────────────────────────────────────────────── █
## █  REQUIRED: GenieSpaceExport JSON for programmatic deployment █
## █  Enables automated deployment via REST API                   █
## █  ⚠️ INCLUDES BENCHMARK SQL - THIS IS WHAT GETS VALIDATED     █
## █                                                              █
## ████████████████████████████████████████████████████████████████

**Purpose:** Enable automated deployment using Databricks REST API instead of manual UI setup.

**⚠️ CRITICAL:** The `benchmarks` section in the JSON is what gets validated before deployment. The benchmark SQL in Section G (markdown) is for human documentation only.

**Format:**
```json
{
  "version": 1,
  "config": {
    "sample_questions": [
      {
        "id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "question": ["Sample question 1 from Section C"]
      },
      {
        "id": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "question": ["Sample question 2 from Section C"]
      }
    ]
  },
  "data_sources": {
    "tables": [
      {
        "identifier": "${catalog}.${gold_schema}.dim_table_name",
        "description": ["Table description"],
        "column_configs": [
          {
            "column_name": "column1",
            "description": ["Column description"],
            "synonyms": ["synonym1", "synonym2"],
            "get_example_values": true
          }
        ]
      }
    ],
    "metric_views": [
      {
        "identifier": "${catalog}.${gold_schema}.metric_view_name",
        "description": ["Metric view description"],
        "column_configs": [
          {
            "column_name": "dimension1"
          },
          {
            "column_name": "measure1"
          }
        ]
      }
    ]
  },
  "instructions": {
    "text_instructions": [
      {
        "id": "cccccccccccccccccccccccccccccccc",
        "content": ["General instructions from Section E (line by line)"]
      }
    ],
    "sql_functions": [
      {
        "id": "dddddddddddddddddddddddddddddddd",
        "identifier": "${catalog}.${gold_schema}.get_function_name"
      }
    ]
  },
  "benchmarks": {
    "questions": [
      {
        "id": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "question": ["Benchmark question 1 from Section G"],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT \n",
              "  column1,\n",
              "  MEASURE(measure1) as metric\n",
              "FROM ${catalog}.${gold_schema}.metric_view\n",
              "WHERE date_column >= CURRENT_DATE() - 30\n",
              "ORDER BY metric DESC\n",
              "LIMIT 10;"
            ]
          }
        ]
      },
      {
        "id": "ffffffffffffffffffffffffffffffff",
        "question": ["Benchmark question 2 from Section G"],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT * FROM ${catalog}.${gold_schema}.get_function_name(\n",
              "  'param_value',\n",
              "  CURRENT_DATE() - 30,\n",
              "  CURRENT_DATE()\n",
              ");"
            ]
          }
        ]
      }
    ]
  }
}
```

**Requirements:**
1. **Save as:** `{space_name}_genie_export.json` (e.g., `cost_intelligence_genie_export.json`)
2. **IDs:** Use 32-char hex strings (UUID without dashes)
3. **String arrays:** All `question`, `description`, `content` fields are arrays (split at newlines)
4. **Variables:** Use `${catalog}` and `${gold_schema}` for template substitution
5. **Sorting:** ALL arrays must be sorted:
   - `tables` by `identifier` (alphabetical)
   - `metric_views` by `identifier` (alphabetical)
   - `column_configs` by `column_name` (alphabetical)
   - `sql_functions` by `identifier` (alphabetical)
6. **Benchmarks:** Copy ALL benchmark questions from Section G into the `benchmarks.questions` array
   - Each question must have exactly ONE answer with `format: "SQL"`
   - SQL content is split into array of lines (for better diffs)
   - The SQL here is what gets validated before deployment

**⚠️ CRITICAL VALIDATION FLOW:**
1. Pre-deployment validation reads `benchmarks.questions[].answer[].content` from JSON
2. Joins the content array into a single SQL string
3. Substitutes `${catalog}` and `${gold_schema}` variables
4. Runs `EXPLAIN` on each SQL query to validate syntax, columns, tables
5. Deployment only proceeds if ALL benchmark SQL queries are valid

**⚠️ REQUIREMENT: Generate valid GenieSpaceExport JSON with ALL benchmark questions from Section G.**

**Reference:** See `.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc` for complete schema.

---

# ✅ DELIVERABLE CHECKLIST

Before submitting, verify ALL sections are complete:

| Section | Requirement | Complete? |
|---------|-------------|-----------|
| **A. Space Name** | Exact name provided | ☐ |
| **B. Space Description** | 2-3 sentences | ☐ |
| **C. Sample Questions** | 10-15 questions | ☐ |
| **D. Data Assets** | All tables & metric views listed | ☐ |
| **E. General Instructions** | ≤20 lines, behavior rules | ☐ |
| **F. TVFs** | All functions with signatures | ☐ |
| **G. Benchmark Questions** | 10-15 with SQL answers | ☐ |
| **H. JSON Export** | GenieSpaceExport format | ☐ |

**🔴 ALL 8 SECTIONS MUST BE COMPLETE. NO EXCEPTIONS. 🔴**

---

# 📖 Detailed Implementation Guide

The sections below provide additional context and examples for each deliverable.

---

## Understanding Genie Spaces

**⚠️ CRITICAL PRINCIPLE:**

Genie Spaces enable **business users to query data using natural language**:

- ✅ **Trusted Assets:** Curated tables, views, and functions
- ✅ **Agent Instructions:** Comprehensive context for query understanding
- ✅ **Benchmark Questions:** Test cases for validation
- ✅ **Metric Views:** Semantic layer with synonyms
- ✅ **Table-Valued Functions:** Pre-built common queries
- ❌ **No Raw Tables:** Use views and semantic layers

**Why This Matters:**
- Democratizes data access (no SQL knowledge required)
- Reduces repetitive analyst queries
- Ensures consistent metric definitions
- Captures business logic in natural language

---

## API Deployment Checklist (NEW - Recommended)

**Using Section H JSON Export for automated deployment:**

### Pre-Creation Verification
- [ ] All metric views deployed and tested
- [ ] All TVFs deployed and tested
- [ ] All Gold tables exist with descriptions
- [ ] SQL benchmark questions validated (run `EXPLAIN` on each)

### JSON Structure Requirements
- [ ] All `tables` sorted alphabetically by `identifier`
- [ ] All `metric_views` sorted alphabetically by `identifier`
- [ ] All `column_configs` sorted alphabetically by `column_name`
- [ ] All `sql_functions` sorted alphabetically by `identifier`
- [ ] IDs are 32-char hex strings (UUID without dashes)
- [ ] Variables use `${catalog}` and `${gold_schema}` format
- [ ] String fields are arrays (split at newlines)

### Pre-Deployment Validation Steps
1. **Validate Benchmark SQL:** Run validation task to check all SQL queries
   ```bash
   databricks bundle run -t dev genie_spaces_deployment_job --profile {profile}
   ```
2. **Check for errors:** Validation task catches syntax, column, and table errors
3. **Fix issues:** Update markdown Section G and regenerate JSON Section H

### Deployment Workflow
```bash
# 1. Place JSON file in src/genie/ folder
# File name: {space_name}_genie_export.json

# 2. Deploy bundle (syncs JSON to workspace)
databricks bundle deploy -t dev --profile {profile}

# 3. Run deployment job (validates + deploys)
databricks bundle run -t dev genie_spaces_deployment_job --profile {profile}
```

### Deployment Output
```
Task validate_genie_spaces: SUCCESS
  ✓ Validated 12 benchmark queries
  ✓ All SQL syntax correct
  ✓ All columns exist
  ✓ All tables/functions exist

Task deploy_genie_spaces: SUCCESS
  ✓ Created Genie Space: {space_name}
  ✓ Space ID: abc123...
```

### Benefits of API Deployment
- ✅ **Version Control:** JSON is tracked in Git
- ✅ **Validation:** Pre-deployment SQL validation catches errors
- ✅ **Repeatability:** Deploy to dev/staging/prod environments
- ✅ **Updates:** Use same JSON to update existing spaces
- ✅ **CI/CD Ready:** Integrate into deployment pipelines

**Reference:** `.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc`

---

## Step 1: Genie Space Setup (UI-Based - Legacy)

### Create Genie Space

**Navigate to:** Databricks Workspace → Genie Spaces → Create New

1. **Space Name:** Use format from Section A
2. **Description:** Use text from Section B
3. **SQL Warehouse:** Select serverless SQL warehouse
4. **Permissions:** Grant access to business user groups

---

## Step 2: Add Trusted Assets

### Asset Selection Strategy

**Priority Order:**
1. **Metric Views** (highest priority - semantic layer)
2. **Table-Valued Functions** (common queries)
3. **Gold dimension tables** (for dimension lookups)
4. **Gold fact tables** (if needed, but prefer Metric Views)

### Assets to Add

```
Trusted Assets:
├── Metric Views (Primary)
│   ├── {metric_view_1}
│   └── {metric_view_2}
│
├── Table-Valued Functions (Common Queries)
│   ├── get_{query1}(params)
│   ├── get_{query2}(params)
│   └── ... (all TVFs from Section F)
│
└── Gold Tables (Context)
    ├── dim_{entity1}
    ├── dim_{entity2}
    └── dim_date
```

**In Genie UI:**
1. Click **"Add Trusted Assets"**
2. Search for each asset
3. Select and add
4. Repeat for all assets

---

## Step 3: Configure Agent Instructions

Copy the General Instructions from Section E into the Genie Space configuration.

**Additional Detailed Instructions (Optional):**

For complex domains, you may add more detailed instructions beyond the 20-line summary:

```markdown
## Query Guidelines

### Revenue Queries
- **Use:** `MEASURE(\`Total Revenue\`)` from {metric_view}
- **Aggregation:** Already aggregated at daily grain, use SUM/AVG as needed
- **Filters:** {available filter dimensions}

### Time-Based Analysis
- **Dimensions:** year, quarter, month_name, is_weekend from dim_date
- **Comparisons:** Use WHERE clause for date ranges
- **Trending:** Use ORDER BY date for time series

## Response Format

### For Tabular Results
- Return clean, formatted tables
- Include relevant columns only
- Sort by most relevant metric (usually revenue DESC)
- Limit to reasonable row count (10-20 for top N queries)

### For Summary Statistics
- Provide context (time period, filters applied)
- Show key metrics
- Include comparisons when relevant (YoY, MoM)
```

---

## Step 4: Add Benchmark Questions

Use the benchmark questions from Section G to:

1. **Validate Genie Setup:** Run each question and verify SQL matches expected
2. **Test Edge Cases:** Ensure complex queries work correctly
3. **Onboard Users:** Show examples of what Genie can answer

### Testing Process

**For each benchmark question:**
1. Ask question in Genie Space
2. Review SQL generated
3. Compare to expected SQL from Section G
4. Verify results accuracy
5. Document any discrepancies

### Common Issues and Fixes

**Issue: Genie doesn't use Metric View**
- Fix: Update agent instructions to emphasize Metric View as primary source

**Issue: Wrong aggregation used**
- Fix: Add explicit guidance in agent instructions about SUM vs AVG

**Issue: Incorrect date filtering**
- Fix: Add examples of date range queries in instructions

**Issue: Doesn't use TVFs**
- Fix: Add examples showing when to use each TVF

---

## Implementation Checklist

### Choose Deployment Method

**Option 1: API Deployment (RECOMMENDED)**
- ✅ Version controlled
- ✅ Automated validation
- ✅ Repeatable across environments
- ✅ CI/CD ready

**Option 2: UI Deployment (Legacy)**
- Manual configuration
- No pre-validation
- Harder to replicate
- Suitable for one-off spaces

---

### API Deployment Workflow

#### Phase 1: Preparation (30 min)
- [ ] Ensure Metric Views are created and tested
- [ ] Ensure TVFs are created and tested
- [ ] Document all trusted assets
- [ ] List common business questions

#### Phase 2: Markdown Documentation (60 min)
- [ ] Create Sections A-G (Space Name through Benchmark Questions)
- [ ] Document all data assets
- [ ] Write concise General Instructions (≤20 lines)
- [ ] Create 10-15 benchmark questions with SQL

#### Phase 3: JSON Export Generation (30 min)
- [ ] Generate Section H JSON from Sections A-G
- [ ] Verify all IDs are 32-char hex (UUID without dashes)
- [ ] Verify all arrays are sorted (tables, metric_views, column_configs)
- [ ] Verify variables use `${catalog}` and `${gold_schema}` format
- [ ] Save as `{space_name}_genie_export.json` in `src/genie/`

#### Phase 4: Pre-Deployment Validation (5 min)
- [ ] Run validation task: `databricks bundle run genie_spaces_deployment_job`
- [ ] Review validation output (all benchmark SQL queries checked)
- [ ] Fix any SQL syntax/column/table errors
- [ ] Re-run validation until all queries pass

#### Phase 5: Deployment (5 min)
- [ ] Deploy bundle: `databricks bundle deploy -t dev`
- [ ] Run deployment job (validation + deployment)
- [ ] Verify Genie Space created successfully
- [ ] Note Space ID from output

#### Phase 6: Testing (15 min)
- [ ] Open Genie Space in Databricks UI
- [ ] Test sample questions from Section C
- [ ] Verify benchmark questions work correctly
- [ ] Refine instructions if needed (update JSON and redeploy)

**Total Time:** ~2.5 hours (vs 3-4 hours for manual UI setup)

---

### UI Deployment Workflow (Legacy)

#### Phase 1: Preparation (30 min)
- [ ] Ensure Metric Views are created and tested
- [ ] Ensure TVFs are created and tested
- [ ] Document all trusted assets
- [ ] List common business questions

#### Phase 2: Genie Space Setup (30 min)
- [ ] Create Genie Space in UI
- [ ] Add name and description (Sections A & B)
- [ ] Select SQL warehouse
- [ ] Grant permissions to user groups

#### Phase 3: Add Trusted Assets (15 min)
- [ ] Add all Metric Views (Section D)
- [ ] Add all Table-Valued Functions (Section F)
- [ ] Add dimension tables (Section D)
- [ ] Verify all assets accessible

#### Phase 4: Agent Instructions (15 min)
- [ ] Add General Instructions (Section E)
- [ ] Add Sample Questions to UI (Section C)

#### Phase 5: Testing (30 min)
- [ ] Test each Benchmark Question (Section G)
- [ ] Compare generated SQL to expected SQL
- [ ] Verify result accuracy
- [ ] Document issues
- [ ] Refine instructions as needed

**Total Time:** ~2 hours initial + ongoing manual maintenance

---

## Key Principles

### 1. Metric Views First
- ✅ Always prefer Metric Views over raw tables
- ✅ Semantic layer provides best query understanding
- ✅ Pre-defined measures and synonyms

### 2. TVFs for Common Queries
- ✅ Use TVFs when they match user question exactly
- ✅ Faster than generating complex SQL
- ✅ Ensures consistent business logic

### 3. Concise Instructions
- ✅ Keep General Instructions to 20 lines
- ✅ Be specific about data sources
- ✅ Define synonyms and alternatives

### 4. Benchmark with SQL
- ✅ Every benchmark question has expected SQL
- ✅ Test regularly after changes
- ✅ Use for validating Genie behavior

---

## Validation Queries

After setup, test these queries manually:

```sql
-- Test Metric View access
SELECT * FROM {catalog}.{schema}.{metric_view} LIMIT 5;

-- Test TVF access
SELECT * FROM get_{function}({params});

-- Test dimension access
SELECT * FROM {catalog}.{schema}.dim_{entity} LIMIT 10;

-- Test measure aggregation
SELECT 
  {dimension},
  MEASURE(`{Metric Name}`) as metric_value
FROM {catalog}.{schema}.{metric_view}
GROUP BY {dimension}
ORDER BY metric_value DESC
LIMIT 10;
```

---

## References

### Official Documentation
- [Genie Spaces](https://docs.databricks.com/genie/)
- [Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
- [Agent Instructions](https://docs.databricks.com/genie/agent-instructions)

### Framework Rules
- [genie-space-patterns.mdc](mdc:framework/rules/16-genie-space-patterns.mdc)

---

## Summary

**🔴 MANDATORY OUTPUT: Complete Genie Space Setup Document with 8 sections:**

| # | Section | What to Provide |
|---|---------|-----------------|
| A | Space Name | Exact name |
| B | Space Description | 2-3 sentences |
| C | Sample Questions | 10-15 questions |
| D | Data Assets | All tables & metric views |
| E | General Instructions | ≤20 lines of behavior rules |
| F | TVFs | All functions with signatures |
| G | Benchmark Questions | 10-15 questions with SQL answers |
| H | JSON Export | GenieSpaceExport format for API deployment |

**Time Estimate:** 1-2 hours (markdown) + 30 min (JSON generation)

**Deployment Options:**
1. **Manual:** Create document with sections A-G, then configure in Databricks UI
2. **Automated (RECOMMENDED):** Create document with all 8 sections, deploy via REST API using JSON from Section H




