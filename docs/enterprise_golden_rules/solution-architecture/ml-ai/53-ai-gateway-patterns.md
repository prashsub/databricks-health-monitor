# Mosaic AI Gateway Patterns

> **Document Owner:** ML Engineering | **Status:** Approved | **Last Updated:** February 2026

## Overview

AI Gateway provides governance, monitoring, and production readiness for model serving endpoints.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **ML-11** | Enable payload logging | Critical |
| **ML-12** | Configure rate limiting | Critical |
| **ML-13** | Enable AI Guardrails (external-facing) | Critical |
| **ML-14** | Usage tracking for cost | Required |
| **ML-15** | Fallbacks for LLM endpoints | Required |

---

## Feature Support Matrix

| Feature | External Model | Foundation Model | Custom Model | Agent |
|---------|---------------|------------------|--------------|-------|
| Rate Limiting | ✅ | ✅ | ✅ | ❌ |
| Payload Logging | ✅ | ✅ | ✅ | ✅ |
| AI Guardrails | ✅ | ✅ | ❌ | ❌ |
| Fallbacks | ✅ | ❌ | ❌ | ❌ |

---

## Payload Logging

```python
auto_capture_config = AutoCaptureConfigInput(
    catalog_name=catalog,
    schema_name=schema,
    table_name_prefix=endpoint_name,
    enabled=True
)
w.serving_endpoints.update_config(name=endpoint_name, auto_capture_config=auto_capture_config)
```

---

## Rate Limiting

| Endpoint Type | Limit |
|---------------|-------|
| External (GPT-4) | 50-100/min |
| Foundation | 200-500/min |
| Custom | 500-1000/min |
| Agents | 30-50/min |

---

## AI Guardrails

- **Safety Filter**: Blocks harmful content (Llama Guard)
- **PII Detection**: Credit cards, SSN, email, phone (Presidio)

```python
guardrails = AiGatewayGuardrails(
    input=AiGatewayGuardrailsInput(
        safety=AiGatewaySafetyConfig(enabled=True),
        pii=AiGatewayPiiConfig(behavior="BLOCK", categories=["CREDIT_CARD", "SSN"])
    )
)
```

---

## Usage Tracking

```sql
SELECT endpoint_name, SUM(total_token_count) AS tokens
FROM system.serving.endpoint_usage
WHERE date >= current_date() - 30
GROUP BY 1;
```

---

## Fallbacks (External Only)

```python
configure_fallbacks(
    endpoint_name="gpt4",
    fallback_endpoints=["claude", "llama"]
)
```

---

## Validation Checklist

- [ ] Payload logging enabled
- [ ] Rate limits configured
- [ ] Guardrails for external-facing
- [ ] Usage tracking active
- [ ] Fallbacks for critical endpoints

---

## References

- [AI Gateway](https://docs.databricks.com/en/ai-gateway/)
- [AI Guardrails](https://docs.databricks.com/en/ai-gateway/guardrails.html)
