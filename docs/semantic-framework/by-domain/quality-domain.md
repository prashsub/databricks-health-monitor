# Quality Domain Metric Views

The Quality Domain provides data quality monitoring and ML-powered intelligence for identifying data freshness issues and anomalies.

## Views in This Domain

| View | Source | Primary Use Case |
|------|--------|------------------|
| `mv_data_quality` | `information_schema.tables` | Table freshness monitoring |
| `mv_ml_intelligence` | `cost_anomaly_predictions` | ML anomaly detection |

---

## mv_data_quality

**Full Name**: `{catalog}.{gold_schema}.mv_data_quality`

### Purpose

Data quality and freshness metrics for Gold layer tables. Monitors table staleness, update frequency, and domain coverage.

### Key Features

- **Freshness status** classification (FRESH, WARNING, STALE)
- **Table category** breakdown (FACT, DIMENSION, OTHER)
- **Domain inference** from naming patterns
- **Age metrics** (hours since update)
- No external dependencies (uses system `information_schema`)

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "Which tables are stale?" | Filter by `freshness_status = 'STALE'` |
| "What's the freshness rate by domain?" | `freshness_rate` grouped by `domain` |
| "How many tables were updated today?" | `fresh_tables` |
| "What's our overall data freshness?" | `freshness_rate` |
| "Fact vs dimension table counts?" | `total_tables` grouped by `table_category` |

### Freshness Classification

| Status | Threshold |
|--------|-----------|
| FRESH | Updated within 24 hours |
| WARNING | Updated 24-48 hours ago |
| STALE | Not updated in 48+ hours |

### SQL Examples

```sql
-- Freshness summary
SELECT 
    MEASURE(total_tables) as total,
    MEASURE(fresh_tables) as fresh,
    MEASURE(stale_tables) as stale,
    MEASURE(freshness_rate) as freshness_pct
FROM mv_data_quality
WHERE table_schema = 'gold';

-- Stale tables detail
SELECT 
    table_full_name,
    freshness_status,
    hours_since_update
FROM mv_data_quality
WHERE freshness_status = 'STALE'
ORDER BY hours_since_update DESC;

-- Freshness by domain
SELECT 
    domain,
    MEASURE(total_tables) as tables,
    MEASURE(freshness_rate) as freshness_pct
FROM mv_data_quality
GROUP BY domain
ORDER BY freshness_pct;

-- Table category breakdown
SELECT 
    table_category,
    MEASURE(total_tables) as count,
    MEASURE(freshness_rate) as freshness_pct
FROM mv_data_quality
GROUP BY table_category;
```

---

## mv_ml_intelligence

**Full Name**: `{catalog}.{gold_schema}.mv_ml_intelligence`

### Purpose

ML-powered intelligence metrics for anomaly detection and predictive insights. Surfaces cost anomalies detected by machine learning models.

### Prerequisites

⚠️ **Requires ML inference pipeline to run first**:

```bash
# Run ML pipeline chain
databricks bundle run -t dev ml_feature_pipeline
databricks bundle run -t dev ml_training_pipeline
databricks bundle run -t dev ml_inference_pipeline
```

### Key Features

- **Anomaly detection** with risk level classification
- **Cost correlation** (anomaly cost vs normal cost)
- **Model versioning** for tracking predictions
- **Risk level thresholds** (CRITICAL, HIGH, MEDIUM, LOW)

### Risk Level Classification

| Risk Level | Anomaly Score |
|------------|---------------|
| CRITICAL | >= 0.9 |
| HIGH | >= 0.7 |
| MEDIUM | >= 0.5 |
| LOW | < 0.5 |

### Technical Note: is_anomaly Column

The `is_anomaly` column from ML inference is **BIGINT** (not BOOLEAN). Expressions use `= 1` comparisons:

```yaml
# CORRECT
anomaly_count: SUM(CASE WHEN source.is_anomaly = 1 THEN 1 ELSE 0 END)

# WRONG (causes DATATYPE_MISMATCH error)
anomaly_count: SUM(CASE WHEN source.is_anomaly THEN 1 ELSE 0 END)
```

### Example Questions

| Question | Relevant Measures |
|----------|-------------------|
| "What anomalies were detected today?" | Filter by `prediction_date` |
| "What's the anomaly rate?" | `anomaly_rate` |
| "Show high-risk predictions" | Filter by `risk_level` |
| "Cost of anomalies?" | `anomaly_cost` |
| "Average anomaly score?" | `avg_anomaly_score` |

### SQL Examples

```sql
-- Anomaly overview
SELECT 
    MEASURE(total_predictions) as predictions,
    MEASURE(anomaly_count) as anomalies,
    MEASURE(anomaly_rate) as anomaly_pct,
    MEASURE(avg_anomaly_score) as avg_score
FROM mv_ml_intelligence;

-- Today's anomalies
SELECT 
    workspace_name,
    sku_name,
    MEASURE(anomaly_count) as anomalies,
    MEASURE(anomaly_cost) as cost_impact
FROM mv_ml_intelligence
WHERE prediction_date = CURRENT_DATE
  AND is_anomaly = 1
GROUP BY workspace_name, sku_name
ORDER BY cost_impact DESC;

-- High-risk anomalies
SELECT 
    workspace_name,
    MEASURE(high_risk_count) as high_risk,
    MEASURE(critical_count) as critical,
    MEASURE(avg_anomaly_score) as avg_score
FROM mv_ml_intelligence
WHERE risk_level IN ('CRITICAL', 'HIGH')
GROUP BY workspace_name;

-- Anomaly trend
SELECT 
    prediction_date,
    MEASURE(anomaly_count) as anomalies,
    MEASURE(anomaly_rate) as rate_pct
FROM mv_ml_intelligence
WHERE prediction_date >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY prediction_date
ORDER BY prediction_date;

-- Anomalies by SKU
SELECT 
    sku_name,
    MEASURE(anomaly_count) as anomalies,
    MEASURE(anomaly_cost) as cost_impact
FROM mv_ml_intelligence
GROUP BY sku_name
HAVING MEASURE(anomaly_count) > 0
ORDER BY cost_impact DESC;
```

---

## When to Use Which View

| Use Case | Recommended View |
|----------|------------------|
| Table freshness monitoring | `mv_data_quality` |
| Stale table detection | `mv_data_quality` |
| Domain health check | `mv_data_quality` |
| Cost anomaly detection | `mv_ml_intelligence` |
| Risk assessment | `mv_ml_intelligence` |
| Anomaly cost impact | `mv_ml_intelligence` |

## Related Resources

- [TVFs: Quality Agent TVFs](../07-quality-agent-tvfs.md)
- [ML Pipeline Architecture](../../../docs/architecture/ml-pipeline-architecture.md)
