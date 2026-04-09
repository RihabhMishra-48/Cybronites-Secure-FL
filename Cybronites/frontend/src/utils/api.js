import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const getStatus = () => api.get('/status');
export const getBlockchain = () => api.get('/blockchain');
export const initiateRound = () => api.post('/initiate-round');
export const aggregateRound = () => api.post('/aggregate');

export default api;
