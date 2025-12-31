# Appendix C - References

## Official Databricks Documentation

### Agent Framework

| Topic | URL |
|-------|-----|
| Multi-Agent Genie | https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie |
| Stateful Agents | https://docs.databricks.com/aws/en/generative-ai/agent-framework/stateful-agents |
| Log Agent | https://docs.databricks.com/aws/en/generative-ai/agent-framework/log-agent |
| Agent Evaluation | https://docs.databricks.com/aws/en/generative-ai/agent-evaluation/ |
| Model Context Protocol (MCP) | https://docs.databricks.com/aws/en/generative-ai/mcp/ |

### MLflow 3.0 GenAI

| Topic | URL |
|-------|-----|
| MLflow GenAI Concepts | https://docs.databricks.com/aws/en/mlflow3/genai/concepts/ |
| Tracing Overview | https://docs.databricks.com/aws/en/mlflow3/genai/tracing/ |
| App Instrumentation | https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/ |
| Tracing Integrations | https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/ |
| Attach Tags to Traces | https://docs.databricks.com/aws/en/mlflow3/genai/tracing/attach-tags/ |

### MLflow Evaluation

| Topic | URL |
|-------|-----|
| Scorers Overview | https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/scorers |
| is_context_relevant Judge | https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_context_relevant |
| Align Judges | https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/align-judges |
| Create Custom Judge | https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/custom-judge/create-custom-judge |
| Synthesize Evaluation Set | https://docs.databricks.com/aws/en/generative-ai/agent-evaluation/synthesize-evaluation-set |
| Evaluation Runs | https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/evaluation-runs |
| Production Monitoring | https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/production-monitoring |

### Prompt Registry

| Topic | URL |
|-------|-----|
| Prompt Registry Overview | https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/ |
| Use Prompts in Deployed Apps | https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/use-prompts-in-deployed-apps |

### Version Tracking

| Topic | URL |
|-------|-----|
| Version Concepts | https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/version-tracking/version-concepts |
| Package App Code | https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/version-tracking/optionally-package-app-code-and-files-for-databricks-model-serving |
| Link Traces to Versions | https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/version-tracking/link-production-traces-to-app-versions |

### Model Serving

| Topic | URL |
|-------|-----|
| Model Serving Overview | https://docs.databricks.com/aws/en/machine-learning/model-serving/ |
| Serverless Compute | https://docs.databricks.com/aws/en/machine-learning/model-serving/serverless-real-time-inference |
| Inference Tables | https://docs.databricks.com/aws/en/machine-learning/model-serving/inference-tables |

### Databricks Apps

| Topic | URL |
|-------|-----|
| Apps Overview | https://docs.databricks.com/aws/en/dev-tools/databricks-apps/ |
| Create Streamlit App | https://docs.databricks.com/aws/en/dev-tools/databricks-apps/create-app |

## Example Notebooks

### Multi-Agent Systems

| Notebook | URL |
|----------|-----|
| LangGraph Multi-Agent Genie | https://docs.databricks.com/aws/en/notebooks/source/generative-ai/langgraph-multiagent-genie.html |
| DSPy Multi-Agent Genie | https://docs.databricks.com/aws/en/notebooks/source/generative-ai/dspy/dspy-multiagent-genie.html |

### Memory Storage

| Notebook | URL |
|----------|-----|
| Short-Term Memory with Lakebase | https://docs.databricks.com/aws/en/notebooks/source/generative-ai/short-term-memory-agent-lakebase.html |
| Long-Term Memory with Lakebase | https://docs.databricks.com/aws/en/notebooks/source/generative-ai/long-term-memory-agent-lakebase.html |

## LangChain/LangGraph Documentation

| Topic | URL |
|-------|-----|
| LangGraph Documentation | https://langchain-ai.github.io/langgraph/ |
| LangGraph Multi-Agent | https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/ |
| LangChain Databricks | https://python.langchain.com/docs/integrations/providers/databricks/ |
| ChatDatabricks | https://python.langchain.com/docs/integrations/chat/databricks/ |

## MLflow Documentation

| Topic | URL |
|-------|-----|
| MLflow Documentation | https://mlflow.org/docs/latest/index.html |
| MLflow LangChain | https://mlflow.org/docs/latest/llms/langchain/index.html |
| MLflow Tracing | https://mlflow.org/docs/latest/llms/tracing/index.html |
| MLflow GenAI | https://mlflow.org/docs/latest/llms/genai/index.html |

## Python Packages

| Package | Version | PyPI |
|---------|---------|------|
| mlflow | >=3.0.0 | https://pypi.org/project/mlflow/ |
| langchain | >=0.3.0 | https://pypi.org/project/langchain/ |
| langgraph | >=0.2.0 | https://pypi.org/project/langgraph/ |
| langchain-databricks | >=0.1.0 | https://pypi.org/project/langchain-databricks/ |
| databricks-sdk | >=0.30.0 | https://pypi.org/project/databricks-sdk/ |
| databricks-agents | >=0.1.0 | https://pypi.org/project/databricks-agents/ |
| pydantic | >=2.0.0 | https://pypi.org/project/pydantic/ |
| tavily-python | >=0.3.0 | https://pypi.org/project/tavily-python/ |
| streamlit | >=1.30.0 | https://pypi.org/project/streamlit/ |

## Related Project Documentation

| Document | Path |
|----------|------|
| Phase 4: Agent Framework Plan | [plans/phase4-agent-framework.md](../../../plans/phase4-agent-framework.md) |
| Phase 3.6: Genie Spaces | [plans/phase3-addendum-3.6-genie-spaces.md](../../../plans/phase3-addendum-3.6-genie-spaces.md) |
| Phase 3.5: AI/BI Dashboards | [plans/phase3-addendum-3.5-ai-bi-dashboards.md](../../../plans/phase3-addendum-3.5-ai-bi-dashboards.md) |
| Gold Layer Design | [gold_layer_design/](../../../gold_layer_design/) |
| MLflow GenAI Cursor Rule | [.cursor/rules/ml/28-mlflow-genai-patterns.mdc](../../../.cursor/rules/ml/28-mlflow-genai-patterns.mdc) |

## API References

### Genie API

```python
from databricks.sdk.service.dashboards import GenieAPI

# Key methods
genie.start_conversation(space_id, content)
genie.create_message(space_id, conversation_id, content)
genie.get_message(space_id, conversation_id, message_id)
```

### MLflow GenAI API

```python
import mlflow.genai

# Tracing
mlflow.trace(name, span_type)
mlflow.start_span(name, span_type)
mlflow.update_current_trace(tags)

# Evaluation
mlflow.genai.evaluate(model, data, scorers)
mlflow.genai.assess(inputs, outputs, scorers)

# Prompts
mlflow.genai.log_prompt(prompt, artifact_path, registered_model_name)
mlflow.genai.load_prompt(uri)

# Scorers
from mlflow.genai.scorers import Relevance, Safety, Correctness, GuidelinesAdherence

# Custom scorer
@mlflow.genai.scorer
def custom_scorer(inputs, outputs, expectations) -> Score:
    return Score(value=0.9, rationale="...")
```

### Model Registry API

```python
from mlflow import MlflowClient

client = MlflowClient()

# Register model
client.create_model_version(name, source, run_id)

# Set alias
client.set_registered_model_alias(name, alias, version)

# Get by alias
client.get_model_version_by_alias(name, alias)
```

