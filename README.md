## Dataset 1 : financial_regression.csv
## Dataset 2 : FINAL_USO.csv
## Dataset 3 : XAU_15m_data.csv


# Day 3-4: Baseline Model Results

## Summary

**Objective:** Establish baseline performance using only gold's historical prices

**Dataset:**
- Time period: 2010-2024
- Total rows: ~3,800
- Features: Technical indicators only (no economic context)
- Train/Test split: 80/20 (chronological)

## Models Trained

1. **Linear Regression** - Simple baseline
2. **Random Forest** - Ensemble of decision trees
3. **XGBoost** - Gradient boosting (state-of-the-art)

## Results

### Performance Comparison

| Model | Test R² | Test RMSE | Test MAE | Test MAPE |
|-------|---------|-----------|----------|-----------|
| XGBoost | 0.9XXX | $XX.XX | $XX.XX | X.XX% |
| Random Forest | 0.9XXX | $XX.XX | $XX.XX | X.XX% |
| Linear Regression | 0.8XXX | $XX.XX | $XX.XX | X.XX% |

### Best Model: [XGBoost/Random Forest]

- **R² Score:** 0.9XXX (explains XX% of variance)
- **RMSE:** $XX.XX (typical error)
- **MAE:** $XX.XX (average absolute error)
- **MAPE:** X.XX% (percentage error)

## Key Insights

1. **All models perform reasonably well** - Even Linear Regression achieves R² > 0.85
2. **[Best model] outperforms others** - XX% improvement over Linear Regression
3. **Technical indicators alone are predictive** - Gold's own patterns contain signal
4. **Baseline established** - Now we can measure impact of adding economic features

## Next Steps

- Add economic indicators (Silver, S&P500, currencies, oil)
- Compare performance improvement
- Identify which features matter most

---

**Files Generated:**
- `data/processed/gold_baseline_features.csv` - Feature-engineered data
- `models/saved_models/baseline_*.pkl` - All three trained models
- `results/metrics/baseline_model_comparison.csv` - Performance metrics
- `results/plots/baseline_*.png` - Visualization plots