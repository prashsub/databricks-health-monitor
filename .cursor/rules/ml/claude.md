# ML Rules for Claude Code

This file combines all Machine Learning cursor rules for use by Claude Code.

**Last Updated:** January 2026  
**Source:** 25 models, 43 training scripts, 100+ errors fixed across 5 domains

---

## Table of Contents
1. [MLflow and ML Models](#mlflow-and-ml-models)
2. [Feature Engineering Patterns (Jan 2026)](#feature-engineering-patterns)
3. [MLflow GenAI Patterns](#mlflow-genai-patterns)

---

## MLflow and ML Models

### Critical Rules

#### 1. Experiment Paths

```python
# ✅ CORRECT: /Shared/ path always works
experiment_name = f"/Shared/health_monitor_ml_{model_name}"
mlflow.set_experiment(experiment_name)

# ❌ WRONG: User paths may fail if subfolder doesn't exist
experiment_name = f"/Users/{user}/subfolder/experiment"  # May fail!
```

#### 2. DO NOT Define Experiments in Asset Bundles

Asset Bundles add `[dev username]` prefix, creating duplicates.

```yaml
# ❌ WRONG: Creates duplicate experiments
resources:
  experiments:
    my_experiment:
      name: "/Shared/my_experiment"

# ✅ CORRECT: Create experiments in notebook code
```

#### 3. Dataset Logging Inside Run Context

```python
# ✅ CORRECT: Inside mlflow.start_run()
with mlflow.start_run():
    mlflow.log_input(training_dataset, context="training")
    # ... training code

# ❌ WRONG: Outside run context
mlflow.log_input(training_dataset)  # Will fail!
with mlflow.start_run():
    pass
```

#### 4. Helper Functions - Always Inline

```python
# ✅ CORRECT: Inline helpers in each notebook
def setup_mlflow_experiment(model_name: str) -> str:
    """
    Inlined helper - module imports don't work in Asset Bundle notebooks.
    CRITICAL: Do not move this to a shared module!
    """
    experiment_name = f"/Shared/wanderbricks_ml_{model_name}"
    try:
        experiment = mlflow.set_experiment(experiment_name)
        print(f"✓ Experiment: {experiment_name}")
        return experiment_name
    except Exception as e:
        print(f"❌ Experiment setup failed: {e}")
        return None

# ❌ WRONG: Module imports fail in Asset Bundles
from shared.ml_helpers import setup_mlflow_experiment  # Won't work!
```

#### 5. Unity Catalog Model Signatures

```python
# ✅ CORRECT: Include both sample_input AND prediction output
sample_input = X_train.head(5)
sample_output = model.predict(sample_input)  # Include this!
signature = infer_signature(sample_input, sample_output)

mlflow.xgboost.log_model(
    model,
    artifact_path="model",
    signature=signature,
    input_example=sample_input,
    registered_model_name=f"{catalog}.{schema}.{model_name}"
)

# ❌ WRONG: Missing output in signature
signature = infer_signature(sample_input)  # Incomplete!
```

#### 6. Job Exit Signaling

```python
# ✅ CORRECT: Signal success to Asset Bundle job
dbutils.notebook.exit("SUCCESS")

# ❌ WRONG: Job status unclear
# (no exit statement)
```

### Standard Training Pipeline Structure

```python
# Databricks notebook source
import mlflow
from mlflow.models import infer_signature
import xgboost as xgb
from pyspark.sql import SparkSession

# 1. Parameters
def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    schema = dbutils.widgets.get("schema")
    model_name = dbutils.widgets.get("model_name")
    return catalog, schema, model_name

# 2. Inlined Helper
def setup_mlflow_experiment(model_name: str) -> str:
    experiment_name = f"/Shared/wanderbricks_ml_{model_name}"
    mlflow.set_experiment(experiment_name)
    return experiment_name

# 3. Main
def main():
    catalog, schema, model_name = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    # Setup experiment
    experiment_name = setup_mlflow_experiment(model_name)
    
    # Load data
    df = spark.table(f"{catalog}.{schema}.training_data").toPandas()
    X = df.drop(columns=["target"])
    y = df["target"]
    
    # Train with MLflow tracking
    with mlflow.start_run():
        # Log parameters
        mlflow.log_params({"learning_rate": 0.1, "max_depth": 6})
        
        # Train model
        model = xgb.XGBRegressor(learning_rate=0.1, max_depth=6)
        model.fit(X, y)
        
        # Log metrics
        predictions = model.predict(X)
        rmse = ((predictions - y) ** 2).mean() ** 0.5
        mlflow.log_metric("rmse", rmse)
        
        # Log model with signature
        sample_input = X.head(5)
        sample_output = model.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        mlflow.xgboost.log_model(
            model,
            artifact_path="model",
            signature=signature,
            input_example=sample_input,
            registered_model_name=f"{catalog}.{schema}.{model_name}"
        )
    
    dbutils.notebook.exit("SUCCESS")

if __name__ == "__main__":
    main()
```

### Batch Inference Type Handling

```python
# Replicate EXACT preprocessing from training
def preprocess_for_inference(df):
    """Must match training preprocessing exactly."""
    # Type conversions
    float_cols = ['feature1', 'feature2']
    for col in float_cols:
        df[col] = df[col].astype('float32')  # float64 → float32
    
    bool_cols = ['is_active', 'has_discount']
    for col in bool_cols:
        df[col] = df[col].astype('float64')  # bool → float64
    
    return df
```

### Asset Bundle ML Job Configuration

```yaml
resources:
  jobs:
    ml_training_job:
      name: "[${bundle.target}] ML Training Pipeline"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
            dependencies:
              - "xgboost>=2.0.0"
              - "mlflow>=2.10.0"
              - "scikit-learn>=1.3.0"
      
      tasks:
        - task_key: train_model
          environment_key: default
          notebook_task:
            notebook_path: ../src/ml/train_model.py
            base_parameters:
              catalog: ${var.catalog}
              schema: ${var.ml_schema}
              model_name: demand_predictor
```

### Validation Checklist

- [ ] Experiment path uses `/Shared/` prefix
- [ ] No experiments defined in Asset Bundles
- [ ] `mlflow.log_input()` inside `start_run()` context
- [ ] Helper functions inlined (not imported)
- [ ] Model signature includes both input and output
- [ ] `dbutils.notebook.exit("SUCCESS")` at end
- [ ] Type preprocessing matches training exactly

---

## Feature Engineering Patterns

### Critical Rules (Jan 2026 Update)

#### 6. Label Column Casting (CRITICAL for Unity Catalog)

```python
# ✅ CORRECT: Cast label to DOUBLE/INT in base_df BEFORE create_training_set
base_df = spark.table(feature_table).select(
    "workspace_id", 
    "usage_date",
    F.col("daily_cost").cast("double").alias("daily_cost")  # Cast here!
).distinct()

training_set = fe.create_training_set(
    df=base_df,
    feature_lookups=feature_lookups,
    label="daily_cost"  # Now DOUBLE, not DECIMAL - signature inference works!
)

# ❌ WRONG: DECIMAL label - fe.log_model() can't infer output signature
base_df = spark.table(feature_table).select(
    "workspace_id", "usage_date", "daily_cost"  # daily_cost is DECIMAL(18,2)
)
# Error: Model signature includes only inputs
```

#### 7. String Labels Must Be Encoded

```python
# ✅ CORRECT: Encode string labels to INT before training_set
tag_values = [r.tag_value for r in base_df.select("tag_value").distinct().collect()]
tag_to_id = {tag: idx for idx, tag in enumerate(sorted(tag_values))}

@F.udf(IntegerType())
def encode_tag(tag):
    return tag_to_id.get(tag, -1) if tag else -1

base_df = base_df.withColumn("tag_label", encode_tag(F.col("tag_value")))

training_set = fe.create_training_set(
    df=base_df,
    feature_lookups=feature_lookups,
    label="tag_label",  # INT, not STRING
    exclude_columns=["tag_value"]  # Exclude original string column
)

# ❌ WRONG: String labels not supported by MLflow signatures
training_set = fe.create_training_set(..., label="tag_value")  # STRING fails!
```

#### 8. Models with Runtime Features (TF-IDF)

```python
# For models with TF-IDF or other runtime-computed features,
# DON'T use fe.log_model() - use mlflow.sklearn.log_model()

# ✅ CORRECT: Explicit signature with mlflow.sklearn.log_model()
input_example = X_train.head(5).astype('float64')
sample_predictions = model.predict(input_example)
signature = infer_signature(input_example, sample_predictions)

mlflow.sklearn.log_model(
    model,
    artifact_path="model",
    input_example=input_example,
    signature=signature,
    registered_model_name=registered_name
)

# ❌ WRONG: fe.log_model() with runtime features
fe.log_model(model, training_set=training_set, ...)  # Can't infer signature!
```

#### 9. Column Name Mapping (Gold → Feature)

```python
# ✅ CORRECT: Explicit column mapping with .withColumn()
base_df = (spark.table(f"{catalog}.{gold_schema}.fact_query_history")
           .withColumn("warehouse_id", F.col("compute_warehouse_id"))  # Map!
           .select("warehouse_id", "query_date", ...))

# ❌ WRONG: Assume Gold column names match Feature table PKs
base_df = spark.table(fact_query).select("compute_warehouse_id", ...)
# Error: UNRESOLVED_COLUMN.WITH_SUGGESTION
```

#### 10. Consistent X_train Variable Naming

```python
# ✅ CORRECT: Consistent naming throughout
def prepare_and_train(training_df, feature_names):
    X_train = pdf[feature_names]  # Use X_train, not X
    ...
    return model, metrics, hyperparams, X_train  # Return X_train

# Capture correctly
model, metrics, hyperparams, X_train = prepare_and_train(...)

# Pass to logging
log_model_with_feature_engineering(fe, model, training_set, X_train, ...)

# ❌ WRONG: Mixed X and X_train
def prepare_and_train(...):
    X = pdf[feature_names]  # Uses X internally
    return model, metrics, hyperparams, X_train  # Returns X_train - undefined!
```

### Feature Engineering Validation Checklist

- [ ] Label cast to DOUBLE (regression) or INT (classification) in base_df
- [ ] STRING labels encoded to INT before create_training_set
- [ ] Column names mapped with `.withColumn()` when Gold ≠ Feature table
- [ ] Feature table PKs defined as NOT NULL
- [ ] NULL values filtered before feature table creation
- [ ] `X_train` used consistently (not `X`) throughout
- [ ] `X_train` returned from prepare_and_train function
- [ ] `X_train` passed to log_model function
- [ ] For runtime features: use `mlflow.sklearn.log_model()` not `fe.log_model()`
- [ ] input_example cast to float64: `X_train.head(5).astype('float64')`

---

## MLflow GenAI Patterns

### Automatic Tracing

```python
# At the TOP of your main module
import mlflow

mlflow.langchain.autolog(
    log_models=True,
    log_input_examples=True,
    log_model_signatures=True,
    log_inputs=True
)
```

### Manual Tracing with Decorators

```python
import mlflow

@mlflow.trace
def process_query(query: str) -> dict:
    """Function-level tracing."""
    result = retriever.search(query)
    return {"result": result}

# With span for sub-operations
@mlflow.trace
def complex_operation(input_data: dict) -> dict:
    with mlflow.start_span(name="preprocessing") as span:
        span.set_inputs({"raw": input_data})
        processed = preprocess(input_data)
        span.set_outputs({"processed": processed})
    
    with mlflow.start_span(name="inference") as span:
        span.set_inputs({"processed": processed})
        result = model.predict(processed)
        span.set_outputs({"prediction": result})
    
    return result
```

### Trace Tagging

```python
with mlflow.start_span(name="operation") as span:
    # Add metadata
    span.set_attributes({
        "user_id": user_id,
        "session_id": session_id,
        "model_version": "v2.1"
    })
```

### LLM Evaluation with Judges

#### Built-in Scorers

```python
from mlflow.genai.scorers import (
    Guidelines,
    RelevanceToInput,
    Safety,
    AnswerSimilarity
)

# Run evaluation
results = mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=my_agent.predict,
    scorers=[
        Guidelines(
            guidelines="Response must be professional and factual",
            name="professionalism_judge"
        ),
        RelevanceToInput(),
        Safety(),
        AnswerSimilarity(targets="expected_output")
    ]
)
```

#### Custom LLM Judge

```python
from mlflow.genai import scorer, Score

@scorer
def domain_accuracy_judge(inputs: dict, outputs: dict, expectations: dict = None) -> Score:
    """Custom judge for domain-specific accuracy."""
    from langchain_databricks import ChatDatabricks
    
    llm = ChatDatabricks(endpoint="databricks-dbrx-instruct", temperature=0)
    
    prompt = f"""Evaluate the response accuracy (0-1):
Query: {inputs.get('query')}
Response: {outputs.get('response')}

Return JSON: {{"score": <float>, "rationale": "<reason>"}}"""
    
    import json
    result = json.loads(llm.invoke(prompt).content)
    
    return Score(
        value=result["score"],
        rationale=result["rationale"]
    )

# Use in evaluation
results = mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=my_agent.predict,
    scorers=[domain_accuracy_judge]
)
```

### Production Monitoring with assess()

```python
import mlflow.genai

# Real-time assessment during inference
def monitored_predict(query: str) -> str:
    response = agent.predict(query)
    
    # Async assessment (non-blocking)
    mlflow.genai.assess(
        inputs={"query": query},
        outputs={"response": response},
        assessments=[
            mlflow.genai.Assessment(
                scorer="relevance",
                value=calculate_relevance(query, response)
            )
        ],
        trace_id=mlflow.get_current_trace_id()
    )
    
    return response
```

### Prompt Registry

#### Log Prompt

```python
import mlflow.genai

mlflow.genai.log_prompt(
    prompt="""You are a helpful assistant.

User context: {user_context}
Query: {query}""",
    artifact_path="prompts/assistant",
    registered_model_name="my_app_assistant_prompt"
)
```

#### Load Prompt

```python
import mlflow.genai

# Load specific version
prompt_template = mlflow.genai.load_prompt(
    model_uri="models:/my_app_assistant_prompt/1"
)

# Use with variables
formatted = prompt_template.format(
    user_context="Premium user",
    query="How do I upgrade?"
)
```

### ChatAgent Implementation

```python
from mlflow.pyfunc import ChatAgent
from mlflow.types.agent import ChatAgentMessage, ChatAgentResponse, ChatContext

class MyAgent(ChatAgent):
    def __init__(self):
        self.llm = ChatDatabricks(endpoint="databricks-dbrx-instruct")
    
    def predict(
        self,
        messages: list[ChatAgentMessage],
        context: ChatContext = None
    ) -> ChatAgentResponse:
        # Process messages
        response = self.llm.invoke([m.content for m in messages])
        
        return ChatAgentResponse(
            messages=[ChatAgentMessage(
                role="assistant",
                content=response.content
            )]
        )

# Log agent
with mlflow.start_run():
    mlflow.pyfunc.log_model(
        artifact_path="agent",
        python_model=MyAgent(),
        registered_model_name=f"{catalog}.{schema}.my_agent"
    )
```

### Validation Checklist

- [ ] Autolog enabled at module top
- [ ] Custom scorers return `Score` objects
- [ ] Trace spans have meaningful names
- [ ] Prompts registered with versioning
- [ ] ChatAgent implements correct interface
- [ ] assess() used for production monitoring

