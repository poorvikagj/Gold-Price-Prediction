"""
Flask API for Gold Price Prediction
Exposes ML models and predictions via REST endpoints
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
from pathlib import Path
import logging
from sklearn.isotonic import IsotonicRegression
from pandas.tseries.offsets import BDay

from data_loader import GoldDataLoader
from feature_engineering import FeatureEngineer
from model_trainer import ModelTrainer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables for models and data
loader = None
engineer = None
trainer = None
data_cache = {}
predictions_cache = {}

REFERENCE_GOLD_USD_BY_YEAR = {
    2010: 1224.0,
    2011: 1571.0,
    2012: 1668.0,
    2013: 1411.0,
    2014: 1266.0,
    2015: 1160.0,
    2016: 1251.0,
    2017: 1257.0,
    2018: 1268.0,
    2019: 1393.0,
    2020: 1769.0,
    2021: 1799.0,
    2022: 1800.0,
    2023: 1943.0,
    2024: 2386.0,
}


def _infer_raw_target_column(df):
    """Infer target column from raw (pre-feature-engineering) dataset."""
    for candidate in ['gold close', 'gold_close', 'Close_gold']:
        if candidate in df.columns:
            return candidate
    raise ValueError('Raw target column not found in dataset')


def _fit_usd_transform(raw_df, date_col='Date'):
    """Fit monotonic mapping from original scale to USD/oz using annual anchors."""
    close_col = _infer_raw_target_column(raw_df)
    work = raw_df[[date_col, close_col]].copy()
    work[date_col] = pd.to_datetime(work[date_col])
    work['year'] = work[date_col].dt.year

    annual_orig = work.groupby('year', as_index=False)[close_col].mean().rename(
        columns={close_col: 'orig_annual_mean'}
    )
    ref = pd.DataFrame({
        'year': list(REFERENCE_GOLD_USD_BY_YEAR.keys()),
        'ref_usd_annual_mean': list(REFERENCE_GOLD_USD_BY_YEAR.values()),
    })
    annual_fit = annual_orig.merge(ref, on='year', how='inner').sort_values('year')
    if len(annual_fit) < 5:
        raise ValueError('Not enough overlapping years for USD transformation')

    iso = IsotonicRegression(increasing=True, out_of_bounds='clip')
    iso.fit(annual_fit['orig_annual_mean'].values, annual_fit['ref_usd_annual_mean'].values)

    x_fit = annual_fit['orig_annual_mean'].to_numpy(dtype=float)
    y_fit = annual_fit['ref_usd_annual_mean'].to_numpy(dtype=float)

    x_min, x_max = float(x_fit.min()), float(x_fit.max())
    y_min = float(y_fit[np.argmin(x_fit)])
    y_max = float(y_fit[np.argmax(x_fit)])

    k = min(4, len(x_fit))
    low_idx = np.argsort(x_fit)[:k]
    high_idx = np.argsort(x_fit)[-k:]
    low_slope = float(np.polyfit(x_fit[low_idx], y_fit[low_idx], 1)[0]) if k >= 2 else 8.0
    high_slope = float(np.polyfit(x_fit[high_idx], y_fit[high_idx], 1)[0]) if k >= 2 else 8.0

    return {
        'iso': iso,
        'x_min': x_min,
        'x_max': x_max,
        'y_min': y_min,
        'y_max': y_max,
        'low_slope': low_slope,
        'high_slope': high_slope,
        'raw_target_col': close_col,
    }


def _to_usd(values):
    """Transform original-scale values to estimated USD/oz."""
    transform = data_cache.get('usd_transform')
    if not transform:
        return np.asarray(values, dtype=float)

    x = np.asarray(values, dtype=float)
    x_min, x_max = transform['x_min'], transform['x_max']
    y_min, y_max = transform['y_min'], transform['y_max']
    low_slope, high_slope = transform['low_slope'], transform['high_slope']
    iso = transform['iso']

    clipped = np.clip(x, x_min, x_max)
    y = iso.predict(clipped)

    low_mask = x < x_min
    high_mask = x > x_max
    if np.any(low_mask):
        y[low_mask] = y_min + low_slope * (x[low_mask] - x_min)
    if np.any(high_mask):
        y[high_mask] = y_max + high_slope * (x[high_mask] - x_max)

    return y


def _infer_target_column(df):
    """Infer the target column used during model training."""
    for candidate in ['gold_close', 'Close_gold', 'close_gold']:
        if candidate in df.columns:
            return candidate
    raise ValueError('Target column not found in dataset')


def _compute_rsi_from_history(history, period=14):
    """Compute RSI using a recent price history list."""
    if len(history) <= period:
        return 50.0

    prices = pd.Series(history[-(period + 1):], dtype=float)
    delta = prices.diff().dropna()
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)

    avg_gain = gains.mean()
    avg_loss = losses.mean()
    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def _build_forecast_features(base_features, history, feature_names):
    """Build one-step-ahead feature vector from recent target history."""
    features = base_features.copy()
    last_price = float(history[-1])

    # Update lag features with most recent recursive history.
    for lag in [1, 2, 3, 5, 7]:
        col = f'Lag_gold_close_{lag}'
        if col in feature_names:
            features[col] = float(history[-lag]) if len(history) >= lag else last_price

    # Update rolling statistics for gold features.
    for window in [7, 14, 30]:
        window_prices = history[-min(window, len(history)):]
        mean_val = float(np.mean(window_prices))
        std_val = float(np.std(window_prices))
        min_val = float(np.min(window_prices))
        max_val = float(np.max(window_prices))

        if f'Rolling_Mean_gold_{window}' in feature_names:
            features[f'Rolling_Mean_gold_{window}'] = mean_val
        if f'Rolling_Std_gold_{window}' in feature_names:
            features[f'Rolling_Std_gold_{window}'] = std_val
        if f'Rolling_Min_gold_{window}' in feature_names:
            features[f'Rolling_Min_gold_{window}'] = min_val
        if f'Rolling_Max_gold_{window}' in feature_names:
            features[f'Rolling_Max_gold_{window}'] = max_val

    # Technical indicators derived from target history.
    for period in [10, 20, 50]:
        col = f'SMA_gold_{period}'
        if col in feature_names:
            window_prices = history[-min(period, len(history)):]
            features[col] = float(np.mean(window_prices))

    for period in [10, 20]:
        col = f'EMA_gold_{period}'
        if col in feature_names:
            prev_ema = float(features.get(col, last_price))
            alpha = 2.0 / (period + 1)
            features[col] = float(alpha * last_price + (1 - alpha) * prev_ema)

    if 'RSI_gold_14' in feature_names:
        features['RSI_gold_14'] = _compute_rsi_from_history(history, period=14)

    if 'Returns_gold' in feature_names:
        prev_price = float(history[-2]) if len(history) >= 2 else last_price
        features['Returns_gold'] = float((last_price - prev_price) / prev_price) if prev_price != 0 else 0.0

    if 'Volatility_gold_20' in feature_names:
        if len(history) >= 3:
            returns = pd.Series(history, dtype=float).pct_change().dropna().tail(20)
            features['Volatility_gold_20'] = float(returns.std()) if len(returns) else 0.0
        else:
            features['Volatility_gold_20'] = 0.0

    # Approximate MACD dynamics from recursive history.
    if 'MACD_gold' in feature_names or 'MACD_Signal_gold' in feature_names or 'MACD_Hist_gold' in feature_names:
        prev_ema12 = float(features.get('EMA_gold_12', last_price))
        prev_ema26 = float(features.get('EMA_gold_26', last_price))
        ema12 = (2.0 / 13.0) * last_price + (11.0 / 13.0) * prev_ema12
        ema26 = (2.0 / 27.0) * last_price + (25.0 / 27.0) * prev_ema26
        macd = float(ema12 - ema26)
        prev_signal = float(features.get('MACD_Signal_gold', macd))
        signal = (2.0 / 10.0) * macd + (8.0 / 10.0) * prev_signal

        if 'EMA_gold_12' in feature_names:
            features['EMA_gold_12'] = float(ema12)
        if 'EMA_gold_26' in feature_names:
            features['EMA_gold_26'] = float(ema26)
        if 'MACD_gold' in feature_names:
            features['MACD_gold'] = macd
        if 'MACD_Signal_gold' in feature_names:
            features['MACD_Signal_gold'] = float(signal)
        if 'MACD_Hist_gold' in feature_names:
            features['MACD_Hist_gold'] = float(macd - signal)

    # Approximate Bollinger bands from recursive history.
    if any(col in feature_names for col in ['BB_Upper_gold', 'BB_Lower_gold', 'BB_Middle_gold', 'BB_Width_gold']):
        bb_window = history[-min(20, len(history)):]
        bb_mean = float(np.mean(bb_window))
        bb_std = float(np.std(bb_window))
        if 'BB_Middle_gold' in feature_names:
            features['BB_Middle_gold'] = bb_mean
        if 'BB_Upper_gold' in feature_names:
            features['BB_Upper_gold'] = bb_mean + 2 * bb_std
        if 'BB_Lower_gold' in feature_names:
            features['BB_Lower_gold'] = bb_mean - 2 * bb_std
        if 'BB_Width_gold' in feature_names:
            features['BB_Width_gold'] = 4 * bb_std

    # Update leaked same-day gold features if present to avoid a completely static vector.
    for col in ['gold_open', 'gold_high', 'gold_low']:
        if col in feature_names:
            features[col] = last_price

    # Keep cross-asset ratios coherent where gold appears.
    if 'Ratio_Gold_Silver' in feature_names and 'silver_close' in features:
        denom = float(features['silver_close']) + 1e-9
        features['Ratio_Gold_Silver'] = last_price / denom
    if 'Ratio_Gold_Platinum' in feature_names and 'platinum_close' in features:
        denom = float(features['platinum_close']) + 1e-9
        features['Ratio_Gold_Platinum'] = last_price / denom
    if 'Ratio_Gold_Oil' in feature_names and 'oil_close' in features:
        denom = float(features['oil_close']) + 1e-9
        features['Ratio_Gold_Oil'] = last_price / denom

    return features


def initialize_app():
    """Initialize app with models and data"""
    global loader, engineer, trainer, data_cache, predictions_cache
    
    logger.info("Initializing application...")
    
    # Load data
    loader = GoldDataLoader()
    raw_df = loader.load_financial_regression_data()
    raw_df = loader.clean_data(raw_df)

    date_col_raw = 'Date' if 'Date' in raw_df.columns else 'date'
    data_cache['usd_transform'] = _fit_usd_transform(raw_df, date_col=date_col_raw)
    
    # Engineer features
    engineer = FeatureEngineer(raw_df)
    df = engineer.create_all_features()
    
    # Prepare for modeling
    data_cache['data'] = loader.prepare_data_for_modeling(df)
    data_cache['stats'] = loader.get_data_statistics(df)
    data_cache['feature_categories'] = engineer.get_feature_categories()

    target_col = _infer_target_column(df)
    last_orig = float(df[target_col].iloc[-1])
    last_usd = float(_to_usd(np.array([last_orig]))[0])
    data_cache['stats']['display_date_range'] = f"{data_cache['stats']['date_min']} to {data_cache['stats']['date_max']}"
    data_cache['stats']['price_unit'] = 'USD per troy ounce (estimated)'
    data_cache['stats']['target_original_range'] = {
        'min': float(df[target_col].min()),
        'max': float(df[target_col].max()),
    }
    data_cache['stats']['last_observed'] = {
        'date': data_cache['stats']['date_max'],
        'original_scale': last_orig,
        'usd_estimated': last_usd,
    }
    
    # Load or train models
    trainer = ModelTrainer(model_dir='./models/saved_models')
    
    try:
        trainer.load_models()
        # Recreate test-set predictions for API endpoints when loading from disk.
        X_test = data_cache['data']['X_test']
        for model_name, model in trainer.models.items():
            X_input = X_test
            if model_name == 'linear_regression' and model_name in trainer.scalers:
                X_input = trainer.scalers[model_name].transform(X_test)
            trainer.predictions[model_name] = model.predict(X_input)
        logger.info("Models loaded from disk")
    except FileNotFoundError:
        logger.info("No saved models found, training new models...")
        data = data_cache['data']
        trainer.train_all_models(data['X_train'], data['y_train'], data['X_test'], data['y_test'])
        trainer.save_models()
        logger.info("Models trained and saved")
    
    # Cache predictions
    data = data_cache['data']
    for model_name in ['linear_regression', 'random_forest', 'xgboost']:
        if model_name in trainer.predictions:
            predictions_cache[model_name] = {
                'predictions': trainer.predictions[model_name],
                'dates': data['dates_test'],
                'actual': data['y_test'],
            }
    
    logger.info("Application initialized successfully")


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200


@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of all trained models with metrics"""
    try:
        models_summary = trainer.get_model_summary()
        return jsonify({
            'success': True,
            'data': models_summary,
        }), 200
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """Get predictions for test period"""
    try:
        # Get query parameters
        model_id = request.args.get('model', 'linear_regression')
        limit = request.args.get('limit', 100, type=int)
        
        if model_id not in predictions_cache:
            return jsonify({'success': False, 'error': f'Model {model_id} not found'}), 404
        
        pred_data = predictions_cache[model_id]
        
        # Convert to list for JSON
        predictions = []
        for i in range(len(pred_data['predictions'])):
            date_str = pd.Timestamp(pred_data['dates'][i]).strftime('%Y-%m-%d')
            actual_orig = float(pred_data['actual'][i])
            predicted_orig = float(pred_data['predictions'][i])
            actual_usd = float(_to_usd(np.array([actual_orig]))[0])
            predicted_usd = float(_to_usd(np.array([predicted_orig]))[0])
            predictions.append({
                'date': date_str,
                'actual': actual_usd,
                'predicted': predicted_usd,
                'actual_original': actual_orig,
                'predicted_original': predicted_orig,
                'error': float(actual_usd - predicted_usd),
                'error_pct': float((actual_usd - predicted_usd) / actual_usd * 100) if actual_usd != 0 else 0,
            })
        
        # Limit results
        predictions = predictions[-limit:]
        
        return jsonify({
            'success': True,
            'model': model_id,
            'data': predictions,
            'count': len(predictions),
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting predictions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    """Get current and future recursive forecasts for a selected model."""
    try:
        model_id = request.args.get('model', 'linear_regression')
        horizon = request.args.get('horizon', 180, type=int)
        horizon = max(1, min(horizon, 180))

        if model_id not in trainer.models:
            return jsonify({'success': False, 'error': f'Model {model_id} not found'}), 404

        data = data_cache['data']
        df_full = data['df_full']
        feature_names = data['feature_names']
        date_col = 'Date' if 'Date' in df_full.columns else 'date'
        target_col = _infer_target_column(df_full)

        model = trainer.models[model_id]

        # Start from the latest engineered feature row.
        base_row = df_full.iloc[-1]
        base_features = {}
        for feature in feature_names:
            value = base_row[feature] if feature in base_row else 0.0
            if isinstance(value, (np.integer, np.floating, int, float)):
                base_features[feature] = float(value)
            else:
                base_features[feature] = 0.0

        # Current prediction from latest available engineered row.
        current_x = np.array([[base_features[f] for f in feature_names]], dtype=float)
        if model_id == 'linear_regression' and model_id in trainer.scalers:
            current_x = trainer.scalers[model_id].transform(current_x)
        current_prediction = float(model.predict(current_x)[0])

        # Recursive multi-step forecast.
        history = df_full[target_col].tail(120).astype(float).tolist()
        last_date = pd.Timestamp(df_full[date_col].iloc[-1])
        start_date = last_date + BDay(1)
        forecast_days = pd.date_range(start=start_date, periods=horizon, freq='B')

        future = []
        rolling_features = base_features.copy()
        for idx, future_date in enumerate(forecast_days, start=1):
            rolling_features = _build_forecast_features(rolling_features, history, feature_names)
            x_future = np.array([[rolling_features[f] for f in feature_names]], dtype=float)
            if model_id == 'linear_regression' and model_id in trainer.scalers:
                x_future = trainer.scalers[model_id].transform(x_future)

            prediction = float(model.predict(x_future)[0])
            prediction_usd = float(_to_usd(np.array([prediction]))[0])
            future.append({
                'date': future_date.strftime('%Y-%m-%d'),
                'predicted': prediction_usd,
                'predicted_original': prediction,
                'day_ahead': idx,
            })
            history.append(prediction)

        rmse = float(trainer.metrics.get(model_id, {}).get('test', {}).get('rmse', 0.0))
        # RMSE is in model-original units. Convert to an approximate USD band at the current prediction.
        high_usd = float(_to_usd(np.array([current_prediction + rmse]))[0])
        low_usd = float(_to_usd(np.array([current_prediction - rmse]))[0])
        rmse_usd = abs(high_usd - low_usd) / 2.0

        return jsonify({
            'success': True,
            'model': model_id,
            'horizon': horizon,
            'last_observed_date': last_date.strftime('%Y-%m-%d'),
            'last_observed_price': float(_to_usd(np.array([float(df_full[target_col].iloc[-1])]))[0]),
            'last_observed_price_original': float(df_full[target_col].iloc[-1]),
            'current_prediction': float(_to_usd(np.array([current_prediction]))[0]),
            'current_prediction_original': current_prediction,
            'price_unit': 'USD per troy ounce (estimated)',
            'forecast_start_date': start_date.strftime('%Y-%m-%d'),
            'forecast': future,
            'uncertainty_band': {
                'plus_minus_rmse': rmse_usd,
                'plus_minus_rmse_original': rmse,
            },
        }), 200

    except Exception as e:
        logger.error(f"Error creating forecast: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get model performance metrics"""
    try:
        metrics = {}
        for model_name, model_metrics in trainer.metrics.items():
            metrics[model_name] = {
                'train': model_metrics.get('train', {}),
                'test': model_metrics.get('test', {}),
            }
        
        return jsonify({
            'success': True,
            'data': metrics,
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feature-importance', methods=['GET'])
def get_feature_importance():
    """Get top features by importance"""
    try:
        model_id = request.args.get('model', 'linear_regression')
        top_n = request.args.get('top_n', 20, type=int)
        
        features = trainer.get_feature_importance(model_id, top_n)
        
        return jsonify({
            'success': True,
            'model': model_id,
            'top_n': top_n,
            'data': features,
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting feature importance: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data-stats', methods=['GET'])
def get_data_stats():
    """Get dataset statistics"""
    try:
        stats = data_cache['stats']
        feature_categories = data_cache['feature_categories']
        
        return jsonify({
            'success': True,
            'data': {
                'rows': stats['rows'],
                'columns': stats['columns'],
                'date_range': stats['date_range'],
                'display_date_range': stats.get('display_date_range', stats['date_range']),
                'date_min': stats['date_min'],
                'date_max': stats['date_max'],
                'feature_count': len(stats['features']),
                'feature_categories': {k: len(v) for k, v in feature_categories.items()},
                'total_dataset_features': sum(len(v) for v in feature_categories.values()),
                'price_unit': stats.get('price_unit', 'USD per troy ounce (estimated)'),
                'target_original_range': stats.get('target_original_range', {}),
                'last_observed': stats.get('last_observed', {}),
            },
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting data stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict():
    """Make prediction for custom input"""
    try:
        data = request.get_json()
        model_id = data.get('model', 'linear_regression')
        features = data.get('features')  # Array of feature values
        
        if model_id not in trainer.models:
            return jsonify({'success': False, 'error': f'Model {model_id} not found'}), 404
        
        if not features:
            return jsonify({'success': False, 'error': 'Features required'}), 400
        
        # Make prediction
        model = trainer.models[model_id]
        X = np.array([features])
        
        # Apply scaling if needed (Linear Regression)
        if model_id == 'linear_regression' and model_id in trainer.scalers:
            scaler = trainer.scalers[model_id]
            X = scaler.transform(X)
        
        prediction = model.predict(X)[0]
        
        return jsonify({
            'success': True,
            'model': model_id,
            'prediction': float(prediction),
        }), 200
    
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/model-comparison', methods=['GET'])
def model_comparison():
    """Get detailed model comparison"""
    try:
        comparison = []
        
        for model_name, metrics_data in trainer.metrics.items():
            test_metrics = metrics_data.get('test', {})
            train_metrics = metrics_data.get('train', {})
            
            comparison.append({
                'model': model_name.replace('_', ' ').title(),
                'model_id': model_name,
                'train_r2': train_metrics.get('r2', 0),
                'test_r2': test_metrics.get('r2', 0),
                'train_rmse': train_metrics.get('rmse', 0),
                'test_rmse': test_metrics.get('rmse', 0),
                'train_mae': train_metrics.get('mae', 0),
                'test_mae': test_metrics.get('mae', 0),
                'test_mape': test_metrics.get('mape', 0),
                'test_samples': test_metrics.get('samples', 0),
            })
        
        # Sort by test R² descending
        comparison.sort(key=lambda x: x['test_r2'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': comparison,
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting model comparison: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/error-analysis', methods=['GET'])
def error_analysis():
    """Get error statistics for predictions"""
    try:
        model_id = request.args.get('model', 'linear_regression')
        
        if model_id not in predictions_cache:
            return jsonify({'success': False, 'error': f'Model {model_id} not found'}), 404
        
        pred_data = predictions_cache[model_id]
        errors = pred_data['actual'] - pred_data['predictions']
        
        error_stats = {
            'mean_error': float(np.mean(errors)),
            'std_error': float(np.std(errors)),
            'min_error': float(np.min(errors)),
            'max_error': float(np.max(errors)),
            'rmse': float(np.sqrt(np.mean(errors**2))),
            'count': int(len(errors)),
        }
        
        # Error distribution (percentiles)
        percentiles = [10, 25, 50, 75, 90]
        error_distribution = {
            f'p{p}': float(np.percentile(errors, p))
            for p in percentiles
        }
        
        return jsonify({
            'success': True,
            'model': model_id,
            'error_stats': error_stats,
            'error_distribution': error_distribution,
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing errors: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Initialize app
    initialize_app()
    
    # Run Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)
