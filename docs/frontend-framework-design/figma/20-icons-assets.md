# Prompt 20: Icons & Assets Library

## 🎯 Prompt Purpose
Create a comprehensive icon library and asset collection for the Databricks Health Monitor. Uses Lucide Icons for consistency with Next.js implementation.

---

## 📦 Icon Library Overview

### Dual Icon Strategy

**Implementation Icons:** Lucide Icons (https://lucide.dev)
- Open source, MIT licensed, React-friendly
- 1400+ icons, consistent 24px grid
- Tree-shakeable for Next.js performance
- Used for UI controls (close, menu, expand, etc.)

**Brand Icons:** Official Databricks Primary Icons
- **Location:** `context/branding/primary_icons/` (200+ icons)
- Official brand assets for Databricks-specific concepts
- Used for domain features (Data Lake, Unity Catalog, MLOps, etc.)
- SVG vectors optimized for Databricks brand consistency

### When to Use Each

| Use Case | Icon Library | Example |
|----------|--------------|---------|
| **UI Controls** | Lucide | Close (X), Menu, Search, ChevronDown, MoreHorizontal |
| **Status Indicators** | Lucide | CheckCircle, AlertTriangle, XCircle, Info |
| **Generic Actions** | Lucide | Copy, Download, Edit, Trash, Share |
| **Databricks Features** | Primary Icons | Delta Lake, Unity Catalog, MLOps, Lakehouse, Serverless |
| **Domain Concepts** | Primary Icons | Data Quality, Governance, Model Registry, Observable Metrics |
| **Platform Services** | Primary Icons | Spark Cluster, Photon, Lakeflow Pipelines, Feature Store |

### Standard Sizes
- **icon-sm:** 16px × 16px - Buttons, table cells, inline
- **icon-md:** 24px × 24px - Cards, list items, navigation (default)
- **icon-lg:** 32px × 32px - Page headers, empty states
- **icon-xl:** 48px × 48px - Hero sections, feature cards

---

## 🎨 Icon Variants to Create

For each icon, create these size variants:

| Size | Dimensions | Use Case |
|------|------------|----------|
| `xs` | 12px × 12px | Inline with small text, badges |
| `sm` | 16px × 16px | Buttons (sm), table cells, menu items |
| `md` | 20px × 20px | Default, buttons (md), nav items |
| `lg` | 24px × 24px | Headers, empty states, large buttons |
| `xl` | 32px × 32px | Feature highlights, onboarding |

---

## 🎨 Databricks Primary Icons (Brand Assets)

**Location:** `context/branding/primary_icons/`

### Key Icons for Health Monitor

**Monitoring & Observability:**
- `Observable Metrics` - Health Score, monitoring dashboards
- `Performance` - Performance domain, latency metrics
- `Cost Management` - Cost domain, spend analytics
- `Data Quality 1` / `Data Quality 2` / `Data Quality 3` - Quality scores
- `Incident Investigation` - Alert details, failed jobs
- `Runbook Playbook` - Actions, remediation guides

**Data Platform:**
- `Delta Lake` - Delta tables, lakehouse references
- `Unity Catalog` - Catalog, governance features
- `Lakeflow Pipelines` - DLT pipelines, data flows
- `Databricks Workspace` - Workspace selector, environment
- `Serverless` - Serverless compute indicators
- `Spark Cluster` - Cluster health, compute resources
- `Data Lineage` - Data flow visualizations
- `Dashboards` - BI dashboards, reporting

**ML & AI:**
- `Machine Learning` - ML domain, model overview
- `MLOps` - MLOps workflows, deployment
- `Feature Store` - Feature engineering references
- `Model Registry` - Model tracking, versioning
- `Model Training` - Training jobs, experiments
- `Auto Machine Learning` - AutoML features

**Security & Governance:**
- `Governance` - Governance domain, compliance
- `Data Security` - Security findings, access control
- `Compliance` - Regulatory compliance checks
- `Privacy` - PII detection, privacy controls
- `Enterprise Security` - Enterprise security features
- `Encryption` - Encryption indicators

**Actions & Infrastructure:**
- `Deploy` - Deployment actions, CI/CD
- `Automation` - Automated workflows
- `Scheduled Jobs` - Job scheduling
- `Webhook` - Integration webhooks
- `Cost` - Cost indicators (red coin icon)
- `Currency` - Financial metrics

### Icon Color Mapping

| Semantic | Color | Use Case |
|----------|-------|----------|
| **Default** | Navy-900 (#0B2026) | Standard, non-interactive icons |
| **Interactive** | Blue-600 (#2272B4) | Clickable icons, hover states |
| **Success** | Green-600 (#00A972) | Healthy, passing, targets met |
| **Warning** | Yellow-600 (#FFAB00) | At-risk, caution |
| **Critical** | Lava-600 (#FF3621) | Failed, critical alerts |
| **Muted** | Navy-500 (#618794) | Disabled, secondary |

---

## 📋 Lucide Icons (Implementation)

### Navigation Icons (14 icons)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| Home | `Home` | Sidebar nav - Home |
| Search | `Search` | Sidebar nav - Explorer, search inputs |
| DollarSign | `DollarSign` | Sidebar nav - Cost domain |
| Activity | `Activity` | Sidebar nav - Reliability domain |
| Zap | `Zap` | Sidebar nav - Performance domain |
| Shield | `Shield` | Sidebar nav - Governance domain |
| CheckSquare | `CheckSquare` | Sidebar nav - Quality domain |
| Bell | `Bell` | Sidebar nav - Alerts |
| MessageSquare | `MessageSquare` | Sidebar nav - Chat |
| Settings | `Settings` | Sidebar nav - Settings |
| Menu | `Menu` | Mobile menu toggle |
| ChevronLeft | `ChevronLeft` | Back navigation |
| ChevronRight | `ChevronRight` | Forward, expand |
| ChevronDown | `ChevronDown` | Dropdowns, collapse |

### Action Icons (20 icons)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| Plus | `Plus` | Create, add |
| X | `X` | Close, remove, cancel |
| Check | `Check` | Confirm, success |
| Edit | `Pencil` | Edit item |
| Trash | `Trash2` | Delete item |
| Copy | `Copy` | Copy to clipboard |
| Download | `Download` | Export, download |
| Upload | `Upload` | Import, upload |
| Share | `Share2` | Share item |
| ExternalLink | `ExternalLink` | Open in new tab |
| RefreshCw | `RefreshCw` | Refresh, sync |
| MoreHorizontal | `MoreHorizontal` | Actions menu (⋯) |
| MoreVertical | `MoreVertical` | Vertical actions menu (⋮) |
| Filter | `Filter` | Filter toggle |
| SortAsc | `ArrowUp` | Sort ascending |
| SortDesc | `ArrowDown` | Sort descending |
| Maximize | `Maximize2` | Expand view |
| Minimize | `Minimize2` | Collapse view |
| Eye | `Eye` | View, preview |
| EyeOff | `EyeOff` | Hide |

### Status & Severity Icons (12 icons)

| Icon Name | Lucide Name | Color Usage (OFFICIAL Databricks) |
|-----------|-------------|-----------------------------------|
| AlertCircle | `AlertCircle` | Critical (#FF3621 Lava-600) ✅ |
| AlertTriangle | `AlertTriangle` | Warning (#FFAB00 Yellow-600) ✅ |
| Info | `Info` | Info (#2272B4 Blue-600) ✅ |
| CheckCircle | `CheckCircle` | Success (#00A972 Green-600) ✅ |
| XCircle | `XCircle` | Error (#FF3621 Lava-600) ✅ |
| HelpCircle | `HelpCircle` | Help (#618794 Navy-500) ✅ |
| Clock | `Clock` | Pending, time (Navy-900) |
| Loader | `Loader2` | Loading (animated, Blue-600) |
| Circle | `Circle` | Neutral status (Navy-500) |
| CircleDot | `CircleDot` | Active/selected (#2272B4 Blue-600) ✅ |
| Ban | `Ban` | Blocked, forbidden (Lava-600) |
| Pause | `PauseCircle` | Paused (Navy-500) |

### Domain-Specific Icons (15 icons)

| Icon Name | Lucide Name | Domain |
|-----------|-------------|--------|
| Wallet | `Wallet` | Cost - budget |
| TrendingUp | `TrendingUp` | Cost - increase |
| TrendingDown | `TrendingDown` | Cost - decrease |
| Server | `Server` | Reliability - infrastructure |
| Database | `Database` | Reliability - data |
| HardDrive | `HardDrive` | Reliability - storage |
| Gauge | `Gauge` | Performance - metrics |
| Timer | `Timer` | Performance - latency |
| Cpu | `Cpu` | Performance - compute |
| Lock | `Lock` | Governance - security |
| Unlock | `Unlock` | Governance - access granted |
| Key | `Key` | Governance - credentials |
| FileCheck | `FileCheck` | Quality - validated |
| FileWarning | `FileWarning` | Quality - issues |
| FileX | `FileX` | Quality - failed |

### Communication Icons (8 icons)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| Mail | `Mail` | Email notifications |
| Send | `Send` | Send message |
| MessageCircle | `MessageCircle` | Comments |
| AtSign | `AtSign` | Mentions |
| Hash | `Hash` | Channels (Slack) |
| Phone | `Phone` | Phone alerts |
| Slack | Custom | Slack integration |
| Webhook | `Webhook` | Webhook integration |

### User & Team Icons (6 icons)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| User | `User` | User profile |
| Users | `Users` | Team |
| UserPlus | `UserPlus` | Add user |
| UserMinus | `UserMinus` | Remove user |
| UserCheck | `UserCheck` | Assigned to |
| Building | `Building2` | Organization |

### Chart & Data Icons (8 icons)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| BarChart | `BarChart3` | Bar chart type |
| LineChart | `LineChart` | Line chart type |
| PieChart | `PieChart` | Pie/donut chart type |
| AreaChart | `AreaChart` | Area chart type |
| Table | `Table` | Table view |
| Grid | `LayoutGrid` | Grid view |
| List | `List` | List view |
| Columns | `Columns` | Column layout |

### AI & Automation Icons (10 icons)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| Sparkles | `Sparkles` | AI-generated content |
| Bot | `Bot` | AI assistant |
| Wand | `Wand2` | Magic/auto actions |
| BrainCircuit | `BrainCircuit` | ML/Intelligence |
| Lightbulb | `Lightbulb` | Insights, suggestions |
| Target | `Target` | Recommendations |
| Brain | `Brain` | Memory panel, AI thinking |
| Hypothesis | `FlaskConical` | Root cause hypotheses |
| Regenerate | `RotateCcw` | Regenerate AI response |
| ThumbsUp | `ThumbsUp` | Positive feedback |
| ThumbsDown | `ThumbsDown` | Negative feedback |

### Resolution & Workflow Icons (12 icons - NEW)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| Play | `Play` | Execute action/step |
| StepForward | `StepForward` | Next step |
| ListChecks | `ListChecks` | Multi-step checklist |
| GitBranch | `GitBranch` | Resolution path |
| Milestone | `Milestone` | Progress milestone |
| CircleCheck | `CircleCheckBig` | Step completed |
| CircleDashed | `CircleDashed` | Step pending |
| CircleX | `CircleX` | Step skipped/failed |
| Workflow | `Workflow` | Playbook/workflow |
| BookOpen | `BookOpen` | Runbook |
| Save | `Save` | Save as playbook |
| ClipboardCheck | `ClipboardCheck` | Resolution complete |

### Evidence & Analysis Icons (10 icons - NEW)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| FileSearch | `FileSearch` | Query profile |
| Code | `Code` | SQL query |
| GitCompare | `GitCompare` | Compare/diff view |
| History | `History` | Audit history |
| Diff | `Diff` | What changed |
| Network | `Network` | Blast radius |
| Impact | `Blend` | Impact visualization |
| Link | `Link2` | Correlation |
| Unlink | `Unlink2` | No correlation |
| Evidence | `Scale` | Evidence weight |

### Time & Scheduling Icons (8 icons - NEW)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| Calendar | `Calendar` | Date picker |
| CalendarRange | `CalendarRange` | Date range picker |
| CalendarClock | `CalendarClock` | Schedule action |
| Snooze | `AlarmClockOff` | Snooze duration |
| Clock | `Clock` | Time indicator |
| Timer | `Timer` | Duration |
| Hourglass | `Hourglass` | Waiting/pending |
| ArrowLeftRight | `ArrowLeftRight` | Compare periods |

### View & Layout Icons (10 icons - NEW)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| LayoutDashboard | `LayoutDashboard` | Dashboard view |
| LayoutList | `LayoutList` | List view |
| LayoutGrid | `LayoutGrid` | Card/grid view |
| GanttChart | `GanttChart` | Timeline view |
| Kanban | `KanbanSquare` | Kanban view |
| Fullscreen | `Fullscreen` | Enter fullscreen |
| Shrink | `Shrink` | Exit fullscreen |
| PanelLeft | `PanelLeft` | Toggle left panel |
| PanelRight | `PanelRight` | Toggle right panel |
| Columns3 | `Columns3` | Three-panel layout |

### Interaction Icons (8 icons - NEW)

| Icon Name | Lucide Name | Usage |
|-----------|-------------|-------|
| Pin | `Pin` | Pin conversation/item |
| PinOff | `PinOff` | Unpin |
| Bookmark | `Bookmark` | Save to watchlist |
| BookmarkX | `BookmarkMinus` | Remove from watchlist |
| Star | `Star` | Favorite |
| StarOff | `StarOff` | Unfavorite |
| Mic | `Mic` | Voice input |
| MicOff | `MicOff` | Mute voice |

---

## 🎨 Color Variants for Status Icons

Create color-coded versions for severity icons (Official Databricks Colors):

```
┌─────────────────────────────────────────────────────────────┐
│ STATUS ICON VARIANTS (Official Databricks)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ AlertCircle                                                 │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│ │Critical│ │ High   │ │Warning │ │  Low   │ │ Default│    │
│ │Lava-600│ │Lava-500│ │Yel-600 │ │Blue-600│ │Navy-500│    │
│ │#FF3621 │ │#FF5F46 │ │#FFAB00 │ │#2272B4 │ │#618794 │    │
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
│                                                             │
│ CheckCircle                                                 │
│ ┌────────┐ ┌────────┐                                      │
│ │Success │ │ Default│                                      │
│ │Green600│ │Navy-500│                                      │
│ │#00A972 │ │#618794 │                                      │
│ └────────┘ └────────┘                                      │
│                                                             │
│ Info                                                        │
│ ┌────────┐ ┌────────┐                                      │
│ │ Brand  │ │ Default│                                      │
│ │Blue-600│ │Navy-500│                                      │
│ │#2272B4 │ │#618794 │                                      │
│ └────────┘ └────────┘                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏢 Logo & Brand Assets

### Primary Logo

```
┌─────────────────────────────────────────────────────────────┐
│ DATABRICKS HEALTH MONITOR LOGO                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Variants:                                                   │
│                                                             │
│ 1. Full Logo (horizontal)                                   │
│    ┌────────────────────────────────────────────────┐      │
│    │ [Icon] Databricks Health Monitor               │      │
│    │ Height: 32px                                   │      │
│    └────────────────────────────────────────────────┘      │
│                                                             │
│ 2. Compact Logo (icon + short name)                         │
│    ┌──────────────────────┐                                │
│    │ [Icon] Health Monitor│                                │
│    │ Height: 32px         │                                │
│    └──────────────────────┘                                │
│                                                             │
│ 3. Icon Only                                                │
│    ┌──────┐                                                │
│    │ [◇]  │ 32px, 40px, 48px variants                     │
│    └──────┘                                                │
│                                                             │
│ Colors:                                                     │
│ - Primary: #2272B4 (Blue-600 - interactive)                │
│ - On dark: #FFFFFF                                          │
│ - On light: #0B2026 (Navy-900)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Logo Icon Design

```
┌─────────────────────────────────────────────────────────────┐
│ LOGO ICON (Abstract Health/Monitor concept)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    ┌────────────────┐                                      │
│    │    ╱──────╲    │                                      │
│    │   ╱  ╱╲   ╲   │  Heartbeat/Activity line             │
│    │  │  ╱  ╲   │  │  inside Databricks-inspired          │
│    │  │ ╱    ╲  │  │  diamond shape                       │
│    │   ╲      ╱   │                                       │
│    │    ╲────╱    │                                       │
│    └────────────────┘                                      │
│                                                             │
│ Construction:                                               │
│ - Diamond shape (Databricks reference)                     │
│ - Activity line inside (health monitoring reference)       │
│ - Clean, geometric, scalable                               │
│                                                             │
│ Sizes: 16px, 24px, 32px, 40px, 48px, 64px, 128px          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🖼️ Illustrations (Empty States)

### Empty State Illustrations

Create simple, line-art style illustrations for:

| Illustration | Usage | Description |
|--------------|-------|-------------|
| NoData | Empty tables | Abstract chart with no bars/lines |
| NoResults | Search with no matches | Magnifying glass with X |
| NoAlerts | Alert center empty | Bell with checkmark |
| NoSignals | Explorer empty | Document with magnifying glass |
| Welcome | First time user | Dashboard with sparkles |
| Error | Error states | Cloud with X |
| Maintenance | System maintenance | Wrench and gear |

**Style Guidelines:**
- Line weight: 1.5px (consistent with icons)
- Max size: 200px × 200px
- Primary: #2272B4 (Blue-600)
- Secondary: #618794 (Navy-500)
- Simple, geometric shapes
- Avoid detailed illustrations

```
┌─────────────────────────────────────────────────────────────┐
│ EMPTY STATE ILLUSTRATION EXAMPLE (NoData)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              ┌──────────────────────┐                      │
│              │                      │                      │
│              │     ╱╲               │                      │
│              │    ╱  ╲   ╱╲        │  Simple line chart   │
│              │   ╱    ╲ ╱  ╲       │  outline with        │
│              │  ─      ╲    ─ ─ ─  │  dashed "no data"    │
│              │                      │  section             │
│              │  ──────────────────  │                      │
│              └──────────────────────┘                      │
│                                                             │
│              "No data available"                            │
│              Body-sm, Navy-500 (#618794)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Figma Make Prompts

### ⚠️ IMPORTANT: Hybrid Icon Workflow

**Figma Make cannot import external SVG files.** Use this hybrid approach:

1. **Figma Make** → Creates placeholder icons with correct names/sizes/colors
2. **Manual Import** → After generation, import real Databricks SVGs
3. **Replace** → Swap placeholders with actual icons

---

### PROMPT 1: Icon Component Setup + Databricks Placeholders (Run First)

```
Create icon component library with placeholder icons for Databricks Health Monitor.

PAGE: Assets/Icons

SECTION 1: DATABRICKS BRAND ICONS (Placeholders to replace later)
Create simple placeholder shapes for these Databricks-specific icons.
Each placeholder should be a labeled rectangle or simple shape that will be 
replaced with actual SVGs after generation.

Create components named:
- "db/Observable Metrics" - Diamond with pulse line inside (for Health Score)
- "db/Cost Management" - Dollar sign in circle (for Cost domain)
- "db/Cost" - Coin icon (for cost indicators)
- "db/Performance" - Speedometer/gauge (for Reliability)
- "db/Governance" - Shield with checkmark (for Governance domain)
- "db/Data Quality 1" - Checklist with star (for Quality domain)
- "db/Data Security" - Lock with shield (for Security)
- "db/Machine Learning" - Brain with nodes (for ML features)
- "db/MLOps" - Gear with brain (for MLOps)
- "db/Delta Lake" - Triangle/delta shape (for Delta tables)
- "db/Unity Catalog" - Catalog book icon (for UC)
- "db/Lakeflow Pipelines" - Flow arrows (for DLT)
- "db/Databricks Workspace" - Grid workspace (for workspace)
- "db/Serverless" - Cloud lightning (for serverless)
- "db/Spark Cluster" - Cluster nodes (for clusters)
- "db/Deploy" - Rocket/arrow up (for deploy actions)
- "db/Automation" - Gear with play (for automation)
- "db/Runbook Playbook" - Book with steps (for playbooks)
- "db/Incident Investigation" - Magnifier with alert (for incidents)
- "db/Help" - Question mark circle (for help)

Each placeholder:
- Size: 24px × 24px (md default)
- Stroke: 1.5px, #0B2026 (Navy-900)
- Simple recognizable shape
- Named with "db/" prefix for easy identification

SECTION 2: ICON COMPONENT STRUCTURE
Create a master icon component with these properties:

Property 1: size
- xs: 12px × 12px (stroke 1px)
- sm: 16px × 16px (stroke 1px)
- md: 24px × 24px (stroke 1.5px) ← DEFAULT
- lg: 32px × 32px (stroke 2px)
- xl: 48px × 48px (stroke 2px)

Property 2: color (Official Databricks)
- default: #0B2026 (Navy-900 - standard icons)
- interactive: #2272B4 (Blue-600 - clickable, links)
- success: #00A972 (Green-600 - healthy, passing)
- warning: #FFAB00 (Yellow-600 - at-risk, caution)
- critical: #FF3621 (Lava-600 - failed, errors)
- muted: #618794 (Navy-500 - disabled, secondary)
- inverse: #FFFFFF (White - on dark backgrounds)

All icons should:
- Use stroke style (not fill)
- Have stroke-linecap: round
- Have stroke-linejoin: round
- Be centered in frame
- Support color inheritance from parent
```

---

### STEP 2: Manual Icon Import (After Figma Make)

After Figma Make generates the design, manually import real icons:

**Option A: Drag and Drop**
1. Open Figma project
2. Navigate to Assets/Icons page
3. Drag SVG files from `context/branding/primary_icons/` onto canvas
4. Replace placeholder components with real icons

**Option B: Copy-Paste SVG Code**
1. Open SVG file in text editor (e.g., VS Code)
2. Copy entire SVG code
3. In Figma, press Cmd+V (Mac) or Ctrl+V (Windows)
4. SVG pastes as vector

**Option C: Figma Plugin "SVG Import"**
1. Install "Insert SVG" or "Icons8" plugin from Figma Community
2. Use plugin to batch import SVGs

**After importing, for each icon:**
1. Select imported SVG
2. Right-click → "Create Component"
3. Rename to match placeholder (e.g., "db/Observable Metrics")
4. Add size variants using Component Properties
5. Delete original placeholder

---

### PROMPT 2: Icon-to-Feature Mapping (Use When Placing Icons)

```
Apply icons to Health Monitor features using this mapping:

DOMAIN ICONS (Use Databricks Primary Icons pasted in Assets):
- Health Score / Overview: "Observable Metrics" icon, color: default
- Cost Domain: "Cost Management" icon, color: default
- Cost Indicator (red coin): "Cost" icon, color: critical when over budget
- Reliability Domain: "Performance" icon, color: default
- Governance Domain: "Governance" icon, color: default
- Data Quality Domain: "Data Quality 1" icon, color: default
- Security Alerts: "Data Security" icon, color: critical for findings
- ML/AI Features: "Machine Learning" icon, color: default
- MLOps: "MLOps" icon, color: default

PLATFORM ICONS (Use Databricks Primary Icons):
- Delta Tables: "Delta Lake" icon
- Unity Catalog: "Unity Catalog" icon
- Workspace: "Databricks Workspace" icon
- Pipelines/DLT: "Lakeflow Pipelines" icon
- Serverless: "Serverless" icon
- Clusters: "Spark Cluster" icon
- Data Lineage: "Data Lineage" icon
- Dashboards: "Dashboards" icon

ACTION ICONS (Use Databricks Primary Icons):
- Deploy/Apply: "Deploy" icon, color: interactive
- Automation: "Automation" icon, color: interactive
- Playbooks/Runbooks: "Runbook Playbook" icon, color: interactive
- Help/Documentation: "Help" icon, color: muted
- Scheduled Jobs: "Scheduled Jobs" icon, color: default
- Incident Investigation: "Incident Investigation" icon, color: critical for alerts

UI CONTROL ICONS (Use Lucide - stroke style):
- Close: X icon
- Menu: Menu icon
- Search: Search icon
- Expand/Collapse: ChevronDown, ChevronRight icons
- More options: MoreHorizontal icon
- Back: ChevronLeft icon
- Edit: Pencil icon
- Delete: Trash2 icon, color: critical
- Copy: Copy icon
- Download: Download icon
- Filter: Filter icon
- Refresh: RefreshCw icon
- External link: ExternalLink icon
```

---

### PROMPT 3: Status Indicator Icons (Apply to Status Chips/Badges)

```
Create status indicator icons with semantic colors:

SEVERITY STATUS (for alerts, signals, incidents):
- Critical: AlertCircle icon, #FF3621 (Lava-600), size: sm or md
- High: AlertTriangle icon, #FF5F46 (Lava-500), size: sm or md
- Medium/Warning: AlertTriangle icon, #FFAB00 (Yellow-600), size: sm or md
- Low/Info: Info icon, #618794 (Navy-500), size: sm or md
- Success/Resolved: CheckCircle icon, #00A972 (Green-600), size: sm or md

HEALTH STATUS (for metrics, resources):
- Healthy: CheckCircle icon, #00A972 (Green-600)
- Degraded: AlertTriangle icon, #FFAB00 (Yellow-600)
- Critical: XCircle icon, #FF3621 (Lava-600)
- Unknown: HelpCircle icon, #618794 (Navy-500)

TREND INDICATORS:
- Trending Up (positive): TrendingUp icon, #00A972 (Green-600)
- Trending Up (negative, like cost): TrendingUp icon, #FF3621 (Lava-600)
- Trending Down (positive): TrendingDown icon, #00A972 (Green-600)
- Trending Down (negative): TrendingDown icon, #FF3621 (Lava-600)
- Stable: ArrowRight icon, #618794 (Navy-500)
```

---

### PROMPT 4: Navigation Bar Icons

```
Apply icons to sidebar navigation with consistent sizing:

SIDEBAR NAVIGATION (size: md 24px, color: default, hover: interactive):
├── Home: Home icon (Lucide)
├── Explorer: Search icon (Lucide)
├── Cost: "Cost Management" Primary Icon (Databricks)
├── Reliability: Activity icon (Lucide) OR "Performance" Primary Icon
├── Performance: Zap icon (Lucide)
├── Governance: Shield icon (Lucide) OR "Governance" Primary Icon
├── Quality: CheckSquare icon (Lucide) OR "Data Quality 1" Primary Icon
├── Alerts: Bell icon (Lucide)
├── Chat: MessageSquare icon (Lucide) OR "Chat" Primary Icon
└── Settings: Settings icon (Lucide)

Icon States:
- Default: #618794 (Navy-500)
- Hover: #2272B4 (Blue-600)
- Active/Selected: #2272B4 (Blue-600) with bg #D7EDFE (Blue-200)
```

---

### PROMPT 5: Resource Topology Node Icons

```
Apply icons to Resource Topology visualization nodes:

LAYER: Data Sources (Bronze)
- Unstructured data: "Unstructured Bronze" Primary Icon, color: default
- Streaming: "Streaming" Primary Icon, color: default
- API sources: "Data Source APIs" Primary Icon, color: default

LAYER: Processing (Silver)
- Delta Lake: "Delta Lake" Primary Icon, color: default
- Pipelines: "Lakeflow Pipelines" Primary Icon, color: default
- ETL: "Data Parser Normalizer Etl Elt" Primary Icon, color: default

LAYER: Serving (Gold)
- Unity Catalog: "Unity Catalog" Primary Icon, color: default
- Data Product: "Data Product" Primary Icon, color: default
- SQL Analytics: "SQL" Primary Icon, color: default

LAYER: Applications
- Workspace: "Databricks Workspace" Primary Icon, color: default
- Dashboards: "Dashboards" Primary Icon, color: default
- ML Models: "Model Registry" Primary Icon, color: default

Node Status Colors:
- Running/Healthy: Icon color default, node border #00A972 (Green-600)
- Warning: Icon color warning, node border #FFAB00 (Yellow-600)
- Error: Icon color critical, node border #FF3621 (Lava-600)
- Disabled: Icon color muted, node border #C4CCD6 (Navy-300)
```

---

### PROMPT 6: AI/Chat Interface Icons

```
Apply icons to AI chat and assistant features:

AI ASSISTANT:
- AI Avatar: Sparkles icon (Lucide), #2272B4 (Blue-600), size: lg
- Bot indicator: Bot icon (Lucide), #2272B4 (Blue-600)
- Thinking/Loading: BrainCircuit icon with animation, #2272B4

CHAT ACTIONS:
- Send message: Send icon (Lucide), color: interactive
- Voice input: Mic icon (Lucide), color: interactive
- Regenerate: RotateCcw icon (Lucide), color: muted
- Thumbs up: ThumbsUp icon, color: success on click
- Thumbs down: ThumbsDown icon, color: critical on click
- Copy response: Copy icon, color: muted

TOOL INDICATORS (in chat responses):
- Query tool: "SQL" Primary Icon, color: interactive
- Analysis tool: "Magnify Analytics" Primary Icon, color: interactive
- Action tool: "Deploy" Primary Icon, color: warning
- Search tool: Search icon (Lucide), color: success

INSIGHT CARDS:
- Recommendation: Lightbulb icon (Lucide), #FFAB00 (Yellow-600)
- Anomaly detected: AlertCircle icon, #FF3621 (Lava-600)
- Optimization: Target icon (Lucide), #00A972 (Green-600)
- Prediction: "Prediction" Primary Icon, #2272B4 (Blue-600)
```

---

### PROMPT 7: Icon Quick Reference Table

```
Create icon placement reference card showing:

┌──────────────────────────────────────────────────────────────────┐
│ ICON SIZE GUIDE                                                  │
├──────────────────┬───────────────────────────────────────────────┤
│ Size   │ Pixels  │ Usage                                         │
├────────┼─────────┼───────────────────────────────────────────────┤
│ xs     │ 12px    │ Inline with small text, badge icons           │
│ sm     │ 16px    │ Buttons (sm), table cells, chips              │
│ md     │ 24px    │ Default, nav, cards, buttons (md)             │
│ lg     │ 32px    │ Page headers, feature highlights              │
│ xl     │ 48px    │ Hero sections, empty states                   │
└────────┴─────────┴───────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ ICON COLOR GUIDE (Official Databricks)                           │
├──────────────────┬───────────────────────────────────────────────┤
│ Semantic         │ Hex         │ When to Use                     │
├──────────────────┼─────────────┼─────────────────────────────────┤
│ default          │ #0B2026     │ Non-interactive, labels         │
│ interactive      │ #2272B4     │ Clickable, links, actions       │
│ success          │ #00A972     │ Healthy, passed, positive       │
│ warning          │ #FFAB00     │ At-risk, needs attention        │
│ critical         │ #FF3621     │ Failed, errors, urgent          │
│ muted            │ #618794     │ Disabled, secondary, hints      │
│ inverse          │ #FFFFFF     │ On dark backgrounds             │
└──────────────────┴─────────────┴─────────────────────────────────┘
```

---

### PROMPT 8: Lucide Icon Library Creation (For UI Controls)

PAGE: Assets/Icons

ICON ORGANIZATION:
Create icon components organized in folders:
- Navigation (14 icons)
- Actions (20 icons)
- Status (12 icons)
- Domain (15 icons)
- Communication (8 icons)
- User (6 icons)
- Charts (8 icons)
- AI (11 icons)
- Resolution (12 icons) - NEW
- Evidence (10 icons) - NEW
- Time (8 icons) - NEW
- View (10 icons) - NEW
- Interaction (8 icons) - NEW

ICON COMPONENT STRUCTURE:
For each icon, create a component with these variants:

Property: size
Values: xs (12px), sm (16px), md (20px), lg (24px), xl (32px)

Each icon should:
- Be a single frame with the icon centered
- Use stroke for the icon (not fill, following Lucide style)
- Stroke width: 1.5px for md/lg, 1px for sm/xs, 2px for xl
- Color: currentColor (inherits from parent)

NAVIGATION ICONS (Create these from Lucide):
Home, Search, DollarSign, Activity, Zap, Shield, CheckSquare, Bell, MessageSquare, Settings, Menu, ChevronLeft, ChevronRight, ChevronDown

ACTION ICONS (Create these from Lucide):
Plus, X, Check, Pencil, Trash2, Copy, Download, Upload, Share2, ExternalLink, RefreshCw, MoreHorizontal, MoreVertical, Filter, ArrowUp, ArrowDown, Maximize2, Minimize2, Eye, EyeOff

STATUS ICONS (Create these from Lucide, with color variants):
AlertCircle (5 colors), AlertTriangle (5 colors), Info (2 colors), CheckCircle (2 colors), XCircle, HelpCircle, Clock, Loader2, Circle, CircleDot, Ban, PauseCircle

Color variants for status (Official Databricks):
- critical: #FF3621 (Lava-600)
- high: #FF5F46 (Lava-500)
- warning: #FFAB00 (Yellow-600)
- low: #2272B4 (Blue-600)
- success: #00A972 (Green-600)
- info: #2272B4 (Blue-600)
- default: #618794 (Navy-500)

DOMAIN ICONS (Create these from Lucide):
Wallet, TrendingUp, TrendingDown, Server, Database, HardDrive, Gauge, Timer, Cpu, Lock, Unlock, Key, FileCheck, FileWarning, FileX

COMMUNICATION ICONS:
Mail, Send, MessageCircle, AtSign, Hash, Phone, Webhook

USER ICONS:
User, Users, UserPlus, UserMinus, UserCheck, Building2

CHART ICONS:
BarChart3, LineChart, PieChart, AreaChart, Table, LayoutGrid, List, Columns

AI ICONS:
Sparkles, Bot, Wand2, BrainCircuit, Lightbulb, Target, Brain, FlaskConical, RotateCcw, ThumbsUp, ThumbsDown

RESOLUTION ICONS (NEW):
Play, StepForward, ListChecks, GitBranch, Milestone, CircleCheckBig, CircleDashed, CircleX, Workflow, BookOpen, Save, ClipboardCheck

EVIDENCE ICONS (NEW):
FileSearch, Code, GitCompare, History, Diff, Network, Blend, Link2, Unlink2, Scale

TIME ICONS (NEW):
Calendar, CalendarRange, CalendarClock, AlarmClockOff, Clock, Timer, Hourglass, ArrowLeftRight

VIEW ICONS (NEW):
LayoutDashboard, LayoutList, LayoutGrid, GanttChart, KanbanSquare, Fullscreen, Shrink, PanelLeft, PanelRight, Columns3

INTERACTION ICONS (NEW):
Pin, PinOff, Bookmark, BookmarkMinus, Star, StarOff, Mic, MicOff

---

PAGE: Assets/Logos

LOGO VARIANTS:
1. Full Logo
   - Width: 240px, Height: 32px
   - [Diamond icon] + "Databricks Health Monitor"
   - Font: DM Sans Bold 16px ✅
   - Color variants: dark (#0B2026 Navy-900), light (#FFFFFF), brand (#2272B4 Blue-600)

2. Compact Logo
   - Width: 160px, Height: 32px
   - [Diamond icon] + "Health Monitor"
   - Font: DM Sans Bold 14px ✅
   - Same color variants

3. Icon Only
   - Sizes: 24px, 32px, 40px, 48px
   - Diamond shape with activity line inside
   - Color variants: brand, dark, light

---

PAGE: Assets/Illustrations

EMPTY STATE ILLUSTRATIONS:
Create 7 simple line illustrations (200px × 200px max):

1. NoData - Chart outline with dashed line
2. NoResults - Magnifying glass with X
3. NoAlerts - Bell with checkmark
4. NoSignals - Document with magnifying glass
5. Welcome - Dashboard with sparkles
6. Error - Cloud with X
7. Maintenance - Wrench and gear

Style:
- Stroke: 1.5px
- Primary color: #2272B4 (Blue-600)
- Secondary color: #618794 (Navy-500)
- No fills (line art only)
- Simple geometric shapes
- Each illustration should be a component
```

---

## ✅ Verification Checklist

After running the prompts, verify:

### Prompt Execution Order
1. [ ] **PROMPT 1:** Icon Component Setup (created size/color variants)
2. [ ] **Import:** Paste Databricks Primary Icons from `context/branding/primary_icons/`
3. [ ] **PROMPT 2:** Icon-to-Feature Mapping (applied to domains, platform, actions)
4. [ ] **PROMPT 3:** Status Indicator Icons (applied to alerts, health badges)
5. [ ] **PROMPT 4:** Navigation Bar Icons (sidebar complete)
6. [ ] **PROMPT 5:** Resource Topology Node Icons (if using topology)
7. [ ] **PROMPT 6:** AI/Chat Interface Icons (chat features complete)
8. [ ] **PROMPT 7:** Quick Reference Table (for developer handoff)
9. [ ] **PROMPT 8:** Lucide Icon Library (UI controls complete)

### Icon Colors Applied (Official Databricks)
- [ ] Default icons use: #0B2026 (Navy-900)
- [ ] Interactive icons use: #2272B4 (Blue-600)
- [ ] Success icons use: #00A972 (Green-600)
- [ ] Warning icons use: #FFAB00 (Yellow-600)
- [ ] Critical icons use: #FF3621 (Lava-600)
- [ ] Muted icons use: #618794 (Navy-500)

### Icon Sizes Applied
- [ ] xs (12px) for inline badges
- [ ] sm (16px) for buttons/table cells
- [ ] md (24px) for navigation/cards (default)
- [ ] lg (32px) for headers
- [ ] xl (48px) for hero/empty states

### Databricks Primary Icons Imported
- [ ] Observable Metrics (Health Score)
- [ ] Cost Management (Cost Domain)
- [ ] Performance (Reliability)
- [ ] Governance (Governance Domain)
- [ ] Data Quality 1 (Quality Domain)
- [ ] Data Security (Security Findings)
- [ ] Delta Lake, Unity Catalog, Lakeflow Pipelines
- [ ] Deploy, Automation, Runbook Playbook
- [ ] Machine Learning, MLOps, Model Registry

### Logo Assets
- [ ] Full logo (3 colors: dark, light, brand)
- [ ] Compact logo (3 colors)
- [ ] Icon only (4 sizes × 3 colors)

### Illustrations
- [ ] 7 empty state illustrations
- [ ] Consistent line art style
- [ ] 200px max dimensions
- [ ] Using brand colors (#2272B4 Blue-600, #618794 Navy-500)

### Component Structure
- [ ] All assets are components (not just groups)
- [ ] Proper variant naming (`size=md`, `color=critical`)
- [ ] Auto Layout where applicable

---

## 📍 Icon Usage Reference

Quick reference for which icons to use where:

| Location | Icons Used |
|----------|------------|
| **Sidebar Nav** | Home, Search, DollarSign, Activity, Zap, Shield, CheckSquare, Bell, MessageSquare, Settings |
| **Top Bar** | Search, Bell, User, ChevronDown, ArrowLeftRight (compare), Calendar |
| **Buttons** | Plus, Check, X, Download, Upload, RefreshCw, Play, Save |
| **Tables** | MoreHorizontal, ChevronDown, ArrowUp, ArrowDown, Eye, Trash2, Bookmark |
| **Status** | AlertCircle, CheckCircle, Clock, Info, CircleCheckBig, CircleDashed, CircleX |
| **Cards** | TrendingUp, TrendingDown, AlertTriangle, Sparkles |
| **Forms** | Check, X, Eye, EyeOff |
| **AI Features** | Sparkles, Bot, Lightbulb, Target, Brain, ThumbsUp, ThumbsDown, RotateCcw |
| **Resolution Path** | ListChecks, CircleCheckBig, Play, GitBranch, Workflow, ClipboardCheck |
| **Evidence Section** | FileSearch, Code, GitCompare, Diff, Network, Scale, Link2 |
| **Compare Mode** | ArrowLeftRight, CalendarRange, History, Diff |
| **Chat Interface** | Mic, Pin, Bookmark, Star, Send, MessageCircle, RotateCcw |
| **View Toggles** | LayoutDashboard, LayoutList, LayoutGrid, GanttChart, Columns3 |
| **Panel Controls** | PanelLeft, PanelRight, Fullscreen, Shrink, ChevronLeft, ChevronRight |

---

## 🔗 Lucide Icon Installation (for Development)

```bash
# Install Lucide React
npm install lucide-react

# Usage in Next.js
import { Home, DollarSign, Activity } from 'lucide-react';

<Home className="w-5 h-5" />  // 20px
<Home className="w-4 h-4" />  // 16px
<Home className="w-6 h-6" />  // 24px
```

This ensures 1:1 parity between Figma icons and code implementation.
