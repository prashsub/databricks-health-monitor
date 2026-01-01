# Appendix C - Official Documentation

## Databricks SQL Alerts

### Primary References

| Resource | URL |
|----------|-----|
| **SQL Alerts User Guide** | https://docs.databricks.com/aws/en/sql/user/alerts |
| **Alerts v2 API Reference** | https://docs.databricks.com/api/workspace/alertsv2/createalert |
| **Databricks SDK - Alerts V2** | https://databricks-sdk-py.readthedocs.io/en/latest/workspace/sql/alerts_v2.html |

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/2.0/alerts` | Create alert |
| `GET /api/2.0/alerts` | List alerts |
| `GET /api/2.0/alerts/{id}` | Get alert details |
| `PATCH /api/2.0/alerts/{id}` | Update alert |
| `DELETE /api/2.0/alerts/{id}` | Trash alert |

## Databricks SDK

| Resource | URL |
|----------|-----|
| **SDK Documentation** | https://databricks-sdk-py.readthedocs.io/ |
| **Installation** | https://databricks-sdk-py.readthedocs.io/en/latest/install.html |
| **Authentication** | https://databricks-sdk-py.readthedocs.io/en/latest/authentication.html |
| **Alerts V2 Module** | https://databricks-sdk-py.readthedocs.io/en/latest/workspace/sql/alerts_v2.html |

## Delta Lake

| Resource | URL |
|----------|-----|
| **Delta Lake Documentation** | https://docs.databricks.com/delta/ |
| **Time Travel** | https://docs.databricks.com/delta/history.html |
| **Change Data Feed** | https://docs.databricks.com/delta/delta-change-data-feed.html |

## Unity Catalog

| Resource | URL |
|----------|-----|
| **Unity Catalog Overview** | https://docs.databricks.com/data-governance/unity-catalog/ |
| **Table Constraints** | https://docs.databricks.com/tables/constraints.html |
| **Access Control** | https://docs.databricks.com/security/access-control/ |

## Databricks Asset Bundles

| Resource | URL |
|----------|-----|
| **Asset Bundles Overview** | https://docs.databricks.com/dev-tools/bundles/ |
| **Bundle Resources** | https://docs.databricks.com/dev-tools/bundles/resources.html |
| **Jobs Configuration** | https://docs.databricks.com/dev-tools/bundles/resources.html#jobs |

## Quartz Cron

| Resource | URL |
|----------|-----|
| **Cron Expression Format** | http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html |
| **Cron Generator** | https://www.freeformatter.com/cron-expression-generator-quartz.html |

## Related Databricks Features

| Feature | Documentation |
|---------|---------------|
| **SQL Warehouses** | https://docs.databricks.com/sql/admin/sql-endpoints.html |
| **Serverless SQL** | https://docs.databricks.com/sql/admin/serverless.html |
| **Query History** | https://docs.databricks.com/sql/admin/query-history.html |

## Internal Project Documentation

| Document | Location |
|----------|----------|
| **Phase 3.7 Plan** | [../../plans/phase3-addendum-3.7-alerting-framework.md](../../plans/phase3-addendum-3.7-alerting-framework.md) |
| **Cursor Rule** | [../../.cursor/rules/monitoring/19-sql-alerting-patterns.mdc](../../.cursor/rules/monitoring/19-sql-alerting-patterns.mdc) |
| **DAB Rule** | [../../.cursor/rules/common/02-databricks-asset-bundles.mdc](../../.cursor/rules/common/02-databricks-asset-bundles.mdc) |


