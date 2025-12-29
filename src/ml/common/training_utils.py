# Databricks notebook source
"""
Training Utilities for Databricks Health Monitor
=================================================

This module provides utilities for model training, evaluation, and validation,
following MLflow 3.0 and scikit-learn best practices.

Features:
- Consistent train/test splitting with temporal awareness
- Cross-validation utilities
- Model evaluation metrics by problem type
- Hyperparameter tuning with Optuna integration
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
)
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """
    Configuration for model training.
    
    Attributes:
        test_size: Proportion of data for testing
        validation_size: Proportion of training data for validation
        random_state: Random seed for reproducibility
        n_cv_splits: Number of cross-validation splits
        time_series_cv: Whether to use time series cross-validation
        early_stopping_rounds: Early stopping rounds for boosting models
    """
    test_size: float = 0.2
    validation_size: float = 0.1
    random_state: int = 42
    n_cv_splits: int = 5
    time_series_cv: bool = False
    early_stopping_rounds: int = 50
    
    # Problem-specific defaults
    classification_threshold: float = 0.5
    anomaly_contamination: float = 0.1


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    config: TrainingConfig,
    timestamp_column: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Split data into train, validation, and test sets.
    
    For time series data, performs chronological split to prevent data leakage.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        config: Training configuration
        timestamp_column: Column name for chronological ordering (if time series)
        
    Returns:
        Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    if timestamp_column and timestamp_column in X.columns:
        # Time series: sort by timestamp and split chronologically
        sort_idx = X[timestamp_column].argsort()
        X_sorted = X.iloc[sort_idx].copy()
        y_sorted = y.iloc[sort_idx].copy()
        
        # Remove timestamp column from features after sorting
        X_sorted = X_sorted.drop(columns=[timestamp_column])
        
        n = len(X_sorted)
        test_start = int(n * (1 - config.test_size))
        val_start = int(test_start * (1 - config.validation_size))
        
        X_train = X_sorted.iloc[:val_start]
        y_train = y_sorted.iloc[:val_start]
        X_val = X_sorted.iloc[val_start:test_start]
        y_val = y_sorted.iloc[val_start:test_start]
        X_test = X_sorted.iloc[test_start:]
        y_test = y_sorted.iloc[test_start:]
        
        logger.info("Performed chronological train/val/test split")
    else:
        # Random split
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=config.test_size, random_state=config.random_state
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=config.validation_size, random_state=config.random_state
        )
        logger.info("Performed random train/val/test split")
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    return X_train, X_val, X_test, y_train, y_val, y_test


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    problem_type: str = "classification",
    threshold: float = 0.5
) -> Dict[str, float]:
    """
    Evaluate model performance and return metrics.
    
    Args:
        model: Trained model with predict and predict_proba methods
        X_test: Test features
        y_test: Test labels
        problem_type: One of 'classification', 'regression', 'anomaly_detection'
        threshold: Classification threshold (for binary classification)
        
    Returns:
        Dictionary of metric names to values
    """
    metrics = {}
    
    if problem_type == "classification":
        # Get predictions
        y_pred = model.predict(X_test)
        
        # Get probabilities if available
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test)
            if y_proba.shape[1] == 2:
                y_proba = y_proba[:, 1]
                metrics['roc_auc'] = roc_auc_score(y_test, y_proba)
        
        # Calculate classification metrics
        metrics['accuracy'] = accuracy_score(y_test, y_pred)
        metrics['precision'] = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        metrics['recall'] = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        metrics['f1'] = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        logger.info(f"Classification metrics: Accuracy={metrics['accuracy']:.4f}, F1={metrics['f1']:.4f}")
        
    elif problem_type == "regression":
        y_pred = model.predict(X_test)
        
        metrics['mse'] = mean_squared_error(y_test, y_pred)
        metrics['rmse'] = np.sqrt(metrics['mse'])
        metrics['mae'] = mean_absolute_error(y_test, y_pred)
        metrics['r2'] = r2_score(y_test, y_pred)
        
        # MAPE only if no zeros in y_test
        if (y_test != 0).all():
            metrics['mape'] = mean_absolute_percentage_error(y_test, y_pred)
        
        logger.info(f"Regression metrics: RMSE={metrics['rmse']:.4f}, R2={metrics['r2']:.4f}")
        
    elif problem_type == "anomaly_detection":
        # For anomaly detection, we often use decision function or predict
        y_pred = model.predict(X_test)
        
        if hasattr(model, 'decision_function'):
            scores = model.decision_function(X_test)
            metrics['anomaly_score_mean'] = float(np.mean(scores))
            metrics['anomaly_score_std'] = float(np.std(scores))
        
        # Convert predictions to binary (1=anomaly, -1=normal for sklearn)
        if y_pred.min() < 0:
            y_pred_binary = (y_pred == -1).astype(int)
        else:
            y_pred_binary = y_pred
        
        metrics['anomaly_rate'] = float(np.mean(y_pred_binary))
        
        # If we have ground truth labels
        if y_test is not None and len(y_test) == len(y_pred_binary):
            metrics['precision'] = precision_score(y_test, y_pred_binary, zero_division=0)
            metrics['recall'] = recall_score(y_test, y_pred_binary, zero_division=0)
            metrics['f1'] = f1_score(y_test, y_pred_binary, zero_division=0)
        
        logger.info(f"Anomaly detection: Rate={metrics['anomaly_rate']:.4f}")
    
    return metrics


def cross_validate(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    config: TrainingConfig,
    scoring: str = "f1_weighted"
) -> Dict[str, float]:
    """
    Perform cross-validation and return summary statistics.
    
    Args:
        model: Model instance (not fitted)
        X: Features
        y: Target
        config: Training configuration
        scoring: Scoring metric name
        
    Returns:
        Dictionary with cv scores statistics
    """
    if config.time_series_cv:
        cv = TimeSeriesSplit(n_splits=config.n_cv_splits)
    else:
        cv = config.n_cv_splits
    
    scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
    
    results = {
        'cv_mean': float(np.mean(scores)),
        'cv_std': float(np.std(scores)),
        'cv_min': float(np.min(scores)),
        'cv_max': float(np.max(scores)),
    }
    
    logger.info(f"CV {scoring}: {results['cv_mean']:.4f} (+/- {results['cv_std']:.4f})")
    
    return results


def create_binary_labels_from_zscore(
    series: pd.Series,
    threshold: float = 3.0,
    direction: str = "both"
) -> pd.Series:
    """
    Create binary anomaly labels from z-scores.
    
    Args:
        series: Series of values
        threshold: Z-score threshold for anomaly
        direction: 'high', 'low', or 'both'
        
    Returns:
        Binary series (1=anomaly, 0=normal)
    """
    mean = series.mean()
    std = series.std()
    
    if std == 0:
        return pd.Series(0, index=series.index)
    
    z_scores = (series - mean) / std
    
    if direction == "high":
        return (z_scores > threshold).astype(int)
    elif direction == "low":
        return (z_scores < -threshold).astype(int)
    else:  # both
        return ((z_scores > threshold) | (z_scores < -threshold)).astype(int)


def get_feature_importance(
    model,
    feature_names: List[str],
    importance_type: str = "auto"
) -> pd.DataFrame:
    """
    Extract feature importance from a trained model.
    
    Args:
        model: Trained model
        feature_names: List of feature names
        importance_type: Type of importance ('auto', 'gain', 'weight', 'cover')
        
    Returns:
        DataFrame with feature names and importance scores
    """
    if hasattr(model, 'feature_importances_'):
        # sklearn-style models
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        # Linear models
        importances = np.abs(model.coef_).flatten()
    elif hasattr(model, 'get_score'):
        # XGBoost with get_score method
        importance_dict = model.get_score(importance_type=importance_type)
        # Map back to feature names
        importances = [importance_dict.get(f, 0) for f in feature_names]
    else:
        logger.warning("Model does not have interpretable feature importance")
        return pd.DataFrame({
            'feature': feature_names,
            'importance': [0] * len(feature_names)
        })
    
    df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    # Normalize
    total = df['importance'].sum()
    if total > 0:
        df['importance_pct'] = df['importance'] / total * 100
    else:
        df['importance_pct'] = 0
    
    return df


class EarlyStopping:
    """
    Early stopping callback for training loops.
    """
    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 0.0001,
        mode: str = "min"
    ):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_score = None
        self.counter = 0
        self.should_stop = False
    
    def __call__(self, score: float) -> bool:
        """
        Check if training should stop.
        
        Args:
            score: Current validation score
            
        Returns:
            True if training should stop
        """
        if self.best_score is None:
            self.best_score = score
            return False
        
        if self.mode == "min":
            improved = score < (self.best_score - self.min_delta)
        else:
            improved = score > (self.best_score + self.min_delta)
        
        if improved:
            self.best_score = score
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
                logger.info(f"Early stopping triggered after {self.counter} epochs")
                return True
        
        return False






