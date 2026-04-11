"""
Model Training Module
Trains Linear Regression, Random Forest, and XGBoost models
Handles evaluation and model persistence
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
import joblib
import json
from pathlib import Path
from datetime import datetime


class ModelTrainer:
    """Train and evaluate gold price prediction models"""
    
    def __init__(self, model_dir='./models/saved_models'):
        """Initialize trainer with model save directory"""
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.scalers = {}
        self.predictions = {}
        self.metrics = {}
    
    def train_linear_regression(self, X_train, y_train, X_test, y_test):
        """Train Linear Regression model"""
        print("\n" + "="*50)
        print("Training Linear Regression...")
        print("="*50)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train
        model = LinearRegression()
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_train_pred = model.predict(X_train_scaled)
        y_test_pred = model.predict(X_test_scaled)
        
        train_metrics = self._calculate_metrics(y_train, y_train_pred, 'Linear Regression', 'Train')
        test_metrics = self._calculate_metrics(y_test, y_test_pred, 'Linear Regression', 'Test')
        
        self.models['linear_regression'] = model
        self.scalers['linear_regression'] = scaler
        self.predictions['linear_regression'] = y_test_pred
        self.metrics['linear_regression'] = {
            'train': train_metrics,
            'test': test_metrics,
            'feature_importance': None,
        }
        
        return model, test_metrics
    
    def train_random_forest(self, X_train, y_train, X_test, y_test):
        """Train Random Forest model"""
        print("\n" + "="*50)
        print("Training Random Forest...")
        print("="*50)
        
        # Train (no scaling needed for tree-based)
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        train_metrics = self._calculate_metrics(y_train, y_train_pred, 'Random Forest', 'Train')
        test_metrics = self._calculate_metrics(y_test, y_test_pred, 'Random Forest', 'Test')
        
        # Get feature importance
        feature_importance = model.feature_importances_
        
        self.models['random_forest'] = model
        self.predictions['random_forest'] = y_test_pred
        self.metrics['random_forest'] = {
            'train': train_metrics,
            'test': test_metrics,
            'feature_importance': feature_importance,
        }
        
        return model, test_metrics
    
    def train_xgboost(self, X_train, y_train, X_test, y_test):
        """Train XGBoost model"""
        print("\n" + "="*50)
        print("Training XGBoost...")
        print("="*50)
        
        # Train
        model = XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            verbosity=1,
            tree_method='hist'
        )
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        
        # Evaluate
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        train_metrics = self._calculate_metrics(y_train, y_train_pred, 'XGBoost', 'Train')
        test_metrics = self._calculate_metrics(y_test, y_test_pred, 'XGBoost', 'Test')
        
        # Get feature importance
        feature_importance = model.feature_importances_
        
        self.models['xgboost'] = model
        self.predictions['xgboost'] = y_test_pred
        self.metrics['xgboost'] = {
            'train': train_metrics,
            'test': test_metrics,
            'feature_importance': feature_importance,
        }
        
        return model, test_metrics
    
    def _calculate_metrics(self, y_true, y_pred, model_name, set_name):
        """Calculate evaluation metrics"""
        
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        mape = mean_absolute_percentage_error(y_true, y_pred)
        
        metrics_dict = {
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2),
            'mape': float(mape),
            'samples': int(len(y_true)),
        }
        
        print(f"{model_name} - {set_name}:")
        print(f"  RMSE: ${rmse:.2f}")
        print(f"  MAE:  ${mae:.2f}")
        print(f"  R²:   {r2:.4f}")
        print(f"  MAPE: {mape:.4f}")
        
        return metrics_dict
    
    def train_all_models(self, X_train, y_train, X_test, y_test):
        """Train all three models"""
        
        print("\n" + "="*70)
        print("TRAINING ALL MODELS")
        print("="*70)
        
        lr_model, lr_metrics = self.train_linear_regression(X_train, y_train, X_test, y_test)
        rf_model, rf_metrics = self.train_random_forest(X_train, y_train, X_test, y_test)
        xgb_model, xgb_metrics = self.train_xgboost(X_train, y_train, X_test, y_test)
        
        print("\n" + "="*70)
        print("MODEL COMPARISON (Test Set)")
        print("="*70)
        for name, metrics in [('Linear Regression', lr_metrics), ('Random Forest', rf_metrics), ('XGBoost', xgb_metrics)]:
            print(f"\n{name}:")
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
        
        return self.models, self.metrics
    
    def save_models(self):
        """Save trained models to disk"""
        print("\n" + "="*50)
        print("Saving models...")
        print("="*50)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save models
        for model_name, model in self.models.items():
            filepath = self.model_dir / f"{model_name}_{timestamp}.pkl"
            joblib.dump(model, filepath)
            print(f"✓ Saved {model_name} to {filepath}")
        
        # Save scalers
        for scaler_name, scaler in self.scalers.items():
            filepath = self.model_dir / f"{scaler_name}_scaler_{timestamp}.pkl"
            joblib.dump(scaler, filepath)
            print(f"✓ Saved {scaler_name} scaler to {filepath}")
        
        # Save metrics
        metrics_filepath = self.model_dir / f"metrics_{timestamp}.json"
        
        # Convert numpy arrays to lists for JSON serialization
        metrics_to_save = {}
        for model_name, model_metrics in self.metrics.items():
            metrics_to_save[model_name] = {}
            for metric_name, value in model_metrics.items():
                if isinstance(value, np.ndarray):
                    metrics_to_save[model_name][metric_name] = value.tolist()
                elif isinstance(value, (np.integer, np.floating)):
                    metrics_to_save[model_name][metric_name] = float(value)
                else:
                    metrics_to_save[model_name][metric_name] = value
        
        with open(metrics_filepath, 'w') as f:
            json.dump(metrics_to_save, f, indent=2)
        print(f"✓ Saved metrics to {metrics_filepath}")
        
        return timestamp
    
    def load_models(self, timestamp=None):
        """Load most recent models from disk"""
        
        if timestamp is None:
            # Find most recent full saved run using metrics files.
            # This avoids accidentally selecting scaler files as model checkpoints.
            metrics_files = sorted(self.model_dir.glob("metrics_*.json"))
            if not metrics_files:
                raise FileNotFoundError("No saved models found")

            most_recent = metrics_files[-1]
            timestamp = most_recent.stem.replace("metrics_", "", 1)
        
        print(f"\nLoading models from timestamp {timestamp}...")
        
        for model_name in ['linear_regression', 'random_forest', 'xgboost']:
            filepath = self.model_dir / f"{model_name}_{timestamp}.pkl"
            if filepath.exists():
                self.models[model_name] = joblib.load(filepath)
                print(f"✓ Loaded {model_name}")
            else:
                raise FileNotFoundError(f"Missing model file: {filepath}")
        
        # Load scalers
        for scaler_name in ['linear_regression']:
            filepath = self.model_dir / f"{scaler_name}_scaler_{timestamp}.pkl"
            if filepath.exists():
                self.scalers[scaler_name] = joblib.load(filepath)
        
        # Load metrics
        metrics_filepath = self.model_dir / f"metrics_{timestamp}.json"
        if metrics_filepath.exists():
            with open(metrics_filepath, 'r') as f:
                self.metrics = json.load(f)
        else:
            raise FileNotFoundError(f"Missing metrics file: {metrics_filepath}")
        
        return self.models
    
    def get_model_summary(self):
        """Get summary of all models for API response"""
        
        summary = []
        
        for model_name, metrics_data in self.metrics.items():
            test_metrics = metrics_data.get('test', {})
            
            summary.append({
                'name': model_name.replace('_', ' ').title(),
                'model_id': model_name,
                'metrics': test_metrics,
                'trained': True,
            })
        
        # Sort by R² score descending
        summary.sort(key=lambda x: x['metrics'].get('r2', 0), reverse=True)
        
        return summary
    
    def get_feature_importance(self, model_name=None, top_n=20):
        """
        Get feature importance from trained models
        
        Args:
            model_name: Which model to get importance from ('random_forest', 'xgboost', or None for best)
            top_n: Number of top features to return
            
        Returns:
            list: Top features with importance scores
        """
        
        if model_name is None:
            # Use best model (likely XGBoost)
            model_name = 'xgboost'
        
        if model_name not in self.metrics:
            return []
        
        feature_importance = self.metrics[model_name]['feature_importance']
        
        if feature_importance is None:
            return []
        
        # Get top features
        top_indices = np.argsort(feature_importance)[-top_n:][::-1]
        top_features = [
            {
                'rank': i + 1,
                'feature': f'Feature_{idx}',
                'importance': float(feature_importance[idx]),
            }
            for i, idx in enumerate(top_indices)
        ]
        
        return top_features


def main():
    """Test model training"""
    from data_loader import GoldDataLoader
    from feature_engineering import FeatureEngineer
    
    # Load and prepare data
    loader = GoldDataLoader()
    df = loader.load_financial_regression_data()
    df = loader.clean_data(df)
    
    # Engineer features
    engineer = FeatureEngineer(df)
    df = engineer.create_all_features()
    
    # Prepare for modeling
    data = loader.prepare_data_for_modeling(df)
    
    # Train models
    trainer = ModelTrainer()
    trainer.train_all_models(data['X_train'], data['y_train'], data['X_test'], data['y_test'])
    
    # Save models
    trainer.save_models()
    
    # Get summary
    summary = trainer.get_model_summary()
    print("\nModel Summary:")
    for model_info in summary:
        print(f"\n{model_info['name']}:")
        print(f"  R²: {model_info['metrics']['r2']:.4f}")
        print(f"  RMSE: ${model_info['metrics']['rmse']:.2f}")


if __name__ == '__main__':
    main()
