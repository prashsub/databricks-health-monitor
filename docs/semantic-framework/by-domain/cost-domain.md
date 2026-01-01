# Cost Domain Metric Views

The Cost Domain provides comprehensive FinOps and billing analytics for managing Databricks spend, budget tracking, and cost attribution.

## Views in This Domain

| View | Source | Primary Use Case |
|------|--------|------------------|
| `mv_cost_analytics` | `fact_usage` | Comprehensive cost analysis and trending |
| `mv_commit_tracking` | `fact_usage` | Budget tracking and forecasting |

---

## mv_cost_analytics

**Full Name**: `{catalog}.{gold_schema}.mv_cost_analytics`

### Purpose

Comprehensive cost analytics for Databricks billing and usage analysis. This is the primary metric view for all cost-related queries.

### Key Features

- **26 Dimensions** for flexible slicing and dicing
- **30 Measures** covering cost, DBUs, growth rates, and coverage metrics
- **Tag-based attribution** via custom_tags MAP column
- **Period comparisons** (WoW, MoM, MTD, YTD)

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "What is our total spend this month?" | `mtd_cost`, `total_cost` |
| "Show cost by workspace" | `total_cost` (grouped by `workspace_name`) |
| "Which SKU costs the most?" | `total_cost` (grouped by `sku_name`) |
| "Daily cost trend for last 30 days" | `total_cost` (grouped by `usage_date`) |
| "What percentage of spend is tagged?" | `tag_coverage_pct` |
| "Week-over-week cost growth?" | `week_over_week_growth_pct` |
| "Serverless vs classic cost split?" | `serverless_cost`, `serverless_ratio` |

### SQL Examples

```sql
-- Total cost by workspace (last 30 days)
SELECT 
    workspace_name,
    MEASURE(total_cost) as spend,
    MEASURE(total_dbu) as dbus,
    MEASURE(serverless_ratio) as serverless_pct
FROM mv_cost_analytics
WHERE usage_date >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY workspace_name
ORDER BY spend DESC;

-- Week-over-week growth by SKU
SELECT 
    sku_name,
    MEASURE(last_7_day_cost) as this_week,
    MEASURE(prior_7_day_cost) as last_week,
    MEASURE(week_over_week_growth_pct) as wow_growth
FROM mv_cost_analytics
GROUP BY sku_name
ORDER BY this_week DESC;

-- Tag coverage analysis
SELECT 
    tag_status,
    MEASURE(total_cost) as cost,
    MEASURE(tag_coverage_pct) as coverage
FROM mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
GROUP BY tag_status;
```

---

## mv_commit_tracking

**Full Name**: `{catalog}.{gold_schema}.mv_commit_tracking`

### Purpose

Budget and commitment tracking analytics for FinOps and finance teams. Focused on burn rate analysis and cost forecasting.

### Key Features

- **Projected monthly cost** based on MTD burn rate
- **Serverless adoption tracking**
- **Cost per DBU** (effective blended rate)
- Simpler dimension set for budget-focused analysis

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "What's our MTD spend?" | `mtd_cost` |
| "What's the projected monthly cost?" | `projected_monthly_cost` |
| "What's our daily burn rate?" | `daily_avg_cost` |
| "Cost per DBU rate?" | `cost_per_dbu` |
| "YTD spend?" | `ytd_cost` |

### SQL Examples

```sql
-- Budget tracking summary
SELECT 
    MEASURE(mtd_cost) as mtd_spend,
    MEASURE(projected_monthly_cost) as projected,
    MEASURE(daily_avg_cost) as daily_burn,
    MEASURE(ytd_cost) as ytd_total
FROM mv_commit_tracking;

-- Monthly projection by workspace
SELECT 
    workspace_name,
    MEASURE(mtd_cost) as current_spend,
    MEASURE(projected_monthly_cost) as projected,
    MEASURE(serverless_ratio) as serverless_pct
FROM mv_commit_tracking
GROUP BY workspace_name
ORDER BY projected DESC;
```

---

## When to Use Which View

| Use Case | Recommended View |
|----------|------------------|
| General cost analysis | `mv_cost_analytics` |
| Cost trending and growth | `mv_cost_analytics` |
| Tag-based chargeback | `mv_cost_analytics` |
| Budget vs actual | `mv_commit_tracking` |
| Monthly projections | `mv_commit_tracking` |
| Burn rate analysis | `mv_commit_tracking` |

## Related Resources

- [TVFs: Cost Agent TVFs](../03-cost-agent-tvfs.md)
- [Phase 3.3 Plan](../../../plans/phase3-addendum-3.3-metric-views.md)
