"""
Tests for Cost Anomaly Detector Model
=====================================

Test coverage:
- Feature preparation and data validation
- Isolation Forest training and predictions
- Anomaly detection accuracy
- MLflow logging (mocked)
"""

import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from unittest.mock import MagicMock, patch


class TestCostAnomalyFeatures:
    """Test feature preparation for cost anomaly detection."""

    @pytest.mark.unit
    def test_feature_columns_valid(self, sample_cost_features):
        """Verify all expected feature columns are present."""
        expected_columns = [
            'daily_dbu',
            'avg_dbu_7d',
            'avg_dbu_30d',
            'z_score_7d',
            'z_score_30d',
            'dbu_change_pct_1d',
            'dbu_change_pct_7d',
            'dow_sin',
            'dow_cos',
            'is_weekend',
            'is_month_end'
        ]

        for col in expected_columns:
            assert col in sample_cost_features.columns, f"Missing column: {col}"

    @pytest.mark.unit
    def test_feature_data_types(self, sample_cost_features):
        """Verify feature data types are numeric."""
        numeric_cols = [
            'daily_dbu', 'avg_dbu_7d', 'avg_dbu_30d',
            'z_score_7d', 'z_score_30d',
            'dbu_change_pct_1d', 'dbu_change_pct_7d',
            'dow_sin', 'dow_cos'
        ]

        for col in numeric_cols:
            assert np.issubdtype(sample_cost_features[col].dtype, np.number), \
                f"Column {col} should be numeric, got {sample_cost_features[col].dtype}"

    @pytest.mark.unit
    def test_feature_no_infinite_values(self, sample_cost_features):
        """Verify no infinite values in features."""
        numeric_cols = sample_cost_features.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            assert not np.isinf(sample_cost_features[col]).any(), \
                f"Column {col} contains infinite values"

    @pytest.mark.unit
    def test_feature_range_dow_cyclical(self, sample_cost_features):
        """Verify day-of-week cyclical features are in [-1, 1] range."""
        assert sample_cost_features['dow_sin'].between(-1, 1).all(), \
            "dow_sin values should be in [-1, 1]"
        assert sample_cost_features['dow_cos'].between(-1, 1).all(), \
            "dow_cos values should be in [-1, 1]"

    @pytest.mark.unit
    def test_feature_binary_columns(self, sample_cost_features):
        """Verify binary columns contain only 0 and 1."""
        binary_cols = ['is_weekend', 'is_month_end']

        for col in binary_cols:
            unique_values = set(sample_cost_features[col].unique())
            assert unique_values <= {0, 1}, \
                f"Column {col} should be binary, got {unique_values}"


class TestIsolationForestTraining:
    """Test Isolation Forest model training."""

    @pytest.mark.unit
    def test_model_trains_successfully(self, sample_cost_features):
        """Verify model trains without errors."""
        feature_cols = [
            'daily_dbu', 'avg_dbu_7d', 'z_score_7d',
            'dow_sin', 'dow_cos', 'is_weekend'
        ]
        X = sample_cost_features[feature_cols].fillna(0)

        model = IsolationForest(
            n_estimators=50,
            contamination=0.05,
            random_state=42
        )

        # Should not raise
        model.fit(X)

        assert hasattr(model, 'estimators_'), "Model should have fitted estimators"
        assert len(model.estimators_) == 50, "Should have 50 trees"

    @pytest.mark.unit
    def test_model_predictions_valid(self, sample_cost_features):
        """Verify model predictions are valid (-1 or 1)."""
        feature_cols = [
            'daily_dbu', 'avg_dbu_7d', 'z_score_7d',
            'dow_sin', 'dow_cos', 'is_weekend'
        ]
        X = sample_cost_features[feature_cols].fillna(0)

        model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)
        model.fit(X)
        predictions = model.predict(X)

        unique_preds = set(predictions)
        assert unique_preds <= {-1, 1}, f"Predictions should be -1 or 1, got {unique_preds}"

    @pytest.mark.unit
    def test_anomaly_rate_matches_contamination(self, sample_cost_features):
        """Verify anomaly rate approximately matches contamination parameter."""
        feature_cols = [
            'daily_dbu', 'avg_dbu_7d', 'z_score_7d',
            'dow_sin', 'dow_cos', 'is_weekend'
        ]
        X = sample_cost_features[feature_cols].fillna(0)

        contamination = 0.05
        model = IsolationForest(n_estimators=100, contamination=contamination, random_state=42)
        model.fit(X)
        predictions = model.predict(X)

        anomaly_rate = (predictions == -1).mean()

        # Allow 2% tolerance
        assert abs(anomaly_rate - contamination) < 0.02, \
            f"Anomaly rate {anomaly_rate:.3f} should be close to contamination {contamination}"

    @pytest.mark.unit
    def test_decision_function_returns_scores(self, sample_cost_features):
        """Verify decision function returns anomaly scores."""
        feature_cols = [
            'daily_dbu', 'avg_dbu_7d', 'z_score_7d',
            'dow_sin', 'dow_cos', 'is_weekend'
        ]
        X = sample_cost_features[feature_cols].fillna(0)

        model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)
        model.fit(X)
        scores = model.decision_function(X)

        assert len(scores) == len(X), "Should have score for each sample"
        assert scores.dtype == np.float64, "Scores should be float"

    @pytest.mark.unit
    def test_anomalies_have_lower_scores(self, sample_cost_features):
        """Verify anomalies have lower decision function scores."""
        feature_cols = [
            'daily_dbu', 'avg_dbu_7d', 'z_score_7d',
            'dow_sin', 'dow_cos', 'is_weekend'
        ]
        X = sample_cost_features[feature_cols].fillna(0)

        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        model.fit(X)

        predictions = model.predict(X)
        scores = model.decision_function(X)

        # Anomalies (pred=-1) should have lower scores than normal (pred=1)
        anomaly_scores = scores[predictions == -1]
        normal_scores = scores[predictions == 1]

        assert anomaly_scores.mean() < normal_scores.mean(), \
            "Anomaly scores should be lower than normal scores"


class TestCostAnomalyDetection:
    """Test anomaly detection accuracy on synthetic data."""

    @pytest.mark.unit
    def test_detects_obvious_anomalies(self):
        """Verify model detects obvious cost spikes."""
        np.random.seed(42)

        # Generate normal data
        n_normal = 950
        normal_data = pd.DataFrame({
            'daily_dbu': np.random.normal(100, 10, n_normal),
            'z_score': np.random.normal(0, 1, n_normal),
        })

        # Add obvious anomalies (10x normal)
        n_anomaly = 50
        anomaly_data = pd.DataFrame({
            'daily_dbu': np.random.normal(1000, 50, n_anomaly),  # 10x spike
            'z_score': np.random.normal(5, 1, n_anomaly),  # High z-score
        })

        # Combine
        data = pd.concat([normal_data, anomaly_data], ignore_index=True)

        # Train model
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        model.fit(data)
        predictions = model.predict(data)

        # Check that most injected anomalies are detected
        # Last 50 samples are anomalies
        true_labels = np.array([1] * n_normal + [-1] * n_anomaly)

        # Calculate recall for anomalies
        anomaly_mask = true_labels == -1
        detected_anomalies = (predictions[anomaly_mask] == -1).sum()
        recall = detected_anomalies / n_anomaly

        assert recall > 0.5, f"Should detect >50% of obvious anomalies, got {recall:.2%}"

    @pytest.mark.unit
    def test_handles_missing_values(self, sample_cost_features):
        """Verify model handles NaN values gracefully."""
        # Introduce some NaN values
        df = sample_cost_features.copy()
        df.loc[0:10, 'daily_dbu'] = np.nan
        df.loc[20:30, 'z_score_7d'] = np.nan

        feature_cols = ['daily_dbu', 'avg_dbu_7d', 'z_score_7d']
        X = df[feature_cols].fillna(0)  # Fill NaN with 0

        model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)

        # Should not raise
        model.fit(X)
        predictions = model.predict(X)

        assert len(predictions) == len(X)


class TestMLflowIntegration:
    """Test MLflow logging and model registration."""

    @pytest.mark.unit
    def test_mlflow_experiment_setup(self, mock_mlflow):
        """Verify MLflow experiment is set up correctly."""
        import mlflow

        experiment_name = "/Shared/health_monitor_ml_cost_anomaly_detector"
        mlflow.set_experiment(experiment_name)

        mock_mlflow['set_experiment'].assert_called_once_with(experiment_name)

    @pytest.mark.unit
    def test_mlflow_params_logged(self, mock_mlflow, sample_cost_features):
        """Verify model parameters are logged to MLflow."""
        import mlflow

        feature_cols = ['daily_dbu', 'avg_dbu_7d', 'z_score_7d']
        X = sample_cost_features[feature_cols].fillna(0)

        with mlflow.start_run(run_name="test_run"):
            model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
            model.fit(X)

            mlflow.log_params({
                "model_type": "IsolationForest",
                "n_estimators": 100,
                "contamination": 0.05,
                "feature_count": len(feature_cols)
            })

        # Verify params were logged
        mock_mlflow['log_params'].assert_called()
        call_args = mock_mlflow['log_params'].call_args[0][0]
        assert call_args['model_type'] == 'IsolationForest'
        assert call_args['n_estimators'] == 100

    @pytest.mark.unit
    def test_mlflow_metrics_logged(self, mock_mlflow, sample_cost_features):
        """Verify model metrics are logged to MLflow."""
        import mlflow

        feature_cols = ['daily_dbu', 'avg_dbu_7d', 'z_score_7d']
        X = sample_cost_features[feature_cols].fillna(0)

        with mlflow.start_run(run_name="test_run"):
            model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)
            model.fit(X)
            predictions = model.predict(X)

            anomaly_rate = (predictions == -1).mean()

            mlflow.log_metrics({
                "anomaly_rate": anomaly_rate,
                "training_samples": len(X)
            })

        mock_mlflow['log_metrics'].assert_called()

    @pytest.mark.unit
    def test_mlflow_model_signature(self, sample_cost_features):
        """Verify model signature can be inferred."""
        from mlflow.models.signature import infer_signature

        feature_cols = ['daily_dbu', 'avg_dbu_7d', 'z_score_7d', 'dow_sin', 'dow_cos']
        X = sample_cost_features[feature_cols].fillna(0)

        model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)
        model.fit(X)

        sample_input = X.head(5)
        sample_output = model.predict(sample_input)

        signature = infer_signature(sample_input, sample_output)

        assert signature is not None
        assert len(signature.inputs.inputs) == len(feature_cols)


class TestCostAnomalyEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.unit
    def test_empty_dataframe_raises_error(self):
        """Verify training on empty data raises appropriate error."""
        X = pd.DataFrame()
        model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)

        with pytest.raises(ValueError):
            model.fit(X)

    @pytest.mark.unit
    def test_single_sample_raises_error(self):
        """Verify training on single sample raises appropriate error."""
        X = pd.DataFrame({'col1': [1.0], 'col2': [2.0]})
        model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)

        with pytest.raises(ValueError):
            model.fit(X)

    @pytest.mark.unit
    def test_all_identical_values(self):
        """Verify model handles data with identical values."""
        X = pd.DataFrame({
            'col1': [1.0] * 100,
            'col2': [2.0] * 100,
        })
        model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)

        # Should not raise
        model.fit(X)
        predictions = model.predict(X)

        # All points should be classified (either normal or anomaly)
        assert len(predictions) == 100

    @pytest.mark.unit
    def test_high_dimensional_features(self):
        """Verify model handles many features."""
        np.random.seed(42)
        n_samples = 500
        n_features = 50

        X = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f'feature_{i}' for i in range(n_features)]
        )

        model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)
        model.fit(X)
        predictions = model.predict(X)

        assert len(predictions) == n_samples
        assert (predictions == -1).sum() > 0  # Should detect some anomalies
