import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import '../styles/Predictions.css';

function Predictions({ models }) {
  const PRICE_UNIT = 'USD per troy ounce (oz)';
  const [selectedModel, setSelectedModel] = useState('linear_regression');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [forecastMeta, setForecastMeta] = useState(null);
  const horizon = 180;

  useEffect(() => {
    if (!models || models.length === 0) return;
    const exists = models.some((m) => m.model_id === selectedModel);
    if (!exists) {
      const preferred = models.find((m) => m.model_id === 'linear_regression')?.model_id || models[0].model_id;
      setSelectedModel(preferred);
    }
  }, [models, selectedModel]);

  useEffect(() => {
    const fetchForecast = async () => {
      try {
        setLoading(true);
        setError(null);
        const forecastRes = await apiService.getForecast(selectedModel, horizon);
        if (forecastRes.success) {
          setForecast(forecastRes.forecast || []);
          setForecastMeta(forecastRes);
        }
      } catch (err) {
        setError('Failed to load 180-day forecast');
        console.error('Failed to load forecast:', err);
      } finally {
        setLoading(false);
      }
    };

    if (selectedModel) {
      fetchForecast();
    }
  }, [selectedModel, horizon]);

  const downloadPredictions = () => {
    if (forecast.length === 0) return;

    const csv_content = [
      ['Date', 'Predicted Price (USD/oz)', 'Predicted Price (Original Scale)', 'Day Ahead'],
      ...forecast.map(p => [
        p.date,
        p.predicted.toFixed(2),
        p.predicted_original?.toFixed(4),
        p.day_ahead,
      ]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csv_content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `predictions_${selectedModel}.csv`;
    a.click();
  };

  const selectedModelMeta = models.find((m) => m.model_id === selectedModel);

  return (
    <div className="predictions">
      <h2>Price Predictions</h2>
      <p className="unit-note">All prices are shown in {PRICE_UNIT}.</p>

      {/* Controls */}
      <div className="controls-section">
        <div className="control-group">
          <label>Select Model:</label>
          <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
            {models.map(model => (
              <option key={model.model_id} value={model.model_id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Forecast Horizon:</label>
          <strong>180 days</strong>
        </div>

        <button onClick={downloadPredictions} className="button-secondary">
          Download as CSV
        </button>
      </div>

      {selectedModelMeta?.metrics && (
        <div className="selected-model-summary">
          <strong>{selectedModelMeta.name}</strong>
          <span>Test R²: {selectedModelMeta.metrics.r2.toFixed(4)}</span>
          <span>RMSE: ${selectedModelMeta.metrics.rmse.toFixed(2)}</span>
          <span>MAPE: {(selectedModelMeta.metrics.mape * 100).toFixed(2)}%</span>
        </div>
      )}

      {loading && <div className="loading"><div className="spinner"></div></div>}
      {error && <div className="error-message">{error}</div>}

      {/* Current and Future Forecast */}
      {forecast.length > 0 && forecastMeta && (
        <section className="predictions-section">
          <h3>Next 180 Days Forecast (From Dataset End Date)</h3>
          <p className="chart-help">Forecast starts from {forecastMeta.forecast_start_date} and shows prediction values in {forecastMeta.price_unit || PRICE_UNIT}.</p>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Last Observed ({forecastMeta.last_observed_date})</div>
              <div className="stat-value">${forecastMeta.last_observed_price.toFixed(2)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Current Predicted</div>
              <div className="stat-value">${forecastMeta.current_prediction.toFixed(2)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Day {horizon} Forecast</div>
              <div className="stat-value">${forecast[forecast.length - 1].predicted.toFixed(2)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Uncertainty (±RMSE)</div>
              <div className="stat-value">
                ${((forecastMeta.uncertainty_band?.plus_minus_rmse ?? 0)).toFixed(2)}
              </div>
            </div>
          </div>

          <div className="chart-container">
            <ResponsiveContainer width="100%" height={360}>
              <LineChart data={forecast}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} />
                <YAxis label={{ value: PRICE_UNIT, angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                <Legend />
                <Line type="monotone" dataKey="predicted" stroke="#ef4444" dot={false} name="Forecast Price" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}
    </div>
  );
}

export default Predictions;
