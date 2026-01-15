# Planning Context Prompts

## Overview

This directory contains context prompts that provide practical guidance for project planning and framework design documentation.

---

## Prompts Index

| Prompt | File | Purpose | Usage |
|---|---|---|---|
| **Framework Design Generation** | [framework-design-generation.md](framework-design-generation.md) | Practical workflow for generating framework designs from plans | Use when transforming a project plan into comprehensive framework documentation |

---

## Workflow Integration

### 1. Project Planning Phase

**Use:** `.cursor/rules/planning/26-project-plan-methodology.mdc`

**Inputs:**
- User requirements
- Data sources (system tables)
- Target domains
- Official documentation

**Outputs:**
- `plans/README.md` - Project overview
- `plans/phase3-use-cases.md` - Master plan
- `plans/phase3-addendum-3.X-*.md` - Domain-specific plans
- `plans/phase4-agent-framework.md` - Agent architecture
- `plans/phase5-frontend-app.md` - UI design

---

### 2. Framework Design Phase ✨

**Use:** 
- `.cursor/rules/planning/27-framework-design-methodology.mdc` (comprehensive rule)
- `context/prompts/planning/framework-design-generation.md` (practical workflow)

**Inputs:**
- Completed project plan (Phase 3 addendum, Phase 4, or Phase 5)
- Framework name (e.g., "agent", "alerting", "dashboard")
- Target audience (data engineers, ML engineers, analysts)

**Outputs:**
- `docs/<framework>-design/00-index.md` - Navigation hub (~150 lines)
- `docs/<framework>-design/01-introduction.md` - Purpose, scope (~300 lines)
- `docs/<framework>-design/02-architecture-overview.md` - System design (~600 lines)
- `docs/<framework>-design/03-XX.md` - Core chapters (~700 lines each, 3-10 chapters)
- `docs/<framework>-design/XX-implementation-guide.md` - Step-by-step (~1000 lines)
- `docs/<framework>-design/YY-deployment-operations.md` - Production (~800 lines)
- `docs/<framework>-design/appendices/` - Supporting materials (~300-500 lines each)

**Total:** 3,000-10,000 lines of comprehensive documentation

---

## Quick Reference: Generation Workflow

### Phase 1: Planning (10% effort)

**Output:** Framework scope document

1. Identify major components (5-10)
2. Define technical challenges (3-5)
3. List best practices (10-15)
4. Determine target audience
5. Define success criteria

**Deliverable:** 1-2 page scope document

---

### Phase 2: Structure (10% effort)

**Output:** Document outline

1. Create document list with topics
2. Map plan sections to chapters
3. Identify cross-references
4. Estimate line counts

**Deliverable:** Complete outline with estimates

---

### Phase 3: Draft Index (10% effort)

**Output:** 00-index.md (complete)

1. Write overview (1 paragraph)
2. Define design principle (highlighted box)
3. Create document index table
4. Draft architecture summary
5. Write quick start (4-5 steps)
6. Create best practices table
7. Document technology stack
8. Add related documentation links

**Review:** Can someone understand the framework from this index?

---

### Phase 4: Architecture Overview (15% effort)

**Output:** 02-architecture-overview.md (complete)

1. Define architecture principle
2. Create high-level diagram
3. Create component layer table
4. Write component breakdown
5. Document data flow
6. Create technology stack table
7. Document integration points
8. Add scalability considerations
9. Define security model

**Review:** Can a developer understand the system from this?

---

### Phase 5: Core Chapters (40% effort)

**Output:** 03-XX.md (one per component)

**Per Chapter:**
1. Write concept overview (2-3 paragraphs)
2. Define design principles (2-3)
3. Create basic implementation pattern
4. Create advanced pattern (if needed)
5. Document common patterns (2-4)
6. Write best practices (3-5)
7. Add integration section
8. Write troubleshooting (2-3 issues)
9. Add performance considerations
10. Link to references

**Review:** Are all code examples complete and tested?

---

### Phase 6: Implementation Guide (15% effort)

**Output:** XX-implementation-guide.md (complete)

1. Define implementation phases (3-5)
2. Write phase dependency diagram
3. For each phase:
   - Phase objective
   - Prerequisites
   - Steps (4-10 per phase)
   - Validation checklist
   - Troubleshooting
4. Document testing strategy
5. Create rollback plan
6. Define success criteria
7. Add post-implementation section

**Review:** Can someone follow this without prior knowledge?

---

### Phase 7: Deployment & Operations (10% effort)

**Output:** YY-deployment-operations.md (complete)

1. Define deployment strategy
2. Document configuration management
3. Create monitoring/alerting section
4. Define maintenance procedures
5. Document disaster recovery
6. Write troubleshooting guide
7. Add performance tuning

**Review:** Are all operational scenarios covered?

---

### Phase 8: Appendices (5% effort)

**Output:** appendices/A-D (complete)

1. **A - Code Examples:** All examples from chapters
2. **B - Cursor Rules:** Relevant rules with examples
3. **C - Official Docs:** Comprehensive links
4. **D - Implementation:** File tree (optional)

---

### Phase 9: Introduction (5% effort)

**Output:** 01-introduction.md (complete)

**Why Last:** You now understand the complete framework

1. Write purpose (2-3 paragraphs)
2. Define scope (in/out tables)
3. List prerequisites
4. Define key concepts (5-10)
5. Create best practices matrix
6. Document structure overview
7. State assumptions

**Review:** Is scope accurate? Are prerequisites complete?

---

### Phase 10: Final Review (5% effort)

**Completeness Check:**
- [ ] All required documents exist
- [ ] All required sections present
- [ ] Total length: 3,000-10,000 lines
- [ ] All code examples complete
- [ ] All diagrams clear
- [ ] All links work

**Quality Check:**
- [ ] Grammar/spelling correct
- [ ] Consistent terminology
- [ ] Code formatting consistent
- [ ] Diagrams use consistent notation
- [ ] Tables properly formatted

**Cross-Reference Check:**
- [ ] Every document links to 3+ others
- [ ] Index accurately reflects content
- [ ] Introduction references all chapters
- [ ] Architecture referenced by all chapters

---

## Quality Standards Checklist

### Documentation Completeness

**Required Documents:**
- [ ] 00-index.md (100-200 lines)
- [ ] 01-introduction.md (200-400 lines)
- [ ] 02-architecture-overview.md (400-800 lines)
- [ ] 03-XX.md core chapters (500-1000 lines each, 3-10 chapters)
- [ ] XX-implementation-guide.md (700-1200 lines)
- [ ] YY-deployment-operations.md (600-1000 lines)
- [ ] appendices/A-D (100-500 lines each)

**Total:** 3,000-10,000 lines ✓

### Code Example Standards

Every code example must:
- [ ] Be self-contained (can run without modifications)
- [ ] Have inline comments (explain key lines)
- [ ] Show input (what goes in)
- [ ] Show output (what comes out)
- [ ] Follow best practices (from cursor rules)
- [ ] Be tested (verified working)
- [ ] Use consistent formatting (language linter)
- [ ] Have context (when to use this)

### Diagram Standards

Every diagram must:
- [ ] Have a clear purpose (what it's explaining)
- [ ] Use consistent notation (same symbols throughout)
- [ ] Be readable (not cluttered)
- [ ] Have a legend (if needed)
- [ ] Flow standard direction (top-to-bottom or left-to-right)
- [ ] Be aligned (proper spacing)

---

## Example Frameworks

Study these for patterns and quality standards:

| Framework | Location | Lines | Key Learnings |
|---|---|---|---|
| **Agent** | [../../docs/agent-framework-design/](../../docs/agent-framework-design/) | ~10,000 | Multi-agent orchestration, MLflow 3.0, frontend integration |
| **Alerting** | [../../docs/alerting-framework-design/](../../docs/alerting-framework-design/) | ~8,000 | Config-driven architecture, SDK integration, hierarchical jobs |
| **Dashboard** | [../../docs/dashboard-framework-design/](../../docs/dashboard-framework-design/) | ~5,000 | Asset rationalization, variable substitution, validation |
| **Monitoring** | [../../docs/lakehouse-monitoring-design/](../../docs/lakehouse-monitoring-design/) | ~6,000 | Custom metrics, Genie integration, async patterns |
| **ML** | [../../docs/ml-framework-design/](../../docs/ml-framework-design/) | ~9,000 | Feature engineering, model registry, 70+ documented errors |
| **Semantic** | [../../docs/semantic-framework/](../../docs/semantic-framework/) | ~7,000 | TVFs, metric views, domain organization, Genie optimization |
| **Frontend** | [../../docs/frontend-framework-design/](../../docs/frontend-framework-design/) | ~12,000 | Design system, component library, complete PRD |
| **Architecture** | [../../docs/project-architecture-design/](../../docs/project-architecture-design/) | ~15,000 | Complete architecture evolution (4 versions) |

---

## Tips for Success

### Document Writing

1. **Start with Index**
   - Forces clear scope definition
   - Creates navigation structure early
   - Identifies gaps in planning

2. **Architecture Before Details**
   - Complete architecture overview first
   - Define all components
   - Document data flow clearly

3. **Test All Code**
   - Every example must run
   - Include complete code
   - Show expected output

4. **Write Introduction Last**
   - You understand the complete framework
   - Can write accurate scope
   - Can identify all prerequisites

### Code Examples

1. **Be Complete**
   - Can copy-paste and run as-is
   - No missing imports
   - No undefined variables

2. **Add Context**
   - Explain when to use this
   - Show the problem it solves
   - Link to related patterns

3. **Show Output**
   - Expected output as comment or separate block
   - Include any error messages
   - Show success indicators

### Diagrams

1. **ASCII Art for Simple Diagrams**
   - Fast to create
   - No external tools needed
   - Easy to maintain

2. **Mermaid for Complex Flows**
   - Flowcharts
   - Sequence diagrams
   - State diagrams

3. **Keep It Simple**
   - One concept per diagram
   - Clear labels
   - Consistent notation

### Quality

1. **Review Multiple Times**
   - First pass: completeness
   - Second pass: accuracy
   - Third pass: clarity
   - Fourth pass: consistency

2. **Get Feedback**
   - Technical review (accuracy)
   - User testing (clarity)
   - Link audit (references)

3. **Iterate**
   - Documentation is never "done"
   - Update as implementation evolves
   - Improve based on user feedback

---

## Common Pitfalls

### Planning Phase

❌ **Skipping Agent Domain tags** → Disorganized artifacts  
✅ **Tag every artifact** → Clear domain ownership

❌ **Planning without Gold layer** → Implementation confusion  
✅ **Reference Gold tables explicitly** → Clear data lineage

❌ **Ignoring user requirements** → Misaligned solution  
✅ **Map requirements to artifacts** → User-centric design

### Design Phase

❌ **Incomplete code examples** → Users can't follow  
✅ **Test all code** → Users succeed immediately

❌ **Skipping architecture** → Disconnected chapters  
✅ **Complete architecture first** → Cohesive documentation

❌ **No cross-references** → Navigation difficult  
✅ **Link extensively** → Easy to explore

❌ **Introduction first** → Inaccurate scope  
✅ **Introduction last** → Accurate representation

---

## References

### Cursor Rules

- [26-project-plan-methodology.mdc](../../.cursor/rules/planning/26-project-plan-methodology.mdc) - Project planning
- [27-framework-design-methodology.mdc](../../.cursor/rules/planning/27-framework-design-methodology.mdc) - Framework design
- [README.md](../../.cursor/rules/planning/README.md) - Planning rules overview

### Official Documentation

- [Databricks Documentation](https://docs.databricks.com/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial release - Framework design generation workflow |
