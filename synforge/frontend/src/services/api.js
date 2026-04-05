import axios from 'axios';

// Set this to your local FastAPI URL or your production URL later
const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

export const uploadDataset = async (file,epsilon) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post(`/upload?epsilon=${epsilon}`, formData);
  return response.data; // returns { job_id: "..." }
};

export const getJobStatus = async (jobId) => {
  const response = await apiClient.get(`/status/${jobId}`);
  return response.data; // returns { status: "...", fidelity: 0.89 }
};

export const getReport = async (jobId) => {
  const response = await apiClient.get(`/report/${jobId}`);
  return response.data; // returns { fidelity_score, privacy_risk, etc }
};