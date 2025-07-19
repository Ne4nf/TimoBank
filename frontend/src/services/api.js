import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://timobanking.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Dashboard overview
  getDashboardOverview: () => api.get('/api/dashboard/overview'),

  // Data quality
  getDataQualitySummary: () => api.get('/api/data-quality/summary'),

  // Fraud alerts
  getFraudAlerts: (params = {}) => api.get('/api/fraud-alerts', { params }),

  // Transactions
  getTransactionSummary: (days = 30) => api.get('/api/transactions/summary', { params: { days } }),

  // Compliance
  getComplianceMetrics: () => api.get('/api/compliance/metrics'),

  // Customer risk profiles
  getCustomerRiskProfiles: (limit = 20) => api.get('/api/customers/risk-profile', { params: { limit } }),

  // Unverified devices
  getUnverifiedDevices: () => api.get('/api/unverified-devices'),
};

export default api;
