import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import '../styles/Dashboard.css';

function Dashboard({ models }) {
  const [dataStats, setDataStats] = useState(null);
  const [modelComparison, setModelComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [statsRes, comparisonRes] = await Promise.all([
          apiService.getDataStats(),
          apiService.getModelComparison(),
        ]);

        if (statsRes.success) {
          setDataStats(statsRes.data);
        }
        if (comparisonRes.success) {
          setModelComparison(comparisonRes.data);
        }
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>

      {/* Dataset Statistics */}
      {dataStats && (
        <section className="dashboard-section">
          <h3>Dataset Overview</h3>
          <p className="chart-help">
            Data coverage: {dataStats.display_date_range}. Prices shown in forecast/prediction views are denormalized to {dataStats.price_unit}.
          </p>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Rows</div>
              <div className="stat-value">{dataStats.rows.toLocaleString()}</div>
              <p>Daily records</p>
            </div>
            <div className="stat-card">
              <div className="stat-label">Date Range</div>
              <div className="stat-value">{dataStats.display_date_range || `${dataStats.date_min} to ${dataStats.date_max}`}</div>
              <p>Dataset coverage window</p>
            </div>
            <div className="stat-card">
              <div className="stat-label">Features</div>
              <div className="stat-value">{dataStats.total_dataset_features}</div>
              <p>Total features engineered</p>
            </div>
            <div className="stat-card">
              <div className="stat-label">Columns</div>
              <div className="stat-value">{dataStats.columns}</div>
              <p>In raw dataset</p>
            </div>
            {dataStats.last_observed?.usd_estimated !== undefined && (
              <div className="stat-card">
                <div className="stat-label">Last Observed (USD Est.)</div>
                <div className="stat-value">${dataStats.last_observed.usd_estimated.toFixed(2)}</div>
                <p>{dataStats.last_observed.date}</p>
              </div>
            )}
          </div>

          {/* Feature Categories */}
          <div className="feature-categories">
            <h4>Feature Categories</h4>
            <div className="category-grid">
              {Object.entries(dataStats.feature_categories || {}).map(([name, count]) => (
                <div key={name} className="category-item">
                  <span className="category-name">{name.replace(/_/g, ' ')}</span>
                  <span className="category-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Model Comparison */}
      {modelComparison && (
        <section className="dashboard-section">
          <h3>Model Performance Comparison</h3>
          <div className="model-comparison-table">
            <table>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Train R²</th>
                  <th>Test R²</th>
                  <th>Train RMSE</th>
                  <th>Test RMSE</th>
                  <th>MAE</th>
                  <th>MAPE</th>
                </tr>
              </thead>
              <tbody>
                {modelComparison.map((model, idx) => (
                  <tr key={idx} className={idx === 0 ? 'best-model' : ''}>
                    <td className="model-name">
                      {idx === 0 && <span className="badge">BEST</span>}
                      {model.model}
                    </td>
                    <td>{model.train_r2.toFixed(4)}</td>
                    <td><strong>{model.test_r2.toFixed(4)}</strong></td>
                    <td>${model.train_rmse.toFixed(2)}</td>
                    <td><strong>${model.test_rmse.toFixed(2)}</strong></td>
                    <td>${model.test_mae.toFixed(2)}</td>
                    <td>{model.test_mape.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Best Model Highlight */}
          {modelComparison.length > 0 && (
            <div className="best-model-card">
              <h4>🏆 Best Model: {modelComparison[0].model}</h4>
              <div className="best-model-metrics">
                <div className="metric">
                  <span>R² Score:</span>
                  <strong>{modelComparison[0].test_r2.toFixed(4)}</strong>
                </div>
                <div className="metric">
                  <span>RMSE:</span>
                  <strong>${modelComparison[0].test_rmse.toFixed(2)}</strong>
                </div>
                <div className="metric">
                  <span>MAE:</span>
                  <strong>${modelComparison[0].test_mae.toFixed(2)}</strong>
                </div>
                <div className="metric">
                  <span>Test Samples:</span>
                  <strong>{modelComparison[0].test_samples}</strong>
                </div>
              </div>
              <p className="model-description">
                {modelComparison[0].model_id === 'xgboost' && 
                  'XGBoost excels at capturing non-linear relationships in economic data and feature interactions.'}
                {modelComparison[0].model_id === 'random_forest' && 
                  'Random Forest provides robust predictions through ensemble learning.'}
                {modelComparison[0].model_id === 'linear_regression' && 
                  'Linear Regression provides interpretable baseline predictions.'}
              </p>
            </div>
          )}
        </section>
      )}

      {/* Key Insights */}
      <section className="dashboard-section insights">
        <h3>📊 Key Insights</h3>
        <div className="insights-grid">
          <div className="insight-card">
            <h4>Economic Features Impact</h4>
            <p>Economic indicators improve predictions by 5-7% over gold-only baseline</p>
          </div>
          <div className="insight-card">
            <h4>Top Predictive Features</h4>
            <p>Silver lags, Gold/Silver ratio, S&P500, and EUR/USD are key drivers</p>
          </div>
          <div className="insight-card">
            <h4>Feature Diminishing Returns</h4>
            <p>80 features ≈ 200+ features in performance (optimization achieved)</p>
          </div>
          <div className="insight-card">
            <h4>Model Architecture</h4>
            <p>XGBoost typically achieves R² ~ 0.95-0.97 on this dataset</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
