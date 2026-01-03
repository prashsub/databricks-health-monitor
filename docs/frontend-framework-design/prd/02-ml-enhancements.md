# 09a - Frontend PRD: ML & Metrics Enhancements

**Document Type:** PRD Enhancement - ML Visualizations & Advanced Metrics  
**Version:** 2.0  
**Last Updated:** January 2026  
**Status:** Ready for Figma Design

---

## Overview

This document **enhances** the base Frontend PRD ([09-frontend-prd.md](09-frontend-prd.md)) with:
- **ML prediction visualizations** (25 models integrated)
- **Advanced metric displays** (277 total measurements)
- **2 additional pages** (Data Quality Center, ML Intelligence)
- **20+ new components** for ML/anomaly displays

**Integration:** This enhancement adds **140 pages** to the base 150-page PRD for a **total of 290 pages**.

---

## Table of Contents

1. [Enhanced Information Architecture](#enhanced-information-architecture)
2. [ML Visualization Patterns](#ml-visualization-patterns)
3. [Page 7: Data Quality Center](#page-7-data-quality-center)
4. [Page 8: ML Intelligence](#page-8-ml-intelligence)
5. [Enhanced Dashboard Hub (ML Widgets)](#enhanced-dashboard-hub-ml-widgets)
6. [Advanced Component Library](#advanced-component-library)
7. [Metric Display Patterns (277 Measurements)](#metric-display-patterns-277-measurements)
8. [ML Model Integration Patterns](#ml-model-integration-patterns)

---

## Enhanced Information Architecture

### Updated Site Map

```
Health Monitor
├── Dashboard Hub (enhanced with ML widgets)
├── Chat Interface (with ML agent responses)
├── Cost Center (+ ML anomaly detection)
├── Job Operations (+ failure predictions)
├── Security Center (+ threat scoring)
├── ⭐ Data Quality Center (NEW)
├── ⭐ ML Intelligence (NEW)
└── Settings
```

### Navigation Enhancement

**Top Navigation - Enhanced:**
- Add "Quality" and "ML" to domain centers dropdown
- Add ML prediction badge (number of active anomalies)
- Add "Insights" button (ML-generated recommendations)

---

## ML Visualization Patterns

### Core ML Display Patterns

#### Pattern 1: Anomaly Score Display

**Purpose:** Show ML-detected anomalies with confidence scores

```
┌─────────────────────────────────────────────────────┐
│ 💰 Cost Anomaly Detected                   [🔕 Dismiss] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌────────────────────────────────────────────┐    │
│  │           Anomaly Score: -0.73             │    │
│  │                                            │    │
│  │  Normal ◄──────●────────────────► Anomaly │    │
│  │  (0.0)       -0.73            (-1.0)      │    │
│  │                                            │    │
│  │  ████████████████░░░░░░░░░░ 73% Anomalous │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│  Details:                                           │
│  • Detected: Today at 10:30 AM                     │
│  • Magnitude: $2,340 above baseline (+45%)         │
│  • Model: cost_anomaly_detector v2.1               │
│  • Confidence: HIGH (87%)                          │
│                                                     │
│  Root Cause Analysis (ML):                          │
│  ✓ GPU training job in ml-workspace                │
│  ✓ Ran for 12 hours on g5.12xlarge                │
│  ✓ Previous cost: $1,200/day → Today: $3,540      │
│                                                     │
│  [View Details] [Investigate in Chat]              │
└─────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Anomaly Score Slider**: Horizontal slider showing position on 0 to -1 scale
- **Progress Bar**: Visual fill showing percentage (red gradient)
- **Confidence Badge**: HIGH/MEDIUM/LOW with color (green/yellow/red)
- **Root Cause Box**: Bullet points with checkmarks
- **Action Buttons**: Primary (View Details) + Secondary (Investigate)

**Color Coding:**
```css
/* Anomaly Score Colors */
--anomaly-none:     #10B981  /* score >= -0.3 */
--anomaly-low:      #F59E0B  /* score -0.3 to -0.5 */
--anomaly-medium:   #EF4444  /* score -0.5 to -0.7 */
--anomaly-high:     #DC2626  /* score < -0.7 */
--anomaly-critical: #991B1B  /* score < -0.9 */
```

---

#### Pattern 2: Prediction Display with Confidence Intervals

**Purpose:** Show ML forecasts with uncertainty bounds

```
┌─────────────────────────────────────────────────────────┐
│  Cost Forecast (Next 30 Days)                          │
│                                                         │
│  Predicted Monthly Cost: $52,300 ± $3,200              │
│                                                         │
│  $60K ┤                                                 │
│       │                            ╱─────────────       │
│  $55K ┤                      ╱────╱                     │
│       │                ╱────╱  Predicted                │
│  $50K ┤          ╱────╱       $52.3K                    │
│       │    ╱────╱                                       │
│  $45K ┤───╱                                             │
│       │  │                                              │
│  $40K ┤  │ Historical                                   │
│       └──┴────────────────────────────────────────►    │
│         Jan 1  Jan 15  Jan 30  Feb 14  Feb 28          │
│                                                         │
│  ━━━ Historical  ━━━ Predicted  ░░░ Confidence (95%)   │
│                                                         │
│  ML Model: budget_forecaster v1.3                      │
│  Confidence Level: 95% interval                         │
│  Last Updated: 2 minutes ago                            │
│                                                         │
│  ⚠️  Budget Alert: 85% probability of exceeding        │
│     $50K target by month end                            │
│                                                         │
│  [View Full Report] [Adjust Budget] [Ask Agent]        │
└─────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Forecast Line**: Dotted line extending from historical
- **Confidence Band**: Shaded area (light gradient) showing ±1σ or ±2σ
- **Prediction Value**: Large text with ± notation
- **Alert Box**: Warning banner if threshold exceeded
- **Model Attribution**: Small text showing model name and version

---

#### Pattern 3: Risk Score Visualization

**Purpose:** Display 1-5 risk levels with context

```
┌──────────────────────────────────────────────────────┐
│  User Risk Assessment: user@company.com              │
├──────────────────────────────────────────────────────┤
│                                                      │
│             Risk Level: 4 / 5                        │
│                                                      │
│          ●────●────●────●────○                       │
│          LOW      MEDIUM    HIGH    CRITICAL         │
│                            ▲                         │
│                            │                         │
│                       Current Risk                   │
│                                                      │
│  Risk Factors:                                       │
│  🔴 HIGH    After-hours access (12 events)          │
│  🟡 MEDIUM  Failed auth attempts (3)                │
│  🟢 LOW     Permission changes (1)                  │
│  🟢 LOW     Data export volume                      │
│                                                      │
│  ML Model: compliance_risk_classifier v2.0          │
│  Confidence: 91%                                     │
│                                                      │
│  Recommended Actions:                                │
│  1. Review after-hours access patterns              │
│  2. Enable 2FA for this user                        │
│  3. Schedule security audit                         │
│                                                      │
│  [View Full Profile] [Contact User] [Set Alert]     │
└──────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Risk Slider**: 5-point scale with filled/unfilled dots
- **Risk Factors List**: Expandable accordion with severity icons
- **Action List**: Numbered recommendations (clickable)
- **Confidence Badge**: Percentage with color coding

**Risk Level Colors:**
```css
--risk-1-low:      #10B981  /* Green */
--risk-2-elevated: #3B82F6  /* Blue */
--risk-3-medium:   #F59E0B  /* Amber */
--risk-4-high:     #EF4444  /* Red */
--risk-5-critical: #DC2626  /* Dark Red */
```

---

#### Pattern 4: Prediction Probability Display

**Purpose:** Show likelihood of future events

```
┌──────────────────────────────────────────────────────┐
│  Job Failure Prediction: nightly_etl                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│      Failure Probability: 73%                        │
│                                                      │
│      ████████████████████████░░░░░░░░░               │
│      0%   25%   50%   75%  100%                      │
│                          ▲                           │
│                         73%                          │
│                                                      │
│  ⚠️  HIGH RISK - Proactive action recommended       │
│                                                      │
│  Contributing Factors:                               │
│  • Historical failure rate: 35% (last 7 days)       │
│  • Similar config failures: 8 jobs                  │
│  • Upstream dependency issues: 2 detected           │
│  • Resource contention: Medium risk                 │
│                                                      │
│  ML Model: job_failure_predictor v3.1               │
│  Prediction Horizon: Next 24 hours                  │
│  Model Accuracy: 89% (on validation set)            │
│                                                      │
│  Recommended Actions:                                │
│  🔧 Check upstream data availability                │
│  🔧 Review cluster configuration                    │
│  🔧 Enable retry with exponential backoff           │
│                                                      │
│  [Schedule Manual Run] [Update Config] [Monitor]    │
└──────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Probability Bar**: Horizontal progress bar with gradient
- **Risk Banner**: Color-coded alert box
- **Contributing Factors**: Bullet list with weights
- **Recommendation Icons**: Wrench/gear icons for actions

**Probability Thresholds:**
```
0-30%:   ✅ LOW RISK (green)
31-50%:  ℹ️  MODERATE (blue)
51-70%:  ⚠️  ELEVATED (amber)
71-90%:  🔴 HIGH RISK (red)
91-100%: 🚨 CRITICAL (dark red, pulsing)
```

---

#### Pattern 5: Drift Detection Visualization

**Purpose:** Show statistical drift over time

```
┌────────────────────────────────────────────────────────────┐
│  Data Distribution Drift: fact_usage.dbus                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Drift Status: 🔴 DRIFTED (Score: 0.42)                   │
│                                                            │
│  Baseline vs Current Distribution:                          │
│                                                            │
│  Frequency                                                  │
│    ┤                                                        │
│    │    ╱‾╲              ╱‾╲                               │
│    │   ╱   ╲            ╱   ╲╲                             │
│    │  ╱     ╲          ╱      ╲╲                           │
│    │ ╱       ╲        ╱        ╲╲                          │
│    │╱         ╲      ╱          ╲╲                         │
│    └────────────────────────────────────────────► DBUs    │
│     0   500  1000 1500 2000 2500                           │
│                                                            │
│    ━━━ Baseline (Jan 1-15)  ━━━ Current (Jan 16-30)       │
│                                                            │
│  Statistical Tests:                                         │
│  • KS Test: D = 0.42 (p < 0.001) ✗ DRIFTED                │
│  • Mean Shift: +450 DBUs (+30%)                            │
│  • Std Dev Change: +120 DBUs (+15%)                        │
│  • Distribution Type: Shifted right                        │
│                                                            │
│  ML Model: data_drift_detector v1.2                        │
│  Detection Method: Kolmogorov-Smirnov Test                 │
│  Sensitivity: MEDIUM (threshold: 0.3)                      │
│                                                            │
│  Impact Assessment:                                         │
│  📊 Cost implications: +$15K/month                         │
│  ⚠️  Data quality concern: Requires investigation          │
│                                                            │
│  [View Baseline Data] [Retrain Model] [Set New Baseline]  │
└────────────────────────────────────────────────────────────┘
```

**Component Specs:**
- **Overlaid Distribution Charts**: Two curves on same axis
- **Statistical Test Results**: Table with pass/fail indicators
- **Drift Score Badge**: Circular badge with color (green/yellow/red)
- **Impact Assessment**: Color-coded consequence list

**Drift Threshold Colors:**
```css
--drift-none:   #10B981  /* score < 0.2 */
--drift-low:    #3B82F6  /* score 0.2-0.3 */
--drift-medium: #F59E0B  /* score 0.3-0.5 */
--drift-high:   #EF4444  /* score > 0.5 */
```

---

## Page 7: Data Quality Center

**Purpose:** Comprehensive data quality monitoring and governance dashboard

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  DATA QUALITY CENTER                    [Export] [Configure]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Quality Overview                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────┐│
│  │ Quality Score│  │ Fresh Tables │  │ Tables with  │  │ Tag  ││
│  │              │  │              │  │  Issues      │  │ Cov  ││
│  │   87 / 100   │  │  34 / 41     │  │      7       │  │ 92%  ││
│  │   ↓ -2 pts   │  │  ✅ 83%      │  │   ⚠️ +2      │  │ ↑+3% ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────┘│
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  🚨 ML-Detected Quality Issues               [View All →] │ │
│  │                                                            │ │
│  │  🔴 HIGH    Data drift detected in fact_usage (42%)       │ │
│  │  🟡 MEDIUM  Schema change predicted for dim_workspace     │ │
│  │  🟢 LOW     Freshness delay in silver_job_run_timeline    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────┐  ┌────────────────────────┐  │
│  │   Freshness Status (41 tbls) │  │   Drift Detection     │  │
│  │                              │  │                        │  │
│  │   📊 Stacked Bar Chart       │  │   📈 Line Chart        │  │
│  │                              │  │                        │  │
│  │   █████ Fresh (<24h): 34     │  │   Baseline  Current    │  │
│  │   ██ Stale (24-48h): 5       │  │   ─────    ─────      │  │
│  │   █ Very Stale (>48h): 2     │  │   Showing drift over   │  │
│  │                              │  │   30 days with alerts  │  │
│  └──────────────────────────────┘  └────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Table Quality Details                         [Search 🔍] │ │
│  │                                                            │ │
│  │  Table          Quality  Fresh  Drift  Issues  Actions    │ │
│  │  ─────────────────────────────────────────────────────── │ │
│  │  fact_usage      85/100  ✅     🔴    3      [Fix]       │ │
│  │  fact_job_run    92/100  ✅     ✅    0      [View]      │ │
│  │  dim_workspace   78/100  🟡     🟡    2      [Fix]       │ │
│  │  fact_audit_log  95/100  ✅     ✅    0      [View]      │ │
│  │  ...                                                      │ │
│  │                                                            │ │
│  │  [< Previous] Page 1 of 5 [Next >]                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Governance Compliance                        [View All →]│ │
│  │                                                            │ │
│  │  Documentation:  ████████████░░ 85% (35/41 tables)        │ │
│  │  Tagging:        █████████████░ 92% (38/41 tables)        │ │
│  │  Access Control: ███████████████ 100% (41/41 tables)      │ │
│  │  Lineage:        ██████████░░░░ 73% (30/41 tables)        │ │
│  │                                                            │ │
│  │  Overall Governance Score: 87.5 / 100 ✅                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Metrics Displayed (32 from inventory)

| Metric | Measurement # | Display Type |
|--------|---------------|--------------|
| **Quality Score** | #236 | Large KPI (0-100) |
| **Fresh Tables** | #230 | KPI with percentage |
| **Tables with Issues** | #235 | KPI with trend |
| **Tag Coverage** | #28 | KPI with percentage |
| **Freshness Rate** | #228 | Progress bar |
| **Staleness Rate** | #229 | Progress bar |
| **Avg Hours Since Update** | #232 | Text metric |
| **Quality Issue Rate** | #240 | Percentage |
| **Documentation Rate** | #251 | Progress bar |
| **Tagging Rate** | #252 | Progress bar |
| **Access Control Rate** | #253 | Progress bar |
| **Lineage Coverage** | #254 | Progress bar |
| **Governance Score** | #255 | Composite (0-100) |
| **Quality Drift** | #241 | Trend line |
| **Freshness Violations** | #233 | Alert count |
| **Schema Drift Count** | #239 | Alert count |

### ML-Powered Features

```
┌──────────────────────────────────────────────────────────┐
│  🤖 ML Quality Predictions                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Predicted Quality Issues (Next 7 Days):                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  dim_workspace                              78%    │ │
│  │  Schema change predicted                           │ │
│  │  Probability: HIGH (78%)                           │ │
│  │  [Prepare Migration Plan]                          │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  fact_usage                                 65%    │ │
│  │  Continued drift expected                          │ │
│  │  Probability: MEDIUM (65%)                         │ │
│  │  [Set New Baseline]                                │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ML Models Active:                                       │
│  • data_drift_detector (monitoring 41 tables)           │
│  • schema_change_predictor (12 tables flagged)         │
│  • schema_evolution_predictor (tracking patterns)       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Component Specifications

#### Quality Score Badge

```
┌─────────────────┐
│  Quality Score  │
│                 │
│      87         │  ← Large number (32px)
│    ─────        │
│     100         │  ← Small denominator (16px)
│                 │
│   ↓ -2 pts      │  ← Trend indicator
│  (from 89)      │
└─────────────────┘

Background color based on score:
- 90-100: success-500 (#10B981)
- 80-89:  info-500 (#3B82F6)
- 70-79:  warning-500 (#F59E0B)
- <70:    error-500 (#EF4444)
```

#### Freshness Status Icon

```
Icon Selection:
✅  Fresh (<24 hours)
🟡  Stale (24-48 hours)
🔴  Very Stale (>48 hours)
⚪  Unknown (no data)

Color Coding:
- success-500 for fresh
- warning-500 for stale
- error-500 for very stale
- text-tertiary for unknown
```

#### Drift Indicator

```
Drift Score → Visual:
- ✅ No Drift (<0.2)
- 🟡 Low Drift (0.2-0.3)
- 🟠 Medium Drift (0.3-0.5)
- 🔴 High Drift (>0.5)

Display as:
┌──────────────┐
│ Drift: 0.42  │  ← Numeric score
│              │
│ 🔴 DRIFTED   │  ← Status badge
└──────────────┘
```

---

## Page 8: ML Intelligence

**Purpose:** Unified view of all ML predictions, anomalies, and recommendations

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ML INTELLIGENCE DASHBOARD              [Model Health] [Retrain]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ML Activity Summary                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────┐ │
│  │ Active Models│  │  Predictions │  │  Anomalies   │  │ Rec ││
│  │              │  │  (24h)       │  │  Detected    │  │ oms ││
│  │      25      │  │   12,456     │  │      37      │  │  18 ││
│  │   ✅ All OK  │  │   ↑ +2.3K    │  │   🔴 +12     │  │ New ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  🚨 Critical ML Alerts                        [View All →] │ │
│  │                                                            │ │
│  │  🔴 CRITICAL  Job failure predicted: nightly_etl (89%)    │ │
│  │  🔴 HIGH      Cost anomaly: ml-workspace (+$2,340)        │ │
│  │  🟡 MEDIUM    Security threat detected: user@company.com  │ │
│  │  🟡 MEDIUM    Data drift: fact_usage (score: 0.42)        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────┐  ┌────────────────────────┐  │
│  │   Anomaly Detection (24h)    │  │   Prediction Accuracy  │  │
│  │                              │  │                        │  │
│  │   📈 Timeline Chart          │  │   📊 Bar Chart         │  │
│  │                              │  │                        │  │
│  │   Showing anomalies by type  │  │   Model    Accuracy    │  │
│  │   Cost:     12 🔴            │  │   Job Fail   89%       │  │
│  │   Security:  8 🟡            │  │   Cost Anom  92%       │  │
│  │   Quality:   7 🟢            │  │   Sec Threat 87%       │  │
│  │   Perf:     10 🔴            │  │   Data Drift 91%       │  │
│  └──────────────────────────────┘  └────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  ML Model Catalog (25 Models)                 [Search 🔍]  │ │
│  │                                                            │ │
│  │  Model           Domain   Health  Accuracy  Last Run      │ │
│  │  ───────────────────────────────────────────────────────  │ │
│  │  job_failure     Reliab   ✅      89%      2 min ago     │ │
│  │  cost_anomaly    Cost     ✅      92%      5 min ago     │ │
│  │  security_threat Security ⚠️      87%      10 min ago    │ │
│  │  data_drift      Quality  ✅      91%      1 min ago     │ │
│  │  ...                                                      │ │
│  │                                                            │ │
│  │  [< Previous] Page 1 of 3 [Next >]                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  🎯 ML-Generated Recommendations              [View All →]│ │
│  │                                                            │ │
│  │  💰 Cost Optimization (3 recommendations)                 │ │
│  │     • Migrate 12 jobs from All-Purpose ($4.2K savings)    │ │
│  │     • Right-size ml-cluster-01 (30% utilization)          │ │
│  │     • Enable auto-scaling on 5 clusters                   │ │
│  │                                                            │ │
│  │  ⚡ Performance Optimization (2 recommendations)           │ │
│  │     • Optimize query_dashboard_kpi (P99: 12s → 3s)        │ │
│  │     • Increase warehouse size for analytics workspace     │ │
│  │                                                            │ │
│  │  🔒 Security (1 recommendation)                           │ │
│  │     • Enable 2FA for 3 high-risk users                    │ │
│  │                                                            │ │
│  │  [Export Report] [Apply All] [Schedule Review]            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### ML Model Card Pattern

```
┌──────────────────────────────────────────────────────────┐
│  job_failure_predictor                      ✅ HEALTHY   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Model Version: v3.1                                     │
│  Algorithm: XGBoost Classifier                           │
│  Domain: Reliability                                     │
│                                                          │
│  Performance Metrics:                                     │
│  • Accuracy:  89%  ████████████████████░░                │
│  • Precision: 91%  █████████████████████░                │
│  • Recall:    85%  █████████████████░░░░                │
│  • F1 Score:  88%  ████████████████████░░                │
│                                                          │
│  Inference Stats (24h):                                   │
│  • Total Predictions:  1,245                             │
│  • High Risk Flagged:  37 (3.0%)                         │
│  • Avg Latency:        87ms                              │
│  • Success Rate:       99.8%                             │
│                                                          │
│  Training Info:                                           │
│  • Last Trained:   Jan 15, 2026                          │
│  • Training Data:  30 days (12,450 runs)                 │
│  • Next Retrain:   Feb 1, 2026                           │
│                                                          │
│  Model Drift Status:                                      │
│  ✅ No significant drift detected                        │
│  Performance stable within 2σ bounds                     │
│                                                          │
│  [View Details] [Retrain Now] [View Predictions]        │
└──────────────────────────────────────────────────────────┘
```

### ML Recommendation Card Pattern

```
┌──────────────────────────────────────────────────────────┐
│  💰 Cost Optimization Recommendation                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Migrate jobs from All-Purpose to Jobs Compute           │
│                                                          │
│  Impact:                                                  │
│  • Potential Savings: $4,200/month (28%)                 │
│  • Jobs Affected:     12 workflows                       │
│  • Effort:            Medium (2-3 hours)                 │
│  • Risk:              Low                                │
│                                                          │
│  Confidence: HIGH (92%)                                   │
│  ████████████████████░░                                  │
│                                                          │
│  Affected Jobs:                                           │
│  1. nightly_etl → $850/month savings                     │
│  2. hourly_sync → $620/month savings                     │
│  3. data_quality_checks → $480/month savings             │
│  4. ... 9 more jobs                                      │
│                                                          │
│  ML Model: job_cost_optimizer v2.1                       │
│  Based On: 90-day usage patterns                         │
│                                                          │
│  Implementation Steps:                                    │
│  1. Update cluster config to "new_job_cluster"          │
│  2. Set compute type to "Jobs Compute"                  │
│  3. Enable auto-termination                             │
│  4. Test in dev environment first                       │
│                                                          │
│  [Apply Recommendation] [View Details] [Dismiss]        │
└──────────────────────────────────────────────────────────┘
```

---

## Enhanced Dashboard Hub (ML Widgets)

**Add ML-powered insights to the main Dashboard Hub**

### New Section: ML Insights

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 ML-Powered Insights                       [View All →]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────┐ │
│  │ 🔴 High Priority │  │ 💰 Cost Savings  │  │ ⚡ Perf  │ │
│  │                  │  │                  │  │  Gains   │ │
│  │   3 Critical     │  │   $12.5K/mo      │  │  45%     │ │
│  │   Alerts         │  │   Available      │  │  Possible│ │
│  │                  │  │                  │  │          │ │
│  │  [Review Now]    │  │  [View Details]  │  │ [Optimize]│
│  └──────────────────┘  └──────────────────┘  └──────────┘ │
│                                                             │
│  Active Predictions:                                        │
│  • 89% chance nightly_etl will fail tonight                │
│  • $52.3K projected cost this month (+15% from budget)     │
│  • Security threat detected: user@company.com (risk: 4/5)  │
│  • Data drift in fact_usage (score: 0.42)                  │
│                                                             │
│  [Open ML Intelligence Dashboard]                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Advanced Component Library

### Component 1: Anomaly Badge

**Purpose:** Compact anomaly indicator for tables/cards

```
Variants:

Normal:    ✅ NORMAL
Low:       🟡 ANOMALY (LOW)
Medium:    🟠 ANOMALY (MED)
High:      🔴 ANOMALY (HIGH)
Critical:  🚨 CRITICAL

Specs:
- Height: 24px
- Padding: 4px 12px
- Border-radius: 12px (pill shape)
- Font: 12px, font-semibold
- Icon + Text
```

---

### Component 2: Confidence Meter

**Purpose:** Show ML prediction confidence

```
┌──────────────────────────────┐
│ Confidence: 87%              │
│ ████████████████████░░       │
│ LOW    MEDIUM    HIGH        │
│               ▲              │
└──────────────────────────────┘

Specs:
- Width: 280px
- Height: 64px
- Progress bar with 3-zone gradient:
  - 0-50%: error-500
  - 50-75%: warning-500
  - 75-100%: success-500
- Text label above bar
- Zone markers below
```

---

### Component 3: Prediction Confidence Interval Display

**Purpose:** Show forecast with uncertainty

```
┌────────────────────────────┐
│  Predicted: $52,300        │  ← Main value (24px)
│  Range: $49,100 - $55,500  │  ← Bounds (14px, muted)
│                            │
│  ████████▓▓▓▓▓▓▓▓▓▓▓▓      │  ← Visual bar
│  ← Low    Best   High →    │
│                            │
│  95% confidence interval   │  ← Label (12px)
└────────────────────────────┘

Colors:
- Dark fill: primary-600 (predicted value)
- Light fill: primary-300 (confidence band)
```

---

### Component 4: Risk Level Indicator

**Purpose:** 1-5 risk scale display

```
┌─────────────────────────────────┐
│  Risk Level: 4 / 5              │
│                                 │
│  ●────●────●────●────○           │
│  1    2    3    4    5          │
│  LOW     MED     HIGH   CRIT    │
│                 ▲               │
│                 │               │
│           Current Risk          │
└─────────────────────────────────┘

Specs:
- Filled dots for achieved levels
- Empty dot for max level
- Color: error-500 for level 4-5
- Color: warning-500 for level 3
- Color: success-500 for level 1-2
```

---

### Component 5: ML Model Attribution Footer

**Purpose:** Show which model generated a prediction

```
┌─────────────────────────────────────────────┐
│ 🤖 Predicted by cost_anomaly_detector v2.1 │
│    Confidence: 92% | Last updated: 2m ago  │
└─────────────────────────────────────────────┘

Specs:
- Font: 11px, text-tertiary
- Icon: Robot emoji or ML icon
- Clickable (opens model details)
- Hover: underline model name
```

---

### Component 6: Actionable Recommendation Card

**Purpose:** ML-generated action item

```
┌──────────────────────────────────────────────┐
│  💡 Recommendation (HIGH Impact)             │
├──────────────────────────────────────────────┤
│                                              │
│  Enable auto-scaling on analytics cluster    │
│                                              │
│  Impact:        $850/month savings           │
│  Effort:        Low (15 minutes)             │
│  Risk:          Low                          │
│  Confidence:    89%                          │
│                                              │
│  [Apply Now] [Learn More] [Dismiss]          │
└──────────────────────────────────────────────┘

Specs:
- Border-left: 4px solid (color by priority)
- Background: bg-secondary with subtle highlight
- Actions: 3 buttons (Primary, Secondary, Ghost)
```

---

### Component 7: Timeline Anomaly Marker

**Purpose:** Show anomalies on time series charts

```
Chart with Anomaly Markers:

Value
  ┤
  │                            ⚠️ ← Anomaly marker (red)
  │                           ╱
  │              ╱─────────────
  │        ╱────╱
  │  ─────╱
  └────────────────────────────────► Time

Specs:
- Marker: Filled circle (8px) with exclamation icon
- Color: error-500 for high anomalies
- Hover: Show tooltip with details
- Click: Open anomaly detail modal
```

---

### Component 8: Drift Score Gauge

**Purpose:** Circular gauge for drift score

```
       ╭─────╮
      ╱   0.42 ╲      ← Score in center
     │   DRIFT  │
      ╲       ╱
       ╰──●──╯        ← Needle points to score
      
     0.0    0.5   1.0
     OK   DRIFT  SEVERE

Specs:
- Size: 120px × 120px
- Arc: 180° (half circle)
- Colors: Green → Yellow → Red gradient
- Needle: 2px thick line
- Center value: 20px bold
```

---

### Component 9: Prediction Timeline

**Purpose:** Show future predictions with dates

```
┌──────────────────────────────────────────────┐
│  Next 7 Days Predictions                     │
├──────────────────────────────────────────────┤
│                                              │
│  Jan 31  ✅ LOW RISK    (12% failure prob)  │
│  Feb 1   🟡 MEDIUM      (45% failure prob)  │
│  Feb 2   🔴 HIGH RISK   (78% failure prob)  │
│  Feb 3   ✅ LOW RISK    (18% failure prob)  │
│  Feb 4   ✅ LOW RISK    (9% failure prob)   │
│  Feb 5   🟡 MEDIUM      (52% failure prob)  │
│  Feb 6   ✅ LOW RISK    (15% failure prob)  │
│                                              │
│  [View Details] [Set Alert for Feb 2]       │
└──────────────────────────────────────────────┘

Specs:
- Each row: 40px height
- Icon + Date + Risk Level + Probability
- Color-coded by risk level
- Hover: Show contributing factors
```

---

### Component 10: Model Health Status

**Purpose:** Quick health indicator for ML models

```
┌─────────────────────────────────┐
│  Model Health: job_failure_pred │
│                                 │
│  ✅ HEALTHY                     │
│                                 │
│  • Accuracy: 89% (target: 85%) │
│  • Latency: 87ms (target: 200ms)│
│  • Uptime: 99.9%                │
│  • Last trained: 15 days ago    │
│                                 │
│  Next action: Retrain Feb 1     │
└─────────────────────────────────┘

Status Icons:
✅ Healthy (all metrics within bounds)
⚠️  Warning (1 metric degraded)
🔴 Unhealthy (2+ metrics degraded)
🔄 Retraining (model update in progress)
```

---

## Metric Display Patterns (277 Measurements)

### Pattern: Metric Value with Context

**Purpose:** Display any metric from inventory with full context

```
Generic Template:

┌───────────────────────────────────────┐
│  [ICON] Metric Name                   │  ← Title with domain icon
├───────────────────────────────────────┤
│                                       │
│          [VALUE]                      │  ← Main value (32px)
│          [UNIT]                       │  ← Unit (14px muted)
│                                       │
│  [TREND] vs [COMPARISON]              │  ← Trend indicator
│                                       │
│  Target: [TARGET_VALUE]               │  ← Optional target
│  Status: [STATUS_BADGE]               │  ← Optional status
│                                       │
│  [Progress bar if applicable]         │
│                                       │
│  Source: [TVF | Metric View | Custom]│  ← Data source
│  Updated: [TIME_AGO]                  │
└───────────────────────────────────────┘
```

### Example 1: Cost Metric (#1 - Total Daily Cost)

```
┌───────────────────────────────────────┐
│  💰 Total Daily Cost                  │
├───────────────────────────────────────┤
│                                       │
│         $45,230                       │
│         USD                           │
│                                       │
│  ↑ +15% vs last month                 │
│                                       │
│  Target: $40,000/day                  │
│  Status: 🟡 OVER BUDGET               │
│                                       │
│  ████████████░░░░░░ 113% of target    │
│                                       │
│  Source: mv_cost_analytics.total_cost │
│  Updated: 5 minutes ago               │
│                                       │
│  [View Breakdown] [Set Alert]         │
└───────────────────────────────────────┘
```

### Example 2: Reliability Metric (#49 - Success Rate)

```
┌───────────────────────────────────────┐
│  🔄 Job Success Rate (24h)            │
├───────────────────────────────────────┤
│                                       │
│          98.2%                        │
│          1,245 runs                   │
│                                       │
│  ↓ -0.5% vs yesterday                 │
│                                       │
│  Target: >95% (SLA)                   │
│  Status: ✅ WITHIN SLA                │
│                                       │
│  ████████████████████░ 98.2%          │
│                                       │
│  Source: mv_job_performance           │
│  Updated: Real-time                   │
│                                       │
│  [View Failed Jobs] [SLA Report]      │
└───────────────────────────────────────┘
```

### Example 3: Performance Metric (#115 - Avg Query Duration)

```
┌───────────────────────────────────────┐
│  ⚡ Avg Query Duration                │
├───────────────────────────────────────┤
│                                       │
│          2.3 sec                      │
│          P95: 8.2 sec                 │
│                                       │
│  ↑ +0.4s vs last week                 │
│                                       │
│  Target: <3s avg                      │
│  Status: ✅ WITHIN TARGET             │
│                                       │
│  ████████████████░░░░ 77% of target   │
│                                       │
│  ML Insight: 🟡 Regression detected   │
│  Query performance degrading slowly   │
│                                       │
│  Source: mv_query_performance         │
│  Updated: 1 minute ago                │
│                                       │
│  [View Slow Queries] [Optimize]       │
└───────────────────────────────────────┘
```

### Metric Status Colors

```css
/* Status Badge Colors */
--status-excellent:  #10B981  /* >100% of target (if higher is better) */
--status-good:       #3B82F6  /* 90-100% of target */
--status-warning:    #F59E0B  /* 80-90% of target */
--status-critical:   #EF4444  /* <80% of target */

/* Progress Bar Colors (match status) */
--progress-excellent: linear-gradient(90deg, #10B981, #059669)
--progress-good:      linear-gradient(90deg, #3B82F6, #2563EB)
--progress-warning:   linear-gradient(90deg, #F59E0B, #D97706)
--progress-critical:  linear-gradient(90deg, #EF4444, #DC2626)
```

---

## ML Model Integration Patterns

### 25 ML Models → UI Integration Map

| Model | Display Location | UI Pattern | Component |
|-------|------------------|------------|-----------|
| **cost_anomaly_detector** | Cost Center, Dashboard Hub | Anomaly card with score slider | Anomaly Badge + Score Display |
| **budget_forecaster** | Cost Center | Forecast chart with confidence interval | Prediction Chart + CI Band |
| **job_cost_optimizer** | Cost Center | Recommendation cards | Actionable Recommendation Card |
| **job_failure_predictor** | Job Operations, Dashboard Hub | Probability bar with factors | Prediction Probability Display |
| **job_duration_forecaster** | Job Operations | Timeline with predicted durations | Prediction Timeline |
| **sla_breach_predictor** | Job Operations | Risk gauge + countdown | Risk Level Indicator + Timer |
| **query_performance_forecaster** | (Cost Center if needed) | Performance trend projection | Forecast Line Chart |
| **warehouse_optimizer** | Cost Center, Settings | Size recommendation cards | Recommendation Card |
| **cluster_sizing_recommender** | Cost Center | Right-sizing cards with savings | Recommendation Card + Savings Badge |
| **security_threat_detector** | Security Center, Dashboard Hub | Threat score with risk factors | Risk Score Visualization |
| **access_pattern_analyzer** | Security Center | Pattern classification badges | Classification Badge |
| **compliance_risk_classifier** | Security Center | Risk level (1-5) with factors | Risk Level Indicator |
| **data_drift_detector** | Data Quality Center | Drift gauge + distribution chart | Drift Score Gauge + Overlay Chart |
| **schema_change_predictor** | Data Quality Center | Prediction timeline | Prediction Timeline |
| **cache_hit_predictor** | (Hidden - used in performance scores) | N/A (backend only) | N/A |
| **regression_detector** | Job Operations | Regression alert banner | Alert Banner with Timeline |
| **query_optimization_recommender** | (Jobs/Cost if needed) | Query optimization cards | Recommendation Card |
| **permission_recommender** | Security Center, Settings | Permission change suggestions | Recommendation Card |
| **schema_evolution_predictor** | Data Quality Center | Evolution timeline | Prediction Timeline |
| **pipeline_health_scorer** | Job Operations | Health score (0-100) with factors | Quality Score Badge |
| **retry_success_predictor** | Job Operations | Retry probability indicator | Probability Bar |
| **cluster_capacity_planner** | Cost Center | Capacity forecast chart | Forecast Chart |
| **chargeback_attribution** | Cost Center | Attribution breakdown | Stacked Bar Chart |
| **tag_recommender** | Data Quality Center | Tag suggestion cards | Recommendation Card |
| **commitment_recommender** | Cost Center | Commitment level suggestions | Recommendation Card + Savings |

---

## Chat Interface ML Enhancements

### ML-Powered Agent Responses

**Enhanced message format showing ML tool calls:**

```
┌────────────────────────────────────────────────────────────┐
│  [Cost Agent] 🤖                                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  I analyzed your cost spike using ML models.               │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  🔍 Tool: cost_anomaly_detector                      │ │
│  │  ✓  Detected anomaly (score: -0.73)                  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Key Findings:                                             │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  💰 Anomaly Detected                                 │ │
│  │                                                      │ │
│  │  Score: -0.73 (HIGH)                                 │ │
│  │  ████████████████████░░░░░ 73% anomalous             │ │
│  │                                                      │ │
│  │  Root Cause:                                         │ │
│  │  • GPU training job in ml-workspace                  │ │
│  │  • Cost: $3,540 (baseline: $1,200)                   │ │
│  │  • Duration: 12 hours                                │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  📊 Cost Breakdown (from TVF)                        │ │
│  │                                                      │ │
│  │  Workspace: ml-workspace                             │ │
│  │  SKU: Jobs Compute GPU (g5.12xlarge)                 │
│  │  DBUs: 15,680                                        │
│  │  Cost: $2,340                                        │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Recommendation:                                           │
│  Consider using smaller GPU instance or incremental       │
│  training approach to reduce cost.                        │
│                                                            │
│  [View Full Report] [Optimize Cluster] [Set Alert]        │
│                                                            │
│  2:46 PM • Model: cost_anomaly_detector v2.1               │
└────────────────────────────────────────────────────────────┘
```

### ML Tool Call Progress Indicator

```
┌────────────────────────────────────────────────────────────┐
│  [Cost Agent] 🤖                                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ⏱️ Analyzing cost spike...                               │
│                                                            │
│  ✓  Called get_daily_cost_summary()          150ms        │
│  ✓  Called cost_anomaly_detector model       230ms        │
│  ✓  Called get_workspace_cost_breakdown()    180ms        │
│  🔄  Running get_top_cost_drivers()          ...          │
│                                                            │
│  Total time: 560ms                                         │
└────────────────────────────────────────────────────────────┘
```

---

## Mobile Enhancements

### Mobile ML Card Pattern

**Compact anomaly display for mobile:**

```
┌──────────────────────────────────┐
│  🔴 Cost Anomaly                 │  ← Collapsed state
│  $3,540 (+45%)                   │
│  [Expand ▼]                      │
└──────────────────────────────────┘

[User taps to expand]

┌──────────────────────────────────┐
│  🔴 Cost Anomaly                 │  ← Expanded state
├──────────────────────────────────┤
│                                  │
│  Score: -0.73 (HIGH)             │
│  ████████████████░░░ 73%         │
│                                  │
│  ml-workspace                    │
│  $3,540 (was $1,200)             │
│  +45% from baseline              │
│                                  │
│  Root Cause:                     │
│  • GPU training job              │
│  • 12h on g5.12xlarge            │
│                                  │
│  [View] [Fix] [Dismiss]          │
│                                  │
│  [Collapse ▲]                    │
└──────────────────────────────────┘
```

---

## Enhanced Accessibility

### Screen Reader ML Patterns

```html
<!-- Anomaly Score Display -->
<div 
  role="status" 
  aria-label="Cost anomaly detected with high severity"
  aria-describedby="anomaly-details"
>
  <div aria-label="Anomaly score: negative 0.73 out of negative 1.0, indicating 73 percent anomalous">
    <!-- Visual display -->
  </div>
  <div id="anomaly-details">
    Root cause: GPU training job in ml-workspace. 
    Cost increased to $3,540 from baseline of $1,200, 
    representing a 45 percent increase.
  </div>
</div>

<!-- Prediction Probability -->
<div 
  role="status"
  aria-label="Job failure prediction"
  aria-describedby="prediction-details"
>
  <div aria-label="Failure probability: 73 percent. High risk.">
    <!-- Visual display -->
  </div>
  <div id="prediction-details">
    Job nightly_etl has a 73 percent probability of failure 
    in the next 24 hours based on machine learning model 
    job_failure_predictor version 3.1
  </div>
</div>
```

---

## Updated Figma Deliverables

### Additional Pages (2)

7. **Data Quality Center** (desktop, tablet, mobile)
   - Quality overview with 4 KPIs
   - ML-detected issues section
   - Freshness status chart
   - Drift detection chart
   - Table quality details table
   - Governance compliance section

8. **ML Intelligence** (desktop, tablet, mobile)
   - ML activity summary with 4 KPIs
   - Critical ML alerts section
   - Anomaly detection timeline
   - Prediction accuracy chart
   - ML model catalog table
   - ML-generated recommendations section

### Additional Components (20)

1. Anomaly Badge (5 variants)
2. Confidence Meter
3. Prediction Confidence Interval Display
4. Risk Level Indicator (5 levels)
5. ML Model Attribution Footer
6. Actionable Recommendation Card (3 priorities)
7. Timeline Anomaly Marker
8. Drift Score Gauge
9. Prediction Timeline (7-day view)
10. Model Health Status (4 states)
11. Anomaly Score Slider
12. ML Tool Call Progress Indicator
13. Risk Factor List (expandable)
14. Distribution Overlay Chart (for drift)
15. Forecast Chart with Confidence Band
16. Model Performance Metrics Card
17. ML Recommendation Priority Badge
18. Statistical Test Results Table
19. Mobile ML Card (collapsed/expanded)
20. Agent Response with ML Results

### Enhanced Existing Components

- **KPI Cards**: Add ML prediction indicators
- **Charts**: Add anomaly markers and forecast bands
- **Tables**: Add risk/score columns
- **Chat Messages**: Add ML tool call visualization
- **Alert Cards**: Add ML confidence scores

---

## Updated Timeline Estimate

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Design System** | 2 weeks (+1) | ML components added |
| **Desktop Pages (8)** | 3 weeks (+1) | 2 new pages added |
| **Tablet Designs (7)** | 2 weeks (+1) | 2 new pages added |
| **Mobile Designs (6)** | 2 weeks (+1) | 2 new pages added |
| **Prototypes** | 2 weeks (+1) | ML interaction flows |
| **Review & Iteration** | 1 week | ML pattern refinements |
| **Total** | **12 weeks** | **Complete + ML enhancements** |

---

## Key Enhancements Summary

### What Was Added

1. ✅ **2 New Pages**
   - Data Quality Center (32 metrics)
   - ML Intelligence (25 models)

2. ✅ **5 ML Visualization Patterns**
   - Anomaly score display
   - Prediction with confidence intervals
   - Risk score visualization
   - Prediction probability display
   - Drift detection visualization

3. ✅ **20 New Components**
   - All ML-specific UI patterns
   - Anomaly indicators
   - Prediction displays
   - Risk visualizations

4. ✅ **277 Metrics Coverage**
   - Documented display patterns for all
   - Organized by domain
   - TVF/Metric View/Custom Metric distinction

5. ✅ **25 ML Model Integration**
   - Each model mapped to UI location
   - Display patterns specified
   - Confidence/accuracy visualization

6. ✅ **Enhanced Chat Interface**
   - ML tool call progress
   - Prediction result displays
   - Confidence indicators

### Impact

- **Page Count**: 150 → 290 pages (+93%)
- **Components**: 20 → 40 (+100%)
- **Metric Coverage**: Generic → All 277 measurements
- **ML Integration**: None → Complete (25 models)
- **Design Effort**: 7 weeks → 12 weeks (+71%)

---

## References

### Internal
- [Base Frontend PRD](09-frontend-prd.md) - Foundation document
- [Metrics Inventory](../../reference/metrics-inventory.md) - 277 measurements
- [ML Framework Design](../ml-framework-design/) - Model specifications

### External
- [Anomaly Detection UI Patterns](https://www.nngroup.com/articles/anomaly-detection-interface/)
- [ML Explainability Guidelines](https://pair.withgoogle.com/chapter/explainability/)
- [Prediction Confidence Display](https://medium.com/designing-for-ai/confidence-displays-f8e4c6c7c89e)

---

**Document Version:** 2.0 (Enhancement)  
**Total PRD Pages:** 290 (Base: 150 + Enhancement: 140)  
**ML Models Integrated:** 25  
**Metrics Covered:** 277  
**Last Updated:** January 2026

