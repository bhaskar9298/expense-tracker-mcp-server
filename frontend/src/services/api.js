// src/services/api.js - API client with credentials
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8001',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
};

export const mcpAPI = {
  execute: (tool, args) => api.post('/mcp/execute', { tool, args }),
};

export default api;
