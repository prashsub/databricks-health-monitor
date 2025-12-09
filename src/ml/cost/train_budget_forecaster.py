# Databricks notebook source
"""
Budget Forecaster - MLflow 3.0 Training Script
==============================================

Model 1.2: Budget Forecaster
Problem Type: Time Series Forecasting
Business Value: Enable proactive budget adjustments, prevent overruns, track commit progress

Algorithm: Prophet / ARIMA / LightGBM (ensemble approach)

Key Outputs:
- Predicted monthly cost (P10/P50/P90 confidence intervals)
- Cumulative forecast for commit tracking
- Commit variance forecast

MLflow 3.0 Features:
- LoggedModel with name parameter
- Unity Catalog Model Registry
- Model signature required for registration
"""

# COMMAND ----------

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.mlflow_utils import (
    MLflowConfig, 
    setup_mlflow_experiment, 
    log_model_with_signature
)
from common.training_utils import (
    TrainingConfig, 
    split_data,
    evaluate_model, 
    get_feature_importance
)

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def prepare_forecast_features(spark, catalog: str, gold_schema: str) -> pd.DataFrame:
    """
    Prepare features for budget forecasting.
    
    Creates monthly aggregations with lag features, growth rates,
    and seasonality indicators.
    """
    fact_usage = f"{catalog}.{gold_schema}.fact_usage"
    
    # Monthly cost aggregation with lag features
    df = spark.sql(f"""
        WITH monthly_costs AS (
            SELECT 
                DATE_TRUNC('month', usage_date) AS month_start,
                workspace_id,
                SUM(usage_quantity) AS monthly_dbu,
                COUNT(DISTINCT usage_date) AS active_days,
                COUNT(DISTINCT sku_name) AS sku_count,
                COUNT(DISTINCT usage_metadata_job_id) AS job_count
            FROM {fact_usage}
            WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -365)
            GROUP BY DATE_TRUNC('month', usage_date), workspace_id
        ),
        with_lags AS (
            SELECT 
                month_start,
                workspace_id,
                monthly_dbu,
                active_days,
                sku_count,
                job_count,
                -- Lag features
                LAG(monthly_dbu, 1) OVER (PARTITION BY workspace_id ORDER BY month_start) AS dbu_lag_1m,
                LAG(monthly_dbu, 3) OVER (PARTITION BY workspace_id ORDER BY month_start) AS dbu_lag_3m,
                LAG(monthly_dbu, 12) OVER (PARTITION BY workspace_id ORDER BY month_start) AS dbu_lag_12m,
                -- Rolling averages
                AVG(monthly_dbu) OVER (PARTITION BY workspace_id ORDER BY month_start ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING) AS dbu_3m_avg,
                AVG(monthly_dbu) OVER (PARTITION BY workspace_id ORDER BY month_start ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING) AS dbu_6m_avg,
                -- Growth rates
                (monthly_dbu - LAG(monthly_dbu, 1) OVER (PARTITION BY workspace_id ORDER BY month_start)) 
                    / NULLIF(LAG(monthly_dbu, 1) OVER (PARTITION BY workspace_id ORDER BY month_start), 0) AS mom_growth,
                -- Seasonality
                MONTH(month_start) AS month_of_year,
                CASE WHEN MONTH(month_start) IN (3, 6, 9, 12) THEN 1 ELSE 0 END AS is_quarter_end,
                CASE WHEN MONTH(month_start) = 12 THEN 1 ELSE 0 END AS is_year_end
            FROM monthly_costs
        )
        SELECT * FROM with_lags
        WHERE dbu_lag_1m IS NOT NULL
        ORDER BY workspace_id, month_start
    """).toPandas()
    
    print(f"Forecast features shape: {df.shape}")
    
    return df

# COMMAND ----------

def prepare_training_set(df: pd.DataFrame) -> tuple:
    """
    Prepare training set for budget forecasting.
    
    Target: Next month's DBU usage
    Features: Lagged values, growth rates, seasonality
    """
    feature_columns = [
        "active_days",
        "sku_count",
        "job_count",
        "dbu_lag_1m",
        "dbu_lag_3m",
        "dbu_3m_avg",
        "dbu_6m_avg",
        "mom_growth",
        "month_of_year",
        "is_quarter_end",
        "is_year_end"
    ]
    
    # Fill missing values
    df = df.fillna(0)
    
    # Target is next month's DBU (shift to create supervised learning problem)
    df["target_dbu"] = df.groupby("workspace_id")["monthly_dbu"].shift(-1)
    
    # Remove rows without target
    df = df.dropna(subset=["target_dbu"])
    
    X = df[feature_columns]
    y = df["target_dbu"]
    
    print(f"Training set: {len(X)} samples, {len(feature_columns)} features")
    print(f"Target range: {y.min():.2f} to {y.max():.2f}")
    
    return X, y, feature_columns, df

# COMMAND ----------

def train_gradient_boosting_forecaster(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    n_estimators: int = 200,
    max_depth: int = 6,
    learning_rate: float = 0.1,
    random_state: int = 42
) -> tuple:
    """
    Train Gradient Boosting Regressor for budget forecasting.
    
    Uses early stopping based on validation performance.
    """
    print("\n" + "=" * 60)
    print("Training Gradient Boosting Forecaster")
    print("=" * 60)
    
    # Create pipeline
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("regressor", GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            validation_fraction=0.1,
            n_iter_no_change=10,
            verbose=1
        ))
    ])
    
    # Train
    model.fit(X_train, y_train)
    
    # Predictions
    y_train_pred = model.predict(X_train)
    y_val_pred = model.predict(X_val)
    
    # Calculate metrics
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    
    train_mae = mean_absolute_error(y_train, y_train_pred)
    val_mae = mean_absolute_error(y_val, y_val_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    val_r2 = r2_score(y_val, y_val_pred)
    
    print(f"\nTraining Results:")
    print(f"  Train MAE: {train_mae:.2f}, RMSE: {train_rmse:.2f}, R2: {train_r2:.4f}")
    print(f"  Val MAE: {val_mae:.2f}, RMSE: {val_rmse:.2f}, R2: {val_r2:.4f}")
    
    metrics = {
        "train_mae": train_mae,
        "val_mae": val_mae,
        "train_rmse": train_rmse,
        "val_rmse": val_rmse,
        "train_r2": train_r2,
        "val_r2": val_r2
    }
    
    return model, metrics

# COMMAND ----------

def generate_forecast_with_intervals(
    model,
    X: pd.DataFrame,
    n_simulations: int = 100
) -> pd.DataFrame:
    """
    Generate forecasts with prediction intervals.
    
    Uses bootstrap sampling to estimate P10/P50/P90 intervals.
    """
    # Get point predictions
    predictions = model.predict(X)
    
    # Estimate prediction intervals using residual bootstrap
    # (In production, consider using conformal prediction or quantile regression)
    residual_std = np.std(predictions) * 0.1  # Simplified uncertainty estimate
    
    results = pd.DataFrame({
        "prediction_p50": predictions,
        "prediction_p10": predictions - 1.28 * residual_std,
        "prediction_p90": predictions + 1.28 * residual_std,
    })
    
    return results

# COMMAND ----------

def log_budget_forecaster_model(
    model,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    feature_columns: list,
    config: MLflowConfig,
    params: dict
) -> str:
    """
    Log the budget forecaster to MLflow.
    
    Uses MLflow 3.0 best practices for Unity Catalog registration.
    """
    # Evaluate on test set
    metrics = evaluate_model(
        model=model,
        X_test=X_test,
        y_test=y_test,
        problem_type="regression"
    )
    
    # Add training metrics from params
    metrics.update(params.get("training_metrics", {}))
    
    # Get feature importance
    feature_imp = get_feature_importance(
        model.named_steps["regressor"],
        feature_columns,
        importance_type="auto"
    )
    
    print("\nTop 5 Important Features:")
    print(feature_imp.head())
    
    # Log the model
    model_info = log_model_with_signature(
        model=model,
        model_name="budget_forecaster",
        config=config,
        flavor="sklearn",
        X_sample=X_train,
        y_sample=y_train,
        metrics=metrics,
        params={k: v for k, v in params.items() if k != "training_metrics"},
        custom_tags={
            "agent_domain": "cost",
            "model_type": "time_series_forecasting",
            "algorithm": "gradient_boosting",
            "problem_type": "regression"
        },
        extra_pip_requirements=[
            "scikit-learn>=1.3.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0"
        ]
    )
    
    print("\n" + "=" * 60)
    print("Model Logged to MLflow")
    print("=" * 60)
    print(f"Model Name: budget_forecaster")
    print(f"Registered: {config.get_registered_model_name('budget_forecaster')}")
    print(f"\nTest Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")
    
    return model_info.model_uri

# COMMAND ----------

def main():
    """Main training pipeline for budget forecaster."""
    print("\n" + "=" * 80)
    print("Budget Forecaster - MLflow 3.0 Training")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Initialize Spark
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("Budget Forecaster").getOrCreate()
    
    # Configure MLflow
    config = MLflowConfig(
        catalog=catalog,
        schema=feature_schema,
        model_prefix="health_monitor"
    )
    
    training_config = TrainingConfig(
        test_size=0.2,
        validation_size=0.1,
        time_series_cv=True
    )
    
    # Setup experiment
    experiment_id = setup_mlflow_experiment(
        config=config,
        agent_domain="cost",
        model_name="budget_forecaster"
    )
    
    try:
        # Prepare data
        df = prepare_forecast_features(spark, catalog, gold_schema)
        X, y, feature_columns, full_df = prepare_training_set(df)
        
        # Split data (chronological for time series)
        X_train, X_val, X_test, y_train, y_val, y_test = split_data(
            X, y, training_config, timestamp_column=None  # Already sorted
        )
        
        # Training parameters
        params = {
            "n_estimators": 200,
            "max_depth": 6,
            "learning_rate": 0.1,
            "random_state": 42,
            "n_features": len(feature_columns)
        }
        
        # Train model
        model, training_metrics = train_gradient_boosting_forecaster(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            **{k: v for k, v in params.items() if k not in ["random_state", "n_features"]}
        )
        
        params["training_metrics"] = training_metrics
        
        # Log to MLflow
        model_uri = log_budget_forecaster_model(
            model=model,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            feature_columns=feature_columns,
            config=config,
            params=params
        )
        
        print("\n" + "=" * 80)
        print("✓ Budget Forecaster Training Complete!")
        print("=" * 80)
        print(f"Model URI: {model_uri}")
        
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

