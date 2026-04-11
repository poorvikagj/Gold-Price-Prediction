# Gold Price Prediction - ML Web Application

An end-to-end machine learning project for gold price forecasting with a Flask backend and React frontend.

## Project Overview

This project demonstrates:
- Data loading and preprocessing for multi-asset financial data
- Feature engineering with technical and time-series features
- Training and comparison of 3 regression models
- Serving predictions and metrics through a REST API
- Interactive visualization in a frontend dashboard

## Latest Results (April 11, 2026)

Source artifacts:
- models/saved_models/metrics_20260411_105936.json
- results/forecasts/analysis_summary.json
- results/forecasts/predictions_2025_best_model.csv
- results/forecasts/predictions_2025_all_models.csv

### Model Test Metrics

| Model | Test R2 | RMSE | MAE | MAPE |
|---|---:|---:|---:|---:|
| Linear Regression | 0.999952 | 0.1554 | 0.1163 | 0.0617% |
| Random Forest | 0.436571 | 16.8328 | 7.7581 | 3.4706% |
| XGBoost | 0.363863 | 17.8860 | 8.4647 | 3.8051% |

Best model from latest run: Linear Regression

### 2025 Forecast Summary

- Forecast horizon: 365 daily points
- Best model used for final forecast: linear_regression
- Predicted USD range: 2923.93 to 3501.61
- Predicted USD mean: 3458.32
- Min predicted day: 2025-01-01
- Max predicted day: 2025-01-07
- Annual fit mean percent error: 0.2824%
- Annual fit max percent error: 2.1242%

Note on scale:
The underlying target series appears to be a derived/scaled instrument rather than direct spot gold USD/oz. The forecast pipeline includes conversion to a USD scale and writes both forms in output CSV files.

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+

### 1. Setup

Run the full setup:

```bash
bash setup.sh
```

### 2. Start the App

Single command:

```bash
bash run.sh
```

Or start manually.

Backend:

```bash
cd backend
python app.py
```

Frontend:

```bash
cd frontend
npm run dev
```

### 3. Open in Browser
- Frontend: http://localhost:3000
- API: http://localhost:5000

## API Endpoints

- GET /api/models
- GET /api/predictions
- GET /api/feature-importance
- GET /api/metrics
- GET /api/data-stats

## Project Structure

```text
gold-price-prediction/
|- backend/
|  |- app.py
|  |- data_loader.py
|  |- feature_engineering.py
|  |- model_trainer.py
|  |- data/raw/
|  \- models/saved_models/
|- frontend/
|  |- src/
|  |- public/
|  \- package.json
|- data/
|- models/
|- results/
|- scripts/
|- setup.sh
|- run.sh
\- README.md
```

## Troubleshooting

- Backend not running: start backend/app.py first
- Frontend cannot call API: verify backend on port 5000
- Missing Python packages: pip install -r requirements.txt
- Missing Node packages: cd frontend && npm install

## Current Status

The repository includes trained models, generated forecasts for 2025, and a working frontend-backend stack for exploration and visualization.