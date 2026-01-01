# Admin Rules for Claude Code

This file combines all admin-related cursor rules for use by Claude Code.

---

## Table of Contents
1. [Cursor Rules Structure](#cursor-rules-structure)
2. [Self-Improvement Patterns](#self-improvement-patterns)
3. [Documentation Organization](#documentation-organization)

---

## Cursor Rules Structure

### Rule File Location

Always place rule files in `PROJECT_ROOT/.cursor/rules/`:
```
.cursor/rules/
├── your-rule-name.mdc
├── another-rule.mdc
└── ...
```

### Naming Convention
- Use kebab-case for filenames
- Always use `.mdc` extension
- Make names descriptive of the rule's purpose

### Directory Structure
```
PROJECT_ROOT/
├── .cursor/
│   └── rules/
│       ├── your-rule-name.mdc
│       └── ...
└── ...
```

### Never Place Rule Files:
- In the project root
- In subdirectories outside `.cursor/rules`
- In any other location

### Rule File Structure

```markdown
---
description: Short description of the rule's purpose
globs: optional/path/pattern/**/*
alwaysApply: false
---
# Rule Title

Main content explaining the rule with markdown formatting.

1. Step-by-step instructions
2. Code examples
3. Guidelines
```

### Context7 Usage
Always use context7 when needing code generation, setup or configuration steps, or library/API documentation. Use library `/databricks` for API and docs.

---

## Self-Improvement Patterns

### Rule Improvement Triggers

- New code patterns not covered by existing rules
- Repeated similar implementations across files
- Common error patterns that could be prevented
- New libraries or tools being used consistently
- Emerging best practices in the codebase

### Analysis Process
- Compare new code with existing rules
- Identify patterns that should be standardized
- Look for references to external documentation
- Check for consistent error handling patterns
- Monitor test patterns and coverage

### Rule Updates

**Add New Rules When:**
- A new technology/pattern is used in 3+ files
- Common bugs could be prevented by a rule
- Code reviews repeatedly mention the same feedback
- New security or performance patterns emerge

**Modify Existing Rules When:**
- Better examples exist in the codebase
- Additional edge cases are discovered
- Related rules have been updated
- Implementation details have changed

### Rule Improvement Workflow

1. **Validate the Trigger**
   - Is this pattern used in 3+ places, or from official documentation?
   - Would this prevent common errors or improve quality?
   - Is there clear benefit to standardizing this pattern?

2. **Research the Pattern**
   - Find official documentation references
   - Identify examples in current codebase
   - Document benefits and trade-offs
   - Check for related patterns already in rules

3. **Update the Rule**
   - Add pattern to appropriate cursor rule file
   - Include before/after examples
   - Add to validation checklist if applicable
   - Link to official documentation
   - Use actual code examples from the project

4. **Apply to Codebase**
   - Update existing code to follow new pattern
   - Verify no linter errors introduced
   - Test that pattern works as expected

5. **Document the Improvement**
   - Create implementation guide (if complex)
   - Create quick reference (for developer use)
   - Document the improvement process itself
   - Update related documentation with references

6. **Knowledge Transfer**
   - Ensure pattern is discoverable
   - Link from main documentation
   - Add to validation checklists
   - Consider team notification if breaking change

### Rule Quality Checks
- Rules should be actionable and specific
- Examples should come from actual code
- References should be up to date
- Patterns should be consistently enforced

### Rule Deprecation
- Mark outdated patterns as deprecated
- Remove rules that no longer apply
- Update references to deprecated rules
- Document migration paths for old patterns

---

## Documentation Organization

### Root Directory Rules

**ALLOWED in Root (Only These):**
```
README.md              # Project hub with links
QUICKSTART.md          # Commands-only quick start  
CHANGELOG.md           # Version history (optional)
LICENSE                # License file (optional)
```

**NEVER Allowed in Root:**
```
*DEPLOYMENT*.md        → docs/deployment/deployment-history/YYYY-MM-DD-name.md
*CHECKLIST*.md         → docs/deployment/checklist-name.md
ISSUE*.md              → docs/troubleshooting/issue-YYYY-MM-DD-description.md
*STEPS*.md             → docs/development/roadmap.md (or delete if temporary)
*SUMMARY*.md           → docs/reference/ or merge into README.md
*GUIDE*.md             → docs/deployment/ or docs/operations/
.hidden-*.md           → docs/[appropriate-category]/
```

### Standard Documentation Structure

```
project_root/
├── README.md                          
├── QUICKSTART.md                      
├── docs/
│   ├── deployment/
│   │   ├── deployment-guide.md
│   │   ├── pre-deployment-checklist.md
│   │   ├── deployment-checklist.md
│   │   └── deployment-history/
│   │       └── YYYY-MM-DD-description.md
│   ├── troubleshooting/
│   │   ├── common-issues.md
│   │   └── issue-YYYY-MM-DD-description.md
│   ├── architecture/
│   │   └── architecture-overview.md
│   ├── operations/
│   │   ├── monitoring.md
│   │   └── runbooks/
│   ├── development/
│   │   ├── roadmap.md
│   │   └── setup.md
│   └── reference/
│       ├── configuration.md
│       └── glossary.md
└── context/
    └── prompts/
```

### Naming Rules

| Format | Use For | Example |
|--------|---------|---------|
| `kebab-case.md` | All docs | `deployment-guide.md` |
| `YYYY-MM-DD-description.md` | Historical/dated | `2025-01-15-bronze-deployment.md` |
| ❌ `PascalCase.md` | Never use | `DeploymentGuide.md` ❌ |
| ❌ `ALL_CAPS.md` | Never use | `DEPLOYMENT_GUIDE.md` ❌ |
| ❌ `snake_case.md` | Never use | `deployment_guide.md` ❌ |

### Auto-Trigger Conditions for Cleanup

Suggest cleanup when:
- Creating any `.md` file (check location first)
- User mentions: "document", "checklist", "summary", "guide", "issue", "steps"
- Root directory has >3 `.md` files (excluding README/QUICKSTART/CHANGELOG)
- See files matching patterns: `*DEPLOYMENT*`, `*CHECKLIST*`, `ISSUE*`, `*STEPS*`, `*SUMMARY*`

### Documentation Type Routing

When user says:
- "Create a deployment summary" → Suggest `docs/deployment/deployment-history/YYYY-MM-DD-summary.md`
- "Document this issue" → Suggest `docs/troubleshooting/issue-YYYY-MM-DD-brief-description.md`
- "Make a checklist" → Suggest `docs/deployment/[type]-checklist.md`
- "Write next steps" → Suggest `docs/development/roadmap.md` or "Use issue tracker instead?"

### Clear Separation

- `.cursor/rules/*.mdc` - AI behavior rules
- `context/prompts/` - Domain context for AI
- `docs/` - Human-readable documentation

