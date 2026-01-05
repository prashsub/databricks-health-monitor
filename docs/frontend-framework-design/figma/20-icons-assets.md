# Prompt 20: Icons & Assets Library

## 🎯 Prompt Purpose
Create a comprehensive icon library and asset collection for the Databricks Health Monitor. Uses Lucide Icons for consistency with Next.js implementation.

---

## 📦 Icon Library Overview

**Icon System:** Lucide Icons (https://lucide.dev)
**Default Size:** 20px × 20px
**Stroke Width:** 1.5px (Lucide default)
**Color:** Inherit from parent (typically text color)

### Why Lucide?
- Open source, MIT licensed
- 1400+ icons
- Consistent 24px grid design
- Tree-shakeable for Next.js
- Active maintenance

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

## 📋 Required Icons by Category

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

| Icon Name | Lucide Name | Color Usage |
|-----------|-------------|-------------|
| AlertCircle | `AlertCircle` | Critical (#DC2626) |
| AlertTriangle | `AlertTriangle` | Warning (#F59E0B) |
| Info | `Info` | Info (#077A9D) |
| CheckCircle | `CheckCircle` | Success (#10B981) |
| XCircle | `XCircle` | Error (#DC2626) |
| HelpCircle | `HelpCircle` | Help (#6B7280) |
| Clock | `Clock` | Pending, time |
| Loader | `Loader2` | Loading (animated) |
| Circle | `Circle` | Neutral status |
| CircleDot | `CircleDot` | Active/selected |
| Ban | `Ban` | Blocked, forbidden |
| Pause | `PauseCircle` | Paused |

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

Create color-coded versions for severity icons:

```
┌─────────────────────────────────────────────────────────────┐
│ STATUS ICON VARIANTS                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ AlertCircle                                                 │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│ │Critical│ │ High   │ │ Medium │ │  Low   │ │ Default│    │
│ │#DC2626 │ │#F97316 │ │#F59E0B │ │#3B82F6 │ │#6B7280 │    │
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
│                                                             │
│ CheckCircle                                                 │
│ ┌────────┐ ┌────────┐                                      │
│ │Success │ │ Default│                                      │
│ │#10B981 │ │#6B7280 │                                      │
│ └────────┘ └────────┘                                      │
│                                                             │
│ Info                                                        │
│ ┌────────┐ ┌────────┐                                      │
│ │ Brand  │ │ Default│                                      │
│ │#077A9D │ │#6B7280 │                                      │
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
│ - Primary: #077A9D (Databricks teal)                       │
│ - On dark: #FFFFFF                                          │
│ - On light: #111827                                         │
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
- Colors: Primary #077A9D, Secondary #6B7280
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
│              Body-sm, #6B7280                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Figma Make Prompt

```
Create icon library for enterprise monitoring dashboard.

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

Color variants for status:
- critical: #DC2626
- high: #F97316
- warning: #F59E0B
- low: #3B82F6
- success: #10B981
- info: #077A9D
- default: #6B7280

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
   - Font: Inter Bold 16px
   - Color variants: dark (#111827), light (#FFFFFF), brand (#077A9D)

2. Compact Logo
   - Width: 160px, Height: 32px
   - [Diamond icon] + "Health Monitor"
   - Font: Inter Bold 14px
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
- Stroke: 1.5px, #077A9D primary, #6B7280 secondary
- No fills (line art only)
- Simple geometric shapes
- Each illustration should be a component
```

---

## ✅ Verification Checklist

After running the prompt, verify:

### Icon Library
- [ ] 132 icons created total (was 89, +43 new)
- [ ] Each icon has 5 size variants (xs, sm, md, lg, xl)
- [ ] Status icons have color variants
- [ ] Icons use stroke (not fill)
- [ ] Icons are properly named and organized in 13 folders

### New Icon Categories (Super-Enhanced)
- [ ] Resolution (12 icons) - for multi-step workflows
- [ ] Evidence (10 icons) - for analysis and correlation
- [ ] Time (8 icons) - for scheduling and compare mode
- [ ] View (10 icons) - for view mode toggles
- [ ] Interaction (8 icons) - for save, pin, voice features

### Logo Assets
- [ ] Full logo (3 colors)
- [ ] Compact logo (3 colors)
- [ ] Icon only (4 sizes × 3 colors)

### Illustrations
- [ ] 7 empty state illustrations
- [ ] Consistent line art style
- [ ] 200px max dimensions
- [ ] Using brand colors

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
