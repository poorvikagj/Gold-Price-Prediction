import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service functions
const apiService = {
  // Models
  getModels: async () => {
    const response = await api.get('/models');
    return response.data;
  },

  getModelComparison: async () => {
    const response = await api.get('/model-comparison');
    return response.data;
  },

  // Predictions
  getPredictions: async (modelId = 'linear_regression', limit = 500) => {
    const response = await api.get('/predictions', {
      params: { model: modelId, limit },
    });
    return response.data;
  },

  getForecast: async (modelId = 'linear_regression', horizon = 180) => {
    const response = await api.get('/forecast', {
      params: { model: modelId, horizon },
    });
    return response.data;
  },

  predictCustom: async (modelId, features) => {
    const response = await api.post('/predict', {
      model: modelId,
      features,
    });
    return response.data;
  },

  // Metrics and Analytics
  getMetrics: async () => {
    const response = await api.get('/metrics');
    return response.data;
  },

  getErrorAnalysis: async (modelId = 'linear_regression') => {
    const response = await api.get('/error-analysis', {
      params: { model: modelId },
    });
    return response.data;
  },

  // Features
  getFeatureImportance: async (modelId = 'linear_regression', topN = 20) => {
    const response = await api.get('/feature-importance', {
      params: { model: modelId, top_n: topN },
    });
    return response.data;
  },

  // Data Statistics
  getDataStats: async () => {
    const response = await api.get('/data-stats');
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default apiService;
