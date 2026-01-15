# Framework Design Generation Context Prompt

## Purpose

This context prompt provides practical guidance for generating complete framework design documentation from project plans, based on the methodology in `.cursor/rules/planning/27-framework-design-methodology.mdc`.

---

## Generation Workflow

### Input: Project Plan Phase

**You will receive:**
- Project plan document (Phase 3 addendum, Phase 4, or Phase 5)
- Target framework name (e.g., "agent", "alerting", "dashboard")
- Domain context (Cost, Security, Performance, Reliability, Quality)

**Expected Output:**
- Complete framework design documentation suite (3,000-10,000 lines)
- All required documents (index, introduction, architecture, core chapters, implementation, deployment, appendices)
- Working code examples (tested and verified)
- Diagrams (ASCII art or Mermaid)
- Cross-references (links between documents)

---

## Generation Order

### Phase 1: Planning (10% of effort)

**Output:** Framework scope document

1. **Identify Major Components**
   - List 5-10 major components from the plan
   - For each component:
     - What does it do?
     - What are its inputs/outputs?
     - What dependencies does it have?

2. **Define Technical Challenges**
   - List 3-5 major technical challenges
   - For each challenge:
     - Why is this challenging?
     - What patterns solve this?
     - What cursor rules apply?

3. **List Best Practices**
   - Extract 10-15 best practices from the plan
   - Map each to a specific cursor rule or pattern
   - Identify which chapter will cover each practice

4. **Determine Target Audience**
   - Who will use this framework? (data engineers, ML engineers, analysts, etc.)
   - What's their skill level? (beginner, intermediate, advanced)
   - What context do they need?

5. **Define Success Criteria**
   - What should someone be able to do after reading this?
   - What metrics indicate successful implementation?
   - What edge cases should be handled?

**Deliverable:** 1-2 page scope document

---

### Phase 2: Structure (10% of effort)

**Output:** Document outline with chapter topics

1. **Create Document List**
   ```markdown
   # <Framework Name> Design Documentation Outline
   
   ## Core Documents (MANDATORY)
   - [ ] 00-index.md (~150 lines)
   - [ ] 01-introduction.md (~300 lines)
   - [ ] 02-architecture-overview.md (~600 lines)
   
   ## Core Chapters (3-10 chapters)
   - [ ] 03-<component-1>.md (~700 lines)
     - Topic: <What this covers>
     - Key Patterns: <3-5 patterns>
     - Code Examples: <2-3 examples>
   
   - [ ] 04-<component-2>.md (~700 lines)
     - Topic: <What this covers>
     - Key Patterns: <3-5 patterns>
     - Code Examples: <2-3 examples>
   
   <Continue for all chapters>
   
   ## Implementation & Operations
   - [ ] XX-implementation-guide.md (~1000 lines)
     - Phases: <List 3-5 phases>
     - Validation: <How to verify each phase>
   
   - [ ] YY-deployment-operations.md (~800 lines)
     - Deployment: <Strategy>
     - Monitoring: <Key metrics>
     - Troubleshooting: <Common issues>
   
   ## Appendices
   - [ ] appendices/A-code-examples.md (~300 lines)
   - [ ] appendices/B-cursor-rule-reference.md (~200 lines)
   - [ ] appendices/C-references.md (~150 lines)
   
   ## Optional
   - [ ] actual-implementation/ (if real implementation exists)
   - [ ] ZZ-frontend-integration.md (if frontend component)
   
   ## Total Estimated Lines: <sum>
   ```

2. **Map Plan to Chapters**
   - For each section of the project plan:
     - Which framework chapter will cover this?
     - What level of detail is needed?
     - What examples are required?

3. **Identify Cross-References**
   - Which chapters reference each other?
   - What cursor rules apply to each chapter?
   - What official documentation is relevant?

**Deliverable:** Complete document outline with estimated line counts

---

### Phase 3: Draft Index (10% of effort)

**Output:** 00-index.md (complete draft)

**Use Template from Rule 27:**

1. **Write Overview** (1 paragraph)
   - What is this framework?
   - What problem does it solve?
   - What's the implementation status?

2. **Define Design Principle** (highlighted box)
   - Extract core principle from project plan
   - 2-3 sentences explaining the principle
   - Why does this principle matter?

3. **Create Document Index Table**
   - List all planned documents
   - Number them sequentially
   - Write 1-sentence description for each
   - Link to document (even if not written yet)

4. **Draft Architecture Summary**
   - ASCII diagram (can be refined later)
   - Or structured bullet points
   - Show major components and data flow

5. **Write Quick Start** (4-5 steps)
   - Step 1: <Action with link>
   - Step 2: <Action with link>
   - Step 3: <Action with link>
   - Step 4: <Action with link>

6. **Create Best Practices Table**
   - List 10-15 best practices from plan
   - Map each to implementation in framework
   - Show which chapter covers each

7. **Document Technology Stack**
   - List all technologies used
   - For each: purpose, version (if known)

8. **Add Related Documentation Links**
   - Link to project plan
   - Link to relevant cursor rules
   - Link to related frameworks

**Review Criteria:**
- Can someone understand the framework from this index alone?
- Are all documents listed with clear descriptions?
- Is the architecture summary understandable?
- Are best practices clearly mapped?

---

### Phase 4: Architecture Overview (15% of effort)

**Output:** 02-architecture-overview.md (complete)

**Use Template from Rule 27:**

1. **Define Architecture Principle**
   - Restate or expand on principle from index
   - Explain why this principle was chosen
   - What alternatives were considered and rejected?

2. **Create High-Level Architecture Diagram**
   - Start with components from plan
   - Add data flow arrows
   - Label all integration points
   - Use ASCII art or Mermaid

   **Example ASCII Template:**
   ```
   ┌───────────────────────────────────────────────┐
   │              <LAYER NAME>                     │
   │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
   │  │Component1│  │Component2│  │Component3│    │
   │  └──────────┘  └──────────┘  └──────────┘    │
   └──────────┬───────────┬───────────┬────────────┘
              │           │           │
              ▼           ▼           ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐
         │ Output1 │ │ Output2 │ │ Output3 │
         └─────────┘ └─────────┘ └─────────┘
   ```

3. **Create Component Layer Table**
   - For each layer:
     - Purpose (what it does)
     - Components (what's in this layer)
     - Technologies (what tools are used)

4. **Write Component Breakdown**
   - For each major component:
     - Purpose (what it does)
     - Key features (3-5 bullet points)
     - Technologies (specific tools/libraries)
     - Configuration (example config)
     - Integration (inputs, outputs, dependencies)

5. **Document Data Flow**
   - Step-by-step numbered flow
   - For each step:
     - Input (what comes in)
     - Process (what happens)
     - Output (what comes out)

6. **Create Technology Stack Table**
   - Category (Compute, Storage, Orchestration, etc.)
   - Technology (specific tool)
   - Version (if known)
   - Purpose (why it's used)

7. **Document Integration Points**
   - External systems (what's outside this framework)
   - Internal APIs (how components communicate)
   - For each:
     - Integration type (REST, gRPC, etc.)
     - Protocol (HTTP, etc.)
     - Authentication (how it's secured)

8. **Add Scalability Considerations**
   - Horizontal scaling (how to scale out)
   - Vertical scaling (how to scale up)
   - Performance characteristics (expected metrics)

9. **Define Security Model**
   - Authentication (how users/systems authenticate)
   - Authorization (how permissions are managed)
   - Data protection (encryption, PII handling, audit logging)

**Review Criteria:**
- Can a developer understand the complete system from this document?
- Are all major components explained?
- Is the data flow clear and complete?
- Are integration points explicit?
- Is the security model comprehensive?

---

### Phase 5: Core Chapters (40% of effort)

**Output:** 03-XX.md (one complete chapter per component)

**Recommended Order:**
1. **Foundation Components** (what others depend on)
2. **Integration Patterns** (how components work together)
3. **Advanced Topics** (optimizations, edge cases)

**Per Chapter - Use Template from Rule 27:**

1. **Write Concept Overview** (2-3 paragraphs)
   - What is this component/pattern?
   - Why is it important?
   - When should you use it?

2. **Define Design Principles** (2-3 highlighted boxes)
   - Principle 1 with explanation
   - Principle 2 with explanation
   - Link to cursor rules that document these principles

3. **Create Basic Implementation Pattern**
   - Purpose (what this accomplishes)
   - When to use (scenarios)
   - Implementation (complete code with comments)
   - Explanation (step-by-step breakdown)

   **Code Example Format:**
   ````markdown
   **Implementation:**
   
   ```python
   # <Brief description>
   
   # Step 1: <What this does>
   <code>
   
   # Step 2: <What this does>
   <code>
   
   # Expected output:
   # <sample output>
   ```
   
   **Explanation:**
   1. **Lines X-Y**: <Why this is important>
   2. **Line Z**: <Why this is important>
   ````

4. **Create Advanced Pattern** (if needed)
   - Same structure as basic pattern
   - For complex scenarios
   - Show edge cases

5. **Document Common Patterns** (2-4 reusable templates)
   - Scenario (when to use)
   - Template (reusable code)
   - Example (concrete implementation)

6. **Write Best Practices** (3-5 do's and don'ts)
   - For each practice:
     - ❌ DON'T: <Anti-pattern with explanation>
     - ✅ DO: <Correct pattern with explanation>
     - Show code examples for both

7. **Add Integration Section**
   - Table showing how this integrates with other components
   - For each integration:
     - Component name
     - Integration point (API, interface, etc.)
     - How to use (brief description)

8. **Write Troubleshooting Section** (2-3 common issues)
   - For each issue:
     - Symptoms (what you see)
     - Cause (root cause)
     - Solution (how to fix with code)

9. **Add Performance Considerations**
   - Table of performance considerations
   - For each:
     - What affects performance
     - Impact (high, medium, low)
     - Recommendation (how to optimize)

10. **Link to References**
    - Official documentation (Databricks, MLflow, etc.)
    - Related chapters in this framework
    - Relevant cursor rules

**Review Criteria per Chapter:**
- Are all code examples complete and tested?
- Are patterns reusable?
- Are best practices clear with good/bad examples?
- Is troubleshooting practical?
- Are all references valid?

---

### Phase 6: Implementation Guide (15% of effort)

**Output:** XX-implementation-guide.md (complete)

**Use Template from Rule 27:**

1. **Define Implementation Phases** (3-5 phases typical)
   - Create phase overview table:
     - Phase number
     - Duration estimate
     - Focus (what's built)
     - Prerequisites (what's needed)

2. **Write Phase Dependency Diagram**
   - Show which phases depend on others
   - Use ASCII diagram or structured bullets

3. **For Each Phase - Complete Breakdown:**

   **Phase Objective:**
   - What this phase accomplishes (1-2 sentences)

   **Prerequisites:**
   - Checklist of what must be in place

   **Steps:**
   - Numbered steps (4-10 per phase)
   - For each step:
     - **Purpose**: Why this step matters
     - **Actions**: Specific commands/code
     - **Expected Outcome**: What should happen
     - **Verification**: How to check it worked

   **Example Step Format:**
   ````markdown
   #### Step X.Y: <Task Name>
   
   **Purpose:** <Why this step matters>
   
   **Actions:**
   
   1. <Action 1>
      ```bash
      <command>
      ```
   
   2. <Action 2>
      ```python
      <code>
      ```
   
   **Expected Outcome:** <What should happen>
   
   **Verification:**
   ```bash
   <verification command>
   ```
   
   **Expected Output:**
   ```
   <sample output>
   ```
   ````

   **Phase Validation Checklist:**
   - Checklist items to verify phase completion
   - For each item:
     - What to check
     - Command to verify
     - Expected result

   **Troubleshooting:**
   - Table of common issues in this phase
   - For each issue:
     - Issue description
     - Cause
     - Solution

4. **Document Testing Strategy**

   **Unit Testing:**
   - What to unit test
   - Example test with code

   **Integration Testing:**
   - What to integration test
   - Test scenarios (2-3)
   - For each scenario:
     - Setup (how to prepare)
     - Execute (how to run)
     - Verify (what to check)

   **End-to-End Testing:**
   - What to test end-to-end
   - Complete test flow

5. **Create Rollback Plan**

   **Rollback Triggers:**
   - When to rollback (conditions)

   **Rollback Procedure:**
   - Per phase, how to rollback
   - Commands with explanation

   **Rollback Verification:**
   - How to verify rollback succeeded

6. **Define Success Criteria**

   **Technical Criteria:**
   - Checklist of technical requirements
   - For each:
     - Metric to measure
     - Target value
     - How to measure

   **Business Criteria:**
   - Checklist of business requirements

7. **Add Post-Implementation Section**
   - Documentation updates needed
   - Training materials required
   - Knowledge transfer checklist
   - Monitoring setup

**Review Criteria:**
- Can someone follow this guide without prior knowledge?
- Are all commands complete and tested?
- Are validation steps clear?
- Is rollback plan comprehensive?
- Are success criteria measurable?

---

### Phase 7: Deployment & Operations (10% of effort)

**Output:** YY-deployment-operations.md (complete)

**Use Template from Rule 27:**

1. **Define Deployment Strategy**
   - Environment table (dev, staging, prod)
   - Deployment process (step-by-step)
   - Rollback procedure

2. **Document Configuration Management**
   - Environment variables table
   - Secrets management (where, how, rotation)
   - Configuration files (location, format)

3. **Create Monitoring and Alerting Section**
   - Key metrics table (metric, thresholds, alert channel)
   - Monitoring dashboards (URL, key panels)
   - Alert configuration (example config)
   - On-call procedures (escalation path, SLAs)

4. **Define Maintenance Procedures**
   - Daily operations table
   - Weekly operations table
   - Monthly operations table

5. **Document Disaster Recovery**
   - Backup strategy (what, frequency, retention, location)
   - Recovery procedures (per failure scenario)
   - Recovery testing (schedule, procedure)

6. **Write Troubleshooting Guide**
   - Common issues (2-5)
   - For each:
     - Symptoms
     - Diagnosis (commands)
     - Resolution (fix commands)
     - Prevention (how to avoid)
   - Debug commands (useful commands)
   - Log analysis (locations, patterns)

7. **Add Performance Tuning Section**
   - Performance baselines table
   - Optimization opportunities (2-3)
   - For each:
     - Current state
     - Improvement suggestion
     - Expected gain

**Review Criteria:**
- Are all operational scenarios covered?
- Are monitoring metrics defined with thresholds?
- Is disaster recovery comprehensive and tested?
- Are troubleshooting steps actionable?

---

### Phase 8: Appendices (5% of effort)

**Output:** appendices/A-D (complete)

**Appendix A: Code Examples**

1. Extract all code examples from core chapters
2. Organize by topic/chapter
3. For each example:
   - Copy complete code
   - Ensure inline comments
   - Show expected output
   - Add context (when to use this)

**Appendix B: Cursor Rule Reference**

1. List all relevant cursor rules
2. For each rule:
   - Rule name and file path
   - Brief description (1-2 sentences)
   - How it applies to this framework
   - Example pattern from this framework

**Appendix C: Official Documentation**

1. List all official Databricks documentation links
2. Organize by category:
   - SDK/API documentation
   - UI documentation
   - Best practices
   - Examples/tutorials
3. For each link:
   - URL
   - Brief description
   - Which chapter references this

**Appendix D: Implementation Reference** (Optional)

1. Show complete file tree of actual implementation
2. For each file:
   - Brief purpose description
   - Link to source (if applicable)

---

### Phase 9: Introduction (5% of effort)

**Output:** 01-introduction.md (complete)

**Why Write This Last:**
- You now understand the complete framework
- Can write accurate scope
- Can identify all prerequisites
- Can list all key concepts
- Can create comprehensive best practices matrix

**Use Template from Rule 27:**

1. **Write Purpose** (2-3 paragraphs)
   - Why does this framework exist?
   - Who is it for?
   - What are key outcomes?

2. **Define Scope**
   - In Scope table (what's covered)
   - Out of Scope table (what's NOT covered + where to find it)

3. **List Prerequisites**
   - Checklist of prerequisites
   - For each:
     - Requirement details
     - Status check command

4. **Define Key Concepts** (5-10 concepts)
   - For each concept:
     - Definition
     - Example (code or scenario)

5. **Create Best Practices Matrix**
   - Extract from all best practice sections
   - Create table:
     - Category (Architecture, Data Quality, etc.)
     - Best Practice
     - Implementation Chapter (link)

6. **Document Structure Overview**
   - Quick tree view of documentation
   - Recommended reading order (by role)

7. **State Assumptions**
   - Explicit checklist of assumptions

**Review Criteria:**
- Is the purpose clear?
- Is scope accurate (matches actual content)?
- Are prerequisites complete and verifiable?
- Are key concepts fundamental to understanding?
- Does best practices matrix cover all practices in framework?

---

### Phase 10: Final Review (5% of effort)

**Completeness Check:**

1. **Document Count Verification**
   - [ ] 00-index.md exists
   - [ ] 01-introduction.md exists
   - [ ] 02-architecture-overview.md exists
   - [ ] 3-10 core chapters exist
   - [ ] Implementation guide exists
   - [ ] Deployment & operations guide exists
   - [ ] 3-4 appendices exist
   - [ ] Total documents: 10-20

2. **Per Document - Required Sections**
   - Run through checklist in Rule 27 for each document type
   - Verify all required sections present
   - Check all code examples are complete
   - Verify all links work

3. **Cross-Reference Audit**
   - Every chapter references 3+ other documents
   - Index accurately lists all documents
   - Introduction references all core chapters
   - Architecture overview is referenced by all core chapters

4. **Code Example Verification**
   - Every code example is complete (can copy-paste and run)
   - Every example has inline comments
   - Every example shows expected output
   - All examples follow cursor rule patterns

5. **Length Verification**
   - Index: 100-200 lines ✓
   - Introduction: 200-400 lines ✓
   - Architecture: 400-800 lines ✓
   - Core chapters: 500-1000 lines each ✓
   - Implementation: 700-1200 lines ✓
   - Deployment: 600-1000 lines ✓
   - Appendices: 100-500 lines each ✓
   - **Total: 3,000-10,000 lines ✓**

**Quality Check:**

1. **Grammar and Spelling**
   - Run spellchecker on all documents
   - Fix all grammar issues
   - Ensure consistent terminology

2. **Code Formatting**
   - All code blocks have language tags
   - All Python code follows PEP 8
   - All SQL code is uppercase keywords
   - All bash commands are tested

3. **Diagram Quality**
   - All ASCII diagrams are aligned
   - All Mermaid diagrams render correctly
   - All diagrams have clear labels
   - All diagrams flow top-to-bottom or left-to-right

4. **Table Formatting**
   - All tables have proper Markdown syntax
   - All columns are aligned
   - All headers are clear

5. **Link Verification**
   - All internal links work
   - All external links are valid
   - All cursor rule references are correct

**Polish:**

1. **Consistency Pass**
   - Same terminology throughout
   - Same code style throughout
   - Same diagram notation throughout
   - Same heading levels throughout

2. **Readability Pass**
   - Remove jargon (or define it)
   - Simplify complex sentences
   - Add examples where needed
   - Break up long paragraphs

3. **Navigation Pass**
   - Clear chapter transitions
   - Good cross-references
   - Helpful "See also" sections

---

## Code Example Guidelines

### Complete Example Checklist

Every code example must:

- [ ] **Be self-contained** (can run without modifications)
- [ ] **Have inline comments** (explain key lines)
- [ ] **Show input** (what goes in)
- [ ] **Show output** (what comes out)
- [ ] **Follow best practices** (from cursor rules)
- [ ] **Be tested** (verified working)
- [ ] **Use consistent formatting** (language linter)
- [ ] **Have context** (when to use this)

### Example Template

````markdown
### Example: <Description>

**Scenario:** <When you would use this>

**Implementation:**

```python
# <Brief description of what this does>

# Step 1: <What this step does>
<code line 1>
<code line 2>

# Step 2: <What this step does>
<code line 3>
<code line 4>

# Expected output:
# <sample output>
```

**Explanation:**

1. **Lines 1-2**: <Why these lines are important>
   - <Additional context if needed>

2. **Lines 3-4**: <Why these lines are important>
   - <Additional context if needed>

**Expected Output:**

```
<complete sample output>
```

**When to Use:**
- <Scenario 1>
- <Scenario 2>

**Related Patterns:**
- [<Pattern Name>](#link-to-pattern)
- [<Chapter Name>](XX-chapter.md)
````

---

## Diagram Guidelines

### ASCII Diagram Standards

**Requirements:**

- [ ] **Clear purpose** (what it's explaining)
- [ ] **Consistent notation** (same symbols throughout)
- [ ] **Readable** (not cluttered)
- [ ] **Legend** (if needed)
- [ ] **Standard flow** (top-to-bottom or left-to-right)
- [ ] **Aligned** (proper spacing)

### Component Diagram Template

```
┌─────────────────────────────────────────────────────────┐
│                  <COMPONENT NAME>                        │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ SubComp1 │    │ SubComp2 │    │ SubComp3 │          │
│  │          │    │          │    │          │          │
│  │ Purpose  │    │ Purpose  │    │ Purpose  │          │
│  └──────────┘    └──────────┘    └──────────┘          │
│        │               │               │                │
└────────┼───────────────┼───────────────┼────────────────┘
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ Output1 │     │ Output2 │     │ Output3 │
    └─────────┘     └─────────┘     └─────────┘
```

### Data Flow Diagram Template

```
┌─────────┐
│ Source  │
└────┬────┘
     │
     │ Data Type
     │ Format
     ▼
┌─────────────┐
│ Processing  │
│ Component   │
│ • Action 1  │
│ • Action 2  │
└─────┬───────┘
      │
      │ Transformed Data
      │ New Format
      ▼
┌─────────────┐
│ Destination │
└─────────────┘
```

### Multi-Layer Architecture Template

```
┌────────────────────────────────────────────────────────────┐
│                      LAYER 3: UI                           │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│   │Frontend1 │  │Frontend2 │  │Frontend3 │                │
│   └──────────┘  └──────────┘  └──────────┘                │
└────────┬───────────────┬───────────────┬────────────────────┘
         │               │               │
         ▼               ▼               ▼
┌────────────────────────────────────────────────────────────┐
│                   LAYER 2: BUSINESS LOGIC                  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│   │Service 1 │  │Service 2 │  │Service 3 │                │
│   └──────────┘  └──────────┘  └──────────┘                │
└────────┬───────────────┬───────────────┬────────────────────┘
         │               │               │
         ▼               ▼               ▼
┌────────────────────────────────────────────────────────────┐
│                    LAYER 1: DATA                           │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│   │Database1 │  │Database2 │  │Database3 │                │
│   └──────────┘  └──────────┘  └──────────┘                │
└────────────────────────────────────────────────────────────┘
```

---

## Quality Checklist

### Before Declaring "Complete"

**Documentation Completeness:**

- [ ] All required documents created
- [ ] All documents have all required sections
- [ ] Total line count: 3,000-10,000 lines
- [ ] All code examples are complete
- [ ] All diagrams are clear
- [ ] All tables are formatted
- [ ] All links work

**Technical Accuracy:**

- [ ] All code examples tested and working
- [ ] All commands verified
- [ ] All configurations accurate
- [ ] All best practices align with cursor rules
- [ ] All references to official docs are current

**Usability:**

- [ ] Can someone follow the implementation guide?
- [ ] Are troubleshooting steps actionable?
- [ ] Is the architecture understandable?
- [ ] Are examples clear and practical?
- [ ] Is navigation easy?

**Consistency:**

- [ ] Terminology consistent throughout
- [ ] Code style consistent
- [ ] Diagram notation consistent
- [ ] Formatting consistent
- [ ] Heading levels consistent

**Cross-Referencing:**

- [ ] Index accurately lists all documents
- [ ] Every chapter references 3+ others
- [ ] All cursor rules referenced where applicable
- [ ] All official docs linked
- [ ] Related frameworks linked

---

## Success Metrics

### Framework Quality Indicators

| Indicator | Target | Measurement |
|---|---|---|
| **Completeness** | 100% | All required sections present |
| **Accuracy** | 0 errors | Technical review passes |
| **Clarity** | 90%+ comprehension | User testing |
| **Code Quality** | 100% working | All examples execute |
| **Length** | 3,000-10,000 lines | Line count |
| **Cross-References** | 3+ per document | Link audit |

### Adoption Indicators

| Indicator | Target | Measurement |
|---|---|---|
| **Implementation Time** | <50% without docs | Project timeline comparison |
| **Bug Rate** | 50% reduction | Bug tracking |
| **Onboarding Time** | <2 days | Time to first contribution |
| **Usage Rate** | 80%+ weekly | Analytics |
| **Pattern Adoption** | 90%+ | Code review metrics |

---

## References

- [27-framework-design-methodology.mdc](../../../.cursor/rules/planning/27-framework-design-methodology.mdc) - Complete methodology
- [26-project-plan-methodology.mdc](../../../.cursor/rules/planning/26-project-plan-methodology.mdc) - Project planning patterns

---

## Example Frameworks

Study these for patterns:

| Framework | Location | Key Learnings |
|---|---|---|
| **Agent Framework** | `docs/agent-framework-design/` | Multi-agent, MLflow 3.0, frontend integration |
| **Alerting Framework** | `docs/alerting-framework-design/` | Config-driven, SDK integration, hierarchical jobs |
| **Dashboard Framework** | `docs/dashboard-framework-design/` | Asset rationalization, variable substitution |
| **ML Framework** | `docs/ml-framework-design/` | Feature engineering, batch inference, troubleshooting |
| **Semantic Framework** | `docs/semantic-framework/` | TVFs, metric views, domain organization |
| **Lakehouse Monitoring** | `docs/lakehouse-monitoring-design/` | Custom metrics, Genie integration |
| **Frontend Framework** | `docs/frontend-framework-design/` | Design system, component library, PRD |
| **Project Architecture** | `docs/project-architecture-design/` | Architecture evolution, PRDs |
