"""
Evaluate saved models: regression metrics, correlation matrix,
direction classification (confusion matrix + ROC/AUC), and plots.

Run from repository root with:
    python3 backend/evaluate_models.py
"""
from pathlib import Path
import sys
import json
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error,
    confusion_matrix,
    accuracy_score,
    roc_curve,
    roc_auc_score,
)


BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from model_trainer import ModelTrainer
from data_loader import GoldDataLoader
from feature_engineering import FeatureEngineer


def regression_metrics(y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    return {'rmse': float(rmse), 'mae': float(mae), 'r2': float(r2), 'mape': float(mape)}


def ensure_reports_dir():
    reports_dir = BASE_DIR / 'reports'
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def plot_and_save_corr(df_full, feature_names, reports_dir, timestamp):
    # Correlation matrix for features + target (select numeric columns)
    # Try to find target column name containing 'gold_close' or 'close_gold'
    target_cols = [c for c in df_full.columns if 'gold_close' in c or 'close_gold' in c or 'close' in c]
    target_col = target_cols[0] if target_cols else None
    cols = feature_names.copy()
    if target_col and target_col not in cols:
        cols.append(target_col)

    corr = df_full[cols].corr()
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr, cmap='coolwarm', center=0)
    plt.title('Feature & Target Correlation Matrix')
    out = reports_dir / f'correlation_matrix_{timestamp}.png'
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def plot_predictions(y_true, y_pred, dates, reports_dir, model_name, timestamp):
    plt.figure(figsize=(12, 6))
    plt.plot(dates, y_true, label='Actual', linewidth=1)
    plt.plot(dates, y_pred, label='Predicted', linewidth=1)
    plt.legend()
    plt.title(f'Actual vs Predicted - {model_name}')
    plt.xlabel('Date')
    plt.ylabel('Price')
    out = reports_dir / f'pred_vs_actual_{model_name}_{timestamp}.png'
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def plot_residuals(y_true, y_pred, reports_dir, model_name, timestamp):
    residuals = y_true - y_pred
    plt.figure(figsize=(8, 5))
    sns.histplot(residuals, kde=True)
    plt.title(f'Residuals Distribution - {model_name}')
    out = reports_dir / f'residuals_{model_name}_{timestamp}.png'
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def plot_roc(actual_labels, scores, reports_dir, model_name, timestamp):
    fpr, tpr, _ = roc_curve(actual_labels, scores)
    auc = roc_auc_score(actual_labels, scores)
    plt.figure(figsize=(6, 6))
    plt.plot(fpr, tpr, label=f'AUC = {auc:.3f}')
    plt.plot([0, 1], [0, 1], '--', color='gray')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC Curve - {model_name}')
    plt.legend()
    out = reports_dir / f'roc_{model_name}_{timestamp}.png'
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out, auc


def evaluate():
    reports_dir = ensure_reports_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Load and prepare data
    loader = GoldDataLoader()
    df = loader.load_financial_regression_data()
    df = loader.clean_data(df)

    engineer = FeatureEngineer(df)
    df_features = engineer.create_all_features()

    data = loader.prepare_data_for_modeling(df_features)
    X_test = data['X_test']
    y_test = data['y_test']
    dates_test = pd.to_datetime(data['dates_test'])
    feature_names = data['feature_names']

    # Load models (from backend/models/saved_models by default)
    trainer = ModelTrainer(model_dir=BASE_DIR / 'models' / 'saved_models')
    models = trainer.load_models()  # uses most recent timestamp

    results = {}

    for model_id, model in models.items():
        # Apply scaler if present
        X_input = X_test
        scaler = trainer.scalers.get(model_id)
        if scaler is not None:
            X_input = scaler.transform(X_test)

        y_pred = model.predict(X_input)

        # Regression metrics
        reg_metrics = regression_metrics(y_test, y_pred)

        # Save prediction plots
        pred_plot = plot_predictions(y_test, y_pred, dates_test, reports_dir, model_id, timestamp)
        resid_plot = plot_residuals(y_test, y_pred, reports_dir, model_id, timestamp)

        # Direction classification: compare sign of next-step change using previous true value
        # Build labels for t=1..n-1 using previous true value as reference
        if len(y_test) > 1:
            y_prev = y_test[:-1]
            actual_next = y_test[1:]
            pred_next = y_pred[1:]

            actual_dir = (actual_next - y_prev) > 0
            pred_dir = (pred_next - y_prev) > 0

            acc = float(accuracy_score(actual_dir, pred_dir))
            cm = confusion_matrix(actual_dir, pred_dir).tolist()

            # For ROC/AUC use predicted delta as score
            scores = (pred_next - y_prev)
            try:
                auc = float(roc_auc_score(actual_dir, scores))
            except Exception:
                auc = None

            # Save ROC plot if possible
            roc_path = None
            if auc is not None:
                roc_path, auc_val = plot_roc(actual_dir.astype(int), scores, reports_dir, model_id, timestamp)
            else:
                auc_val = None
        else:
            acc = None
            cm = None
            auc_val = None
            roc_path = None

        results[model_id] = {
            'regression_metrics': reg_metrics,
            'direction_accuracy': acc,
            'confusion_matrix': cm,
            'roc_auc': auc_val,
            'plots': {
                'predictions': str(pred_plot),
                'residuals': str(resid_plot),
                'roc': str(roc_path) if roc_path else None,
            }
        }

    # Correlation matrix (using df_features and feature names)
    corr_path = plot_and_save_corr(df_features, feature_names, reports_dir, timestamp)

    out = reports_dir / f'metrics_summary_{timestamp}.json'
    with open(out, 'w') as f:
        json.dump({'timestamp': timestamp, 'results': results, 'correlation_plot': str(corr_path)}, f, indent=2)

    print(f"Saved evaluation summary to {out}")
    for mid, info in results.items():
        print(f"\nModel: {mid}")
        print("Regression metrics:")
        for k, v in info['regression_metrics'].items():
            print(f"  {k}: {v}")
        if info['direction_accuracy'] is not None:
            print(f"Direction accuracy: {info['direction_accuracy']}")
            print(f"Confusion matrix: {info['confusion_matrix']}")
            print(f"ROC AUC: {info['roc_auc']}")
        print(f"Plots: {info['plots']}")


if __name__ == '__main__':
    evaluate()
