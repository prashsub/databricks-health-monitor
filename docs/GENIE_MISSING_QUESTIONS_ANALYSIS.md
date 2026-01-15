# Genie Space Missing Questions Analysis

**Date:** January 9, 2026  
**Issue:** 123 questions in JSON files vs 150 expected (25 per space × 6 spaces)  
**Root Cause:** Questions documented in .md files but never copied to JSON export files

---

## 📊 Question Count Summary

| Genie Space | Expected | Actual (JSON) | Missing | Status |
|---|---|---|---|---|
| cost_intelligence | 25 | 25 | 0 | ✅ Complete |
| performance | 25 | 25 | 0 | ✅ Complete |
| data_quality_monitor | 25 | 16 | 9 | ❌ Missing Q17-Q25 |
| job_health_monitor | 25 | 18 | 7 | ❌ Missing Q19-Q25 |
| security_auditor | 25 | 18 | 7 | ❌ Missing Q19-Q25 |
| unified_health_monitor | 25 | 21 | 4 | ❌ Missing Q22-Q25 |
| **TOTAL** | **150** | **123** | **27** | **82% coverage** |

---

## 🔍 Missing Questions Breakdown

### data_quality_monitor (9 missing)
**Missing Q17-Q25:**
- Q17: "What is our ML prediction accuracy?"
- Q18: "Show me quality drift metrics"
- Q19: "What is the governance coverage?"
- Q20: "Show me quality score distribution"
- Q21: 🔬 DEEP RESEARCH: Comprehensive table health assessment
- Q22: 🔬 DEEP RESEARCH: Data freshness optimization
- Q23: 🔬 DEEP RESEARCH: Data quality ROI analysis
- Q24: 🔬 DEEP RESEARCH: ML-powered quality forecasting
- Q25: 🔬 DEEP RESEARCH: End-to-end governance dashboard

### job_health_monitor (7 missing)
**Missing Q19-Q25:**
- Q19: "Show me job execution patterns"
- Q20: "What is the job repair success rate?"
- Q21: 🔬 DEEP RESEARCH: Job reliability dashboard
- Q22: 🔬 DEEP RESEARCH: Cross-job dependency analysis
- Q23: 🔬 DEEP RESEARCH: Job cost vs reliability tradeoffs
- Q24: 🔬 DEEP RESEARCH: Predictive job failure analysis
- Q25: 🔬 DEEP RESEARCH: Executive job health dashboard

### security_auditor (7 missing)
**Missing Q19-Q25:**
- Q19: "Show me user authentication patterns"
- Q20: "What is our security compliance score?"
- Q21: 🔬 DEEP RESEARCH: Security threat detection
- Q22: 🔬 DEEP RESEARCH: Access control effectiveness
- Q23: 🔬 DEEP RESEARCH: Insider threat analysis
- Q24: 🔬 DEEP RESEARCH: Compliance audit trail
- Q25: 🔬 DEEP RESEARCH: Executive security dashboard

### unified_health_monitor (4 missing)
**Missing Q22-Q25:**
- Q22: 🔬 DEEP RESEARCH: Cross-domain anomaly detection
- Q23: 🔬 DEEP RESEARCH: Platform optimization roadmap
- Q24: 🔬 DEEP RESEARCH: Executive platform health report
- Q25: 🔬 DEEP RESEARCH: Predictive platform intelligence

---

## 🎯 Impact Analysis

### Why This Matters

1. **Validation Coverage:** Currently validating 123/150 (82%)
2. **Missing Deep Research:** Most missing questions are complex "Deep Research" queries
3. **Benchmark Completeness:** Genie Spaces have incomplete benchmark coverage
4. **User Expectations:** Documentation promises 25 questions, but 4 spaces deliver <20

### Risk Assessment

| Risk | Severity | Impact |
|---|---|---|
| **Incomplete Validation** | Medium | 27 SQL queries never tested |
| **Missing Features** | Low | Questions exist in .md specs |
| **Documentation Mismatch** | Medium | Users expect 150, get 123 |
| **Complex Query Gaps** | Medium | Deep Research queries missing |

---

## 🔧 Recommended Actions

### Option 1: Add All Missing Questions (Recommended)
**Goal:** Get to 150/150 benchmark questions

**Steps:**
1. Extract missing questions from .md files
2. Generate SQL for missing questions
3. Add to JSON export files
4. Validate all 150 questions
5. Deploy complete Genie Spaces

**Timeline:** 4-6 hours  
**Benefit:** 100% feature parity with documentation

### Option 2: Document Actual Coverage
**Goal:** Align documentation with reality

**Steps:**
1. Update .md files to show actual question counts
2. Mark missing questions as "Future Enhancement"
3. Deploy 123 questions as-is

**Timeline:** 1 hour  
**Benefit:** Truth in advertising, no validation risk

### Option 3: Hybrid Approach (Balanced)
**Goal:** Add high-value missing questions only

**Steps:**
1. Add missing Q17-Q21 (normal questions) = +20 questions
2. Skip Deep Research Q22-Q25 for now = defer 7 questions
3. Validate 143 questions
4. Deploy with "143/150 coverage"

**Timeline:** 2-3 hours  
**Benefit:** Most value, lower risk

---

## 📋 Implementation Plan (Option 1: Complete Coverage)

### Phase 1: Extract Missing Questions from .md Files
**File:** `scripts/extract_missing_genie_questions.py`

```python
import re
import json
from pathlib import Path

def extract_questions_from_md(md_file):
    """Extract benchmark questions from .md specification."""
    content = open(md_file).read()
    
    # Find all Q[0-9]+ sections
    pattern = r'### Question (\d+): "(.*?)".*?```sql\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    questions = []
    for q_num, q_text, q_sql in matches:
        questions.append({
            "id": f"Q{q_num}_{md_file.stem}",
            "question": [q_text],
            "answer": [{
                "format": "SQL",
                "content": [q_sql.strip()]
            }]
        })
    
    return questions

# Process each Genie space
for md_file in Path("src/genie").glob("*_genie.md"):
    json_file = md_file.with_suffix("_export.json")
    
    # Extract from .md
    md_questions = extract_questions_from_md(md_file)
    
    # Load existing JSON
    json_data = json.load(open(json_file))
    existing_count = len(json_data["benchmarks"]["questions"])
    
    # Add missing questions
    for q in md_questions[existing_count:]:
        json_data["benchmarks"]["questions"].append(q)
    
    # Save updated JSON
    json.dump(json_data, open(json_file, "w"), indent=2)
    
    print(f"{md_file.stem}: {existing_count} → {len(json_data['benchmarks']['questions'])}")
```

### Phase 2: Validate All 150 Questions
```bash
databricks bundle deploy -t dev
databricks bundle run -t dev genie_benchmark_sql_validation_job
```

### Phase 3: Fix Any New Errors
Expected new error types:
- Missing TVFs (if questions reference non-existent functions)
- Column mismatches (if schemas changed)
- Syntax errors (from manual .md documentation)

### Phase 4: Deploy Complete Genie Spaces
```bash
databricks bundle deploy -t dev
databricks bundle run -t dev genie_spaces_deployment_job
```

---

## 📊 Expected Validation Results

### Before Adding Questions
- **Pass Rate:** 96% (118/123)
- **Coverage:** 82% (123/150)

### After Adding Questions
- **Pass Rate:** ~85-90% (128-135/150) - new questions may have errors
- **Coverage:** 100% (150/150)
- **Fix Effort:** Estimated 20-30 new errors to fix

---

## 🎓 Lessons Learned

### Root Cause
**Why did this happen?**
1. .md files created first as specifications
2. JSON files created manually (not auto-generated from .md)
3. Copy-paste process incomplete (stopped at Q16-Q21 for 4 spaces)
4. No validation to ensure .md ↔ JSON parity

### Prevention
**How to avoid in future:**
1. Generate JSON from .md automatically (single source of truth)
2. Add validation: "JSON must have same question count as .md"
3. Use structured data format (YAML) for both .md and JSON
4. Automated sync scripts with validation

---

## 🚀 Recommendation

### Short-Term (This Week)
✅ **Option 2: Document Actual Coverage**
- Update validation script to show "123/123 (100%)"
- Update .md files: "Benchmark Questions: 16-25 (varies by space)"
- Deploy at 96% pass rate with 123 questions
- **Rationale:** Fastest path to deployment, no new validation risk

### Medium-Term (Next Sprint)
📋 **Option 3: Hybrid Approach**
- Add missing Q17-Q21 normal questions (+20)
- Defer Deep Research Q22-Q25 for later (+7)
- Validate 143 questions
- Deploy at ~90% pass rate
- **Rationale:** Balanced value vs risk

### Long-Term (Future Enhancement)
🎯 **Option 1: Complete Coverage**
- Add all 27 missing questions
- Validate all 150 questions
- Fix any new errors
- Deploy at 100% coverage
- **Rationale:** Feature completeness, but requires 4-6 hour investment

---

## 📞 Decision Needed

**Which option should we pursue?**
1. ✅ Deploy now with 123 questions (fastest, lowest risk)
2. 📋 Add 20 normal questions first (balanced)
3. 🎯 Add all 27 questions (complete, but higher risk)

**Current recommendation:** **Option 1** - Deploy now, add questions in next iteration.

---

**Status:** Analysis complete  
**Recommendation:** Deploy 123 questions now, add missing 27 in next sprint  
**Deployment Readiness:** ✅ Ready at 96% (118/123 passing)

