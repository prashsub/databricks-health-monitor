# Design Prompts

Reusable prompts for generating complete UI/UX design systems from any codebase.

---

## 🎯 The Two-Step Process

```
Step 1: AUDIT your capabilities   →  16-capability-audit-prompt.md
Step 2: GENERATE Figma guides     →  17-figma-interface-design-prompt.md
```

**Always audit first.** Design without capability audit leads to:
- Features that don't exist in UI
- Missing capabilities not surfaced
- Rework when capabilities don't match designs

---

## 📁 Prompts

| # | Prompt | Purpose | When to Use |
|---|--------|---------|-------------|
| 16 | [Capability Audit](16-capability-audit-prompt.md) | Extract capabilities from codebase | Before any design work |
| 17 | [Figma Interface Design](17-figma-interface-design-prompt.md) | Generate complete Figma design guides | After capability audit |

---

## 🚀 Quick Start

### 1. Audit Your Capabilities (30 min)

```bash
# Open your codebase and run the audit prompt
# Output: capabilities.yaml
```

### 2. Generate Figma Guides (1 hour)

```bash
# Fill in the design prompt template with your capabilities
# Output: Complete figma/ folder with step-by-step guides
```

### 3. Design in Figma (6 weeks)

```bash
# Follow the generated guides sequentially
# Copy-paste prompts into Figma AI
```

---

## ✅ What Makes This Different

| Traditional Approach | Capability-Grounded Approach |
|---------------------|------------------------------|
| Design first, build later | Audit first, design what exists |
| Features may not be implementable | Every feature maps to real capability |
| Rework when specs don't match | Design matches implementation |
| Aspirational features in UI | Only show what's actually built |

---

## 📊 Example Output

The prompts generate a complete design system:

```
figma/
├── 00-getting-started.md      # Workflow overview
├── 01-context-setup.md        # Initial AI context
├── 02-executive-overview.md   # Home screen
├── 03-global-explorer.md      # List/browse view
├── 04-domain-pages.md         # Domain-specific pages
├── 05-detail-view.md          # Drilldown page
├── 06-chat-interface.md       # AI assistant (if agents exist)
├── 07-alert-center.md         # Alerts (if alerts exist)
├── 08-settings.md             # Settings page
├── 09-visualizations.md       # Chart patterns
└── 10-component-library.md    # All components
```

Each file contains:
- ASCII wireframe
- Copy-paste Figma AI prompt
- Component specifications
- Capability mapping
- Interaction notes

---

## 🎨 Design Philosophy

These prompts enforce:

1. **Capability-grounded** - Only surface what exists
2. **Enterprise-grade** - Matches Datadog/Grafana quality
3. **AI-native** - Built for AI-assisted design tools
4. **Iterative** - Sequential workflow, one screen at a time
5. **Complete** - Covers all states, components, tokens

---

## 📚 Based On

Lessons learned from designing the Databricks Health Monitor:
- 10 screens designed
- 110+ components
- 6-week design timeline
- Zero features without backend capability

---

**Version:** 1.0  
**Created:** January 2026

