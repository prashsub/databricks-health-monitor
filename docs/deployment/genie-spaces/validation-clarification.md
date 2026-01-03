# Genie Space Validation Clarification: JSON vs Markdown

**Date:** 2026-01-03
**Issue:** Validation was extracting SQL from markdown files instead of JSON exports
**Status:** ✅ Fixed

---

## The Clarification

**User's Key Insight:**
> "The markdown files are simply listing it for human review. The same benchmark questions should be part of your Genie JSON export, the SQL of that needs to be validated before deployment."

---

## Problem

### Before (Incorrect)
```
Markdown files (*_genie.md)
  └─ Section G: Benchmark Questions with SQL
       └─ ❌ Validation extracted SQL from here

JSON exports (*_genie_export.json)  
  └─ benchmarks.questions[].answer[].content
       └─ ✅ But this is what gets deployed!
```

**Issue:** Validating markdown SQL doesn't guarantee JSON SQL is correct.

### Root Cause
Initial implementation assumed:
- Markdown Section G = documentation only
- **BUT** didn't validate the actual deployed SQL (JSON)

---

## Solution

### After (Correct)
```
Markdown files (*_genie.md)
  └─ Section G: Benchmark Questions with SQL
       └─ 📖 Human documentation only (not validated)

JSON exports (*_genie_export.json)  
  └─ benchmarks.questions[].answer[].content
       └─ ✅ THIS is validated before deployment
```

**Fix:** Validation now reads from JSON export files.

---

## Technical Changes

### 1. Updated `validate_genie_benchmark_sql.py`

**Before:**
```python
def extract_benchmark_queries_from_markdown(md_path: Path, ...):
    """Extract SQL from markdown Section G"""
    # Regex to parse ### Question N: ... **Expected SQL:**
    return queries
```

**After:**
```python
def extract_benchmark_queries_from_json(json_path: Path, ...):
    """Extract SQL from JSON benchmarks section"""
    data = json.load(json_path)
    benchmarks = data['benchmarks']['questions']
    
    for benchmark in benchmarks:
        # Get SQL from answer[].content array
        sql_lines = benchmark['answer'][0]['content']
        sql_query = ''.join(sql_lines)
        # Substitute variables and validate
    return queries
```

**Key Difference:**
- ❌ `glob("*_genie.md")` → ✅ `glob("*_genie_export.json")`
- ❌ Regex parsing → ✅ JSON parsing
- ❌ Section G → ✅ `benchmarks.questions`

---

### 2. Updated Prompt (`06-genie-space-prompt.md`)

**Added Clarifications:**

#### Section H Header
```markdown
## █  SECTION H: JSON EXPORT FOR API DEPLOYMENT                   █
## █  ⚠️ INCLUDES BENCHMARK SQL - THIS IS WHAT GETS VALIDATED     █
```

#### Critical Notice
```markdown
**⚠️ CRITICAL:** The `benchmarks` section in the JSON is what gets validated 
before deployment. The benchmark SQL in Section G (markdown) is for human 
documentation only.
```

#### Validation Flow Documentation
```markdown
**⚠️ CRITICAL VALIDATION FLOW:**
1. Pre-deployment validation reads `benchmarks.questions[].answer[].content` from JSON
2. Joins the content array into a single SQL string
3. Substitutes `${catalog}` and `${gold_schema}` variables
4. Runs `EXPLAIN` on each SQL query to validate syntax, columns, tables
5. Deployment only proceeds if ALL benchmark SQL queries are valid
```

#### Enhanced Example
Added detailed example showing SQL content as array:
```json
"benchmarks": {
  "questions": [
    {
      "id": "...",
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
    }
  ]
}
```

---

### 3. Updated Documentation

**`docs/deployment/genie-spaces/benchmark-sql-validation.md`:**

#### Relationship Table
| File | Section | Purpose | Validated? |
|------|---------|---------|-----------|
| `{space}_genie.md` | Section G | Human documentation | ❌ No |
| `{space}_genie_export.json` | benchmarks.questions | Machine deployment | ✅ Yes |

#### Workflow Diagram
```
Task 1: validate_genie_spaces
  ├─ Read *_genie_export.json      ← JSON, not markdown!
  ├─ Extract benchmarks.questions
  ├─ Join SQL content array
  ├─ Substitute variables
  ├─ EXPLAIN each query
  └─ Report errors
```

---

## The Proper Workflow

### Developer Creates Genie Space

1. **Write Markdown (Sections A-G)** - Human documentation
   ```markdown
   ## Section G: Benchmark Questions
   
   ### Question 1: "What is total revenue?"
   **Expected SQL:**
   ```sql
   SELECT MEASURE(total_revenue) FROM metric_view;
   ```
   ```

2. **Generate JSON (Section H)** - Machine deployment
   ```json
   {
     "benchmarks": {
       "questions": [
         {
           "question": ["What is total revenue?"],
           "answer": [{
             "format": "SQL",
             "content": [
               "SELECT MEASURE(total_revenue) FROM metric_view;"
             ]
           }]
         }
       ]
     }
   }
   ```

3. **Validation Reads JSON** ✅ Not markdown!
   ```python
   json_files = glob("*_genie_export.json")
   for json_file in json_files:
       queries = extract_from_json(json_file)  # ← From JSON
       for query in queries:
           spark.sql(f"EXPLAIN {query}")  # Validate
   ```

4. **Deploy if Valid**
   - ✅ All SQL queries valid → Deploy Genie Space
   - ❌ Any SQL errors → Block deployment, show errors

---

## Why This Matters

### Scenario: Typo in JSON but Not Markdown

**Markdown (Section G):**
```markdown
### Question 1: "Top products by revenue"
**Expected SQL:**
```sql
SELECT product_name, MEASURE(total_revenue) as revenue
FROM product_revenue
ORDER BY revenue DESC LIMIT 10;
```
```

**JSON (Section H):**
```json
{
  "content": [
    "SELECT product_nam, MEASURE(total_revenue) as revenue\n",  // ← Typo!
    "FROM product_revenue\n",
    "ORDER BY revenue DESC LIMIT 10;"
  ]
}
```

### Before Fix (Validating Markdown)
```
Validation: ✅ PASS (markdown SQL is correct)
Deployment: ✅ SUCCESS
Genie Space: ❌ FAILS (typo in deployed JSON SQL)
```

### After Fix (Validating JSON)
```
Validation: ❌ FAIL (typo detected in JSON)
  Error: Column 'product_nam' not found. Did you mean 'product_name'?
Deployment: 🚫 BLOCKED
Developer: Fix JSON, redeploy
Genie Space: ✅ Works correctly
```

---

## Validation Output Example

### JSON-Based Validation (Correct)

```
📋 Found 2 Genie Space JSON export files
   cost_intelligence_genie_export.json: 12 benchmark queries
   job_health_monitor_genie_export.json: 12 benchmark queries

🔍 Validating 24 benchmark queries from JSON exports...
  [1/24] ✓ cost_intelligence Q1
  [2/24] ✓ cost_intelligence Q2
  [3/24] ✗ cost_intelligence Q3
    Error: [UNRESOLVED_COLUMN] Column 'total_spend' not found
    Suggestion: Did you mean 'total_cost'?
  ...

❌ VALIDATION FAILED: 1 benchmark queries have errors.
RuntimeError: Genie Space benchmark SQL validation failed for 1 queries.
```

**Result:** Deployment blocked until JSON is fixed.

---

## Testing

### Deployment Test (Jan 3, 2026)

```bash
$ databricks bundle run genie_spaces_deployment_job --profile health_monitor

Run URL: https://e2-demo-field-eng.cloud.databricks.com/...

Task validate_genie_spaces: SUCCESS ✅
Task deploy_genie_spaces: SUCCESS ✅
```

**Validation Output:**
- Read from `*_genie_export.json` files ✅
- Extracted SQL from `benchmarks.questions[].answer[].content` ✅
- Validated 24 benchmark queries ✅
- All queries valid ✅
- Deployment proceeded ✅

---

## Files Modified

| File | Changes |
|------|---------|
| `src/genie/validate_genie_benchmark_sql.py` | Changed from markdown parsing to JSON parsing |
| `context/prompts/semantic-layer/06-genie-space-prompt.md` | Added clarifications about JSON validation |
| `docs/deployment/genie-spaces/benchmark-sql-validation.md` | Updated to reflect JSON-based validation |
| `docs/deployment/genie-spaces/validation-clarification.md` | This document |

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Validation Source** | Markdown Section G | JSON benchmarks.questions |
| **Files Read** | `*_genie.md` | `*_genie_export.json` |
| **Extraction Method** | Regex parsing | JSON parsing |
| **SQL Format** | String from markdown | Array joined from JSON |
| **Guarantees** | Markdown SQL valid | **Deployed SQL valid** ✅ |
| **Error Detection** | Late (after deployment) | Early (before deployment) |

---

## Key Takeaway

**The JSON export is the source of truth for deployment.**

- ✅ Section G (markdown) = Human documentation
- ✅ Section H (JSON) = Machine deployment + validation

**Validation must always check the JSON**, not the markdown.

---

## References

- **Validation Script:** `src/genie/validate_genie_benchmark_sql.py`
- **Updated Prompt:** `context/prompts/semantic-layer/06-genie-space-prompt.md`
- **Validation Docs:** `docs/deployment/genie-spaces/benchmark-sql-validation.md`
- **JSON Schema:** `.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc`

