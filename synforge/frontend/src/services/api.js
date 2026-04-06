import axios from 'axios';

// FIX: Clean assignment of the environment variable
const API_BASE_URL = process.env.REACT_APP_API_URL || "https://synforge.onrender.com";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // Note: Do not hardcode 'multipart/form-data' in the global config 
  // as it can interfere with GET requests. Axios handles it automatically for FormData.
});

export const uploadDataset = async (file, epsilon) => {
  const formData = new FormData();
  formData.append('file', file);
  
  // Using query params as your FastAPI endpoint expects
  const response = await apiClient.post(`/upload?epsilon=${epsilon}`, formData);
  return response.data; 
};

export const getJobStatus = async (jobId) => {
  const response = await apiClient.get(`/status/${jobId}`);
  return response.data; 
};

export const getReport = async (jobId) => {
  const response = await apiClient.get(`/report/${jobId}`);
  return response.data; 
};