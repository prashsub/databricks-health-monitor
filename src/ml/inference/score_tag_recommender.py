# Databricks notebook source
"""
Tag Recommender Inference
=========================

Custom inference for the tag_recommender model which uses TF-IDF features.

This model cannot use fe.score_batch() because:
1. TF-IDF features are computed at runtime from job names
2. These features are not stored in feature tables
3. Model was logged with mlflow.sklearn.log_model() (not fe.log_model())

Pipeline:
1. Load model and artifacts (TF-IDF vectorizer, label encoder) from MLflow
2. Find untagged jobs from Gold layer
3. Join with cost features
4. Compute TF-IDF features from job names
5. Make predictions
6. Store results in tag_recommendations table
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType
import mlflow
from mlflow import MlflowClient
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
import json

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

MODEL_NAME = "tag_recommender"
OUTPUT_TABLE = "tag_recommendations"

# Cost features used by the model (must match training)
COST_FEATURE_COLUMNS = [
    "daily_dbu", "daily_cost", "avg_dbu_7d", "avg_dbu_30d",
    "jobs_on_all_purpose_cost", "all_purpose_inefficiency_ratio"
]

# COMMAND ----------

def get_parameters():
    """Get notebook parameters from widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def load_model_and_artifacts(catalog: str, feature_schema: str):
    """
    Load the tag_recommender model and its artifacts.
    
    For Unity Catalog models, use pyfunc to load the model and 
    extract run_id from model_info for artifact download.
    
    Returns:
        tuple: (model, tfidf_vectorizer, label_encoder, model_version)
    """
    print(f"\n{'='*60}")
    print("Loading Tag Recommender Model and Artifacts")
    print("="*60)
    
    model_full_name = f"{catalog}.{feature_schema}.{MODEL_NAME}"
    
    # Use pyfunc to load model - this works with UC's /latest alias
    model_uri = f"models:/{model_full_name}@champion"
    
    # Try champion alias first, fall back to version 1 if not found
    try:
        print(f"  Trying model URI: {model_uri}")
        pyfunc_model = mlflow.pyfunc.load_model(model_uri)
        model_info = mlflow.models.get_model_info(model_uri)
    except Exception as e1:
        print(f"  Champion alias not found: {e1}")
        # Fall back to version 1
        model_uri = f"models:/{model_full_name}/1"
        print(f"  Trying model URI: {model_uri}")
        pyfunc_model = mlflow.pyfunc.load_model(model_uri)
        model_info = mlflow.models.get_model_info(model_uri)
    
    run_id = model_info.run_id
    print(f"  Run ID: {run_id}")
    
    # Extract version from model_info
    model_version = 0
    if hasattr(model_info, 'registered_model_version'):
        try:
            model_version = int(model_info.registered_model_version)
        except:
            pass
    print(f"  Model version: {model_version}")
    
    # Load the sklearn model from the same URI
    print(f"  Loading sklearn model...")
    model = mlflow.sklearn.load_model(model_uri)
    print(f"  ✓ Model loaded")
    
    # Download artifacts from the run
    print(f"  Downloading artifacts from run: {run_id}")
    artifacts_path = mlflow.artifacts.download_artifacts(run_id=run_id)
    
    # Load TF-IDF vectorizer
    tfidf_path = f"{artifacts_path}/tfidf_vectorizer.pkl"
    try:
        with open(tfidf_path, 'rb') as f:
            tfidf = pickle.load(f)
        print(f"  ✓ TF-IDF vectorizer loaded")
    except FileNotFoundError:
        raise FileNotFoundError(f"TF-IDF vectorizer not found at {tfidf_path}. Was the model trained correctly?")
    
    # Load label encoder
    le_path = f"{artifacts_path}/label_encoder.pkl"
    try:
        with open(le_path, 'rb') as f:
            label_encoder = pickle.load(f)
        print(f"  ✓ Label encoder loaded ({len(label_encoder.classes_)} classes)")
        print(f"  Tag classes: {list(label_encoder.classes_)[:5]}{'...' if len(label_encoder.classes_) > 5 else ''}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Label encoder not found at {le_path}. Was the model trained correctly?")
    
    return model, tfidf, label_encoder, model_version

# COMMAND ----------

def get_untagged_jobs(spark, catalog: str, gold_schema: str, feature_schema: str):
    """
    Get untagged jobs from the Gold layer that need tag recommendations.
    
    Joins:
    - fact_usage (untagged records)
    - dim_job (job names for TF-IDF)
    - cost_features (cost metrics)
    
    Returns:
        DataFrame with job_id, job_name, workspace_id, usage_date, and cost features
    """
    print(f"\n{'='*60}")
    print("Finding Untagged Jobs")
    print("="*60)
    
    fact_usage = f"{catalog}.{gold_schema}.fact_usage"
    dim_job = f"{catalog}.{gold_schema}.dim_job"
    cost_features = f"{catalog}.{feature_schema}.cost_features"
    
    # Get untagged jobs (is_tagged = False or no custom_tags)
    untagged_jobs = (
        spark.table(fact_usage)
        .filter(
            (F.col("is_tagged") == False) | 
            (F.col("custom_tags").isNull()) |
            (F.size(F.col("custom_tags")) == 0)
        )
        .filter(F.col("usage_metadata_job_id").isNotNull())
        .groupBy(F.col("usage_metadata_job_id").alias("job_id"))
        .agg(
            F.first("workspace_id").alias("workspace_id"),
            F.first(F.to_date("usage_date")).alias("usage_date"),
            F.sum("list_cost").alias("total_cost_30d"),
            F.count("*").alias("usage_count")
        )
    )
    
    untagged_count = untagged_jobs.count()
    print(f"  Untagged jobs in fact_usage: {untagged_count}")
    
    if untagged_count == 0:
        print("  ✓ No untagged jobs to process")
        return None
    
    # Join with dim_job to get job names (required for TF-IDF)
    jobs_with_names = (
        untagged_jobs
        .join(
            spark.table(dim_job)
                .select("job_id", "name")
                .dropDuplicates(["job_id"]),
            "job_id",
            "inner"
        )
        .withColumnRenamed("name", "job_name")
    )
    
    with_names_count = jobs_with_names.count()
    print(f"  Jobs with names (after dim_job join): {with_names_count}")
    
    if with_names_count == 0:
        print("  ⚠ No jobs found in dim_job - cannot compute TF-IDF")
        return None
    
    # Join with cost_features to get cost metrics
    jobs_with_features = (
        jobs_with_names
        .join(
            spark.table(cost_features),
            ["workspace_id", "usage_date"],
            "left"
        )
    )
    
    final_count = jobs_with_features.count()
    print(f"  Jobs with cost features: {final_count}")
    
    # Show sample
    print("\n  Sample untagged jobs:")
    jobs_with_features.select("job_id", "job_name", "workspace_id", "total_cost_30d").show(5, truncate=50)
    
    return jobs_with_features

# COMMAND ----------

def prepare_features_and_predict(
    pdf: pd.DataFrame,
    model,
    tfidf,
    label_encoder
) -> pd.DataFrame:
    """
    Prepare features and run inference.
    
    Steps:
    1. Compute TF-IDF features from job_name
    2. Prepare cost features
    3. Combine features
    4. Run model.predict()
    5. Decode labels
    
    Returns:
        DataFrame with predictions added
    """
    print(f"\n{'='*60}")
    print("Preparing Features and Running Inference")
    print("="*60)
    
    n_samples = len(pdf)
    print(f"  Samples to score: {n_samples}")
    
    # 1. Compute TF-IDF features from job names
    print("  Computing TF-IDF features...")
    job_names = pdf['job_name'].fillna('').astype(str)
    tfidf_features = tfidf.transform(job_names).toarray()
    tfidf_df = pd.DataFrame(
        tfidf_features,
        columns=[f"tfidf_{i}" for i in range(tfidf_features.shape[1])]
    )
    print(f"  ✓ TF-IDF features: {tfidf_features.shape[1]} dimensions")
    
    # 2. Prepare cost features
    print("  Preparing cost features...")
    available_cost_cols = [c for c in COST_FEATURE_COLUMNS if c in pdf.columns]
    missing_cols = set(COST_FEATURE_COLUMNS) - set(available_cost_cols)
    
    if missing_cols:
        print(f"  ⚠ Missing cost features (will use 0): {missing_cols}")
    
    cost_df = pdf[available_cost_cols].copy() if available_cost_cols else pd.DataFrame()
    
    # Add missing columns with zeros
    for col in missing_cols:
        cost_df[col] = 0.0
    
    # Ensure correct order
    cost_df = cost_df[[c for c in COST_FEATURE_COLUMNS if c in cost_df.columns]]
    
    # Clean and cast to float64
    for col in cost_df.columns:
        cost_df[col] = pd.to_numeric(cost_df[col], errors='coerce')
    cost_df = cost_df.fillna(0).replace([np.inf, -np.inf], 0).astype('float64')
    
    print(f"  ✓ Cost features: {len(cost_df.columns)} columns")
    
    # 3. Combine features (must match training order: cost + tfidf)
    X = pd.concat([cost_df.reset_index(drop=True), tfidf_df.reset_index(drop=True)], axis=1)
    print(f"  ✓ Combined feature matrix: {X.shape}")
    
    # 4. Run predictions
    print("  Running model.predict()...")
    predictions_encoded = model.predict(X)
    
    # 5. Decode predictions to tag names
    predicted_tags = label_encoder.inverse_transform(predictions_encoded)
    
    # 6. Get prediction probabilities if available
    try:
        probabilities = model.predict_proba(X)
        # Get max probability for confidence score
        confidence_scores = np.max(probabilities, axis=1)
        print(f"  ✓ Predictions complete with confidence scores")
    except AttributeError:
        confidence_scores = np.ones(len(predictions_encoded)) * 0.5
        print(f"  ✓ Predictions complete (no confidence available)")
    
    # Add predictions to dataframe
    pdf['predicted_tag'] = predicted_tags
    pdf['confidence_score'] = confidence_scores
    
    # Show distribution
    tag_dist = pdf['predicted_tag'].value_counts().head(10)
    print(f"\n  Predicted tag distribution (top 10):")
    for tag, count in tag_dist.items():
        print(f"    {tag}: {count} ({100*count/n_samples:.1f}%)")
    
    return pdf

# COMMAND ----------

def apply_tag_recommendations_metadata(spark, output_table: str) -> bool:
    """
    Apply table and column metadata for tag_recommendations table.
    Enables Genie Space natural language queries and AI/BI discoverability.
    
    Uses centralized metadata from utility module if available, fallback to inline.
    """
    try:
        # Try using centralized metadata (has comprehensive descriptions)
        from src.ml.utils.prediction_metadata import PREDICTION_TABLE_METADATA, apply_table_metadata
        if "tag_recommendations" in PREDICTION_TABLE_METADATA:
            result = apply_table_metadata(spark, output_table)
            if result:
                print(f"  ✓ Applied comprehensive metadata from utility module")
                return result
    except ImportError:
        print(f"  ⚠ Utility module not found, using inline metadata")
    except Exception as e:
        print(f"  ⚠ Utility module error: {str(e)[:50]}, using inline metadata")
    
    # Fallback to inline metadata
    try:
        table_comment = """ML predictions from tag_recommender model.
Recommends tags for untagged jobs using TF-IDF text analysis and Random Forest classification.
Interpretation: predicted_tag is the recommended tag value with associated confidence_score.
Business Use: Improve cost attribution coverage, governance compliance, automated tagging.
Action: Review high-confidence recommendations (>0.7) for auto-tagging. Manual review for lower confidence.
Source: cost_features + job names (TF-IDF) | Model: RandomForestClassifier | Domain: Cost"""
        table_comment = table_comment.replace("'", "''")
        spark.sql(f"COMMENT ON TABLE {output_table} IS '{table_comment}'")
        
        # Column comments with interpretation guidance
        column_comments = {
            "job_id": "Unique identifier of the untagged job. Use to apply recommended tag via Jobs API.",
            "job_name": "Name of the job (used for TF-IDF feature extraction). Consistent naming improves accuracy.",
            "workspace_id": "Workspace where the job is defined. Use for workspace-level tag standardization.",
            "usage_date": "Reference date for cost features. Recent dates ensure current cost patterns.",
            "predicted_tag": "Recommended tag value (team name, project, cost center). Verify matches org taxonomy.",
            "confidence_score": "Model confidence (0-1). >0.8=auto-tag safe, 0.5-0.8=manual review, <0.5=human decision.",
            "total_cost_30d": "Job cost over 30 days (USD). Prioritize high-cost jobs for tagging.",
            "model_name": "ML model for lineage (tag_recommender).",
            "model_version": "Model version for reproducibility.",
            "scored_at": "Prediction timestamp. Use recent predictions for tagging campaigns.",
            "scored_date": "Date partition. Filter by scored_date for recent recommendations."
        }
        
        table_columns = [f.name for f in spark.table(output_table).schema.fields]
        columns_updated = 0
        
        for col_name, col_comment in column_comments.items():
            if col_name in table_columns:
                escaped_comment = col_comment.replace("'", "''")
                spark.sql(f"ALTER TABLE {output_table} ALTER COLUMN `{col_name}` COMMENT '{escaped_comment}'")
                columns_updated += 1
        
        print(f"  ✓ Table comment + {columns_updated} column comments applied (inline)")
        return True
        
    except Exception as e:
        print(f"  ⚠ Metadata warning: {str(e)[:80]}")
        return False

# COMMAND ----------

def save_predictions(
    spark,
    predictions_pdf: pd.DataFrame,
    catalog: str,
    feature_schema: str,
    model_version: int
):
    """
    Save predictions to the tag_recommendations table.
    
    Creates the table if it doesn't exist, appends predictions.
    """
    print(f"\n{'='*60}")
    print("Saving Predictions")
    print("="*60)
    
    output_table = f"{catalog}.{feature_schema}.{OUTPUT_TABLE}"
    
    # Prepare output DataFrame
    output_pdf = predictions_pdf[[
        'job_id', 'job_name', 'workspace_id', 'usage_date',
        'predicted_tag', 'confidence_score', 'total_cost_30d'
    ]].copy()
    
    # Add metadata
    output_pdf['model_name'] = MODEL_NAME
    output_pdf['model_version'] = model_version
    output_pdf['scored_at'] = datetime.now()
    
    # Convert to Spark DataFrame
    output_df = spark.createDataFrame(output_pdf)
    
    # Add partition column for efficient querying
    output_df = output_df.withColumn("scored_date", F.to_date("scored_at"))
    
    # Write to table (merge to avoid duplicates on job_id + scored_date)
    print(f"  Writing {len(output_pdf)} predictions to {output_table}")
    
    try:
        # Try to create or append
        output_df.write \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(output_table)
        print(f"  ✓ Saved to {output_table}")
        
    except Exception as e:
        print(f"  ⚠ Error saving: {e}")
        # Fallback: append
        output_df.write.mode("append").saveAsTable(output_table)
        print(f"  ✓ Appended to {output_table}")
    
    # Apply table and column metadata for Genie/AI-BI discoverability
    apply_tag_recommendations_metadata(spark, output_table)
    
    # Show sample output
    print(f"\n  Sample predictions:")
    spark.table(output_table).select(
        "job_id", "job_name", "predicted_tag", "confidence_score"
    ).show(10, truncate=40)
    
    return len(output_pdf)

# COMMAND ----------

def main():
    """Main entry point for tag recommender inference."""
    print("\n" + "=" * 80)
    print("TAG RECOMMENDER - BATCH INFERENCE")
    print("Custom inference with TF-IDF feature extraction")
    print("=" * 80)
    
    start_time = datetime.now()
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    spark = SparkSession.builder.getOrCreate()
    
    try:
        # 1. Load model and artifacts
        model, tfidf, label_encoder, model_version = load_model_and_artifacts(
            catalog, feature_schema
        )
        
        # 2. Get untagged jobs
        untagged_df = get_untagged_jobs(spark, catalog, gold_schema, feature_schema)
        
        if untagged_df is None or untagged_df.count() == 0:
            print("\n" + "=" * 80)
            print("✓ NO UNTAGGED JOBS TO PROCESS")
            print("=" * 80)
            dbutils.notebook.exit(json.dumps({
                "status": "SUCCESS",
                "records_scored": 0,
                "message": "No untagged jobs found"
            }))
            return
        
        # 3. Convert to pandas for sklearn inference
        pdf = untagged_df.toPandas()
        
        # 4. Prepare features and predict
        predictions_pdf = prepare_features_and_predict(
            pdf, model, tfidf, label_encoder
        )
        
        # 5. Save predictions
        records_saved = save_predictions(
            spark, predictions_pdf, catalog, feature_schema, model_version
        )
        
        # Summary
        duration = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("✓ TAG RECOMMENDER INFERENCE COMPLETE")
        print("=" * 80)
        print(f"  Records scored: {records_saved}")
        print(f"  Model version: {model_version}")
        print(f"  Duration: {duration:.1f}s")
        print(f"  Output table: {catalog}.{feature_schema}.{OUTPUT_TABLE}")
        print("=" * 80)
        
        dbutils.notebook.exit(json.dumps({
            "status": "SUCCESS",
            "records_scored": records_saved,
            "model_version": model_version,
            "duration_seconds": round(duration, 1)
        }))
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"\n❌ ERROR: {error_msg}")
        print(traceback.format_exc())
        
        dbutils.notebook.exit(json.dumps({
            "status": "FAILED",
            "error": error_msg
        }))
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()

